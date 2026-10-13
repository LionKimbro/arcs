# Basic Search implementation

`search` owns pure criteria/matching/clipboard validation. `search_core` is part
of the Core machine: per-window reducers, executed/displayed/input specifications,
query and selection generations, clipboard incorporation, inspections, and shared
session bindings. `search_ui` is part of the Tk machine: independent amber windows,
checkbox rows, scrolling naming/rebinding dialogs, read-only inspections, and
system clipboard effects. No additional workers or database access in Tk.

Mem searches accepted Basic records and returns copied result metadata under a
Mobile Stack carrying view identity and query generation. Core retains that data
before stack retirement and ignores obsolete/closed-view returns. Every accepted
domain change offers refresh to executed searches; unused windows remain unused.
Refresh preserves surviving UUID selections and user-edited parameters. A new
user query clears selection and blocks selection actions while it is pending.
Requests use the existing Core queue and global shutdown barrier. Inspection opens
the canonical object, not a result-row copy. Events/journals show associations and
temporal claims; optional link metadata exposes its Link data; other Basic kinds
have a minimal read-only view. `open` resolves explicit UUID, session name, then
Basic name. `edit-arc` uses the same session precedence with an arc-only target.

SQLite version 3 migrates v2 by adding `basic.tags_json` with empty-list default.
The v1 migration still runs first when needed. Basic owns tags for all object
kinds; Arc header and authoring editors use comma-separated labels. Labels may
contain spaces but not commas or line breaks. Trim labels and collapse casefold
duplicates while preserving first spelling. No independent tag identity or link
is created. Existing aspect revisions, identities, and claims are preserved.

Core owns one session binding map cleared on startup. All assignments validate
before applying; conflicts return current/incoming UUIDs for explicit replacement.
Confirmation carries the observed old targets, which Core checks again. Session
names never rewrite Basic names or query substrings. Naming errors remain visible
in the naming dialog; late clipboard acknowledgments cannot override newer status.

Tk checks clipboard on focus and rereads it on adoption. Recognition does not
adopt or execute. Query JSON strictly validates supported fields/version; a UUID
array remains references. Reset replaces criteria; incorporation compares each
condition, with tags and all/any treated as one condition. Conflict decisions use
an input-generation token and apply together. Tk also checks the expected input
before realizing adopted parameters, preserving newer typing across the seam.
Clipboard failures and malformed/unsupported definitions leave input/results
intact. UUID copy uses displayed selected-row order, including singleton arrays.

Checks cover v1/v2 migration, real canonical searches, whole-tag all/any matches,
selection and input preservation, query supersession/close, Basic link inclusion,
session shadowing/rebinding/restart, stale incorporation, clipboard errors, and
native Tk interactions with temporary databases. Temporal predicates/range
payloads and the Welder remain deliberately absent pending their bounded designs.
