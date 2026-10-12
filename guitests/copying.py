"""Native double-click checks for UUID labels and read-only text."""

import tkinter
from tkinter import ttk
from uuid import uuid4

from arcs import authoring, author_ui, main, records, tk


def find_label(parent, value):
    for child in parent.winfo_children():
        if isinstance(child, ttk.Label) and child.cget("text") == value:
            return child
        found = find_label(child, value)
        if found is not None:
            return found
    return None


def double_click(widget, point=(5, 5)):
    widget.event_generate("<Motion>", x=point[0], y=point[1])
    for moment in (1000, 1100):
        widget.event_generate("<ButtonPress-1>", x=point[0], y=point[1], time=moment)
        widget.event_generate("<ButtonRelease-1>", x=point[0], y=point[1], time=moment + 10)


def check_copying():
    main.initialize_workers_and_wire_queues()
    tk.build_command_center_before_workers_start()
    root = tk.g["root"]
    root.update()
    try:
        prior = root.clipboard_get()
    except tkinter.TclError:
        prior = None
    try:
        arc = records.create_arc(str(uuid4()))
        tk.build_arc_detail_window({"view": "copy-test", "record": arc,
                                    "fields": records.get_editor_fields(arc)})
        root.update_idletasks()
        double_click(find_label(tk.windows["copy-test"]["window"], arc["uuid"]))
        assert root.clipboard_get() == arc["uuid"]
        draft = authoring.create_draft("event", arc)
        draft["fields"]["description"] = "A reference: " + arc["uuid"]
        record = authoring.create_record(draft)
        record.update({"time-label": "Time unknown", "successor": None})
        author_ui.install_record_details({"view": "copy-test", "record": record})
        root.update_idletasks()
        double_click(find_label(tk.windows["copy-test"]["detail"], record["uuid"]))
        assert root.clipboard_get() == record["uuid"]
        body = next(child for child in tk.windows["copy-test"]["detail"].winfo_children()
                    if isinstance(child, tkinter.Text))
        index = body.search(arc["uuid"], "1.0")
        box = body.bbox(index)
        double_click(body, (box[0] + 2, box[1] + 2))
        assert root.clipboard_get() == arc["uuid"]
        author_ui.build_author_editor({"view": "copy-test", "draft": draft, "arc-title": arc["title"]})
        root.update_idletasks()
        double_click(find_label(tk.windows["copy-test"]["detail"], arc["uuid"]))
        assert root.clipboard_get() == arc["uuid"]
        # Unicode preceding a UUID must not shift the tagged text indices.
        second = str(uuid4()).upper()
        tk.realize_core_command({"type": "OUTPUT", "text": "Copy \U0001f310 " + arc["uuid"] + " and " + second})
        root.update_idletasks()
        output = tk.widgets["output"]
        index = output.search(second, "1.0")
        output.see(index)
        root.update_idletasks()
        box = output.bbox(index)
        double_click(output, (box[0] + 2, box[1] + 2))
        assert root.clipboard_get() == second, (index, box, output.index("current"),
                                               output.tag_names("current"), root.clipboard_get())
        assert output.cget("state") == "disabled"
        print("Real Tk UUID copying passed")
    finally:
        root.clipboard_clear()
        if prior is not None:
            root.clipboard_append(prior)
        root.destroy()


if __name__ == "__main__":
    check_copying()
