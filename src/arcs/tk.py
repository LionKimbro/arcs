"""Main-thread windows and semantic input hooks."""

from queue import Empty
import tkinter as tkinter
from tkinter import messagebox, ttk
import traceback

from . import author_ui, machine

g = {"root": None, "incoming": None, "outgoing": None, "closing": False}
widgets = {}
windows = {}


def send(event):
    if not g["closing"]:
        g["outgoing"].put(event)


def enqueue_core_command_and_wake_tk(command):
    if machine.a_thread_died_unexpectedly.is_set():
        return
    g["incoming"].put(command)
    g["root"].event_generate("<<CoreMailAvailable>>", when="tail")


def build_command_center_before_workers_start():
    g["closing"] = False
    widgets.clear()
    windows.clear()
    root = tkinter.Tk()
    root.report_callback_exception = lambda *exception: handle_when_tk_callback_fails(exception)
    g["root"] = root
    root.title("Arcs — Command Center")
    root.geometry("820x480")
    root.minsize(500, 300)
    root.protocol("WM_DELETE_WINDOW", handle_when_user_closes_command_center)
    root.bind("<<CoreMailAvailable>>", handle_when_core_mail_arrives)
    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    ttk.Label(frame, text="ARCS / Command Center", font=("Segoe UI", 15, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 8))
    output_frame = ttk.Frame(frame)
    output_frame.grid(row=1, column=0, sticky="nsew")
    output = tkinter.Text(output_frame, wrap="word", state="disabled", font=("Consolas", 11))
    scrollbar = ttk.Scrollbar(output_frame, command=output.yview)
    output.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    output.pack(fill="both", expand=True)
    ttk.Label(frame, text="Command — press Enter to submit").grid(
        row=2, column=0, sticky="w", pady=(10, 4))
    entry = tkinter.Entry(frame, font=("Consolas", 12))
    entry.grid(row=3, column=0, sticky="ew")
    entry.bind("<Return>", handle_when_user_submits_command)
    entry.focus_set()
    widgets.update(output=output, entry=entry)


def handle_when_user_submits_command(event):
    text = widgets["entry"].get()
    widgets["entry"].delete(0, "end")
    send({"type": "COMMAND", "text": text})
    return "break"


def get_view_fields(view_id):
    window = windows[view_id]
    return {**{key: variable.get() for key, variable in window["variables"].items()},
            "description": window["description"].get("1.0", "end-1c")}


def has_unsaved_draft(view_id):
    return get_view_fields(view_id) != windows[view_id]["base"]


def handle_when_user_changes_arc_fields(view_id):
    window = windows.get(view_id)
    if window is None or window["installing"]:
        return
    window["description"].edit_modified(False)
    send({"type": "DRAFT", "view": view_id, "fields": get_view_fields(view_id)})
    if has_unsaved_draft(view_id):
        window["status"].set("Unsaved draft.")


def handle_when_user_saves_arc_draft(view_id):
    send({"type": "SAVE", "view": view_id, "fields": get_view_fields(view_id),
          "base": windows[view_id]["base-revision"]})


def handle_when_user_reloads_saved_arc(view_id):
    if has_unsaved_draft(view_id) and not messagebox.askyesno(
            "Discard draft?", "Discard this window's unsaved draft and reload saved data?",
            parent=windows[view_id]["window"]):
        return
    send({"type": "RELOAD", "view": view_id, "fields": get_view_fields(view_id)})


def handle_when_user_closes_detail_window(view_id):
    author_ui.request_navigation(view_id, {"kind": "close"})


