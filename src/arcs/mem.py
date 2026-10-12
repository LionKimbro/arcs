"""Canonical accepted records. Commit before publishing acceptance."""

from copy import deepcopy

from . import authoring, machine, mobile_stacks, records

arcs = {}
objects = {}
links = {}


def resolve_arc_uuid_for_command_selector(selector):
    try:
        uuid = records.normalize_uuid(selector)
    except ValueError:
        uuid = None
    if uuid in arcs:
        return uuid
    matches = [record["uuid"] for record in arcs.values() if record["name"] == selector]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError("More than one arc has that name. Use list-arcs and edit-arc with its UUID.")
    raise ValueError("Unknown arc name or UUID. Use list-arcs to see available arcs.")


def handle_when_mem_receives_initial_records():
    arcs.clear()
    objects.clear()
    links.clear()
    loaded = mobile_stacks.get_register("loaded")
    objects.update(deepcopy(loaded["objects"]))
    links.update(deepcopy(loaded["links"]))
    arcs.update({uuid: record for uuid, record in objects.items() if record["type"] == "arc"})
    mobile_stacks.set_register("result", {"status": "ready", "count": len(arcs)})


def handle_when_mem_receives_arc_request():
    request = mobile_stacks.get_register("request")
    action = request["action"]
    if action == "author":
        try:
            bundle = authoring.prepare_bundle(request["draft"], {"objects": objects, "links": links})
        except ValueError as error:
            mobile_stacks.set_register("result", {"status": "error", "message": str(error)})
            return
        mobile_stacks.set_register("bundle", bundle)
        machine.continue_with_frames([{"machine": "MEM", "entry": "AUTHORED"},
                                      {"machine": "DISK", "entry": "AUTHOR_WRITE"}])
        return
    if action == "list":
        mobile_stacks.set_register("result", {"status": "listed", "arcs": [
            {"uuid": r["uuid"], "name": r["name"]}
            for r in sorted(arcs.values(), key=lambda r: (r["name"], r["uuid"]))]})
        return
    if action == "open" and "selector" in request:
        try:
            request["uuid"] = resolve_arc_uuid_for_command_selector(request["selector"])
        except ValueError as error:
            mobile_stacks.set_register("result", {"status": "error", "message": str(error)})
            return
    record = arcs.get(request["uuid"])
    if action in ("open", "reload", "author-refresh"):
        mobile_stacks.set_register("result", {"status": "opened", "record": deepcopy(record),
                                              "chronology": authoring.get_chronology(request["uuid"], {"objects": objects, "links": links})}
                                  if record else {"status": "error", "message": "Unknown arc UUID."})
        return
    if action == "create":
        if record is not None:
            raise RuntimeError("Generated UUID already exists")
        proposal = records.create_arc(request["uuid"])
        base = None
    else:
        if record is None:
            mobile_stacks.set_register("result", {"status": "error", "message": "Unknown arc UUID."})
            return
        if record["revision"] != request["base"]:
            mobile_stacks.set_register("result", {"status": "conflict", "record": deepcopy(record)})
            return
        try:
            proposal = records.prepare_arc_update(record, request["fields"])
        except ValueError as error:
            mobile_stacks.set_register("result", {"status": "error", "message": str(error)})
            return
        base = record["revision"]
    mobile_stacks.set_register("proposal", proposal)
    mobile_stacks.set_register("base", base)
    machine.continue_with_frames([
        {"machine": "MEM", "entry": "COMMITTED"},
        {"machine": "DISK", "entry": "WRITE"}])


def handle_when_mem_receives_committed_arc():
    if not mobile_stacks.get_register("committed"):
        raise RuntimeError("Missing commit acknowledgment")
    record = mobile_stacks.get_register("proposal")
    arcs[record["uuid"]] = deepcopy(record)
    objects[record["uuid"]] = arcs[record["uuid"]]
    mobile_stacks.set_register("result", {"status": "accepted", "record": deepcopy(record)})


def handle_when_mem_receives_authored_commit():
    error = mobile_stacks.get_register("write-error")
    if error:
        mobile_stacks.set_register("result", {"status": "error", "message": "Save failed: " + error})
        return
    if not mobile_stacks.get_register("committed"):
        raise RuntimeError("Missing authoring commit acknowledgment")
    bundle = mobile_stacks.get_register("bundle")
    for record in bundle["objects"]:
        objects[record["uuid"]] = deepcopy(record)
        if record["type"] == "arc":
            arcs[record["uuid"]] = objects[record["uuid"]]
    for link in bundle["links"]:
        links[link["uuid"]] = deepcopy(link)
    mobile_stacks.set_register("result", {
        "status": "authored", "selected": bundle["selected"],
        "arcs": {uuid: deepcopy(arcs[uuid]) for uuid in bundle["affected"]},
        "chronologies": {uuid: authoring.get_chronology(uuid, {"objects": objects, "links": links})
                         for uuid in bundle["affected"]}})


def run_mem_machine():
    arcs.clear()
    objects.clear()
    links.clear()
    machine.run_machine()
