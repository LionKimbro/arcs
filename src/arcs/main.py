"""Explicit composition and producer-before-consumer shutdown."""

import argparse
from queue import Queue

from . import core, disk, machine, mem, tk

worker_threads = {}


def initialize_workers_and_wire_queues():
    machine.initialize_machine_system()
    worker_threads.clear()
    for name, handlers in (
            ("CORE", {"RESULT": core.handle_when_core_receives_operation_result}),
            ("MEM", {"LOADED": mem.handle_when_mem_receives_initial_records,
                     "REQUEST": mem.handle_when_mem_receives_arc_request,
                     "COMMITTED": mem.handle_when_mem_receives_committed_arc}),
            ("DISK", {"LOAD": disk.handle_when_disk_receives_initial_load,
                      "WRITE": disk.handle_when_disk_receives_arc_write})):
        machine.install_machine({"name": name, "inbox": Queue(), "handlers": handlers})
    tk.g["outgoing"] = machine.machines["CORE"]["inbox"]
    tk.g["incoming"] = Queue()
    core.g["send"] = tk.enqueue_core_command_and_wake_tk


def start_permanent_workers_in_reference_order():
    for name, loop in (("DISK", disk.run_disk_machine), ("MEM", mem.run_mem_machine),
                       ("CORE", core.run_reducer_core)):
        worker_threads[name] = machine.start_worker(name, loop)


def finish_worker_shutdown():
    worker_threads["CORE"].join()
    worker_threads["MEM"].join()
    machine.machines["DISK"]["inbox"].put(None)
    worker_threads["DISK"].join()
    machine.reap_exited_machines()


def run_application(database=None):
    disk.initialize_database_location(database)
    initialize_workers_and_wire_queues()
    tk.build_command_center_before_workers_start()
    start_permanent_workers_in_reference_order()
    try:
        tk.run_tk_machine()
    except BaseException:
        machine.handle_when_a_worker_dies_unexpectedly()
        raise
    finally:
        finish_worker_shutdown()
    if machine.a_thread_died_unexpectedly.is_set():
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Arcs — meaningful passages of life")
    parser.add_argument("--database", help="Exact SQLite path; default is MachineRoot db-root-2026/arcs/arcs.sqlite3")
    options = parser.parse_args()
    run_application(options.database)
