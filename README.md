# Arcs

Arcs records meaningful passages of life, their boundaries, and your story about
them. It provides a tkinter Command Center, concurrent Arc Detail windows,
journal/event authoring, event-driven transitions, and SQLite persistence.
The interface follows Today's dark layered panels and flat controls, with an
amber palette, warm cream text, and gold focus and action accents.

## Run

Requires Python 3.11+ with tkinter (included with normal Windows Python installs).

```powershell
python -m pip install -e .
arcs
```

The default database is `<MachineRoot db-root-2026>/arcs/arcs.sqlite3`. Missing
MachineRoot configuration fails clearly. To choose an exact database instead:

```powershell
arcs --database F:/my-data/arcs.sqlite3
```

The editable install creates the `arcs` command and picks up source changes
without reinstalling. Run it from any directory. `python -m arcs` is also supported.

## Commands and editing

- `create-arc`: commits a new arc, prints its UUID, and opens its detail window.
- `edit-arc <name-or-UUID>`: opens another view of that existing arc. Names match exactly; if several arcs share a name, use its UUID from `list-arcs`.
- `list-arcs`: prints `name:UUID` for each known arc.
- `search`: opens an independent Basic Search window.
- `open <name-or-UUID>`: opens an arc or inspects another Basic object.
- `help`: displays the command summary.
- `exit`: closes Arcs, with the usual unsaved-draft prompts and completion of submitted saves.

Commands ignore case and use the supplied `cmdparts` parser. There is no shell
evaluation. Startup opens Command Center alone. New arcs have title “Untitled
arc,” a generated editable name, and unknown boundaries. Creation does not imply
an ongoing ending or a beginning today.

Double-click a UUID label to copy it to the clipboard. UUIDs in Command Center
output and saved journal/event prose can also be copied by double-clicking them.

