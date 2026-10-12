# Arc
Created: 2026-10-11
Modified: 2026-10-11

## Meaning and examples
Created: 2026-10-11
Modified: 2026-10-11

An arc is a passage of life or history with a beginning, an end, and relationships to other arcs. It can be part of a larger arc. Earlier notes describe arcs as meaningful passages through lived time, including concurrent and overlapping passages.

Lion's examples include childhood, K through fifth grade, a distinctive sixth grade, junior high, high school, college, employment at Pokémon, his general career history, a recent three-year unemployment period, a year working for Robert Kelly, and his present passage. His employment arcs belong to his larger career-history arc, which does not extend into childhood.

Examples also include the Renaissance, Enlightenment, Middle Ages, Dark Ages, the life of Jesus Christ, and Lion's whole life. An arc is therefore not limited to a task, project, short duration, or present activity.

## Story to oneself
Created: 2026-10-11
Modified: 2026-10-11

Lion describes an arc as also representing his story to himself about who he is and what he is doing. An arc therefore carries a personal interpretation of a passage, alongside its events, boundaries, and relationships. This adds identity and self-understanding to the orientation Arcs provides. How that story is expressed or revisited in the system remains to be explored; no particular field or interface is implied yet.

## Identity and relationships
Created: 2026-10-11
Modified: 2026-10-11

Arcs will be [M1](m1.md) objects conceptually: each arc has a stable UUID, and its information and relationships can be mapped to M1 aspects and link entities. Internal records need not use an aspect-shaped schema or native M1 storage. Relationships include dependency, “this arc transitions to that arc,” and “this arc contains these sub-arcs.” Exact mapping aspects and link-type identifiers remain to be specified.

An arc can belong to multiple larger arcs. Containment therefore must support multiple parents rather than require a single-parent tree.

Lion specifies that creating a transition also creates a new successor arc and a separate M1-conforming link object between the predecessor and successor. The link has its own stable UUID, with a Link Aspect whose `from` is the predecessor UUID and `to` is the successor UUID. This relationship object is distinct from the event that establishes the transition. See [the adopted authoring design](../design/arc-authoring.md).

## Character, events, and endings
Created: 2026-10-11
Modified: 2026-10-11

The current working model is that arcs do not shift internally. An arc retains its defining character while [events](event.md) happen within it. A change in that defining character means one arc ends and another begins. Lion initially qualified this with “I think,” then explained the distinction through the example below.

While looking for work, applying for a job is an event, and receiving an invitation to interview is another event. Neither ends the job-search arc. Getting hired ends that arc because Lion is no longer looking for work. An arc's end is the cessation of that passage, whether through fulfillment, exhaustion, or another cause.

An event can mark an arc's beginning or endpoint. [Journal entries](journal-entry.md) are usually associated with one arc, but may be associated with several. Events similarly are usually associated with one arc and may be associated with several.

## Boundaries still to clarify
Created: 2026-10-11
Modified: 2026-10-11

Lion has designated [ChronoMark](chronomark.md) (`F:\repo\chronomark`) for handling uncertain times and related temporal representation. Its location is recorded in [the filesystem location registry](../../db/file-system-locations.json); a brief conceptual review is recorded in its concept note, with detailed integration review deferred. How Arcs uses it for ongoing arcs, boundaries, and retrospective interpretation remains to be discussed. Whether every beginning and ending must be represented by an explicit event also remains open.
