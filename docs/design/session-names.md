# Session names
Created: 2026-10-13
Modified: 2026-10-13

## Adopted role and scope
Created: 2026-10-13
Modified: 2026-10-13

Session names are short user-chosen variables referring to object UUIDs. Basic Search's Name selected action assigns them without renaming the Basic record or creating a copied object. Use one application-session binding map owned by Core, shared across Command Center, Search windows, and later Welder interactions. Bindings last until the application exits; persistent/restored bindings are a later feature, not an initial SQLite obligation.

Support naming arcs, events, journal entries, and other selected Basic objects. Several different session names can bind the same UUID. A name's stored value is the UUID, so changing an object's Basic name or title does not redirect the binding. Session variables name individual objects in this slice, not result collections or queries.

## Assignment and collisions
Created: 2026-10-13
Modified: 2026-10-13

For several selected objects, show one label and input per object. Require nonempty, whitespace-free session names, preserving case and using exact session-name equality. Show validation errors before applying the assignment. Do not invent auto-numbered names or assign a single input to all selected objects. Existing bindings to the same UUID are harmless; a binding to a different UUID requires an explicit Replace binding choice showing both objects. Cancel leaves the map unchanged. Duplicate names within one multi-object assignment are a conflict, not last-write-wins.

Session names shadow Basic names as Lion specifies. When a user supplies a name handle, resolve a session binding first, otherwise resolve a Basic name. Explicit full UUID references bypass name lookup. Session names matching the full UUID syntax are disallowed in this initial UI to keep that identity route unambiguous. Basic-name ambiguity must be surfaced rather than choosing the first match. Access to a shadowed object is always possible by its full UUID; a separate explicit Basic-name syntax is not required for this slice.

Search's name/title substring fields are literal search text, not handle resolution. If searching for Basic names containing `a`, do not substitute the session binding `a`. Kind and relationship-type fields likewise are not session variables.

## Updates and presentation
Created: 2026-10-13
Modified: 2026-10-13

Session assignment is Core-local state, not a Mem domain edit, an M1 link, or a SQLite transaction. Notify relevant views within Core so displayed session aliases refresh. Missing/deleted target objects produce an unresolved-reference result; never create a replacement under the same name implicitly. User action is required to rebind.

The search UI should clearly label this action as session naming. Naming does not alter search specifications or result selection. A later command syntax can expose the same binding operation through Command Center while preserving these semantics.
