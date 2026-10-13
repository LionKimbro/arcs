# Basic Search
Created: 2026-10-13
Modified: 2026-10-13

## Adoption and implementation scope
Created: 2026-10-13
Modified: 2026-10-13

Lion ratifies the Basic Search window design, including the refinement that search copies UUID references rather than directly sending results to the Arc Welder. This is specific application design. The approved visual is preserved in [the reference record](../design-references/basic-search-window.md); its HTML is an interactive illustration, not application code or a normative query engine.

Implement in bounded parts: generic Basic search first, arc-specific temporal search next, then the Welding Station. The generic slice includes real searches, separate windows, selection actions, session naming, and query/reference clipboard operations. It must not use the mockup's fictional data, simulated clipboard, or simplified date comparisons. Arc timing is the adopted next extension, but interval/uncertainty semantics and its range payload need a narrow design pass before implementation. Do not ship a working-looking temporal control that silently does nothing.

The Welder's clipboard pull-in contract is agreed, but building the Welder is a later slice. No direct Pull into Arc Welder button belongs in Basic Search. This design handoff does not authorize this conversation to implement code; Lion will instruct the programming agent separately.

## Window lifetime and independence
Created: 2026-10-13
Modified: 2026-10-13

Users can open several Basic Search windows on demand. Each has its own view identity, editable search specification, last executed specification, results collection, selection, naming editor, status, and outstanding request token. Changing or closing one does not change another. Command Center remains singular and continues to anchor application lifetime. Add a Command Center route for opening a search window; exact command spelling follows the current parser conventions.

An empty search window does not run automatically merely because it opens. It presents criteria and a clear not-yet-searched state. Search with empty filters finds all supported Basic objects. The mockup starts with example results so the layout can be inspected; that is not permission to create sample objects or query without a user action in the real application.

## Layout and search parameters
Created: 2026-10-13
Modified: 2026-10-13

The window has three regions: parameters at the top, results in the middle, and actions on selected objects at the bottom. Use the existing Tk styling and resizable native window conventions; the reference's spacing and colors illustrate the arrangement rather than requiring a new UI framework.

Initial parameters are object type, name contains, title contains, and tags with an All tags/Any tag choice. Type offers all Basic objects and kinds represented in the application's Basic data, including arcs, events, journal entries, and links when they have optional Basic metadata. A link existing only in links is not a Basic result. Do not make a Basic row for every link solely to populate search.

Name and title are separate substring filters, not handle resolution or equality lookup. For the initial interface use case-insensitive matching while preserving stored spelling. Tags match complete classification labels, with case-insensitive matching and surrounding query whitespace ignored; All requires all entered labels and Any requires at least one. Empty tag input imposes no constraint. Combine populated type/name/title/tag filters with AND. A clear delimiter or token control must make multiple tags unambiguous; commas are the approved mockup's example. Do not silently split stored tags on spaces. Actual tag storage and editing follow [arc tags](arc-tags.md).

Provide **Search**, **Clear parameters**, and **Copy search**. Editing criteria marks them as changed but retains the old results until Search is pressed. Make that distinction visible. Clear parameters clears query input, not saved records, session bindings, or another window's search. It does not automatically run. Show waiting/error state for requests without pretending stale results match the edited input.

## Results and selection
Created: 2026-10-13
Modified: 2026-10-13

Display one row per matching Basic object, keyed by full UUID. Show its title and Basic name, object type, tags, and associated Basic date where available. Empty fields stay empty or unknown; do not substitute creation time for occurrence time. Full UUID should be inspectable, with an optional UUID column/display useful during development. Never use shortened UUIDs as actual reference values.

Support individual checkboxes and selecting all currently returned rows. Show result count and selection count. Selections are local to that window. Results are a collection for the executed query, not copies of domain objects and not automatically assigned M1 membership links. The initial implementation can use a stable title/name/UUID order; sorting refinements and pagination can follow actual need. Do not truncate matches silently.

On a new user-executed search, clear selection so actions cannot accidentally target objects from an old query. On a domain-driven refresh of the same executed query, preserve selected UUIDs still present. Return changes can cause objects to enter or leave the result set; update from accepted data without overwriting the user's edited parameters. Identify which executed specification the collection belongs to.

## Selection actions
Created: 2026-10-13
Modified: 2026-10-13

Provide **Open selected**, **Name selected object(s)…**, and **Copy reference(s)**. With no selection, disable them. Open selected initially requires exactly one object. For an arc, summon its Arc Detail view; for an event or journal entry, use the application's object detail presentation rather than silently doing nothing. Other Basic kinds need a minimal inspect view or a clear unsupported-open explanation. Opening does not alter the query or create another Command Center.

Naming opens a compact editor with a separate session-name field for each selected object. Assign names to the individual UUIDs; do not implicitly name the result collection or rename Basic records. Follow [session names](session-names.md), including shadowing and explicit rebinding. Copy reference(s) works for any selected Basic kinds, not only arcs, and uses the exact format in [search clipboard](search-clipboard.md).

## Clipboard offers
Created: 2026-10-13
Modified: 2026-10-13

When a supported search definition is recognized on the clipboard, offer two distinct actions near the parameters: **Reset to clipboard search** and **Incorporate…**. Neither recognition nor adoption executes a search. After adoption show the new parameters and require Search. Do not disturb the old result collection until execution.

Reset replaces the query input, clearing fields absent in the payload. Incorporation preserves existing input and adds compatible criteria; conflict behavior is defined in [search clipboard](search-clipboard.md). An object-reference UUID array must not be misinterpreted as a search definition. A later supported temporal-range payload offers range-context adoption, not arbitrary code execution or a guessed query.

## Arc-specific extension
Created: 2026-10-13
Modified: 2026-10-13

When the search is restricted to arcs, expose a clearly grouped Arc timing area. It supplies reference range context and predicates such as overlap and neighboring within a number of days/months/years/decades. Range context may come from the planned Copy temporal range action in an Arc Detail view. Do not use Basic's loose date alone as an arc interval or reuse the mockup's comparisons as the query implementation.

Preserve ChronoMark uncertainty, multiple unresolved claims, precision, timezone, and ongoing/unknown boundaries. Define possible versus definite matching, interval adjacency, calendar-unit distance, and working-claim selection before this temporal slice. If switching back to an unrestricted or non-arc type while temporal criteria are present, visibly ask to clear incompatible criteria or retain the arc restriction; do not hide a still-active filter or silently ignore it.

## Machine ownership and data updates
Created: 2026-10-13
Modified: 2026-10-13

All Tk widgets, clipboard reads/writes, and presentation are owned by the Tk main thread. Core interprets semantic events, owns per-search-window reducer state and session bindings, and dispatches effects. Mem searches its accepted canonical Basic data or supplies query snapshots according to the established load strategy; Disk owns any SQL and schema migrations. No SQLite work occurs in a Tk callback.

Carry the view identity and a query-generation token through the Mobile Stack. Core retains results as independent event data before the stack completes. A closed view or superseded query cannot receive an obsolete result as its current collection. Accepted domain-change information is offered to every window reducer; each search reducer decides whether its executed query needs refresh. This follows existing return-driven synchronization, not periodic Mem polling.

Clipboard I/O is separate from domain querying. Checking clipboard on window activation/focus is a small initial trigger; re-read on an adoption action so stale clipboard contents are not imported. A shared clipboard-classification result may be distributed through Core, but it must not cause several windows to reset themselves. Clipboard failures return a local readable status and must not erase input. Exact helper names and wake handling follow the current Tk/Core seam.
