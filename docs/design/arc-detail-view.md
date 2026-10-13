# Arc Detail View
Created: 2026-10-11
Modified: 2026-10-12

## Role and source
Created: 2026-10-11
Modified: 2026-10-11

Use **Arc Detail View** as the name of the window showing one arc. It is distinct from Command Center and from a future broad arc explorer. Lion selects this view, alongside Command Center, as the first GUI focus. The adopted broad structure comes from [Wing-Cat's artifact](../design-references/arc-detail-view-from-wingcat.md): identity and summary above, chronology below-left, selected record details below-right. Open design suggestions in the source artifact are not automatically settled by adopting that structure.

The window is summoned on demand by a user action in the one Command Center, either creating a new arc or opening an existing arc. Repeated actions can create multiple views for the same or different arcs. Application startup does not create arbitrary detail windows or restore them without user action in this initial design.

## Header
Created: 2026-10-11
Modified: 2026-10-12

Show the arc's human-readable title, editable machine-oriented name, beginning and ending or ongoing status, and paragraph-length narrative description. Identity is the stable UUID behind the view; it can also be inspected through development output. The name permits lowercase letters, digits, and hyphens, with no spaces or underscores. It is not an immutable ID or an assumed unique lookup key. Title permits ordinary human-readable text and punctuation.

The description occupies a comfortable multiline text area. The header should ultimately permit editing title, name, description, and boundaries without requiring departure from the arc. The precise first-slice editing mechanism remains open: explicit edit/save controls or immediate working edits followed by deliberate save. Do not silently choose autosave behavior or copy Today's debounce timers merely because its code is available.

Lion now requires [arc tags](arc-tags.md), stored conceptually in Basic's tags list. The view needs a way to see and edit the displayed arc's tags; exact placement and controls remain to be designed. Tags will also support finding arcs for the exploratory Arc Welder.

Boundary information may include time and an associated event; it can also be unknown. An ongoing ending is a semantic state, not a date. Display preferences are distinct from temporal knowledge. The reference describes independently selectable beginning/ending formats, including date, year/month, event name, combined date/event, and ongoing. The full style chooser need not precede basic creation and viewing, but the first slice must not erase temporal precision or make an unknown time appear exact. The detailed editor and initial subset of styles remain to be settled.

## Chronology and detail panes
Created: 2026-10-11
Modified: 2026-10-11

Use a narrower scrolling chronology pane on the left and a wider detail pane on the right. Roughly 35/65 is a reference example, not a fixed requirement. Most recent records appear above older records. Selecting an event or journal entry changes the right-hand pane in that window. Another window's selection stays independent, even when both display the same arc.

An empty arc has an honest empty chronology and a right-hand no-selection state. It must not require a journal entry before the arc can be opened. A real chronology with records shows their distinguishable types and sufficient labels to select meaningfully; exact ordering for unknown or overlapping temporal claims remains to be designed. Do not silently use registration timestamps as occurrence times to manufacture order.

Sub-arc boundaries and interval visualization remain unresolved and are not required by the initial create-three-arcs scenario. Parent browsing, resource links, media, and neighborhood navigation are future extensions. The panes should not be filled with controls that imply those features already work.

## Required authoring buttons
Created: 2026-10-11
Modified: 2026-10-11

Place **New journal entry**, **New event**, and **Transition to another arc** buttons near the chronology, above the lower panes. Each acts on the arc displayed in this particular window, including when its chronology is empty. These are required working GUI actions, not optional Command Center buttons.

Use the right-hand detail pane as the draft editor with Save and Cancel while keeping the surrounding arc context visible. Ordinary entries and events populate the chronology without changing arc boundaries; a transition records an event, ends the current arc, and creates a successor. See [Arc authoring](arc-authoring.md) for the required flows, draft handling, multi-window updates, and atomic persistence of transitions.

## Multiple instances and updates
Created: 2026-10-11
Modified: 2026-10-11

Each view has a distinct view identity and reducer state in Core. Different arcs can be visible simultaneously. The architecture also supports multiple views of the same arc; a development opening action should make it possible to exercise that case, even if later ordinary opening behavior favors reusing an existing window.

A Mem result is distributed to all window reducers. Relevant reducers update their known data and emit targeted presentation commands without disturbing their independent selections. If editing is implemented, a refresh must preserve local unsaved text and distinguish it from the latest accepted snapshot. Conflict behavior is an implementation gate, not permission to overwrite a draft silently.

## Close behavior
Created: 2026-10-11
Modified: 2026-10-11

Closing this window removes the view and its Tk resources; it does not delete the arc, stop Core, or end the application. Draft behavior must be decided before editable controls ship. Closing Command Center closes the application and every Arc Detail window through the [lifecycle protocol](lifecycle.md).
