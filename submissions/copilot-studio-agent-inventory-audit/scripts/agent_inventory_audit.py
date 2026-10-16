#!/usr/bin/env python3
"""Audit a Power Platform agent inventory export for governance posture.

Usage:
    python3 agent_inventory_audit.py INVENTORY [INVENTORY ...]
        [--md report.md] [--json report.json]
        [--environments FILE] [--users FILE] [--departing ID_OR_UPN,...]
        [--environment NAME_OR_ID] [--agent NAME_OR_ID] [--owner NAME_OR_ID_OR_UPN]
        [--brief] [--draft-days 90] [--stale-days 365] [--owner-threshold 15]
        [--editor-threshold 5] [--as-of YYYY-MM-DD]
        [--allowed-regions REGION,...] [--watch-connectors ID,...]
        [--max-rows 25]

INVENTORY is an export of the Power Platform inventory that contains
Copilot Studio agents (resource type microsoft.copilotstudio/agents):

  * JSON from the Power Platform inventory API or `pac resource-query`
    (an object with a `data` array), or from Azure Resource Graph (a list of
    records, an object with `data`, a columns/rows table, or newline-delimited
    JSON; `properties` may be a JSON string), or
  * CSV downloaded from the Power Platform admin center inventory pages or
    from an Azure Resource Graph query.

Environment records (microsoft.powerplatform/environments) found in the same
export, or supplied with --environments, are joined by environment ID. A user
list (--users, CSV or JSON with object IDs, UPNs, display names, and account
state) resolves owner names and marks disabled accounts.

Standard library only. No network access. Nothing is changed anywhere: the
script reads the export and writes a report.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone

TOOL_VERSION = "1.2.0"
AGENT_TYPE = "microsoft.copilotstudio/agents"
ENV_TYPE = "microsoft.powerplatform/environments"

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
CAP_LIMIT = 200  # the inventory lists at most 200 resources of each type per agent
LIST_CAP = 5     # items shown inline before "and N more"

# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------


def norm_key(key):
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == "" or value.strip().lower() in ("null", "none", "n/a", "-", "–", "—")
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def value_blank(value):
    """True for empty normalized values, including share dicts with no counts and empty count dicts."""
    if isinstance(value, dict):
        return all(v is None for v in value.values())
    return is_blank(value)


def field_blank(field, value):
    """value_blank, except that the normalized authentication value "None" (no user authentication) is a real value."""
    if field == "authentication":
        return value is None
    return value_blank(value)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("true", "yes", "y", "1", "enabled", "on"):
        return True
    if text in ("false", "no", "n", "0", "disabled", "off"):
        return False
    return None


_DT_FORMATS = (
    "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d",
    "%d %b %Y %H:%M", "%d %b %Y", "%b %d, %Y %I:%M %p", "%b %d, %Y", "%B %d, %Y",
    # Day-first forms are tried last; an ambiguous 01/03/2026 is read as January 3.
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y",
)


def parse_dt(value):
    """Return an aware UTC datetime, or None. Naive values are taken as UTC."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        seconds = value / 1000.0 if abs(value) >= 1e11 else value  # epoch milliseconds or seconds
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if is_blank(text):
        return None
    if re.fullmatch(r"\d{10,13}", text):
        return parse_dt(int(text))
    iso = text.replace(" UTC", "").replace("Z", "+00:00").replace("z", "+00:00")
    iso = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], iso, count=1)
    iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", iso)
    try:
        parsed = datetime.fromisoformat(iso)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def fmt_dt(value):
    if not value:
        return ""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d")


def days_between(later, earlier):
    """Calendar days between two aware datetimes, so a 10:00 publish and a midnight reference date count whole days."""
    return (later.astimezone(timezone.utc).date() - earlier.astimezone(timezone.utc).date()).days


def maybe_json(value):
    """Parse a JSON-looking string; return the original value otherwise."""
    if isinstance(value, str):
        text = value.strip()
        if text[:1] in ("{", "[") and text[-1:] in ("}", "]"):
            try:
                return json.loads(text)
            except ValueError:
                return value
    return value


def dedupe(items):
    seen = OrderedDict()
    for item in items:
        if item not in seen:
            seen[item] = True
    return list(seen.keys())


def dedupe_ci(items):
    """Case-insensitive dedupe that keeps the first spelling seen."""
    seen = OrderedDict()
    for item in items:
        key = item.lower()
        if key not in seen:
            seen[key] = item
    return list(seen.values())


def parse_list(value):
    value = maybe_json(value)
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("displayName") or item.get("name") or item.get("channel") or item.get("id")
                if not is_blank(name):
                    out.append(str(name).strip())
            elif not is_blank(item):
                out.append(str(item).strip())
        return dedupe_ci(out)
    if isinstance(value, dict):
        return dedupe_ci([str(k) for k, v in value.items() if parse_bool(v) is not False])
    text = str(value).strip()
    if is_blank(text):
        return []
    return dedupe_ci([p.strip().strip('"\'') for p in re.split(r"[;,|\n]+", text) if p.strip()])


