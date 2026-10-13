"""Tk-only search controls, checkboxes, naming, and clipboard effects."""

from copy import deepcopy
import json
import tkinter
from tkinter import messagebox, ttk

from . import appearance, search, tk

windows = {}
inspections = {}


def read_criteria(view_id):
    variables = windows[view_id]["variables"]
    return {"type": variables["type"].get() or None,
            "name-contains": variables["name-contains"].get(),
            "title-contains": variables["title-contains"].get(),
            "tags": search.parse_tags(variables["tags"].get()),
            "tag-match": variables["tag-match"].get()}


def get_query_caption(view_id):
    window = windows[view_id]
    if window["executed"] is None:
        return "Not yet searched. Press Search to find objects."
    try:
        changed = read_criteria(view_id) != window["executed"]
    except ValueError:
        changed = True
    summary = json.dumps(window["executed"], ensure_ascii=False)
    return ("Parameters changed; displayed results still belong to: " if changed else "Displayed query: ") + summary


def handle_when_search_parameters_change(view_id):
    window = windows.get(view_id)
    if not window or window["installing"]:
        return
    window["caption"].set(get_query_caption(view_id))
    try:
        tk.send({"type": "SEARCH_INPUT", "view": view_id, "criteria": read_criteria(view_id)})
    except ValueError as error:
        window["status"].set(str(error))


def handle_when_user_runs_basic_search(view_id):
    window = windows[view_id]
    try:
        criteria = read_criteria(view_id)
    except ValueError as error:
        window["status"].set(str(error))
        return
    window["selected"] = []
    window["selection-blocked"] = True
    window["selection-generation"] += 1
    update_selection_controls(view_id)
    clear_name_editor(view_id)
    window["status"].set("Searching…")
    tk.send({"type": "SEARCH_RUN", "view": view_id, "criteria": criteria,
             "selection-generation": window["selection-generation"]})


def handle_when_user_clears_search_parameters(view_id):
    install_criteria(view_id, search.empty_criteria())
    handle_when_search_parameters_change(view_id)


def install_criteria(view_id, criteria):
    window = windows[view_id]
    window["installing"] = True
    for key, variable in window["variables"].items():
        variable.set(", ".join(criteria[key]) if key == "tags" else criteria[key] or "")
    window["installing"] = False
    window["caption"].set(get_query_caption(view_id))


def handle_when_user_copies_search_query(view_id):
    try:
        tk.send({"type": "SEARCH_COPY_QUERY", "view": view_id, "criteria": read_criteria(view_id)})
    except ValueError as error:
        windows[view_id]["status"].set(str(error))


def read_clipboard():
    try:
        return {"text": tk.g["root"].clipboard_get()}
    except tkinter.TclError:
        return {"error": "Clipboard text is unavailable. Parameters are unchanged."}


def handle_when_search_window_gains_focus(view_id):
    window = windows.get(view_id)
    if window and not window["clipboard-pending"] and not tk.g["closing"]:
        window["clipboard-pending"] = True
        tk.g["root"].after_idle(lambda: handle_when_search_clipboard_check_is_ready(view_id))


def handle_when_search_clipboard_check_is_ready(view_id):
    if view_id in windows:
        windows[view_id]["clipboard-pending"] = False
        tk.send({"type": "SEARCH_CLIPBOARD", "view": view_id, **read_clipboard()})


def handle_when_user_adopts_clipboard_search(view_id, mode):
    try:
        criteria = read_criteria(view_id)
    except ValueError as error:
        windows[view_id]["status"].set(str(error))
        return
    tk.send({"type": "SEARCH_ADOPT", "view": view_id, "mode": mode, "criteria": criteria, **read_clipboard()})


def clear_name_editor(view_id):
    window = windows[view_id]
    close_session_binding_confirmation(view_id)
    if window.get("name-dialog"):
        window["name-dialog"].destroy()
        window["name-dialog"] = None
    window["name-variables"] = {}


def update_selection_controls(view_id):
    window = windows[view_id]
    selected = set(window["selected"])
    count = len(selected)
    blocked = window["selection-blocked"]
    for row in window["rows"]:
        window["tree"].set(row["uuid"], "checked", "☑" if row["uuid"] in selected else "☐")
    window["select-all"].set(bool(window["rows"]) and count == len(window["rows"]))
    window["counts"].set(f"{len(window['rows'])} results · {count} selected")
    window["open"].configure(state="normal" if count == 1 and not blocked else "disabled")
    for key in ("name", "copy"):
        window[key].configure(state="normal" if count and not blocked else "disabled")
    window["select-all-control"].configure(state="disabled" if blocked else "normal")
    window["name"].configure(text="Name selected objects…" if count > 1 else "Name selected object…")


