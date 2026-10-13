# Arc Welder
Created: 2026-10-12
Modified: 2026-10-13

## Concept and motivation
Created: 2026-10-12
Modified: 2026-10-12

Lion names a possible neighborhood-and-linking interface the **Arc Welder**. It should make it easy to look at the neighborhood of an arc and weld arcs together in interesting ways. The need emerged while entering historical information: the current transition button is the only implemented linking workflow, and general linking was never planned. This is a new capability to explore, not a repair of broken behavior.

## Relationship to Arc Neighborhood
Created: 2026-10-12
Modified: 2026-10-12

Arc Neighborhood was proposed as navigation through an arc's parents, children, predecessors, successors, and associated records. Arc Welder adds active relationship authoring to that neighborhood exploration. Its exact layout and place in the application remain open; it is not yet a committed implementation specification.

## Working interpretation — Aevia
Created: 2026-10-12
Modified: 2026-10-12

Welding creates independently identified links between objects that retain their own UUIDs, content, and histories. It does not mean merging arc objects. A possible interaction is to select the arc being explored, choose another object, specify the relationship and direction, inspect the proposed connection, and save it. The neighborhood would then reveal the new connection for navigation.

Historical and current arcs should be available to explore without assuming that every connection is a live transition that ends one arc and creates another. Linking existing objects and editing their temporal boundaries are distinct operations. Whether the Welder also connects events and journal entries, provides transition-via-event authoring, supports new relationship types, or exposes link objects themselves needs discussion. Existing types and their meanings are recorded in [M1 link types](../design-references/m1-link-types.md).

## Gathering arcs into the workspace
Created: 2026-10-12
Modified: 2026-10-12

Lion describes starting with one arc, then deliberately “pulling into” the workspace other arcs found through search criteria. Discovery methods include temporal overlap with the starting arc, temporal neighboring within a user-specified number of days/months/years/decades, tags, name substring, and title substring. Name and title are separate searchable fields, not substitutes for UUID identity. These are ways to find candidates, not automatic declarations that the arcs are related. The user chooses which candidates to bring into the workspace and which relationships to establish.

Temporal overlap discovers contemporaneous arcs. Temporal neighboring can also bring in passages just before or after the starting arc. Whether neighboring measures the gap between intervals or distance from a particular boundary, and how calendar units and uncertain ChronoMark bounds affect results, remains to be designed. Candidate discovery must not silently turn uncertain temporal information into certain overlap or proximity.

Lion explicitly identifies [arc tagging](../design/arc-tags.md) as a needed capability. Tags can provide another route to relevant arcs when temporal proximity alone is insufficient. How criteria combine, which search results are shown, and the workspace's visual arrangement remain open.

## Possible search entry point
Created: 2026-10-12
Modified: 2026-10-13

Lion originally suggested a general [Arc Search](arc-search.md) window rather than limiting discovery to controls inside the Welder. The original direct Pull into Arc Welder action in search is now superseded by clipboard transfer as described below.

Lion then broadens this to [Basic Search](basic-search.md): search any object with Basic metadata using Basic criteria. Arc results can be found by object type together with name/title/tag filters. Adjacency, overlap, and approximate temporal proximity remain arc-specific searches; how to integrate them with Basic Search is open. The Arc Welder does not require committing to a separate general Arc Search window.

## Clipboard pull-in
Created: 2026-10-13
Modified: 2026-10-13

Basic Search's Copy references action places a JSON list of UUID strings on the clipboard. The Welder has a button that becomes available/highlighted when the clipboard contains a nonempty UUID list resolving to arcs. Pressing it pulls those arcs into that Welder's workspace. Clipboard recognition does not itself import anything; the user chooses when and where to pull them in.

Resolve UUIDs against the domain data rather than guessing object kind from the text: a well-formed UUID alone does not prove that the object exists or is an arc. Mixed non-arc or unresolved lists must not be silently treated as an eligible all-arc list. Revalidate when the action is activated because clipboard contents may have changed. Detection timing and presentation of ineligible lists remain open.

Pulling adds existing arcs to the workspace, preserving identities and boundaries and creating no weld links. Each Welder consumes the clipboard into its own workspace when its button is pressed, so search does not need a destination picker or direct knowledge of Welder windows.