Edit title, lowercase/digit/hyphen name, tags, description, and boundaries, then click
**Save**. Boundaries accept `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, or `UNKNOWN`; the end
also accepts `ONGOING`. Changed boundaries add a ChronoMark claim and select it
as the working claim; previous claims remain. Richer saved boundaries appear as
JSON and survive unrelated edits; this is not a full ChronoMark editor.

Each window has its own draft. A save from another window refreshes clean views
and preserves dirty drafts. A stale-base save reports a conflict; **Reload saved**
asks before discarding a draft. Typing during an outstanding save remains unsaved.
Closing a detail window closes only that view. Navigation and close offer Save,
Discard, or Cancel for dirty drafts. Closing Command Center waits for submitted
operations and their commit returns. Unexpected worker/storage failure closes the application with exit 1;
it does not promise to save pending work. Terminal tracebacks provide diagnostics.

## Journals, events, and transitions

Each detail window has **New journal entry**, **New event**, and **Transition to
another arc** buttons above its chronology. Their editors occupy the right pane;
Save and Cancel stay visible while the longer editor scrolls. Saved records are
selected and readable in that pane. Other views refresh their chronologies while
retaining their own selections and drafts.

Occurrence controls accept `UNKNOWN`, years, months, dates, or ISO timestamps
with an explicit offset, such as `2026-10-11T12:30:00-07:00`. Optional earliest and
latest bounds plus temporal notes preserve uncertainty. Basic's `date` contains
the stated focus value, if any; it is not the database registration time. Chronology
uses the working focus, falling back to stated bounds, newest first; undated items
appear last with stable UUID ordering. This display order does not claim that
overlapping or approximate times are historically disjoint.

A transition editor combines the event and a new successor arc. Saving ends the
predecessor at that event, begins the successor there, and marks its end ongoing.
All objects and four independently identified links commit together. Stay in the
predecessor view, then use **Open successor arc** in the event details. Boundary
event buttons also let you revisit the beginning/ending event. A stale or already
ended predecessor is rejected without losing the draft. **Refresh predecessor**
explicitly updates the transition's base revision before retrying.

Authoring validation and transaction errors preserve the draft and report the
error; retry uses the same object identities. If a submitted save fails during
close, closing is canceled. Cancel creates no record. Ordinary events and journals
do not modify arc boundaries. Submitted authoring controls are disabled until the
operation returns, preventing duplicate Save clicks.

## Basic Search and session names

Enter `search` in Command Center. Each search window starts without running a
query and has independent parameters, results, and checkbox selections. Filter
by Basic type, name/title substrings, and comma-separated tags. Substrings and
whole-tag matches ignore case; populated filters combine with AND. Choose All
tags or Any tag. Empty filters find all Basic objects, including links with Basic
metadata; links without Basic metadata are not results.

**Search** executes the parameters. Editing or **Clear parameters** keeps old
results labeled with their executed query. A new search clears selection; saves
refresh executed queries while preserving surviving selections and edited input.
Use individual checkboxes, Space on a focused row, or Select all. Open selected
requires one object and opens its real detail/inspection window. Full UUIDs in
the results can be copied by double-clicking their column.

**Name selected object(s)…** assigns one session name per object. Names have no
whitespace, preserve case, and cannot look like full UUIDs. Duplicate names in a
batch are rejected. Rebinding requires reviewing both objects and explicitly
replacing the bindings; cancel applies nothing. Session names are shared across
windows and disappear at application exit. They shadow Basic names in `open` and
`edit-arc`, while explicit UUIDs always identify the object directly. Assignment
does not rename Basic records. Search substring fields remain literal text.

**Copy reference(s)** writes a JSON array of full UUID strings to the system
clipboard, even for one object. **Copy search** writes the currently edited
criteria in the versioned `arcs-basic-search` format. On focus, another search
window offers **Reset to clipboard search** and **Incorporate…**. Adoption never
runs a query. Reset replaces criteria; incorporation retains compatible filters
and asks Keep current/Use incoming for conflicts. Cancel leaves input unchanged.
Clipboard access/validation errors preserve parameters and results.

Tags are stored in Basic as a JSON list. Enter comma-separated labels in Arc
Detail or authoring forms; spaces within a label are allowed. Labels are trimmed,
empty separators ignored, and case-insensitive duplicates keep their first
spelling. Commas and line breaks cannot be part of a label. Saving or removing an
arc's tags changes only that object's tags. Tags are classification, not links.

SQLite schema version 3 adds `tags_json` to the version 2 Basic representation.
Version 2 extended `basic` with one object-kind `type` and `date`,
uses `links` for UUID-keyed directed relationships, and `temporal` for richer entry/
event claims. Prose lives only in Basic. Arc aspect data remains in `arc`. There
are no separate event/journal body tables or parallel typehint fields. Link endpoints
resolve to Basic objects or other links; links need no Basic row. Existing v1/v2
databases migrate automatically, initially assigning empty tags while preserving
identities, metadata, temporal claims, and links.
Use one running Arcs session per database; there is no multi-process edit protocol.

Temporal search/range transfer and the Arc Welder await their separate design
decisions. Full temporal editing, existing-successor transitions, M1 exchange,
and FileTalk integration remain subsequent work.

## Verification

```powershell
./run-tests.bat
```

This checks coding conventions, worker integration, and fresh-process real Tk
creation/reopening, authoring, draft navigation/conflicts, atomic transition rollback,
migration, endpoint validation, shutdown, and fatal-worker/write failures.
Search checks include stale/closed returns, domain refresh, tags, session naming,
clipboard contracts, real system clipboard transfer, and native search dialogs.
All databases used by these checks are temporary; no personal database is touched.
GUI checks briefly open native windows.

Design: [docs/design/overview.md](docs/design/overview.md). Implementation notes:
[docs/code/first-slice.md](docs/code/first-slice.md) and
[docs/code/authoring.md](docs/code/authoring.md) and [docs/code/search.md](docs/code/search.md).
BAD sketches: [pseudo/first-slice.md](pseudo/first-slice.md),
[pseudo/authoring.md](pseudo/authoring.md), and [pseudo/search.md](pseudo/search.md).
