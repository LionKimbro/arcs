# First implementation

This records the original slice. Schema and authoring extensions are documented
in [authoring.md](authoring.md); they preserve the worker/continuation architecture.

`main` resolves configuration, installs queues/runtimes, builds Command Center,
starts Disk/Mem/Core in that order, and joins Core/Mem before stopping Disk.
`machine` and `mobile_stacks` adapt Today's current permanent-worker mechanisms:
thread-local runtime, exclusive active stack, transfer before queue publication,
runtime-owned frame removal, and an idempotent fatal latch.

`core` interprets `cmdparts` output through current-event registers. One Core
worker owns independent view records/drafts and serializes domain requests. Load
uses Disk → Mem → Core; mutations use Mem → Disk → Mem → Core. No acceptance or
saved output precedes SQLite commit. A closed origin does not cancel its write.
Relevant view reducers receive independent accepted-record copies.

`mem` owns canonical records and validates/stages mutations. `disk` opens and
closes SQLite on its own worker. Schema version 1 maps Basic fields to `basic`
and Arc-specific revision/temporal content to `arc`, keyed by object UUID.
Transactions acquire a write lock before checking the stored revision. The whole
arc set loads once; corrupt or unknown databases fail, never become empty stores.

`records` preserves PERIOD/claim UUIDs, explicit timezone, granularity, unknown
and ongoing states, and prior claims. The initial PERIOD UUID equals the arc UUID.
Registration timestamps are UTC record history. The editor's limited boundary
syntax does not round uncertainty into an exact instant or select among competing
claims. A new temporal assertion does not inherit an old claim's confidence or
provenance. Full ChronoMark runtime integration remains future work.

`tk` captures input and realizes semantic commands. No Tk callback accesses SQLite
or performs domain validation. Refresh commands carry expected editor fields so
newer typing survives the queue/wake seam. Closing discards only confirmed drafts;
submitted operations drain before Core and Mem retire. Tk waits for Core's final
wake call to return before destruction. Fatal closure similarly leaves Tcl alive
until workers exit. No worker joins occur in Tk callbacks.

Validation is split between ordinary worker tests and real-Tk fresh processes.
There is no hung-worker watchdog or emergency-save path. There is no multi-process
write protocol. Later aspects get their own tables; this slice does not invent
schemas for future events, journal entries, links, or resources.
