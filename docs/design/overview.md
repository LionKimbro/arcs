# Specific design
Created: 2026-10-11
Modified: 2026-10-11

## Working locations and method
Created: 2026-10-11
Modified: 2026-10-11

`docs/concepts/` holds conceptual vocabulary, background, and ideas we explore without necessarily adopting in the application. Some background may not be relevant to the specific design. `docs/design-references/` is a dictionary of design ideas and a warehouse for design-related artifacts, including Wing-Cat's candidate interface design and other proposals; inclusion there does not establish design authority. `docs/design/` holds the actual application design: adopted decisions and unresolved details of those decisions. Unaccepted alternatives belong in design references, not as established design. Root-level `pseudo/` holds Bounded Agentic Development (BAD) sketches for implementation; root-level `src/` holds source code. These two directories already exist. All directory and file names are lowercase.

Lion explicitly chooses BAD: discuss a bounded area, settle its responsibilities and consequential choices, sketch it, then render it into code when requested. A bounded declaration can identify ownership, reads, calls, assumptions, guarantees, and exclusions, but the sections are flexible rather than a mandatory schema. Do not silently settle broader architectural questions during local implementation.

Keep `pseudo/` very minimal. Err on the side of minimalism: broad strokes, lightly expressed, more sketch than a total reification of the system. Do not expand sketches into exhaustive specifications, boilerplate, or a duplicate description of all implementation details.

No BAD reference was found in the supplied Librarian2 registry on October 11. The known reference, read for this discussion, is `F:\repo\bad-development-ruminition\docs\distillation\basic-method.md`. Its location is now preserved in [the project's reference table](../../db/file-system-locations.json).

## Established direction
Created: 2026-10-11
Modified: 2026-10-11

Use Today's Tk/Core/Mem/Disk architecture and Mobile Stack continuations. Disk owns SQLite persistence; Mem owns canonical in-memory domain data; Core owns application behavior and working presentation state; Tk owns presentation and event hooks on the main thread. The initial development interface is a [Command Center](command-center.md).

There is exactly one Command Center throughout a running application session. Startup opens that window alone. User commands or buttons create arcs and summon their Arc Detail windows, or open existing arcs; repeated user actions can open multiple detail windows for the same or different arcs. No arbitrary detail windows are opened at startup.

The first implementation includes both Command Center and the [Arc Detail View](arc-detail-view.md), backed by the worker architecture and SQLite. Closing Command Center shuts down the whole application; closing a detail window closes that view alone. See [the implementation handoff](implementation-handoff.md), [first-arc flow](first-arc.md), [data and persistence](data-and-persistence.md), [lifecycle](lifecycle.md), and [acceptance scenarios](acceptance-scenarios.md).

See [architecture](architecture.md) for ownership and transport. Lion has accepted the [multiple-window architecture](multiple-windows.md): one Tk main thread and one shared Core with per-view state. Returned memory-change information is offered to each window's reducer, which handles relevant changes and ignores others; polling is not required. Earlier [alternatives](../design-references/window-synchronization.md) are retained as discussion history. SQL schema, command vocabulary, database location, and memory layout remain open. No application implementation or BAD pseudocode has been authored by this design pass.
