"""Basic-centered records, temporal claims, and independently identified links."""

from copy import deepcopy
from datetime import datetime, timezone
import re
from uuid import uuid4

from . import records, search

LINK_TYPES = {name: f"tag:m1lattice.net,2026:/linktype/{name}"
              for name in ("transition", "via", "member-of", "parent-child")}


def create_draft(kind, arc):
    return {"uuid": str(uuid4()), "kind": kind, "arc": arc["uuid"], "base": arc["revision"],
            "successor": str(uuid4()) if kind == "transition" else None,
            "fields": {"title": "", "description": "", "when": "UNKNOWN", "earliest": "",
                       "latest": "", "notes": "", "tags": "", "successor-title": "",
                       "successor-name": "", "successor-description": "", "successor-tags": ""}}


def parse_occurrence(value):
    value = value.strip()
    if value in ("", "UNKNOWN"):
        return None
    if "T" not in value:
        return records.parse_boundary(value, "event")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})", value):
        raise ValueError("Time of day requires an ISO timestamp with an offset or Z.")
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    fraction = re.search(r"\.(\d+)", value)
    precision = ("MICROSECOND" if fraction and len(fraction[1]) > 3 else "MILLISECOND" if fraction
                 else "SECOND" if value[16:17] == ":" else "MINUTE")
    return {"focus": value, "precision": precision}


def get_time_key(value):
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    # Calendar ordering retains its expressed granularity; it does not assert an instant.
    return value


def prepare_temporal_claim(fields):
    point = {}
    precision = None
    for source, target in (("when", "focus"), ("earliest", "earliest"), ("latest", "latest")):
        parsed = parse_occurrence(fields[source])
        if parsed:
            point[target] = parsed["focus"]
            precision = precision or parsed["precision"]
    if point:
        point["precision"] = precision
    # Comparable values of equal granularity must form a coherent range.
    for left, right in (("earliest", "latest"), ("earliest", "focus"), ("focus", "latest")):
        if left in point and right in point:
            a, b = point[left], point[right]
            if len(a) == len(b) and get_time_key(a) > get_time_key(b):
                raise ValueError(f"Occurrence {left} must not be later than {right}.")
    claim = {"uuid": str(uuid4()), "recorded-at": records.stamp()}
    if point:
        claim["event"] = point
    if fields["notes"].strip():
        claim["claim-notes"] = fields["notes"].strip()
    return claim if point or "claim-notes" in claim else None


def create_record(draft):
    fields = draft["fields"]
    description = fields["description"]
    if not description.strip():
        raise ValueError("Write the journal entry or describe what happened before saving.")
    claim = prepare_temporal_claim(fields)
    kind = "event" if draft["kind"] == "transition" else draft["kind"]
    return {"uuid": draft["uuid"], "type": kind, "name": f"{kind}-{draft['uuid'][:8]}",
            "title": fields["title"].strip(), "description": description,
            "tags": search.parse_tags(fields.get("tags", "")),
            "date": (claim or {}).get("event", {}).get("focus", ""), "revision": 1,
            "temporal": {"format": "CHRONOMARK-MCCMc26", "version": "0.1",
                         "timezone": "America/Los_Angeles", "records": [
                             {"uuid": draft["uuid"], "type": "EVENT", "registered-at": records.stamp(),
                              "temporal-claims": [claim] if claim else []}]}}


def create_link(source, destination):
    return {"uuid": str(uuid4()), "from": source, "to": destination,
            "type": "member-of", "revision": 1}


def validate_links(bundle, existing):
    objects = {**existing["objects"], **{r["uuid"]: r for r in bundle["objects"]}}
    links = {**existing["links"], **{r["uuid"]: r for r in bundle["links"]}}
    for uuid in objects.keys() & links.keys():
        if objects[uuid]["type"] != "link":
            raise ValueError("A Basic object and unrelated link cannot share an identity.")
    for link in bundle["links"]:
        for key in ("uuid", "from", "to"):
            if records.normalize_uuid(link[key]) != link[key]:
                raise ValueError("Link UUIDs must be normalized.")
        if not isinstance(link["type"], str) or not link["type"].strip() or link["revision"] < 1:
            raise ValueError("A link needs a nonempty type and positive revision.")
        if link["from"] not in objects and link["from"] not in links:
            raise ValueError("Link source does not exist.")
        if link["to"] not in objects and link["to"] not in links:
            raise ValueError("Link destination does not exist.")
        source, target = objects.get(link["from"]), objects.get(link["to"])
        if link["type"] == "member-of" and (not source or source["type"] not in ("event", "journal-entry")
                                             or not target or target["type"] != "arc"):
            raise ValueError("member-of must point from an entry/event to an arc.")
        if link["type"] in ("transition", "parent-child") and (
                not source or not target or source["type"] != "arc" or target["type"] != "arc"):
            raise ValueError("Arc relationships must connect two arcs.")
        if link["type"] == "via" and (link["from"] not in links
                                      or links[link["from"]]["type"] != "transition"
                                      or not target or target["type"] != "event"):
            raise ValueError("via must point from a transition link to an event.")


