# Temporal range clipboard
Created: 2026-10-12
Modified: 2026-10-12

## Lion's candidate interaction
Created: 2026-10-12
Modified: 2026-10-12

While viewing an arc, activate a control that copies its temporal coordinates as a range to the clipboard. A search window recognizing a temporal range in the clipboard offers to set search parameters from it. This is an exploratory interface idea, not an adopted clipboard protocol or implementation request.

The copied range provides context for searching without requiring the search window to infer which open arc the user means. Recognition should offer an explicit action; it does not automatically alter search criteria or start a query. How and when the window checks the clipboard remains open.

## Interpretation — Aevia
Created: 2026-10-12
Modified: 2026-10-12

A possible flow is **Copy temporal range**, then **Use clipboard range** in search, followed by choosing a relation such as overlap, occurrence within the range, or neighboring within a specified distance. These relations remain distinct; copying a range does not choose one. Show the imported range and chosen search relation so the search context is visible.

The payload could be recognizable structured text, such as JSON with an explicit format marker, rather than an ambiguous pair of dates. Preserve ChronoMark-supported uncertainty, precision, timezone, and unknown/ongoing boundaries. Do not collapse multiple unresolved claims into an invented exact interval. Exact encoding and rules for choosing or carrying claims remain to be designed. An optional source arc UUID can supply provenance, but the range should be interpretable without fetching that arc.

The clipboard carries a snapshot rather than a live subscription to the source arc. How ongoing boundaries are interpreted at query time must be explicit, not silently frozen to the copy time. This proposal does not yet specify interoperability with other applications, though a documented payload could later be useful to them.

## Basic versus arc-specific search
Created: 2026-10-12
Modified: 2026-10-12

The interaction could appear in [Basic Search](basic-search.md), but supported temporal predicates depend on the searched object kind: event occurrence within a range is different from an arc period overlapping it. The source range is reusable context; domain-specific time interpretation still belongs in the corresponding query behavior. Clipboard recognition alone does not resolve this integration question.