def parse_int(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return None


def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def plural(count, noun, plural_noun=None):
    if count == 1:
        return "1 " + noun
    return "%d %s" % (count, plural_noun or noun + "s")


def capped(items, cap=LIST_CAP, sep=", "):
    items = list(items)
    if len(items) <= cap:
        return sep.join(items)
    return sep.join(items[:cap]) + " and %d more" % (len(items) - cap)


def short_id(value):
    value = str(value or "")
    return value[-8:] if len(value) > 8 else value


# --------------------------------------------------------------------------
# Loading exports
# --------------------------------------------------------------------------

CONTAINER_KEYS = ("data", "value", "Data", "Resources", "resources", "records", "items", "rows", "results", "Results")


def table_records(container):
    cols = [c.get("name") if isinstance(c, dict) else str(c) for c in container["columns"]]
    return [dict(zip(cols, row)) for row in container["rows"] if isinstance(row, list)]


def page_meta(payload):
    """Pagination evidence from an inventory API / pac resource-query page, or Azure Resource Graph REST response."""
    meta = {}
    low = {norm_key(k): v for k, v in payload.items()}
    for key, canon in (("totalrecords", "totalRecords"), ("count", "count"), ("resulttruncated", "resultTruncated"),
                       ("skiptoken", "skipToken"), ("totalrecordscount", "totalRecords")):
        if key in low and canon not in meta:
            meta[canon] = low[key]
    if "skipToken" not in meta and isinstance(low.get("$skiptoken"), str):
        meta["skipToken"] = low["$skiptoken"]
    truncated = meta.get("resultTruncated")
    if isinstance(truncated, str):
        truncated = truncated.strip().lower() in ("true", "1", "yes")
    meta["truncated"] = bool(truncated) or not is_blank(meta.get("skipToken"))
    total = meta.get("totalRecords")
    try:
        meta["totalRecords"] = int(total) if total is not None and not isinstance(total, bool) else None
    except (TypeError, ValueError):
        meta["totalRecords"] = None
    return meta


def unwrap_json(payload):
    """Return (records, shape_label, page_meta) from any supported JSON container."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)], "JSON list", {}
    if isinstance(payload, dict):
        if isinstance(payload.get("rows"), list) and isinstance(payload.get("columns"), list):
            return table_records(payload), "Azure Resource Graph table (columns/rows)", {}
        for key in CONTAINER_KEYS:
            inner = payload.get(key)
            if isinstance(inner, list):
                keys = set(norm_key(k) for k in payload)
                api = key == "data" and bool(keys & {"totalrecords", "totalrecordscount", "resulttruncated", "skiptoken"})
                label = "inventory API / pac resource-query" if api else "JSON object with '%s' array" % key
                return [r for r in inner if isinstance(r, dict)], label, (page_meta(payload) if api else {})
            if isinstance(inner, dict) and isinstance(inner.get("rows"), list) and isinstance(inner.get("columns"), list):
                return table_records(inner), "Azure Resource Graph REST (columns/rows)", page_meta(payload)
        if "properties" in payload or "type" in payload:
            return [payload], "single JSON record", {}
    return [], "unrecognized JSON", {}


def load_file(path):
    """Return (records, shape_label, page_meta). Records are raw dicts; page_meta is {} unless the file is an API page."""
    with open(path, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8-sig", errors="replace")
    stripped = text.lstrip()
    if stripped[:1] in ("{", "["):
        try:
            return unwrap_json(json.loads(text))
        except ValueError:
            pass
        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except ValueError:
                records = []
                break
            if isinstance(item, dict):
                records.append(item)
        if records:
            return records, "newline-delimited JSON", {}
        return [], "invalid JSON (could not be parsed as a JSON document or as newline-delimited JSON)", {}
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text, newline=""), dialect=dialect)
    records = []
    for row in reader:
        if row is None:
            continue
        clean = {}
        for key, value in row.items():
            if key is None:
                continue
            clean[str(key).strip()] = value
        if any(not is_blank(v) for v in clean.values()):
            records.append(clean)
    return records, "CSV, %d columns" % len(reader.fieldnames or []), {}


# --------------------------------------------------------------------------
# Record normalization
# --------------------------------------------------------------------------

JSON_VALUED = ("properties", "sharedwithviewers", "sharedwitheditors", "capabilitiescounts", "powerplatformconnectors", "channels")


def flatten(record):
    """Map normalized key -> value for every path and leaf name in a record.

    Full paths win over bare leaf names when both exist, and the first value
    seen for a key is kept, so `properties.displayName` is not overwritten by
    an unrelated nested `displayName`.
    """
    paths = {}
    leaves = {}

    def walk(node, prefix):
        for key, value in node.items():
            path = (prefix + "." + str(key)) if prefix else str(key)
            if isinstance(value, str) and norm_key(key) in JSON_VALUED:
                value = maybe_json(value)
            paths.setdefault(norm_key(path), value)
            leaves.setdefault(norm_key(key), value)
            if isinstance(value, dict):
                walk(value, path)

    walk(record, "")
    merged = dict(leaves)
    merged.update(paths)
    return merged


# canonical field -> aliases in priority order (normalized keys).
FIELD_ALIASES = OrderedDict([
    ("type", ["type", "itemtype", "resourcetype"]),
    ("displayName", ["propertiesdisplayname", "displayname", "itemname", "agentname", "resourcename", "botname"]),
    ("id", ["itemid", "agentid", "resourceid", "propertiesbotid", "botid", "propertiesname", "id"]),
    ("location", ["location", "region", "environmentregion"]),
    ("tenantId", ["tenantid"]),
    ("createdAt", ["propertiescreatedat", "createdat", "createdon", "createdtime", "created", "createddate"]),
    ("createdBy", ["propertiescreatedby", "createdby", "creator"]),
    ("ownerId", ["propertiesownerid", "ownerid", "owner", "ownerobjectid"]),
    ("environmentId", ["propertiesenvironmentid", "environmentid", "joinkey"]),
    ("environmentName", ["environmentname", "environmentdisplayname", "environment"]),
    ("environmentType", ["environmenttype"]),
    ("isManagedEnvironment", ["ismanagedenvironment", "managedenvironment"]),
    ("lastPublishedAt", ["propertieslastpublishedat", "lastpublishedat", "lastpublished", "lastpublishedon", "publishedon", "lastpublisheddate"]),
    ("createdIn", ["propertiescreatedin", "createdin", "authoringtool", "source"]),
    ("schemaName", ["propertiesschemaname", "schemaname"]),
    ("isQuarantined", ["propertiesisquarantined", "isquarantined", "quarantined", "blocked", "isblocked"]),
    ("quarantinedAt", ["propertiesquarantinedat", "quarantinedat"]),
    ("isManaged", ["propertiesismanaged", "ismanaged", "managed", "insolution", "managedsolution"]),
    ("harness", ["propertiesharness", "harness"]),
    ("isCLIAgent", ["propertiesiscliagent", "iscliagent"]),
    ("entraAppId", ["propertiesentraappid", "entraappid", "appid", "applicationid", "appregistrationid"]),
    ("entraAgentId", ["propertiesentraagentid", "entraagentid", "agentidentityid", "agentidentity"]),
    ("entraAgentBlueprintId", ["propertiesentraagentblueprintid", "entraagentblueprintid", "blueprintid"]),
    ("orchestration", ["propertiesorchestration", "orchestration", "orchestrationmode"]),
    ("model", ["propertiesmodel", "model", "aimodel", "primarymodel"]),
    ("authentication", ["propertiesauthentication", "authentication", "authenticationmode", "authmode", "userauthentication"]),
    ("channels", ["propertieschannels", "channels", "publishedchannels", "deployedchannels"]),
    ("sharedWithViewers", ["propertiessharedwithviewers", "sharedwithviewers", "viewers", "sharedwithusers"]),
    ("sharedWithEditors", ["propertiessharedwitheditors", "sharedwitheditors", "editors", "coauthors"]),
    ("capabilitiesCounts", ["propertiescapabilitiescounts", "capabilitiescounts"]),
    ("powerPlatformConnectors", ["propertiespowerplatformconnectors", "powerplatformconnectors", "connectors", "connectorsused"]),
    ("isWebSearchEnabledForKnowledge", ["propertiesiswebsearchenabledforknowledge", "iswebsearchenabledforknowledge", "websearch", "websearchenabled"]),
])

DATE_FIELDS = ("createdAt", "lastPublishedAt", "quarantinedAt")
BOOL_FIELDS = ("isQuarantined", "isManaged", "isCLIAgent", "isWebSearchEnabledForKnowledge", "isManagedEnvironment")
JOIN_FIELDS = ("environmentName", "environmentType", "isManagedEnvironment")
STRING_FIELDS = ("id", "displayName", "ownerId", "createdBy", "environmentId", "environmentName", "environmentType",
                 "createdIn", "schemaName", "entraAppId", "entraAgentId", "entraAgentBlueprintId", "orchestration",
                 "model", "location", "tenantId", "harness")


def pick(flat, aliases):
    for alias in aliases:
        if alias in flat:
            return True, flat[alias]
    return False, None


def norm_auth(value):
    if value is None:
        return None
    text = str(value).strip()
    low = text.lower()
    if low in ("none", "noauthentication", "no authentication", "noauth", "anonymous", "no", "not required", "unauthenticated"):
        return "None"
    if is_blank(text):
        return None
    if "entra" in low or "azure active directory" in low or low in ("aad", "microsoft", "microsoftentra", "authenticate with microsoft", "integrated"):
        return "Microsoft Entra"
    if "oauth" in low or "generic" in low or "manual" in low:
        return "Generic OAuth 2.0"
    return text


ENTIRE_WORDS = ("entire", "everyone", "whole", "all users", "tenant-wide", "tenant wide", "organization-wide", "org-wide")


def parse_share(value):
    value = maybe_json(value)
    out = {"userCount": None, "groupCount": None, "entireTenant": None}
    if value is None or is_blank(value):
        return out
    if isinstance(value, dict):
        flat = {norm_key(k): v for k, v in value.items()}
        out["userCount"] = parse_int(flat.get("usercount"))
        out["groupCount"] = parse_int(flat.get("groupcount"))
        out["entireTenant"] = parse_bool(flat.get("entiretenant"))
        return out
    text = str(value).strip().lower()
    users = re.search(r"(\d+)\s*(?:individual\s+)?users?", text)
    groups = re.search(r"(\d+)\s*(?:security\s+)?groups?", text)
    if users:
        out["userCount"] = int(users.group(1))
    if groups:
        out["groupCount"] = int(groups.group(1))
    if any(word in text for word in ENTIRE_WORDS) or (not re.search(r"\d", text) and text in ("tenant", "organization", "organisation", "org")):
        out["entireTenant"] = True
    elif users or groups:
        out["entireTenant"] = False
    elif parse_bool(text) is not None:
        out["entireTenant"] = parse_bool(text)
    elif parse_int(text) is not None:
        out["userCount"] = parse_int(text)
        out["entireTenant"] = False
    return out


def parse_counts(value):
    value = maybe_json(value)
    if isinstance(value, dict):
        return {str(k): parse_int(v) for k, v in value.items() if parse_int(v) is not None}
    return {}


OP_KEYS = {
    "operationid": "operationId", "createdby": "createdBy", "isenabled": "isEnabled", "usedas": "usedAs",
    "requiresenduserconsent": "requiresEndUserConsent", "whencanbeused": "whenCanBeUsed",
    "connectionprovider": "connectionProvider", "connectionidsharedbymaker": "connectionIdSharedByMaker",
}


def parse_connectors(value):
    """Return (connectors, has_detail). connectors: [{connectorId, operations:[...]}]."""
    value = maybe_json(value)
    if value is None or is_blank(value):
        return [], False
    connectors = []
    has_detail = False
    if isinstance(value, list):
        for item in value:
            item = maybe_json(item)
            if isinstance(item, dict):
                flat = {norm_key(k): v for k, v in item.items()}
                cid = flat.get("connectorid") or flat.get("id") or flat.get("name") or flat.get("displayname")
                ops_raw = maybe_json(flat.get("operations")) or []
                ops = []
                if isinstance(ops_raw, list):
                    for op in ops_raw:
                        if isinstance(op, dict):
                            opflat = {norm_key(k): v for k, v in op.items()}
                            entry = {}
                            for key, canon in OP_KEYS.items():
                                if key in opflat:
                                    entry[canon] = opflat[key]
                            if "isEnabled" in entry:
                                entry["isEnabled"] = parse_bool(entry["isEnabled"])
                            if "requiresEndUserConsent" in entry:
                                entry["requiresEndUserConsent"] = parse_bool(entry["requiresEndUserConsent"])
                            for key in ("connectionIdSharedByMaker", "createdBy"):
                                if key in entry and not is_blank(entry[key]):
                                    entry[key] = str(entry[key]).strip().lower()
                            if any(k in entry for k in ("connectionProvider", "usedAs", "whenCanBeUsed")):
                                has_detail = True
                            ops.append(entry)
                        elif not is_blank(op):
                            ops.append({"operationId": str(op)})
                if cid:
                    connectors.append({"connectorId": str(cid), "operations": ops})
            elif not is_blank(item):
                connectors.append({"connectorId": str(item).strip(), "operations": []})
        return connectors, has_detail
    if isinstance(value, dict):
        return parse_connectors([value])
    names = parse_list(value)
    return [{"connectorId": n, "operations": []} for n in names], False


def derive_harness(agent):
    if not is_blank(agent.get("harness")):
        return str(agent["harness"]).strip(), False
    if agent.get("isCLIAgent") is True:
        return "GitHub Copilot", True
    model = (agent.get("model") or "").lower()
    created_in = (agent.get("createdIn") or "").lower()
    if "microsoft 365 copilot" in model or "agent builder" in created_in:
        return "Copilot Chat", True
    return "Standard", True


def normalize_record(raw, source):
    flat = flatten(raw)
    rec = {"_source": source, "_sources": {source}, "_present": set()}
    for field, aliases in FIELD_ALIASES.items():
        found, value = pick(flat, aliases)
        if found:
            rec["_present"].add(field)
        rec[field] = value
    arm_shaped = isinstance(raw.get("properties"), (dict, str)) or (isinstance(raw.get("type"), str) and raw.get("type", "").lower().startswith("microsoft."))
    if arm_shaped:
        if not is_blank(raw.get("name")) and ("itemid" not in flat and "agentid" not in flat):
            rec["id"] = raw.get("name")
            rec["_present"].add("id")
        props = maybe_json(raw.get("properties"))
        if isinstance(props, dict) and not is_blank(props.get("displayName")):
            rec["displayName"] = props.get("displayName")
    elif is_blank(rec.get("displayName")) and "name" in flat:
        rec["displayName"] = flat["name"]
        rec["_present"].add("displayName")
    for field in ("ownerId", "createdBy", "environmentId", "id", "authentication", "model", "orchestration", "createdIn", "location", "displayName"):
        value = rec.get(field)
        if isinstance(value, dict):
            inner = {norm_key(k): v for k, v in value.items()}
            rec[field] = (inner.get("id") or inner.get("objectid") or inner.get("userid")) if field in ("ownerId", "createdBy", "environmentId", "id") else None
            rec[field] = rec[field] or inner.get("name") or inner.get("displayname") or inner.get("mode") or inner.get("type") or inner.get("value") or json.dumps(value, sort_keys=True)
    rec["_rawLastPublished"] = rec.get("lastPublishedAt")
    for field in DATE_FIELDS:
        rec[field] = parse_dt(rec.get(field))
    for field in BOOL_FIELDS:
        rec[field] = parse_bool(rec.get(field))
    rec["type"] = (str(rec["type"]).strip().lower() if not is_blank(rec.get("type")) else None)
    rec["authentication"] = norm_auth(rec.get("authentication"))
    rec["channels"] = parse_list(rec.get("channels"))
    rec["sharedWithViewers"] = parse_share(rec.get("sharedWithViewers"))
    rec["sharedWithEditors"] = parse_share(rec.get("sharedWithEditors"))
    rec["capabilitiesCounts"] = parse_counts(rec.get("capabilitiesCounts"))
    connectors, has_detail = parse_connectors(rec.get("powerPlatformConnectors"))
    rec["powerPlatformConnectors"] = connectors
    rec["_connectorDetail"] = has_detail
    if has_detail:
        rec["_present"].add("connectorOperations")
    for field in STRING_FIELDS:
        rec[field] = None if is_blank(rec.get(field)) else str(rec[field]).strip()
    for field in ("environmentId", "ownerId", "createdBy"):
        if rec.get(field):
            rec[field] = rec[field].lower()
    if rec.get("id") and "/" in rec["id"]:
        rec["id"] = rec["id"].rstrip("/").rsplit("/", 1)[-1]
    finalize(rec)
    return rec


def agent_key(rec):
    """Identity used for de-duplication and cross-references. A bot keeps its ID when a solution is deployed
    to another environment, so the key is the ID qualified by the environment when it is known. (Tenant is not
    part of the key: environment IDs are already tenant-unique, and CSV exports omit the tenant.)"""
    if not rec.get("id"):
        return None
    return "%s|%s" % (env_identity(rec), rec["id"].lower())


def env_identity(rec):
    """Environment ID when known, else the environment name (admin center CSVs name environments), else ''."""
    if rec.get("environmentId"):
        return rec["environmentId"].lower()
    if rec.get("environmentName"):
        return "name:" + rec["environmentName"].strip().lower()
    return ""


def finalize(rec):
    """Recompute derived fields; called after normalization and after merging duplicates."""
    if rec.get("_harnessDerived"):
        rec["harness"] = None  # an inferred harness is not evidence; re-derive from the merged record
    rec["harness"], rec["_harnessDerived"] = derive_harness(rec)
    rec["isAgentBuilder"] = bool(rec.get("createdIn") and "agent builder" in rec["createdIn"].lower()) or rec["harness"] == "Copilot Chat"
    rec["_unparsedPublishDate"] = False
    if rec.get("lastPublishedAt") is not None:
        rec["published"] = True
    elif "lastPublishedAt" not in rec["_present"]:
        rec["published"] = None
    elif is_blank(rec.get("_rawLastPublished")):
        rec["published"] = False
    else:
        rec["published"] = None  # a date the parser could not read: unknown, not draft
        rec["_unparsedPublishDate"] = True


def looks_like_agent(rec):
    if rec.get("type"):
        return rec["type"] == AGENT_TYPE or rec["type"].endswith("/agents") or rec["type"] in ("agent", "agents", "copilot studio agent")
    return True  # untyped export (for example a CSV from Manage > Copilot Studio): treat as agents


def looks_like_environment(rec):
    return bool(rec.get("type")) and (rec["type"] == ENV_TYPE or rec["type"].endswith("/environments") or rec["type"] == "environment")


# --------------------------------------------------------------------------
# Environments and users
# --------------------------------------------------------------------------


def environment_from_record(raw):
    flat = flatten(raw)
    arm_shaped = isinstance(raw.get("properties"), (dict, str)) or str(raw.get("type", "")).lower().startswith("microsoft.")
    id_aliases = ("name", "environmentid", "itemid", "id") if arm_shaped else ("environmentid", "itemid", "id", "name")
    env_id = None
    for alias in id_aliases:
        if alias in flat and not is_blank(flat[alias]):
            env_id = str(flat[alias]).strip().lower()
            break
    if not env_id:
        return None
    if "/" in env_id:
        env_id = env_id.rstrip("/").rsplit("/", 1)[-1]
    props = maybe_json(raw.get("properties"))
    name = None
    if isinstance(props, dict) and not is_blank(props.get("displayName")):
        name = props.get("displayName")
    else:
        name_aliases = ("propertiesdisplayname", "displayname", "environmentname", "itemname", "environment") + (() if arm_shaped else ("name",))
        for alias in name_aliases:
            if alias in flat and not is_blank(flat[alias]):
                name = flat[alias]
                break
    env_type = None
    for alias in ("propertiesenvironmenttype", "environmenttype", "" if arm_shaped else "type", "sku"):
        if alias and alias in flat and not is_blank(flat[alias]):
            env_type = str(flat[alias]).strip()
            break
    managed = None
    for alias in ("propertiesismanaged", "ismanaged", "ismanagedenvironment", "managedenvironment", "managed"):
        if alias in flat:
            managed = parse_bool(flat[alias])
            break
    group = None
    for alias in ("propertiesenvironmentgroup", "environmentgroup", "environmentgroupname"):
        if alias in flat and not is_blank(flat[alias]):
            group = str(flat[alias]).strip()
            break
    region = None
    for alias in ("location", "region", "environmentregion"):
        if alias in flat and not is_blank(flat[alias]):
            region = str(flat[alias]).strip()
            break
    return {"id": env_id, "name": (str(name).strip() if name else None), "type": env_type, "isManaged": managed, "group": group, "region": region}


DEPARTED_WORDS = ("disabled", "departed", "left", "terminated", "inactive", "offboard", "blocked", "deleted")


def load_users(path):
    records, _, _ = load_file(path)
    users = {}
    by_name = {}
    for raw in records:
        flat = flatten(raw)
        uid = None
        for alias in ("id", "objectid", "userid", "userobjectid", "entraid", "aadobjectid"):
            if alias in flat and not is_blank(flat[alias]):
                uid = str(flat[alias]).strip().lower()
                break
        upn = None
        for alias in ("userprincipalname", "upn", "email", "mail", "principalname"):
            if alias in flat and not is_blank(flat[alias]):
                upn = str(flat[alias]).strip().lower()
                break
        name = None
        for alias in ("displayname", "name", "fullname"):
            if alias in flat and not is_blank(flat[alias]):
                name = str(flat[alias]).strip()
                break
        enabled = None
        for alias in ("accountenabled", "enabled", "isenabled", "active", "isactive"):
            if alias in flat:
                enabled = parse_bool(flat[alias])
                break
        for alias in ("status", "accountstatus", "state", "employmentstatus"):
            if alias in flat and not is_blank(flat[alias]):
                status = str(flat[alias]).lower()
                if any(word in status for word in DEPARTED_WORDS):
                    enabled = False
                break
        entry = {"id": uid, "upn": upn, "name": name, "enabled": enabled}
        if uid:
            users[uid] = entry
        if upn:
            users.setdefault(upn, entry)
        if name:
            by_name.setdefault(name.lower(), []).append(entry)
    # Admin center CSVs carry owners as display names; index a name only when it maps to exactly one user.
    for name, entries in by_name.items():
        if len(entries) == 1:
            users.setdefault(name, entries[0])
    return users


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

RULES = OrderedDict([
    ("ID1", ("No agent identity recorded", "identity")),
    ("ID2", ("Legacy app registration identity", "identity")),
    ("EX1", ("Published without user authentication", "exposure")),
    ("EX2", ("Shared with the entire tenant", "exposure")),
    ("EX3", ("Web search enabled as knowledge", "exposure")),
    ("EX4", ("Broad editor access", "exposure")),
    ("CR1", ("Maker-provided connection used for tools without end-user consent", "credentials")),
    ("CR2", ("Maker-provided connection used for knowledge", "credentials")),
    ("CR3", ("Maker-provided connection reused across agents", "credentials")),
    ("CR4", ("Custom or watched connector in use", "credentials")),
    ("CR5", ("Disabled connector operations left configured", "credentials")),
    ("LC1", ("Draft never published", "lifecycle")),
    ("LC2", ("Quarantined or blocked", "lifecycle")),
    ("LC3", ("Unmanaged agent in a Production environment", "lifecycle")),
    ("LC4", ("Published from the Default environment", "lifecycle")),
    ("LC5", ("Published from a Developer or Trial environment", "lifecycle")),
    ("LC6", ("Inventory truncated at 200 resources", "lifecycle")),
    ("LC7", ("Not republished for a long time", "lifecycle")),
    ("OW1", ("Owner account disabled or departing", "ownership")),
    ("OW2", ("No owner recorded", "ownership")),
    ("OW3", ("Ownership concentration", "ownership")),
    ("RG1", ("Outside allowed regions", "region")),
    ("MD1", ("Non-Microsoft model as primary model", "model")),
])

# Fields each rule needs. "any:" groups mean at least one of the fields must be available.
# "present:" means the column only has to exist in the audited records, because the rule's evidence is an empty value.
RULE_FIELDS = {
    "ID1": ["any:entraAgentId,entraAppId,entraAgentBlueprintId"],
    "ID2": ["entraAppId"],
    "EX1": ["authentication", "channels"],
    "EX2": ["sharedWithViewers"],
    "EX3": ["isWebSearchEnabledForKnowledge"],
    "EX4": ["sharedWithEditors"],
    "CR1": ["connectorOperations"],
    "CR2": ["connectorOperations"],
    "CR3": ["connectorOperations"],
    "CR4": ["powerPlatformConnectors"],
    "CR5": ["connectorOperations"],
    "LC1": ["present:lastPublishedAt", "createdAt"],
    "LC2": ["isQuarantined"],
    "LC3": ["isManaged", "environmentType"],
    "LC4": ["environmentType"],
    "LC5": ["environmentType", "channels"],
    "LC6": ["capabilitiesCounts"],
    "LC7": ["lastPublishedAt"],
    "OW1": ["ownerId", "accountState"],
    "OW2": ["present:ownerId"],
    "OW3": ["ownerId"],
    "RG1": ["location"],
    "MD1": ["model"],
}

TEAMS_LIKE = ("teams", "microsoft teams", "microsoft 365", "m365 copilot", "copilot")
EXTERNAL_MODEL_WORDS = ("claude", "anthropic", "sonnet", "opus", "haiku", "mistral", "grok", "llama", "gemini", "deepseek", "cohere", "command-r")


def channel_is_teams_like(channel):
    low = channel.lower().strip()
    return low in TEAMS_LIKE or low.startswith("microsoft 365 copilot") or low.startswith("teams")


def custom_connector(connector_id):
    """Heuristic: Microsoft does not document the ID pattern. Custom connector IDs look like
    shared_<escaped display name>-5f<hex...> (for example shared_my-20connector-5f0027f520b23e81c1)."""
    low = connector_id.lower()
    return low.startswith("shared_") and bool(re.search(r"-5f[0-9a-f]{8,}$", low))


def coverage_of(agents):
    """Per-field {present, populated} counts over a list of records."""
    cov = OrderedDict()
    fields = [f for f in FIELD_ALIASES if f not in JOIN_FIELDS] + ["connectorOperations"]
    for field in fields:
        present = sum(1 for a in agents if field in a["_present"])
        populated = 0
        for a in agents:
            value = a.get(field)
            if field == "connectorOperations":
                value = a.get("_connectorDetail") or None
            if not field_blank(field, value):
                populated += 1
        cov[field] = {"present": present, "populated": populated}
    return cov


def sum_coverage(covs):
    out = OrderedDict()
    for cov in covs:
        for field, c in cov.items():
            cell = out.setdefault(field, {"present": 0, "populated": 0})
            cell["present"] += c["present"]
            cell["populated"] += c["populated"]
    return out


class Audit:
    def __init__(self, agents, environments, users, opts, coverage_agents=None, source_coverage=None):
        self.agents = agents
        self.by_id = {agent_key(a): a for a in agents if agent_key(a)}
        self.environments = environments
        self.users = users
        self.opts = opts
        self.findings = []
        self.not_evaluated = OrderedDict()
        # Field coverage describes the export, so it is computed on all agents even when the audit is scoped.
        self.coverage = self._coverage(coverage_agents if coverage_agents is not None else agents)
        # Rule availability also needs the field in the file(s) the audited agents come from, so a scoped audit
        # of agents from a CSV is not enabled by fields that only another file carries. Optional JSON properties
        # that happen to be unset for every in-scope agent still count, because their file carries them.
        # Source coverage is taken from the records as each file supplied them (before duplicates were merged),
        # so a field another file added to one agent does not make the whole file look like it carries it.
        everyone = coverage_agents if coverage_agents is not None else agents
        if source_coverage is not None:
            self.source_coverage = source_coverage
        else:
            self.source_coverage = OrderedDict()
            for source in sorted(set(s for a in everyone for s in a["_sources"])):
                self.source_coverage[source] = self._coverage([a for a in everyone if source in a["_sources"]])
        sources = sorted(set(s for a in agents for s in a["_sources"]))
        self.scope_coverage = sum_coverage([self.source_coverage[s] for s in sources if s in self.source_coverage]) if sources else self.coverage
        self.gaps = []  # evidence gaps found while rules ran; reported as warnings
        self.partial = OrderedDict()  # rule -> (agents skipped, {source: count}, fields) when only part of the scope carried the fields
        self.departing = set(x.strip().lower() for x in (opts.departing or "").split(",") if x.strip())
        self.allowed_regions = set(x.strip().lower() for x in (opts.allowed_regions or "").split(",") if x.strip())
        self.watch_connectors = [x.strip().lower() for x in (opts.watch_connectors or "").split(",") if x.strip()]
        self.name_collisions = self._collisions()

    # -- coverage -----------------------------------------------------------
    def _coverage(self, agents):
        return coverage_of(agents)

    def fields_absent(self):
        return [f for f, c in self.coverage.items() if c["present"] == 0]

    def fields_empty(self):
        return [f for f, c in self.coverage.items() if c["present"] > 0 and c["populated"] == 0]

    def field_present(self, field):
        """The field exists in at least one record of the file(s) the audited agents come from."""
        return self.scope_coverage.get(field, {}).get("present", 0) > 0

    def field_available(self, field):
        """The field exists in the audited agents' file(s) and the export populates it somewhere."""
        if field == "accountState":
            return self.account_state_available()
        if field == "environmentType":
            return any((a.get("_env") or {}).get("type") for a in self.agents)
        return self.field_present(field) and self.coverage.get(field, {}).get("populated", 0) > 0

    def account_state_available(self):
        return bool(self.departing) or any(u.get("enabled") is not None for u in self.users.values())

    def agent_has_field(self, agent, field):
        """The field exists in a file this agent's record came from (an unset optional property still counts)."""
        if field in ("environmentType", "accountState"):
            return True
        return any(self.source_coverage.get(s, {}).get(field, {}).get("present", 0) > 0 for s in agent["_sources"])

    def agent_field_available(self, agent, field):
        """The field is populated somewhere in a file this agent's record came from."""
        return any(self.source_coverage.get(s, {}).get(field, {}).get("populated", 0) > 0 for s in agent["_sources"])

    def agent_measure_ok(self, agent, fields):
        return all(self.agent_has_field(agent, f) and self.field_available(f) for f in fields)

    def rule_fields(self, rule):
        out = []
        for req in RULE_FIELDS[rule]:
            if req.startswith("any:"):
                out.append(req[4:].split(","))
            elif req.startswith("present:"):
                out.append([req[8:]])
            else:
                out.append([req])
        return out

    def agent_eligible(self, agent, rule):
        return all(any(self.agent_has_field(agent, f) for f in group) for group in self.rule_fields(rule))

    def field_reason(self, field):
        if field == "accountState":
            return "no owner account state supplied"
        if field == "environmentType":
            return "environment type not in export or join"
        if not self.field_present(field):
            if self.coverage.get(field, {}).get("present", 0) > 0:
                return "%s not in the file the audited agents come from" % field
            return "%s not in export" % field
        return "%s present but empty in every record" % field

    def rule_available(self, rule):
        missing = []
        for req in RULE_FIELDS[rule]:
            if req.startswith("any:"):
                names = req[4:].split(",")
                if not any(self.field_available(f) for f in names):
                    missing.append("no identity column (%s) populated" % ", ".join(names))
            elif req.startswith("present:"):
                if not self.field_present(req[8:]):
                    missing.append(self.field_reason(req[8:]))
            elif not self.field_available(req):
                missing.append(self.field_reason(req))
        if missing:
            self.not_evaluated[rule] = missing
            return False
        return True

    def _collisions(self):
        counts = Counter((a.get("displayName") or "").lower() for a in self.agents if a.get("displayName"))
        return set(name for name, n in counts.items() if n > 1)

    # -- labels -------------------------------------------------------------
    def agent_label(self, agent):
        name = agent.get("displayName")
        if not name:
            return agent.get("id") or "(unnamed agent)"
        if name.lower() in self.name_collisions and agent.get("id"):
            return "%s (…%s)" % (name, short_id(agent["id"]))
        return name

    def env_label(self, agent):
        env = agent.get("_env") or {}
        return env.get("name") or agent.get("environmentName") or agent.get("environmentId") or "(unknown environment)"

    def env_type(self, agent):
        return ((agent.get("_env") or {}).get("type") or agent.get("environmentType") or "")

    def owner_label(self, agent_or_id):
        oid = agent_or_id.get("ownerId") if isinstance(agent_or_id, dict) else agent_or_id
        if not oid:
            return "(no owner)"
        user = self.users.get(oid.lower())
        if user and user.get("name"):
            return "%s (%s)" % (user["name"], user.get("upn") or oid)
        return oid

    def owner_state(self, oid):
        """Return 'account disabled', 'departing', or ''."""
        hit, why = self._departing(oid)
        if not hit:
            return ""
        return "account disabled" if "disabled" in why else "departing"

    def labels_for(self, agents, func):
        labels = dedupe([func(a) for a in agents])
        return ", ".join(labels) if len(labels) <= 3 else "(several: %d)" % len(labels)

    # -- predicates ---------------------------------------------------------
    def is_published(self, agent):
        return agent.get("published") is not False

    def maker_ops(self, agent):
        out = []
        for c in agent["powerPlatformConnectors"]:
            for op in c["operations"]:
                if str(op.get("connectionProvider", "")).lower() == "maker" and op.get("isEnabled") is not False:
                    out.append("%s.%s" % (c["connectorId"], op.get("operationId") or "?"))
        return out

    def has_maker_connection(self, agent):
        return bool(self.maker_ops(agent))

    def anonymous(self, agent):
        return agent.get("authentication") == "None"

    def entire_tenant(self, agent):
        return agent["sharedWithViewers"].get("entireTenant") is True

    def _ops(self, agent):
        for c in agent["powerPlatformConnectors"]:
            for op in c["operations"]:
                yield c["connectorId"], op

    def _departing(self, oid):
        if not oid:
            return False, ""
        low = oid.lower()
        if low in self.departing:
            return True, "listed as departing"
        user = self.users.get(low)
        if user:
            if (user.get("upn") and user["upn"] in self.departing) or (user.get("id") and user["id"] in self.departing):
                return True, "listed as departing"
            if user.get("enabled") is False:
                return True, "marked disabled in the user list"
        return False, ""

    # -- findings -----------------------------------------------------------
    def add(self, rule, severity, agents, detail, **extra):
        agents = [a for a in agents if a is not None]
        finding = {
            "rule": rule, "title": RULES[rule][0], "category": RULES[rule][1], "severity": severity,
            "agentIds": [a.get("id") for a in agents if a.get("id")],
            "agentKeys": [agent_key(a) for a in agents if agent_key(a)],
            "agentId": agents[0].get("id") if len(agents) == 1 else None,
            "agentName": self.agent_label(agents[0]) if len(agents) == 1 else "%d agents" % len(agents),
            "environment": self.labels_for(agents, self.env_label) if agents else "",
            "environmentId": agents[0].get("environmentId") if len(agents) == 1 else None,
            "owner": self.labels_for(agents, self.owner_label) if agents else "",
            "ownerId": agents[0].get("ownerId") if len(agents) == 1 else None,
            "detail": detail,
            "_agents": agents,
        }
        finding.update(extra)
        self.findings.append(finding)

    def run(self):
        everyone = self.agents
        for rule in RULES:
            if not self.rule_available(rule):
                continue
            eligible = [a for a in everyone if self.agent_eligible(a, rule)]
            if len(eligible) < len(everyone):
                skipped = [a for a in everyone if a not in eligible]
                by_source = Counter(os.path.basename(min(a["_sources"])) for a in skipped)
                lacking = sorted(set(f for a in skipped for group in self.rule_fields(rule) for f in group if not any(self.agent_has_field(a, g) for g in group)))
                self.partial[rule] = (len(skipped), by_source, lacking)
            self.agents = eligible
            try:
                getattr(self, "rule_" + rule)()
            finally:
                self.agents = everyone
            if rule in self.not_evaluated:
                self.partial.pop(rule, None)  # the rule opted out entirely (for example RG1 without --allowed-regions)
        self.findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["rule"], (f.get("agentName") or "").lower(), f.get("agentId") or ""))
        for index, finding in enumerate(self.findings, 1):
            finding["id"] = "F%d" % index
        for a in self.agents:
            a["_findings"] = []
        for f in self.findings:
            if f.get("_attach", True):
                for a in f["_agents"]:
                    a["_findings"].append(f)
        return self.findings

    def rule_ID1(self):
        for a in self.agents:
            if a["isAgentBuilder"] or not self.is_published(a):
                continue
            if a.get("entraAgentId") or a.get("entraAppId") or a.get("entraAgentBlueprintId"):
                continue
            agent_col = self.agent_field_available(a, "entraAgentId")
            app_col = self.agent_field_available(a, "entraAppId")
            when = "published %s" % fmt_dt(a["lastPublishedAt"]) if a.get("lastPublishedAt") else "publish state not in export"
            note = " GitHub Copilot harness agents receive an identity at first publish." if a["harness"] == "GitHub Copilot" else ""
            missing = [n for n, ok in (("Entra Agent ID", agent_col), ("app registration", app_col)) if not ok]
            who = "a published Copilot Studio agent (%s harness, %s)" % (a["harness"], when)
            if missing:
                self.add("ID1", "medium", [a], "No identity recorded for %s. The export carries no populated %s column, so the agent may hold an identity this export cannot show. Confirm in Copilot Studio Settings > Advanced > Metadata.%s" % (who, " or ".join(missing), note))
            else:
                self.add("ID1", "high", [a], "No Entra Agent ID or app registration recorded for %s. Without an identity there is nothing for Entra audit, Conditional Access, or Agent 365 to attach to. Confirm in Copilot Studio Settings > Advanced > Metadata and under Entra ID > Agents > Agent identities.%s" % (who, note))

    def rule_ID2(self):
        for a in self.agents:
            if a["isAgentBuilder"] or not a.get("entraAppId") or a.get("entraAgentId"):
                continue
            if self.agent_field_available(a, "entraAgentId"):
                self.add("ID2", "medium", [a], "Identity is a legacy app registration (%s). Connector scopes and Conditional Access on the agent identity apply only to Entra Agent IDs; migrate in the Power Platform admin center (Actions > Recommendations) or with the migration API, or wait for Microsoft's automatic migration." % a["entraAppId"])
            else:
                self.add("ID2", "medium", [a], "App registration %s is recorded and the export has no populated Entra Agent ID column, so this agent may be a legacy identity awaiting migration or may already be migrated. Confirm in Copilot Studio Settings > Advanced > Metadata before scheduling a migration." % a["entraAppId"])

    def rule_EX1(self):
        for a in self.agents:
            if not self.anonymous(a) or not self.is_published(a) or not a["channels"]:
                continue
            web = [c for c in a["channels"] if not channel_is_teams_like(c)]
            severity = "high" if web else "medium"
            if web:
                demo = any("demo" in c.lower() for c in web)
                where = ", ".join(web) + (", a Microsoft-hosted page that anyone with the link can use without signing in" if demo and len(web) == 1 else "")
                detail = "Authentication is None and the agent is published to %s." % where
                if not (demo and len(web) == 1):
                    detail += " Anyone with the link can use %s without signing in." % ", ".join(web)
                detail += " Confirm the %s still in use; if not, remove %s, because %s stays reachable for as long as the agent is published." % (
                    "channel is" if len(web) == 1 else "channels are", "it" if len(web) == 1 else "them", "it" if len(web) == 1 else "each")
            else:
                detail = "Authentication is None and the agent is published to %s. Microsoft documents the Teams and Microsoft 365 Copilot channel as requiring Authenticate with Microsoft, so this combination is usually stale channel data or a legacy configuration; confirm on the agent's Channels page." % ", ".join(a["channels"])
            extras = []
            if self.has_maker_connection(a):
                extras.append("tools run on maker-provided connections")
            if self.entire_tenant(a):
                extras.append("shared with the entire tenant")
            if extras:
                detail += " On the same agent: " + "; ".join(extras) + "."
            self.add("EX1", severity, [a], detail, channels=list(web))

    def rule_EX2(self):
        for a in self.agents:
            if not self.entire_tenant(a):
                continue
            detail = "Viewer sharing is set to the entire tenant, so every licensed user can chat with this agent once it is published. The inventory does not show how it was shared: Copilot Studio Share > Everyone takes effect with no approval step, while a Teams or Microsoft 365 agent-store submission waits for admin approval."
            aggravators = [x for x in [
                "authentication is None" if self.anonymous(a) else "",
                "tools run on maker-provided connections" if self.has_maker_connection(a) else "",
                "web search is enabled" if a.get("isWebSearchEnabledForKnowledge") is True else ""] if x]
            if aggravators:
                detail += " On the same agent: " + "; ".join(aggravators) + "."
            if a.get("published") is False:
                detail += " The agent is not yet published; review it before first publish."
            self.add("EX2", "high" if aggravators else "medium", [a], detail)

    def rule_EX3(self):
        for a in self.agents:
            if a.get("isWebSearchEnabledForKnowledge") is True and self.is_published(a):
                self.add("EX3", "medium", [a], "Web search is enabled as a knowledge source, so answers can come from the public web. Confirm that is acceptable for this audience and whether a data policy should block public-web knowledge in this environment.")

    def rule_EX4(self):
        threshold = self.opts.editor_threshold
        for a in self.agents:
            editors = a["sharedWithEditors"]
            users = editors.get("userCount") or 0
            groups = editors.get("groupCount") or 0
            if groups > 0 or users >= threshold:
                self.add("EX4", "low", [a], "Editor access is shared with %s and %s. Every editor can change and republish the agent." % (plural(users, "user"), plural(groups, "group")))

    def rule_CR1(self):
        unknown_ops = 0
        unknown_agents = 0
        for a in self.agents:
            if a.get("published") is False:
                continue  # drafts are covered by LC1
            hits = []
            consent_unknown = []
            unknown_when = False
            for cid, op in self._ops(a):
                if op.get("isEnabled") is False:
                    continue
                used = str(op.get("usedAs", "")).lower()
                if used not in ("tool", "topic tool", "topictool", "action"):
                    continue
                if str(op.get("connectionProvider", "")).lower() != "maker":
                    continue
                when = str(op.get("whenCanBeUsed", "") or "").lower().replace(" ", "")
                if when and when != "anytime":
                    continue
                consent = op.get("requiresEndUserConsent")
                if consent is True:
                    continue
                if consent is not False:
                    consent_unknown.append("%s.%s" % (cid, op.get("operationId") or "?"))
                    continue
                if not when:
                    unknown_when = True
                hits.append("%s.%s" % (cid, op.get("operationId") or "?"))
            if consent_unknown:
                unknown_ops += len(consent_unknown)
                unknown_agents += 1
            if not hits:
                continue
            severity = "high" if (self.anonymous(a) or self.entire_tenant(a)) else "medium"
            one = len(hits) == 1
            detail = "%s, %s, %s on a maker-provided connection without asking the user for consent, and the orchestrator can call %s in any conversation%s. Anyone chatting with the agent can trigger %s with the maker's permissions" % (
                "One tool operation" if one else "%d tool operations" % len(hits), capped(hits), "runs" if one else "run", "it" if one else "them",
                "" if not unknown_when else " (whenCanBeUsed not in export)", "it" if one else "them")
            if self.anonymous(a):
                detail += "; since the agent has no user authentication, that includes anonymous users."
            elif self.entire_tenant(a):
                detail += "; the agent is shared with the entire tenant."
            else:
                detail += "."
            if consent_unknown:
                n = len(consent_unknown)
                detail += " %s on the same agent %s no requiresEndUserConsent value in the export and %s not assessed." % (
                    plural(n, "more maker-provided tool operation", "more maker-provided tool operations"), "has" if n == 1 else "have", "was" if n == 1 else "were")
            self.add("CR1", severity, [a], detail, operations=hits)
        if unknown_ops:
            self.gaps.append("CR1: %s on %s %s no requiresEndUserConsent value in the export, so consent is unknown and no finding was raised for %s. Check each tool's connection settings in Copilot Studio." % (
                plural(unknown_ops, "maker-provided tool operation"), plural(unknown_agents, "published agent"), "has" if unknown_ops == 1 else "have", "it" if unknown_ops == 1 else "them"))

    def rule_CR2(self):
        for a in self.agents:
            if a.get("published") is False:
                continue
            hits = []
            for cid, op in self._ops(a):
                if op.get("isEnabled") is False:
                    continue
                if str(op.get("usedAs", "")).lower() == "knowledge" and str(op.get("connectionProvider", "")).lower() == "maker":
                    hits.append(cid)
            if hits:
                self.add("CR2", "medium", [a], "Knowledge from %s is read through a maker-provided connection, so results are limited only by what that connection can see, not by the asking user's permissions." % ", ".join(dedupe(hits)), connectors=dedupe(hits))

    def shared_connections(self):
        """connectionId -> OrderedDict(agent key -> (agent, set(connectorIds)))"""
        by_connection = OrderedDict()
        for a in self.agents:
            for cid, op in self._ops(a):
                conn = op.get("connectionIdSharedByMaker")
                if conn and not is_blank(conn):
                    by_connection.setdefault(str(conn), OrderedDict()).setdefault(agent_key(a) or id(a), (a, set()))[1].add(cid)
        return by_connection

    def rule_CR3(self):
        for conn, agents in self.shared_connections().items():
            if len(agents) < 2:
                continue
            names = ["%s (%s)" % (self.agent_label(a), capped(sorted(cids), 3)) for a, cids in agents.values()]
            self.add("CR3", "medium", [a for a, _ in agents.values()],
                     "Maker-provided connection %s is used by %d agents: %s. Revoking or rotating it, or removing its owner's account, affects all of them." % (conn, len(agents), capped(names, LIST_CAP, "; ")),
                     connectionId=conn)

    def rule_CR4(self):
        for a in self.agents:
            custom = []
            watched = []
            for c in a["powerPlatformConnectors"]:
                cid = c["connectorId"]
                low = cid.lower()
                if any(w == low or w in low for w in self.watch_connectors):
                    watched.append(cid)
                elif custom_connector(cid):
                    custom.append(cid)
            if watched:
                self.add("CR4", "medium", [a], "Uses connectors on the watch list: %s." % capped(dedupe(watched)), connectors=dedupe(watched))
            if custom:
                self.add("CR4", "low", [a], "Uses connectors that look like custom connectors: %s. Custom connectors, MCP servers, and REST tools do not add API permissions to the Entra Agent ID, so Conditional Access on the identity never sees them; govern them through connector and data policies." % capped(dedupe(custom)), connectors=dedupe(custom))

    def rule_CR5(self):
        for a in self.agents:
            disabled = ["%s.%s" % (cid, op.get("operationId") or "?") for cid, op in self._ops(a) if op.get("isEnabled") is False]
            if disabled:
                self.add("CR5", "low", [a], "%s configured but disabled: %s. Remove what is no longer needed." % (plural(len(disabled), "operation"), capped(disabled)), operations=disabled)

    def rule_LC1(self):
        cutoff = self.opts.as_of_dt - timedelta(days=self.opts.draft_days)
        for a in self.agents:
            if a.get("published") is not False or not a.get("createdAt"):
                continue
            if a["createdAt"] <= cutoff:
                age = days_between(self.opts.as_of_dt, a["createdAt"])
                ops = self.maker_ops(a)
                severity = "medium" if ops else "low"
                detail = "Created %s (%d days ago) and never published." % (fmt_dt(a["createdAt"]), age)
                if ops:
                    detail += " It holds maker-provided connections (%s): a parked credential, not runtime exposure, until it is published." % capped(ops, 3)
                self.add("LC1", severity, [a], detail, createdAt=fmt_dt(a["createdAt"]))

    def rule_LC2(self):
        for a in self.agents:
            if a.get("isQuarantined") is True:
                since = (" since %s" % fmt_dt(a["quarantinedAt"])) if a.get("quarantinedAt") else " (date not in export)"
                self.add("LC2", "medium", [a], "Quarantined or blocked%s. Makers can still test it; it cannot be used in any channel. Decide whether to remediate and release it or delete it." % since)

    def rule_LC3(self):
        for a in self.agents:
            if a.get("isManaged") is False and self.env_type(a).lower() == "production" and self.is_published(a) and not a["isAgentBuilder"]:
                self.add("LC3", "medium", [a], "Not part of a managed solution, in the Production environment %s. Changes are made directly in production with no deployment pipeline." % self.env_label(a))

    def rule_LC4(self):
        for a in self.agents:
            if self.env_type(a).lower() != "default" or not self.is_published(a) or a["isAgentBuilder"]:
                continue
            risky = self.entire_tenant(a) or self.anonymous(a) or self.has_maker_connection(a)
            detail = "Published from the Default environment, where every licensed user holds the Environment Maker role and which cannot be deleted or reset."
            if risky:
                detail += " On the same agent: " + ", ".join(x for x in [
                    "shared with the entire tenant" if self.entire_tenant(a) else "",
                    "no user authentication" if self.anonymous(a) else "",
                    "tools on maker-provided connections" if self.has_maker_connection(a) else ""] if x) + "."
            self.add("LC4", "medium" if risky else "low", [a], detail)

    def rule_LC5(self):
        for a in self.agents:
            if self.env_type(a).lower() in ("developer", "trial") and self.is_published(a) and a["channels"]:
                self.add("LC5", "low", [a], "Published to %s from a %s environment. Developer environments are for their owner and trial environments expire; neither is a place for shared workloads." % (", ".join(a["channels"]), self.env_type(a)), envType=self.env_type(a))

    def rule_LC6(self):
        for a in self.agents:
            over = {k: v for k, v in a["capabilitiesCounts"].items() if v is not None and v > CAP_LIMIT}
            if over:
                self.add("LC6", "info", [a], "Capability counts exceed the inventory's %d-item cap (%s); the connector list in the export is incomplete. Review the agent's tools in Copilot Studio directly." % (CAP_LIMIT, ", ".join("%s=%d" % kv for kv in over.items())))

    def rule_LC7(self):
        cutoff = self.opts.as_of_dt - timedelta(days=self.opts.stale_days)
        for a in self.agents:
            if a.get("lastPublishedAt") and a["lastPublishedAt"] <= cutoff:
                self.add("LC7", "info", [a], "Last published %s (%d days ago). Confirm it is still in use and that its model, knowledge, and tools are current." % (fmt_dt(a["lastPublishedAt"]), days_between(self.opts.as_of_dt, a["lastPublishedAt"])))

    def rule_OW1(self):
        for a in self.agents:
            hit, why = self._departing(a.get("ownerId"))
            if hit:
                self.add("OW1", "high", [a], "Owner %s is %s. When the account is removed the agent has no owner and any maker-provided connection it uses stops working." % (self.owner_label(a), why))
        if self.users:
            owners = set(a.get("ownerId") for a in self.agents if a.get("ownerId"))
            unknown = [o for o in owners if o not in self.departing and (self.users.get(o) is None or self.users[o].get("enabled") is None)]
            if unknown:
                self.gaps.append("OW1: account state unknown for %d of %d owners (not in the user list, or the list has no account state for them); only owners listed as departing or marked disabled were flagged." % (len(unknown), len(owners)))

    def rule_OW2(self):
        none_populated = self.coverage.get("ownerId", {}).get("populated", 0) == 0
        for a in self.agents:
            if "ownerId" not in a["_present"] or a.get("ownerId") or not self.is_published(a):
                continue
            detail = "No owner recorded for a published agent. Assign an owner with the Power Platform API reassign operation or PowerShell."
            if none_populated:
                detail += " Every record in this export has an empty owner, so confirm that the export route carries owners (the admin center inventory and the inventory API do) before treating this as an orphaned agent."
            self.add("OW2", "medium", [a], detail)

    def rule_OW3(self):
        counts = Counter(a.get("ownerId") for a in self.agents if a.get("ownerId"))
        for oid, count in counts.most_common():
            if count < self.opts.owner_threshold:
                break
            owned = [a for a in self.agents if a.get("ownerId") == oid]
            self.add("OW3", "low", owned, "%s owns %d agents in the audited scope. Plan co-ownership or a transfer path so one departure does not orphan them." % (self.owner_label(oid), count),
                     agentName="%d agents" % count, owner=self.owner_label(oid), ownerId=oid, _attach=False)

    def rule_RG1(self):
        if not self.allowed_regions:
            self.not_evaluated["RG1"] = ["--allowed-regions not supplied"]
            return
        for a in self.agents:
            loc = (a.get("location") or "").lower()
            if loc and loc not in self.allowed_regions:
                self.add("RG1", "medium", [a], "Located in region %s, which is not in the allowed list (%s)." % (a["location"], ", ".join(sorted(self.allowed_regions))))

    def rule_MD1(self):
        for a in self.agents:
            model = (a.get("model") or "").lower()
            if model and any(word in model for word in EXTERNAL_MODEL_WORDS):
                self.add("MD1", "info", [a], "Primary model is %s. The model name alone does not establish where data is processed; Microsoft notes that some models, including several GPT models outside the US, Europe, and the UK, may process data outside the organization's geographic boundary. Confirm the model's data-processing terms against the agent's data classification." % a["model"])