def handle_when_user_closes_command_center():
    if g["closing"]:
        return
    saves = []
    for view_id, window in windows.items():
        if has_unsaved_draft(view_id) and not window["header-pending"]:
            choice = messagebox.askyesnocancel("Unsaved arc fields", "Save arc fields before closing Arcs?\n"
                                              "Yes: Save; No: Discard; Cancel: Stay here.", parent=window["window"])
            if choice is None:
                return
            if choice:
                saves.append({"type": "SAVE", "view": view_id, "fields": get_view_fields(view_id),
                              "base": window["base-revision"]})
        if author_ui.has_author_changes(view_id) and not window["author-pending"]:
            choice = messagebox.askyesnocancel("Unsaved record", "Save this record before closing Arcs?\n"
                                              "Yes: Save; No: Discard; Cancel: Stay here.", parent=window["window"])
            if choice is None:
                return
            if choice:
                saves.append({"type": "AUTHOR_SAVE", "view": view_id, "uuid": window["author"]["uuid"],
                              "fields": author_ui.get_author_fields(view_id)})
    for event in saves:
        send(event)
    g["closing"] = True
    widgets["entry"].configure(state="disabled")
    for window in windows.values():
        window["save"].configure(state="disabled")
        window["reload"].configure(state="disabled")
        for control in window.get("author-controls", []) + window["author-buttons"]:
            control.configure(state="disabled")
    g["outgoing"].put({"type": "SHUTDOWN"})


