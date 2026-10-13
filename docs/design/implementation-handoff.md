# First implementation handoff
Created: 2026-10-11
Modified: 2026-10-13

## Purpose and authority
Created: 2026-10-11
Modified: 2026-10-11

This document orients a separate implementation conversation that does not have the design conversation's history. Lion will provide programming conventions separately. This handoff supplies product intent, accepted architecture, initial scope, reference code, and questions still needing decisions. It does not authorize implementation merely by being read.

The initial application and authoring work have progressed since this first-slice handoff. For the newly ratified search extension, begin with [Basic Search](basic-search.md), [search clipboard](search-clipboard.md), [session names](session-names.md), and [search acceptance](basic-search-acceptance.md). Preserve the current implementation's settled mechanisms; this older handoff's unresolved details are not permission to redesign them. Generic search is the next bounded slice, followed by arc-specific temporal search and then the Welder.

`docs/design/` describes the adopted application direction. Specific unresolved details are labeled as such. `docs/design-references/` contains supporting artifacts and proposals, not blanket requirements. `docs/concepts/` contains vocabulary, background, and exploratory ideas. Implementation sketches belong in root-level `pseudo/`, code in root-level `src/`. Keep pseudocode exceptionally small: broad strokes, lightly expressed, not an exhaustive reification of the system.

## What Arcs is for
Created: 2026-10-11
Modified: 2026-10-11

Arcs helps Lion situate himself within meaningful passages of life and their causal and contextual relationships. An arc represents both a passage and his story to himself about who he is and what he is doing. It is not primarily a task manager or an attention-priority system. Focus is a separate application for attention management; Today provides daily context; the future Project Browser provides project context. ADHD-related distractibility makes continuity and recovery of context important.

An arc has a beginning, an end or ongoing state, and relationships to other arcs. It can belong to several larger arcs. Internal events do not necessarily change its defining character. A fundamental change means an arc ends and another begins, rather than the same arc shifting internally. A journal entry and an event are distinct domain records. Either may be associated with multiple arcs, usually one. An event may establish an arc boundary or connect an ending arc to its successor.

Arc identity is a stable UUID. Editable names and titles are not identity. Internal records and SQLite storage may use a custom shape but must be conceptually mappable to M1. ChronoMark is designated for uncertain temporal information. Record creation time must never be substituted for an unknown real-life beginning.

## First implementation focus
Created: 2026-10-11
Modified: 2026-10-11

The first GUI effort includes both **Command Center** and **Arc Detail View**. It is not sufficient to deliver only a terminal window or worker skeleton. There is exactly one Command Center throughout a running session, and it is the only window opened at startup. It acts as a programmer's remote control: a large output Text widget, a command Entry beneath it, and optional buttons. From it Lion must be able to issue three successive creation actions and keep the resulting detail windows open together. These are on-demand windows caused by user actions, never three random or prepopulated windows opened by startup. Created arcs persist in SQLite and can be reopened after restart through further user actions.

Each open window has its own reducer state within one Core machine. Tk owns all windows on the main thread. Mem owns canonical domain records. Disk owns the SQLite connection and persistence. Internal worker cooperation uses Mobile Stacks. Returned memory-change information is offered to every window reducer; relevant reducers handle it, others ignore it. This synchronization does not require revision polling.

Command Center controls process lifetime. Closing an Arc Detail window closes that view; closing Command Center initiates orderly shutdown of the entire application and all windows.

## Required initial behavior versus subsequent work
Created: 2026-10-11
Modified: 2026-10-11

The initial delivery must implement creation, durable retrieval, the actual arc header and two-pane detail layout, concurrent windows, and lifecycle behavior. The detail header should support the established identity, boundary, and narrative concepts. Editing mechanics and the extent of the initial temporal editor need a small design decision before rendering; do not silently present inert editable-looking controls as completed functionality.

The initial create/open implementation has now been completed according to Lion. He requests the next design extension explicitly: three required buttons in every Arc Detail View, **New journal entry**, **New event**, and **Transition to another arc**, with working authoring flows. [Arc authoring](arc-authoring.md) is now specific design authority for those actions; their earlier placement in design references no longer means they are optional or deferred. Empty chronology remains a valid state, and the buttons must work from it.

Banded exploration, Arc Neighborhood, frames, media management, project integration, full M1 exchange, and live FileTalk integration are later work unless explicitly brought into scope. Preserve the architecture and identities needed for them without implementing speculative general frameworks.

## Reading order
Created: 2026-10-11
Modified: 2026-10-11

1. This handoff and [overview](overview.md).
2. [Command Center](command-center.md), [Arc Detail View](arc-detail-view.md), [Arc authoring](arc-authoring.md), and [first-arc flow](first-arc.md).
3. [Architecture](architecture.md), [multiple windows](multiple-windows.md), and [lifecycle](lifecycle.md).
4. [Data and persistence](data-and-persistence.md), including unresolved implementation gates.
5. [Acceptance scenarios](acceptance-scenarios.md).
6. The relevant Today source, identified below, and Lion's programming conventions supplied in the implementation conversation.

Consult concepts selectively: `arc.md`, `m1.md`, `chronomark.md`, `filetalk.md`, `use-cases.md`. The [reference table](../../db/file-system-locations.json) preserves external documentation locations. Wing-Cat is Lion's separate ChatGPT collaborator; Aevia is the Codex collaborator maintaining this design. Their names are provenance, not application architecture.

## Today reference implementation
Created: 2026-10-11
Modified: 2026-10-11

The reference application is `F:\repo\today`, with executable package `src/today/`. Aevia inspected the relevant implementation on October 11, 2026. Follow current source when historical sketches disagree. Do not import Today's day/tab/panel model into Arcs.

| Source | What to inspect |
| --- | --- |
| `src/today/main.py` | Composition, queue wiring, worker startup, final join order |
| `src/today/machine.py` | Runtime installation, thread-local machine selection, stack transfer, handler completion, lifecycle and fatal latch |
| `src/today/mobile_stacks.py` | Bottom-first frames and traveling registers |
| `src/today/core.py` | Inbox translation, reducer event/effect processing, save generations, shutdown readiness |
| `src/today/tk.py` | Queue-before-wake, command draining, close request, main-thread failure check |
| `src/today/mem.py` | Canonical ownership, copied snapshots, revisioned acceptance, pending-write scheduling |
| `src/today/disk.py` | Resource-root resolution and Disk ownership; replace JSON day-bundle persistence with SQLite |
| `docs/architecture-review.md` | October 6 architecture report and limitations |

Today includes dynamic image workers. They are not required for this initial Arcs scope. The runtime's permanent worker model, ownership, and orderly shutdown are the relevant baseline.
