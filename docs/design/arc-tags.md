# Arc tags
Created: 2026-10-12
Modified: 2026-10-12

## Required capability
Created: 2026-10-12
Modified: 2026-10-12

Lion specifies that arcs need to support tags, using the concept already present in M1 Basic. An arc can have several tags and the same tag can classify several arcs. Tags enable finding arcs, including candidates to pull into a future Arc Welder workspace. Adding a tag does not create containment, membership, or transition links.

## Simplified representation and mapping
Created: 2026-10-12
Modified: 2026-10-12

Model tags as a list of classification strings associated with the arc's Basic information, mapping directly to M1 Basic's `tags` list. These labels are distinct from tag URI identifiers: a tag such as `work` is not an object identity or a formal link-type URI. No independent UUID is required for each tag label.

The existing Basic object-kind `type` continues to identify the object as an arc; tags describe additional categories or concerns. They should not replace object kind or be interpreted as arc-parent relationships. A normalized SQLite tag-association table or JSON storage can implement the list; the SQL choice is not settled by requiring tags.

## Interaction and queries
Created: 2026-10-12
Modified: 2026-10-12

Provide a way to view, add, and remove an arc's tags, and find arcs by tag. Arc Detail View is a natural place to edit the arc's own tags; exact controls remain open. Save through the existing Core/Mem/Disk path and distribute accepted changes to relevant views. Reopening the application preserves tags.

Case sensitivity, allowed characters/spaces, duplicate handling, multiple-tag search semantics, and the precise storage migration require a small design pass. M1 describes classification tags as typically restricted labels without spaces, but does not supply a complete mandatory validation scheme here. Do not silently impose an elaborate tag ontology or force a full M1 representation.

Update, October 13: [Basic Search](basic-search.md) now specifies case-insensitive complete-tag matching and an All tags/Any tag choice. Search trims surrounding query whitespace without changing stored label spelling. The storage migration, editing validation, and duplicate-label policy still require their bounded implementation decision.

## Scope and verification
Created: 2026-10-12
Modified: 2026-10-12

Tag support is a required new capability, not a claim of existing implementation. The Arc Welder remains exploratory. Verify that an arc can retain several tags, several arcs can share one, searches return matching arcs, removing a tag from one arc does not remove it from others, and updates preserve UUIDs and other Basic data. Implementation and schema changes are separate from this design note.
