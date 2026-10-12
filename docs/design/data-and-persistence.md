# Data and persistence
Created: 2026-10-11
Modified: 2026-10-11

## Established constraints
Created: 2026-10-11
Modified: 2026-10-11

Disk owns SQLite operations and the database connection. Open and use that connection on the Disk worker, and close it in its cleanup path. Main may resolve configuration before worker startup, as Today does, but must not create a live connection for other machines to share. Mem owns canonical in-memory domain records. Core has copied view data and working drafts. Tk has presentation data and widgets. No layer reads another layer's mutable domain containers directly.

Each arc has a stable UUID in lowercase hyphenated representation. Title and name are editable labels. The model allows multiple parent arcs and future independently identified events, journal entries, and relationships; do not encode a single mandatory parent in the conceptual model. M1 interoperability requires preserved identity and mappable meaning, not M1-shaped SQL tables. FileTalk is inter-application communication, not database access.

## Initial records and temporal information
Created: 2026-10-11
Modified: 2026-10-11

The initial persistence slice needs arc identity, title, name, description, and enough temporal/boundary data for creation and display. Revisions or equivalent acceptance generations must distinguish a view's saved base from later changes. Created/modified metadata, if included, is database-record history rather than an arc's beginning/ending.

The authoring extension explicitly requires transitions to create independently identified M1-conforming link objects. Persist the link UUID and directed `from`/`to` arc UUIDs, with relationship typing as specified in [Arc authoring](arc-authoring.md). A bare pair of arc references with no link identity is insufficient. The SQL representation need not literally store an aspect mapping, but must map to M1's Link Aspect. Include the link in the atomic transition transaction, separately from the event record.

The adopted transition structure has two links: `transition` from predecessor to successor, and `via` from that transition link to the event. Each has a separate UUID. Internal short type names are allowed; their formal M1 identifiers are preserved in [M1 link types](../design-references/m1-link-types.md). Persist both links in the atomic transaction.

The selected [links table](links-table.md) closely follows the M1 Link Aspect: link UUID, `from`, `to`, one required simplified `type` string, plus an application revision. Do not store `typehint`. Links have independent identities in that table and do not require Basic rows. Endpoints can resolve to Basic objects or links, so validation must cover both. Its DDL and migration requirements are specified separately.

Use member-of links from journal entries/events to their associated arcs, and parent-child links from larger arcs to sub-arcs. Each relationship has its own stable link UUID. A transition event has member-of links to both arcs as well as the via link from the transition relationship. Persist all links involved in a transition within that operation's transaction.

ChronoMark models an event or period separately from claims about its time, allowing uncertain bounds, multiple claims, and a working interpretation. Arc boundaries can be unknown and endings ongoing. Do not force calendar uncertainty into a single exact timestamp, overwrite competing claims, or assume a boundary event exists. Full ChronoMark editor integration and the relationship between its record UUID and arc UUID require an explicit mapping decision.

The existing implementation has `basic` and `arc` tables, with JSON temporal content on the arc record. The [links table](links-table.md) now supplies DDL for the selected relationship extension; event and journal-entry schema details require their own bounded design. Full schemas for all future features should not be invented. Keep migrations possible without destabilizing UUIDs.

## Load path
Created: 2026-10-11
Modified: 2026-10-11

On startup or a cache miss, route through Disk and Mem before returning canonical snapshots to Core. Disk returns storage data; Mem installs or reconciles it according to the selected cache/revision policy; Core installs an independent view snapshot. Initial full loading versus lazy loading is open. Either can satisfy the first slice; avoid both paths concurrently unless necessary.

Use an empty database as a normal first-run state. Unknown object IDs return not-found rather than implicit creation. Database corruption and I/O failures are not equivalent to an empty database and must not silently erase or recreate personal data.

## Basic-centered events and journal entries
Created: 2026-10-11
Modified: 2026-10-11

Lion points out that much of an event or journal entry can be contained in the Basic table. Use this as the design direction: the object's UUID, name, title, and description belong in its existing Basic row. The journal entry's prose can be its Basic description; an event's description can express what happened. Do not duplicate that text in a second record body merely because the objects have different kinds. Dedicated event or journal tables are not required for information Basic already represents.

Arc associations stay in the links table as member-of links, supporting one entry/event associated with several arcs without copying its content. Lion chooses one simplified `type` field in Basic, with values `arc`, `event`, and `journal-entry`. Optional Basic metadata for a link uses `link`. Do not add a Basic typehint field alongside it. `basic.type` means object kind; `links.type` means relationship kind, such as transition or via. The same field spelling has different meanings in the two tables. Basic type can later map to formal M1 Basic's typehint without requiring that formal spelling internally.

M1 Basic also has `date`, a general-purpose, context-dependent string, so a simple associated date belongs naturally in Basic. There is no separate time field or dedicated date-time field in core Basic v3. Its fields are loosely interpreted and permit additional keys; the exact convention for a date containing a time remains to be chosen. The current SQL Basic table omits these available M1 fields and can be extended to carry them. ChronoMark's richer uncertain claims, occurrence versus creation semantics, and journal dating still require a clear mapping, but not necessarily separate event/journal tables.

## Save milestones and required acknowledgment
Created: 2026-10-11
Modified: 2026-10-11

Mem acceptance and Disk transaction completion are distinct. A returned accepted change can refresh all Core views as already agreed. To make a SQLite save report truthful, its operation must also have an observable committed completion or error. Core must not display an unconditional “saved” on Mem acceptance alone if Disk has not committed.

The initial protocol must be settled in one bounded sketch. Two compatible approaches are: Mem accepts then tracks a pending Disk commit with a separate completion result, or Mem stages a proposal, Disk commits it, and Mem publishes canonical acceptance afterward. Neither ordering is selected here. Concurrent writes, revisions, failed saves, and shutdown have to agree with the chosen ordering. Do not retrofit a return path that sends results to already-retired workers.

An immediate Disk transaction per explicit create/save is a useful small-scope option; Today's one-second coalescing is not a requirement for SQLite. If buffering is selected, define its pending operations and flush behavior. Normal shutdown must finish submitted domain writes while required continuation destinations remain alive.

## Multiple-view edits
Created: 2026-10-11
Modified: 2026-10-11

When Mem returns a change, Core offers the retained result to all window reducers. Each decides relevance by displayed objects and other dependencies, and preserves its local selection. Editing the same arc from two windows requires a chosen stale-base/conflict rule before unrestricted editing ships. A base revision lets Mem detect a stale save; the UI response must not silently discard a user's draft. Exact field-level merge is not required by the established design.

## Storage configuration and implementation gates
Created: 2026-10-11
Modified: 2026-10-11

Choose the personal database location explicitly. Today's MachineRoot `db-root-2026` resolution is a reference, not permission to reuse its `today` directory. Tests need an exact temporary database path override. The repository's `db/` currently holds documentation references; it is not automatically the location for personal SQLite data.

Before implementing persistence, settle location/configuration, initial schema, load strategy, and the commit acknowledgment ordering. Also settle the initial boundary representation and editing/conflict policy. Journal mode, cache size, broad export machinery, media storage, and sophisticated migrations should follow concrete need rather than being assumed necessary for the first slice.
