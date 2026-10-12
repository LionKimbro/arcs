# Creating and opening arcs
Created: 2026-10-11
Modified: 2026-10-11

## Adopted workflow
Created: 2026-10-11
Modified: 2026-10-11

Command Center can create an independent arc when the database is empty and again when arcs already exist. Creation does not require a predecessor, parent, journal entry, or event. Successful creation opens an Arc Detail View for the created arc. Repeating creation produces separate UUIDs and allows three arcs' detail windows to remain open at once.

Exactly one Command Center opens at startup. Arc Detail windows appear only when the user requests creation or opening, through typed commands or optional buttons. Three simultaneously open detail windows describe the result of three user actions in an acceptance scenario, not a startup arrangement. Existing-arc opening can produce multiple views of the same UUID as well.

The first implementation must expose creation through typed commands. Buttons can invoke the same semantic operations but cannot be the only usable route. Exact command syntax is still open; [Command Center](command-center.md) records the required operation vocabulary without prescribing a parser.

## Creation data
Created: 2026-10-11
Modified: 2026-10-11

Core initiates a request using an automatically generated stable UUID; assign it once and carry it through Mem and Disk rather than generating a replacement in each layer. The exact UUID-producing function/module is a routine implementation choice within the ownership sketch. Domain validation belongs in the application/Mem path, not a Tk callback.

Provide title, name, narrative description, and temporal boundary information as far as known. The smallest typed creation command can accept a title and allow the other information to be completed in the detail view; exact required fields and name suggestion rules remain to be agreed. Unknown start time is valid conceptual information. Whether an unspecified end defaults to ongoing should be explicit in the creation interaction; do not mistake omission for a known historical fact.

The creation timestamp, if stored, means the record was created now. It is distinct from the arc's life-time beginning. Historical arcs are legitimate, including completed ones. A creation command should not require an event to manufacture either boundary.

## Completion and failures
Created: 2026-10-11
Modified: 2026-10-11

The operation carries a request identity distinct from arc and view identities. Mem returns created-record information to Core, which offers it to reducers and opens the requested view. Report the UUID in Command Center so the record can be reopened unambiguously. Distinguish any provisional in-memory acceptance from completed SQLite persistence; the precise acknowledgment protocol is covered as an open gate in [data and persistence](data-and-persistence.md).

Invalid command input is reported in Command Center and creates no partial record. Unknown UUID lookup is an ordinary not-found result. Storage failure must not be reported as successful creation. A close request arriving during creation must honor the operation's defined save completion and the producer-before-consumer shutdown order.

## Reopening
Created: 2026-10-11
Modified: 2026-10-11

Provide a way to list existing arcs and open one by UUID. Names and titles can be shown for recognition, but do not infer unique identity from them. Closing a detail window and opening its arc again retrieves the same object. After full application restart, listing and reopening returns the same three UUIDs and their persisted fields.
