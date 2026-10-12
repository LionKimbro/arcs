# Journal entry
Created: 2026-10-11
Modified: 2026-10-11

## Meaning and arc associations
Created: 2026-10-11
Modified: 2026-10-11

A journal entry is a kind of record distinct from an [event](event.md). It is typically within, or associated with, one [arc](arc.md), though it may be associated with multiple arcs. Lion has not yet specified its fields or the precise distinction in content and interface behavior between journal entries and events; do not assume that a journal entry marks an arc boundary.

Lion favors keeping much of the journal entry record in Basic, including identity and its prose in the description field, with arc associations expressed through links. The simplified Basic `type` is `journal-entry`, mapping to formal M1 Basic typehint if needed; Basic's `date` permits a simple associated date. Richer temporal information still needs a suitable mapping; a separate journal-entry table is not inherently required.
