# Arc authoring
Created: 2026-10-11
Modified: 2026-10-11

## Status and placement
Created: 2026-10-11
Modified: 2026-10-11

These are required authoring actions in the Arc Detail View. Lion requests their inclusion in the specific design after the initial implementation omitted them. This document adopts the three-button direction previously held in [the authoring reference](../design-references/arc-authoring-proposal.md). It extends the existing implementation; it is not permission to rewrite its established architecture or resolved persistence protocol.

Every Arc Detail window has three visibly labeled buttons near the chronology, above the lower browsing panes:

- **New journal entry**
- **New event**
- **Transition to another arc**

They are available even when the chronology is empty. Each applies to the arc displayed in that window, identified by UUID, not a global last-selected arc or the title. These are actual GUI buttons with working authoring flows, not optional Command Center conveniences or placeholders. Command Center text equivalents may be added, but do not substitute for these buttons.

## Shared editor behavior
Created: 2026-10-11
Modified: 2026-10-11

Pressing a button opens a draft editor in that window's right-hand detail pane. Keep the arc header and chronology visible. Clearly identify the draft type and arc association, and provide **Save** and **Cancel**. This does not create an extra Command Center or automatically open unrelated windows.

Drafts belong to the window's reducer state in Core, separate from Mem's accepted records. Tk captures input and emits semantic events; validation, operation creation, and persistence follow the existing Core/Mem/Disk path. Allocate stable UUIDs for new domain records and preserve them through the save operation. Each event or journal entry is one record associated with the viewed arc, rather than duplicated content embedded in every arc.

Use Basic as the primary home for each event or journal entry's identity and descriptive content: journal prose and the description of what happened can occupy Basic's description field. One simplified Basic `type` distinguishes `event`, `journal-entry`, and `arc`; there is no additional typehint field. Basic's `date` can carry a simple associated date. Do not require separate domain tables just to repeat this data. Extending the current SQL Basic table and representing richer temporal information are described in [data and persistence](data-and-persistence.md); associations use the links table. Basic object type is separate from Link relationship type.

Cancel discards the new draft without creating domain records and restores the prior selection when still available. Selecting another item, starting another authoring action, or closing a view must not silently destroy unsaved content: offer Save, Discard, or Cancel navigation. A pending save cannot be submitted repeatedly by clicking Save; retain its operation state until completion. Save errors preserve the draft and display the error. The existing application's distinction between Mem acceptance and SQLite completion must be honored; do not report durable success prematurely.

After successful save, leave draft mode, select the created record, and show its readable details. Insert it at its chronology position, which may be below newer items. Other windows viewing the same arc receive the returned accepted-change information, update relevant data, and preserve their own selection and drafts.

## New journal entry
Created: 2026-10-11
Modified: 2026-10-11

Open a multiline writing area for the entry's content and a visible date/time control for the entry, associated with the viewed arc. A title may be offered but is not required by this design. Save creates the journal entry and its association, and selects it in the chronology. It does not change arc boundaries.

Persist the association as an independently identified `member-of` link from the journal entry UUID to the displayed arc UUID, in the links table. Use only the simplified type string, not a separate typehint.

Entry dating is distinct from a database creation timestamp. An editable present-time suggestion is permitted for writing now, but backdated or uncertain temporal information must not be silently made exact. Detailed temporal controls should reuse the established temporal representation rather than invent a competing format. Adding associations to other arcs is supported by the conceptual model but a multiple-arc picker is not required for this first authoring extension.

## New event
Created: 2026-10-11
Modified: 2026-10-11

Open an editor for what happened and when it happened, associated with the viewed arc. Require a meaningful nonempty description of what happened; do not require an exact occurrence date when it is unknown. Use ChronoMark-compatible temporal information and keep recording time separate from occurrence time. A title may be offered as a browsing label but does not replace the event description.

Save creates one event and its association and selects it in the chronology. This ordinary event action leaves the arc's beginning and ending unchanged. It does not implicitly create a successor or decide that a life passage has fundamentally changed.

