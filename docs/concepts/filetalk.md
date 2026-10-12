# FileTalk
Created: 2026-10-11
Modified: 2026-10-11

## Purpose
Created: 2026-10-11
Modified: 2026-10-11

FileTalk is a philosophy of inspectable, composable programs cooperating through plain files, commonly JSON. It favors small replaceable participants and visible communication. Patchboard is a routing architecture associated with FileTalk; it is not required for every FileTalk system. The repository is `F:\repo\filetalk`.

## Core message
Created: 2026-10-11
Modified: 2026-10-11

Core v1 requires a JSON object with `channel`, `signal`, and `timestamp`. The channel is an opaque routing identifier; all semantic meaning belongs in the signal, which may be any JSON value. The timestamp is Unix seconds encoded as a string, optionally fractional. Core is transport-agnostic and does not promise delivery or ordering, or define routing.

## Basic file transport
Created: 2026-10-11
Modified: 2026-10-11

The file transport profile represents each message as one UTF-8 JSON file with a filename unique within its directory. By convention, a participant writes outgoing messages to OUTBOX and polls INCOMING for incoming messages. Others can write to its INCOMING or read and remove files from its OUTBOX.

Files may be visible while being written. A consumer treats parse failures as incomplete writes and retries later; the profile discourages temporary-file publication through atomic rename. Once fully processed, a message must leave the directory through deletion or archival. Timestamp ordering is advisory, and routing, acknowledgments, reliability, deduplication, and consumer coordination are outside the profile.

## Sources and relevance to Arcs
Created: 2026-10-11
Modified: 2026-10-11

The manifesto, core JSON specification, and file transport JSON specification are preserved in [the filesystem location registry](../../db/file-system-locations.json), together with Markdown companion paths for the specifications. No FileTalk entry was found in the supplied Librarian2 registry; these references were located through the FileTalk repository README. Although the filenames and JSON document IDs use `patchboard`, the core Markdown describes FileTalk Core v1 and the transport JSON names the FileTalk File Transport Profile v1. The core Markdown designates JSON as authoritative.

Lion explicitly identifies FileTalk as how his programs communicate with one another, including Focus, Arcs, Today, and the Project Browser to come. This establishes FileTalk as the communication mechanism for the [use case](use-cases.md) of instructing Today to navigate to a day. Application command schemas, channel wiring, and endpoint locations remain to be specified.
