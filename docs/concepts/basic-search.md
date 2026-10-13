# Basic Search
Created: 2026-10-12
Modified: 2026-10-13

## General object discovery
Created: 2026-10-12
Modified: 2026-10-12

Lion proposes an **M1 Basic search window** that locates anything represented in Basic using Basic criteria, generalizing the earlier Arc Search idea. In Arcs this means searching the simplified M1 kernel's Basic records, not requiring full formal M1 storage. Results can include arcs, events, journal entries, and any other objects with Basic metadata. A link stored only in the links table is not a Basic result unless it also has optional Basic metadata.

Name substring, title substring, tags, and object type are natural criteria from Basic. Other Basic fields can become criteria as supported by the application; this concept does not assert that every formal Basic field is already implemented or must appear in the initial search interface. The exact controls, matching rules, and result actions remain to be designed.

## Relationship to Arc Search and the Welder
Created: 2026-10-12
Modified: 2026-10-13

This generalizes the proposed [Arc Search](arc-search.md) window rather than requiring a separate arc-only window for ordinary name/title/tag lookup. Searching Basic with object type `arc` supplies those arc results. Lion removes the proposed direct Pull into Arc Welder action: Basic Search copies selected references as a JSON array of UUID strings, even for a single selected object. It does not need to know a destination Welder or transfer objects directly.

The Arc Welder recognizes an eligible UUID list in the clipboard and offers its own pull-in action. Actual clipboard text is just the array, not a wrapped object with type labels or a destination. The mockup's demo clipboard keeps internal bookkeeping separately; it is not the transfer format. Search definitions and temporal-range payloads remain distinct clipboard concepts.

Searching for arcs adjacent to, overlapping, or approximately near another arc is arc-specific. It requires arc interval semantics, a reference arc or interval, and treatment of ChronoMark uncertainty. A loose Basic date field does not define those interval relationships. How specialized arc discovery relates to the general Basic search interface is deliberately unresolved: it could be a specialized mode, an additional filter source, or a separate interaction in the Welder.

Lion suggests [copying temporal range coordinates to the clipboard](temporal-range-clipboard.md) from an arc, then having search offer to use a recognized range as parameters. This could supply explicit temporal context without binding search to a particular open view. Recognition offers a choice rather than automatically replacing search criteria; range encoding and domain-specific predicates remain open.

Lion extends this to [copying a whole search](search-clipboard.md): a search window recognizes the definition and offers to configure its criteria accordingly. It copies query intent rather than a static result set. Clipboard recognition remains an offer, with exact adoption/run behavior unresolved.

Clipboard adoption distinguishes **Reset to this search** from **Incorporate into current search**. The first replaces query criteria; the second composes them with the current query. Exact combination semantics and automatic-versus-explicit execution remain open.

## Status
Created: 2026-10-12
Modified: 2026-10-13

Lion ratified the Basic Search window on October 13. The adopted design is [Basic Search](../design/basic-search.md), with [clipboard contracts](../design/search-clipboard.md) and [session names](../design/session-names.md); the [approved visual](../design-references/basic-search-window.md) is preserved in design references. These working documents settle the generic window behavior. Arc-specific temporal semantics and the complete Welder design remain subsequent bounded work.