# --------------------------------------------------------------------------
# Summaries and derived tables
# --------------------------------------------------------------------------


def identity_class(agent):
    if agent["isAgentBuilder"]:
        return "Agent Builder (no identity by design)"
    if agent.get("entraAgentId"):
        return "Entra Agent ID"
    if agent.get("entraAppId"):
        return "Legacy app registration"
    if agent.get("published") is False:
        return "Draft, none yet"
    return "None recorded"


def sev_counts(findings):
    counts = Counter(f["severity"] for f in findings)
    return {s: counts.get(s, 0) for s in SEVERITY_ORDER}


def env_key(agent):
    return agent.get("environmentId") or (agent.get("environmentName") or (agent.get("_env") or {}).get("name") or "").lower() or "(unknown)"


def build_summary(audit):
    agents = audit.agents
    findings = audit.findings
    by_sev = Counter(f["severity"] for f in findings)
    published = [a for a in agents if a.get("published") is True]
    drafts = [a for a in agents if a.get("published") is False]
    unknown = [a for a in agents if a.get("published") is None]

    def measure(fields, value):
        if isinstance(fields, str):
            fields = (fields,)
        return value if all(audit.field_available(f) for f in fields) else None

    summary = OrderedDict()
    summary["agents"] = len(agents)
    summary["published"] = len(published)
    summary["drafts"] = len(drafts)
    summary["publishStateUnknown"] = len(unknown)
    summary["environments"] = len(set(env_key(a) for a in agents if env_key(a) != "(unknown)"))
    summary["owners"] = len(set(a.get("ownerId") for a in agents if a.get("ownerId")))
    summary["quarantined"] = measure("isQuarantined", sum(1 for a in agents if a.get("isQuarantined") is True))
    summary["entireTenant"] = measure("sharedWithViewers", sum(1 for a in agents if audit.entire_tenant(a)))
    summary["anonymousPublished"] = measure(("authentication", "channels"), sum(1 for a in agents if audit.anonymous(a) and audit.is_published(a) and a["channels"]))
    summary["webSearch"] = measure("isWebSearchEnabledForKnowledge", sum(1 for a in agents if a.get("isWebSearchEnabledForKnowledge") is True))
    summary["findingsBySeverity"] = OrderedDict((s, by_sev.get(s, 0)) for s in SEVERITY_ORDER)
    summary["agentsWithHigh"] = sum(1 for a in agents if any(f["severity"] == "high" for f in a["_findings"]))
    summary["agentsWithHighOrMedium"] = sum(1 for a in agents if any(f["severity"] in ("high", "medium") for f in a["_findings"]))
    summary["identity"] = Counter(identity_class(a) for a in agents)
    summary["authentication"] = Counter(a.get("authentication") or "(not in export)" for a in agents)
    summary["harness"] = Counter(a["harness"] for a in agents)
    summary["harnessDerived"] = any(a["_harnessDerived"] for a in agents)
    summary["createdIn"] = Counter(a.get("createdIn") or "(not in export)" for a in agents)
    summary["orchestration"] = Counter(a.get("orchestration") or "(not in export)" for a in agents)
    summary["models"] = Counter(a.get("model") or "(not in export)" for a in agents)
    channels = Counter()
    spelling = {}
    for a in agents:
        for c in a["channels"]:
            spelling.setdefault(c.lower(), c)
            channels[c.lower()] += 1
    summary["channels"] = Counter({spelling[k]: v for k, v in channels.items()})
    summary["noChannels"] = sum(1 for a in agents if not a["channels"])
    return summary


