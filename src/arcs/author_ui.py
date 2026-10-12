"""Tk-side chronology, readable records, and in-pane authoring controls."""

from copy import deepcopy
import tkinter
from tkinter import messagebox, ttk

from . import tk

reg = {"view": None, "frame": None, "row": 0}


def get_author_fields(view_id):
    window = tk.windows[view_id]
    fields = deepcopy(window["author"]["fields"])
    fields.update({key: variable.get() for key, variable in window["author-variables"].items()})
    fields.update({key: text.get("1.0", "end-1c") for key, text in window["author-texts"].items()})
    return fields


def has_author_changes(view_id):
    window = tk.windows[view_id]
    return bool(window["author"] and get_author_fields(view_id) != window["author"]["fields"])


def set_author_busy(view_id, busy):
    window = tk.windows[view_id]
    window["author-pending"] = busy
    for widget in window.get("author-controls", []):
        widget.configure(state="disabled" if busy or tk.g["closing"] else "normal")


def handle_when_author_fields_change(view_id):
    window = tk.windows.get(view_id)
    if window is None or window.get("author-installing") or window["author"] is None:
        return
    for text in window["author-texts"].values():
        text.edit_modified(False)
    tk.send({"type": "AUTHOR_DRAFT", "view": view_id, "uuid": window["author"]["uuid"],
             "fields": get_author_fields(view_id)})


def save_author_draft(view_id, after=None):
    window = tk.windows[view_id]
    if window["author"] is None or window["author-pending"]:
        return
    fields = get_author_fields(view_id)
    set_author_busy(view_id, True)
    window["author-status"].set("Saving…")
    tk.send({"type": "AUTHOR_SAVE", "view": view_id, "uuid": window["author"]["uuid"],
             "fields": fields, "after": after})


def request_navigation(view_id, intent):
    window = tk.windows.get(view_id)
    if window is None or tk.g["closing"]:
        return
    if window["author-pending"] or window["header-pending"]:
        if intent["kind"] == "close" and not window["header-pending"] and not tk.has_unsaved_draft(view_id):
            tk.send({"type": "CLOSE_VIEW", "view": view_id})
            return
        if window["author"]:
            window["author-status"].set("Wait for the submitted save before navigating.")
        restore_chronology_selection(view_id)
        return
    if intent["kind"] == "close" and tk.has_unsaved_draft(view_id):
        choice = messagebox.askyesnocancel("Unsaved arc fields", "Save arc fields before closing?\n"
                                          "Yes: Save; No: Discard; Cancel: Stay here.", parent=window["window"])
        if choice is None:
            return
        if choice:
            tk.send({"type": "SAVE", "view": view_id, "fields": tk.get_view_fields(view_id),
                     "base": window["base-revision"], "after": intent})
            return
    if intent["kind"] != "cancel" and has_author_changes(view_id):
        choice = messagebox.askyesnocancel("Unsaved record", "Save this draft before navigating?\n"
                                          "Yes: Save; No: Discard; Cancel: Stay here.", parent=window["window"])
        if choice is None:
            restore_chronology_selection(view_id)
            return
        if choice:
            save_author_draft(view_id, intent)
            restore_chronology_selection(view_id)
            return
    tk.send({"type": "AUTHOR_NAVIGATE", "view": view_id, "intent": intent})


def handle_when_user_starts_record(view_id, kind):
    request_navigation(view_id, {"kind": "start", "draft-kind": kind,
                                 "base": tk.windows[view_id]["base-revision"]})


def handle_when_user_selects_chronology(view_id):
    window = tk.windows[view_id]
    selection = window["tree"].selection()
    if not selection or selection[0] == window["selected"]:
        return
    request_navigation(view_id, {"kind": "select", "uuid": selection[0]})


def restore_chronology_selection(view_id):
    window = tk.windows[view_id]
    tree = window["tree"]
    tree.selection_remove(tree.selection())
    if window["selected"] and tree.exists(window["selected"]):
        tree.selection_set(window["selected"])


def install_chronology(command):
    window = tk.windows[command["view"]]
    tree = window["tree"]
    window["selected"] = command["selected"]
    tree.delete(*tree.get_children())
    for record in command["items"]:
        label = record["title"] or record["description"].splitlines()[0][:75]
        kind = "Journal" if record["type"] == "journal-entry" else "Transition" if record["successor"] else "Event"
        tree.insert("", "end", iid=record["uuid"], text=label,
                    values=(kind, record["time-label"]))
    window["empty-label"].configure(text="No events or journal entries yet." if not command["items"] else "")
    restore_chronology_selection(command["view"])


def clear_detail_presentation(view_id):
    window = tk.windows[view_id]
    window["author"] = None
    window["author-controls"] = []
    for frame in (window["detail"], window["detail-actions"]):
        for child in frame.winfo_children():
            child.destroy()


def install_record_details(command):
    view_id = command["view"]
    clear_detail_presentation(view_id)
    frame = tk.windows[view_id]["detail"]
    record = command["record"]
    if record is None:
        ttk.Label(frame, text="Select a chronology record to read it here.").pack(anchor="w", pady=10)
        return
    kind = "Journal entry" if record["type"] == "journal-entry" else "Transition event" if record["successor"] else "Event"
    ttk.Label(frame, text=record["title"] or kind, font=("Segoe UI", 14, "bold"), wraplength=480).pack(anchor="w", pady=(0, 8))
    ttk.Label(frame, text=kind + " · " + record["time-label"], wraplength=480).pack(anchor="w", pady=4)
    body = tkinter.Text(frame, height=8, wrap="word", font=("Segoe UI", 11))
    body.insert("1.0", record["description"])
    body.configure(state="disabled")
    body.pack(fill="both", expand=True, pady=8)
    ttk.Label(frame, text=record["uuid"], foreground="#666666").pack(anchor="w")
    temporal = record["temporal"]["records"][0]
    for claim in temporal.get("temporal-claims", []):
        if claim.get("claim-notes"):
            ttk.Label(frame, text=claim["claim-notes"], wraplength=480).pack(anchor="w", pady=4)
    if record["successor"]:
        ttk.Button(frame, text="Open successor arc", command=lambda: tk.send(
            {"type": "OPEN_SUCCESSOR", "view": view_id})).pack(anchor="w", pady=12)


