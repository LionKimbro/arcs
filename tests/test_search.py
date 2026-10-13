"""Search contracts and real worker/reducer behavior against temporary databases."""

from copy import deepcopy
from contextlib import closing
import json
import sqlite3
from threading import Event
import unittest

import test_arcs as harness
from arcs import core, machine, mobile_stacks, search, search_core


class SearchContractTests(unittest.TestCase):
    def test_matching_and_clipboard_contracts(self):
        objects = {
            "a": {"uuid": "a", "title": "Coastal MOVE", "name": "coastal-move", "type": "arc",
                  "tags": ["Home", "New chapter"], "date": ""},
            "b": {"uuid": "b", "title": "Moving again", "name": "elsewhere", "type": "event", "tags": ["home"]},
            "c": {"uuid": "c", "title": "Link metadata", "name": "relationship", "type": "link"}}
        criteria = {"type": "arc", "name-contains": "COAST", "title-contains": "move",
                    "tags": [" HOME ", "new CHAPTER"]}
        self.assertEqual([row["uuid"] for row in search.find_results(criteria, objects)], ["a"])
        self.assertFalse(search.find_results({**criteria, "tags": ["hom"]}, objects))
        self.assertEqual(len(search.find_results({"tags": ["HOME", "absent"], "tag-match": "any"}, objects)), 2)
        self.assertFalse(search.find_results({"tags": ["HOME", "absent"], "tag-match": "all"}, objects))
        self.assertEqual(len(search.find_results({}, objects)), 3)
        rows = search.find_results({}, objects)
        rows[0]["tags"].append("unaccepted mutation")
        self.assertNotIn("unaccepted mutation", objects["a"]["tags"])
        self.assertEqual(search.parse_tags(" Work, work, New chapter, , HOME "), ["Work", "New chapter", "HOME"])
        payload = search.serialize_search(criteria)
        self.assertEqual(search.classify_clipboard(payload)["criteria"], search.validate_criteria(criteria))
        self.assertEqual(search.classify_clipboard('{"format":"arcs-basic-search","version":1,"criteria":{}}')["criteria"], search.empty_criteria())
        for invalid in (
                '{"format":"arcs-basic-search","version":2,"criteria":{}}',
                '{"format":"arcs-basic-search","version":true,"criteria":{}}',
                '{"format":"arcs-basic-search","version":1,"criteria":{"overlap":true}}',
                '{"format":"arcs-basic-search","version":1,"criteria":{"tags":"home"}}',
                '["invalid UUID"]', '{broken'):
            with self.assertRaises(ValueError):
                search.classify_clipboard(invalid)
        self.assertEqual(search.classify_clipboard("Ordinary prose")["kind"], "ordinary")

    def test_incorporation_and_session_validation(self):
        merge = search.get_incorporation({"type": "arc", "tags": ["Home"], "tag-match": "all"},
                                         {"type": "event", "tags": ["home"], "tag-match": "any", "title-contains": "coast"})
        self.assertEqual({item["field"] for item in merge["conflicts"]}, {"type", "tags"})
        self.assertEqual(merge["criteria"]["title-contains"], "coast")
        self.assertEqual(search.get_incorporation({"tags": ["Home"]}, {"tags": ["HOME"]})["conflicts"], [])
        self.assertEqual(search.get_incorporation({"title-contains": "Coast"}, {"title-contains": "COAST"})["conflicts"], [])
        for name in ("", " has-space", "a b", "a\nb", "00000000-0000-0000-0000-000000000001"):
            with self.assertRaises(ValueError):
                search.validate_session_name(name)
        self.assertEqual(search.validate_session_name("A"), "A")


