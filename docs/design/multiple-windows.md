# Multiple windows
Created: 2026-10-11
Modified: 2026-10-13

## Accepted architecture
Created: 2026-10-11
Modified: 2026-10-11

Lion accepts one Tk main thread/event loop, one shared Core worker, and per-window state within Core. Additional native windows use Tk top-level windows. A window does not require its own thread or Core machine. This is an adopted design decision; implementation will proceed through bounded sketches when requested.

There is exactly one Command Center for the running session. It is opened at startup and controls application lifetime. Arc Detail windows are created on demand in sensible response to user commands/buttons that create or open arcs, not automatically as a batch at startup. Multiple detail windows may show the same or different arcs.

## View identity and shared objects
Created: 2026-10-11
Modified: 2026-10-11

Give each open view a distinct view identity, separate from the UUID of any arc or other domain object it displays. Core tracks each view's kind, displayed object, selection, working draft, and request state as needed. Tk maintains a corresponding map from view identities to native windows and widgets.

Several windows can display the same arc UUID while selecting different chronology items or holding different local drafts. Canonical arc data stays owned by Mem; neither window becomes its owner. Accepting a domain change should update affected views without silently overwriting newer unsaved drafts. The exact notification and revision policy remains open.

Lion has selected return-driven synchronization rather than polling. When a Mobile Stack returns from Mem, it carries accepted-change information in a register. Core retains an independent copy as reducer-event data before the stack continues or completes, then offers that information to each window's reducer. Each reducer decides whether it is relevant to its view: handle it and emit any needed Tk commands, or ignore it. The originating window is not the only recipient.

This distributes information within the shared Core worker; it does not transfer the live stack to several windows or create a thread per reducer. Closing the requesting window does not prevent the remaining reducers from receiving an accepted domain change. The exact change payload and revision/conflict rules remain to be sketched. Earlier [synchronization alternatives](../design-references/window-synchronization.md) are retained as discussion history.

## Reducer events and commands
Created: 2026-10-11
Modified: 2026-10-11

User events carry the originating view identity. Core routes the event to the appropriate per-view state and emits presentation commands naming the destination view. Application-wide events such as shutdown are explicitly distinguished from view-specific events. Per-view reducer helpers may keep handlers understandable while the shared Core loop serializes state changes.

For example, selecting an event in window A changes A's selection and detail pane, leaving window B's selection alone. A committed arc title change affects every view of that arc. Opening or closing a window is an application event producing a targeted Tk create/destroy command, with any draft handling settled before destruction.

## Outstanding continuations
Created: 2026-10-11
Modified: 2026-10-11

Mobile Stack context can carry the requesting view identity and an operation token. Core checks that the view still exists and the result is still relevant before presenting it. Closing a window does not retire Core or remove Mem's records. It also must not undo a domain operation simply because its originating view closed. Distinguish processing a completed domain operation from updating a now-closed presentation.

Rapid reselection or replacement of displayed content requires stale-result handling so an older response cannot replace a newer selection. Exact token/generation rules and cancellation semantics remain to be sketched.

## Lifecycle choices still open
Created: 2026-10-11
Modified: 2026-10-11

Closing Command Center exits the whole application through orderly shutdown; closing another window only closes that view. Startup opens Command Center alone, and detail windows arise from user actions. How detail-window closes handle drafts and whether ordinary existing-arc opening reuses a view or creates another remain undecided, but the user must be able to request multiple views of the same arc. The one-Core design supports the chosen standalone detail windows and a possible later browser.

## Basic Search views
Created: 2026-10-13
Modified: 2026-10-13

The ratified [Basic Search](basic-search.md) also uses independent on-demand windows with per-window reducers in Core. Each owns its query input, executed query, results collection, selection, and request generation. App-session name bindings are shared Core state, not one copy per search window. Clipboard recognition can offer actions to several windows, but adoption is explicit and affects only the chosen window. Closing a search window leaves the application, bindings, and other views alive; Command Center close shuts down all windows.
