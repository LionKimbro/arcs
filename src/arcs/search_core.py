"""Core-owned search reducers, query generations, and session bindings."""

from copy import deepcopy
import json
from uuid import uuid4

from . import core, records, search

views = {}
bindings = {}
inspections = {}
g = {"types": []}


def initialize_search_for_new_session():
    views.clear()
    bindings.clear()
    inspections.clear()
    g["types"] = []


def create_search_view():
    view_id = str(uuid4())
    views[view_id] = {"input": search.empty_criteria(), "executed": None, "displayed": None,
                      "rows": [], "selected": [], "generation": 0, "input-generation": 0,
                      "pending": False, "user-query-pending": False,
                      "status": "Not yet searched.", "status-token": 0,
                      "offer": None, "merge": None}
    views[view_id]["selection-generation"] = 0
    core.emit({"type": "SEARCH_OPEN", "view": view_id, "types": deepcopy(g["types"])})
    present_search(view_id)


def present_search(view_id):
    view = views[view_id]
    core.emit({"type": "SEARCH_PRESENT", "view": view_id, "rows": deepcopy(view["rows"]),
               "selected": list(view["selected"]), "executed": deepcopy(view["displayed"]),
               "pending": view["pending"], "status": view["status"], "types": deepcopy(g["types"]),
               "selection-blocked": view["user-query-pending"],
               "aliases": deepcopy(bindings), "selection-generation": view["selection-generation"]})


def request_query(view_id, refresh=False):
    view = views[view_id]
    if not refresh:
        view["executed"] = search.validate_criteria(view["input"])
        view["selected"] = []
        view["user-query-pending"] = True
    view["generation"] += 1
    view["status-token"] += 1
    view["pending"] = True
    view["status"] = "Refreshing executed search…" if refresh else "Searching…"
    core.enqueue_request({"action": "search", "view": view_id, "generation": view["generation"],
                          "criteria": deepcopy(view["executed"]), "refresh": refresh})
    present_search(view_id)


def reduce_search_operation_result(event):
    request, result = event["request"], event["result"]
    view_id = request.get("view")
    if request["action"] == "search":
        view = views.get(view_id)
        if not view or view["generation"] != request["generation"]:
            return True
        view["pending"] = False
        view["user-query-pending"] = False
        if result["status"] == "searched":
            g["types"] = result["types"]
            view["rows"] = deepcopy(result["rows"])
            view["displayed"] = deepcopy(request["criteria"])
            available = {row["uuid"] for row in view["rows"]}
            view["selected"] = [uuid for uuid in view["selected"] if uuid in available]
            view["status"] = "Results refreshed." if request["refresh"] else "Search complete."
        else:
            view["status"] = "Search failed: " + result["message"]
        present_search(view_id)
        return True
    if request["action"] in ("inspect", "inspect-refresh"):
        if request["action"] == "inspect" and request.get("source") != "command" and view_id not in views:
            return True
        if request["action"] == "inspect-refresh" and view_id not in inspections:
            return True
        if result["status"] == "error":
            if request.get("source") == "command":
                core.say("Error: " + result["message"])
            elif view_id in views:
                views[view_id]["status"] = result["message"]
                present_search(view_id)
            else:
                core.emit({"type": "INSPECT_STATUS", "view": view_id, "status": result["message"]})
        elif result["record"]["type"] == "arc":
            if not core.g["closing"]:
                core.create_detail_view(result["record"], result["chronology"])
        elif not core.g["closing"]:
            if request["action"] == "inspect":
                view_id = str(uuid4())
                inspections[view_id] = result["record"]["uuid"]
                kind = "INSPECT_OPEN"
            else:
                kind = "INSPECT_UPDATE"
            core.emit({"type": kind, "view": view_id, "record": deepcopy(result["record"])})
        return True
    return False


