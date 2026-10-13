"""Real search windows, clipboard transfers, naming dialogs, and worker shutdown."""

import argparse
import json
from pathlib import Path
from threading import Event, enumerate as enumerate_threads
from time import monotonic
import tkinter
from tkinter import ttk
from copying import double_click

from arcs import core, disk, machine, main, mobile_stacks, search, search_core, search_ui, tk

g = {"phase": 0, "deadline": None, "error": None, "arc-view": None, "other-view": None,
     "arc": None, "other": None, "event": None, "first": None, "second": None,
     "conflicts": 0, "choice": None, "clipboard": None, "release": None, "held": None}


def submit(text):
    entry = tk.widgets["entry"]
    entry.focus_force()
    entry.delete(0, "end")
    entry.insert(0, text)
    entry.event_generate("<Return>")


def find_button(parent, title):
    for child in parent.winfo_children():
        if isinstance(child, (ttk.Button, ttk.Checkbutton)) and child.cget("text") == title:
            return child
        found = find_button(child, title)
        if found:
            return found
    return None


def set_query(view_id, fields):
    for key, value in fields.items():
        search_ui.windows[view_id]["variables"][key].set(value)


def tick_row(view_id, uuid):
    tree = search_ui.windows[view_id]["tree"]
    tree.see(uuid)
    tree.update_idletasks()
    box = tree.bbox(uuid, "checked")
    assert box
    tree.event_generate("<Button-1>", x=box[0] + 8, y=box[1] + 8)
    tree.event_generate("<ButtonRelease-1>", x=box[0] + 8, y=box[1] + 8)


def handle_when_test_answers_search_conflict(*args, **kwargs):
    g["conflicts"] += 1
    return g["choice"]


def restore_clipboard():
    tk.g["root"].clipboard_clear()
    if g["clipboard"] is not None:
        tk.g["root"].clipboard_append(g["clipboard"])


def has_copied_reference(uuid):
    try:
        return json.loads(tk.g["root"].clipboard_get()) == [uuid]
    except (ValueError, tkinter.TclError):
        return False


def handle_when_searching_test_advances():
    try:
        if monotonic() > g["deadline"]:
            raise AssertionError(f"Search GUI phase {g['phase']} timed out")
        advance_scenario()
        if g["phase"] != 99:
            tk.g["root"].after(20, handle_when_searching_test_advances)
    except BaseException as error:
        g["error"] = error
        if g["release"]:
            g["release"].set()
        restore_clipboard()
        machine.handle_when_a_worker_dies_unexpectedly()


