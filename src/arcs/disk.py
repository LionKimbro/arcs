"""SQLite connection and transactions, exclusively on the Disk worker."""

import json
from pathlib import Path
import sqlite3

from . import authoring, machine, mobile_stacks, records

g = {"database": None, "connection": None}


def initialize_database_location(path=None):
    if path is None:
        import machineroot
        path = Path(machineroot.get("db-root-2026")) / "arcs" / "arcs.sqlite3"
    g["database"] = Path(path).expanduser().resolve()


def open_database_and_check_initial_schema():
    g["database"].parent.mkdir(parents=True, exist_ok=True)
    g["connection"] = sqlite3.connect(g["database"])
    connection = g["connection"]
    connection.execute("PRAGMA foreign_keys=ON")
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == 0:
        if connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            raise ValueError("Refusing to initialize an unrecognized nonempty database.")
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("CREATE TABLE basic (uuid TEXT PRIMARY KEY, name TEXT NOT NULL, "
                               "title TEXT NOT NULL, description TEXT NOT NULL)")
            connection.execute("CREATE TABLE arc (uuid TEXT PRIMARY KEY REFERENCES basic(uuid), "
                               "revision INTEGER NOT NULL CHECK(revision > 0), temporal_json TEXT NOT NULL)")
            connection.execute("PRAGMA user_version=1")
        version = 1
    if version == 1:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("ALTER TABLE basic ADD COLUMN type TEXT NOT NULL DEFAULT 'arc'")
            connection.execute("ALTER TABLE basic ADD COLUMN date TEXT NOT NULL DEFAULT ''")
            connection.execute("ALTER TABLE arc ADD COLUMN begin_event TEXT REFERENCES basic(uuid)")
            connection.execute("ALTER TABLE arc ADD COLUMN end_event TEXT REFERENCES basic(uuid)")
            connection.execute('CREATE TABLE links (uuid TEXT PRIMARY KEY NOT NULL, "from" TEXT NOT NULL, '
                               '"to" TEXT NOT NULL, type TEXT NOT NULL CHECK(length(trim(type)) > 0), '
                               'revision INTEGER NOT NULL CHECK(revision > 0))')
            connection.execute('CREATE INDEX links_from_type ON links ("from", type)')
            connection.execute('CREATE INDEX links_to_type ON links ("to", type)')
            connection.execute("CREATE INDEX basic_type ON basic(type)")
            connection.execute("CREATE TABLE temporal (uuid TEXT PRIMARY KEY NOT NULL REFERENCES basic(uuid), "
                               "temporal_json TEXT NOT NULL)")
            connection.execute("PRAGMA user_version=2")
    elif version != 2:
        raise ValueError(f"Unsupported database version: {version}")


def handle_when_disk_receives_initial_load():
    connection = g["connection"]
    result = {"objects": {}, "links": {}}
    for uuid, name, title, description, kind, associated_date in connection.execute(
            "SELECT uuid,name,title,description,type,date FROM basic"):
        record = dict(uuid=uuid, name=name, title=title, description=description,
                      type=kind, date=associated_date, revision=1)
        if records.normalize_uuid(uuid) != uuid:
            raise ValueError("Stored UUID is not normalized")
        if kind == "arc":
            aspect = connection.execute("SELECT revision,temporal_json,begin_event,end_event FROM arc WHERE uuid=?", (uuid,)).fetchone()
            if aspect is None:
                raise ValueError("Arc Basic row lacks its Arc aspect")
            record.update(revision=aspect[0], temporal=json.loads(aspect[1]),
                          **{"begin-event": aspect[2], "end-event": aspect[3]})
            records.validate_stored_arc(record)
        elif kind in ("event", "journal-entry"):
            aspect = connection.execute("SELECT temporal_json FROM temporal WHERE uuid=?", (uuid,)).fetchone()
            if aspect is None:
                raise ValueError("Entry/event lacks temporal content")
            record["temporal"] = json.loads(aspect[0])
            temporal_record = record["temporal"]["records"][0]
            if temporal_record["uuid"] != uuid or temporal_record["type"] != "EVENT":
                raise ValueError("Invalid entry/event temporal identity")
        result["objects"][uuid] = record
    for uuid, source, target, kind, revision in connection.execute('SELECT uuid,"from","to",type,revision FROM links'):
        result["links"][uuid] = dict(uuid=uuid, **{"from": source, "to": target}, type=kind, revision=revision)
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("Broken aspect or boundary references")
    authoring.validate_links({"objects": [], "links": list(result["links"].values())}, result)
    mobile_stacks.set_register("loaded", result)