def prepare_bundle(draft, store):
    predecessor = store["objects"].get(draft["arc"])
    if not predecessor or predecessor["type"] != "arc":
        raise ValueError("The associated arc no longer exists.")
    event = create_record(draft)
    bundle = {"objects": [event], "links": [create_link(event["uuid"], predecessor["uuid"])],
              "bases": {event["uuid"]: None}, "affected": [predecessor["uuid"]],
              "selected": event["uuid"]}
    if draft["kind"] == "transition":
        if predecessor["revision"] != draft["base"]:
            raise ValueError("The predecessor changed. Refresh predecessor before retrying; draft retained.")
        end = (records.get_effective_claim(predecessor) or {}).get("end")
        period = predecessor["temporal"]["records"][0]
        if (end not in (None, "UNKNOWN", "ONGOING") or predecessor.get("end-event")
                or (period.get("temporal-claims") and records.get_effective_claim(predecessor) is None)
                or any(link["type"] == "transition" and link["from"] == predecessor["uuid"]
                       for link in store["links"].values())):
            raise ValueError("This arc already has an ending or unresolved boundary claims; transition was not saved.")
        fields = draft["fields"]
        successor = records.create_arc(draft["successor"])
        successor = records.prepare_arc_update(successor, {
            **records.get_editor_fields(successor), "title": fields["successor-title"],
            "name": fields["successor-name"].strip() or successor["name"],
            "description": fields["successor-description"], "tags": fields.get("successor-tags", "")})
        successor["revision"] = 1
        previous = deepcopy(predecessor)
        previous["revision"] += 1
        occurrence = (records.get_effective_claim(event) or {}).get("event", "UNKNOWN")
        for arc, side in ((previous, "end"), (successor, "begin")):
            prior = records.get_effective_claim(arc) or {}
            claim = {key: deepcopy(prior[key]) for key in ("begin", "end", "timezone") if key in prior}
            claim.update(uuid=str(uuid4()), **{"recorded-at": records.stamp(), side: deepcopy(occurrence)})
            if arc is successor:
                claim["end"] = "ONGOING"
            arc["temporal"]["records"][0].setdefault("temporal-claims", []).append(claim)
            arc["temporal"]["records"][0]["working-temporal-claim"] = claim["uuid"]
            arc[side + "-event"] = event["uuid"]
        transition = create_link(previous["uuid"], successor["uuid"])
        transition["type"] = "transition"
        via = create_link(transition["uuid"], event["uuid"])
        via["type"] = "via"
        bundle["objects"].extend((successor, previous))
        bundle["links"].extend((transition, via, create_link(event["uuid"], successor["uuid"])))
        bundle["bases"].update({successor["uuid"]: None, previous["uuid"]: predecessor["revision"]})
        bundle["affected"].append(successor["uuid"])
    validate_links(bundle, store)
    return bundle


def get_chronology(arc_id, store):
    ids = {link["from"] for link in store["links"].values()
           if link["type"] == "member-of" and link["to"] == arc_id}
    items = []
    for uuid in ids:
        record = deepcopy(store["objects"][uuid])
        point = (records.get_effective_claim(record) or {}).get("event", {})
        focus = point.get("focus") or point.get("latest") or point.get("earliest")
        record["time-label"] = records.get_boundary_text(point) if point else "Time unknown"
        record["sort-time"] = get_time_key(focus) if focus else ""
        record["successor"] = next((store["links"][via["from"]]["to"] for via in store["links"].values()
                                   if via["type"] == "via" and via["to"] == uuid), None)
        items.append(record)
    # UUIDs stabilize equal/unknown claims, never registration timestamps.
    items.sort(key=lambda item: item["uuid"])
    items.sort(key=lambda item: item["sort-time"], reverse=True)
    return items
