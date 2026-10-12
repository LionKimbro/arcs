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

ChronoMark models an event or period separately from claims about its time, allowing uncertain bounds, multiple claims, and a working interpretation. Arc boundaries can be unknown and endings ongoing. Do not force calendar uncertainty into a single exact timestamp, overwrite competing claims, or assume a boundary event exists. Full ChronoMark editor integration and the relationship between its record UUID and arc UUID require an explicit mapping decision.

Concrete SQL DDL is intentionally not supplied yet. A small arc table with ordinary fields and JSON temporal content is a possible implementation, not a selected schema. Full schemas for all future features should not be invented to implement three arcs. Keep later migrations possible without destabilizing UUIDs.

## Load path
Created: 2026-10-11
Modified: 2026-10-11

On startup or a cache miss, route through Disk and Mem before returning canonical snapshots to Core. Disk returns storage data; Mem installs or reconciles it according to the selected cache/revision policy; Core installs an independent view snapshot. Initial full loading versus lazy loading is open. Either can satisfy the first slice; avoid both paths concurrently unless necessary.

Use an empty database as a normal first-run state. Unknown object IDs return not-found rather than implicit creation. Database corruption and I/O failures are not equivalent to an empty database and must not silently erase or recreate personal data.

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
