"""Worker integration against exact temporary databases."""

from copy import deepcopy
from contextlib import closing
from pathlib import Path
from queue import Empty, Queue
import sqlite3
import json
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic
import unittest
from uuid import uuid4

from arcs import authoring, core, disk, machine, main, mobile_stacks, records


class ArcIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.database = Path(self.directory.name) / "arcs.sqlite3"
        self.output = Queue()
        self.start_session()

    def start_session(self):
        disk.initialize_database_location(self.database)
        main.initialize_workers_and_wire_queues()
        core.g["send"] = self.output.put
        main.start_permanent_workers_in_reference_order()
        self.wait_command("READY")

    def tearDown(self):
        if machine.machines:
            machine.machines["CORE"]["inbox"].put({"type": "SHUTDOWN"})
            main.finish_worker_shutdown()
        self.directory.cleanup()

    def send(self, event):
        machine.machines["CORE"]["inbox"].put(event)

    def command(self, text):
        self.send({"type": "COMMAND", "text": text})

    def wait_command(self, kind, view=None):
        deadline = monotonic() + 8
        while monotonic() < deadline:
            try:
                command = self.output.get(timeout=0.1)
            except Empty:
                if machine.a_thread_died_unexpectedly.is_set():
                    self.fail("Worker failed")
                continue
            if command["type"] == kind and (view is None or command.get("view") == view):
                return command
        self.fail(f"Timed out waiting for {kind}")

    def create(self):
        self.command("create-arc")
        return self.wait_command("OPEN")

    def start_author(self, view, kind):
        self.send({"type": "AUTHOR_NAVIGATE", "view": view,
                   "intent": {"kind": "start", "draft-kind": kind}})
        return self.wait_command("AUTHOR", view)["draft"]

    def submit_author(self, view, draft):
        self.send({"type": "AUTHOR_SAVE", "view": view, "uuid": draft["uuid"], "fields": draft["fields"]})
        self.wait_command("AUTHOR_BUSY", view)

    def test_authoring_chronology_association_and_restart(self):
        first = self.create()
        self.command("edit-arc " + first["record"]["uuid"])
        second = self.wait_command("OPEN")
        unrelated = self.create()
        journal = self.start_author(first["view"], "journal-entry")
        journal["fields"].update(description="A journal's actual prose.\nAnother paragraph.", when="2026-09-01")
        self.submit_author(first["view"], journal)
        self.wait_command("CHRONOLOGY", first["view"])
        detail = self.wait_command("DETAIL", first["view"])["record"]
        self.assertEqual(detail["description"], journal["fields"]["description"])
        self.assertEqual(detail["type"], "journal-entry")
        self.wait_command("AUTHOR_BUSY", first["view"])
        other_draft = self.start_author(second["view"], "event")
        self.send({"type": "AUTHOR_DRAFT", "view": second["view"], "uuid": other_draft["uuid"],
                   "fields": {**other_draft["fields"], "description": "Independent unsaved event"}})
        backdated = self.start_author(first["view"], "event")
        backdated["fields"].update(description="An earlier event", when="1998", earliest="1997", latest="1999")
        self.submit_author(first["view"], backdated)
        items = self.wait_command("CHRONOLOGY", first["view"])["items"]
        self.assertEqual([item["uuid"] for item in items], [journal["uuid"], backdated["uuid"]])
        self.wait_command("AUTHOR_BUSY", first["view"])
        self.assertEqual(core.views[second["view"]]["author"]["fields"]["description"], "Independent unsaved event")
        self.assertEqual(core.views[unrelated["view"]]["chronology"], [])
        unknown = self.start_author(first["view"], "event")
        unknown["fields"]["description"] = "An undated event"
        self.submit_author(first["view"], unknown)
        items = self.wait_command("CHRONOLOGY", first["view"])["items"]
        self.assertEqual(items[-1]["uuid"], unknown["uuid"])
        self.assertEqual(items[-1]["time-label"], "Time unknown")
        self.wait_command("AUTHOR_BUSY", first["view"])
        self.assertEqual(core.views[first["view"]]["record"]["revision"], 1)
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        main.finish_worker_shutdown()
        self.start_session()
        self.command("edit-arc " + first["record"]["uuid"])
        opened = self.wait_command("OPEN")
        reopened = self.wait_command("CHRONOLOGY", opened["view"])["items"]
        self.assertEqual([item["uuid"] for item in reopened], [journal["uuid"], backdated["uuid"], unknown["uuid"]])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM links WHERE type='member-of'").fetchone()[0], 3)
            self.assertEqual(connection.execute("SELECT date FROM basic WHERE uuid=?", (journal["uuid"],)).fetchone()[0], "2026-09-01")

    def test_atomic_transition_links_and_stale_predecessor(self):
        first = self.create()
        self.command("edit-arc " + first["record"]["uuid"])
        second = self.wait_command("OPEN")
        a = self.start_author(first["view"], "transition")
        b = self.start_author(second["view"], "transition")
        for draft in (a, b):
            draft["fields"].update(description="A defining change", when="2001-04", earliest="2001-03",
                                   latest="2001-05", **{"successor-title": "The next passage"})
        self.submit_author(first["view"], a)
        self.wait_command("AUTHOR_BUSY", first["view"])
        self.assertIsNone(core.views[first["view"]]["author"])
        self.assertEqual(core.views[first["view"]]["selected"], a["uuid"])
        self.submit_author(second["view"], b)
        self.assertIn("predecessor changed", self.wait_command("AUTHOR_STATUS", second["view"])["status"])
        self.wait_command("AUTHOR_BUSY", second["view"])
        self.assertEqual(core.views[second["view"]]["author"]["fields"], b["fields"])
        self.command("edit-arc " + a["successor"])
        successor = self.wait_command("OPEN")["record"]
        self.assertEqual(successor["end-event"], None)
        self.assertEqual(successor["begin-event"], a["uuid"])
        self.assertEqual(records.get_effective_claim(successor)["end"], "ONGOING")
        self.assertEqual(records.get_effective_claim(successor)["begin"]["earliest"], "2001-03")
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        main.finish_worker_shutdown()
        with closing(sqlite3.connect(self.database)) as connection:
            links = connection.execute('SELECT uuid,"from","to",type FROM links').fetchall()
            self.assertEqual(len(links), 4)
            self.assertEqual(len({link[0] for link in links}), 4)
            transition = next(link for link in links if link[3] == "transition")
            via = next(link for link in links if link[3] == "via")
            self.assertEqual(transition[1:3], (first["record"]["uuid"], a["successor"]))
            self.assertEqual(via[1:3], (transition[0], a["uuid"]))
            self.assertEqual(connection.execute("SELECT count(*) FROM basic WHERE type='link'").fetchone()[0], 0)
            identities = {link[0] for link in links}
        self.start_session()
        self.command("edit-arc " + first["record"]["uuid"])
        predecessor = self.wait_command("OPEN")
        item = self.wait_command("CHRONOLOGY", predecessor["view"])["items"][0]
        self.assertEqual(item["successor"], a["successor"])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual({row[0] for row in connection.execute("SELECT uuid FROM links")}, identities)

    def test_failed_transition_rolls_back_and_cancels_shutdown(self):
        first = self.create()
        draft = self.start_author(first["view"], "transition")
        draft["fields"].update(description="An attempted transition", **{"successor-title": "Successor"})
        entered, release = Event(), Event()
        original = machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"]

        def handle_when_test_rejects_transition_via():
            connection = disk.g["connection"]
            connection.execute("CREATE TEMP TRIGGER reject_via BEFORE INSERT ON links WHEN NEW.type='via' "
                               "BEGIN SELECT RAISE(ABORT, 'Injected via failure'); END")
            entered.set()
            release.wait(5)
            try:
                original()
            finally:
                connection.execute("DROP TRIGGER reject_via")

        machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"] = handle_when_test_rejects_transition_via
        self.submit_author(first["view"], draft)
        self.assertTrue(entered.wait(3))
        self.send({"type": "SHUTDOWN"})
        release.set()
        self.wait_command("CLOSE_ABORTED")
        self.wait_command("AUTHOR_BUSY", first["view"])
        self.assertEqual(core.views[first["view"]]["author"]["fields"], draft["fields"])
        self.assertTrue(main.worker_threads["CORE"].is_alive())
        with closing(sqlite3.connect(self.database)) as connection:
            for table, expected in (("basic", 1), ("arc", 1), ("temporal", 0), ("links", 0)):
                self.assertEqual(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0], expected)
            self.assertEqual(connection.execute("SELECT revision FROM arc").fetchone()[0], 1)
        machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"] = original
        event = {"type": "AUTHOR_SAVE", "view": first["view"], "uuid": draft["uuid"], "fields": draft["fields"]}
        self.send(event)
        self.send(deepcopy(event))
        self.wait_command("AUTHOR_BUSY", first["view"])
        self.wait_command("AUTHOR_BUSY", first["view"])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM arc").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT count(*) FROM links").fetchone()[0], 4)

    def test_migration_preserves_version_one_arc(self):
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        main.finish_worker_shutdown()
        self.database = Path(self.directory.name) / "legacy.sqlite3"
        original = records.create_arc("00000000-0000-0000-0000-000000000001")
        original.update(title="Legacy title", description="Preserve me", name="legacy")
        with closing(sqlite3.connect(self.database)) as connection:
            connection.executescript("CREATE TABLE basic (uuid TEXT PRIMARY KEY,name TEXT NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL);"
                                     "CREATE TABLE arc (uuid TEXT PRIMARY KEY REFERENCES basic(uuid),revision INTEGER NOT NULL,temporal_json TEXT NOT NULL);"
                                     "PRAGMA user_version=1;")
            connection.execute("INSERT INTO basic VALUES (?,?,?,?)", (original["uuid"], original["name"], original["title"], original["description"]))
            connection.execute("INSERT INTO arc VALUES (?,?,?)", (original["uuid"], 1, json.dumps(original["temporal"])))
            connection.commit()
        self.start_session()
        self.command("edit-arc " + original["uuid"])
        self.assertEqual(self.wait_command("OPEN")["fields"], records.get_editor_fields(original))
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertIn("type", {row[1] for row in connection.execute("PRAGMA table_info(basic)")})
            self.assertNotIn("typehint", {row[1] for row in connection.execute("PRAGMA table_info(links)")})

    def test_disk_rechecks_endpoint_and_rolls_back_entry(self):
        first = self.create()
        original = machine.machines["MEM"]["handlers"]["REQUEST"]

        def handle_when_test_supplies_bad_endpoint():
            original()
            if mobile_stacks.get_register("request")["action"] == "author":
                mobile_stacks.get_register("bundle")["links"][0]["to"] = str(uuid4())

        machine.machines["MEM"]["handlers"]["REQUEST"] = handle_when_test_supplies_bad_endpoint
        draft = self.start_author(first["view"], "journal-entry")
        draft["fields"]["description"] = "No orphan record should persist."
        self.submit_author(first["view"], draft)
        self.assertIn("endpoint does not exist", self.wait_command("AUTHOR_STATUS", first["view"])["status"])
        self.wait_command("AUTHOR_BUSY", first["view"])
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM basic").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM links").fetchone()[0], 0)

    def test_stored_multiple_parents_and_optional_link_basic(self):
        parents = [self.create() for _ in range(2)]
        child = self.create()
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        main.finish_worker_shutdown()
        links = [authoring.create_link(parent["record"]["uuid"], child["record"]["uuid"])
                 for parent in (parents[0], parents[1], parents[0])]
        with closing(sqlite3.connect(self.database)) as connection:
            for link in links:
                connection.execute('INSERT INTO links VALUES (?,?,?,?,?)', (link["uuid"], link["from"], link["to"], "parent-child", 1))
            connection.execute("INSERT INTO basic (uuid,name,title,description,type,date) VALUES (?,?,?,?,?,?)",
                               (links[0]["uuid"], "relationship", "Parent relationship", "", "link", ""))
            connection.commit()
        self.start_session()
        self.command("list-arcs")
        while True:
            text = self.wait_command("OUTPUT")["text"]
            if child["record"]["uuid"] in text:
                self.assertEqual(len(text.splitlines()), 3)
                break
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM links WHERE "to"=? AND type=\'parent-child\'',
                                                (child["record"]["uuid"],)).fetchone()[0], 3)

    def test_three_arcs_persist_and_reopen_after_restart(self):
        self.assertEqual(core.views, {})
        created = [self.create() for _ in range(3)]
        ids = [item["record"]["uuid"] for item in created]
        self.assertEqual(len(set(ids)), 3)
        first = created[0]
        fields = {**first["fields"], "title": "Career: a new chapter", "name": "new-chapter",
                  "description": "A passage with its own story.\nSecond paragraph.",
                  "begin": "2024-03", "end": "ONGOING"}
        self.send({"type": "SAVE", "view": first["view"], "fields": fields})
        self.wait_command("BUSY")
        update = self.wait_command("UPDATE")
        self.assertEqual(update["fields"], fields)
        self.wait_command("BUSY")
        self.send({"type": "CLOSE_VIEW", "view": first["view"]})
        self.wait_command("CLOSE")
        self.command("edit-arc " + ids[0])
        self.assertEqual(self.wait_command("OPEN")["fields"], fields)
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        main.finish_worker_shutdown()
        self.assertIsNone(disk.g["connection"])
        self.start_session()
        self.command("list-arcs")
        listing = []
        while not listing:
            text = self.wait_command("OUTPUT")["text"]
            if all(uuid in text for uuid in ids):
                listing = text.splitlines()
        self.assertEqual(len(listing), 3)
        self.command("edit-arc " + ids[0].upper())
        self.assertEqual(self.wait_command("OPEN")["fields"], fields)

    def test_conflicts_and_snapshot_isolation(self):
        first = self.create()
        uuid = first["record"]["uuid"]
        # Mutating returned presentation data must not reach canonical memory.
        first["record"]["temporal"]["records"].clear()
        first["fields"]["description"] = "Mutated presentation copy"
        self.assertEqual(core.views[first["view"]]["draft"]["description"], "")
        self.command("edit-arc " + uuid)
        second = self.wait_command("OPEN")
        self.assertEqual(len(second["record"]["temporal"]["records"]), 1)
        draft = {**second["fields"], "title": "My independent draft"}
        self.send({"type": "DRAFT", "view": second["view"], "fields": draft})
        accepted = {**second["fields"], "title": "Saved in first view"}
        self.send({"type": "SAVE", "view": first["view"], "fields": accepted})
        self.wait_command("BUSY")
        updates = [self.wait_command("UPDATE") for _ in range(2)]
        other = next(item for item in updates if item["view"] == second["view"])
        self.assertNotIn("fields", other)
        self.wait_command("BUSY")
        self.send({"type": "SAVE", "view": second["view"], "fields": draft})
        self.wait_command("BUSY")
        self.assertIn("Conflict", self.wait_command("STATUS")["status"])
        self.wait_command("BUSY")
        self.send({"type": "RELOAD", "view": second["view"], "fields": draft})
        self.wait_command("BUSY")
        self.assertEqual(self.wait_command("UPDATE")["fields"]["title"], accepted["title"])

    def test_close_waits_for_commit_and_closed_view_return(self):
        first = self.create()
        held, release = Event(), Event()
        original = machine.machines["DISK"]["handlers"]["WRITE"]

        def handle_when_test_holds_disk_write():
            held.set()
            if not release.wait(5):
                raise RuntimeError("Test did not release Disk")
            original()

        machine.machines["DISK"]["handlers"]["WRITE"] = handle_when_test_holds_disk_write
        fields = {**first["fields"], "description": "Write must survive closing its view."}
        self.send({"type": "SAVE", "view": first["view"], "fields": fields})
        self.assertTrue(held.wait(3))
        self.send({"type": "CLOSE_VIEW", "view": first["view"]})
        self.wait_command("CLOSE")
        self.send({"type": "SHUTDOWN"})
        self.send({"type": "SHUTDOWN"})
        # Receipt of close output proves Core remains responsive during the held write.
        self.assertIn("Closing", self.wait_command("OUTPUT")["text"])
        self.assertTrue(main.worker_threads["CORE"].is_alive())
        release.set()
        self.wait_command("SHUTDOWN_COMPLETE")
        main.finish_worker_shutdown()
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT description FROM basic").fetchone()[0], fields["description"])

    def test_edit_arc_resolves_names_and_reports_ambiguity(self):
        first = self.create()
        self.command("edit-arc " + first["record"]["name"])
        self.assertEqual(self.wait_command("OPEN")["record"]["uuid"], first["record"]["uuid"])
        fields = {**first["fields"], "name": "my-chapter"}
        self.send({"type": "SAVE", "view": first["view"], "fields": fields})
        self.wait_command("BUSY")
        self.wait_command("UPDATE")
        self.wait_command("BUSY")
        self.command("edit-arc my-chapter")
        self.assertEqual(self.wait_command("OPEN")["record"]["uuid"], first["record"]["uuid"])
        self.command("edit-arc " + first["record"]["name"])
        while "Unknown arc name or UUID" not in self.wait_command("OUTPUT")["text"]:
            pass
        second = self.create()
        self.send({"type": "SAVE", "view": second["view"],
                   "fields": {**second["fields"], "name": "my-chapter"}})
        self.wait_command("BUSY")
        self.wait_command("UPDATE")
        self.wait_command("BUSY")
        self.command("edit-arc my-chapter")
        while "More than one arc" not in self.wait_command("OUTPUT")["text"]:
            pass
        self.command("edit-arc " + first["record"]["uuid"].upper())
        self.assertEqual(self.wait_command("OPEN")["record"]["uuid"], first["record"]["uuid"])

    def test_bad_commands_and_validation_leave_no_partial_records(self):
        for text in ("create-arc extra", "edit-arc invalid", "edit-arc 00000000-0000-0000-0000-000000000000"):
            self.command(text)
        self.command("list-arcs")
        while self.wait_command("OUTPUT")["text"] != "No arcs.":
            pass
        first = self.create()
        fields = {**first["fields"], "name": "Bad name", "begin": "2024-99"}
        self.send({"type": "SAVE", "view": first["view"], "fields": fields})
        self.wait_command("BUSY")
        self.wait_command("STATUS")
        self.wait_command("BUSY")
        self.command("edit-arc " + first["record"]["uuid"])
        self.assertEqual(self.wait_command("OPEN")["record"]["revision"], 1)


