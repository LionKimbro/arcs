# Data storage
Created: 2026-10-11
Modified: 2026-10-11

## Established requirements and current preference
Created: 2026-10-11
Modified: 2026-10-11

Each arc has a stable UUID. Internal data structure and storage are free choices as long as the data is conceptually mappable to M1 for interoperability. Lion has now selected SQLite and established that the Disk machine owns database access, while Mem owns canonical in-memory data, using Today's architecture. FileTalk is the established communication mechanism between applications and is distinct from internal persistence. See [the specific architecture design](../design/architecture.md).

## Initial proposal — Aevia
Created: 2026-10-11
Modified: 2026-10-11

Use one SQLite database for Arcs' records and relationships, rather than a separate database for every arc. Give events and journal entries stable UUIDs too, so they can be associated with multiple arcs without duplicating the underlying record. Represent multi-parent arc containment and other arc relationships explicitly. UUIDs, not editable names or titles, identify records and relationship endpoints. Exact tables, link identities, and mapping details remain to be discussed.

Keep temporal claims capable of preserving ChronoMark's uncertainty and multiple perspectives. SQLite may hold structured columns alongside JSON temporal data; the representation is not chosen yet. Do not silently flatten unknown or approximate time into exact timestamps.

Persist a transition's event, successor arc, boundary associations, and relationship coherently. SQLite transactions are a candidate mechanism so an interrupted save does not leave only half the transition. The distinction between worker ownership, in-memory changes, and durable database commits still needs a bounded design.

## Decisions still open
Created: 2026-10-11
Modified: 2026-10-11

Database location, initial schema, schema changes, backup behavior, and media storage remain open. Worker ownership is settled: Disk owns SQLite, Mem owns canonical in-memory records. The repository's `db/` reference files do not establish where personal Arcs data should live. Full M1 import/export need not be implemented in the initial slice, but identities and relationships must remain mappable.
