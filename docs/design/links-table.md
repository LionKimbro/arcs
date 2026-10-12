# Links table
Created: 2026-10-11
Modified: 2026-10-11

## Decision and implementation status
Created: 2026-10-11
Modified: 2026-10-11

Lion selects a SQLite table named `links` whose data closely follows M1's Link Aspect. The existing `src/arcs/disk.py` currently initializes `basic` and `arc`, with database version 1; it does not implement this table. This document specifies the extension, not an applied migration.

The `basic` table holds descriptive objects; the `links` table independently holds link objects and their stable UUIDs. A link does not require a Basic row. Optional descriptive Basic metadata for a link can use that same UUID and Basic type `link`, but it is not a second identity or a creation prerequisite. An endpoint may be an arc, event, link, or another represented object; do not constrain endpoints to the `arc` or `basic` table alone.

## Columns and M1 mapping
Created: 2026-10-11
Modified: 2026-10-11

| Column | SQLite representation | Meaning |
| --- | --- | --- |
| `uuid` | TEXT, primary key, not null | Stable identity of the link entity; no Basic row required |
| `from` | TEXT, not null | Source UUID, resolving to a Basic object or link; M1 Link Aspect `from` |
| `to` | TEXT, not null | Target UUID, resolving to a Basic object or link; M1 Link Aspect `to` |
| `type` | TEXT, not null, nonempty | Simplified relationship type string; maps to M1 Link Aspect `type` |
| `revision` | INTEGER, positive, not null | Application revision for accepted updates, outside the Link Aspect |

Store UUIDs in lowercase hyphenated form, using the application's existing UUID validation. The application currently uses UUID object identities, although general M1 also permits tag URI entity IDs. `uuid` is the entity identity, not a field inside the mapped Link Aspect. Basic title/name/description stay in `basic` rather than being duplicated here.

Store only `type`, using simplified strings; do not add a `typehint` column or a parallel relationship-label field. The selected types are `transition`, `via`, `member-of`, and `parent-child`; map them to the exact formal tag URIs in [M1 link types](../design-references/m1-link-types.md). A short name is an internal encoding, not itself a valid M1 entity ID. Future types may be added as needed; do not restrict this table permanently to this initial vocabulary. Although M1 permits an absent type, Arcs requires a nonempty type for its links. Human-readable presentation can derive labels from the type without storing a second field.

## Table definition
Created: 2026-10-11
Modified: 2026-10-11

Use quoted `from` and `to` column identifiers in SQL to preserve the M1 field names without conflicting with SQL syntax. The table definition is:

```sql
CREATE TABLE links (
    uuid TEXT PRIMARY KEY NOT NULL,
    "from" TEXT NOT NULL,
    "to" TEXT NOT NULL,
    type TEXT NOT NULL CHECK (length(trim(type)) > 0),
    revision INTEGER NOT NULL CHECK (revision > 0)
);

CREATE INDEX links_from_type ON links ("from", type);
CREATE INDEX links_to_type ON links ("to", type);
```

The endpoint indexes support outgoing and incoming relationship lookup. Do not add uniqueness on endpoint pairs or on endpoint/type triples: M1 permits multiple independently identified links between the same entities. Do not add automatic cascading deletion; deletion semantics have not been designed. Keep foreign-key enforcement enabled as the existing Disk worker already does.

Because endpoints can resolve to either Basic objects or independently stored links, a foreign key to Basic alone is incorrect. Mem validates endpoint existence and relationship kinds; Disk verifies endpoint existence within the save transaction against Basic and links, including records inserted by that transaction. Use the same UUID for optional Basic metadata on a link; reject unrelated cross-table identity collisions. A shared entity table is not required just to restore endpoint foreign keys. Exact validation helpers belong in the bounded implementation sketch.

## Transition example
Created: 2026-10-11
Modified: 2026-10-11

For predecessor A, successor A′, and event E:

- L1 has its own UUID, `from = A`, `to = A′`, and `type = transition`.
- L2 has a different UUID, `from = L1`, `to = E`, and `type = via`.

A, A′, E, L1, and L2 have distinct identities. A, A′, and E have Basic rows; L1 and L2 are identified by their links rows and do not need Basic rows.

Create the successor and event with their Basic data, both links, and the boundary changes in the [authoring transaction](arc-authoring.md). Make referenced objects available before dependent links are validated; in particular, the transition link must resolve when creating its via link. Existing objects must be reused by UUID, not duplicated for each link.

## Entry, event, and sub-arc links
Created: 2026-10-11
Modified: 2026-10-11

Use `member-of` from a journal entry to an associated arc, and from an event to an associated arc. Each association is a link object with its own UUID. A record associated with several arcs has several member-of links to the same record identity, not several copies of its content. An arc's chronology can query incoming member-of links and distinguish events from journal entries by the linked object's domain kind.

Use `parent-child` from the larger arc to the sub-arc, matching M1's recommended Parent → Child direction. Several parent arcs can have parent-child links to one sub-arc. Do not infer containment solely from date ranges. No inverse child-parent link needs to be stored just to browse parents; query incoming parent-child links instead.

A transition event is a member of both predecessor and successor, so persist two member-of links in addition to its transition and via links. The member-of links associate the event with the two chronologies; the via link identifies it as the event through which the particular transition occurs. These meanings are distinct, even though they involve some of the same objects.

## Migration, ownership, and acceptance
Created: 2026-10-11
Modified: 2026-10-11

Disk owns the migration, transactions, and SQL. Add a recognized versioned migration for existing version-1 databases, coordinating its version number with the other authoring schema extensions. Preserve existing arcs and metadata; do not recreate the database or change UUIDs. Decide the minimal migration sketch before rendering it into code.

Mem owns accepted in-memory link records. Returned changes identify affected objects so all relevant Core window reducers can update, including when the source of a via link is another link. Native M1 emission is not required; the stored identities and fields must support the mapping.

Verify migration of an existing isolated database, persistence and reopening of both transition links, rejection of nonexistent endpoints, allowance of multiple links between the same pair, and rollback of the complete transition on failure. No actual database or application code is modified by this design document.
