"""Inject fatal workers or a final SQLite write failure in a fresh Tk process."""

import argparse
from threading import enumerate as enumerate_threads

from arcs import core, disk, machine, main, mem, tk

g = {"write-failure": False, "requested": False}


def handle_when_test_injects_worker_failure():
    raise RuntimeError("Injected fatal worker failure")


def handle_when_test_injects_write_failure():
    connection = disk.g["connection"]
    connection.execute("CREATE TEMP TRIGGER fail_arc BEFORE INSERT ON arc "
                       "BEGIN SELECT RAISE(ABORT, 'Injected Arc aspect failure'); END")
    disk.handle_when_disk_receives_arc_write()


def handle_when_failure_test_checks_readiness():
    if not g["requested"] and "Ready." in tk.widgets["output"].get("1.0", "end"):
        g["requested"] = True
        machine.machines["DISK"]["handlers"]["WRITE"] = handle_when_test_injects_write_failure
        tk.widgets["entry"].insert(0, "create-arc")
        tk.handle_when_user_submits_command(None)
        tk.handle_when_user_closes_command_center()
    if not tk.g["closing"]:
        tk.g["root"].after(20, handle_when_failure_test_checks_readiness)


def main_test():
    parser = argparse.ArgumentParser()
    parser.add_argument("failure", choices=("CORE", "MEM", "DISK", "WRITE"))
    parser.add_argument("database")
    options = parser.parse_args()
    if options.failure == "WRITE":
        original = tk.build_command_center_before_workers_start

        def build_window_and_schedule_failure_check():
            original()
            tk.g["root"].after(20, handle_when_failure_test_checks_readiness)

        tk.build_command_center_before_workers_start = build_window_and_schedule_failure_check
    else:
        module, attribute = {"CORE": (core, "run_reducer_core"), "MEM": (mem, "run_mem_machine"),
                             "DISK": (disk, "run_disk_machine")}[options.failure]
        setattr(module, attribute, handle_when_test_injects_worker_failure)
    try:
        main.run_application(options.database)
    except SystemExit as error:
        assert error.code == 1
        assert not any(thread.name.startswith("Arcs ") for thread in enumerate_threads())
        assert disk.g["connection"] is None
        print("Fatal Tk", options.failure, "closed and joined; exit 1")
        raise
    raise AssertionError("Fatal failure returned success")


if __name__ == "__main__":
    main_test()
