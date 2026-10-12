# Interface directions
Created: 2026-10-11
Modified: 2026-10-11

## Status
Created: 2026-10-11
Modified: 2026-10-11

These are broad candidate interface concepts for discussion, not a settled design or implementation request. Lion is gathering use cases from his notes. He requested conceptual descriptions without screenshots. The alternatives below may turn out to be complementary views rather than exclusive designs.

Lion has now supplied four [use cases](use-cases.md): browsing, logging a journal entry, logging an event, and logging an event plus an arc transition. Browsing includes parent arcs and connected resources, plus instructing Today to navigate to a particular day. These are concrete workflows against which to evaluate the candidate views.

## Record views and arc detail — Lion's sketch
Created: 2026-10-11
Modified: 2026-10-11

Lion expects views for a [journal entry](journal-entry.md), an [event](event.md), and an [arc](arc.md). Whether each is a separate window or appears within a browser remains open.

The tentative arc view occupies a rectangular space: information about the arc at the top, a chronology with most recent items first in the lower-left, and details of the selected journal entry or event below or toward the lower-right. Selection in the chronology determines which record's details appear. This is a conceptual arrangement, not a finalized layout or a decision about editing behavior.

## Banded interface — Lion's concept
Created: 2026-10-11
Modified: 2026-10-11

Show arcs as time spans within bands representing areas of life, such as relationships, friends, or employment. Within a band, avoid visual overlap by adding a row when concurrent spans require it. Reuse rows for non-overlapping spans and favor fewer rows rather than permanently assigning a row to each person or job. The resemblance to a Gantt chart concerns temporal layout; dependency tracking is not the organizing purpose. This arrangement reveals continuity, concurrence, gaps, and changes across areas of life. Bands are not yet defined as M1 relationships, tags, or containing arcs.

Lion currently thinks a banded explorer should exist somewhere in the program. Its strength is showing size and proportion in relation to calendar time and spatial extent. Its location and whether it is the opening view remain undecided.

## Selected-day scale view — Lion's concept
Created: 2026-10-11
Modified: 2026-10-11

Start with a selected day, defaulting to today, and show the arcs relevant on that date at different timescales without requiring drawn timelines. Lion explored both vertical directions, then described the broadest passages as the foundation at the bottom and smaller, more immediate passages above. Actual containment, duration-based arrangement, and separate concerns such as work or relationships need to be distinguished: a longer span does not automatically contain a shorter one conceptually. Lion considered a hierarchical arrangement but also questioned it, and suggested a tag such as work as a possible focus. These choices remain open. Dictated personal names and era names in the examples have not been resolved to authoritative spellings.

Lion is now less confident in this direction because it risks overlapping [Focus](focus.md), whose fundamental concern is different. This is not currently a preferred Arcs direction.

## Current story cockpit — Codex proposal
Created: 2026-10-11
Modified: 2026-10-11

Orient the opening view around the stories Lion is currently living: who he understands himself to be and what he is doing. Show a small set of current arcs with their defining character, why they began, and relevant recent events or journal entries. Larger context and related arcs are available from each story. The purpose is rapid recovery of personal orientation; a story's prose presentation is not a proposed mandatory data field.

Lion finds its literary/textual quality intriguing, but judges this proposed cockpit to overlap Focus and therefore to be out of scope for Arcs. This excludes the interface proposal, not the established idea that an arc expresses a story to oneself.

## Arc neighborhood — Codex proposal
Created: 2026-10-11
Modified: 2026-10-11

Choose one arc as the center and explore its immediate relationships: larger arcs it belongs to, smaller arcs it contains, predecessor and successor arcs, and associated events or journal entries. Expand or follow one relationship at a time rather than requiring an entire life graph to be visible. This respects multiple parents and makes the causal and contextual connections around a passage the main means of navigation.

Lion is interested in this direction and describes its appeal as hodological. Its tension with the banded explorer is that navigating meaningful relationships does not by itself reveal temporal size and proportion. How to retain both qualities remains open.

## Life chapters — Codex proposal
Created: 2026-10-11
Modified: 2026-10-11

Browse a readable account of life through arcs, significant events, and journal entries, with broad passages expandable into more particular ones. Follow a concern such as work or relationships, or explore an era across concerns. Allow concurrent and multiply related passages rather than forcing one exclusive sequence of chapters. The purpose is remembering and interpreting the story over time; ChronoMark uncertainty should be retained rather than made artificially exact for presentation.

In response to this direction, Lion introduced [frames](frame.md): predefined views that determine what to show, what not to show, and how to present it visually. This does not yet establish Life Chapters as a chosen view.
