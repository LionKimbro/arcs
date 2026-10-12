# Arc authoring — Aevia proposal
Created: 2026-10-11
Modified: 2026-10-11

## Status and placement
Created: 2026-10-11
Modified: 2026-10-11

This document preserves the original proposal. Lion has now requested the three authoring buttons as specific design; [docs/design/arc-authoring.md](../design/arc-authoring.md) is the authoritative adopted design and supersedes this proposal where they differ. The proposal extends [Wing-Cat's Arc Detail View](arc-detail-view-from-wingcat.md): three visible actions near the chronology, **New journal entry**, **New event**, and **Transition to another arc**, with the right-hand pane used as a draft editor while retaining arc context.

## New journal entry
Created: 2026-10-11
Modified: 2026-10-11

Open a draft associated with the viewed arc, offering its text and date, with any title or additional associations treated as design choices rather than settled required fields. Save adds it to the chronology at its chronological position and selects it for reading. Cancel returns to the previous selection. If another draft is open, preserve it or ask how to handle it rather than silently replacing it. Detailed draft persistence remains undecided.

## New event
Created: 2026-10-11
Modified: 2026-10-11

Open a draft associated with the viewed arc, with what happened and temporal information. Use ChronoMark-compatible temporal representation; do not equate the recording date with the occurrence date or force uncertain time to be exact. Save adds and selects the event. Ordinary event creation leaves the arc's boundaries unchanged.

## Transition to another arc
Created: 2026-10-11
Modified: 2026-10-11

Offer a dedicated action because a transition is a meaningful authoring use case. The editor combines the transition event with identification of the successor arc. Initially it can support creating the successor; choosing an existing arc is a possible later addition. Show the current arc explicitly as the arc that will end. Capture the event's occurrence information and the successor's title and description, with other successor metadata handled as needed.

Before saving, present the consequence together: this event ends the current arc and begins the successor. Saving establishes the event, its association with both arcs, the corresponding boundaries, and the predecessor/successor relationship as one coherent user action. The exact data representation and persistence guarantees are not specified here. The predecessor retains its identity and history; “replacement” describes succession, not overwriting it.

Keep the completed transition visible in the current arc, with an explicit **Open successor arc** action so saving does not unexpectedly navigate away. An existing event could also offer **Use as transition…**, reusing its identity instead of creating a duplicate event. The selected temporal information should remain consistent across the event and the boundaries it establishes; uncertain timing must remain uncertain.

## Questions exposed by the proposal
Created: 2026-10-11
Modified: 2026-10-11

Whether chronology mixes records by occurrence date or journal date, how uncertain or undated records sort, and how drafts survive navigation remain open. A transition should not automatically copy every parent arc or resource association to the successor; the desired inheritance behavior needs explicit design.