def build_arc_detail_window(command):
    view_id = command["view"]
    window = tkinter.Toplevel(g["root"])
    window.geometry("1060x820")
    window.minsize(780, 620)
    window.protocol("WM_DELETE_WINDOW", lambda: handle_when_user_closes_detail_window(view_id))
    frame = ttk.Frame(window, padding=16)
    frame.pack(fill="both", expand=True)
    variables = {key: tkinter.StringVar(window) for key in ("title", "name", "begin", "end")}
    header = ttk.Frame(frame)
    header.pack(fill="x")
    header.columnconfigure(1, weight=1)
    for row, key in enumerate(("title", "name", "begin", "end")):
        ttk.Label(header, text=key.capitalize()).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=3)
        entry = ttk.Entry(header, textvariable=variables[key], font=("Segoe UI", 12))
        entry.grid(row=row, column=1, sticky="ew", pady=3)
    ttk.Label(frame, text="Boundaries: YYYY / YYYY-MM / YYYY-MM-DD / UNKNOWN; end also accepts ONGOING.").pack(anchor="w", pady=6)
    ttk.Label(frame, text=command["record"]["uuid"], foreground="#666666").pack(anchor="w")
    boundary_actions = ttk.Frame(frame)
    boundary_actions.pack(fill="x")
    ttk.Label(frame, text="Description").pack(anchor="w", pady=(10, 4))
    description = tkinter.Text(frame, height=5, wrap="word", font=("Segoe UI", 11), undo=True)
    description.pack(fill="x")
    actions = ttk.Frame(frame)
    actions.pack(fill="x", pady=10)
    save = ttk.Button(actions, text="Save", command=lambda: handle_when_user_saves_arc_draft(view_id))
    save.pack(side="left")
    reload_button = ttk.Button(actions, text="Reload saved", command=lambda: handle_when_user_reloads_saved_arc(view_id))
    reload_button.pack(side="left", padx=8)
    status = tkinter.StringVar(window)
    ttk.Label(actions, textvariable=status).pack(side="left", padx=8)
    author_actions = ttk.Frame(frame)
    author_actions.pack(fill="x", pady=(0, 8))
    author_buttons = []
    for label, kind in (("New journal entry", "journal-entry"), ("New event", "event"),
                        ("Transition to another arc", "transition")):
        button = ttk.Button(author_actions, text=label,
                            command=lambda kind=kind: author_ui.handle_when_user_starts_record(view_id, kind))
        button.pack(side="left", padx=(0, 8))
        author_buttons.append(button)
    panes = ttk.Panedwindow(frame, orient="horizontal")
    panes.pack(fill="both", expand=True)
    chronology = ttk.Frame(panes, padding=12)
    detail = ttk.Frame(panes, padding=12)
    panes.add(chronology, weight=1)
    panes.add(detail, weight=2)
    ttk.Label(chronology, text="Chronology", font=("Segoe UI", 12, "bold")).pack(anchor="w")
    empty_label = ttk.Label(chronology, text="No events or journal entries yet.", wraplength=260)
    empty_label.pack(anchor="w", pady=4)
    tree_frame = ttk.Frame(chronology)
    tree_frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(tree_frame, columns=("kind", "when"), show="tree headings", selectmode="browse")
    tree.heading("#0", text="Record")
    tree.heading("kind", text="Kind")
    tree.heading("when", text="Occurrence")
    tree.column("#0", width=180, minwidth=100)
    tree.column("kind", width=80, minwidth=60)
    tree.column("when", width=120, minwidth=80)
    tree_scroll = ttk.Scrollbar(tree_frame, command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)
    tree_scroll.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)
    horizontal = ttk.Scrollbar(chronology, orient="horizontal", command=tree.xview)
    horizontal.pack(fill="x")
    tree.configure(xscrollcommand=horizontal.set)
    tree.bind("<<TreeviewSelect>>", lambda _: author_ui.handle_when_user_selects_chronology(view_id))
    detail_actions = ttk.Frame(detail)
    detail_actions.pack(fill="x", pady=(0, 6))
    detail_canvas = tkinter.Canvas(detail, highlightthickness=0)
    detail_scroll = ttk.Scrollbar(detail, command=detail_canvas.yview)
    detail_scroll.pack(side="right", fill="y")
    detail_canvas.configure(yscrollcommand=detail_scroll.set)
    detail_canvas.pack(fill="both", expand=True)
    detail_body = ttk.Frame(detail_canvas, padding=4)
    detail_item = detail_canvas.create_window((0, 0), window=detail_body, anchor="nw")
    detail_body.bind("<Configure>", lambda _: detail_canvas.configure(scrollregion=detail_canvas.bbox("all")))
    detail_canvas.bind("<Configure>", lambda event: detail_canvas.itemconfigure(detail_item, width=event.width))
    windows[view_id] = {"window": window, "variables": variables, "description": description,
                        "status": status, "save": save, "reload": reload_button,
                        "installing": False, "base": command["fields"],
                        "base-revision": command["record"]["revision"], "header-pending": False,
                        "author": None, "author-pending": False, "author-buttons": author_buttons,
                        "author-controls": [], "selected": None, "tree": tree,
                        "empty-label": empty_label, "detail": detail_body, "detail-canvas": detail_canvas,
                        "detail-actions": detail_actions, "boundary-actions": boundary_actions}
    install_view_presentation({**command, "status": "Saved."})
    author_ui.install_record_details({"view": view_id, "record": None})
    for variable in variables.values():
        variable.trace_add("write", lambda *_: handle_when_user_changes_arc_fields(view_id))
    description.bind("<<Modified>>", lambda _: handle_when_user_changes_arc_fields(view_id)
                     if description.edit_modified() else None)


def install_view_presentation(command):
    window = windows[command["view"]]
    window["window"].title(command["record"]["title"] + " — Arcs")
    for child in window["boundary-actions"].winfo_children():
        child.destroy()
    for side, label in (("begin", "View beginning event"), ("end", "View ending event")):
        event_id = command["record"].get(side + "-event")
        if event_id:
            ttk.Button(window["boundary-actions"], text=label, command=lambda event_id=event_id: author_ui.request_navigation(
                command["view"], {"kind": "select", "uuid": event_id})).pack(side="left", padx=(0, 8))
    # Presentation only: Core supplies the saved field snapshot.
    window["base"] = command["saved-fields"] if "saved-fields" in command else command.get("fields", window["base"])
    may_install = ("expected-fields" not in command
                   or get_view_fields(command["view"]) == command["expected-fields"])
    if "fields" in command and may_install:
        window["base-revision"] = command["record"]["revision"]
        window["installing"] = True
        for key, variable in window["variables"].items():
            variable.set(command["fields"][key])
        window["description"].delete("1.0", "end")
        window["description"].insert("1.0", command["fields"]["description"])
        window["description"].edit_modified(False)
        window["installing"] = False
    elif command.get("own-save"):
        window["base-revision"] = command["record"]["revision"]
    window["status"].set(command["status"] if may_install else "Saved data changed; newer typing retained.")


