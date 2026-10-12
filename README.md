# Arcs

Arcs records meaningful passages of life, their boundaries, and your story about
them. This first slice provides a tkinter Command Center, concurrent Arc Detail
windows, explicit editing, and SQLite persistence.

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

From an uninstalled checkout:

```powershell
./run-arcs.bat
# Or choose an exact database:
./run-arcs.bat --database F:/my-data/arcs.sqlite3
```

## Commands and editing

- `create-arc`: commits a new arc, prints its UUID, and opens its detail window.
- `edit-arc <UUID>`: opens another view of that existing arc.
- `list-arcs`: prints `name:UUID` for each known arc.
- `help`: displays the command summary.

Commands ignore case and use the supplied `cmdparts` parser. There is no shell
evaluation. Startup opens Command Center alone. New arcs have title “Untitled
arc,” a generated editable name, and unknown boundaries. Creation does not imply
an ongoing ending or a beginning today.

Edit title, lowercase/digit/hyphen name, description, and boundaries, then click
**Save**. Boundaries accept `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, or `UNKNOWN`; the end
also accepts `ONGOING`. Changed boundaries add a ChronoMark claim and select it
as the working claim; previous claims remain. Richer saved boundaries appear as
JSON and survive unrelated edits; this is not a full ChronoMark editor.

Each window has its own draft. A save from another window refreshes clean views
and preserves dirty drafts. A stale-base save reports a conflict; **Reload saved**
asks before discarding a draft. Typing during an outstanding save remains unsaved.
Closing a detail window closes only that view. Closing Command Center asks before
discarding unsaved drafts and waits for submitted operations and their commit
returns. Unexpected worker/storage failure closes the application with exit 1;
it does not promise to save pending work. Terminal tracebacks provide diagnostics.

SQLite uses one UUID-keyed `basic` table for the M1 Basic fields, and a separate
UUID-keyed `arc` table for the Arc aspect's revision and temporal content. Identity
is permanent; names are not unique keys. Use one running Arcs session per database;
external writes cause a fatal consistency error rather than an unnoticed overwrite.

Journal/event authoring, transitions, full temporal editing, M1 exchange, and
FileTalk integration are subsequent slices. The chronology currently shows an
honest empty state.

## Verification

```powershell
./run-tests.bat
```

This checks coding conventions, worker integration, and fresh-process real Tk
creation/reopening, draft conflicts, shutdown, and fatal-worker/write failures.
All databases used by these checks are temporary; no personal database is touched.
GUI checks briefly open native windows.

Design: [docs/design/overview.md](docs/design/overview.md). Implementation notes:
[docs/code/first-slice.md](docs/code/first-slice.md). BAD sketch:
[pseudo/first-slice.md](pseudo/first-slice.md).
