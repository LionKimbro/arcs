"""Commands, operation scheduling, and independent window reducers."""

from collections import deque
from copy import deepcopy
from uuid import uuid4

from . import authoring, machine, mobile_stacks, records, search_core

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
    search_core.initialize_search_for_new_session()
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


def create_detail_view(record, chronology=None):
    view_id = str(uuid4())
    fields = records.get_editor_fields(record)
    views[view_id] = {"record": deepcopy(record), "draft": deepcopy(fields), "pending": False,
                      "chronology": deepcopy(chronology or []), "selected": None,
                      "author": None, "author-pending": False, "prior-selection": None}
    emit({"type": "OPEN", "view": view_id, "record": deepcopy(record), "fields": fields})
    present_chronology(view_id)


def present_chronology(view_id):
    view = views[view_id]
    emit({"type": "CHRONOLOGY", "view": view_id, "items": deepcopy(view["chronology"]),
          "selected": view["selected"]})


def present_record_details(view_id):
    view = views[view_id]
    record = next((record for record in view["chronology"] if record["uuid"] == view["selected"]), None)
    emit({"type": "DETAIL", "view": view_id, "record": deepcopy(record)})


def navigate_authoring_view(view_id, intent):
    view = views[view_id]
    if view["author-pending"]:
        present_chronology(view_id)
        return
    prior = view["prior-selection"] if view["author"] else view["selected"]
    view["author"] = None
    kind = intent["kind"]
    if kind == "start":
        view["prior-selection"] = prior
        view["selected"] = None
        view["author"] = authoring.create_draft(intent["draft-kind"], view["record"])
        view["author"]["base"] = intent.get("base", view["record"]["revision"])
        emit({"type": "AUTHOR", "view": view_id, "draft": deepcopy(view["author"]),
              "arc-title": view["record"]["title"]})
    elif kind == "select":
        if any(item["uuid"] == intent["uuid"] for item in view["chronology"]):
            view["selected"] = intent["uuid"]
        present_record_details(view_id)
    elif kind == "cancel":
        view["selected"] = prior
        present_record_details(view_id)
    elif kind == "close":
        del views[view_id]
        emit({"type": "CLOSE", "view": view_id})
        return
    present_chronology(view_id)


def reduce_authored_change_for_each_view(event):
    request, result = event["request"], event["result"]
    for view_id, view in list(views.items()):
        arc_id = view["record"]["uuid"]
        if arc_id not in result["arcs"]:
            continue
        if result["arcs"][arc_id]["revision"] != view["record"]["revision"]:
            reduce_view_change(view_id, result["arcs"][arc_id])
        view["chronology"] = deepcopy(result["chronologies"][arc_id])
        if view_id == request["view"] and view["author"] and view["author"]["uuid"] == request["draft"]["uuid"]:
            view["author"] = None
            view["selected"] = result["selected"]
        present_chronology(view_id)
        if view["author"] is None:
            present_record_details(view_id)
    say(f"Saved {request['draft']['kind']} {result['selected']}.")


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
    if search_core.reduce_search_operation_result(event):
        return
    view_id = request.get("view")
    view = views.get(view_id)
    if view:
        view["author-pending" if request["action"] in ("author", "author-refresh") else "pending"] = False
    status = result["status"]
    if status == "ready":
        g["ready"] = True
        search_core.g["types"] = result["types"]
        say(f"Ready. {result['count']} arc(s). Commands: create-arc | edit-arc <name-or-UUID> | list-arcs | search | open <handle> | help | exit")
        emit({"type": "READY"})
    elif status == "listed":
        say("\n".join(f"{r['name']}:{r['uuid']}" for r in result["arcs"]) or "No arcs.")
    elif status == "opened":
        if request["action"] == "author-refresh" and view and view["author"]:
            reduce_view_change(view_id, result["record"])
            view["author"]["base"] = result["record"]["revision"]
            emit({"type": "AUTHOR_STATUS", "view": view_id,
                  "status": "Predecessor refreshed. Your transition draft is retained."})
        elif request["action"] == "reload" and view:
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
            create_detail_view(result["record"], result["chronology"])
    elif status == "authored":
        reduce_authored_change_for_each_view(event)
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
            emit({"type": "AUTHOR_STATUS" if request["action"] in ("author", "author-refresh") else "STATUS",
                  "view": view_id, "status": result["message"]})
    if status in ("accepted", "authored"):
        search_core.refresh_searches_after_domain_change(result)
    if status in ("error", "conflict") and g["closing"]:
        g["closing"] = False
        emit({"type": "CLOSE_ABORTED", "text": "Close canceled because a save failed. Drafts are retained."})
    if view:
        emit({"type": "AUTHOR_BUSY" if request["action"] in ("author", "author-refresh") else "BUSY",
              "view": view_id, "busy": False})
        if request.get("after") and status in ("accepted", "authored") and not g["closing"]:
            emit({"type": "NAVIGATION_CONTINUE", "view": view_id, "intent": request["after"]})


