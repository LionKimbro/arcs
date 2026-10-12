# M1 link types
Created: 2026-10-11
Modified: 2026-10-11

## Adopted identifiers and internal names
Created: 2026-10-11
Modified: 2026-10-11

Lion supplied the formal transition/via identifiers and directs Arcs to use simplified type strings internally, with no separate typehint. Native M1 encoding is not required. The member-of and parent-child names below follow the M1 recommended vocabulary. When mapping to M1, map the short names to the identifiers below and preserve each tag URI exactly, including the slash after the colon.

| Internal type | Formal M1 type identifier | Direction and meaning |
| --- | --- | --- |
| `transition` | `tag:m1lattice.net,2026:/linktype/transition` | Predecessor arc → successor arc |
| `via` | `tag:m1lattice.net,2026:/linktype/via` | Transition link object → event through which the transition occurs |
| `member-of` | `tag:m1lattice.net,2026:/linktype/member-of` | Journal entry → associated arc, or event → associated arc |
| `parent-child` | `tag:m1lattice.net,2026:/linktype/parent-child` | Larger arc → sub-arc |

The transition/via identifiers were supplied by Lion. Member-of and parent-child appear in `F:\repo\m1\docs\raw\022__link-types.json`, document ID `m1lattice.vocab.linktypes.v1`, read on October 11. That draft guide offers recommendations, not requirements; it describes member-of as membership in a group or collection and parent-child as hierarchical containment or derivation. Arcs uses membership for its arc-associated records and containment for sub-arcs. The core specification itself does not define this vocabulary. New types may be introduced when needed rather than forcing an unsuitable recommended term.

## Association direction and multiplicity
Created: 2026-10-11
Modified: 2026-10-11

Journal entries and events use the same `member-of` relation; their distinct domain kinds identify what the source record is. Each association has its own link UUID. One entry/event can have member-of links to several arcs. For sub-arcs, the parent is the source and the child is the target; multiple parent-child links allow a child to belong to several larger arcs. Neither relationship requires storing an inverse link solely for reverse navigation.

## Transition structure
Created: 2026-10-11
Modified: 2026-10-11

The transition relationship is an independently identified link entity with its own UUID, `from` equal to the predecessor arc UUID, `to` equal to the successor arc UUID, and internal type `transition`. A second independently identified link entity has its own UUID, `from` equal to the transition link UUID, `to` equal to the event UUID, and internal type `via`. Both map to M1's Link Aspect (`tag:m1lattice.net,2026:aspect/link`).

The event, both links, and both arcs have distinct identities. Read the relationship as “Arc A transitions to Arc A′ via Event E.” The `via` relationship does not itself assert a separate causal relation or replace the arc boundary information. See [the authoring design](../design/arc-authoring.md) for the coherent save operation.
