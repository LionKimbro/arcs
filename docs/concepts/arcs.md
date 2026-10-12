# Arcs
Created: 2026-10-11
Modified: 2026-10-11

## Purpose and current work
Created: 2026-10-11
Modified: 2026-10-11

Arcs is the system Lion and Codex are discussing in this repository. It tracks the [arcs](arc.md) of Lion's life, with emphasis on causality and relationships between passages of life. Calendar dates matter, but they are not its organizing center. The current work is conceptual, particularly the design of what the user interface needs to do.

Arcs is one of four major [cockpit](cockpits.md) areas, alongside Today, Projects, and Focus.

An arc also represents Lion's story to himself about who he is and what he is doing. Arcs therefore supports orientation through personal narrative and self-understanding as well as temporal and causal relationships.

Its data must be conceptually mappable to [M1](m1.md) for cooperation with other systems, with stable UUID identity as the key. Internal structure and storage remain free choices, including SQLite or custom JSON. M1 interoperability does not prescribe the application's internal schema.

Lion has selected SQLite, with the Disk machine owning persistence. [Data storage](data-storage.md) records the decisions and open design choices; each arc's UUID is established regardless of storage.

## Connection to the earlier design
Created: 2026-10-11
Modified: 2026-10-11

The [initial design note](../raw/002__initial-thrust.md) describes meaningful lived time, overlapping arcs, an arc-field, transitions, and preservation of continuity. Its proposed initial capabilities are creating and editing arcs, marking shifts, showing the current arc-field and history, and visualizing overlap. It defers productivity features.

Lion's October 11 account adds explicit nesting, life-scale and historical examples, and [M1](m1.md) as the conceptual object model. These notes preserve the earlier ideas as design context, rather than treating every earlier proposal as a settled requirement.

Lion subsequently clarified that an arc can belong to multiple larger arcs and that the current model has no internal arc shifts: a change in defining character ends one arc and begins another. This revises the earlier “mark arc shift” proposal. [Events](event.md) can occur within an arc without changing its character, or mark a beginning or endpoint. [Journal entries](journal-entry.md) are a separate kind of record. Both events and journal entries are usually associated with one arc but can be associated with multiple arcs.

## Implementation context
Created: 2026-10-11
Modified: 2026-10-11

The repository currently contains design and conceptual source material and an empty Python package scaffold. The October 7 work note references the Tk/Core/Mem/Disk worker architecture with Mobile Stack continuations used in Today and applies only to that date. Lion has now explicitly adopted that architecture in this conversation; the current decision is recorded in [docs/design](../design/overview.md). It is not yet implemented in Arcs.
