# Basic Search acceptance
Created: 2026-10-13
Modified: 2026-10-13

## Generic search slice
Created: 2026-10-13
Modified: 2026-10-13

Open two Basic Search windows on demand while the one Command Center remains open. Each starts not-yet-searched. In one search arcs with title containing a chosen substring; in the other search journal entries or events by a different name/tag condition. Verify real results from canonical data, no fictional mockup data, and independent specifications, result collections, selections, and status.

Verify case-insensitive name/title substrings, populated filters combined with AND, all/any tag modes, no-constraint empty filters, and supported Basic object kinds. Link-only records without Basic metadata are not included. Editing or clearing parameters leaves old results visibly associated with their executed query until Search. Running a new query clears selection. Select one and then several results and confirm enabled actions match selection cardinality.

Open a selected arc without duplicating Command Center. Inspect other supported object kinds through their real detail presentation. Close one search window while its request is held and return the result afterward: no destroyed widget is touched and another search remains usable. Rapid repeated searches cannot install an older response over a newer one. Domain changes refresh affected executed searches and preserve surviving selected UUIDs without overwriting edited parameters.

## Session naming
Created: 2026-10-13
Modified: 2026-10-13

Assign `a` to one selected object and several distinct names through a multi-selection editor. Resolve the same bindings from another window. Verify Basic fields and UUIDs are unchanged and search substring input is not expanded as a handle. A session name matching a Basic name shadows it. Rebinding a name from one UUID to another requires explicit confirmation; duplicate inputs in one batch do not partially apply. Closing a search window preserves application-session bindings; application restart clears them.

## Clipboard
Created: 2026-10-13
Modified: 2026-10-13

Copy one and several selected references. Verify actual system clipboard text parses as a JSON array of full UUID strings, without a wrapper and without session names. Copy the edited query and adopt it in another search window. Recognition alone changes neither parameters nor results. Reset replaces parameters; incorporation retains compatible current filters and exposes conflicting populated fields. Canceling conflict resolution preserves the original query. Adoption requires Search to execute. Unsupported versions/criteria and clipboard access failures return clear status without erasing state.

Use the clipboard without any Arc Welder present; copying references does not require or open one. Search has no Pull into Arc Welder button. The Welder receiver contract is verified when that later slice exists, not through a dummy working-looking button in search.

## Temporal and Welder slices
Created: 2026-10-13
Modified: 2026-10-13

Temporal controls and queries require their own bounded criteria/uncertainty design. Verify actual overlap/proximity against resolved and uncertain ChronoMark data once implemented, not merely that controls can be drawn. Preserve range precision/timezone and explicit unknown/ongoing behavior. Choosing a non-arc search kind must not hide an active incompatible arc filter.

When the Welder is implemented, a nonempty clipboard UUID array resolving entirely to arcs makes its pull-in action available. Recognition creates no workspace items. Click imports those existing UUIDs into that Welder, without duplicate arcs, domain links, or boundary changes. Invalid, mixed, or unresolved arrays are not silently partially imported.

## Implementation discipline
Created: 2026-10-13
Modified: 2026-10-13

Use temporary databases and real Tk checks alongside reducer/worker checks. Disk owns SQL; Tk owns the system clipboard. The adopted four-machine architecture and global shutdown contract remain intact. Keep BAD sketches small and cover behavior with meaningful checks rather than mirroring every line of implementation. Apply schema migration only for fields missing from current Basic/tag data; preserve existing UUIDs and records.
