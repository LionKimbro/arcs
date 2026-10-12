"""Worker integration against exact temporary databases."""

from copy import deepcopy
from contextlib import closing
from pathlib import Path
from queue import Empty, Queue
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic
import unittest

from arcs import core, disk, machine, main, records


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

    def wait_command(self, kind):
        deadline = monotonic() + 8
        while monotonic() < deadline:
            try:
                command = self.output.get(timeout=0.1)
            except Empty:
                if machine.a_thread_died_unexpectedly.is_set():
                    self.fail("Worker failed")
                continue
            if command["type"] == kind:
                return command
        self.fail(f"Timed out waiting for {kind}")

    def create(self):
        self.command("create-arc")
        return self.wait_command("OPEN")

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


if __name__ == "__main__":
    unittest.main()
