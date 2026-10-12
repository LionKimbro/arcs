"""Permanent worker runtime, adapted from Today's machine.py."""

from threading import Event, RLock, Thread, current_thread, local, main_thread
import traceback

machines = {}
thread_state = local()
machines_lock = RLock()
a_thread_died_unexpectedly = Event()


def initialize_machine_system():
    with machines_lock:
        if any(r["thread"] and r["thread"].is_alive() for r in machines.values()):
            raise RuntimeError("cannot reset live workers")
        machines.clear()
        a_thread_died_unexpectedly.clear()


def install_machine(runtime):
    runtime.update({"thread": None, "lifecycle": "starting", "running": False,
                    "current-stack": None, "continuation-frames": None})
    machines[runtime["name"]] = runtime


def start_worker(name, worker_loop):
    with machines_lock:
        runtime = machines[name]
        if runtime["thread"] is not None:
            raise RuntimeError("worker already started")
        thread = Thread(target=handle_entire_worker_execution, args=(name, worker_loop),
                        name=f"Arcs {name}")
        runtime["thread"] = thread
        thread.start()
        return thread


def claim_machine(name):
    thread_state.runtime = machines[name]


def get_current_runtime():
    return thread_state.runtime


def get_current_inbox():
    return get_current_runtime()["inbox"]


def handle_entire_worker_execution(name, worker_loop):
    claim_machine(name)
    runtime = get_current_runtime()
    try:
        runtime["lifecycle"] = "running"
        runtime["running"] = True
        if not a_thread_died_unexpectedly.is_set():
            worker_loop()
        if runtime["running"] and not a_thread_died_unexpectedly.is_set():
            raise RuntimeError(f"{name} returned unexpectedly")
    except BaseException:
        traceback.print_exc()
        handle_when_a_worker_dies_unexpectedly()
    finally:
        runtime.update({"running": False, "current-stack": None,
                        "continuation-frames": None, "lifecycle": "exited"})


def handle_when_a_worker_dies_unexpectedly():
    with machines_lock:
        if a_thread_died_unexpectedly.is_set():
            return
        a_thread_died_unexpectedly.set()
        for runtime in machines.values():
            runtime["inbox"].put(None)


def request_machine_retirement():
    get_current_runtime().update({"running": False, "lifecycle": "stopping"})


def reap_exited_machines():
    if current_thread() is not main_thread():
        raise RuntimeError("only main may reap workers")
    for name, runtime in list(machines.items()):
        if runtime["lifecycle"] == "exited":
            runtime["thread"].join()
            runtime["lifecycle"] = "reaped"
            del machines[name]


def continue_with_frames(frames):
    runtime = get_current_runtime()
    if runtime["continuation-frames"] is not None:
        raise RuntimeError("continuation already installed")
    runtime["continuation-frames"] = list(frames)


def clear_current_stack():
    get_current_runtime()["current-stack"] = None


def route_current_stack():
    from . import mobile_stacks

    with machines_lock:
        if a_thread_died_unexpectedly.is_set():
            clear_current_stack()
            return
        target = machines[mobile_stacks.top()["machine"]]
        if target["lifecycle"] not in ("starting", "running"):
            raise RuntimeError("cannot route to a retired worker")
        stack = mobile_stacks.stack()
        clear_current_stack()
        target["inbox"].put(stack)


def handle_received_mobile_stack(stack):
    from . import mobile_stacks

    if a_thread_died_unexpectedly.is_set():
        return
    runtime = get_current_runtime()
    if runtime["current-stack"] is not None:
        raise RuntimeError("active stack would be replaced")
    runtime["current-stack"] = stack
    frame = mobile_stacks.top()
    if frame["machine"] != runtime["name"]:
        raise RuntimeError("wrong stack destination")
    runtime["handlers"][frame["entry"]]()
    mobile_stacks.drop_frame()
    if runtime["continuation-frames"] is not None:
        stack["frames"].extend(runtime["continuation-frames"])
        runtime["continuation-frames"] = None
    if mobile_stacks.has_frames():
        route_current_stack()
    else:
        clear_current_stack()


def run_machine():
    runtime = get_current_runtime()
    while runtime["running"] and not a_thread_died_unexpectedly.is_set():
        item = runtime["inbox"].get()
        if item is None or a_thread_died_unexpectedly.is_set():
            request_machine_retirement()
            return
        handle_received_mobile_stack(item)
