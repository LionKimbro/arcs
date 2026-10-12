"""Exercise native authoring buttons, navigation prompts, and persistence."""

import argparse
from pathlib import Path
import sqlite3
from threading import Event, enumerate as enumerate_threads
from time import monotonic
from tkinter import ttk

from arcs import author_ui, disk, machine, main, tk

g = {"phase": 0, "deadline": None, "first": None, "second": None, "other": None,
     "arc": None, "journal": None, "transition": None, "successor": None,
     "error": None, "mode": None, "database": None, "release": None}


def submit(text):
    entry = tk.widgets["entry"]
    entry.focus_force()
    entry.insert(0, text)
    entry.event_generate("<Return>")


def click_start(view_id, label):
    next(button for button in tk.windows[view_id]["author-buttons"] if button.cget("text") == label).invoke()


def click_editor(view_id, label):
    next(button for button in tk.windows[view_id]["author-controls"]
         if isinstance(button, ttk.Button) and button.cget("text") == label).invoke()


def fill(view_id, fields):
    window = tk.windows[view_id]
    for key, value in fields.items():
        if key in window["author-variables"]:
            window["author-variables"][key].set(value)
        else:
            window["author-texts"][key].delete("1.0", "end")
            window["author-texts"][key].insert("1.0", value)


def get_items(view_id):
    return tk.windows[view_id]["tree"].get_children()


def handle_when_authoring_test_advances():
    try:
        if monotonic() > g["deadline"]:
            raise AssertionError(f"Authoring GUI phase {g['phase']} timed out")
        advance_scenario()
        if g["phase"] != 99:
            tk.g["root"].after(20, handle_when_authoring_test_advances)
    except BaseException as error:
        g["error"] = error
        if g["release"]:
            g["release"].set()
        machine.handle_when_a_worker_dies_unexpectedly()