def build_attention(audit):
    rows = []
    for a in audit.agents:
        hm = [f for f in a["_findings"] if f["severity"] in ("high", "medium")]
        if not hm:
            continue
        counts = sev_counts(a["_findings"])
        rows.append({
            "agentId": a.get("id"), "agent": audit.agent_label(a), "environment": audit.env_label(a),
            "owner": audit.owner_label(a), "ownerState": audit.owner_state(a.get("ownerId")),
            "high": counts["high"], "medium": counts["medium"], "low": counts["low"], "info": counts["info"],
            "findings": [f["id"] for f in hm], "otherFindings": [f["id"] for f in a["_findings"] if f["severity"] not in ("high", "medium")],
        })
    rows.sort(key=lambda r: (-r["high"], -r["medium"], r["agent"].lower()))
    return rows


def build_owner_work(audit):
    rows = OrderedDict()
    for a in audit.agents:
        key = a.get("ownerId") or "(no owner)"
        row = rows.setdefault(key, {"ownerId": a.get("ownerId"), "owner": audit.owner_label(a), "ownerState": audit.owner_state(a.get("ownerId")),
                                    "agentsOwned": 0, "agentsWithFindings": 0, "high": 0, "medium": 0, "agentsToActOn": [], "findings": []})
        row["agentsOwned"] += 1
        if a["_findings"]:
            row["agentsWithFindings"] += 1
        counts = sev_counts(a["_findings"])
        if counts["high"] or counts["medium"]:
            row["agentsToActOn"].append(audit.agent_label(a))
        row.setdefault("_f", {}).update({f["id"]: f for f in a["_findings"] if f["severity"] in ("high", "medium")})
    for row in rows.values():
        fs = row.pop("_f", {})
        row["high"] = sum(1 for f in fs.values() if f["severity"] == "high")
        row["medium"] = sum(1 for f in fs.values() if f["severity"] == "medium")
        row["findings"] = sorted(fs.keys(), key=lambda x: int(x[1:]))
    return sorted(rows.values(), key=lambda r: (-r["high"], -r["medium"], -r["agentsOwned"], r["owner"].lower()))


def build_environment_table(audit):
    rows = OrderedDict()
    for a in audit.agents:
        key = env_key(a)
        row = rows.setdefault(key, {"id": key, "name": audit.env_label(a), "type": audit.env_type(a) or "", "managed": (a.get("_env") or {}).get("isManaged", a.get("isManagedEnvironment")),
                                    "agents": 0, "published": None, "publishStateUnknown": 0, "agentsWithFindings": 0, "high": 0, "medium": 0,
                                    "entireTenant": None, "anonymous": None, "quarantined": None})
        row["agents"] += 1
        # A measure stays None (n/a) until an agent in the environment carries the evidence for it.
        if audit.agent_has_field(a, "lastPublishedAt"):
            row["published"] = (row["published"] or 0) + (1 if a.get("published") is True else 0)
            if a.get("published") is None:
                row["publishStateUnknown"] += 1
        if a["_findings"]:
            row["agentsWithFindings"] += 1
        counts = sev_counts(a["_findings"])
        row["high"] += counts["high"]
        row["medium"] += counts["medium"]
        if audit.agent_measure_ok(a, ("sharedWithViewers",)):
            row["entireTenant"] = (row["entireTenant"] or 0) + (1 if audit.entire_tenant(a) else 0)
        if audit.agent_measure_ok(a, ("authentication", "channels")):
            row["anonymous"] = (row["anonymous"] or 0) + (1 if audit.anonymous(a) and a["channels"] and audit.is_published(a) else 0)
        if audit.agent_measure_ok(a, ("isQuarantined",)):
            row["quarantined"] = (row["quarantined"] or 0) + (1 if a.get("isQuarantined") is True else 0)
    return sorted(rows.values(), key=lambda r: (-r["high"], -r["medium"], -r["agents"], r["name"].lower()))


def env_cell(value, unknown=0):
    if value is None:
        return "n/a"
    return "%d (+%d unknown)" % (value, unknown) if unknown else value


def build_connector_table(audit):
    rows = OrderedDict()
    for a in audit.agents:
        seen = set()
        for c in a["powerPlatformConnectors"]:
            cid = c["connectorId"]
            row = rows.setdefault(cid, {"connectorId": cid, "agents": 0, "agentIds": [], "operations": 0, "makerConnections": 0, "asKnowledge": 0, "disabled": 0, "custom": custom_connector(cid)})
            if cid not in seen:
                row["agents"] += 1
                if a.get("id"):
                    row["agentIds"].append(a["id"])
                seen.add(cid)
            for op in c["operations"]:
                row["operations"] += 1
                if str(op.get("connectionProvider", "")).lower() == "maker":
                    row["makerConnections"] += 1
                if str(op.get("usedAs", "")).lower() == "knowledge":
                    row["asKnowledge"] += 1
                if op.get("isEnabled") is False:
                    row["disabled"] += 1
    return sorted(rows.values(), key=lambda r: (-r["agents"], r["connectorId"]))


def row_key(audit, agent):
    """Environment-qualified agent key, or the label for an agent without an ID."""
    return agent_key(agent) or "name:" + audit.agent_label(agent)