def write_object(record, base):
    connection = g["connection"]
    current = connection.execute("SELECT type FROM basic WHERE uuid=?", (record["uuid"],)).fetchone()
    if base is None:
        existing_link = connection.execute("SELECT uuid FROM links WHERE uuid=?", (record["uuid"],)).fetchone()
        if current or (existing_link and record["type"] != "link"):
            raise ValueError("New object identity is already in use")
        connection.execute("INSERT INTO basic (uuid,name,title,description,type,date) VALUES (?,?,?,?,?,?)", (
            record["uuid"], record["name"], record["title"], record["description"], record["type"], record.get("date", "")))
    else:
        stored = connection.execute("SELECT revision FROM arc WHERE uuid=?", (record["uuid"],)).fetchone()
        if current is None or current[0] != "arc" or not stored or stored[0] != base:
            raise ValueError("Database revision changed outside this view; reload before saving.")
        connection.execute("UPDATE basic SET name=?,title=?,description=?,date=? WHERE uuid=?", (
            record["name"], record["title"], record["description"], record.get("date", ""), record["uuid"]))
    if record["type"] == "arc":
        values = (record["revision"], json.dumps(record["temporal"]), record.get("begin-event"),
                  record.get("end-event"), record["uuid"])
        if base is None:
            connection.execute("INSERT INTO arc (revision,temporal_json,begin_event,end_event,uuid) VALUES (?,?,?,?,?)", values)
        else:
            connection.execute("UPDATE arc SET revision=?,temporal_json=?,begin_event=?,end_event=? WHERE uuid=?", values)
    elif "temporal" in record:
        connection.execute("INSERT INTO temporal VALUES (?,?)", (record["uuid"], json.dumps(record["temporal"])))


def verify_link_endpoints_within_transaction(bundle):
    connection = g["connection"]
    for link in bundle["links"]:
        if connection.execute("SELECT type FROM basic WHERE uuid=?", (link["uuid"],)).fetchone():
            kind = connection.execute("SELECT type FROM basic WHERE uuid=?", (link["uuid"],)).fetchone()[0]
            if kind != "link":
                raise ValueError("Unrelated Basic/link identity collision")
        for endpoint in (link["from"], link["to"]):
            found = connection.execute("SELECT uuid FROM basic WHERE uuid=? UNION ALL SELECT uuid FROM links WHERE uuid=?",
                                       (endpoint, endpoint)).fetchone()
            if found is None:
                raise ValueError("A link endpoint does not exist")


def handle_when_disk_receives_authoring_write():
    bundle = mobile_stacks.get_register("bundle")
    connection = g["connection"]
    mobile_stacks.set_register("write-error", None)
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            # Event first, then successor, then predecessor; boundary references resolve.
            for record in bundle["objects"]:
                write_object(record, bundle["bases"][record["uuid"]])
            for link in bundle["links"]:
                connection.execute('INSERT INTO links (uuid,"from","to",type,revision) VALUES (?,?,?,?,?)', (
                    link["uuid"], link["from"], link["to"], link["type"], link["revision"]))
            verify_link_endpoints_within_transaction(bundle)
    except (sqlite3.IntegrityError, sqlite3.OperationalError, ValueError) as error:
        mobile_stacks.set_register("write-error", str(error))
        return
    mobile_stacks.set_register("committed", True)


def handle_when_disk_receives_arc_write():
    proposal = mobile_stacks.get_register("proposal")
    base = mobile_stacks.get_register("base")
    connection = g["connection"]
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        write_object(proposal, base)
    mobile_stacks.set_register("committed", True)


def run_disk_machine():
    try:
        open_database_and_check_initial_schema()
        machine.run_machine()
    finally:
        if g["connection"] is not None:
            g["connection"].close()
            g["connection"] = None