def interpret_current_command_from_entry():
    reg["command"], reg["tail"], reg["args"] = cmdparts(reg["event"]["text"])
    command, args = reg["command"], reg["args"]
    if not command:
        return
    say("> " + reg["event"]["text"])
    if command == "HELP" and not args:
        say("create-arc — create and open an arc\nedit-arc <name-or-UUID> — open an existing arc\n"
            "list-arcs — print name:UUID\nsearch — open a Basic Search window\n"
            "open <name-or-UUID> — open an arc or inspect another Basic object\n"
            "help — this summary\nexit — close Arcs")
        return
    if command == "EXIT" and not args:
        emit({"type": "REQUEST_CLOSE"})
        return
    if not g["ready"]:
        say("Arcs is still starting.")
        return
    if command == "CREATE-ARC" and not args:
        enqueue_request({"action": "create", "uuid": str(uuid4())})
        say("Creating arc…")
    elif command == "LIST-ARCS" and not args:
        enqueue_request({"action": "list"})
    elif command in ("EDIT-ARC", "OPEN") and len(args) == 1:
        try:
            uuid = records.normalize_uuid(args[0])
        except ValueError:
            uuid = search_core.bindings.get(args[0])
        request = {"action": "open" if command == "EDIT-ARC" else "inspect"}
        request.update({"uuid": uuid} if uuid is not None else {"selector": args[0]})
        if command == "OPEN":
            request["source"] = "command"
        enqueue_request(request)
    elif command == "SEARCH" and not args:
        search_core.create_search_view()
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
    if search_core.reduce_search_semantic_event(event):
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
                         "fields": deepcopy(view["draft"]), "after": event.get("after")})
        emit({"type": "BUSY", "view": view_id, "busy": True})
    elif kind == "AUTHOR_NAVIGATE":
        navigate_authoring_view(view_id, event["intent"])
    elif kind == "AUTHOR_DRAFT" and view["author"] and not view["author-pending"]:
        if event["uuid"] == view["author"]["uuid"]:
            view["author"]["fields"] = deepcopy(event["fields"])
    elif kind == "AUTHOR_SAVE" and view["author"] and not view["author-pending"]:
        if event["uuid"] != view["author"]["uuid"]:
            return
        view["author"]["fields"] = deepcopy(event["fields"])
        view["author-pending"] = True
        enqueue_request({"action": "author", "view": view_id, "draft": deepcopy(view["author"]),
                         "after": event.get("after")})
        emit({"type": "AUTHOR_BUSY", "view": view_id, "busy": True})
    elif kind == "AUTHOR_REFRESH" and view["author"] and not view["author-pending"]:
        view["author-pending"] = True
        enqueue_request({"action": "author-refresh", "view": view_id, "uuid": view["record"]["uuid"]})
        emit({"type": "AUTHOR_BUSY", "view": view_id, "busy": True})
    elif kind == "OPEN_SUCCESSOR":
        selected = next((item for item in view["chronology"] if item["uuid"] == view["selected"]), None)
        if selected and selected["successor"]:
            enqueue_request({"action": "open", "uuid": selected["successor"]})
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
