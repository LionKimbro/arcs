# Search clipboard contracts
Created: 2026-10-13
Modified: 2026-10-13

## Object references
Created: 2026-10-13
Modified: 2026-10-13

Copy reference(s) puts plain JSON text on the system clipboard: an array of full UUID strings. Use this same array shape for one selected object. No object titles, names, kinds, source-window IDs, or destination wrappers are required. For example:

```json
["7426b7cb-e477-4d88-8f41-d4ecdb06fc10"]
```

The example UUID is illustrative, not a seeded database object. Produce references in displayed selected-row order, once per UUID. Clipboard copying creates no domain record or relationship. Session names are not copied in place of UUIDs.

A future Arc Welder recognizes a nonempty valid UUID list, resolves the objects, and makes its own pull-in button available/highlighted when they all identify arcs. Recognition alone imports nothing. Revalidate on click. Pulling assembles that Welder's workspace without changing boundaries or creating links. Mixed non-arc or unresolved lists must not silently import an eligible subset; explain why the list is not eligible. Already-present arcs need not be duplicated in the workspace. This receiver contract does not require implementing the Welder during the generic search slice.

## Search definitions
Created: 2026-10-13
Modified: 2026-10-13

Copy search copies the currently specified criteria, even if they have been edited since the last execution. It copies the question, not selected results or result UUIDs. The initial generic transfer format is:

```json
{
  "format": "arcs-basic-search",
  "version": 1,
  "criteria": {
    "type": "arc",
    "name-contains": "",
    "title-contains": "coast",
    "tags": ["home"],
    "tag-match": "all"
  }
}
```

Type is a Basic object-kind string or null for all types. Empty substrings and an empty tags array impose no constraint. Tag-match is all or any. Omitted fields reset to those empty defaults. A receiver validates structure and version, rejects unsupported semantics with a readable explanation, and never executes the payload as code. This is a proposed application protocol now adopted with the ratified search design, not an M1 formal transport format.

Search payloads carry no view identity, session bindings, or Welder destination. A search created in one window can be adopted by another without modifying the source. Copying should include only supported active criteria, not hidden controls or stale transient UI state. Future temporal predicates need a documented version-compatible extension or new version; do not discard them silently when receiving a format the current implementation cannot interpret.

## Reset versus incorporation
Created: 2026-10-13
Modified: 2026-10-13

Reset replaces the current query input, clearing existing criteria not supplied in the incoming query. Incorporation compares populated criteria: fill an unconstrained field from the incoming query, keep identical criteria once, and retain current criteria when the incoming field is unconstrained. Different populated constraints on the same field require an explicit conflict choice rather than silent replacement. For tags, compare the whole tag condition, including all/any; do not blindly union two conditions with different meanings.

Initially, conflicts can be presented with the current and incoming values and a Keep current/Use incoming choice per conflicting field. Apply the combined result only after those choices are resolved, or cancel with input untouched. A general Boolean query-builder is not required. Do not weaken current constraints or imply that every combination is automatically AND. Neither reset nor incorporation automatically runs; mark parameters changed and leave existing results until Search.

## Temporal ranges and clipboard detection
Created: 2026-10-13
Modified: 2026-10-13

Range transfer is the planned separate context payload described in [the temporal-range concept](../concepts/temporal-range-clipboard.md). Its exact serialization and ChronoMark query semantics are still a bounded temporal-slice decision. A range is not a search or a list of object references. Preserve uncertainty and explicit timezone and do not force unknown values into exact dates.

Tk accesses the clipboard, with semantic content sent to Core for classification and validation. Recognize supported payloads on window activation/focus, offer actions without applying them, and re-read before adoption. Do not depend on a continuous clipboard polling loop for generic search. Raw ordinary text remains ordinary text; malformed/unsupported data does not replace criteria. Cross-application behavior can reuse these documented formats later without adding a FileTalk router dependency to clipboard transfer.