def submit_selection(view_id, uuids):
    window = windows[view_id]
    if window["selection-blocked"]:
        return
    selected = set(uuids)
    window["selected"] = [row["uuid"] for row in window["rows"] if row["uuid"] in selected]
    window["selection-generation"] += 1
    clear_name_editor(view_id)
    update_selection_controls(view_id)
    tk.send({"type": "SEARCH_SELECT", "view": view_id, "uuids": window["selected"],
             "selection-generation": window["selection-generation"]})


def handle_when_user_ticks_search_row(view_id, event):
    if windows[view_id]["selection-blocked"]:
        return "break"
    tree = windows[view_id]["tree"]
    uuid = tree.identify_row(event.y)
    if uuid and tree.identify_column(event.x) == "#1":
        selected = set(windows[view_id]["selected"])
        selected.symmetric_difference_update({uuid})
        tree.focus(uuid)
        submit_selection(view_id, selected)
        return "break"


def handle_when_user_toggles_focused_search_row(view_id):
    if windows[view_id]["selection-blocked"]:
        return "break"
    uuid = windows[view_id]["tree"].focus()
    if uuid:
        selected = set(windows[view_id]["selected"])
        selected.symmetric_difference_update({uuid})
        submit_selection(view_id, selected)
    return "break"


def handle_when_user_double_clicks_search_uuid(view_id, event):
    tree = windows[view_id]["tree"]
    uuid = tree.identify_row(event.y)
    if uuid and tree.identify_column(event.x) == "#6":
        return tk.handle_when_user_double_clicks_uuid(uuid)


def handle_when_user_selects_all_search_results(view_id):
    window = windows[view_id]
    submit_selection(view_id, [row["uuid"] for row in window["rows"]] if window["select-all"].get() else [])


def handle_when_user_names_selected_objects(view_id):
    window = windows[view_id]
    clear_name_editor(view_id)
    dialog = tkinter.Toplevel(window["window"])
    window["name-dialog"] = dialog
    dialog.title("Assign session names — Arcs")
    dialog.geometry("780x500")
    dialog.minsize(650, 350)
    dialog.transient(window["window"])
    dialog.protocol("WM_DELETE_WINDOW", lambda: clear_name_editor(view_id))
    frame = ttk.Frame(dialog, padding=16)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Session names", style="Heading.TLabel").pack(anchor="w")
    ttk.Label(frame, text="These names last for this session and do not rename Basic records.",
              style="Muted.TLabel").pack(anchor="w", pady=(4, 12))
    scroll_frame = ttk.Frame(frame)
    scroll_frame.pack(fill="both", expand=True)
    canvas = tkinter.Canvas(scroll_frame, highlightthickness=0)
    scroll = ttk.Scrollbar(scroll_frame, command=canvas.yview)
    scroll.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(fill="both", expand=True)
    names = ttk.Frame(canvas)
    item = canvas.create_window((0, 0), window=names, anchor="nw")
    names.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(item, width=event.width))
    names.columnconfigure(0, weight=1)
    row_number = 0
    for row in window["rows"]:
        if row["uuid"] not in window["selected"]:
            continue
        label = ttk.Frame(names)
        label.grid(row=row_number, column=0, sticky="ew", pady=6)
        ttk.Label(label, text=row["title"] or row["name"] or row["type"], wraplength=470).pack(anchor="w")
        tk.build_uuid_label(label, row["uuid"]).pack(anchor="w")
        variable = tkinter.StringVar(names)
        window["name-variables"][row["uuid"]] = variable
        ttk.Entry(names, textvariable=variable, width=18).grid(row=row_number, column=1, sticky="ew", padx=(12, 0))
        row_number += 1
    buttons = ttk.Frame(frame)
    buttons.pack(anchor="w", pady=(12, 0))
    ttk.Button(buttons, text="Assign names", style="Primary.TButton",
               command=lambda: handle_when_user_assigns_session_names(view_id)).pack(side="left")
    ttk.Button(buttons, text="Cancel", command=lambda: clear_name_editor(view_id)).pack(side="left", padx=8)
    window["name-status"] = tkinter.StringVar(dialog)
    ttk.Label(frame, textvariable=window["name-status"], style="Muted.TLabel", wraplength=740).pack(anchor="w", pady=(8, 0))


