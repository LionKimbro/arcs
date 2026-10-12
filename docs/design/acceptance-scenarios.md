# Initial acceptance scenarios
Created: 2026-10-11
Modified: 2026-10-11

## Primary user scenario
Created: 2026-10-11
Modified: 2026-10-11

Launch against an isolated empty SQLite database. Command Center appears with a large output area and a command entry. Once ready, type commands to create three independent arcs. Each creation reports its UUID and opens that arc's actual detail window. All three windows remain open with their own titles, names, descriptions, boundaries, and empty chronology/no-selection states. Command Center remains usable.

Verify exactly one Command Center and no Arc Detail windows at startup, even with an existing database. No arcs or sample windows are created automatically. The three detail windows appear individually as the user issues the three creation actions. Opening an existing UUID is a separate user action that can summon another view of that same arc.

Close one detail window: the application and the other windows continue running, and the record remains. Reopen that UUID. Close Command Center: all windows close, submitted writes finish under the normal save contract, the SQLite connection closes on Disk, and every worker terminates. Restart against the same database, list the arcs, and reopen all three with unchanged identities and persisted data.

## View isolation and change distribution
Created: 2026-10-11
Modified: 2026-10-11

Open two views of the same arc, using a development action or test hook if ordinary opening reuses windows. Different selections or drafts remain view-local. A Mem accepted-change return is offered to both reducers; both refresh relevant accepted information and neither silently overwrites its draft. A third window showing an unrelated arc ignores the change. Exercise this through supported editing if delivered, or through isolated reducer tests when editing has not yet shipped.

An operation completing after its originating view closes still updates canonical/application data and other relevant views. An obsolete selection result cannot replace the newest selected item. No return or presentation command accesses a destroyed Tk window.

## Ownership and persistence verification
Created: 2026-10-11
Modified: 2026-10-11

Verify that Tk callbacks do not open SQLite or perform domain work; the SQLite connection is created, used, and closed by Disk; and copied snapshots/register results cannot mutate Mem's canonical containers. Thread-local machine selection, runtime-owned frame completion, and transfer-before-queue-publication follow the current Today mechanisms.

Invalid creation input, malformed commands, and unknown UUIDs return readable errors without partial records. An isolated injected Disk commit failure must not print successful saved completion. Closing during a held save must wait for the necessary return path before its workers retire. Do not inspect a test database while another worker owns an uncompleted transaction and treat that as proof of success.

## Lifecycle verification
Created: 2026-10-11
Modified: 2026-10-11

Run worker-only checks and actual Tk integration checks; they prove different things. Confirm normal close with several detail windows and no remaining workers. Inject Core, Mem, and Disk failures independently in fresh processes and check fatal closure and nonzero exit. Confirm idempotent repeated close and failure notifications. Final SQLite write failure must not become a successful saved exit.

These are design-level verification targets, not a request for a large redundant test framework. Use isolated temporary databases and meaningful checks for the delivered behavior. Exact test commands and launch conventions belong to the implementation conversation after its environment and packaging are settled.
