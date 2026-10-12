# Authoring

Basic holds kind, prose, labels, and simple date. Links own relationship UUIDs;
endpoints resolve across Basic and links. Temporal aspect holds richer record
claims. Disk migrates v1 to v2 without changing identities.

Core owns each view's chronology, selection, and author draft. Tk captures fields
and presents Save/Discard/Cancel navigation. Mem stages; Disk commits atomically;
Mem accepts; all relevant reducers refresh without losing drafts or selections.

Journal/event creation adds Basic, temporal, and member-of. Transition adds an
event, successor, predecessor ending, transition, via, and two member-of links.
Reject stale or already-ended predecessors. Keep failed drafts; cancel close if
a submitted save fails. Duplicate Save cannot submit a second operation.

Occurrence controls accept calendar precision, offset timestamps, and optional
uncertain bounds/notes. Sort by working focus (bounds when focus absent), newest
first; undated last, UUID tie-break. Never sort by registration time.