def advance_scenario():
    phase = g["phase"]
    output = tk.widgets["output"].get("1.0", "end")
    first = search_ui.windows.get(g["first"])
    second = search_ui.windows.get(g["second"])
    if phase == 0 and "Ready." in output and tk.widgets["entry"].winfo_ismapped():
        submit("create-arc")
        submit("create-arc")
        g["phase"] = 1
    elif phase == 1 and len(tk.windows) == 2:
        g["arc-view"], g["other-view"] = list(tk.windows)
        for view_id, title, name, tags in ((g["arc-view"], "Coastal move", "coastal-move", "Home, Change"),
                                           (g["other-view"], "Second passage", "second-passage", "Work")):
            window = tk.windows[view_id]
            window["variables"]["title"].set(title)
            window["variables"]["name"].set(name)
            window["variables"]["tags"].set(tags)
            window["save"].invoke()
        g["phase"] = 2
    elif phase == 2 and all(window["base-revision"] == 2 and not window["header-pending"] for window in tk.windows.values()):
        g["arc"] = next(view["record"]["uuid"] for view in core.views.values()
                        if view["record"]["name"] == "coastal-move")
        g["other"] = next(view["record"]["uuid"] for view in core.views.values()
                          if view["record"]["name"] == "second-passage")
        find_button(tk.windows[g["arc-view"]]["window"], "New event").invoke()
        g["phase"] = 3
    elif phase == 3 and tk.windows[g["arc-view"]]["author"]:
        window = tk.windows[g["arc-view"]]
        for key, value in (("title", "Keys collected"), ("when", "2024-08-30"), ("tags", "Home")):
            window["author-variables"][key].set(value)
        window["author-texts"]["description"].insert("1.0", "Collected the keys and began moving in.")
        g["event"] = window["author"]["uuid"]
        next(button for button in window["author-controls"]
             if isinstance(button, ttk.Button) and button.cget("text") == "Save").invoke()
        g["phase"] = 4
    elif phase == 4 and tk.windows[g["arc-view"]]["author"] is None:
        submit("search")
        submit("search")
        g["phase"] = 5
    elif phase == 5 and len(search_ui.windows) == 2:
        g["first"], g["second"] = list(search_ui.windows)
        assert all(window["rows"] == [] and window["executed"] is None for window in search_ui.windows.values())
        set_query(g["first"], {"type": "arc", "title-contains": "COAST", "tags": "home"})
        set_query(g["second"], {"type": "event", "title-contains": "keys", "tags": "HOME"})
        search_ui.windows[g["first"]]["controls"]["Search"].invoke()
        search_ui.windows[g["second"]]["controls"]["Search"].invoke()
        g["phase"] = 6
    elif phase == 6 and first["rows"] and second["rows"]:
        assert [row["uuid"] for row in first["rows"]] == [g["arc"]]
        assert [row["uuid"] for row in second["rows"]] == [g["event"]]
        tick_row(g["first"], g["arc"])
        find_button(second["window"], "Select all returned objects").invoke()
        g["phase"] = 7
    elif phase == 7 and first["selected"] == [g["arc"]] and second["selected"] == [g["event"]]:
        assert str(first["open"].cget("state")) == "normal"
        second["open"].invoke()
        first["copy"].invoke()
        g["phase"] = 8
    elif phase == 8 and search_ui.inspections and has_copied_reference(g["arc"]):
        assert json.loads(tk.g["root"].clipboard_get()) == [g["arc"]]
        inspection = next(iter(search_ui.inspections.values()))
        assert "Collected the keys" in inspection["body"].get("1.0", "end")
        first["tree"].xview_moveto(1.0)
        first["tree"].update_idletasks()
        box = first["tree"].bbox(g["arc"], "uuid")
        double_click(first["tree"], (box[0] + 8, box[1] + 8))
        assert tk.g["root"].clipboard_get() == g["arc"]
        assert first["selected"] == [g["arc"]]
        first["name"].invoke()
        first["name-variables"][g["arc"]].set("a")
        find_button(first["name-dialog"], "Assign names").invoke()
        g["phase"] = 9
    elif phase == 9 and search_core.bindings.get("a") == g["arc"] and first["name-dialog"] is None:
        submit("edit-arc a")
        g["phase"] = 10
    elif phase == 10 and len(tk.windows) == 3:
        assert len(search_ui.windows) == 2
        set_query(g["first"], {"title-contains": "No match"})
        assert first["rows"][0]["uuid"] == g["arc"]
        assert "Parameters changed" in first["caption"].get()
        first["controls"]["Copy search"].invoke()
        second["window"].focus_force()
        g["phase"] = 11
    elif phase == 11 and '"No match"' in tk.g["root"].clipboard_get():
        payload = json.loads(tk.g["root"].clipboard_get())
        assert payload["format"] == "arcs-basic-search" and payload["version"] == 1
        assert search_ui.read_criteria(g["second"])["type"] == "event"
        find_button(second["offer"], "Reset to clipboard search").invoke()
        g["phase"] = 12
    elif phase == 12 and search_ui.read_criteria(g["second"])["title-contains"] == "No match":
        assert second["rows"][0]["uuid"] == g["event"]
        assert second["executed"]["type"] == "event"
        second["controls"]["Clear parameters"].invoke()
        assert search_ui.read_criteria(g["second"]) == search.empty_criteria()
        assert first["variables"]["title-contains"].get() == "No match"
        set_query(g["second"], {"type": "event", "title-contains": "keys"})
        tk.g["root"].clipboard_clear()
        tk.g["root"].clipboard_append(search.serialize_search({"type": "arc", "title-contains": "coast", "name-contains": "coast"}))
        search_ui.messagebox.askyesnocancel = handle_when_test_answers_search_conflict
        g["choice"] = None
        find_button(second["offer"], "Incorporate…").invoke()
        g["phase"] = 13
    elif phase == 13 and g["conflicts"] == 1:
        assert search_ui.read_criteria(g["second"])["type"] == "event"
        assert search_ui.read_criteria(g["second"])["name-contains"] == ""
        assert search_ui.read_criteria(g["second"])["title-contains"] == "keys"
        g["choice"] = False
        find_button(second["offer"], "Incorporate…").invoke()
        g["phase"] = 14
    elif phase == 14 and search_ui.read_criteria(g["second"])["name-contains"] == "coast":
        assert search_ui.read_criteria(g["second"])["type"] == "event"
        assert search_ui.read_criteria(g["second"])["title-contains"] == "keys"
        assert second["rows"][0]["uuid"] == g["event"]
        second["controls"]["Clear parameters"].invoke()
        set_query(g["second"], {"type": "arc"})
        second["controls"]["Search"].invoke()
        g["phase"] = 15
    elif phase == 15 and len(second["rows"]) == 2 and second["executed"]["type"] == "arc":
        assert second["selected"] == []
        find_button(second["window"], "Select all returned objects").invoke()
        g["phase"] = 16
    elif phase == 16 and len(second["selected"]) == 2:
        assert str(second["open"].cget("state")) == "disabled"
        second["copy"].invoke()
        second["name"].invoke()
        for variable in second["name-variables"].values():
            variable.set("duplicate")
        find_button(second["name-dialog"], "Assign names").invoke()
        g["phase"] = 17
    elif phase == 17 and "distinct" in second["name-status"].get():
        assert "duplicate" not in search_core.bindings
        assert json.loads(tk.g["root"].clipboard_get()) == second["selected"]
        second["name-variables"][g["arc"]].set("b")
        second["name-variables"][g["other"]].set("a")
        find_button(second["name-dialog"], "Assign names").invoke()
        g["phase"] = 18
    elif phase == 18 and second["binding-dialog"]:
        assert search_core.bindings == {"a": g["arc"]}
        find_button(second["binding-dialog"], "Cancel").invoke()
        assert search_core.bindings == {"a": g["arc"]}
        find_button(second["name-dialog"], "Assign names").invoke()
        g["phase"] = 181
    elif phase == 181 and second["binding-dialog"]:
        find_button(second["binding-dialog"], "Replace bindings and assign names").invoke()
        g["phase"] = 19
    elif phase == 19 and search_core.bindings.get("a") == g["other"] and second["name-dialog"] is None:
        assert search_core.bindings["b"] == g["arc"]
        window = tk.windows[g["arc-view"]]
        window["description"].insert("1.0", "Updated domain prose")
        window["save"].invoke()
        g["phase"] = 20
    elif phase == 20 and "Results refreshed" in first["status"].get() and not tk.windows[g["arc-view"]]["header-pending"]:
        assert first["selected"] == [g["arc"]]
        assert first["variables"]["title-contains"].get() == "No match"
        assert first["executed"]["title-contains"] == "COAST"
        assert len(second["selected"]) == 2
        set_query(g["first"], {"title-contains": "Second", "tags": ""})
        first["controls"]["Search"].invoke()
        g["phase"] = 21
    elif phase == 21 and first["rows"] and first["rows"][0]["uuid"] == g["other"]:
        assert first["selected"] == []
        original = machine.machines["MEM"]["handlers"]["REQUEST"]
        g["release"], g["held"] = Event(), Event()

        def handle_when_searching_test_holds_query():
            if mobile_stacks.get_register("request")["action"] == "search":
                g["held"].set()
                if not g["release"].wait(4):
                    raise RuntimeError("GUI did not release the held query")
                machine.machines["MEM"]["handlers"]["REQUEST"] = original
            original()

        machine.machines["MEM"]["handlers"]["REQUEST"] = handle_when_searching_test_holds_query
        first["controls"]["Search"].invoke()
        g["phase"] = 22
    elif phase == 22 and g["held"].is_set():
        first["window"].tk.call(first["window"].protocol("WM_DELETE_WINDOW"))
        tk.g["root"].after(150, g["release"].set)
        g["phase"] = 23
    elif phase == 23 and g["first"] not in search_ui.windows and g["release"].is_set():
        assert g["first"] not in search_core.views
        assert search_core.bindings["a"] == g["other"]
        second["controls"]["Search"].invoke()
        g["phase"] = 24
    elif phase == 24 and len(second["rows"]) == 2 and not search_core.views[g["second"]]["pending"]:
        assert len(search_ui.windows) == 1
        assert not machine.a_thread_died_unexpectedly.is_set()
        restore_clipboard()
        submit("exit")
        g["phase"] = 99


def main_test():
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    options = parser.parse_args()
    g["deadline"] = monotonic() + 25
    disk.initialize_database_location(options.database)
    main.initialize_workers_and_wire_queues()
    tk.build_command_center_before_workers_start()
    try:
        g["clipboard"] = tk.g["root"].clipboard_get()
    except tkinter.TclError:
        pass
    main.start_permanent_workers_in_reference_order()
    tk.g["root"].after(30, handle_when_searching_test_advances)
    tk.run_tk_machine()
    main.finish_worker_shutdown()
    if g["error"]:
        raise g["error"]
    assert g["phase"] == 99
    assert not machine.a_thread_died_unexpectedly.is_set()
    assert disk.g["connection"] is None
    assert not any(thread.name.startswith("Arcs ") for thread in enumerate_threads())
    print("Real Tk Basic Search passed")


if __name__ == "__main__":
    main_test()