class TemporalTests(unittest.TestCase):
    def test_claim_history_and_precision(self):
        record = records.create_arc("00000000-0000-0000-0000-000000000001")
        first = records.prepare_arc_update(record, {**records.get_editor_fields(record), "begin": "1998", "end": "ONGOING"})
        second = records.prepare_arc_update(first, {**records.get_editor_fields(first), "begin": "1998-06"})
        claims = second["temporal"]["records"][0]["temporal-claims"]
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0]["begin"]["precision"], "YEAR")
        self.assertEqual(claims[1]["begin"]["precision"], "MONTH")
        self.assertEqual(record["temporal"]["records"][0]["temporal-claims"], [])
        with self.assertRaises(ValueError):
            records.parse_boundary("ONGOING", "begin")
        with self.assertRaises(ValueError):
            records.parse_boundary("2026-02-30", "end")

    def test_richer_claims_survive_unrelated_edits(self):
        record = records.create_arc("00000000-0000-0000-0000-000000000001")
        record["temporal"]["records"][0]["temporal-claims"] = [
            {"uuid": "00000000-0000-0000-0000-000000000002", "recorded-at": records.stamp(),
             "begin": {"earliest": "1998", "latest": "2000", "precision": "YEAR"},
             "claim-notes": "Remembered only approximately."}]
        result = records.prepare_arc_update(record, {**records.get_editor_fields(record), "title": "Changed title"})
        self.assertEqual(result["temporal"]["records"][0]["temporal-claims"], record["temporal"]["records"][0]["temporal-claims"])


