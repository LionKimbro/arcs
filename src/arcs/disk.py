"""SQLite connection and transactions, exclusively on the Disk worker."""

import json
from pathlib import Path
import sqlite3

from . import machine, mobile_stacks, records

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
    elif version != 1:
        raise ValueError(f"Unsupported database version: {version}")


def handle_when_disk_receives_initial_load():
    connection = g["connection"]
    rows = connection.execute("SELECT b.uuid,b.name,b.title,b.description,a.revision,a.temporal_json "
                              "FROM basic b JOIN arc a ON a.uuid=b.uuid").fetchall()
    if len(rows) != connection.execute("SELECT count(*) FROM arc").fetchone()[0]:
        raise ValueError("Arc aspect without Basic data.")
    result = []
    for uuid, name, title, description, revision, temporal in rows:
        record = dict(uuid=uuid, name=name, title=title, description=description,
                      revision=revision, temporal=json.loads(temporal))
        records.validate_stored_arc(record)
        result.append(record)
    mobile_stacks.set_register("loaded", result)


def handle_when_disk_receives_arc_write():
    proposal = mobile_stacks.get_register("proposal")
    base = mobile_stacks.get_register("base")
    connection = g["connection"]
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute("SELECT revision FROM arc WHERE uuid=?",
                                     (proposal["uuid"],)).fetchone()
        if (current[0] if current else None) != base:
            # External writers are unsupported; never accept stale data silently.
            raise RuntimeError("Database changed outside this Arcs session.")
        if base is None:
            connection.execute("INSERT INTO basic VALUES (?,?,?,?)", (
                proposal["uuid"], proposal["name"], proposal["title"], proposal["description"]))
            connection.execute("INSERT INTO arc VALUES (?,?,?)", (
                proposal["uuid"], proposal["revision"], json.dumps(proposal["temporal"])))
        else:
            connection.execute("UPDATE basic SET name=?,title=?,description=? WHERE uuid=?", (
                proposal["name"], proposal["title"], proposal["description"], proposal["uuid"]))
            connection.execute("UPDATE arc SET revision=?,temporal_json=? WHERE uuid=?", (
                proposal["revision"], json.dumps(proposal["temporal"]), proposal["uuid"]))
    mobile_stacks.set_register("committed", True)


def run_disk_machine():
    try:
        open_database_and_check_initial_schema()
        machine.run_machine()
    finally:
        if g["connection"] is not None:
            g["connection"].close()
            g["connection"] = None