def advance_scenario():
    phase = g["phase"]
    output = tk.widgets["output"].get("1.0", "end")
    first = tk.windows.get(g["first"])
    if phase == 0 and "Ready." in output:
        assert not tk.windows
        if g["mode"] == "reopen":
            connection = sqlite3.connect(g["database"])
            try:
                g["arc"] = connection.execute("SELECT uuid FROM arc WHERE end_event IS NOT NULL").fetchone()[0]
                g["successor"] = connection.execute("SELECT uuid FROM basic WHERE title='New passage'").fetchone()[0]
            finally:
                connection.close()
            submit("edit-arc " + g["arc"])
            submit("edit-arc " + g["successor"])
            g["phase"] = 90
        else:
            submit("create-arc")
            submit("create-arc")
            g["phase"] = 1
    elif phase == 1 and len(tk.windows) == 2:
        g["first"], g["other"] = list(tk.windows)
        g["arc"] = next(line.split("Saved ")[1].split(" ")[0] for line in output.splitlines() if line.startswith("Saved "))
        submit("edit-arc " + g["arc"])
        g["phase"] = 2
    elif phase == 2 and len(tk.windows) == 3:
        g["second"] = next(view_id for view_id in tk.windows if view_id not in (g["first"], g["other"]))
        assert len(first["author-buttons"]) == 3
        click_start(g["first"], "New journal entry")
        g["phase"] = 3
    elif phase == 3 and first["author"]:
        fill(g["first"], {"description": "Journal prose visible in the detail pane.", "when": "2025-03-04"})
        g["journal"] = first["author"]["uuid"]
        click_editor(g["first"], "Save")
        g["phase"] = 4
    elif phase == 4 and first["author"] is None and len(get_items(g["first"])) == 1:
        assert first["selected"] == g["journal"]
        text = next(child for child in first["detail"].winfo_children() if child.winfo_class() == "Text")
        assert "Journal prose" in text.get("1.0", "end")
        tk.windows[g["second"]]["tree"].selection_set(g["journal"])
        g["phase"] = 5
    elif phase == 5 and tk.windows[g["second"]]["selected"] == g["journal"]:
        click_start(g["second"], "New event")
        click_start(g["first"], "New event")
        g["phase"] = 6
    elif phase == 6 and first["author"] and tk.windows[g["second"]]["author"]:
        fill(g["second"], {"description": "The other view's unsaved event."})
        fill(g["first"], {"description": "A backdated event", "when": "2000", "earliest": "1999", "latest": "2001"})
        click_editor(g["first"], "Save")
        g["phase"] = 7
    elif phase == 7 and first["author"] is None and len(get_items(g["first"])) == 2:
        assert get_items(g["first"])[0] == g["journal"]
        assert author_ui.get_author_fields(g["second"])["description"] == "The other view's unsaved event."
        assert len(get_items(g["second"])) == 2
        assert not get_items(g["other"])
        click_editor(g["second"], "Cancel")
        click_start(g["other"], "New event")
        g["phase"] = 8
    elif phase == 8 and tk.windows[g["other"]]["author"] and tk.windows[g["second"]]["author"] is None:
        assert tk.windows[g["second"]]["selected"] == g["journal"]
        fill(g["other"], {"description": "An event with unknown occurrence time."})
        click_editor(g["other"], "Save")
        click_start(g["first"], "Transition to another arc")
        g["phase"] = 9
    elif phase == 9 and first["author"] and tk.windows[g["other"]]["author"] is None:
        fill(g["first"], {"description": "A defining change", "when": "2004-05", "notes": "Remembered to the month.",
                           "successor-title": "New passage", "successor-name": "new-passage",
                           "successor-description": "The next story."})
        g["transition"] = first["author"]["uuid"]
        g["successor"] = first["author"]["successor"]
        original = machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"]

        def handle_when_gui_test_rejects_via():
            connection = disk.g["connection"]
            connection.execute("CREATE TEMP TRIGGER reject_via BEFORE INSERT ON links WHEN NEW.type='via' "
                               "BEGIN SELECT RAISE(ABORT,'GUI transition failure'); END")
            try:
                original()
            finally:
                connection.execute("DROP TRIGGER reject_via")
                machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"] = original

        machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"] = handle_when_gui_test_rejects_via
        click_editor(g["first"], "Save")
        click_editor(g["first"], "Save")
        g["phase"] = 10
    elif phase == 10 and not first["author-pending"] and "GUI transition failure" in first["author-status"].get():
        assert first["author"]["uuid"] == g["transition"]
        assert author_ui.get_author_fields(g["first"])["successor-title"] == "New passage"
        assert len(get_items(g["first"])) == 2
        click_editor(g["first"], "Save")
        g["phase"] = 11
    elif phase == 11 and first["author"] is None and len(get_items(g["first"])) == 3:
        assert len(tk.windows) == 3, "Transition should stay in predecessor view"
        assert first["selected"] == g["transition"]
        assert first["variables"]["end"].get() == "2004-05"
        assert tk.windows[g["second"]]["selected"] == g["journal"]
        button = next(child for child in first["detail"].winfo_children()
                      if isinstance(child, ttk.Button) and child.cget("text") == "Open successor arc")
        button.invoke()
        g["phase"] = 12
    elif phase == 12 and len(tk.windows) == 4:
        successor = next(window for window in tk.windows.values() if window["base"]["name"] == "new-passage")
        assert successor["variables"]["begin"].get() == "2004-05"
        assert successor["variables"]["end"].get() == "ONGOING"
        assert successor["tree"].get_children() == (g["transition"],)
        click_start(g["first"], "New event")
        g["phase"] = 13
    elif phase == 13 and first["author"]:
        fill(g["first"], {"description": "Draft for navigation choices"})
        old_uuid = first["author"]["uuid"]
        tk.messagebox.askyesnocancel = lambda *args, **kwargs: None
        click_start(g["first"], "New journal entry")
        assert first["author"]["uuid"] == old_uuid
        tk.messagebox.askyesnocancel = lambda *args, **kwargs: False
        click_start(g["first"], "New journal entry")
        g["phase"] = 14
    elif phase == 14 and first["author"] and first["author"]["kind"] == "journal-entry":
        fill(g["first"], {"description": "Saved before navigating", "when": "2024-06-01T12:34:00-07:00"})
        tk.messagebox.askyesnocancel = lambda *args, **kwargs: True
        first["tree"].selection_set(g["journal"])
        g["phase"] = 15
    elif phase == 15 and first["author"] is None and len(get_items(g["first"])) == 4 and first["selected"] == g["journal"]:
        click_start(g["first"], "New journal entry")
        g["phase"] = 16
    elif phase == 16 and first["author"]:
        fill(g["first"], {"description": "Close waits for this journal save", "when": "2026-01"})
        original = machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"]
        g["release"] = Event()

        def handle_when_gui_test_holds_authoring_save():
            if not g["release"].wait(4):
                raise RuntimeError("GUI did not release its held save")
            original()

        machine.machines["DISK"]["handlers"]["AUTHOR_WRITE"] = handle_when_gui_test_holds_authoring_save
        click_editor(g["first"], "Save")
        tk.handle_when_user_closes_command_center()
        tk.g["root"].after(150, g["release"].set)
        g["phase"] = 99
    elif phase == 90 and len(tk.windows) == 2:
        predecessor = next(view_id for view_id, window in tk.windows.items() if window["base"]["title"] != "New passage")
        successor = next(view_id for view_id in tk.windows if view_id != predecessor)
        if len(get_items(predecessor)) != 5 or len(get_items(successor)) != 1:
            return
        assert tk.windows[successor]["base"]["end"] == "ONGOING"
        tk.handle_when_user_closes_command_center()
        g["phase"] = 99


def main_test():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "reopen"))
    parser.add_argument("database", type=Path)
    options = parser.parse_args()
    g.update(mode=options.mode, database=options.database, deadline=monotonic() + 25)
    disk.initialize_database_location(options.database)
    main.initialize_workers_and_wire_queues()
    tk.build_command_center_before_workers_start()
    main.start_permanent_workers_in_reference_order()
    tk.g["root"].after(30, handle_when_authoring_test_advances)
    tk.run_tk_machine()
    main.finish_worker_shutdown()
    if g["error"]:
        raise g["error"]
    assert g["phase"] == 99
    assert not machine.a_thread_died_unexpectedly.is_set()
    assert not any(thread.name.startswith("Arcs ") for thread in enumerate_threads())
    print("Real Tk authoring", options.mode, "passed")


if __name__ == "__main__":
    main_test()