def build_shared_connections(audit):
    rows = []
    for conn, agents in audit.shared_connections().items():
        items = list(agents.values())
        rows.append({
            "connectionId": conn, "agents": len(items),
            "agentIds": [a.get("id") for a, _ in items if a.get("id")],
            "agentKeys": [row_key(audit, a) for a, _ in items],
            "agentNames": [audit.agent_label(a) for a, _ in items],
            "connectorIds": sorted(set(c for _, cids in items for c in cids)),
            "ownerIds": dedupe([a.get("ownerId") for a, _ in items if a.get("ownerId")]),
            "owners": dedupe([audit.owner_label(a) for a, _ in items]),
        })
    rows.sort(key=lambda r: (-r["agents"], r["connectionId"]))
    return rows


REMEDIATION = OrderedDict([
    ("Ownership (Power Platform API reassign operation; PowerShell; Microsoft 365 admin center for shared agents)", {
        "OW1": "Reassign ownership before the account is removed; the previous owner loses access, and the new owner re-creates maker-provided connections.",
        "OW2": "Assign an owner to every published agent.",
        "OW3": "Add co-owners or document a transfer path for heavily loaded owners.",
    }),
    ("Agent identity (Copilot Studio settings; Microsoft Entra admin center; Power Platform admin center)", {
        "ID1": "Confirm each agent's identity in Copilot Studio Settings > Advanced > Metadata; if none exists, republish, then verify it under Entra ID > Agents > Agent identities in the Microsoft Entra admin center, and raise a support request if it is still absent.",
        "ID2": "Migrate legacy app-registration agents to Entra Agent IDs (Power Platform admin center Actions > Recommendations, PowerShell, or the migration API; manual migration is preview and reversible) so connector scopes and Conditional Access apply to the identity, or wait for Microsoft's automatic migration.",
    }),
    ("Authentication and channels (Copilot Studio agent settings)", {
        "EX1": "Set authentication to Microsoft Entra (or the organization's identity provider) and republish, or remove channels that admit anonymous users. Where anonymous access is intended, document it and keep tools and knowledge read-only and public.",
    }),
    ("Sharing (Copilot Studio Share; Microsoft 365 admin center; Managed Environments sharing limits)", {
        "EX2": "Confirm the sharing was intended. For store submissions check Microsoft 365 admin center > Agents > All agents > Requests; for Copilot Studio Share > Everyone, reduce viewers to named groups or accept and document it. Limit how broadly makers can share with Managed Environments sharing limits (Copilot Studio agents) or Microsoft 365 admin center Copilot settings (Agent Builder agents).",
        "EX4": "Reduce editor access to the people who maintain the agent.",
    }),
    ("Knowledge and web content (agent knowledge settings; data policies)", {
        "EX3": "Turn web search off on the agent and rely on curated knowledge sources, or confirm the audience and keep it; consider a data policy that blocks public-web knowledge where it is never acceptable.",
        "CR2": "Switch connector knowledge to user-provided connections where answers must respect each user's permissions, or restrict the agent audience to people who are entitled to the full source.",
    }),
    ("Tool connections and consent (Copilot Studio agent tools; connector and data policies)", {
        "CR1": "Switch tool connections to user-provided where the action should run as the user, or enable end-user consent, or restrict when the orchestrator may call the tool. Keep maker-provided connections only for service-style actions with a documented owner.",
        "CR3": "Document the shared connection's owner and rotation plan; prefer one connection per agent for high-impact connectors.",
        "CR4": "Review custom and watched connectors against connector and data policies; custom connectors, MCP servers, and REST tools are not represented in Entra Agent ID scopes.",
        "CR5": "Remove disabled operations that are no longer needed so the agent's footprint matches what it does.",
    }),
    ("Lifecycle (Copilot Studio; Power Platform admin center)", {
        "LC1": "Ask owners to publish, delete, or justify long-standing drafts; delete drafts whose owners do not respond.",
        "LC2": "For each quarantined or blocked agent, finish the investigation and either release it (admin center or quarantine API) or delete it.",
        "LC7": "Confirm stale agents are still used; retire the rest.",
        "LC6": "Open the agent in Copilot Studio to review its full tool list; the export is truncated.",
    }),
    ("ALM and environment strategy (solutions, pipelines, Managed Environments)", {
        "LC3": "Move production agents into managed solutions deployed through pipelines, and restrict direct editing in Production.",
        "LC4": "Move shared agents out of the Default environment into a governed environment; use Managed Environments, sharing limits, and environment routing to keep new work out of Default.",
        "LC5": "Move shared workloads out of Developer and Trial environments.",
    }),
    ("Region and model policy", {
        "RG1": "Confirm the region is acceptable or recreate the agent in an approved environment.",
        "MD1": "Confirm the model's data processing terms against the data the agent handles; switch models where the classification does not allow it.",
    }),
])

OWNER_SIDE_RULES = ("EX1", "EX3", "EX4", "CR1", "CR2", "CR4", "CR5", "LC1", "LC7", "MD1")


def remediation_for(rule):
    for group, actions in REMEDIATION.items():
        if rule in actions:
            return group, actions[rule]
    return "", ""


def build_remediation(audit):
    by_rule = defaultdict(list)
    for f in audit.findings:
        by_rule[f["rule"]].append(f)
    plan = []
    for group, actions in REMEDIATION.items():
        items = []
        for rule, action in actions.items():
            hits = by_rule.get(rule)
            if not hits:
                continue
            agent_keys = set()
            for f in hits:
                for a in f["_agents"]:
                    agent_keys.add(agent_key(a) or id(a))
            counts = sev_counts(hits)
            if rule == "OW3":
                scale = "%s (%s)" % (plural(len(hits), "owner"), plural(len(agent_keys), "agent"))
            elif rule == "CR3":
                scale = "%s (%s)" % (plural(len(hits), "connection"), plural(len(agent_keys), "agent"))
            else:
                scale = plural(len(agent_keys), "agent")
            present = [s for s in SEVERITY_ORDER if counts[s]]
            severity = present[0]
            if len(present) > 1:
                severity_text = ", ".join("%d %s" % (counts[s], s.capitalize()) for s in present)
            else:
                severity_text = severity.capitalize()
            items.append({"rule": rule, "title": RULES[rule][0], "action": action, "findings": [f["id"] for f in hits],
                          "agents": len(agent_keys), "scale": scale, "severity": severity, "severityText": severity_text})
        if items:
            items.sort(key=lambda i: (SEVERITY_ORDER[i["severity"]], i["rule"]))
            plan.append({"group": group, "items": items})
    return plan


def build_identity_migration(audit):
    return [{"agentId": a.get("id"), "agent": audit.agent_label(a), "environment": audit.env_label(a), "owner": audit.owner_label(a), "entraAppId": a.get("entraAppId")}
            for a in audit.agents if a.get("entraAppId") and not a.get("entraAgentId") and not a["isAgentBuilder"]]


# --------------------------------------------------------------------------
# Markdown rendering
# --------------------------------------------------------------------------

SEV_LABEL = {"high": "High", "medium": "Medium", "low": "Low", "info": "Info"}
MEASURE_FIELDS = {"entireTenant": ("sharedWithViewers",), "anonymousPublished": ("authentication", "channels"), "webSearch": ("isWebSearchEnabledForKnowledge",), "quarantined": ("isQuarantined",)}

LOCATION = {
    "ID1": "Copilot Studio > Settings > Advanced > Metadata; Microsoft Entra admin center > Agents",
    "ID2": "Power Platform admin center > Actions > Recommendations",
    "EX1": "Copilot Studio > Settings > Security > Authentication",
    "EX2": "Copilot Studio > Share; Microsoft 365 admin center > Agents",
    "EX3": "Copilot Studio > Knowledge",
    "EX4": "Copilot Studio > Share",
    "CR1": "Copilot Studio > Tools",
    "CR2": "Copilot Studio > Knowledge",
    "CR3": "Power Platform admin center > Environments > Connections",
    "CR4": "Power Platform admin center > Policies",
    "CR5": "Copilot Studio > Tools",
    "LC1": "Copilot Studio",
    "LC2": "Power Platform admin center > Manage > Copilot Studio",
    "LC3": "Solutions and pipelines",
    "LC4": "Power Platform admin center > Environments",
    "LC5": "Power Platform admin center > Environments",
    "LC6": "Copilot Studio > Tools",
    "LC7": "Copilot Studio > Analytics",
    "OW1": "Power Platform API reassign operation or PowerShell",
    "OW2": "Power Platform API reassign operation or PowerShell",
    "OW3": "Power Platform API reassign operation or PowerShell",
    "RG1": "Power Platform admin center > Environments",
    "MD1": "Copilot Studio > Settings > Generative AI",
}


def short_action(f):
    rule = f["rule"]
    ops = capped(f.get("operations") or [], 3)
    conns = capped(f.get("connectors") or [], 3)
    return {
        "ID1": "confirm the agent identity in Settings > Advanced > Metadata; republish if none exists",
        "ID2": "migrate the legacy app registration to an Entra Agent ID",
        "EX1": "enable Microsoft Entra authentication or remove the public channel%s" % ((" (" + capped(f.get("channels") or [], 2) + ")") if f.get("channels") else ""),
        "EX2": "confirm tenant-wide sharing is intended or narrow it to named groups",
        "EX3": "turn web search off or confirm it for this audience",
        "EX4": "reduce editor access to the maintaining team",
        "CR1": "switch %s to a user-provided connection or enable end-user consent" % (ops or "the tool operations"),
        "CR2": "switch %s knowledge to a user-provided connection" % (conns or "the connector"),
        "CR3": "document the owner of connection %s and plan its rotation" % (f.get("connectionId") or ""),
        "CR4": "review %s against connector and data policies" % (conns or "the connectors"),
        "CR5": "remove disabled operations%s" % ((" " + ops) if ops else ""),
        "LC1": "publish it or delete it; draft since %s" % (f.get("createdAt") or "creation"),
        "LC2": "finish the investigation, then release or delete",
        "LC3": "bring it into a managed solution and pipeline",
        "LC4": "move it out of the Default environment",
        "LC5": "move it out of the %s environment" % (f.get("envType") or "Developer or Trial"),
        "LC6": "review the full tool list in Copilot Studio",
        "LC7": "confirm it is still used; retire it otherwise",
        "OW1": "reassign ownership before the account is removed",
        "OW2": "assign an owner",
        "OW3": "add co-owners or document a transfer path",
        "RG1": "confirm the region or re-create the agent in an approved environment",
        "MD1": "confirm the model's data-processing terms",
    }.get(rule, remediation_for(rule)[1])


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join([" --- "] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(md_escape("" if c is None else c) for c in row) + " |")
    return "\n".join(out)


def counter_rows(counter, label):
    rows = [(k, v) for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]).lower()))]
    return table([label, "Agents"], rows) if rows else "_none_"


def yes_no(value, unknown="n/a"):
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return unknown


def shorten_id(value, limit=40):
    value = str(value)
    return value if len(value) <= limit else value[:24] + "…" + value[-8:]


def truncated_note(rows, shown, what):
    if len(rows) <= shown:
        return []
    extra = len(rows) - shown
    return ["", "… and %d more %s (see JSON or raise --max-rows)." % (extra, what if extra != 1 else what[:-1])]


def partial_text(audit):
    """Rules that ran only on the agents whose source file carries their fields."""
    parts = []
    for rule, (count, by_source, lacking) in audit.partial.items():
        where = ", ".join("%d from %s" % (n, s) for s, n in by_source.most_common())
        parts.append("%s skipped %s (%s; %s not in that file)" % (rule, plural(count, "agent"), where, ", ".join(lacking)))
    return "; ".join(parts)


def not_evaluated_text(audit):
    """Group skipped rules by cause and say what would enable them."""
    if not audit.not_evaluated:
        return "none"
    groups = OrderedDict()
    for rule, reasons in audit.not_evaluated.items():
        reason = "; ".join(reasons)
        if "connectorOperations" in reason:
            key = ("connector operation detail not in export", "re-export from the inventory API or Azure Resource Graph")
            label = rule
        elif "--allowed-regions" in reason:
            key = ("--allowed-regions not supplied", "pass --allowed-regions to check")
            label = rule
        elif "present but empty" in reason:
            key = ("field present but empty in every record", "re-export with the field populated, or check in Copilot Studio")
            label = "%s (%s)" % (rule, reason.split(" present")[0])
        elif "not in the file the audited agents" in reason:
            key = ("field not in the file the audited agents come from", "another file in the export carries it; re-export the audited agents through the inventory API or Azure Resource Graph")
            label = "%s (%s)" % (rule, reason.split(" not in")[0])
        elif "environment type" in reason:
            key = ("environment type not in export or join", "pass --environments with an environment export")
            label = rule
        elif "identity column" in reason:
            key = ("no identity column populated", "use an export that carries identity fields")
            label = rule
        elif "account state" in reason:
            key = ("no owner account state supplied", "pass --users with an account-enabled or status column, or --departing")
            label = rule
        else:
            key = ("field not in export", "use an API or Azure Resource Graph export")
            label = "%s (%s)" % (rule, reason.split(" not in export")[0])
        groups.setdefault(key, []).append(label)
    return "; ".join("%s: %s (%s)" % (", ".join(labels), reason, hint) for (reason, hint), labels in groups.items())


def scope_note(ctx):
    opts = ctx["opts"]
    if opts.environment:
        return "Scope is limited to one environment; connections and owners shared with agents outside it are not shown. Run without --environment to see every dependent."
    return ""


def render_header(ctx, brief=False):
    audit = ctx["audit"]
    opts = ctx["opts"]
    lines = ["# Agent inventory audit" + (" (brief)" if brief else ""), ""]
    rows = []
    rows.append(("Sources", "; ".join("%s (%s, %d records)" % (os.path.basename(p), shape, n) for p, shape, n in ctx["sources"])))
    scope = "%d" % len(audit.agents)
    if ctx["excluded"]:
        scope += " of %d agent records (%d outside the requested scope)" % (len(audit.agents) + ctx["excluded"], ctx["excluded"])
    rows.append(("Agents audited", scope))
    if ctx["exportComplete"] is False:
        rows.append(("Export completeness", "INCOMPLETE: a page was truncated or records are missing (see Warnings); tenant-wide statements are not supported"))
    rows.append(("Reference date (--as-of)", fmt_dt(opts.as_of_dt) + " (used for age calculations; not the export time)"))
    if not brief:
        rows.append(("Environment records in export", ctx["env_records"]))
        if ctx["other_types"]:
            rows.append(("Other resources in export", ", ".join("%d %s" % (n, t) for t, n in ctx["other_types"].most_common())))
        rows.append(("Environments joined", "%d of %d environment IDs resolved to a name" % (ctx["env_resolved"], ctx["env_total"]) if ctx["env_total"] else "none"))
        if ctx["user_count"]:
            rows.append(("Users joined", "%d records; %d of %d distinct owners resolved" % (ctx["user_count"], ctx["owners_resolved"], ctx["owners_total"])))
        else:
            rows.append(("Users joined", "none"))
        absent = audit.fields_absent()
        empty = audit.fields_empty()
        coverage = "%d of %d fields present" % (len(audit.coverage) - len(absent), len(audit.coverage))
        if absent:
            coverage += "; absent: " + ", ".join(absent)
        if empty:
            coverage += "; present but empty: " + ", ".join(empty)
        rows.append(("Field coverage", coverage))
    rows.append(("Rules not evaluated", not_evaluated_text(audit)))
    if audit.partial:
        rows.append(("Rules evaluated on part of the scope", partial_text(audit)))
    if not brief:
        rows.append(("Not visible to this audit", "instructions, knowledge content, usage, data policy evaluation results, Conditional Access state, Entra sponsors, Copilot Credits, agent evaluation results"))
    rows.append(("Tool", "agent_inventory_audit.py %s" % TOOL_VERSION))
    lines.append(table(["Item", "Value"], rows))
    lines.append("")
    note = scope_note(ctx)
    if note:
        lines.append(note)
        lines.append("")
    if ctx["warnings"]:
        lines.append("## Warnings")
        lines.append("")
        for w in ctx["warnings"]:
            lines.append("- " + w)
        lines.append("")
    return lines


def owner_cell(label, state):
    if not state:
        return label
    if label.endswith(")"):
        return label[:-1] + "; " + state + ")"
    return "%s (%s)" % (label, state)


def render_attention(ctx):
    rows = ctx["attention"]
    max_rows = ctx["opts"].max_rows
    lines = ["## Agents needing attention", ""]
    if not rows:
        lines.append("No agent has a high or medium finding under the evaluated rules.")
        lines.append("")
        return lines
    lines.append("Agents with at least one high or medium finding, worst first. Finding IDs before the dot are high or medium; after it, low and info. A shared-connection finding (CR3) counts for every agent it names; ownership concentration (OW3) appears under Findings and in the remediation plan, not per agent.")
    lines.append("")
    lines.append(table(["Agent", "Environment", "Owner", "High", "Medium", "Findings"],
                       [(r["agent"], r["environment"], owner_cell(r["owner"], r["ownerState"]), r["high"], r["medium"], " ".join(r["findings"]) + ((" · " + " ".join(r["otherFindings"])) if r["otherFindings"] else "")) for r in rows[:max_rows]]))
    lines += truncated_note(rows, max_rows, "agents")
    lines.append("")
    return lines


