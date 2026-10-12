# Window synchronization alternatives
Created: 2026-10-11
Modified: 2026-10-11

## Problem and status
Created: 2026-10-11
Modified: 2026-10-11

The accepted design uses one Core with per-view state and Mem-owned canonical records. When one view submits a change and Mem accepts it, every relevant view must learn about the new version without losing independent selections or unsaved drafts. Lion has now selected return-driven synchronization: Core offers the returned register information to each window's reducer, which handles it if relevant and otherwise ignores it. Polling is not required. The adopted decision is recorded in [the multiple-window design](../design/multiple-windows.md); alternatives below remain discussion history. Mem acceptance remains distinct from SQLite durability.

## Revision polling — Lion's candidate
Created: 2026-10-11
Modified: 2026-10-11

About once a second, a view requests changes from Mem through a Mobile Stack, supplying the version it currently sees. If Mem has a newer version, return the new data to Core for the view. If unchanged, the operation can complete without carrying replacement data. This provides eventual refresh without requiring Mem to track interested views.

Revision scope needs definition: one global revision invalidates every view for any change, while object revisions allow more selective checks. Chronology also depends on linked records and associations, so an arc row's revision alone is insufficient unless those changes advance an appropriate aggregate revision. If unchanged requests terminate in Mem, Core must not await a response needed to clear an in-flight request. A small UNCHANGED return is an alternative when operation bookkeeping needs completion notification.

With a shared Core, polling can be batched once per unique watched object or query, not once per window. Core can distribute returned changes to its affected views. This avoids duplicate work when several windows show the same arc. One-second polling introduces a visible delay and repeated no-change checks, but is a viable deliberate tradeoff.

## Accepted-change return and Core distribution — Aevia preference
Created: 2026-10-11
Modified: 2026-10-11

On a normal write request, Mem's return continuation supplies an accepted-change result with affected identities, revisions, and enough accepted data for Core to refresh or request fresh snapshots. Core processes this as an application-level event and distributes it to all affected views, not just the requester. This does not require per-window subscriptions in Mem. The originating view can close while the domain change still gets processed.

If every canonical mutation passes through Core's requests and Mem returns a complete change result, ordinary edits need no polling. If Mem can change independently, for example through future import or external-message paths, those paths must also report changes to Core or be covered by another refresh mechanism. Broader query views such as bands or frames may need invalidation beyond one arc identity.

## Mem notifications or hybrid refresh
Created: 2026-10-11
Modified: 2026-10-11

Mem could report every relevant accepted change to Core through a notification Mobile Stack, including changes not initiated by a particular view. Core remains responsible for deciding which windows need updates. This supplies prompt updates but adds an explicit notification protocol and may duplicate write returns unless their roles are defined.

A hybrid can distribute ordinary accepted write results immediately and use occasional batched revision checks for independently changing data. Choose this only if those independent paths justify it; it need not be introduced for the initial system.

## Drafts and revisions
Created: 2026-10-11
Modified: 2026-10-11

An incoming accepted snapshot updates the view's known base without silently replacing unsaved text. If another window edited the same field, automatic rebase, explicit conflict handling, or a simpler temporary edit restriction must be chosen. Supplying a base revision with a save lets Mem detect stale proposals, but the application conflict policy remains open. View selection and draft state are separate from the accepted domain snapshot.
