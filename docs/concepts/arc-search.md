# Arc Search
Created: 2026-10-12
Modified: 2026-10-13

## Candidate interface
Created: 2026-10-12
Modified: 2026-10-12

Lion proposes a general **Arc Search** window for finding existing arcs, with a result action such as **Pull into Arc Welder**. This is a candidate interface, not yet an adopted window design. It separates finding an arc from choosing how to connect it, and could be useful outside the Welder as well.

Lion subsequently generalizes ordinary discovery to [Basic Search](basic-search.md), finding any object represented in Basic rather than just arcs. This supersedes the arc-only general search-window idea for Basic criteria. Arc-specific temporal discovery remains needed; its interface relationship to Basic Search is unresolved. Keep the notes below as the original proposal's context rather than a decision to create an additional search window.

## Search criteria
Created: 2026-10-12
Modified: 2026-10-12

Required discovery capabilities for pulling arcs into the Welder include name substring, title substring, tags, temporal overlap, and temporal neighboring within a specified number of days/months/years/decades. Temporal comparison requires a reference arc or interval; a general search window cannot silently assume which open arc supplies that context. Case sensitivity, how criteria combine, result ordering, and treatment of uncertain dates remain to be designed.

## Pulling a result into the Welder
Created: 2026-10-12
Modified: 2026-10-13

Select a found arc and activate Pull into Arc Welder to add that existing UUID to the workspace being assembled. Pulling in is workspace membership, not an assertion of an M1 member-of relationship: it creates neither a new domain arc nor a weld link and does not change temporal boundaries. The user can then inspect the arc in context and deliberately establish a relationship.

This original direct-transfer proposal is superseded: [Basic Search](basic-search.md) copies a JSON array of UUID strings, and the [Welder](arc-welder.md) offers its own clipboard pull-in button when the references resolve to arcs. No direct Welder action or destination picker is needed in search.

How the destination workspace is identified, whether a Welder is opened when none exists, duplicate workspace-item handling, and multiple-result selection remain open. Aevia suggests that a search opened from a particular Welder carry that destination and reference arc explicitly, while a standalone search ask for a destination when needed; this suggestion has not been adopted.
