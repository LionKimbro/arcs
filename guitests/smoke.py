"""Real Tk checks. Run twice: create, then reopen the same isolated database."""

import argparse
import faulthandler
from copy import deepcopy
from pathlib import Path
import sqlite3
from threading import enumerate as enumerate_threads
from time import monotonic

from arcs import core, disk, machine, main, tk

g = {"phase": 0, "deadline": None, "ids": [], "first": None,
     "second": None, "error": None, "mode": None, "database": None}


def submit(text):
    tk.widgets["entry"].focus_force()
    tk.widgets["entry"].delete(0, "end")
    tk.widgets["entry"].insert(0, text)
    tk.widgets["entry"].event_generate("<Return>")


def handle_when_gui_test_advances():
    try:
        if monotonic() > g["deadline"]:
            raise AssertionError(f"GUI phase {g['phase']} timed out")
        advance_scenario()
        if g["phase"] != 99:
            tk.g["root"].after(20, handle_when_gui_test_advances)
    except BaseException as error:
        g["error"] = error
        machine.handle_when_a_worker_dies_unexpectedly()


def advance_scenario():
    output = tk.widgets["output"].get("1.0", "end")
    phase = g["phase"]
    if phase == 0 and "Ready." in output:
        assert not tk.windows, "Startup must open only Command Center"
        entry = tk.widgets["entry"]
        assert entry.winfo_ismapped()
        assert entry.winfo_height() >= 20
        assert entry.winfo_rooty() >= tk.widgets["output"].winfo_rooty() + tk.widgets["output"].winfo_height()
        assert entry.winfo_rooty() + entry.winfo_height() <= tk.g["root"].winfo_rooty() + tk.g["root"].winfo_height()
        if g["mode"] == "reopen":
            connection = sqlite3.connect(g["database"])
            try:
                g["ids"] = [row[0] for row in connection.execute("SELECT uuid FROM arc")]
            finally:
                connection.close()
            assert len(g["ids"]) == 3
            submit("list-arcs")
            for uuid in g["ids"]:
                submit("edit-arc " + uuid)
            g["phase"] = 90
        else:
            for _ in range(3):
                submit("create-arc")
            g["phase"] = 1
    elif phase == 1 and len(tk.windows) == 3:
        g["ids"] = [view["record"]["uuid"] for view in core.views.values()]
        g["first"] = next(iter(tk.windows))
        tk.handle_when_user_closes_detail_window(g["first"])
        g["phase"] = 2
    elif phase == 2 and len(tk.windows) == 2:
        submit("edit-arc " + g["ids"][0])
        g["phase"] = 3
    elif phase == 3 and len(tk.windows) == 3:
        g["first"] = next(view_id for view_id, view in core.views.items() if view["record"]["uuid"] == g["ids"][0])
        submit("edit-arc " + g["ids"][0])
        g["phase"] = 4
    elif phase == 4 and len(tk.windows) == 4:
        g["second"] = next(view_id for view_id, view in core.views.items()
                           if view_id != g["first"] and view["record"]["uuid"] == g["ids"][0])
        first, second = tk.windows[g["first"]], tk.windows[g["second"]]
        second["variables"]["title"].set("Independent draft")
        first["variables"]["title"].set("A persisted passage")
        first["variables"]["name"].set("persisted-passage")
        first["variables"]["begin"].set("2020-04")
        first["variables"]["end"].set("ONGOING")
        first["description"].insert("1.0", "A story that persists after restart.")
        tk.handle_when_user_saves_arc_draft(g["first"])
        g["phase"] = 5
    elif phase == 5 and "revision 2" in output:
        assert tk.windows[g["second"]]["variables"]["title"].get() == "Independent draft"
        assert tk.windows[g["second"]]["base-revision"] == 1
        assert tk.windows[g["first"]]["window"].title() == "A persisted passage — Arcs"
        tk.handle_when_user_saves_arc_draft(g["second"])
        g["phase"] = 6
    elif phase == 6 and "Save conflict" in output:
        assert tk.windows[g["second"]]["variables"]["title"].get() == "Independent draft"
        tk.messagebox.askyesno = lambda *args, **kwargs: True
        tk.messagebox.askyesnocancel = lambda *args, **kwargs: False
        tk.handle_when_user_reloads_saved_arc(g["second"])
        g["phase"] = 7
    elif phase == 7 and tk.windows[g["second"]]["status"].get() == "Reloaded saved data.":
        assert tk.windows[g["second"]]["variables"]["title"].get() == "A persisted passage"
        assert tk.windows[g["second"]]["base-revision"] == 2
        assert not tk.has_unsaved_draft(g["first"])
        # A refresh already queued by Core must preserve typing made before Tk realizes it.
        expected = tk.get_view_fields(g["second"])
        tk.windows[g["second"]]["variables"]["title"].set("Typing after refresh was queued")
        refreshed = deepcopy(core.views[g["second"]]["record"])
        refreshed["revision"] = 3
        tk.realize_core_command({"type": "UPDATE", "view": g["second"], "record": refreshed,
                                 "fields": expected, "saved-fields": expected,
                                 "expected-fields": expected, "status": "Saved."})
        assert tk.get_view_fields(g["second"])["title"] == "Typing after refresh was queued"
        assert tk.windows[g["second"]]["base-revision"] == 2
        tk.messagebox.askyesnocancel = lambda *args, **kwargs: None
        submit("exit")
        g["phase"] = 8
    elif phase == 8 and "> exit" in output:
        assert not tk.g["closing"]
        assert tk.get_view_fields(g["second"])["title"] == "Typing after refresh was queued"
        tk.messagebox.askyesnocancel = lambda *args, **kwargs: False
        submit("EXIT")
        g["phase"] = 99
    elif phase == 90 and len(tk.windows) == 3:
        assert all(uuid in output for uuid in g["ids"])
        saved = next(window for window in tk.windows.values() if window["base"]["name"] == "persisted-passage")
        assert saved["base"]["begin"] == "2020-04"
        assert saved["base"]["description"] == "A story that persists after restart."
        submit("exit")
        g["phase"] = 99


def main_test():
    faulthandler.dump_traceback_later(20)
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "reopen"))
    parser.add_argument("database", type=Path)
    options = parser.parse_args()
    g.update(mode=options.mode, database=options.database, deadline=monotonic() + 15)
    disk.initialize_database_location(options.database)
    main.initialize_workers_and_wire_queues()
    tk.build_command_center_before_workers_start()
    main.start_permanent_workers_in_reference_order()
    tk.g["root"].after(30, handle_when_gui_test_advances)
    tk.run_tk_machine()
    main.finish_worker_shutdown()
    if g["error"]:
        raise g["error"]
    assert g["phase"] == 99
    assert not machine.a_thread_died_unexpectedly.is_set()
    assert disk.g["connection"] is None
    assert not any(thread.name.startswith("Arcs ") for thread in enumerate_threads())
    print("Real Tk", options.mode, "passed")


if __name__ == "__main__":
    main_test()