def render_owner_work(ctx):
    rows = ctx["ownerWork"]
    max_rows = ctx["opts"].max_rows
    lines = ["## Work by owner", ""]
    lines.append("The per-person side of the remediation plan. High and medium count distinct findings; a finding that names several of one owner's agents counts once. The last column lists high and medium finding IDs only.")
    lines.append("")
    lines.append(table(["Owner", "Agents owned", "With findings", "High", "Medium", "Agents to act on", "High and medium findings"],
                       [(owner_cell(r["owner"], r["ownerState"]), r["agentsOwned"], r["agentsWithFindings"], r["high"], r["medium"], capped(r["agentsToActOn"], 4, "; ") or "none", capped(r["findings"], 12, " ") or "none") for r in rows[:max_rows]]))
    lines += truncated_note(rows, max_rows, "owners")
    lines.append("")
    return lines


def na_text(audit, key, value):
    if value is not None:
        return value
    fields = MEASURE_FIELDS.get(key) or ()
    missing = [f for f in fields if not audit.field_available(f)]
    named = (" " + ", ".join(missing)) if len(fields) > 1 and missing else ""
    if missing and all(audit.field_present(f) for f in missing):
        return "n/a (%s empty in export)" % named.strip() if named else "n/a (empty in export)"
    return "n/a (%s not in export)" % named.strip() if named else "n/a (not in export)"


def render_measures(ctx):
    s = ctx["summary"]
    audit = ctx["audit"]
    lines = ["## Posture summary", ""]
    rows = [
        ("Agents in scope", s["agents"]),
        ("Published", s["published"]),
        ("Drafts (never published)", s["drafts"]),
    ]
    if s["publishStateUnknown"]:
        rows.append(("Publish state unknown", s["publishStateUnknown"]))
    rows += [
        ("Environments", s["environments"]),
        ("Distinct owners", s["owners"]),
        ("Shared with the entire tenant", na_text(audit, "entireTenant", s["entireTenant"])),
        ("Published without user authentication (with a channel)", na_text(audit, "anonymousPublished", s["anonymousPublished"])),
        ("Web search enabled", na_text(audit, "webSearch", s["webSearch"])),
        ("Quarantined or blocked", na_text(audit, "quarantined", s["quarantined"])),
        ("Findings: high / medium / low / info", " / ".join(str(v) for v in s["findingsBySeverity"].values())),
        ("Agents with a high finding", s["agentsWithHigh"]),
        ("Agents with a high or medium finding", s["agentsWithHighOrMedium"]),
    ]
    lines.append(table(["Measure", "Count"], rows))
    lines.append("")
    return lines


def render_profile(ctx):
    s = ctx["summary"]
    lines = ["## Inventory profile", ""]
    lines.append("### Identity coverage")
    lines.append("")
    lines.append(counter_rows(s["identity"], "Identity"))
    lines.append("")
    lines.append("### Authentication")
    lines.append("")
    lines.append(counter_rows(s["authentication"], "Authentication"))
    lines.append("")
    lines.append("### Harness and authoring tool")
    lines.append("")
    lines.append(counter_rows(s["harness"], "Harness" + (" (derived)" if s["harnessDerived"] else "")))
    lines.append("")
    lines.append(counter_rows(s["createdIn"], "Created in"))
    lines.append("")
    lines.append("### Channels")
    lines.append("")
    lines.append(counter_rows(s["channels"], "Channel"))
    if s["noChannels"]:
        lines.append("")
        lines.append("%s no channel recorded." % plural(s["noChannels"], "agent has", "agents have"))
    lines.append("")
    if any(k != "(not in export)" for k in s["models"]) or any(k != "(not in export)" for k in s["orchestration"]):
        lines.append("### Orchestration and models")
        lines.append("")
        lines.append(counter_rows(s["orchestration"], "Orchestration"))
        lines.append("")
        lines.append(counter_rows(s["models"], "Model"))
        lines.append("")
    return lines


def render_findings(ctx, severities, compact=False):
    audit = ctx["audit"]
    max_rows = ctx["opts"].max_rows
    lines = []
    for severity in severities:
        group = [f for f in audit.findings if f["severity"] == severity]
        if not group:
            continue
        lines.append("### %s (%d)" % (SEV_LABEL[severity], len(group)))
        lines.append("")
        if compact:
            by_rule = OrderedDict()
            for f in group:
                by_rule.setdefault(f["rule"], []).append(f)
            for rule, items in by_rule.items():
                agents = set()
                for f in items:
                    for a in f["_agents"]:
                        agents.add(a.get("id") or id(a))
                lines.append("- **%s %s**: %s, %s. Refs: %s." % (rule, RULES[rule][0], plural(len(items), "finding"), plural(len(agents), "agent"), capped([f["id"] for f in items], 12)))
            lines.append("")
            continue
        rows = [(f["id"], f["rule"], f.get("agentName") or f.get("agentId") or "", f.get("owner") or "", f["detail"]) for f in group[:max_rows]]
        lines.append(table(["#", "Rule", "Agent", "Owner", "Finding"], rows))
        if len(group) > max_rows:
            lines.append("")
            lines.append("… and %d more (%s). Use --json for the full list or --max-rows to show more." % (len(group) - max_rows, ", ".join(f["id"] for f in group[max_rows:max_rows + 20]) + (" …" if len(group) - max_rows > 20 else "")))
        lines.append("")
    return lines


def render_findings_section(ctx, brief):
    lines = ["## Findings", ""]
    if not ctx["audit"].findings:
        lines.append("No findings for the evaluated rules.")
        lines.append("")
        return lines
    lines.append("Rule IDs (EX1, CR1, …) are stable; finding numbers (F1, F2, …) are assigned per run.")
    lines.append("")
    lines += render_findings(ctx, ("high", "medium"))
    lines += render_findings(ctx, ("low", "info"), compact=brief)
    return lines


def render_environments(ctx):
    rows = ctx["environments"]
    max_rows = ctx["opts"].max_rows
    lines = ["## Environments", ""]
    if not rows:
        lines.append("_No environment information in the export._")
        lines.append("")
        return lines
    lines.append("Finding counts are per agent; a shared-connection finding counts once for each agent it names. n/a means no agent in that environment carries the evidence for the measure.")
    lines.append("")
    lines.append(table(["Environment", "Type", "Managed Environment", "Agents", "Published", "With findings", "High", "Medium", "Shared with entire tenant", "No user auth"],
                       [(r["name"], r["type"] or "n/a", yes_no(r["managed"]), r["agents"], env_cell(r["published"], r["publishStateUnknown"]), r["agentsWithFindings"], r["high"], r["medium"], env_cell(r["entireTenant"]), env_cell(r["anonymous"])) for r in rows[:max_rows]]))
    lines += truncated_note(rows, max_rows, "environments")
    lines.append("")
    return lines


def render_connectors(ctx):
    rows = ctx["connectors"]
    max_rows = ctx["opts"].max_rows
    detail = any(a["_connectorDetail"] for a in ctx["audit"].agents)
    lines = ["## Connector footprint", ""]
    if not rows:
        lines.append("_No connector information in the export._")
        lines.append("")
        return lines
    if detail:
        lines.append(table(["Connector", "Agents", "Operations", "Ops on maker-provided connections", "As knowledge", "Disabled", "Custom (heuristic)"],
                           [(shorten_id(r["connectorId"]), r["agents"], r["operations"], r["makerConnections"], r["asKnowledge"], r["disabled"], "yes" if r["custom"] else "") for r in rows[:max_rows]]))
    else:
        lines.append(table(["Connector", "Agents", "Custom (heuristic)"], [(shorten_id(r["connectorId"]), r["agents"], "yes" if r["custom"] else "") for r in rows[:max_rows]]))
        lines.append("")
        lines.append("The export lists connector names without operation detail, so connection provider, consent, and usage were not evaluated.")
    lines += truncated_note(rows, max_rows, "connectors")
    if any(len(r["connectorId"]) > 40 for r in rows[:max_rows]):
        lines.append("")
        lines.append("Long connector IDs are shortened here; the JSON has them in full.")
    lines.append("")
    shared = ctx["sharedConnections"]
    if shared:
        lines.append("### Maker-provided connections")
        lines.append("")
        lines.append("Connections the maker supplied, with every agent that uses them. One connection in several agents is one credential with several blast radii.")
        note = scope_note(ctx)
        if note:
            lines.append(note)
        lines.append("")
        lines.append(table(["Connection", "Agents", "Connectors", "Owners"],
                           [(r["connectionId"], "%d: %s" % (r["agents"], capped(r["agentNames"], 4, "; ")), capped([shorten_id(c) for c in r["connectorIds"]], 4), capped(r["owners"], 3, "; ")) for r in shared[:max_rows]]))
        lines += truncated_note(shared, max_rows, "connections")
        lines.append("")
    return lines


def render_remediation(ctx, brief=False):
    lines = ["## Remediation plan", ""]
    if not ctx["remediation"]:
        lines.append("Nothing to remediate for the evaluated rules.")
        lines.append("")
        return lines
    if brief:
        for group in ctx["remediation"]:
            for item in group["items"]:
                lines.append("- **%s %s** (%s, %s): %s Refs: %s." % (item["rule"], item["title"], item["severityText"], item["scale"], item["action"].split(". ")[0].rstrip(".") + ".", capped(item["findings"], 8)))
        lines.append("")
        return lines
    lines.append("Grouped by the control that fixes each rule. Ownership comes first: on agents with OW1 or OW2, nobody else can act until an owner exists. The work-by-owner table below gives the per-person list.")
    lines.append("")
    for group in ctx["remediation"]:
        lines.append("### " + group["group"])
        lines.append("")
        for item in group["items"]:
            lines.append("- **%s %s** — %s, %s. %s Refs: %s." % (item["rule"], item["title"], item["severityText"], item["scale"], item["action"], capped(item["findings"], 15)))
        lines.append("")
    return lines


def render_method(ctx):
    lines = ["## Method and limits", ""]
    lines.append("- Source: Power Platform inventory records of type %s. The inventory reflects each agent's last published version; unpublished edits are not visible. Classic chatbots (V1) are not in the inventory." % AGENT_TYPE)
    lines.append("- Severity is a review heuristic from this script's rule catalog, not a Microsoft rating or a compliance verdict. Each finding names what to verify in the live tenant.")
    lines.append("- Rules are evaluated only when the export contains populated values for the fields they need; rules listed as not evaluated say nothing about the tenant. Measures shown as n/a could not be computed from this export.")
    if ctx["summary"]["harnessDerived"]:
        lines.append("- Harness was derived from isCLIAgent, model, and createdIn for some agents because the export has no harness field.")
    lines.append("- Connector detail (provider, consent, usage) is Preview data and is capped at %d resources of each type per agent. The custom-connector test is a heuristic on the connector ID; the watch list is the authoritative check." % CAP_LIMIT)
    lines.append("- The inventory does not show knowledge sources other than connectors and web search, topic content, instructions, data policy results, usage, or Copilot Credits consumption. Those need Copilot Studio, the admin center, or Agent 365 reports.")
    lines.append("- Owner and creator names come from the supplied user list or from the export's own owner column; otherwise object IDs are shown.")
    lines.append("- Drafts: %d days; stale: %d days; owner concentration: %d agents; editor threshold: %d. Reference date: %s." % (ctx["opts"].draft_days, ctx["opts"].stale_days, ctx["opts"].owner_threshold, ctx["opts"].editor_threshold, fmt_dt(ctx["opts"].as_of_dt)))
    lines.append("")
    return lines


def agent_id_rows(audit, agents):
    return [(audit.agent_label(a), a["id"], audit.env_label(a)) for a in sorted(agents, key=lambda a: audit.agent_label(a).lower()) if a.get("id")]


def render_agent_ids(ctx, agents=None, title="Agents named in findings, for cross-reference with Copilot Studio and the admin center."):
    audit = ctx["audit"]
    agents = agents if agents is not None else [a for a in audit.agents if a["_findings"]]
    rows = agent_id_rows(audit, agents)
    if not rows:
        return []
    lines = ["## Agent IDs", "", title, ""]
    lines.append(table(["Agent", "Agent ID", "Environment"], rows[:ctx["opts"].max_rows * 4]))
    lines += truncated_note(rows, ctx["opts"].max_rows * 4, "agents")
    lines.append("")
    return lines


def share_text(share):
    if share.get("userCount") is None and share.get("groupCount") is None:
        return "not in export"
    return "%s, %s" % (plural(share.get("userCount") or 0, "user"), plural(share.get("groupCount") or 0, "group"))


def viewers_text(agent):
    return "entire tenant" if agent["sharedWithViewers"].get("entireTenant") else share_text(agent["sharedWithViewers"])


def actions_for(audit, findings):
    """Return (owner_actions, admin_actions): lists of dicts with rule, title, action, and finding refs."""
    owner, admin = OrderedDict(), OrderedDict()
    for f in findings:
        target = owner if f["rule"] in OWNER_SIDE_RULES else admin
        entry = target.setdefault(f["rule"], {"rule": f["rule"], "title": RULES[f["rule"]][0], "action": remediation_for(f["rule"])[1], "refs": []})
        entry["refs"].append(f["id"])
    admin_items = sorted(admin.values(), key=lambda e: (0 if e["rule"] in ("OW1", "OW2") else 1, e["rule"]))
    return list(owner.values()), admin_items


CHECK_IN_STUDIO = ("Settings > Advanced > Metadata (identity)", "Settings > Security > Authentication", "each tool's connection and consent settings",
                   "knowledge sources and their connections", "the Channels page", "the Share panel", "Analytics (usage and reactions)", "evaluation results",
                   "data policy evaluation in the Power Platform admin center")

RUN_NOTE = "Finding numbers (F1, F2, …) are assigned per run and differ between reports; cross-reference by rule ID (CR1, EX2, …)."


