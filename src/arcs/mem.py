"""Canonical accepted records. Commit before publishing acceptance."""

from copy import deepcopy

from . import machine, mobile_stacks, records

arcs = {}


def handle_when_mem_receives_initial_records():
    arcs.clear()
    for record in mobile_stacks.get_register("loaded"):
        arcs[record["uuid"]] = deepcopy(record)
    mobile_stacks.set_register("result", {"status": "ready", "count": len(arcs)})


def handle_when_mem_receives_arc_request():
    request = mobile_stacks.get_register("request")
    action = request["action"]
    if action == "list":
        mobile_stacks.set_register("result", {"status": "listed", "arcs": [
            {"uuid": r["uuid"], "name": r["name"]}
            for r in sorted(arcs.values(), key=lambda r: (r["name"], r["uuid"]))]})
        return
    record = arcs.get(request["uuid"])
    if action in ("open", "reload"):
        mobile_stacks.set_register("result", {"status": "opened", "record": deepcopy(record)}
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
    mobile_stacks.set_register("result", {"status": "accepted", "record": deepcopy(record)})


def run_mem_machine():
    arcs.clear()
    machine.run_machine()
