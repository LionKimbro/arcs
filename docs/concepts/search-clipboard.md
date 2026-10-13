# Search clipboard
Created: 2026-10-12
Modified: 2026-10-13

## Portable search definitions
Created: 2026-10-12
Modified: 2026-10-12

Lion likes the idea of copying any given search to the clipboard. A search window recognizes a copied search and enthusiastically offers to configure itself from it: “You've got a search; I know what to do with that.” This generalizes the [temporal range clipboard](temporal-range-clipboard.md) concept from carrying temporal context to carrying a search definition. It remains a conceptual direction rather than a finalized protocol.

Update, October 13: ratification of Basic Search establishes [the generic clipboard contract](../design/search-clipboard.md), including its JSON query definition, UUID-reference arrays, reset/incorporation behavior, and explicit Search after adoption. The original exploratory notes below preserve context; the adopted contract takes precedence for the generic slice. Rich temporal-range serialization remains a follow-up decision.

The definition represents the query criteria, not a frozen list of matching objects. Reusing it can therefore find different results as the data changes. Criteria can include Basic field filters, object types, and supported domain-specific temporal predicates and their range context. Which additional settings, such as sort order, are included remains open.

## Recognize, offer, adopt
Created: 2026-10-12
Modified: 2026-10-12

A candidate interaction is **Copy search** in the source window and a contextual **Use search from clipboard** offer in the destination. Adopting it populates that window's criteria. Recognition alone does not replace the user's current search. Whether adoption also runs the query, or leaves a separate Search action, remains to be decided.

Lion requires two distinct ways to adopt clipboard criteria:

- **Reset to this search:** replace the currently specified query with the copied search definition, clearing existing query criteria not present in that definition.
- **Incorporate into current search:** retain the current query and modify it to incorporate the copied criteria or temporal context.

Do not collapse these into one ambiguous import action. Incorporation is an explicit query-composition operation, not necessarily an overwrite or a universal AND. How criteria on the same field combine, whether predicates use AND/OR, and how conflicting object types or temporal contexts are handled remain to be designed. Show the resulting criteria and surface unresolved conflicts rather than silently dropping constraints. Query replacement does not imply resetting unrelated window state such as its destination Welder workspace. Clipboard recognition alone invokes neither operation.

Interpret “reprogram myself” as configuring the window from declarative data, not executing clipboard code. A recognizable format marker and version can distinguish a search definition from a temporal range and ordinary prose. Unsupported criteria should be identified rather than silently discarded into a different query. Exact serialization, detection timing, validation, and UI wording remain open.

## Relationship to other concepts
Created: 2026-10-12
Modified: 2026-10-12

[Basic Search](basic-search.md) is a natural home for this interaction. A range alone supplies context for constructing a query; a copied search supplies the chosen predicates and context together. Neither copying a search nor adopting one creates domain objects or weld links. The exact treatment of referenced IDs, data-source portability, and transient result actions such as pulling into a particular Welder workspace is not yet specified.
