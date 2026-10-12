# Event-established transition — modeling proposal
Created: 2026-10-11
Modified: 2026-10-11

## Lion's proposed structure
Created: 2026-10-11
Modified: 2026-10-11

Lion proposes:

```text
Arc A -----------(1)-----------> Arc A′

(1)-------------(2)-----------> Transition Event
```

Aevia interprets (1) as the independently identified transition link from predecessor to successor, and (2) as a second independently identified link from that first link to the event. Lion subsequently selected `transition` and `via` as their types and supplied formal M1 tag URIs. This structure is now adopted in [the authoring design](../design/arc-authoring.md), with identifiers preserved in [M1 link types](m1-link-types.md).

## M1 fit and meaning
Created: 2026-10-11
Modified: 2026-10-11

M1 links are entities with identities, so a link entity can be the source or target of another link. Link (1) has `from = A`, `to = A′`, and type `transition`; link (2) has `from = UUID of (1)`, `to = event UUID`, and type `via`. Both have their own UUIDs and map to Link Aspects. Internal short names map to Lion's formal identifiers; the application need not store native M1-shaped data.

This structure associates the event with the particular transition relationship, rather than just separately associating it with the two arcs. The event's temporal information and any boundary references remain distinct concerns: the second link does not itself define an arc's ending or the successor's beginning. Neither duplicate event objects nor duplicate temporal claims are implied.

The selected word “via” identifies the event through which the transition occurs without requiring a separate causal assertion. Whether the application needs a distinct “caused by” relation is open. Allowed numbers of associated transition events, reverse lookup, and any convenience event-reference field on the transition link remain to be designed. Both link objects are included in the adopted coherent transition save operation.
