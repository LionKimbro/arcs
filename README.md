# Arcs

Arcs records meaningful passages of life, their boundaries, and your story about
them. It provides a tkinter Command Center, concurrent Arc Detail windows,
journal/event authoring, event-driven transitions, and SQLite persistence.

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
- `help`: displays the command summary.
- `exit`: closes Arcs, with the usual unsaved-draft prompts and completion of submitted saves.

Commands ignore case and use the supplied `cmdparts` parser. There is no shell
evaluation. Startup opens Command Center alone. New arcs have title “Untitled
arc,” a generated editable name, and unknown boundaries. Creation does not imply
an ongoing ending or a beginning today.

Double-click a UUID label to copy it to the clipboard. UUIDs in Command Center
output and saved journal/event prose can also be copied by double-clicking them.

Edit title, lowercase/digit/hyphen name, description, and boundaries, then click
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

SQLite schema version 2 extends `basic` with one object-kind `type` and `date`,
uses `links` for UUID-keyed directed relationships, and `temporal` for richer entry/
event claims. Prose lives only in Basic. Arc aspect data remains in `arc`. There
are no separate event/journal body tables or parallel typehint fields. Link endpoints
resolve to Basic objects or other links; links need no Basic row. Existing v1
databases migrate automatically without changing arc identities or metadata.
Use one running Arcs session per database; there is no multi-process edit protocol.

Full temporal editing, existing-successor transitions, M1 exchange, and FileTalk
integration remain subsequent work.

## Verification

```powershell
./run-tests.bat
```

This checks coding conventions, worker integration, and fresh-process real Tk
creation/reopening, authoring, draft navigation/conflicts, atomic transition rollback,
migration, endpoint validation, shutdown, and fatal-worker/write failures.
All databases used by these checks are temporary; no personal database is touched.
GUI checks briefly open native windows.

Design: [docs/design/overview.md](docs/design/overview.md). Implementation notes:
[docs/code/first-slice.md](docs/code/first-slice.md) and
[docs/code/authoring.md](docs/code/authoring.md). BAD sketches:
[pseudo/first-slice.md](pseudo/first-slice.md) and [pseudo/authoring.md](pseudo/authoring.md).