def handle_when_user_assigns_session_names(view_id):
    windows[view_id]["name-status"].set("")
    tk.send({"type": "SESSION_ASSIGN", "view": view_id, "assignments": [
        {"uuid": uuid, "name": variable.get()} for uuid, variable in windows[view_id]["name-variables"].items()]})


def build_search_window(command):
    view_id = command["view"]
    window = tkinter.Toplevel(tk.g["root"])
    window.title("Basic Search — Arcs")
    window.geometry("1100x820")
    window.minsize(820, 660)
    window.protocol("WM_DELETE_WINDOW", lambda: tk.send({"type": "SEARCH_CLOSE", "view": view_id}))
    window.bind("<FocusIn>", lambda _: handle_when_search_window_gains_focus(view_id))
    window.bind("<Configure>", lambda event: handle_when_search_window_resizes(view_id, event))
    border = tkinter.Frame(window, background=appearance.COLORS["border"])
    border.pack(fill="both", expand=True, padx=12, pady=12)
    frame = ttk.Frame(border, padding=16)
    frame.pack(fill="both", expand=True, padx=1, pady=1)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)
    ttk.Label(frame, text="Basic Search", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
    parameters = ttk.Frame(frame)
    parameters.grid(row=1, column=0, sticky="ew")
    parameters.columnconfigure(0, weight=1)
    parameters.columnconfigure(1, weight=1)
    variables = {key: tkinter.StringVar(window) for key in search.empty_criteria()}
    variables["tag-match"].set("all")
    controls = {}
    for position, spec in enumerate((("type", "Object type (empty means all)"), ("name-contains", "Name contains"),
                                     ("title-contains", "Title contains"), ("tags", "Tags (comma-separated)"))):
        key, label = spec
        cell = ttk.Frame(parameters, padding=(0, 0, 12, 8))
        cell.grid(row=position // 2, column=position % 2, sticky="ew")
        ttk.Label(cell, text=label, style="Muted.TLabel").pack(anchor="w")
        if key == "type":
            control = ttk.Combobox(cell, textvariable=variables[key], state="readonly", values=["", *command["types"]])
        else:
            control = ttk.Entry(cell, textvariable=variables[key])
        control.pack(fill="x", pady=(4, 0))
        controls[key] = control
        if key == "tags":
            modes = ttk.Frame(cell)
            modes.pack(anchor="w", pady=(4, 0))
            for mode, title in (("all", "All tags"), ("any", "Any tag")):
                ttk.Radiobutton(modes, text=title, variable=variables["tag-match"], value=mode).pack(side="left", padx=(0, 12))
    toolbar = ttk.Frame(parameters)
    toolbar.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 6))
    for title, callback in (("Search", lambda: handle_when_user_runs_basic_search(view_id)),
                             ("Clear parameters", lambda: handle_when_user_clears_search_parameters(view_id)),
                             ("Copy search", lambda: handle_when_user_copies_search_query(view_id))):
        button = ttk.Button(toolbar, text=title, command=callback,
                            style="Primary.TButton" if title == "Search" else "TButton")
        button.pack(side="left", padx=(0, 8))
        controls[title] = button
    offer = ttk.Frame(parameters)
    ttk.Label(offer, text="A search is on the clipboard.", style="Muted.TLabel").pack(side="left", padx=(0, 12))
    for mode, label in (("reset", "Reset to clipboard search"), ("incorporate", "Incorporate…")):
        ttk.Button(offer, text=label, command=lambda mode=mode: handle_when_user_adopts_clipboard_search(view_id, mode)).pack(
            side="left", padx=(0, 8))
    caption = tkinter.StringVar(window, value="Not yet searched.")
    caption_label = ttk.Label(parameters, textvariable=caption, style="Muted.TLabel", wraplength=760)
    caption_label.grid(
        row=4, column=0, columnspan=2, sticky="w", pady=(4, 8))
    results = ttk.Frame(frame)
    results.grid(row=2, column=0, sticky="nsew")
    counts = tkinter.StringVar(window, value="0 results · 0 selected")
    select_all = tkinter.BooleanVar(window)
    select_all_control = ttk.Checkbutton(results, text="Select all returned objects", variable=select_all,
                                         command=lambda: handle_when_user_selects_all_search_results(view_id))
    select_all_control.pack(anchor="w")
    columns = ("checked", "object", "type", "tags", "date", "uuid")
    tree = ttk.Treeview(results, columns=columns, show="headings", selectmode="browse")
    for key, title, width in (("checked", "✓", 36), ("object", "Title / Basic name", 290), ("type", "Type", 105),
                              ("tags", "Tags", 150), ("date", "Basic date", 110), ("uuid", "UUID · double-click to copy", 305)):
        tree.heading(key, text=title)
        tree.column(key, width=width, minwidth=width if key in ("checked", "uuid") else 80,
                    stretch=key == "object")
    tree.bind("<Button-1>", lambda event: handle_when_user_ticks_search_row(view_id, event))
    tree.bind("<space>", lambda _: handle_when_user_toggles_focused_search_row(view_id))
    tree.bind("<Double-Button-1>", lambda event: handle_when_user_double_clicks_search_uuid(view_id, event))
    vertical = ttk.Scrollbar(results, command=tree.yview)
    vertical.pack(side="right", fill="y")
    horizontal = ttk.Scrollbar(results, orient="horizontal", command=tree.xview)
    horizontal.pack(side="bottom", fill="x")
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.pack(fill="both", expand=True)
    actions = ttk.Frame(frame)
    actions.grid(row=3, column=0, sticky="ew", pady=(10, 0))
    ttk.Label(actions, textvariable=counts, style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
    buttons = ttk.Frame(actions)
    buttons.pack(fill="x")
    open_button = ttk.Button(buttons, text="Open selected", state="disabled", command=lambda: tk.send(
        {"type": "SEARCH_OPEN_SELECTED", "view": view_id}))
    open_button.pack(side="left", padx=(0, 8))
    name_button = ttk.Button(buttons, text="Name selected object…", state="disabled",
                             command=lambda: handle_when_user_names_selected_objects(view_id))
    name_button.pack(side="left", padx=(0, 8))
    copy_button = ttk.Button(buttons, text="Copy reference(s)", state="disabled", command=lambda: tk.send(
        {"type": "SEARCH_COPY_REFERENCES", "view": view_id}))
    copy_button.pack(side="left")
    status = tkinter.StringVar(window)
    status_label = ttk.Label(frame, textvariable=status, style="Muted.TLabel", wraplength=760)
    status_label.grid(
        row=4, column=0, sticky="w", pady=(8, 0))
    windows[view_id] = {"window": window, "variables": variables, "controls": controls, "tree": tree,
                        "caption": caption, "counts": counts, "select-all": select_all, "offer": offer,
                        "select-all-control": select_all_control, "selection-blocked": False,
                        "caption-label": caption_label, "status-label": status_label,
                        "status": status, "open": open_button, "name": name_button, "copy": copy_button,
                        "name-dialog": None, "binding-dialog": None, "name-variables": {},
                        "selected": [], "selection-generation": 0,
                        "rows": [], "executed": None, "installing": False, "clipboard-pending": False,
                        "aliases": {}}
    for variable in variables.values():
        variable.trace_add("write", lambda *_: handle_when_search_parameters_change(view_id))


def install_search_presentation(command):
    view_id = command["view"]
    window = windows[view_id]
    old_selection = set(window["selected"])
    if command["rows"] != window["rows"] or command["aliases"] != window["aliases"]:
        focus, scroll = window["tree"].focus(), window["tree"].yview()
        window["tree"].delete(*window["tree"].get_children())
        window["rows"] = deepcopy(command["rows"])
        window["aliases"] = deepcopy(command["aliases"])
        for row in window["rows"]:
            aliases = [name for name, uuid in window["aliases"].items() if uuid == row["uuid"]]
            label = (row["title"] or "(untitled)") + " · " + row["name"]
            if aliases:
                label += " · session: " + ", ".join(aliases)
            window["tree"].insert("", "end", iid=row["uuid"], values=("☐", label, row["type"],
                ", ".join(row["tags"]), row["date"], row["uuid"]))
        if window["tree"].exists(focus):
            window["tree"].focus(focus)
        if scroll:
            window["tree"].yview_moveto(scroll[0])
    if command["selection-generation"] >= window["selection-generation"]:
        window["selected"] = list(command["selected"])
        window["selection-generation"] = command["selection-generation"]
    else:
        window["selected"] = [row["uuid"] for row in window["rows"] if row["uuid"] in old_selection]
    if old_selection != set(window["selected"]):
        clear_name_editor(view_id)
    window["executed"] = deepcopy(command["executed"])
    window["selection-blocked"] = command["selection-blocked"]
    window["controls"]["type"].configure(values=["", *command["types"]])
    window["status"].set(command["status"])
    window["caption"].set(get_query_caption(view_id))
    update_selection_controls(view_id)


def handle_when_search_window_resizes(view_id, event):
    window = windows.get(view_id)
    if window and event.widget == window["window"]:
        for key in ("caption-label", "status-label"):
            window[key].configure(wraplength=max(300, event.width - 64))


def resolve_clipboard_conflicts(command):
    choices = {}
    for conflict in command["merge"]["conflicts"]:
        text = (f"Criterion: {conflict['field']}\nCurrent: {conflict['current']}\nIncoming: {conflict['incoming']}"
                + (f"\nModes: current {conflict['current-mode']}; incoming {conflict['incoming-mode']}"
                   if conflict["field"] == "tags" else "")
                + "\n\nYes: Use incoming; No: Keep current; Cancel: Leave parameters unchanged.")
        choice = messagebox.askyesnocancel("Incorporate search", text, parent=windows[command["view"]]["window"])
        if choice is None:
            return
        choices[conflict["field"]] = "incoming" if choice else "current"
    tk.send({"type": "SEARCH_MERGE", "view": command["view"], "token": command["merge"]["token"], "choices": choices})


def confirm_session_rebindings(command):
    view_id = command["view"]
    window = windows[view_id]
    if window["name-dialog"] is None:
        return
    close_session_binding_confirmation(view_id)
    dialog = tkinter.Toplevel(window["name-dialog"])
    window["binding-dialog"] = dialog
    dialog.title("Replace session bindings? — Arcs")
    dialog.geometry("780x430")
    dialog.minsize(700, 330)
    dialog.transient(window["name-dialog"])
    dialog.protocol("WM_DELETE_WINDOW", lambda: close_session_binding_confirmation(view_id))
    frame = ttk.Frame(dialog, padding=16)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Replace session bindings?", style="Heading.TLabel").pack(anchor="w")
    ttk.Label(frame, text="Review the current and incoming objects. Cancel keeps every binding unchanged.",
              style="Muted.TLabel", wraplength=740).pack(anchor="w", pady=(4, 12))
    host = ttk.Frame(frame)
    host.pack(fill="both", expand=True)
    canvas = tkinter.Canvas(host, highlightthickness=0)
    scroll = ttk.Scrollbar(host, command=canvas.yview)
    scroll.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(fill="both", expand=True)
    items = ttk.Frame(canvas)
    item = canvas.create_window((0, 0), window=items, anchor="nw")
    items.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(item, width=event.width))
    titles = {row["uuid"]: row["title"] or row["name"] for row in window["rows"]}
    for conflict in command["conflicts"]:
        group = ttk.Frame(items, padding=(0, 0, 0, 12))
        group.pack(fill="x")
        ttk.Label(group, text="Session name: " + conflict["name"], font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        for side, label in (("current", "Current object"), ("incoming", "Incoming object")):
            ttk.Label(group, text=label + ": " + titles.get(conflict[side], ""), wraplength=700).pack(anchor="w", pady=(4, 0))
            tk.build_uuid_label(group, conflict[side]).pack(anchor="w")
    buttons = ttk.Frame(frame)
    buttons.pack(anchor="w", pady=(12, 0))
    ttk.Button(buttons, text="Replace bindings and assign names", style="Primary.TButton",
               command=lambda: handle_when_user_confirms_session_rebinding(view_id, command)).pack(side="left")
    ttk.Button(buttons, text="Cancel", command=lambda: close_session_binding_confirmation(view_id)).pack(side="left", padx=8)
    dialog.grab_set()


def close_session_binding_confirmation(view_id):
    dialog = windows[view_id].get("binding-dialog")
    if dialog:
        dialog.grab_release()
        dialog.destroy()
        windows[view_id]["binding-dialog"] = None


def handle_when_user_confirms_session_rebinding(view_id, command):
    close_session_binding_confirmation(view_id)
    tk.send({"type": "SESSION_ASSIGN", "view": view_id, "assignments": command["assignments"],
             "replacements": {item["name"]: item["current"] for item in command["conflicts"]}})


def install_object_inspection(command):
    view_id, record = command["view"], command["record"]
    if view_id not in inspections:
        window = tkinter.Toplevel(tk.g["root"])
        window.geometry("800x650")
        window.minsize(620, 460)
        window.protocol("WM_DELETE_WINDOW", lambda: tk.send({"type": "INSPECT_CLOSE", "view": view_id}))
        border = tkinter.Frame(window, background=appearance.COLORS["border"])
        border.pack(fill="both", expand=True, padx=12, pady=12)
        frame = ttk.Frame(border, padding=16)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        inspections[view_id] = {"window": window, "frame": frame}
    window, frame = inspections[view_id]["window"], inspections[view_id]["frame"]
    window.title((record["title"] or record["name"] or record["type"]) + " — Arcs")
    for child in frame.winfo_children():
        child.destroy()
    ttk.Label(frame, text=record["title"] or record["type"], style="Heading.TLabel", wraplength=700).pack(anchor="w")
    date_label = ("Occurrence: " + record["time-label"] if "time-label" in record
                  else "Basic date: " + (record["date"] or "Unknown"))
    ttk.Label(frame, text=f"{record['type']} · {record['name']}\n{date_label}\n"
              f"Tags: {', '.join(record.get('tags', []))}", style="Muted.TLabel", wraplength=700).pack(anchor="w", pady=8)
    tk.build_uuid_label(frame, record["uuid"]).pack(anchor="w", pady=(0, 8))
    for arc in record["associations"]:
        ttk.Button(frame, text="Open arc: " + arc["title"], command=lambda uuid=arc["uuid"]: tk.send(
            {"type": "INSPECT_OPEN_ARC", "view": view_id, "uuid": uuid})).pack(anchor="w", pady=2)
    text_frame = ttk.Frame(frame)
    text_frame.pack(fill="both", expand=True, pady=(8, 0))
    body = tkinter.Text(text_frame, wrap="word", font=("Segoe UI", 11))
    scroll = ttk.Scrollbar(text_frame, command=body.yview)
    scroll.pack(side="right", fill="y")
    body.configure(yscrollcommand=scroll.set)
    body.pack(fill="both", expand=True)
    body.insert("end", record["description"])
    if record.get("link"):
        body.insert("end", "\n\nLink data:\n" + json.dumps(record["link"], ensure_ascii=False, indent=2))
    if record.get("temporal"):
        body.insert("end", "\n\nTemporal claims:\n" + json.dumps(
            record["temporal"]["records"][0].get("temporal-claims", []), ensure_ascii=False, indent=2))
    tk.tag_uuids(body)
    body.configure(state="disabled")
    inspections[view_id]["body"] = body


def realize_search_command(command):
    kind, view_id = command["type"], command.get("view")
    if kind == "SEARCH_OPEN" and not tk.g["closing"]:
        build_search_window(command)
    elif kind == "INSPECT_OPEN" and not tk.g["closing"]:
        install_object_inspection(command)
    elif kind == "INSPECT_UPDATE" and view_id in inspections:
        install_object_inspection(command)
    elif kind == "INSPECT_CLOSE" and view_id in inspections:
        inspections.pop(view_id)["window"].destroy()
    elif kind == "INSPECT_STATUS" and view_id in inspections:
        ttk.Label(inspections[view_id]["frame"], text=command["status"], style="Muted.TLabel").pack(anchor="w")
    elif view_id in windows:
        window = windows[view_id]
        if kind == "SEARCH_PRESENT":
            install_search_presentation(command)
        elif kind == "SEARCH_INPUT":
            try:
                if read_criteria(view_id) == command["expected"]:
                    install_criteria(view_id, command["criteria"])
                else:
                    handle_when_search_parameters_change(view_id)
            except ValueError:
                window["status"].set("Newer typing retained; fix the tag input before adopting again.")
        elif kind == "SEARCH_OFFER":
            if command["available"]:
                window["offer"].grid(row=3, column=0, columnspan=2, sticky="w", pady=6)
            else:
                window["offer"].grid_remove()
        elif kind == "SEARCH_CONFLICTS":
            resolve_clipboard_conflicts(command)
        elif kind == "SESSION_CONFLICTS":
            confirm_session_rebindings(command)
        elif kind == "SESSION_ASSIGNED":
            clear_name_editor(view_id)
        elif kind == "SESSION_ERROR" and window["name-dialog"]:
            window["name-status"].set(command["status"])
        elif kind == "SEARCH_COPY":
            try:
                tk.g["root"].clipboard_clear()
                tk.g["root"].clipboard_append(command["text"])
                status = command["status"]
            except tkinter.TclError:
                status = "Clipboard copying failed. Your data is unchanged."
            tk.send({"type": "SEARCH_STATUS", "view": view_id, "status": status,
                     "status-token": command["status-token"]})
        elif kind == "SEARCH_CLOSE":
            windows.pop(view_id)["window"].destroy()
