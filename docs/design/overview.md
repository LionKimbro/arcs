# Specific design
Created: 2026-10-11
Modified: 2026-10-13

## Working locations and method
Created: 2026-10-11
Modified: 2026-10-11

`docs/concepts/` holds conceptual vocabulary, background, and ideas we explore without necessarily adopting in the application. Some background may not be relevant to the specific design. `docs/design-references/` is a dictionary of design ideas and a warehouse for design-related artifacts, including Wing-Cat's candidate interface design and other proposals; inclusion there does not establish design authority. `docs/design/` holds the actual application design: adopted decisions and unresolved details of those decisions. Unaccepted alternatives belong in design references, not as established design. Root-level `pseudo/` holds Bounded Agentic Development (BAD) sketches for implementation; root-level `src/` holds source code. These two directories already exist. All directory and file names are lowercase.

Lion explicitly chooses BAD: discuss a bounded area, settle its responsibilities and consequential choices, sketch it, then render it into code when requested. A bounded declaration can identify ownership, reads, calls, assumptions, guarantees, and exclusions, but the sections are flexible rather than a mandatory schema. Do not silently settle broader architectural questions during local implementation.

Keep `pseudo/` very minimal. Err on the side of minimalism: broad strokes, lightly expressed, more sketch than a total reification of the system. Do not expand sketches into exhaustive specifications, boilerplate, or a duplicate description of all implementation details.

No BAD reference was found in the supplied Librarian2 registry on October 11. The known reference, read for this discussion, is `F:\repo\bad-development-ruminition\docs\distillation\basic-method.md`. Its location is now preserved in [the project's reference table](../../db/file-system-locations.json).

## Established direction
Created: 2026-10-11
Modified: 2026-10-13

Use Today's Tk/Core/Mem/Disk architecture and Mobile Stack continuations. Disk owns SQLite persistence; Mem owns canonical in-memory domain data; Core owns application behavior and working presentation state; Tk owns presentation and event hooks on the main thread. The initial development interface is a [Command Center](command-center.md).

There is exactly one Command Center throughout a running application session. Startup opens that window alone. User commands or buttons create arcs and summon their Arc Detail windows, or open existing arcs; repeated user actions can open multiple detail windows for the same or different arcs. No arbitrary detail windows are opened at startup.

The first implementation includes both Command Center and the [Arc Detail View](arc-detail-view.md), backed by the worker architecture and SQLite. Closing Command Center shuts down the whole application; closing a detail window closes that view alone. See [the implementation handoff](implementation-handoff.md), [first-arc flow](first-arc.md), [data and persistence](data-and-persistence.md), [lifecycle](lifecycle.md), and [acceptance scenarios](acceptance-scenarios.md).

Lion reports that initial implementation is complete. The next required extension is [Arc authoring](arc-authoring.md): three buttons in each detail view for creating journal entries, creating events, and recording an event that ends the current arc and begins a new one. Their behavior is adopted specific design, not merely a candidate in design references. This documentation update does not claim that those actions are implemented yet.

Relationship persistence uses the adopted [links table](links-table.md), modeled closely on M1's Link Aspect with stable link UUIDs and general-object endpoints. Its SQL shape and migration obligations are specified; implementation remains separate.

Lion also requires [arc tags](arc-tags.md), conceptually mapping to Basic's tags list and usable for search. The [Arc Welder](../concepts/arc-welder.md) remains an exploratory neighborhood/linking interface: start from an arc and pull in candidates found by temporal overlap, temporal neighboring, or tags.

Lion has ratified [Basic Search](basic-search.md). It supports multiple independent search windows, generic Basic filters, selectable result collections, object opening, session naming, and clipboard reference/query transfer. Read [clipboard contracts](search-clipboard.md), [session names](session-names.md), and [search acceptance](basic-search-acceptance.md) with it. The [approved visual reference](../design-references/basic-search-window.md) preserves the mockup, while working-design documents govern behavior.

Develop generic search first, then arc-specific temporal queries, then the Welding Station. Basic Search has no direct Pull into Arc Welder action. It copies a JSON list of UUID strings; the future Welder offers its own pull-in action when those references resolve to arcs. Recognition alone does not import or create relationships. The complete Welder layout remains unratified, and temporal query semantics need a bounded follow-up before coding that part.

See [architecture](architecture.md) for ownership and transport. Lion has accepted the [multiple-window architecture](multiple-windows.md): one Tk main thread and one shared Core with per-view state. Returned memory-change information is offered to each window's reducer, which handles relevant changes and ignores others; polling is not required. Earlier [alternatives](../design-references/window-synchronization.md) are retained as discussion history. The earlier handoff records questions that were open before implementation; consult the current code and implementation records for decisions settled there before extending it. No application code or BAD pseudocode is changed by this authoring design update.
