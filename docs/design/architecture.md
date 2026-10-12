# Architecture
Created: 2026-10-11
Modified: 2026-10-11

## Established ownership
Created: 2026-10-11
Modified: 2026-10-11

Lion explicitly adopts the architecture used by Today. This is a current decision, independent of the date-limited October 7 work note. Borrow the worker and continuation pattern while designing Arcs-specific memory, persistence, and application behavior.

| Machine | Owns |
| --- | --- |
| Tk | Main-thread widgets, presentation, native UI event hooks, and the widget references needed to present windows |
| Core | Application behavior, reducer processing and effects, working view state, and semantic presentation commands |
| Mem | Canonical in-memory domain records and their relationships |
| Disk | SQLite access and durable data reads and writes |

Tk captures input and sends semantic data; it does not parse application commands, operate the database, or perform domain work. Core's view snapshots and drafts are distinct from Mem's canonical domain records. Disk ownership includes the database connection and transaction operations. Core coordinates one Command Center reducer and one reducer for each on-demand Arc Detail view, all within the same worker. Exact Mem data layout and commit protocol need bounded sketches before implementation.

## Queues and Tk seam
Created: 2026-10-11
Modified: 2026-10-11

Use Core, Mem, and Disk inboxes plus a dedicated Core-to-Tk presentation-command queue, following Today. Tk sends semantic events into Core's inbox; Core also receives returned Mobile Stacks there. Tk drains its command queue on the established main-thread wake mechanism. Widgets and Tk objects remain on the Tk side; data crossing the seam is ordinary semantic data.

Tk's main thread remains responsive while worker requests are outstanding. Detailed wake, lifecycle, error, and shutdown behavior should follow the current Today mechanisms as explicitly adapted in later sketches, rather than being reconstructed from old intermediate pseudocode alone.

## Mobile Stacks
Created: 2026-10-11
Modified: 2026-10-11

A Mobile Stack travels between machines with registers carrying context and bottom-first frames carrying continuation control. The top frame identifies the next machine and handler. Queue publication transfers ownership; the sender clears its active stack slot before publication. The receiver installs the stack as its current stack. In Today's current runtime, handlers leave the executing frame in place and runtime removes it after return, then routes the next frame. This preserves the return path without a callback registry. Same-machine continuations still travel through the inbox.

Core converts returned register data to independently retained reducer-event data before the stack continues or completes. Stack context belongs to the operation; it must not become shared mutable canonical data. Operation identity and view targeting for multiple windows are discussed in [the accepted multiple-window design](multiple-windows.md).

For accepted memory changes, Core offers the returned information to each window's reducer. Each handles relevant changes, including producing targeted Tk commands, and ignores irrelevant changes. Polling is not required for this synchronization path.

## Persistence and interoperability
Created: 2026-10-11
Modified: 2026-10-11

SQLite is selected for persistence, with Disk owning its use. Mem owns the in-memory domain model. Acceptance into Mem and completion of a SQLite transaction are different milestones; the save acknowledgment and shutdown policies remain to be specified. Each arc has a stable UUID. Storage must remain conceptually mappable to M1, and temporal representation must preserve ChronoMark uncertainty.

FileTalk handles communication with Today, Focus, and the future Project Browser. It is separate from the internal worker queues and Mobile Stacks.

## Reference and unresolved boundaries
Created: 2026-10-11
Modified: 2026-10-11

Primary reference: `F:\repo\today\docs\architecture-review.md` (October 6 report). Supporting sketches include `F:\repo\today\pseudo\systems\tk-core.md`, `pseudo/model/mobile-stack.md`, and `pseudo/modules/mobile-stacks.md`. Some Today sketches retain intermediate descriptions; use the report's runtime-owned frame completion when they differ.

Database location, SQLite schema, loading/caching, revision conflicts, draft retention, save completion, and exact command syntax remain open. Lifetime is settled: one Command Center anchors the session; user actions summon detail windows; closing Command Center initiates orderly global shutdown. See [lifecycle](lifecycle.md) for the inspected Today sequence and SQLite adaptation, and [data and persistence](data-and-persistence.md) for protocol gates.
