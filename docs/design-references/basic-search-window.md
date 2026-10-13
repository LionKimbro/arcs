# Approved Basic Search window reference
Created: 2026-10-13
Modified: 2026-10-13

## Approval and artifact
Created: 2026-10-13
Modified: 2026-10-13

Lion ratified this design after inspecting Aevia's interactive mockup and removing the direct Pull into Arc Welder action. The preserved [HTML illustration](basic-search-window.html) depicts independent search windows with parameters above, results in the middle, and selection actions below. The authoritative adopted behavior is in [Basic Search](../design/basic-search.md), [clipboard contracts](../design/search-clipboard.md), and [session names](../design/session-names.md).

The illustration uses example objects and a simulated clipboard; it was checked for filters, multi-selection, naming, clipboard reset, independent results, and narrow-width overflow. It is a fragment for the conversation's interactive preview, not a standalone deployed app. Arc interval predicates were not implemented in the mockup, and its simple Basic-date comparisons must not be reused as correct temporal searching.

## Ratified visual arrangement
Created: 2026-10-13
Modified: 2026-10-13

Parameters include object type, name substring, title substring, tags/all-any, Search, Clear parameters, Copy search, and clipboard adoption offers. Arc-specific temporal controls belong in a grouped extension when arcs are selected. Results support checkboxes, a select-all control, recognizable Basic metadata, and a selection count. Bottom actions open a selected object, assign individual session names, and copy UUID references.

The final approved version contains no Pull into Arc Welder button. Selected references travel as a plain JSON array of UUID strings, with the future Welder offering its own explicit clipboard pull-in action. Specific colors, dimensions, sample objects, mockup state restoration, and demo messages are illustration mechanics rather than application requirements.
