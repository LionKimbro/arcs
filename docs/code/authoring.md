# Authoring extension

The authoring schema described below was introduced as version 2. The current
[search extension](search.md) adds version 3 Basic tags and tag authoring controls.

Schema version 2 migrates v1 in a Disk-owned transaction: Basic gains `type` and
`date`; Arc gains `begin_event` and `end_event`; `links` uses the adopted DDL and
endpoint indexes; `temporal` stores ChronoMark-compatible entry/event content.
Basic owns descriptive content, including journal prose. Link type and Basic
type have distinct meanings. `authoring.LINK_TYPES` preserves the exact M1 mapping.
Links are independent entities; optional Basic metadata shares the link UUID.

Mem loads Basic objects and links once at startup. Arc records remain indexed
separately for existing commands. Core view state gains chronology, selection,
prior selection, author draft, and pending author operation. Draft UUIDs are
allocated once by Core. Selection uses already-copied records, so no asynchronous
selection result can replace a newer one. Accepted changes refresh relevant
chronologies; unrelated views and all other author drafts remain untouched.

`authoring` validates and stages one bundle. Ordinary authoring adds a Basic
record, temporal aspect, and member-of link without updating Arc. Transition adds
the event first, successor second, predecessor update third, then four links.
The event, predecessor end, and successor begin share the uncertain occurrence
point; period claims and boundary-event references retain its meaning and history.
The successor ends ONGOING. Stale revisions, established endings, unresolved
boundary claims, and existing outgoing transitions are rejected.

Disk writes the whole bundle under BEGIN IMMEDIATE, verifies object revisions
and endpoint existence within that transaction, and returns committed completion.
Only then does Mem install any of it. Integrity/operational write errors roll back
and return readable errors; the editor and draft survive. Unexpected failures still
use the existing fatal-worker boundary. A failed save during orderly close cancels
close rather than claiming a saved exit. There is no multi-process write protocol.

`author_ui` is part of the Tk presentation machine. It captures fields and navigates
through semantic events, without touching Mem or SQLite. Save/Cancel remain fixed
above a scrolling editor. Dirty navigation offers Save/Discard/Cancel; a requested
navigation after Save occurs only following a successful commit. Cancel restores
the prior selection. Submitted editor controls freeze until completion. Closing a
view with its submitted author save outstanding does not undo that save.

Calendar and offset timestamp controls preserve precision, optional bounds, and
notes. Basic date is the occurrence focus, not registration time. Chronology orders
by working focus (latest/earliest bound if absent), descending; unknown times remain
last, with UUID ties. Full competing-claim editing and interval visualization remain
future work. UI labels expose precision/uncertainty, never a synthetic creation date.

Verification includes legacy migration, copied data, multi-window draft/selection
isolation, backdating, unknown time, transition/via/member-of identities and rollback,
duplicate submission, endpoint revalidation, multiple parents, optional link Basic
metadata, Save/Discard/Cancel navigation, and close with a held author save. Native
Tk creation and reopening run in fresh processes against temporary databases.