def realize_core_command(command):
    kind = command["type"]
    if kind == "OUTPUT":
        output = widgets["output"]
        output.configure(state="normal")
        output.insert("end", command["text"] + "\n")
        output.see("end")
        output.configure(state="disabled")
    elif kind == "OPEN" and not g["closing"]:
        build_arc_detail_window(command)
    elif kind == "REQUEST_CLOSE":
        handle_when_user_closes_command_center()
    elif kind == "SHUTDOWN_COMPLETE":
        # An earlier wake can drain this command before its worker-side wake returns.
        # Keep Tcl alive until Core has left event_generate and retired.
        g["root"].after(10, handle_when_waiting_for_core_retirement)
    elif kind == "CLOSE_ABORTED":
        g["closing"] = False
        widgets["entry"].configure(state="normal")
        realize_core_command({"type": "OUTPUT", "text": command["text"]})
        for view_id, window in windows.items():
            window["save"].configure(state="disabled" if window["header-pending"] else "normal")
            window["reload"].configure(state="disabled" if window["header-pending"] else "normal")
            author_ui.set_author_busy(view_id, window["author-pending"])
            for button in window["author-buttons"]:
                button.configure(state="normal")
    elif command.get("view") in windows:
        window = windows[command["view"]]
        if kind == "UPDATE":
            install_view_presentation(command)
        elif kind == "STATUS":
            window["status"].set(command["status"])
        elif kind == "BUSY":
            window["header-pending"] = command["busy"]
            state = "disabled" if command["busy"] or g["closing"] else "normal"
            window["save"].configure(state=state)
            window["reload"].configure(state=state)
        elif kind == "CHRONOLOGY":
            author_ui.install_chronology(command)
        elif kind == "DETAIL":
            author_ui.install_record_details(command)
        elif kind == "AUTHOR":
            author_ui.build_author_editor(command)
        elif kind == "AUTHOR_BUSY":
            author_ui.set_author_busy(command["view"], command["busy"])
            for button in window["author-buttons"]:
                button.configure(state="disabled" if command["busy"] or g["closing"] else "normal")
        elif kind == "AUTHOR_STATUS" and window["author"]:
            window["author-status"].set(command["status"])
        elif kind == "NAVIGATION_CONTINUE":
            author_ui.request_navigation(command["view"], command["intent"])
        elif kind == "CLOSE":
            del windows[command["view"]]
            window["window"].destroy()


def handle_when_core_mail_arrives(event):
    try:
        while not machine.a_thread_died_unexpectedly.is_set():
            command = g["incoming"].get_nowait()
            realize_core_command(command)
            if command["type"] == "SHUTDOWN_COMPLETE":
                return
    except Empty:
        pass


def handle_when_checking_for_fatal_worker_failure():
    if machine.a_thread_died_unexpectedly.is_set():
        g["closing"] = True
        if all(runtime["lifecycle"] == "exited" for runtime in machine.machines.values()):
            g["root"].destroy()
        else:
            g["root"].after(10, handle_when_checking_for_fatal_worker_failure)
        return
    g["root"].after(50, handle_when_checking_for_fatal_worker_failure)


def handle_when_waiting_for_core_retirement():
    if machine.machines["CORE"]["lifecycle"] == "exited":
        g["root"].destroy()
    else:
        g["root"].after(10, handle_when_waiting_for_core_retirement)


def handle_when_tk_callback_fails(exception):
    traceback.print_exception(*exception)
    machine.handle_when_a_worker_dies_unexpectedly()


def run_tk_machine():
    handle_when_checking_for_fatal_worker_failure()
    g["root"].mainloop()