class LinkTests(unittest.TestCase):
    def test_general_endpoints_parent_direction_and_metadata_identity(self):
        a, b, child = [records.create_arc(str(uuid4())) for _ in range(3)]
        event_draft = authoring.create_draft("event", a)
        event_draft["fields"]["description"] = "An event"
        event = authoring.create_record(event_draft)
        transition = authoring.create_link(a["uuid"], b["uuid"])
        transition["type"] = "transition"
        via = authoring.create_link(transition["uuid"], event["uuid"])
        via["type"] = "via"
        parents = [authoring.create_link(parent["uuid"], child["uuid"]) for parent in (a, b, a)]
        for link in parents:
            link["type"] = "parent-child"
        bundle = {"objects": [a, b, child, event], "links": [transition, via, *parents]}
        empty = {"objects": {}, "links": {}}
        authoring.validate_links(bundle, empty)
        # A link needs no Basic row, and optional metadata must reuse its identity.
        bundle["objects"].append({"uuid": transition["uuid"], "type": "link"})
        authoring.validate_links(bundle, empty)
        bundle["objects"][-1]["type"] = "arc"
        with self.assertRaisesRegex(ValueError, "share an identity"):
            authoring.validate_links(bundle, empty)
        bundle["objects"].pop()
        via["from"] = str(uuid4())
        with self.assertRaisesRegex(ValueError, "source does not exist"):
            authoring.validate_links(bundle, empty)
        self.assertEqual(authoring.LINK_TYPES["via"], "tag:m1lattice.net,2026:/linktype/via")

    def test_occurrence_precision_and_unknown_claims(self):
        arc = records.create_arc(str(uuid4()))
        draft = authoring.create_draft("event", arc)
        draft["fields"].update(description="Unknown event", notes="Remembered, but undated.")
        event = authoring.create_record(draft)
        self.assertEqual(event["date"], "")
        self.assertNotIn("event", records.get_effective_claim(event))
        draft["fields"].update(when="2026-10-11T12:30:05.123-07:00", notes="")
        event = authoring.create_record(draft)
        self.assertEqual(records.get_effective_claim(event)["event"]["precision"], "MILLISECOND")
        draft["fields"]["when"] = "2026-10-11T12:30:00"
        with self.assertRaises(ValueError):
            authoring.create_record(draft)


if __name__ == "__main__":
    unittest.main()