class SearchIntegrationTests(unittest.TestCase):
    setUp = harness.ArcIntegrationTests.setUp
    tearDown = harness.ArcIntegrationTests.tearDown
    start_session = harness.ArcIntegrationTests.start_session
    send = harness.ArcIntegrationTests.send
    command = harness.ArcIntegrationTests.command
    wait_command = harness.ArcIntegrationTests.wait_command
    create = harness.ArcIntegrationTests.create
    start_author = harness.ArcIntegrationTests.start_author
    submit_author = harness.ArcIntegrationTests.submit_author

    def open_search(self):
        self.command("search")
        view = self.wait_command("SEARCH_OPEN")["view"]
        initial = self.wait_command("SEARCH_PRESENT", view)
        self.assertIsNone(initial["executed"])
        self.assertEqual(initial["rows"], [])
        return view

    def wait_search(self, view):
        while True:
            result = self.wait_command("SEARCH_PRESENT", view)
            if not result["pending"]:
                return result

    def run_search(self, view, criteria):
        self.send({"type": "SEARCH_RUN", "view": view, "criteria": criteria})
        self.wait_command("SEARCH_PRESENT", view)
        return self.wait_search(view)

    def save_arc(self, opened, changes):
        fields = {**core.views[opened["view"]]["draft"], **changes}
        self.send({"type": "SAVE", "view": opened["view"], "fields": fields})
        self.wait_command("BUSY", opened["view"])
        self.wait_command("UPDATE", opened["view"])
        self.wait_command("BUSY", opened["view"])

    def select(self, view, uuids):
        self.send({"type": "SEARCH_SELECT", "view": view, "uuids": uuids})
        return self.wait_command("SEARCH_PRESENT", view)

    def test_queries_refresh_without_replacing_input_and_tags_persist(self):
        arc = self.create()
        other = self.create()
        self.save_arc(arc, {"title": "Alpha coast", "tags": "Work, Home, work"})
        self.save_arc(other, {"title": "Beta coast", "tags": "Work"})
        first, second = self.open_search(), self.open_search()
        criteria = {"type": "arc", "title-contains": "ALPHA", "tags": ["work"]}
        result = self.run_search(first, criteria)
        self.assertEqual([row["uuid"] for row in result["rows"]], [arc["record"]["uuid"]])
        self.select(first, [arc["record"]["uuid"]])
        edited = {**criteria, "title-contains": "future input"}
        self.send({"type": "SEARCH_INPUT", "view": first, "criteria": edited})
        self.save_arc(arc, {"description": "New prose"})
        refreshed = self.wait_search(first)
        self.assertEqual(refreshed["selected"], [arc["record"]["uuid"]])
        self.assertEqual(search_core.views[first]["input"]["title-contains"], "future input")
        self.assertEqual(refreshed["executed"], search.validate_criteria(criteria))
        self.save_arc(arc, {"tags": "Home"})
        refreshed = self.wait_search(first)
        self.assertEqual(refreshed["rows"], [])
        self.assertEqual(refreshed["selected"], [])
        journal = self.start_author(arc["view"], "journal-entry")
        journal["fields"].update(title="Journal coast", description="A journal", tags="Home, Work", when="2024")
        self.submit_author(arc["view"], journal)
        self.wait_command("AUTHOR_BUSY", arc["view"])
        result = self.run_search(second, {"type": "journal-entry", "tags": ["WORK"]})
        self.assertEqual([row["uuid"] for row in result["rows"]], [journal["uuid"]])
        self.assertEqual(result["rows"][0]["date"], "2024")
        self.assertEqual(search_core.views[first]["input"]["title-contains"], "future input")
        self.select(second, [journal["uuid"]])
        self.send({"type": "SEARCH_OPEN_SELECTED", "view": second})
        inspection = self.wait_command("INSPECT_OPEN")
        self.assertEqual(inspection["record"]["description"], "A journal")
        self.assertEqual(inspection["record"]["associations"][0]["uuid"], arc["record"]["uuid"])
        self.send({"type": "SESSION_ASSIGN", "view": second, "assignments": [{"name": "entry", "uuid": journal["uuid"]}]})
        self.wait_command("SESSION_ASSIGNED", second)
        self.command("open entry")
        self.assertEqual(self.wait_command("INSPECT_OPEN")["record"]["uuid"], journal["uuid"])
        self.command("open " + result["rows"][0]["name"])
        self.assertEqual(self.wait_command("INSPECT_OPEN")["record"]["uuid"], journal["uuid"])
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        harness.main.finish_worker_shutdown()
        self.start_session()
        view = self.open_search()
        result = self.run_search(view, {"tags": ["work"]})
        self.assertEqual({row["uuid"] for row in result["rows"]}, {other["record"]["uuid"], journal["uuid"]})

    def test_obsolete_and_closed_query_results_are_ignored(self):
        first, second = self.create(), self.create()
        view = self.open_search()
        entered, release = Event(), Event()
        original = machine.machines["MEM"]["handlers"]["REQUEST"]

        def handle_when_search_test_holds_query():
            if mobile_stacks.get_register("request")["action"] == "search" and not entered.is_set():
                entered.set()
                if not release.wait(5):
                    raise RuntimeError("Query hold timed out")
            original()

        machine.machines["MEM"]["handlers"]["REQUEST"] = handle_when_search_test_holds_query
        try:
            self.send({"type": "SEARCH_RUN", "view": view, "criteria": {"name-contains": first["record"]["name"]}})
            self.wait_command("SEARCH_PRESENT", view)
            self.assertTrue(entered.wait(5))
            self.send({"type": "SEARCH_RUN", "view": view, "criteria": {"name-contains": second["record"]["name"]}})
            self.wait_command("SEARCH_PRESENT", view)
            release.set()
            result = self.wait_search(view)
            self.assertEqual([row["uuid"] for row in result["rows"]], [second["record"]["uuid"]])
            other = self.open_search()
            entered.clear()
            release.clear()
            self.send({"type": "SEARCH_RUN", "view": other, "criteria": {}})
            self.wait_command("SEARCH_PRESENT", other)
            self.assertTrue(entered.wait(5))
            self.send({"type": "SEARCH_CLOSE", "view": other})
            self.wait_command("SEARCH_CLOSE", other)
            release.set()
            self.assertNotIn(other, search_core.views)
            self.assertEqual(len(self.run_search(view, {})["rows"]), 2)
        finally:
            release.set()
            machine.machines["MEM"]["handlers"]["REQUEST"] = original

    def test_session_shadowing_atomic_rebinding_and_clipboard_adoption(self):
        first, second = self.create(), self.create()
        view = self.open_search()
        self.run_search(view, {})
        first_id, second_id = first["record"]["uuid"], second["record"]["uuid"]
        self.select(view, [first_id])
        name = second["record"]["name"]
        self.send({"type": "SESSION_ASSIGN", "view": view, "assignments": [{"name": name, "uuid": first_id}]})
        self.wait_command("SESSION_ASSIGNED", view)
        self.command("edit-arc " + name)
        self.assertEqual(self.wait_command("OPEN")["record"]["uuid"], first_id)
        self.command("edit-arc " + second_id.upper())
        self.assertEqual(self.wait_command("OPEN")["record"]["uuid"], second_id)
        self.select(view, [first_id, second_id])
        before = deepcopy(search_core.bindings)
        self.send({"type": "SESSION_ASSIGN", "view": view, "assignments": [
            {"name": "a", "uuid": first_id}, {"name": "a", "uuid": second_id}]})
        self.assertIn("distinct", self.wait_command("SEARCH_PRESENT", view)["status"])
        self.assertEqual(search_core.bindings, before)
        self.select(view, [second_id])
        assignment = [{"name": name, "uuid": second_id}]
        self.send({"type": "SESSION_ASSIGN", "view": view, "assignments": assignment})
        conflict = self.wait_command("SESSION_CONFLICTS", view)
        self.assertEqual(conflict["conflicts"][0]["current"], first_id)
        self.assertEqual(search_core.bindings, before)
        self.send({"type": "SESSION_ASSIGN", "view": view, "assignments": assignment, "replacements": {name: first_id}})
        self.wait_command("SESSION_ASSIGNED", view)
        self.assertEqual(search_core.bindings[name], second_id)
        self.send({"type": "SEARCH_COPY_REFERENCES", "view": view})
        self.assertEqual(json.loads(self.wait_command("SEARCH_COPY", view)["text"]), [second_id])
        payload = search.serialize_search({"type": "event", "title-contains": "coast"})
        self.send({"type": "SEARCH_CLIPBOARD", "view": view, "text": payload})
        while not self.wait_command("SEARCH_OFFER", view)["available"]:
            pass
        self.assertEqual(search_core.views[view]["input"], search.empty_criteria())
        old_rows = deepcopy(search_core.views[view]["rows"])
        self.send({"type": "SEARCH_ADOPT", "view": view, "text": payload, "mode": "reset", "criteria": search.empty_criteria()})
        adopted = self.wait_command("SEARCH_INPUT", view)
        self.assertEqual(adopted["criteria"]["type"], "event")
        self.assertEqual(search_core.views[view]["rows"], old_rows)
        self.assertFalse(search_core.views[view]["pending"])
        incoming = search.serialize_search({"type": "arc", "name-contains": "chapter"})
        self.send({"type": "SEARCH_ADOPT", "view": view, "text": incoming, "mode": "incorporate", "criteria": adopted["criteria"]})
        merge = self.wait_command("SEARCH_CONFLICTS", view)["merge"]
        self.assertEqual(search_core.views[view]["input"], adopted["criteria"])
        self.send({"type": "SEARCH_MERGE", "view": view, "token": merge["token"], "choices": {"type": "current"}})
        combined = self.wait_command("SEARCH_INPUT", view)["criteria"]
        self.assertEqual(combined["type"], "event")
        self.assertEqual(combined["name-contains"], "chapter")
        self.assertEqual(search_core.views[view]["rows"], old_rows)
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        harness.main.finish_worker_shutdown()
        self.start_session()
        self.assertEqual(search_core.bindings, {})

    def test_clipboard_errors_and_stale_incorporation_preserve_parameters(self):
        view = self.open_search()
        original = search.validate_criteria({"type": "arc", "title-contains": "current"})
        self.run_search(view, original)
        for payload in ('{broken', '{"format":"arcs-basic-search","version":9,"criteria":{}}'):
            self.send({"type": "SEARCH_ADOPT", "view": view, "mode": "reset", "text": payload, "criteria": original})
            response = self.wait_command("SEARCH_PRESENT", view)
            self.assertNotEqual(response["status"], "Search complete.")
            self.assertEqual(search_core.views[view]["input"], original)
        self.send({"type": "SEARCH_ADOPT", "view": view, "mode": "reset", "error": "Clipboard unavailable", "criteria": original})
        self.assertEqual(self.wait_command("SEARCH_PRESENT", view)["status"], "Clipboard unavailable")
        self.assertEqual(search_core.views[view]["input"], original)
        payload = search.serialize_search({"type": "event", "name-contains": "incoming"})
        self.send({"type": "SEARCH_ADOPT", "view": view, "mode": "incorporate", "text": payload, "criteria": original})
        merge = self.wait_command("SEARCH_CONFLICTS", view)["merge"]
        self.wait_command("SEARCH_PRESENT", view)
        newer = {**original, "title-contains": "new typing"}
        self.send({"type": "SEARCH_INPUT", "view": view, "criteria": newer})
        self.send({"type": "SEARCH_MERGE", "view": view, "token": merge["token"], "choices": {"type": "incoming"}})
        self.assertIn("changed", self.wait_command("SEARCH_PRESENT", view)["status"])
        self.assertEqual(search_core.views[view]["input"], newer)
        self.assertEqual(search_core.views[view]["displayed"], original)
        self.send({"type": "SEARCH_CLIPBOARD", "view": view, "text": '["00000000-0000-0000-0000-000000000001"]'})
        self.assertFalse(self.wait_command("SEARCH_OFFER", view)["available"])
        self.assertEqual(search_core.views[view]["input"], newer)

    def test_schema_two_migration_preserves_authoring_and_basic_link_metadata(self):
        arc = self.create()
        event = self.start_author(arc["view"], "event")
        event["fields"]["description"] = "Existing v2 event"
        self.submit_author(arc["view"], event)
        self.wait_command("AUTHOR_BUSY", arc["view"])
        self.send({"type": "SHUTDOWN"})
        self.wait_command("SHUTDOWN_COMPLETE")
        harness.main.finish_worker_shutdown()
        with closing(sqlite3.connect(self.database)) as connection:
            link = connection.execute("SELECT uuid FROM links").fetchone()[0]
            connection.execute("INSERT INTO basic(uuid,name,title,description,type,date) VALUES (?,?,?,?,?,?)",
                               (link, "association", "Entry membership", "Optional metadata", "link", ""))
            connection.execute("ALTER TABLE basic DROP COLUMN tags_json")
            connection.execute("PRAGMA user_version=2")
            connection.commit()
        self.start_session()
        view = self.open_search()
        result = self.run_search(view, {})
        self.assertEqual({row["uuid"] for row in result["rows"]}, {arc["record"]["uuid"], event["uuid"], link})
        self.assertTrue(all(row["tags"] == [] for row in result["rows"]))
        self.select(view, [link])
        self.send({"type": "SEARCH_OPEN_SELECTED", "view": view})
        detail = self.wait_command("INSPECT_OPEN")["record"]
        self.assertEqual(detail["link"]["from"], event["uuid"])
        self.assertEqual(detail["description"], "Optional metadata")


if __name__ == "__main__":
    unittest.main()
