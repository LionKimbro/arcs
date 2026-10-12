# Event
Created: 2026-10-11
Modified: 2026-10-11

## Meaning and arc associations
Created: 2026-10-11
Modified: 2026-10-11

An event has a moment in time and describes what happened. It is distinct from a [journal entry](journal-entry.md). Events are usually associated with one [arc](arc.md), but can be associated with multiple arcs. An event can occur within an arc without changing its defining character, and it can also mark an arc's beginning or endpoint.

Lion favors keeping much of the event record in Basic, including identity and descriptive content, with arc associations expressed through links. The simplified Basic `type` is `event`, mapping to formal M1 Basic typehint if needed; Basic's `date` permits a simple associated date. Richer temporal information still needs a suitable mapping; a separate event table is not inherently required.

## Job-search example
Created: 2026-10-11
Modified: 2026-10-11

Applying for a job and receiving an invitation to interview are separate events within a job-search arc. Getting hired is an event that ends the job-search arc: the condition defining that arc has ceased. A fundamental change is represented by an arc ending and another beginning, rather than an internal shift of the same arc.
