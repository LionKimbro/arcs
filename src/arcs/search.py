"""Basic query values, clipboard contracts, and session-name validation."""

from copy import deepcopy
import json

from . import records


def empty_criteria():
    return {"type": None, "name-contains": "", "title-contains": "", "tags": [], "tag-match": "all"}


def normalize_tags(labels):
    if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
        raise ValueError("Tags must be a list of labels.")
    result, seen = [], set()
    for label in labels:
        label = label.strip()
        if not label or any(char in label for char in ",\r\n"):
            raise ValueError("Each tag must be nonempty and contain no commas or line breaks.")
        if label.casefold() not in seen:
            result.append(label)
            seen.add(label.casefold())
    return result


def parse_tags(value):
    if not isinstance(value, str):
        raise ValueError("Enter tags separated by commas.")
    return normalize_tags([part for part in value.split(",") if part.strip()])


def validate_criteria(value):
    if not isinstance(value, dict):
        raise ValueError("Search criteria must be a JSON object.")
    unsupported = value.keys() - empty_criteria().keys()
    if unsupported:
        raise ValueError("Unsupported search criteria: " + ", ".join(sorted(str(key) for key in unsupported)))
    criteria = {**empty_criteria(), **deepcopy(value)}
    if criteria["type"] is not None and (not isinstance(criteria["type"], str) or not criteria["type"].strip()):
        raise ValueError("Search type must be an object kind or null.")
    if any(not isinstance(criteria[key], str) for key in ("name-contains", "title-contains")):
        raise ValueError("Name and title filters must be text.")
    if criteria["tag-match"] not in ("all", "any"):
        raise ValueError("Tag matching must be all or any.")
    criteria["tags"] = normalize_tags(criteria["tags"])
    return criteria


def find_results(criteria, objects):
    criteria = validate_criteria(criteria)
    rows = []
    wanted = {label.casefold() for label in criteria["tags"]}
    for record in objects.values():
        if criteria["type"] is not None and record["type"] != criteria["type"]:
            continue
        if any(criteria[key + "-contains"].casefold() not in record[key].casefold() for key in ("name", "title")):
            continue
        tags = {label.casefold() for label in record.get("tags", [])}
        if wanted and not (wanted <= tags if criteria["tag-match"] == "all" else wanted & tags):
            continue
        rows.append({key: deepcopy(record.get(key, [] if key == "tags" else ""))
                     for key in ("uuid", "name", "title", "type", "tags", "date")})
    return sorted(rows, key=lambda row: (row["title"].casefold(), row["name"].casefold(), row["uuid"]))


def get_object_kinds(objects):
    return sorted({"arc", "event", "journal-entry", "link"} | {record["type"] for record in objects.values()})


def classify_clipboard(text):
    if not text.lstrip().startswith(("{", "[")):
        return {"kind": "ordinary"}
    try:
        value = json.loads(text)
    except (ValueError, TypeError) as error:
        raise ValueError("Clipboard JSON is malformed.") from error
    if isinstance(value, list):
        if not value:
            return {"kind": "ordinary"}
        try:
            ids = [records.normalize_uuid(item) for item in value]
        except ValueError as error:
            raise ValueError("Clipboard reference lists must contain full UUID strings.") from error
        return {"kind": "references", "uuids": ids}
    if not isinstance(value, dict) or value.get("format") != "arcs-basic-search":
        return {"kind": "ordinary"}
    if type(value.get("version")) is not int or value["version"] != 1:
        raise ValueError("Unsupported clipboard search version.")
    if "criteria" not in value:
        raise ValueError("Clipboard search is missing its criteria.")
    unsupported = value.keys() - {"format", "version", "criteria"}
    if unsupported:
        raise ValueError("Unsupported clipboard search fields: " + ", ".join(sorted(unsupported)))
    return {"kind": "search", "criteria": validate_criteria(value["criteria"])}


def serialize_search(criteria):
    return json.dumps({"format": "arcs-basic-search", "version": 1,
                       "criteria": validate_criteria(criteria)}, ensure_ascii=False)


def get_incorporation(current, incoming):
    current, incoming = validate_criteria(current), validate_criteria(incoming)
    combined, conflicts = deepcopy(current), []
    for key in ("type", "name-contains", "title-contains", "tags"):
        left, right = current[key], incoming[key]
        if not right:
            continue
        if key == "tags":
            left = (frozenset(t.casefold() for t in left), current["tag-match"]) if left else None
            right = (frozenset(t.casefold() for t in right), incoming["tag-match"])
        elif key in ("name-contains", "title-contains"):
            left, right = left.casefold(), right.casefold()
        if not left:
            combined[key] = deepcopy(incoming[key])
            if key == "tags":
                combined["tag-match"] = incoming["tag-match"]
        elif left != right:
            conflicts.append({"field": key, "current": deepcopy(current[key]), "incoming": deepcopy(incoming[key]),
                              "current-mode": current["tag-match"], "incoming-mode": incoming["tag-match"]})
    return {"criteria": combined, "conflicts": conflicts, "incoming": incoming}


def validate_session_name(value):
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise ValueError("Session names must be nonempty and contain no whitespace.")
    try:
        records.normalize_uuid(value)
    except ValueError:
        return value
    raise ValueError("A session name cannot have full UUID syntax.")
