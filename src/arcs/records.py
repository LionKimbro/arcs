"""Arc records and a deliberately small ChronoMark boundary editor."""

from copy import deepcopy
from datetime import date, datetime, timezone
import re
from uuid import UUID, uuid4


def normalize_uuid(value):
    if not isinstance(value, str) or not re.fullmatch(
            r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
        raise ValueError("Use a standard hyphenated UUID.")
    return str(UUID(value))


def stamp():
    return datetime.now(timezone.utc).isoformat()


def create_arc(uuid):
    return {"uuid": uuid, "name": f"arc-{uuid[:8]}", "title": "Untitled arc",
            "description": "", "revision": 1,
            "temporal": {"format": "CHRONOMARK-MCCMc26", "version": "0.1",
                         "timezone": "America/Los_Angeles", "records": [
                             {"uuid": uuid, "type": "PERIOD", "registered-at": stamp(),
                              "what-happened": "Untitled arc", "temporal-claims": []}]}}


def get_effective_claim(record):
    period = record["temporal"]["records"][0]
    claims = period.get("temporal-claims", [])
    selected = period.get("working-temporal-claim")
    if selected:
        return next((claim for claim in claims if claim["uuid"] == selected), None)
    return claims[0] if len(claims) == 1 else None


def get_boundary_text(boundary):
    if boundary is None:
        return "UNKNOWN"
    if isinstance(boundary, str):
        return boundary
    if set(boundary) <= {"focus", "precision"} and "focus" in boundary:
        return boundary["focus"]
    # Preserve richer temporal content visibly; this subset editor cannot rewrite it.
    import json
    return json.dumps(boundary, ensure_ascii=False, sort_keys=True)


def get_editor_fields(record):
    claim = get_effective_claim(record) or {}
    return {"title": record["title"], "name": record["name"],
            "description": record["description"],
            "begin": get_boundary_text(claim.get("begin")),
            "end": get_boundary_text(claim.get("end"))}


def parse_boundary(text, side):
    text = text.strip()
    if text == "UNKNOWN" or (text == "ONGOING" and side == "end"):
        return text
    if re.fullmatch(r"\d{4}", text) and 1 <= int(text) <= 9999:
        return {"focus": text, "precision": "YEAR"}
    if re.fullmatch(r"\d{4}-\d{2}", text):
        date.fromisoformat(text + "-01")
        return {"focus": text, "precision": "MONTH"}
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        date.fromisoformat(text)
        return {"focus": text, "precision": "DAY"}
    raise ValueError(f"{side}: use YYYY, YYYY-MM, YYYY-MM-DD, UNKNOWN"
                     + (", or ONGOING." if side == "end" else "."))


def prepare_arc_update(record, fields):
    title = fields["title"].strip()
    name = fields["name"].strip()
    if not title:
        raise ValueError("Title cannot be empty.")
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError("Name permits lowercase letters, digits, and hyphens.")
    proposal = deepcopy(record)
    proposal.update(title=title, name=name, description=fields["description"],
                    revision=record["revision"] + 1)
    period = proposal["temporal"]["records"][0]
    period["what-happened"] = title
    original = get_editor_fields(record)
    if any(fields[side] != original[side] for side in ("begin", "end")):
        prior = get_effective_claim(record) or {}
        claim = {key: deepcopy(prior[key]) for key in ("begin", "end", "timezone") if key in prior}
        claim.update(uuid=str(uuid4()), **{"recorded-at": stamp()})
        claim.pop("id", None)
        for side in ("begin", "end"):
            if fields[side] != original[side]:
                claim[side] = parse_boundary(fields[side], side)
        period.setdefault("temporal-claims", []).append(claim)
        period["working-temporal-claim"] = claim["uuid"]
    return proposal


def validate_stored_arc(record):
    if normalize_uuid(record["uuid"]) != record["uuid"]:
        raise ValueError("Stored UUID is not normalized.")
    if not isinstance(record["revision"], int) or record["revision"] < 1:
        raise ValueError("Invalid stored revision.")
    temporal = record["temporal"]
    if temporal["format"] != "CHRONOMARK-MCCMc26" or temporal["version"] != "0.1":
        raise ValueError("Unsupported temporal format.")
    if not temporal.get("timezone"):
        raise ValueError("Missing temporal timezone.")
    period = temporal["records"][0]
    if len(temporal["records"]) != 1 or period["uuid"] != record["uuid"] or period["type"] != "PERIOD":
        raise ValueError("Invalid arc temporal identity.")
    prepare_arc_update(record, get_editor_fields(record))
