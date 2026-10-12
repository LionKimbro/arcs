# First slice

Tk presents one Command Center and on-demand detail windows. Core owns commands,
view drafts, and outstanding operations. Mem owns accepted records. Disk owns SQLite.
Use Today's thread-local Mobile Stacks and fatal-worker boundary.

Commands: create-arc; edit-arc UUID; list-arcs; help. Creation starts untitled,
with a generated name and unknown boundaries. UUIDs never change.

Basic and Arc aspects have separate UUID-keyed tables. Load once at startup.
Mem validates/stages; Disk commits; Mem accepts; Core distributes copied results.
Serialize mutations while a commit is outstanding. Conflicts preserve drafts.

Explicit Save; Reload discards a draft after confirmation. Closing asks before
discarding unsaved text. Submitted writes and their returns finish before workers
retire. Disk stops last and closes its connection on its own thread.

Temporal claims retain uncertainty and history; a changed boundary adds a claim.
Initial editor: year/month/date, UNKNOWN, and end-only ONGOING. No invented events.
