# Arc Detail View — Wing-Cat
Created: 2026-10-11
Modified: 2026-10-11

## Source and status
Created: 2026-10-11
Modified: 2026-10-11

This design concept is transcribed and organized from a proposal by Wing-Cat. It describes a conceptual Arc Detail View, not a finalized interface or implementation specification. The overall structure is proposed; exact proportions, editing behavior, and sub-arc visualization remain open.

## Conceptual wireframe
Created: 2026-10-11
Modified: 2026-10-11

```text
ARC DETAIL VIEW

ARC HEADER
  Arc Title
  arc-name
  Beginning ↔ Ending / Ongoing
  Editable paragraph-length description of the arc

CHRONOLOGY
  ▼ Recent event
    Journal entry
    Sub-arc boundary?
  Older entries ↓

DETAIL VIEWER
  Selected item
  Event or journal entry
  Full content / details of the selected chronological item
```

This wireframe captures the broad arrangement: an identity-and-summary region across the top, with a chronological browser coupled to a detail viewer below. The precise arrangement within the header, proportions, and sub-arc visualization remain open.

## Arc Detail View
Created: 2026-10-11
Modified: 2026-10-11

### Arc header
Created: 2026-10-11
Modified: 2026-10-11

The header occupies the top region and contains the arc's identity, temporal boundaries, and description.

#### Arc title

- Human-readable title.
- May use uppercase, lowercase, spaces, and ordinary punctuation. Title Case is permitted but not required.
- Editable.

#### Arc name

- Machine-oriented identifier.
- Lowercase letters (`a-z`), digits (`0-9`), and hyphens (`-`) only.
- No spaces or underscores.
- Editable.
- Example: `building-the-temple-of-focus`.

#### Arc temporal boundaries

The beginning and ending each have a date, potentially including a time, and may reference an event that establishes the boundary. Their presentation styles are configurable independently. The date, associated event, and presentation are editable.

The ending may instead have the status `ongoing`.

Possible boundary presentation styles include:

- Date only: `2026-10-11`
- Date and time: `2026-10-11 14:30`
- Event name only: `The Project Begins`
- Date prominently, with the event name underneath
- Event name prominently, with the date underneath
- Month and year only: `October 2026`
- Year only: `2026`
- Ongoing status: `Ongoing`

Approximately eight or nine predefined styles were suggested. The beginning and ending may use different styles. Presentation is distinct from the underlying temporal data.

#### Arc description

- Large, multiline editable text area, comparable to a `Tkinter.Text` widget.
- Comfortably accommodates at least one paragraph.
- Presents the arc's narrative description.
- Can be edited without leaving the page.

#### Header editing controls

Some means of editing the title, name, description, and boundaries is needed. The interaction design is undecided; possibilities include inline editing, an edit button or mode, or individual controls.

### Arc browser
Created: 2026-10-11
Modified: 2026-10-11

The browser occupies the lower region and consists of a narrower chronology pane on the left and a wider detail pane on the right.

#### Chronology pane

- Vertically scrolling list, in reverse chronological order: most recent at the top and oldest at the bottom.
- Vertical scrollbar on the right edge of the pane.
- Selectable chronological items include events, journal entries, and possibly sub-arc boundaries.
- Selecting an event or journal entry displays it in the detail pane.
- Sub-arc boundaries could show the beginning and ending markers of child arcs, making their temporal extent visible. Their design is unresolved, particularly when sub-arcs overlap. Whether sub-arcs themselves appear as selectable items remains undecided.

#### Detail pane

- Displays the selected chronology item; the selection in the chronology pane determines its contents.
- For an event, displays event details and associated information.
- For a journal entry, displays its content and associated information.
- A future sub-arc selection might show a preview or navigate to that arc's own detail view.
- Editing behavior in this pane is unspecified.

#### Pane layout

- Two columns: chronology on the left, detail on the right.
- The left column is narrower; the right column receives most of the width.
- An initial ratio of 35% chronology and 65% detail was suggested as an example.
- Whether the divider is draggable remains undecided.

## Questions for a later design pass
Created: 2026-10-11
Modified: 2026-10-11

### What is an arc boundary?

Are beginning and ending dates fundamentally dates, events, or both? Wing-Cat suggests modeling a boundary as an object with its own temporal information, an optional event reference, and a presentation preference. This would separate the underlying data from its display. This is a design suggestion, not a settled data model.

### How should sub-arcs appear in chronology?

A sub-arc occupies an interval rather than a single moment. If sub-arcs overlap, showing them in a chronological list may call for an interval visualization, perhaps with vertical tracks alongside events and journal entries and markers for sub-arc beginnings and endings. The design remains unresolved.

### Is the detail pane also an editor?

The right pane might serve as both viewer and editor, allowing the chronology to remain stable while the selected item is read or edited. This behavior has not been decided.

## Design summary
Created: 2026-10-11
Modified: 2026-10-11

The top tells us what the arc is and when it exists. The left tells us what happened within it. The right lets us examine one thing in depth. This is Wing-Cat's proposed visual grammar for the Arc Detail View.
