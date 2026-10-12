"""Commands, operation scheduling, and independent window reducers."""

from collections import deque
from copy import deepcopy
from uuid import uuid4

from . import machine, mobile_stacks, records

g = {"ready": False, "closing": False, "active": None, "send": None}
reg = {"event": None, "command": None, "tail": None, "args": None}
views = {}
requests = deque()
events = deque()


def cmdparts(s):
    result = s.split(None, 1)
    if len(result) == 0: return "", "", []
    elif len(result) == 1: return result[0].upper(), "", []
    else: return result[0].upper(), result[1], result[1].split()


def emit(command):
    g["send"](command)


def say(text):
    emit({"type": "OUTPUT", "text": text})


def initialize_core_for_a_new_session():
    g.update(ready=False, closing=False, active=None)
    views.clear()
    requests.clear()
    events.clear()
    say("Starting Arcs…")
    requests.append({"action": "startup", "id": str(uuid4())})


def enqueue_request(request):
    request["id"] = str(uuid4())
    requests.append(request)


def process_next_request_or_finish_shutdown():
    if g["active"] is not None:
        return
    if requests:
        request = requests.popleft()
        g["active"] = request
        mobile_stacks.create_stack()
        mobile_stacks.set_register("request", deepcopy(request))
        mobile_stacks.push_frame({"machine": "CORE", "entry": "RESULT"})
        if request["action"] == "startup":
            mobile_stacks.push_frame({"machine": "MEM", "entry": "LOADED"})
            mobile_stacks.push_frame({"machine": "DISK", "entry": "LOAD"})
        else:
            mobile_stacks.push_frame({"machine": "MEM", "entry": "REQUEST"})
        machine.route_current_stack()
    elif g["closing"]:
        machine.request_machine_retirement()
        machine.machines["MEM"]["inbox"].put(None)
        emit({"type": "SHUTDOWN_COMPLETE"})


def handle_when_core_receives_operation_result():
    events.append({"type": "RESULT", "request": deepcopy(mobile_stacks.get_register("request")),
                   "result": deepcopy(mobile_stacks.get_register("result"))})


def create_detail_view(record):
    view_id = str(uuid4())
    fields = records.get_editor_fields(record)
    views[view_id] = {"record": deepcopy(record), "draft": deepcopy(fields), "pending": False}
    emit({"type": "OPEN", "view": view_id, "record": deepcopy(record), "fields": fields})


def reduce_view_change(view_id, record):
    view = views[view_id]
    if view["record"]["uuid"] != record["uuid"]:
        return
    accepted_draft = view.pop("accepted-draft", None)
    clean = (view["draft"] == records.get_editor_fields(view["record"])
             or view["draft"] == accepted_draft)
    command = {"type": "UPDATE", "view": view_id, "record": deepcopy(record),
               "saved-fields": records.get_editor_fields(record),
               "own-save": accepted_draft is not None,
               "status": "Saved." if clean else "Saved data changed; your draft is preserved."}
    if clean:
        command["expected-fields"] = deepcopy(view["draft"])
        view["record"] = deepcopy(record)
        view["draft"] = records.get_editor_fields(record)
        command["fields"] = deepcopy(view["draft"])
    emit(command)


def reduce_returned_operation_for_all_views(event):
    request, result = event["request"], event["result"]
    if g["active"] is None or request["id"] != g["active"]["id"]:
        raise RuntimeError("Unexpected operation completion")
    g["active"] = None
    view_id = request.get("view")
    view = views.get(view_id)
    if view:
        view["pending"] = False
    status = result["status"]
    if status == "ready":
        g["ready"] = True
        say(f"Ready. {result['count']} arc(s). Commands: create-arc | edit-arc <UUID> | list-arcs | help")
        emit({"type": "READY"})
    elif status == "listed":
        say("\n".join(f"{r['name']}:{r['uuid']}" for r in result["arcs"]) or "No arcs.")
    elif status == "opened":
        if request["action"] == "reload" and view:
            view["record"] = deepcopy(result["record"])
            command = {"type": "UPDATE", "view": view_id, "record": deepcopy(view["record"]),
                       "saved-fields": records.get_editor_fields(view["record"]),
                       "status": "Reloaded saved data; newer typing retained."}
            if view["draft"] == request["fields"]:
                command["expected-fields"] = deepcopy(view["draft"])
                view["draft"] = records.get_editor_fields(view["record"])
                command.update(fields=deepcopy(view["draft"]), status="Reloaded saved data.")
            emit(command)
        elif not g["closing"]:
            create_detail_view(result["record"])
    elif status == "accepted":
        record = result["record"]
        # Mark only the submitted generation clean; preserve edits made during a save.
        if view:
            view["accepted-draft"] = request.get("fields")
        for target in list(views):
            reduce_view_change(target, record)
        if view:
            view["record"] = deepcopy(record)
        say(f"Saved {record['uuid']} (revision {record['revision']}).")
        if request["action"] == "create" and not g["closing"]:
            create_detail_view(record)
    elif status == "conflict":
        if view:
            # Keep the stale base: another Save cannot accidentally overwrite the newer record.
            emit({"type": "STATUS", "view": view_id,
                  "status": "Conflict: another view saved this arc. Draft retained; Reload to start from saved data."})
        say("Save conflict; draft retained.")
    else:
        say("Error: " + result["message"])
        if view:
            emit({"type": "STATUS", "view": view_id, "status": result["message"]})
    if view:
        emit({"type": "BUSY", "view": view_id, "busy": False})