def refresh_searches_after_domain_change(result):
    changed = ({result["record"]["uuid"]} if result["status"] == "accepted"
               else set(result["arcs"]) | {result["selected"]})
    for view_id, view in list(views.items()):
        if view["executed"] is not None and not core.g["closing"]:
            request_query(view_id, True)
    for view_id, uuid in list(inspections.items()):
        if uuid in changed and not core.g["closing"]:
            core.enqueue_request({"action": "inspect-refresh", "view": view_id, "uuid": uuid})


def install_search_input(view_id, criteria):
    view = views[view_id]
    expected = deepcopy(view["input"])
    view["input"] = search.validate_criteria(criteria)
    view["input-generation"] += 1
    view["merge"] = None
    core.emit({"type": "SEARCH_INPUT", "view": view_id, "criteria": deepcopy(view["input"]), "expected": expected})


def classify_search_clipboard_for_view(view_id, event):
    view = views[view_id]
    view["offer"] = None
    core.emit({"type": "SEARCH_OFFER", "view": view_id, "available": False})
    if event.get("error"):
        view["status"] = event["error"]
    else:
        classified = search.classify_clipboard(event["text"])
        if classified["kind"] == "search":
            view["offer"] = classified["criteria"]
    core.emit({"type": "SEARCH_OFFER", "view": view_id, "available": view["offer"] is not None})
    present_search(view_id)


def prepare_clipboard_adoption_for_view(view_id, event):
    view = views[view_id]
    if event.get("error"):
        raise ValueError(event["error"])
    incoming = search.classify_clipboard(event["text"])
    if incoming["kind"] != "search":
        raise ValueError("The clipboard no longer contains a supported search.")
    if event["mode"] == "reset":
        install_search_input(view_id, incoming["criteria"])
    else:
        merge = search.get_incorporation(view["input"], incoming["criteria"])
        if merge["conflicts"]:
            merge.update(token=str(uuid4()), generation=view["input-generation"])
            view["merge"] = merge
            core.emit({"type": "SEARCH_CONFLICTS", "view": view_id, "merge": deepcopy(merge)})
        else:
            install_search_input(view_id, merge["criteria"])
    view["status"] = "Clipboard adoption does not run a search. Press Search when ready."
    present_search(view_id)


def finish_clipboard_incorporation_for_view(view_id, event):
    view = views[view_id]
    merge = view["merge"]
    if not merge or merge["token"] != event["token"] or merge["generation"] != view["input-generation"]:
        raise ValueError("Parameters changed during incorporation. Please incorporate again.")
    criteria = deepcopy(merge["criteria"])
    choices = event["choices"]
    if set(choices) != {conflict["field"] for conflict in merge["conflicts"]}:
        raise ValueError("Resolve every conflicting criterion before applying.")
    for field, choice in choices.items():
        if choice not in ("current", "incoming"):
            raise ValueError("Invalid incorporation choice.")
        if choice == "incoming":
            criteria[field] = deepcopy(merge["incoming"][field])
            if field == "tags":
                criteria["tag-match"] = merge["incoming"]["tag-match"]
    install_search_input(view_id, criteria)
    view["status"] = "Criteria incorporated. Press Search to execute."
    present_search(view_id)


def assign_session_names_from_selection(view_id, event):
    view = views[view_id]
    assignments = event["assignments"]
    if not isinstance(assignments, list) or not assignments or len(assignments) != len(view["selected"]):
        raise ValueError("Enter a session name for every selected object.")
    proposal = {}
    for assignment in assignments:
        name = search.validate_session_name(assignment["name"])
        uuid = assignment["uuid"]
        if name in proposal:
            raise ValueError("Each selected object needs a distinct session name.")
        if uuid not in view["selected"]:
            raise ValueError("The naming selection changed. Reopen the session-name editor.")
        proposal[name] = uuid
    if {item["uuid"] for item in assignments} != set(view["selected"]):
        raise ValueError("Enter one name for each selected object.")
    conflicts = [{"name": name, "current": bindings[name], "incoming": uuid}
                 for name, uuid in proposal.items() if name in bindings and bindings[name] != uuid]
    approved = event.get("replacements", {})
    if any(approved.get(item["name"]) != item["current"] for item in conflicts):
        core.emit({"type": "SESSION_CONFLICTS", "view": view_id, "assignments": deepcopy(assignments),
                   "conflicts": conflicts})
        return
    bindings.update(proposal)
    view["status"] = "Session names assigned. Basic records are unchanged."
    core.emit({"type": "SESSION_ASSIGNED", "view": view_id})
    for target in list(views):
        present_search(target)