def render_dossier(ctx, agent):
    audit = ctx["audit"]
    opts = ctx["opts"]
    env = agent.get("_env") or {}
    lines = ["# Agent dossier: %s" % md_escape(audit.agent_label(agent)), ""]
    header = "Source: %s. Reference date %s (not the export time). Tool %s." % ("; ".join(os.path.basename(p) for p, _, _ in ctx["sources"]), fmt_dt(opts.as_of_dt), TOOL_VERSION)
    if audit.not_evaluated:
        header += " Not evaluated: %s." % not_evaluated_text(audit)
    skipped_for = [rule for rule in audit.partial if rule not in audit.not_evaluated and not audit.agent_eligible(agent, rule)]
    if skipped_for:
        header += " Not evaluated for this agent because its source file lacks the fields: %s." % ", ".join(skipped_for)
    if ctx["exportComplete"] is False:
        header += " EXPORT INCOMPLETE: a page was truncated, so shared-connection dependents and owner counts may be missing."
    lines.append(header)
    lines.append("")
    lines.append(RUN_NOTE)
    lines.append("")
    owner_state = audit.owner_state(agent.get("ownerId"))
    creator = audit.users.get((agent.get("createdBy") or "").lower(), {}).get("name") or agent.get("createdBy") or "?"
    published = fmt_dt(agent.get("lastPublishedAt"))
    if published:
        published += " (%d days ago)" % days_between(opts.as_of_dt, agent["lastPublishedAt"])
    elif agent.get("published") is False:
        published = "never"
    else:
        published = "not in export"
    env_type = (audit.env_type(agent) or "type unknown")
    if env.get("isManaged") is True:
        env_type += "; a Managed Environment"
    elif env.get("isManaged") is False:
        env_type += "; not a Managed Environment"
    if env.get("group"):
        env_type += "; group " + env["group"]
    rows = [
        ("Agent ID", agent.get("id")),
        ("Schema name", agent.get("schemaName")),
        ("Environment", audit.env_label(agent)),
        ("Environment type", env_type),
        ("Region", agent.get("location")),
        ("Owner", owner_cell(audit.owner_label(agent), owner_state)),
        ("Created", "%s by %s" % (fmt_dt(agent.get("createdAt")), creator)),
        ("Created in", agent.get("createdIn")),
        ("Harness", agent["harness"] + (" (derived)" if agent["_harnessDerived"] else "")),
        ("Last published", published),
        ("In managed solution", yes_no(agent.get("isManaged"))),
        ("Quarantined or blocked", yes_no(agent.get("isQuarantined")) + ((" since " + fmt_dt(agent.get("quarantinedAt"))) if agent.get("quarantinedAt") else "")),
        ("Identity", identity_class(agent) + (": " + (agent.get("entraAgentId") or agent.get("entraAppId") or "") if (agent.get("entraAgentId") or agent.get("entraAppId")) else "")),
        ("Blueprint", agent.get("entraAgentBlueprintId") or "none recorded"),
        ("Orchestration", agent.get("orchestration")),
        ("Model", agent.get("model")),
        ("Authentication", agent.get("authentication") or "not in export"),
        ("Channels", ", ".join(agent["channels"]) or "none recorded"),
        ("Viewers", viewers_text(agent)),
        ("Editors", share_text(agent["sharedWithEditors"])),
        ("Web search knowledge", yes_no(agent.get("isWebSearchEnabledForKnowledge"))),
        ("Capability counts", ", ".join("%s=%s" % kv for kv in agent["capabilitiesCounts"].items()) or "none"),
    ]
    lines.append(table(["Field", "Value"], [(k, "n/a" if v is None else v) for k, v in rows]))
    lines.append("")
    lines.append("## Connectors")
    lines.append("")
    shared = {r["connectionId"]: r for r in ctx["sharedConnections"]}
    if not agent["powerPlatformConnectors"]:
        lines.append("_None recorded._")
    elif agent["_connectorDetail"]:
        op_rows = []
        conns = OrderedDict()
        for c in agent["powerPlatformConnectors"]:
            if not c["operations"]:
                op_rows.append((c["connectorId"], "(no operations listed)", "", "", "", "", ""))
            for op in c["operations"]:
                conn = op.get("connectionIdSharedByMaker", "") or ""
                if conn:
                    conns.setdefault(conn, set()).add(c["connectorId"])
                op_rows.append((c["connectorId"], op.get("operationId", ""), op.get("usedAs", ""), yes_no(op.get("isEnabled")), op.get("whenCanBeUsed", "") or "n/a", op.get("connectionProvider", "") or "n/a", yes_no(op.get("requiresEndUserConsent"))))
        lines.append(table(["Connector", "Operation", "Used as", "Enabled", "Orchestrator may call", "Connection", "End-user consent"], op_rows))
        for conn, cids in conns.items():
            others = [n for n in shared.get(conn, {}).get("agentNames", []) if n != audit.agent_label(agent)]
            lines.append("")
            lines.append("Maker-provided connection %s backs %s%s." % (conn, capped(sorted(cids), 3), (", and is also used by " + capped(others, 3, "; ")) if others else ""))
    else:
        lines.append(", ".join(c["connectorId"] for c in agent["powerPlatformConnectors"]))
        lines.append("")
        lines.append("Operation detail (provider, consent, usage) is not in this export.")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    mine = agent["_findings"]
    if mine:
        lines.append(table(["#", "Severity", "Rule", "Finding"], [(f["id"], SEV_LABEL[f["severity"]], "%s %s" % (f["rule"], f["title"]), f["detail"]) for f in mine]))
    else:
        lines.append("No findings for the evaluated rules.")
    lines.append("")
    owner_actions, admin_actions = actions_for(audit, mine)
    if owner_actions or admin_actions:
        lines.append("## Recommended actions")
        lines.append("")
        if admin_actions:
            lines.append("**Administrators**" + (" (ownership first: the owner's account is disabled)" if owner_state == "account disabled" else (" (ownership first: the owner is departing)" if owner_state else "")))
            lines.append("")
            for e in admin_actions:
                lines.append("- %s %s: %s Refs: %s." % (e["rule"], e["title"], e["action"], ", ".join(e["refs"])))
            lines.append("")
        if owner_actions:
            lines.append("**Agent owner**" + (" (the new owner, after the transfer)" if owner_state or not agent.get("ownerId") else ""))
            lines.append("")
            for e in owner_actions:
                lines.append("- %s %s: %s Refs: %s." % (e["rule"], e["title"], e["action"], ", ".join(e["refs"])))
            lines.append("")
    lines.append("## Check in Copilot Studio and the admin center (not in the inventory)")
    lines.append("")
    for item in CHECK_IN_STUDIO:
        lines.append("- " + item)
    lines.append("")
    return lines


def render_handover(ctx, owner_key):
    audit = ctx["audit"]
    opts = ctx["opts"]
    owned = [a for a in audit.agents if (a.get("ownerId") or "") == owner_key]
    label = audit.owner_label(owner_key)
    state = audit.owner_state(owner_key)
    lines = ["# Owner handover: %s" % md_escape(label), ""]
    header = "Matched on owner key `%s`%s. Source: %s. Reference date %s (not the export time). Tool %s." % (
        owner_key, (", " + state) if state else "", "; ".join(os.path.basename(p) for p, _, _ in ctx["sources"]), fmt_dt(opts.as_of_dt), TOOL_VERSION)
    if audit.not_evaluated:
        header += " Not evaluated: %s." % not_evaluated_text(audit)
    if audit.partial:
        header += " Rules evaluated on part of the scope: %s." % partial_text(audit)
    if ctx["exportComplete"] is False:
        header += " EXPORT INCOMPLETE: a page was truncated, so agents this owner holds and the agents that depend on their connections may be missing from this list."
    lines.append(header)
    lines.append("")
    lines.append(RUN_NOTE)
    lines.append("")
    lines.append("## Agents owned (%d)" % len(owned))
    lines.append("")
    rows = []

    def top_finding(a):
        others = [f for f in a["_findings"] if f["rule"] != "OW1"]
        return others[0] if others else None
    for a in sorted(owned, key=lambda a: (SEVERITY_ORDER[top_finding(a)["severity"]] if top_finding(a) else 9, audit.agent_label(a).lower())):
        top = top_finding(a)
        rows.append((audit.agent_label(a), audit.env_label(a), "yes" if a.get("published") is True else ("no" if a.get("published") is False else "n/a"),
                     ", ".join(a["channels"]) or "none", viewers_text(a), ("%s (%s)" % (top["rule"], SEV_LABEL[top["severity"]])) if top else "none", " ".join(f["id"] for f in a["_findings"])))
    lines.append(table(["Agent", "Environment", "Published", "Channels", "Viewers", "Highest finding besides ownership", "Findings"], rows) if rows else "_No agents owned by this key in the audited scope._")
    lines.append("")
    lines.append("## Shared connections and dependents")
    lines.append("")
    owned_keys = set(row_key(audit, a) for a in owned)
    conn_rows = []
    for r in ctx["sharedConnections"]:
        if not any(k in owned_keys for k in r["agentKeys"]):
            continue
        others = [n for k, n in zip(r["agentKeys"], r["agentNames"]) if k not in owned_keys]
        conn_rows.append((r["connectionId"], capped([shorten_id(c) for c in r["connectorIds"]], 4), "%d: %s" % (r["agents"], capped(r["agentNames"], 4, "; ")), capped(others, 4, "; ") or "none", capped([o for o in r["owners"] if o != label], 3, "; ") or "none"))
    if conn_rows:
        lines.append("Maker-provided connections in this owner's agents. The inventory records which connection is shared, not who owns it; if it is this person's, every listed agent stops when the account is removed.")
        note = scope_note(ctx)
        if note:
            lines.append(note)
        lines.append("")
        lines.append(table(["Connection", "Connectors", "Used by", "Other agents depending on it", "Other owners"], conn_rows))
    elif any(a["_connectorDetail"] for a in audit.agents):
        lines.append("No maker-provided connections recorded in this owner's agents.")
    else:
        lines.append("Connector operation detail is not in this export, so shared connections could not be determined.")
    lines.append("")
    created = []
    for a in audit.agents:
        if (a.get("ownerId") or "") == owner_key:
            continue
        for cid, op in audit._ops(a):
            if op.get("createdBy") and op["createdBy"] == owner_key:
                created.append((audit.agent_label(a), audit.owner_label(a), "%s.%s" % (cid, op.get("operationId") or "?"), op.get("connectionProvider", "")))
    lines.append("## Operations this person configured in other owners' agents")
    lines.append("")
    if created:
        lines.append(table(["Agent", "Owner", "Operation", "Connection"], created[:opts.max_rows]))
        lines += truncated_note(created, opts.max_rows, "operations")
    else:
        lines.append("None recorded (matched on the operation's createdBy field against the owner key).")
    lines.append("")
    lines.append("## Not visible in the inventory")
    lines.append("")
    not_visible = ["editor seats this person holds on other agents (only counts are exported)", "flows, connections, and apps outside these agents",
                   "whether this person's connections still authenticate today", "group memberships behind shared viewer or editor groups"]
    if not audit.users:
        not_visible.insert(3, "whether the account is already disabled (no user list was supplied)")
    for item in not_visible:
        lines.append("- " + item)
    lines.append("")
    lines.append("## Actions before the departure")
    lines.append("")
    action_rows = []
    if owned:
        action_rows.append(("1", "Reassign ownership of %s to named owners, or delete drafts nobody needs. The previous owner loses access." % capped([audit.agent_label(a) for a in owned], 4, "; "), "Power Platform admin", LOCATION["OW1"] + "; Microsoft 365 admin center for shared agents"))
    if conn_rows:
        action_rows.append(("2", "Identify the owner of %s; if this person's, re-create it under the new owner or a service account in every dependent agent." % capped([r[0] for r in conn_rows], 3), "Power Platform admin; dependent agents' owners", LOCATION["CR3"] + "; Copilot Studio > Tools"))
    per_finding = []
    seen = set()
    for a in owned:
        for f in a["_findings"]:
            if f["rule"] in ("OW1", "OW3", "CR3") or f["id"] in seen:
                continue
            seen.add(f["id"])
            who = "New owner" if f["rule"] in OWNER_SIDE_RULES else "Power Platform admin"
            per_finding.append((SEVERITY_ORDER[f["severity"]], int(f["id"][1:]), "%s %s: %s (%s)." % (f["rule"], audit.agent_label(a), short_action(f), f["id"]), who, LOCATION.get(f["rule"], "")))
    for _, _, action, who, where in sorted(per_finding):
        action_rows.append(("", action, who, where))
    action_rows = [(str(i),) + row[1:] for i, row in enumerate(action_rows, 1)]
    lines.append(table(["Order", "Action", "Who", "Where"], action_rows) if action_rows else "Nothing to do from the inventory for this owner.")
    lines.append("")
    lines += render_agent_ids(ctx, owned, "This owner's agents, for cross-reference with Copilot Studio and the admin center.")
    return lines


def render_brief(ctx):
    audit = ctx["audit"]
    s = ctx["summary"]
    lines = render_header(ctx, brief=True)
    lines.append("%s: %s across %s; %s attention." % (
        plural(len(audit.findings), "finding"), ", ".join("%d %s" % (v, k) for k, v in s["findingsBySeverity"].items()),
        plural(s["agents"], "agent"), plural(s["agentsWithHighOrMedium"], "agent needs", "agents need")))
    lines.append("")
    lines += render_attention(ctx)
    if audit.findings:
        lines.append("## Findings")
        lines.append("")
        lines.append("Rule IDs are stable; finding numbers are assigned per run.")
        lines.append("")
        for severity in ("high", "medium"):
            group = [f for f in audit.findings if f["severity"] == severity]
            if not group:
                continue
            lines.append("### %s (%d)" % (SEV_LABEL[severity], len(group)))
            lines.append("")
            lines.append(table(["#", "Agent", "Finding"], [(f["id"], f.get("agentName") or f.get("agentId") or "", "%s: %s" % (f["rule"], f["detail"])) for f in group[:ctx["opts"].max_rows]]))
            lines += truncated_note(group, ctx["opts"].max_rows, "findings")
            lines.append("")
        lines += render_findings(ctx, ("low", "info"), compact=True)
    lines += render_remediation(ctx, brief=True)
    lines.append("## Method")
    lines.append("")
    lines.append("Brief report. Owner, environment, connector, and profile tables, the full remediation text, and agent IDs are in the full report (run without --brief) and in the JSON. Severity is this script's review heuristic, not a Microsoft rating or a compliance verdict.")
    lines.append("")
    return lines


def render_markdown(ctx):
    if ctx["dossier"]:
        return "\n".join(render_dossier(ctx, ctx["dossier"]))
    if ctx["handover"] is not None:
        return "\n".join(render_handover(ctx, ctx["handover"]))
    if ctx["opts"].brief:
        return "\n".join(render_brief(ctx))
    lines = []
    lines += render_header(ctx)
    lines += render_measures(ctx)
    lines += render_attention(ctx)
    lines += render_findings_section(ctx, False)
    lines += render_remediation(ctx)
    lines += render_owner_work(ctx)
    lines += render_environments(ctx)
    lines += render_connectors(ctx)
    lines += render_profile(ctx)
    lines += render_agent_ids(ctx)
    lines += render_method(ctx)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# JSON output
# --------------------------------------------------------------------------


def agent_to_json(agent):
    out = {}
    for key, value in agent.items():
        if key.startswith("_"):
            continue
        if isinstance(value, datetime):
            value = value.astimezone(timezone.utc).isoformat()
        out[key] = value
    env = agent.get("_env")
    if env:
        out["environment"] = env
    out["harnessDerived"] = agent["_harnessDerived"]
    out["connectorDetail"] = agent["_connectorDetail"]
    out["identityClass"] = identity_class(agent)
    out["findings"] = [f["id"] for f in agent["_findings"]]
    out["severityCounts"] = sev_counts(agent["_findings"])
    return out


def finding_to_json(f):
    return OrderedDict((k, v) for k, v in f.items() if not k.startswith("_"))


def build_json(ctx):
    audit = ctx["audit"]

    def counter_dict(counter):
        return OrderedDict(sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0]))))
    summary = OrderedDict()
    for key, value in ctx["summary"].items():
        summary[key] = counter_dict(value) if isinstance(value, Counter) else value
    out = OrderedDict([
        ("tool", "agent_inventory_audit.py"),
        ("version", TOOL_VERSION),
        ("generatedAt", datetime.now(timezone.utc).isoformat()),
        ("referenceDate", ctx["opts"].as_of_dt.isoformat()),
        ("sources", [{"path": p, "shape": s, "records": n} for p, s, n in ctx["sources"]]),
        ("scope", {"environmentFilter": ctx["opts"].environment, "agentFilter": ctx["opts"].agent, "ownerFilter": ctx["opts"].owner, "excluded": ctx["excluded"]}),
        ("warnings", ctx["warnings"]),
        ("exportComplete", ctx["exportComplete"]),
        ("partiallyEvaluated", OrderedDict((r, {"agentsSkipped": c, "bySource": dict(b), "fieldsMissing": l}) for r, (c, b, l) in audit.partial.items())),
        ("fieldCoverage", audit.coverage),
        ("fieldsAbsent", audit.fields_absent()),
        ("fieldsPresentButEmpty", audit.fields_empty()),
        ("rulesNotEvaluated", audit.not_evaluated),
        ("rules", OrderedDict((k, {"title": v[0], "category": v[1]}) for k, v in RULES.items())),
        ("summary", summary),
        ("attention", ctx["attention"]),
        ("ownersWork", ctx["ownerWork"]),
        ("findings", [finding_to_json(f) for f in audit.findings]),
        ("environments", ctx["environments"]),
        ("connectors", ctx["connectors"]),
        ("sharedConnections", ctx["sharedConnections"]),
        ("identityMigration", ctx["identityMigration"]),
        ("remediation", ctx["remediation"]),
        ("agents", [agent_to_json(a) for a in audit.agents]),
    ])
    if ctx["dossier"]:
        out["dossier"] = {"agentId": ctx["dossier"].get("id"), "agent": audit.agent_label(ctx["dossier"]), "findings": [f["id"] for f in ctx["dossier"]["_findings"]]}
    if ctx["handover"] is not None:
        owned = [a for a in audit.agents if (a.get("ownerId") or "") == ctx["handover"]]
        out["handover"] = {"ownerKey": ctx["handover"], "owner": audit.owner_label(ctx["handover"]), "agentIds": [a.get("id") for a in owned if a.get("id")]}
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def match_agent(agents, needle):
    low = needle.strip().lower()
    exact = [a for a in agents if (a.get("id") or "").lower() == low or (a.get("displayName") or "").lower() == low]
    if len(exact) == 1:
        return exact[0], None
    if len(exact) > 1:
        if len(set((a.get("id") or "").lower() for a in exact)) == 1:
            return None, "Agent ID %s exists in %d environments (%s); add --environment to pick one." % (exact[0].get("id"), len(exact), ", ".join(dedupe([(a.get("_env") or {}).get("name") or a.get("environmentId") or "?" for a in exact])))
        return None, "%d agents match '%s' exactly (%s); use the agent ID." % (len(exact), needle, "; ".join(a.get("id") or "?" for a in exact[:10]))
    partial = [a for a in agents if low in (a.get("displayName") or "").lower()]
    if len(partial) == 1:
        return partial[0], None
    if not partial:
        return None, "No agent matches '%s'." % needle
    return None, "%d agents contain '%s': %s. Use the agent ID." % (len(partial), needle, "; ".join((a.get("displayName") or a.get("id")) for a in partial[:10]))