Persist the association as an independently identified `member-of` link from the event UUID to the displayed arc UUID. Events and journal entries share this association type while retaining their distinct domain kinds.

## Transition to another arc
Created: 2026-10-11
Modified: 2026-10-11

Open a combined editor with three clearly distinguished parts: the current arc that will end, the transition event (what happened and its temporal information), and the new successor arc (title, name, and narrative description). The current arc is identified from this window's displayed UUID. Generate a distinct UUID for the successor; do not rename or overwrite the predecessor into the new arc. Require a successor title and a description of the event; successor narrative may be completed later.

Show the consequence before Save: **this event ends the current arc and begins the new arc**. Preserve uncertain timing consistently across the event and the two boundaries it establishes. The successor begins at this event and initially has an ongoing ending. Do not infer or automatically copy all parents, resources, or descriptions from the predecessor.

Save is one coherent operation that persists the event, its associations with both arcs, the predecessor's ending, the successor's beginning, the successor record, and the predecessor/successor relationship. Disk commits the related SQLite changes in one transaction: failure must not leave an event without its successor or end the predecessor while failing to create the new arc. Mem's accepted state and returned revisions must remain consistent with the established commit protocol. Validate current predecessor state and stale-base revisions before accepting; if an existing ending or concurrent update conflicts with the proposed transition, report it and preserve the draft rather than silently overwrite that boundary.

The predecessor/successor relationship is a separate **link object**, not just an anonymous association or a field on an arc. Lion explicitly requires conceptual conformity with M1's Link structure. Give the link its own stable UUID, `from` equal to the predecessor arc UUID, `to` equal to the successor arc UUID, and internal type `transition`. Its formal M1 Link Aspect type identifier is `tag:m1lattice.net,2026:/linktype/transition`.

Create a second link object with its own stable UUID, `from` equal to the transition link UUID, `to` equal to the transition event UUID, and internal type `via`. Its formal M1 type identifier is `tag:m1lattice.net,2026:/linktype/via`. This is the adopted structure “Arc A transitions to Arc A′ via Event E.” The event and links are distinct objects: the event records what happened, the transition link connects the arcs, and the via link connects that relationship to its event.

Internal SQLite representation remains free and may encode types simply as `transition` and `via`; it need not emit native M1. Preserve both link identities and endpoint directions, and include both links in the same transaction as the event, successor, and boundary changes. The exact identifiers and mapping are preserved in [M1 link types](../design-references/m1-link-types.md).

Store both relationship objects in the adopted [links table](links-table.md). They do not require Basic rows. Endpoint resolution covers both Basic objects and links, preserving the via link's ability to point from a transition link to an event.

The event's association with each arc is also an independently identified `member-of` link, directed from the event to that arc. Thus the transition operation creates four links: predecessor → successor (`transition`), transition link → event (`via`), event → predecessor (`member-of`), and event → successor (`member-of`). Persist all four in the same transaction. Only the simplified `type` string is stored; there is no typehint field.

After successful save, remain in the predecessor's Arc Detail View with the transition event selected. Show an explicit **Open successor arc** action in its details; activating it summons the successor's detail window. This gives the user control over navigation while making the next passage easy to reach. Every other relevant view receives the accepted result, including the updated predecessor boundary and chronology.

The initial transition editor creates a new successor. Choosing an existing successor or converting an existing event through **Use as transition…** remains a later extension, not a prerequisite for the three buttons. Such an extension must reuse an existing event's UUID rather than duplicate it.

## Remaining narrow decisions
Created: 2026-10-11
Modified: 2026-10-11

Use the current implementation's settled save protocol and schema where suitable. Extend them in a bounded sketch for journal entries, events, associations, and atomic transitions. The exact uncertain-time editor, chronology ordering of undated/disputed items, and any new record-field spelling need explicit local decisions. These questions do not make the three buttons optional or permit inert controls to count as completed authoring.