def build_author_field(spec):
    window = tk.windows[reg["view"]]
    key, label, multiline = spec
    ttk.Label(reg["frame"], text=label).grid(row=reg["row"], column=0, sticky="w", pady=(6, 2))
    reg["row"] += 1
    if multiline:
        widget = tkinter.Text(reg["frame"], height=4, wrap="word", font=("Segoe UI", 11), undo=True)
        widget.insert("1.0", window["author"]["fields"][key])
        widget.edit_modified(False)
        window["author-texts"][key] = widget
        view_id = reg["view"]
        widget.bind("<<Modified>>", lambda _, text=widget: handle_when_author_fields_change(view_id)
                    if text.edit_modified() else None)
    else:
        variable = tkinter.StringVar(reg["frame"], value=window["author"]["fields"][key])
        widget = ttk.Entry(reg["frame"], textvariable=variable)
        window["author-variables"][key] = variable
        view_id = reg["view"]
        variable.trace_add("write", lambda *_: handle_when_author_fields_change(view_id))
    widget.grid(row=reg["row"], column=0, sticky="ew")
    reg["row"] += 1
    window["author-controls"].append(widget)


def handle_when_user_refreshes_predecessor(view_id):
    window = tk.windows[view_id]
    tk.send({"type": "AUTHOR_DRAFT", "view": view_id, "uuid": window["author"]["uuid"],
             "fields": get_author_fields(view_id)})
    set_author_busy(view_id, True)
    tk.send({"type": "AUTHOR_REFRESH", "view": view_id})


def build_author_editor(command):
    view_id = command["view"]
    clear_detail_presentation(view_id)
    window = tk.windows[view_id]
    draft = deepcopy(command["draft"])
    window.update({"author": draft, "author-variables": {}, "author-texts": {},
                   "author-controls": [], "author-installing": True, "author-pending": False})
    frame = window["detail"]
    frame.columnconfigure(0, weight=1)
    reg.update(view=view_id, frame=frame, row=0)
    label = {"journal-entry": "New journal entry", "event": "New event", "transition": "Transition to another arc"}[draft["kind"]]
    ttk.Label(frame, text=label, font=("Segoe UI", 13, "bold")).grid(row=reg["row"], column=0, sticky="w")
    reg["row"] += 1
    ttk.Label(frame, text="For: " + command["arc-title"] + "\n" + draft["arc"], wraplength=480).grid(
        row=reg["row"], column=0, sticky="w", pady=4)
    reg["row"] += 1
    if draft["kind"] == "transition":
        ttk.Label(frame, text="This event ends the current arc and begins the new arc.",
                  wraplength=480).grid(row=reg["row"], column=0, sticky="w", pady=8)
        reg["row"] += 1
        ttk.Label(frame, text="Transition event", font=("Segoe UI", 11, "bold")).grid(
            row=reg["row"], column=0, sticky="w", pady=(8, 0))
        reg["row"] += 1
    for spec in (("title", "Title (optional)", False),
                 ("description", "Entry content" if draft["kind"] == "journal-entry" else "What happened", True),
                 ("when", "Date/time (UNKNOWN, YYYY, YYYY-MM, date, or ISO time with offset)", False),
                 ("earliest", "Earliest plausible time (optional)", False),
                 ("latest", "Latest plausible time (optional)", False),
                 ("notes", "Temporal notes (optional)", True)):
        build_author_field(spec)
    if draft["kind"] == "transition":
        ttk.Label(frame, text="New successor arc", font=("Segoe UI", 11, "bold")).grid(
            row=reg["row"], column=0, sticky="w", pady=(8, 0))
        reg["row"] += 1
        for spec in (("successor-title", "New successor arc title (required)", False),
                     ("successor-name", "Successor name (optional; generated if blank)", False),
                     ("successor-description", "Successor narrative", True)):
            build_author_field(spec)
    actions = ttk.Frame(window["detail-actions"])
    actions.pack(fill="x")
    save = ttk.Button(actions, text="Save", command=lambda: save_author_draft(view_id))
    save.pack(side="left")
    cancel = ttk.Button(actions, text="Cancel", command=lambda: request_navigation(view_id, {"kind": "cancel"}))
    cancel.pack(side="left", padx=8)
    window["author-controls"].extend((save, cancel))
    if draft["kind"] == "transition":
        refresh = ttk.Button(actions, text="Refresh predecessor", command=lambda: handle_when_user_refreshes_predecessor(view_id))
        refresh.pack(side="left")
        window["author-controls"].append(refresh)
    window["author-status"] = tkinter.StringVar(frame, value="Draft — not saved")
    ttk.Label(window["detail-actions"], textvariable=window["author-status"], wraplength=480).pack(anchor="w", pady=4)
    window["author-installing"] = False
    window["detail-canvas"].yview_moveto(0)
    reg.update(view=None, frame=None, row=0)
