# Object handles
Created: 2026-10-13
Modified: 2026-10-13

## Three kinds of UI handle
Created: 2026-10-13
Modified: 2026-10-13

Lion identifies three ways for a user to refer to an object in the application:

- Its full UUID: stable object identity.
- Its Basic name: the persistent name associated with the object, distinct from its display title.
- Its session name: a short user-chosen variable name such as `a` or `x` that refers to the object during the session.

Session names can refer to arcs, journal entries, events, and other objects; they are not restricted to arcs. They provide convenient references without requiring every interaction to use clipboard copy/paste. Clipboard workflows remain desired and coexist with these handles.

## Session bindings — working interpretation
Created: 2026-10-13
Modified: 2026-10-13

A session name binds to an object's UUID rather than copying its content or renaming its Basic record. The name is a UI convenience, not a new domain identity or an M1 link. Aevia suggests sharing bindings across Command Center, search, and the future Welding Station so a name assigned in one place is useful elsewhere; scope has not yet been settled.

Update, October 13: the ratified search design adopts [session names](../design/session-names.md) with an application-wide Core-owned binding map, shared across views and cleared at application exit. It defines individual naming from multi-selection, explicit rebinding, and name-resolution behavior. That specific design supersedes the earlier open questions here for the initial slice.

Persistence across restarts, assignment syntax or controls, rebinding behavior, case sensitivity, and whether several session names can refer to one object remain to be designed. The phrase session name suggests a session lifetime, but no restoration policy has been established.

## Resolution and ambiguity
Created: 2026-10-13
Modified: 2026-10-13

Resolve handles to UUIDs before performing domain operations. Lion establishes that **session names shadow Basic names**: when a name matches a session binding, use that binding rather than looking up the same name in Basic. When there is no matching session binding, Basic-name lookup applies. The current design does not require Basic names to be globally unique, so that lookup may still need disambiguation. Full UUIDs remain explicit object identities. How to explicitly request a shadowed Basic name without removing the session binding remains open.

Editing an object's title or Basic name should not change its UUID or accidentally redirect a UUID-bound session variable. Missing/deleted objects should produce a clear unresolved reference rather than an implicit replacement object. Exact lifecycle behavior awaits design.