def match_environment(agents, needle):
    low = needle.strip().lower()
    by_id = [a for a in agents if (a.get("environmentId") or "") == low]
    if by_id:
        return by_id, None
    exact_ids = set(a.get("environmentId") or a["_env"].get("name") for a in agents if (a["_env"].get("name") or "").lower() == low)
    if len(exact_ids) > 1:
        return None, "%d environments are named '%s' (%s); use the environment ID." % (len(exact_ids), needle, ", ".join(sorted(str(x) for x in exact_ids)))
    if exact_ids:
        return [a for a in agents if (a["_env"].get("name") or "").lower() == low], None
    partial_ids = set(a.get("environmentId") or a["_env"].get("name") for a in agents if low in (a["_env"].get("name") or "").lower())
    if len(partial_ids) == 1:
        return [a for a in agents if low in (a["_env"].get("name") or "").lower()], None
    if not partial_ids:
        return None, "no agents in environment '%s'" % needle
    return None, "%d environments contain '%s'; use the environment ID." % (len(partial_ids), needle)


def match_owner(agents, users, needle):
    low = needle.strip().lower()
    keys = set(a.get("ownerId") for a in agents if a.get("ownerId"))
    if low in keys:
        return low, None
    user = users.get(low)
    if user:
        for candidate in (user.get("id"), user.get("upn"), (user.get("name") or "").lower()):
            if candidate and candidate in keys:
                return candidate, None
    by_name = [k for k in keys if (users.get(k, {}).get("name") or "").lower() == low or (users.get(k, {}).get("upn") or "") == low]
    if len(by_name) == 1:
        return by_name[0], None
    partial = [k for k in keys if low in (users.get(k, {}).get("name") or "").lower() or low in k]
    if len(partial) == 1:
        return partial[0], None
    if len(partial) > 1:
        return None, "%d owners match '%s'; use the object ID." % (len(partial), needle)
    return None, "No owner matches '%s' in the audited scope (owner keys are object IDs unless the export or a user list carries names)." % needle


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit a Power Platform agent inventory export for governance posture.")
    parser.add_argument("inventory", nargs="+", help="inventory export file(s): JSON or CSV")
    parser.add_argument("--md", help="write the Markdown report to this file (default: stdout)")
    parser.add_argument("--json", dest="json_path", help="write the JSON report to this file")
    parser.add_argument("--environments", help="environment list (JSON or CSV) to resolve environment names and types")
    parser.add_argument("--users", help="user list (JSON or CSV) with object IDs, UPNs, names, and account state")
    parser.add_argument("--departing", help="comma-separated owner object IDs or UPNs that are leaving (UPNs need --users)")
    parser.add_argument("--environment", help="restrict the audit to one environment (ID or name)")
    parser.add_argument("--agent", help="produce a dossier for one agent (ID or display name)")
    parser.add_argument("--owner", help="produce an owner handover for one owner (object ID, UPN, or name)")
    parser.add_argument("--brief", action="store_true", help="chat-sized report: short header, one summary line, attention table, high and medium findings, one line per low or info rule, one-line-per-rule remediation plan")
    parser.add_argument("--draft-days", type=int, default=90, help="age in days after which an unpublished draft is reported (default 90)")
    parser.add_argument("--stale-days", type=int, default=365, help="days since last publish after which an agent is reported as stale (default 365)")
    parser.add_argument("--owner-threshold", type=int, default=15, help="agents per owner that triggers the concentration finding (default 15)")
    parser.add_argument("--editor-threshold", type=int, default=5, help="individual editors that triggers the broad editor finding (default 5)")
    parser.add_argument("--as-of", help="reference date YYYY-MM-DD for age calculations (default: today, UTC)")
    parser.add_argument("--allowed-regions", help="comma-separated inventory location values that are approved (enables RG1)")
    parser.add_argument("--watch-connectors", help="comma-separated connector IDs or fragments to flag wherever used")
    parser.add_argument("--max-rows", type=int, default=25, help="rows per table before truncation (default 25)")
    opts = parser.parse_args(argv)

    if opts.as_of:
        as_of = parse_dt(opts.as_of)
        if not as_of:
            parser.error("--as-of must be a date such as 2026-10-16")
        opts.as_of_dt = as_of
    else:
        opts.as_of_dt = datetime.now(timezone.utc)

    warnings = []
    sources = []
    raw_agents = []
    env_map = {}
    env_records = 0
    other_types = Counter()

    page_files = OrderedDict()  # absolute path -> {"keys", "nokey", "meta"} for API-shaped files, to judge completeness
    for path in opts.inventory:
        if not os.path.isfile(path):
            parser.error("not a file: %s" % path)
        records, shape, meta = load_file(path)
        sources.append((path, shape, len(records)))
        source_id = os.path.abspath(path)  # full path, so inventory.csv in two folders are two sources
        if meta:
            page_files[source_id] = {"keys": set(), "nokey": 0, "meta": meta}
        if not records:
            warnings.append("%s: no records recognized (%s)." % (os.path.basename(path), shape))
            continue
        for raw in records:
            rec = normalize_record(raw, source_id)
            if meta:
                if agent_key(rec):
                    page_files[source_id]["keys"].add(agent_key(rec))
                else:
                    page_files[source_id]["nokey"] += 1
            if looks_like_environment(rec):
                env = environment_from_record(raw)
                if env:
                    env_records += 1
                    env_map[env["id"]] = env
                continue
            if looks_like_agent(rec):
                raw_agents.append(rec)
            else:
                other_types[rec["type"]] += 1

    export_complete = None  # None: no pagination evidence; True/False otherwise
    if page_files:
        # Pages of one query share its totalRecords, so completeness is judged per total: distinct resources
        # supplied by that group of files against that total. Records from another query cannot fill the gap.
        groups = OrderedDict()
        for source_id, info in page_files.items():
            total = info["meta"].get("totalRecords")
            group = groups.setdefault(total, {"keys": set(), "nokey": 0, "files": [], "truncated": []})
            group["keys"] |= info["keys"]
            group["nokey"] += info["nokey"]
            group["files"].append(os.path.basename(source_id))
            if info["meta"].get("truncated"):
                group["truncated"].append(os.path.basename(source_id))
        problems = []
        for total, group in groups.items():
            supplied = len(group["keys"]) + group["nokey"]
            n_files, n_trunc = len(group["files"]), len(group["truncated"])
            if total is not None and supplied >= total:
                # One query's pages are n-1 truncated pages plus a final one; several complete single pages have none.
                if n_trunc == 0 or n_trunc == n_files - 1:
                    continue
                problems.append("%s share totalRecords=%d but %d of %d pages are truncated, so they look like pages of different queries that are each missing their final page (%d distinct records supplied)" % (
                    ", ".join(group["files"]), total, n_trunc, n_files, supplied))
                continue
            if group["truncated"]:
                problems.append("%s %s a truncated page (resultTruncated or skipToken set)%s" % (
                    ", ".join(group["truncated"]), "is" if len(group["truncated"]) == 1 else "are",
                    " with %d of %d distinct records supplied" % (supplied, total) if total is not None else ""))
            elif total is not None:
                problems.append("%s supplied %d of %d distinct records (totalRecords in the page header)" % (", ".join(group["files"]), supplied, total))
        export_complete = not problems
        if problems:
            warnings.append("Export incomplete: %s. Request the remaining pages with skipToken and pass all page files together before drawing tenant-wide conclusions. Ownership counts, shared-connection dependencies, and owner handovers cover only the records supplied." % "; ".join(problems))

    if opts.environments:
        records, _, _ = load_file(opts.environments)
        for raw in records:
            env = environment_from_record(raw)
            if env:
                env_map.setdefault(env["id"], {}).update({k: v for k, v in env.items() if v is not None})

    users = load_users(opts.users) if opts.users else {}

    # Resolve environment names to IDs before de-duplication, so an admin center CSV row (environment by name)
    # and an API record (environment by ID) for the same agent share a key.
    name_to_id = {}
    for eid, env in env_map.items():
        if env.get("name"):
            name_to_id.setdefault(env["name"].lower(), set()).add(eid)
    for rec in raw_agents:
        if not rec.get("environmentId") and rec.get("environmentName"):
            ids = name_to_id.get(rec["environmentName"].lower())
            if ids and len(ids) == 1:
                rec["environmentId"] = next(iter(ids))
                rec["_present"].add("environmentId")

    # Per-file coverage is measured before merging, so enrichment of one agent by another file is not
    # attributed to the file that lacked the field.
    source_coverage = OrderedDict()
    for source in dedupe([r["_source"] for r in raw_agents]):
        source_coverage[source] = coverage_of([r for r in raw_agents if r["_source"] == source])

    agents = []
    seen = {}
    by_bare_id = {}  # bare agent ID -> kept records, for records whose environment is unknown
    for rec in raw_agents:
        key = agent_key(rec)
        first = seen.get(key) if key else None
        if first is None and rec.get("id"):
            # A record with no environment (or a candidate with none) merges into the only record with that ID.
            candidates = by_bare_id.get(rec["id"].lower(), [])
            if len(candidates) == 1 and (not env_identity(rec) or not env_identity(candidates[0])):
                first = candidates[0]
        if first is not None:
            if first.get("_harnessDerived"):
                first["harness"] = None  # let an explicit harness from the second record win over an inferred one
            for field in FIELD_ALIASES:
                if field not in rec["_present"]:
                    continue
                if field == "powerPlatformConnectors":
                    first["_present"].add(field)  # values are merged below; the column still counts as present
                    continue
                if field not in first["_present"] or field_blank(field, first.get(field)):
                    if not field_blank(field, rec.get(field)) or field not in first["_present"]:
                        first[field] = rec[field]
                        if field == "lastPublishedAt":
                            first["_rawLastPublished"] = rec.get("_rawLastPublished")
                    first["_present"].add(field)
            first["_sources"] |= rec["_sources"]
            if (rec["_connectorDetail"] and not first["_connectorDetail"]) or (rec["powerPlatformConnectors"] and not first["powerPlatformConnectors"]):
                first["powerPlatformConnectors"] = rec["powerPlatformConnectors"]
                first["_connectorDetail"] = first["_connectorDetail"] or rec["_connectorDetail"]
                if first["_connectorDetail"]:
                    first["_present"].add("connectorOperations")
            finalize(first)
            seen[agent_key(first)] = first  # the merge may have supplied the environment; key it under the new identity too
            continue
        if key:
            seen[key] = rec
            by_bare_id.setdefault(rec["id"].lower(), []).append(rec)
        agents.append(rec)
    if len(raw_agents) != len(agents):
        warnings.append("%d duplicate agent records merged by ID within the same environment." % (len(raw_agents) - len(agents)))
    same_id = Counter((a.get("id") or "").lower() for a in agents if a.get("id"))
    cross_env = sum(1 for n in same_id.values() if n > 1)
    if cross_env:
        warnings.append("%s in more than one environment: the same bot deployed through a solution, or one file naming the environment while another gives its ID. Each is audited separately; pass --environments so names resolve to IDs, and use --environment with --agent to pick one." % plural(cross_env, "agent ID appears", "agent IDs appear"))
    no_id = sum(1 for a in agents if not a.get("id"))
    if no_id:
        warnings.append("%d agent records have no ID column; findings for them cannot be cross-referenced." % no_id)

    for a in agents:
        eid = a.get("environmentId")
        env = dict(env_map.get(eid, {})) if eid else {}
        if a.get("environmentName") and not env.get("name"):
            env["name"] = a["environmentName"]
        if a.get("environmentType") and not env.get("type"):
            env["type"] = a["environmentType"]
        if a.get("isManagedEnvironment") is not None and env.get("isManaged") is None:
            env["isManaged"] = a["isManagedEnvironment"]
        a["_env"] = env

    all_agents = agents
    excluded = 0
    if opts.environment:
        kept, error = match_environment(agents, opts.environment)
        if error:
            parser.error(error)
        excluded = len(agents) - len(kept)
        agents = kept

    env_total = sum(1 for a in agents if a.get("environmentId"))
    env_resolved = sum(1 for a in agents if a.get("environmentId") and a["_env"].get("name"))

    if not agents:
        warnings.append("No agent records found. Check that the export contains microsoft.copilotstudio/agents resources.")

    untyped = sum(1 for a in agents if not a.get("type"))
    if untyped and untyped == len(agents):
        warnings.append("The export has no resource type column; all %d records were treated as agents." % untyped)
    unparsed = sum(1 for a in agents if a.get("_unparsedPublishDate"))
    if unparsed:
        warnings.append("Last-published dates could not be parsed for %s; the publish state is unknown and exposure rules treated them as published." % plural(unparsed, "agent"))
    unknown_publish = sum(1 for a in agents if a.get("published") is None) - unparsed
    if unknown_publish:
        warnings.append("Publish state is not in the export for %s; exposure rules treated them as published." % plural(unknown_publish, "agent"))
    if agents and not any(a["_connectorDetail"] for a in agents):
        warnings.append("No connector operation detail (provider, consent, usage) in the export. Credential rules CR1, CR2, CR3, and CR5 were not evaluated; export from the inventory API or Azure Resource Graph to include properties.powerPlatformConnectors.")
    if env_total and env_resolved < env_total:
        warnings.append("%s in environments the export does not name; pass --environments with an environment export to resolve names and types." % plural(env_total - env_resolved, "agent is", "agents are"))

    owner_keys = set(a.get("ownerId") for a in agents if a.get("ownerId"))
    owners_resolved = sum(1 for k in owner_keys if users.get(k, {}).get("name"))
    user_count = len(set(id(u) for u in users.values()))
    if users and owner_keys and owners_resolved == 0:
        warnings.append("0 of %d distinct owner keys matched the user list. Owner keys in the export are %s; the user list needs a matching id, UPN, or name column." % (
            len(owner_keys), "object IDs" if all(re.fullmatch(r"[0-9a-f-]{32,36}", k) for k in owner_keys) else "names or UPNs"))

    audit = Audit(agents, env_map, users, opts, coverage_agents=all_agents, source_coverage=source_coverage)
    for value in sorted(audit.departing):
        matched = any(audit._departing(k)[0] and (k == value or (users.get(k, {}).get("upn") == value) or (users.get(k, {}).get("id") == value)) for k in owner_keys)
        if not matched:
            warnings.append("--departing value '%s' matched no owner in the audited scope%s." % (value, "" if users else "; UPNs need --users to map to object IDs"))
    audit.run()
    warnings.extend(audit.gaps)

    dossier = None
    if opts.agent:
        dossier, error = match_agent(agents, opts.agent)
        if error:
            parser.error(error)
    handover = None
    if opts.owner:
        handover, error = match_owner(agents, users, opts.owner)
        if error:
            parser.error(error)

    ctx = {
        "audit": audit, "opts": opts, "sources": sources, "warnings": warnings, "excluded": excluded, "exportComplete": export_complete,
        "other_types": other_types, "env_records": env_records, "env_total": env_total, "env_resolved": env_resolved,
        "user_count": user_count, "owners_resolved": owners_resolved, "owners_total": len(owner_keys),
        "dossier": dossier, "handover": handover,
    }
    ctx["summary"] = build_summary(audit)
    ctx["attention"] = build_attention(audit)
    ctx["ownerWork"] = build_owner_work(audit)
    ctx["environments"] = build_environment_table(audit)
    ctx["connectors"] = build_connector_table(audit)
    ctx["sharedConnections"] = build_shared_connections(audit)
    ctx["identityMigration"] = build_identity_migration(audit)
    ctx["remediation"] = build_remediation(audit)

    markdown = render_markdown(ctx)
    if opts.md:
        with open(opts.md, "w", encoding="utf-8") as handle:
            handle.write(markdown + "\n")
    else:
        sys.stdout.write(markdown + "\n")
    if opts.json_path:
        with open(opts.json_path, "w", encoding="utf-8") as handle:
            json.dump(build_json(ctx), handle, indent=2, default=str)
    if opts.md:
        if dossier:
            what = "dossier for %s: %d findings" % (audit.agent_label(dossier), len(dossier["_findings"]))
        elif handover is not None:
            what = "owner handover for %s: %s owned" % (audit.owner_label(handover), plural(sum(1 for a in agents if (a.get("ownerId") or "") == handover), "agent"))
        else:
            what = "%s, %s (%s)" % (plural(len(agents), "agent"), plural(len(audit.findings), "finding"), ", ".join("%d %s" % (v, k) for k, v in ctx["summary"]["findingsBySeverity"].items()))
        sys.stderr.write("Wrote %s%s: %s.\n" % (opts.md, (" and " + opts.json_path) if opts.json_path else "", what))
    return 0


if __name__ == "__main__":
    sys.exit(main())