def reduce_search_semantic_event(event):
    kind, view_id = event["type"], event.get("view")
    if kind == "INSPECT_CLOSE":
        inspections.pop(view_id, None)
        core.emit({"type": "INSPECT_CLOSE", "view": view_id})
        return True
    if kind == "INSPECT_OPEN_ARC":
        if view_id in inspections:
            core.enqueue_request({"action": "open", "uuid": event["uuid"]})
        return True
    if not kind.startswith("SEARCH_") and kind != "SESSION_ASSIGN":
        return False
    if view_id not in views:
        return True
    view = views[view_id]
    if kind not in ("SEARCH_STATUS", "SEARCH_CLIPBOARD"):
        view["status-token"] += 1
    try:
        if kind == "SEARCH_CLOSE":
            del views[view_id]
            core.emit({"type": "SEARCH_CLOSE", "view": view_id})
        elif kind == "SEARCH_INPUT":
            view["input"] = search.validate_criteria(event["criteria"])
            view["input-generation"] += 1
            view["merge"] = None
        elif kind == "SEARCH_RUN":
            view["input"] = search.validate_criteria(event["criteria"])
            view["input-generation"] += 1
            view["merge"] = None
            view["selection-generation"] = event.get("selection-generation", view["selection-generation"] + 1)
            request_query(view_id)
        elif kind == "SEARCH_SELECT":
            if view["user-query-pending"]:
                return True
            generation = event.get("selection-generation", view["selection-generation"] + 1)
            if generation >= view["selection-generation"]:
                selected = set(event["uuids"])
                view["selected"] = [row["uuid"] for row in view["rows"] if row["uuid"] in selected]
                view["selection-generation"] = generation
            present_search(view_id)
        elif kind == "SEARCH_OPEN_SELECTED" and len(view["selected"]) == 1 and not view["user-query-pending"]:
            core.enqueue_request({"action": "inspect", "view": view_id, "uuid": view["selected"][0]})
        elif kind == "SEARCH_COPY_REFERENCES" and view["selected"]:
            core.emit({"type": "SEARCH_COPY", "view": view_id, "text": json.dumps(view["selected"]),
                       "status": "Copied UUID references as a JSON array.", "status-token": view["status-token"]})
        elif kind == "SEARCH_COPY_QUERY":
            core.emit({"type": "SEARCH_COPY", "view": view_id, "text": search.serialize_search(event["criteria"]),
                       "status": "Copied the current search parameters.", "status-token": view["status-token"]})
        elif kind == "SEARCH_CLIPBOARD":
            classify_search_clipboard_for_view(view_id, event)
        elif kind == "SEARCH_ADOPT":
            view["input"] = search.validate_criteria(event["criteria"])
            view["input-generation"] += 1
            prepare_clipboard_adoption_for_view(view_id, event)
        elif kind == "SEARCH_MERGE":
            finish_clipboard_incorporation_for_view(view_id, event)
        elif kind == "SESSION_ASSIGN":
            assign_session_names_from_selection(view_id, event)
        elif kind == "SEARCH_STATUS":
            if event.get("status-token", view["status-token"]) == view["status-token"]:
                view["status"] = event["status"]
                present_search(view_id)
    except ValueError as error:
        view["status"] = str(error)
        if kind == "SESSION_ASSIGN":
            core.emit({"type": "SESSION_ERROR", "view": view_id, "status": str(error)})
        present_search(view_id)
    return True