def interpret_current_command_from_entry():
    reg["command"], reg["tail"], reg["args"] = cmdparts(reg["event"]["text"])
    command, args = reg["command"], reg["args"]
    if not command:
        return
    say("> " + reg["event"]["text"])
    if command == "HELP" and not args:
        say("create-arc — create and open an arc\nedit-arc <UUID> — open an existing arc\n"
            "list-arcs — print name:UUID\nhelp — this summary")
        return
    if not g["ready"]:
        say("Arcs is still starting.")
        return
    if command == "CREATE-ARC" and not args:
        enqueue_request({"action": "create", "uuid": str(uuid4())})
        say("Creating arc…")
    elif command == "LIST-ARCS" and not args:
        enqueue_request({"action": "list"})
    elif command == "EDIT-ARC" and len(args) == 1:
        try:
            uuid = records.normalize_uuid(args[0])
        except ValueError as error:
            say("Error: " + str(error))
            return
        enqueue_request({"action": "open", "uuid": uuid})
    else:
        say("Unknown command or wrong arguments. Type help.")


def reduce_current_semantic_event():
    event = reg["event"]
    kind = event["type"]
    if kind == "RESULT":
        reduce_returned_operation_for_all_views(event)
        return
    if kind == "SHUTDOWN":
        if not g["closing"]:
            g["closing"] = True
            say("Closing after submitted operations finish…")
        return
    if g["closing"]:
        return
    if kind == "COMMAND":
        interpret_current_command_from_entry()
        return
    view_id = event.get("view")
    view = views.get(view_id)
    if view is None:
        return
    if kind == "CLOSE_VIEW":
        del views[view_id]
        emit({"type": "CLOSE", "view": view_id})
    elif kind == "DRAFT":
        view["draft"] = deepcopy(event["fields"])
    elif kind == "SAVE" and not view["pending"]:
        view["draft"] = deepcopy(event["fields"])
        view["pending"] = True
        enqueue_request({"action": "save", "view": view_id, "uuid": view["record"]["uuid"],
                         "base": event.get("base", view["record"]["revision"]),
                         "fields": deepcopy(view["draft"])})
        emit({"type": "BUSY", "view": view_id, "busy": True})
    elif kind == "RELOAD" and not view["pending"]:
        # Queued behind writes, so this obtains the latest accepted snapshot.
        view["pending"] = True
        view["draft"] = deepcopy(event["fields"])
        enqueue_request({"action": "reload", "view": view_id, "uuid": view["record"]["uuid"],
                         "fields": deepcopy(view["draft"])})
        emit({"type": "BUSY", "view": view_id, "busy": True})


def run_reducer_core():
    initialize_core_for_a_new_session()
    process_next_request_or_finish_shutdown()
    runtime = machine.get_current_runtime()
    while runtime["running"] and not machine.a_thread_died_unexpectedly.is_set():
        item = machine.get_current_inbox().get()
        if machine.a_thread_died_unexpectedly.is_set():
            break
        if mobile_stacks.is_mobile_stack(item):
            machine.handle_received_mobile_stack(item)
        else:
            events.append(item or {"type": "SHUTDOWN"})
        while events and not machine.a_thread_died_unexpectedly.is_set():
            reg["event"] = events.popleft()
            reduce_current_semantic_event()
        reg["event"] = None
        process_next_request_or_finish_shutdown()
