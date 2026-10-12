# Startup and shutdown
Created: 2026-10-11
Modified: 2026-10-11

## Adopted lifetime and reference
Created: 2026-10-11
Modified: 2026-10-11

Command Center controls the application's lifetime. While it remains open, closing Arc Detail windows does not stop the system. Closing Command Center requests orderly application shutdown and closes every remaining window. The reference is Today's actual implementation in `F:\repo\today\src\today`, inspected on October 11, not only its historical architecture sketches.

There is exactly one Command Center, created at startup. Arc Detail windows are opened only in response to user creation/opening actions during the session. The create-three-arcs scenario is user-driven and is not an instruction to bootstrap sample arcs or windows.

There is one Tk presentation machine on the main thread and one dedicated worker thread each for Core, Mem, and Disk. Each worker has one installed machine runtime and inbox. Several window reducers execute within the single Core machine, not separate threads. Initial Arcs does not require Today's dynamic image machines.

## Observed Today startup
Created: 2026-10-11
Modified: 2026-10-11

Today's `main.main` resolves its data root before building Tk or starting workers, initializes the machine registry, creates four queues, installs permanent runtimes and handlers, and connects Tk's outgoing events and incoming command queue. It builds its root window, starts **Disk, then Mem, then Core**, enters Tk's main loop, and performs final joins after that loop returns. Core initializes its own state and enqueues START in its reducer loop. Mem initializes its store in its worker.

Worker startup is not a guarantee that initialization has completed. Queued requests can wait for receivers, but application readiness, including SQLite open/schema/load completion, needs a defined Core-visible result. Show startup state or restrict commands requiring data until that result; do not report ready just because Thread.start returned. Database failure must produce a failed startup, not an empty successful session.

## Adopted startup structure for Arcs
Created: 2026-10-11
Modified: 2026-10-11

Resolve the configured database location, initialize queues and machine registrations, wire Tk/Core communication, build Command Center, start Disk/Mem/Core in the reference order, and enter the single Tk main loop. Disk opens SQLite on its worker and supplies any startup storage results through the agreed continuations. Mem initializes its Arcs-specific canonical store. Core starts its Command Center reducer and coordinates readiness and requests to open additional views. Exact handlers and bootstrap stack sequence belong in a small lifecycle sketch after the persistence protocol is chosen.

## Scheduling and wake behavior observed in Today
Created: 2026-10-11
Modified: 2026-10-11

Core normally blocks on its inbox, translates one item to reducer events, processes local events/effects until quiet, then blocks again. Disk blocks on its inbox. Mem blocks with a timeout only when a pending write deadline requires it. Today schedules day-bundle writes for one second after the latest change using monotonic time; it flushes due writes after handling an inbox item or after timeout. That deadline is a Today persistence choice, not a necessary Arcs cadence.

Core-to-Tk queues a semantic command before signaling `<<CoreMailAvailable>>`. Tk drains queued commands on that wake. Tk independently checks the fatal worker latch every 50 milliseconds, so it can close even if Core has failed. Today's one-second text debounce, image timers, and tab/scroll timers are product behavior, not generic machine-loop requirements. Arcs does not poll Mem once a second to synchronize its windows.

## Observed Today normal shutdown
Created: 2026-10-11
Modified: 2026-10-11

Today's Tk close hook submits pending input/debounce work before SHUTDOWN and leaves Tk alive. Core requests shutdown, forces dirty snapshots toward Mem, and remains active until the latest dirty work is accepted. It then retires Core, sends Mem its sentinel, and sends SHUTDOWN_COMPLETE to Tk. Mem force-publishes pending day writes to Disk before retiring. Tk destroys the root when permitted; destruction ends its main loop.

Main's `finish_worker_shutdown` closes dynamic creation, joins Core, joins remaining dynamic workers, joins Mem, then queues Disk's sentinel, joins Disk, and reaps exited runtimes on the main thread. Because Disk's producers have stopped before its sentinel is added, queued writes precede that sentinel. SHUTDOWN_COMPLETE is permission to close Tk, not itself proof of durable persistence; final joins complete the exit path.

## Required Arcs close behavior and SQLite adaptation
Created: 2026-10-11
Modified: 2026-10-11

A Command Center close request is idempotent. Stop admitting new user operations, capture any input that the selected editor/save policy promises to preserve, and keep Tk's event loop responsive while Core coordinates outstanding required saves. Do not immediately destroy the root, join workers in a Tk callback, or stop Disk while another worker can still publish writes.

Track submitted create/save operations and any selected draft-save obligations. Complete their required SQLite transactions and return-path processing while Mem and Core still exist. If a commit or revision conflict prevents an orderly saved exit, it must not be mislabeled successful. The exact draft choice and failure UI are open, but ordinary close cannot silently abandon work that was already reported saved.

Once the selected completion barrier is met, retire Core and Mem in producer order, permit Tk to destroy all windows, and let main perform joins. Stop Disk only after its producers have stopped; close the SQLite connection on Disk's thread as that worker exits, then join/reap. If the eventual save design uses return continuations after Disk commits, do not copy Today's early Core/Mem retirement before those returns have been handled. Today's fire-and-forget final JSON writes do not establish that SQLite acknowledgment returns can be dropped.

An individual Arc Detail close is a view-close event, subject to its draft policy. It does not delete the arc or initiate global shutdown. Pending domain results still reach the remaining reducers even if their requesting view has closed; presentation commands for removed views must not touch destroyed widgets.

## Unexpected worker death
Created: 2026-10-11
Modified: 2026-10-11

Follow Today's failure boundary: uncaught BaseException or unexplained return of a still-running worker is fatal. The wrapper prints a traceback, sets an idempotent shared fatal latch, wakes worker inboxes, and marks runtime exit in cleanup. Ordinary routing and reducer work stop. Tk's independent main-thread check closes the UI even if Core is the failed worker. Main joins and reaps, with a nonzero process exit.

Expected validation/not-found/conflict results belong in ordinary application replies, not the fatal path. Unexpected infrastructure failure must not leave other machines pretending the application is healthy. Fatal shutdown does not promise normal flush, retry, recovery, or emergency saves. Disk cleanup must not accidentally commit incomplete work while reporting failure. Already committed SQLite data is different from pending in-memory work; no stronger power-loss guarantee is implied.

Today's cooperative shutdown has no watchdog or forced interruption of a hung handler; joins have no application timeout. Do not silently introduce a new recovery architecture or claim that the reference handles hangs. Raise such a requirement if it becomes necessary.
