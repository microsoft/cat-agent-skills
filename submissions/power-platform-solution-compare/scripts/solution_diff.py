#!/usr/bin/env python3
"""Compare two Power Platform solution packages and report what changed.

Usage:
    python3 solution_diff.py BASELINE CANDIDATE [--md report.md] [--json report.json]
                             [--max-changes 25] [--include-noise]
                             [--types "Security roles,Cloud flows"] [--brief]

BASELINE and CANDIDATE are solution exports: a .zip file, or a folder that
contains solution.xml and customizations.xml (an extracted export). Managed
and unmanaged exports both work. Standard library only; no network access.

The script inventories every component collection it finds in
customizations.xml and opens packaged canvas apps (.msapp) to compare their
screens, controls, property formulas, data sources, and connections
(tables, columns, forms, views, charts, relationships,
choices, roles, field security profiles, processes incl. cloud and desktop
flows, model-driven apps, sitemaps, dashboards, web resources, plug-in
assemblies and steps, custom APIs, connection references, environment
variables, canvas apps, custom controls, Copilot Studio agents, and any other
collection through a generic fallback), compares the two packages, flags
likely-breaking changes, and writes a Markdown report plus optional JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict

TOOL_VERSION = "1.0.0"

# --------------------------------------------------------------------------
# Package loading
# --------------------------------------------------------------------------


TEXT_EXT = (".xml", ".json", ".js", ".html", ".htm", ".css", ".xaml", ".txt", ".csv", ".svg", ".resx", ".md", ".yaml", ".yml")
LARGE = 2 * 1024 * 1024


MSAPP_TEXT = ("properties.json", "header.json", "references/datasources.json", "references/resources.json",
              "componentsmetadata.json", "connections.json")
CONNECTED_DS_TYPES = {"ConnectedDataSourceInfo", "NativeCDSDataSourceInfo", "ServiceInfo", "CdsNativeDataSourceInfo",
                      "SqlDataSourceInfo"}


def read_msapp(data: bytes):
    """Return the text entries of a canvas app package (controls, components, source YAML, properties, data sources)
    plus hashes of its media under Assets/ and Resources/. Entry names are normalized to forward slashes."""
    out = {"__assets__": {}, "__skipped__": []}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                n = info.filename.replace("\\", "/")
                nl = n.lower()
                is_text = (nl.startswith(("controls/", "components/")) and nl.endswith(".json")) or \
                          (nl.startswith("src/") and nl.endswith((".yaml", ".yml", ".json"))) or nl in MSAPP_TEXT
                if is_text and info.file_size > 64 * 1024 * 1024:
                    out["__skipped__"].append(f"{n} ({info.file_size // (1024 * 1024)} MB)")
                elif is_text:
                    out[n] = zf.read(info)
                elif nl.startswith(("assets/", "resources/")) and not nl.endswith(".json"):
                    out["__assets__"][n] = hashlib.sha256(zf.read(info)).hexdigest()[:12]
    except (zipfile.BadZipFile, OSError):
        return None
    return out


class Package:
    def __init__(self, label: str, files: "dict[str, bytes]", packaged: str = ""):
        self.label = label
        self.packaged = packaged  # date of the packaged solution.xml, when known
        self.hashes = {k: hashlib.sha256(v).hexdigest()[:12] for k, v in files.items()}
        # canvas app packages are opened once; only their text entries are kept
        self.msapps = {k: read_msapp(v) for k, v in files.items() if k.lower().endswith(".msapp")}
        # keep bytes for text-like and small files only; large binaries are represented by their hash
        self.files = {k: v for k, v in files.items() if (len(v) <= LARGE or k.lower().endswith(TEXT_EXT)) and not k.lower().endswith(".msapp")}
        self.all_paths = sorted(files)

    def msapp(self, path: str):
        path = path.lstrip("/").replace("\\", "/")
        if path in self.msapps:
            return self.msapps[path]
        lowered = {k.lower(): k for k in self.msapps}
        key = lowered.get(path.lower())
        return self.msapps[key] if key else None

    def hash(self, path: str):
        path = path.lstrip("/").replace("\\", "/")
        if path in self.hashes:
            return self.hashes[path]
        lowered = {k.lower(): k for k in self.hashes}
        key = lowered.get(path.lower())
        return self.hashes[key] if key else None

    def get(self, path: str):
        path = path.lstrip("/").replace("\\", "/")
        if path in self.files:
            return self.files[path]
        lowered = {k.lower(): k for k in self.files}
        key = lowered.get(path.lower())
        return self.files[key] if key else None

    def find(self, prefix: str):
        prefix = prefix.lower()
        return sorted(k for k in self.all_paths if k.lower().startswith(prefix))


def _reroot(files: "dict[str, bytes]", label: str) -> "dict[str, bytes]":
    """If customizations.xml sits inside a wrapper folder (zip extracted into a subfolder), strip that prefix.
    Refuse `pac solution unpack` source, whose Other/Customizations.xml is incomplete."""
    lowered = {k.lower(): k for k in files}
    if any(re.search(r"(^|/)other/(customizations|solution)\.xml$", k) for k in lowered) or \
       any(re.match(r"^(.*/)?entities/[^/]+/entity\.xml$", k) for k in lowered):
        sys.exit(f"error: {label} looks like source unpacked with `pac solution unpack` (Other/Customizations.xml, Entities/*/Entity.xml). "
                 "Repack it with `pac solution pack` and compare the resulting .zip, or compare the unpacked files directly.")
    if "customizations.xml" in lowered:
        return files
    hits = [k for k in lowered if k.endswith("/customizations.xml")]
    if len(hits) == 1:
        prefix = lowered[hits[0]][: -len("customizations.xml")]
        return {k[len(prefix):]: v for k, v in files.items() if k.startswith(prefix)}
    if len(hits) > 1:
        sys.exit(f"error: {label} contains {len(hits)} customizations.xml files ({', '.join(sorted(lowered[h] for h in hits)[:4])}); point the script at one solution")
    return files


def load_package(path: str) -> Package:
    import datetime
    if os.path.isdir(path):
        files, packaged = {}, ""
        for root, _dirs, names in os.walk(path):
            for n in names:
                full = os.path.join(root, n)
                rel = os.path.relpath(full, path).replace(os.sep, "/")
                with open(full, "rb") as fh:
                    files[rel] = fh.read()
                if n.lower() == "solution.xml":
                    packaged = datetime.date.fromtimestamp(os.path.getmtime(full)).isoformat()
        return Package(os.path.basename(os.path.normpath(path)), _reroot(files, path), packaged)
    if zipfile.is_zipfile(path):
        files, packaged = {}, ""
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                files[info.filename.replace("\\", "/")] = zf.read(info)
                if info.filename.lower().endswith("solution.xml") and info.date_time[0] > 1980:
                    packaged = "%04d-%02d-%02d" % info.date_time[:3]
        return Package(os.path.basename(path), _reroot(files, path), packaged)
    sys.exit(f"error: {path} is neither a .zip file nor a folder")


def parse_xml(data: bytes):
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        sys.exit(f"error: could not parse XML: {exc}")


# --------------------------------------------------------------------------
# XML helpers
# --------------------------------------------------------------------------

NOISE_TAGS = {
    "IntroducedVersion", "introducedversion", "modifiedon", "createdon",
    "versionnumber", "overwritetime", "solutionid", "supportingsolutionid",
    "ismanaged", "IsManaged", "iscustomizable_managed", "timezoneruleversionnumber",
    "CreatedByClientVersion", "MinClientVersion",
}
PRIMARY_KEYS = ["PhysicalName", "alias", "name", "Name", "schemaName", "SchemaName", "attribute", "languagecode", "LCID",
                "id", "Id", "key", "uniquename", "UniqueName", "schemaname", "logicalname", "LogicalName",
                "connectionreferencelogicalname", "handlerUniqueId", "functionName"]
SECONDARY_KEYS = ["value"]
KEY_ATTRS = PRIMARY_KEYS + SECONDARY_KEYS
TEXT_KEYS = ["LogicalName", "SchemaName", "UniqueName", "Name", "name", "schemaname", "uniquename", "logicalname"]


def text(el, tag: str, default: str = ""):
    """Return attribute `tag` or text of child `tag` (case-insensitive)."""
    if el is None:
        return default
    for k, v in el.attrib.items():
        if k.lower() == tag.lower():
            return v
    for child in el:
        if child.tag.lower() == tag.lower():
            return (child.text or "").strip()
    return default


def localized_name(el, tag="LocalizedNames", child="LocalizedName"):
    if el is None:
        return ""
    for ln in el.iter():
        if ln.tag == tag:
            for c in ln:
                if c.tag == child:
                    return c.attrib.get("description", "")
    return ""


def child_key(el):
    """Stable identity for an element: all present primary key attributes joined, else an id-like attribute,
    else an identifying text child, else the bare tag. Never positional when an identifier exists."""
    vals = [el.attrib[a] for a in PRIMARY_KEYS if el.attrib.get(a, "") != ""]
    if vals:
        return f"{el.tag}[{','.join(vals)}]"
    for a, v in el.attrib.items():
        if a.lower().endswith("id") and v:
            return f"{el.tag}[{v}]"
    for a in SECONDARY_KEYS:
        if el.attrib.get(a, "") != "":
            return f"{el.tag}[{el.attrib[a]}]"
    for c in el:
        if c.tag in TEXT_KEYS and (c.text or "").strip() and len(c) == 0:
            return f"{el.tag}[{c.text.strip()}]"
    return el.tag


def component_key(el):
    """Best identifier for a component in an unknown collection."""
    k = child_key(el)
    if k != el.tag:
        return k
    for a, v in el.attrib.items():
        if a.lower().endswith("id") and v:
            return f"{el.tag}[{v.strip('{}').lower()}]"
    for c in el:
        tag = c.tag.lower()
        if tag in ("schemaname", "uniquename", "name", "logicalname", "displayname") and (c.text or "").strip():
            return f"{el.tag}[{c.text.strip()}]"
    for c in el:
        if c.tag.lower().endswith("id") and (c.text or "").strip():
            return f"{el.tag}[{c.text.strip().strip('{}').lower()}]"
    return el.tag


# Empty, attribute-less elements whose presence alone changes behaviour (FetchXML); other empty unkeyed
# wrappers such as <CustomActions/> are packaging skeleton and record nothing.
PRESENCE_TAGS = {"all-attributes", "no-lock"}

# Parent tag -> child tag whose order carries meaning (form layout, view column order, query sort, navigation).
# The parent records one `@<child>-order` leaf listing its children's keys in document order, so a reorder is
# reported as a single change while unordered collections stay order-insensitive.
ORDERED_CHILDREN = {"tabs": "tab", "sections": "section", "columns": "column", "rows": "row", "row": "cell",
                    "entity": "order", "link-entity": "order", "SiteMap": "Area", "Area": "Group", "Group": "SubArea",
                    "options": "option", "steps": "step", "stages": "stage"}


def flatten(el, noise: bool, prefix: str = "", out=None, counters=None, root: bool = True, repeated: bool = False):
    """Flatten an element into {path: value} for leaf comparison.

    Path rules, chosen so that a path never changes because a sibling appeared or disappeared:
    - the component root contributes its bare tag, so a rename does not move every leaf; its identifying
      attributes (Name, ids) are recorded as `tag/@attr` leaves and compare like any other value;
    - keyed elements (see child_key) contribute `tag[key]`; identical keys among siblings get `#n`;
    - unkeyed elements with children and no attributes of their own are transparent wrappers when they
      are the only child of their tag: they add no segment and their children attach to the parent path;
    - unkeyed elements that carry attributes (FetchXML `filter type="or"`, `forms type="main"`) or that
      repeat among siblings become positional segments (`filter`, `filter#2`) so nested and sibling
      groups keep their own attributes and children;
    - keyed leaf elements always record a presence leaf, so `<attribute name="x"/>` registers;
      unkeyed empty wrappers such as `<CustomActions/>` record nothing, except PRESENCE_TAGS
      (`<all-attributes/>`), whose presence is itself the setting.
    """
    if out is None:
        out = OrderedDict()
    if counters is None:
        counters = defaultdict(int)
    if el.tag in NOISE_TAGS and not noise:
        return out
    key = el.tag if root else child_key(el)  # identity of the component root is established by matching, not by its path
    keyed = key != el.tag
    has_children = len(el) > 0
    own_attrs = any(noise or a not in NOISE_TAGS for a in el.attrib)
    if keyed or root or not has_children or repeated or own_attrs:
        counters[(prefix, key)] += 1
        n = counters[(prefix, key)]
        if n > 1:
            key = f"{key}#{n}"
        path = f"{prefix}/{key}" if prefix else key
        child_prefix = path
    else:
        path = f"{prefix}/{el.tag}" if prefix else el.tag  # transparent wrapper: attrs only
        child_prefix = prefix
    consumed = set(el.attrib[a] for a in PRIMARY_KEYS if el.attrib.get(a, "") != "") if keyed else set()
    if keyed and not consumed:
        consumed = {el.attrib[a] for a in el.attrib if a.lower().endswith("id") and el.attrib[a]} or {el.attrib.get(a, "") for a in SECONDARY_KEYS}
    wrote = False
    for a, v in sorted(el.attrib.items()):
        if a in NOISE_TAGS and not noise:
            continue
        if (a in KEY_ATTRS or a.lower().endswith("id")) and v in consumed:
            continue
        out[f"{path}/@{a}"] = v
        wrote = True
    t = (el.text or "").strip()
    if not has_children and (t or (keyed and not wrote) or el.tag in PRESENCE_TAGS):
        out[path] = t
    sub = defaultdict(int) if child_prefix == path else counters
    tags = defaultdict(int)
    for c in el:
        tags[c.tag] += 1
    for c in el:
        flatten(c, noise, child_prefix, out, sub, False, tags[c.tag] > 1)
    ordered = ORDERED_CHILDREN.get(el.tag)
    if ordered and tags.get(ordered, 0) > 1:
        seq = [child_key(c)[len(ordered) + 1:-1] if child_key(c) != ordered else "?" for c in el if c.tag == ordered]
        out[f"{path}/@{ordered}-order"] = " > ".join(seq)
    return out


def digest(mapping) -> str:
    h = hashlib.sha256()
    for k, v in mapping.items():
        h.update(k.encode("utf-8", "replace"))
        h.update(b"=")
        h.update(str(v).encode("utf-8", "replace"))
        h.update(b"\n")
    return h.hexdigest()[:16]


def _collapse(paths, other):
    """Group leaf paths that are entirely new (or entirely gone) under their nearest keyed ancestor
    that has no counterpart in the other side, so a new form control is one row, not five."""
    other_prefixes = set()
    for k in other:
        segs = k.split("/")
        for i in range(1, len(segs) + 1):
            other_prefixes.add("/".join(segs[:i]))
    groups = OrderedDict()
    for k in paths:
        segs = k.split("/")
        chosen = None
        for i in range(1, len(segs) + 1):
            prefix = "/".join(segs[:i])
            if prefix not in other_prefixes and "[" in segs[i - 1]:
                chosen = prefix
                break
        groups.setdefault(chosen or k, []).append(k)
    return groups


def diff_flat(a, b, limit: int):
    changes = []
    removed = [k for k in a if k not in b]
    added = [k for k in b if k not in a]
    for k in a:
        if k in b and a[k] != b[k]:
            changes.append({"path": k, "kind": "changed", "old": a[k], "new": b[k]})
    def summary(src, prefix, leaves):
        vals = OrderedDict()
        for k in leaves[:4]:
            rel = k[len(prefix) + 1:] if k.startswith(prefix + "/") else (k[len(prefix):] or "(element)")
            if src.get(k, "") != "":
                vals[rel.lstrip("/")] = src[k]
        return vals
    for prefix, leaves in _collapse(removed, b).items():
        if len(leaves) == 1 and leaves[0] == prefix:
            changes.append({"path": prefix, "kind": "removed", "old": a[prefix]})
        else:
            changes.append({"path": prefix, "kind": "removed", "old": "", "leaves": len(leaves), "subtree": True, "values": summary(a, prefix, leaves)})
    for prefix, leaves in _collapse(added, a).items():
        if len(leaves) == 1 and leaves[0] == prefix:
            changes.append({"path": prefix, "kind": "added", "new": b[prefix]})
        else:
            changes.append({"path": prefix, "kind": "added", "new": "", "leaves": len(leaves), "subtree": True, "values": summary(b, prefix, leaves)})
    # rename detection: a removed subtree and an added subtree with identical relative leaves
    removed_sub = [c for c in changes if c["kind"] == "removed" and c.get("subtree")]
    added_sub = [c for c in changes if c["kind"] == "added" and c.get("subtree")]
    if removed_sub and added_sub:
        def rel(src, prefix):
            return tuple(sorted((k[len(prefix):], v) for k, v in src.items() if k.startswith(prefix + "/") or k == prefix))
        sig_added = {}
        for c in added_sub:
            sig_added.setdefault(rel(b, c["path"]), []).append(c)
        renamed = []
        for c in removed_sub:
            sig = rel(a, c["path"])
            if len(sig) >= 2 and sig in sig_added and sig_added[sig]:
                other = sig_added[sig].pop(0)
                renamed.append((c, other))
        for old, new in renamed:
            changes.remove(old)
            changes.remove(new)
            changes.append({"path": old["path"], "kind": "renamed", "new_path": new["path"], "leaves": old["leaves"]})

    def keep_order_leaf(c):
        leaf = c["path"].rsplit("/", 1)[-1]
        if not (leaf.startswith("@") and leaf.endswith("-order")):
            return True
        if c["kind"] != "changed":
            return False  # the sequence leaf appeared or vanished with the member count; members report themselves
        o, n = str(c.get("old", "")).split(" > "), str(c.get("new", "")).split(" > ")
        return sorted(o) == sorted(n)  # keep only a pure reorder; membership changes are already reported
    changes = [c for c in changes if keep_order_leaf(c)]
    total = len(changes)
    return changes[:limit], total


# --------------------------------------------------------------------------
# Component extraction
# --------------------------------------------------------------------------

COMPONENT_TYPES = {
    "1": "Table", "2": "Column", "3": "Relationship", "9": "Choice", "10": "Table relationship",
    "11": "Relationship role", "13": "Managed property", "14": "Alternate key", "16": "Privilege", "20": "Security role",
    "21": "Role privilege", "22": "Display string", "24": "Form (classic)", "26": "View", "29": "Process",
    "31": "Report", "36": "Email template", "37": "Contract template", "38": "Article template",
    "39": "Mail merge template", "44": "Duplicate rule", "46": "Entity map", "47": "Attribute map",
    "48": "Ribbon command", "50": "Ribbon customization", "52": "Ribbon rule", "59": "Chart", "60": "Form",
    "61": "Web resource", "62": "Sitemap", "63": "Connection role", "65": "Hierarchy rule", "66": "Custom control",
    "68": "Custom control default config", "70": "Field security profile", "71": "Field permission",
    "80": "Model-driven app", "90": "Plug-in type", "91": "Plug-in assembly", "92": "Plug-in step",
    "93": "Plug-in step image", "95": "Service endpoint", "150": "Routing rule", "152": "SLA",
    "154": "Convert rule", "161": "Mobile offline profile", "165": "Similarity rule", "166": "Data source mapping",
    "201": "SDK message", "300": "Canvas app", "371": "Connector", "372": "Connector",
    "380": "Environment variable definition", "381": "Environment variable value", "400": "AI project type",
    "401": "AI project", "402": "AI configuration", "430": "Entity analytics config", "431": "Attribute image config",
    "432": "Entity image config",
}


def component_type_name(code: str) -> str:
    if code in COMPONENT_TYPES:
        return COMPONENT_TYPES[code]
    try:
        if int(code) >= 10000:
            return f"table-based component ({code})"
    except ValueError:
        pass
    return f"type {code}"


GUID_RE = r"\{?[0-9a-f][0-9a-f-]*\}?"  # export folder suffixes are GUIDs; anything with other letters is another component's name


def attached_files(pkg: Package, folder: str, name: str, ident: str = ""):
    """Files under folder/ that belong to component `name`: folder/name/..., folder/name-<GUID>/... (the export's
    own suffix, or the component's id when known), or a direct file name.* / name_<Kind>Uri.*. A hyphenated
    sibling such as `Contoso-Tools` never matches `Contoso`."""
    if not name:
        return {}
    name_l, ident_l = name.lower(), (ident or "").strip("{}").lower()
    out = {}
    for f in pkg.find(folder.rstrip("/") + "/"):
        rest = f[len(folder.rstrip("/")) + 1:]
        first = rest.split("/")[0].lower()
        stem = first.rsplit(".", 1)[0] if "/" not in rest else first
        if "/" in rest:
            owner = first == name_l or (ident_l and first == f"{name_l}-{ident_l}") \
                or (not ident_l and re.fullmatch(re.escape(name_l) + "-" + GUID_RE, first) is not None)
        else:
            owner = stem == name_l or re.match(re.escape(name_l) + r"_[a-z]+uri$", stem) is not None
        if owner:
            out[rest] = pkg.hash(f)
    return out


WORKFLOW_CATEGORY = {
    "0": "Classic workflow", "1": "Dialog", "2": "Business rule", "3": "Action",
    "4": "Business process flow", "5": "Cloud flow", "6": "Desktop flow",
    "7": "AI flow",
}


class Component:
    __slots__ = ("ctype", "key", "label", "flat", "extra", "parent")

    def __init__(self, ctype, key, label, flat, extra=None, parent=None):
        self.ctype, self.key, self.label = ctype, key, label
        self.flat, self.extra, self.parent = flat, extra or {}, parent


def add(components, comp: Component):
    components[(comp.ctype, comp.key)] = comp


def fetch_column_refs(el, primary: str):
    """Columns a view or chart reads, as 'table.column' lower-cased, attributed to their owning table: columns of the
    primary entity to the primary table, link-entity columns to the linked table, conditions with `entityname` and
    layout cells named `alias.column` to the aliased table."""
    refs, alias = set(), {}

    def index_aliases(node):  # aliases can be referenced by conditions that precede the link in document order
        for c in node.iter():
            if c.tag.lower() == "link-entity" and c.attrib.get("alias") and c.attrib.get("name"):
                alias[c.attrib["alias"]] = c.attrib["name"]

    def walk(node, table):
        for c in node:
            tag = c.tag.lower()
            if tag == "link-entity":
                t = c.attrib.get("name") or table
                if c.attrib.get("alias"):
                    alias[c.attrib["alias"]] = t
                if c.attrib.get("from"):
                    refs.add((t, c.attrib["from"]))  # join column on the linked table
                if c.attrib.get("to"):
                    refs.add((table, c.attrib["to"]))  # join column on the parent table
                walk(c, t)
            elif tag == "attribute":
                if c.attrib.get("name"):
                    refs.add((table, c.attrib["name"]))
            elif tag == "order":
                if c.attrib.get("attribute"):
                    refs.add((alias.get(c.attrib.get("alias", ""), table), c.attrib["attribute"]))
            elif tag == "condition":
                if c.attrib.get("attribute"):
                    en = c.attrib.get("entityname", "")
                    refs.add((alias.get(en, en) if en else table, c.attrib["attribute"]))
                walk(c, table)
            elif tag == "filter":
                walk(c, table)
            else:
                walk(c, table)

    fetches = [f for f in el.iter() if f.tag.lower() == "fetch"]
    for holder in el.iter():  # charts carry their fetch as escaped text inside datadescription
        if not len(holder) and holder.text and "<fetch" in holder.text:
            try:
                parsed = ET.fromstring(holder.text.strip())
                fetches.extend([f for f in parsed.iter() if f.tag.lower() == "fetch"] or ([parsed] if parsed.tag.lower() == "fetch" else []))
            except ET.ParseError:
                pass
    for fetch in fetches:
        index_aliases(fetch)
    for fetch in fetches:
        for ent in fetch:
            if ent.tag.lower() == "entity":
                walk(ent, ent.attrib.get("name") or primary)
    for cell in el.iter():
        if cell.tag.lower() == "cell" and cell.attrib.get("name"):
            name = cell.attrib["name"]
            if "." in name:
                a, col = name.split(".", 1)
                refs.add((alias.get(a, a), col))
            else:
                refs.add((primary, name))
    return sorted(f"{t}.{c}".lower() for t, c in refs if t and c)


def extract_entity(ent, noise, components):
    name_el = ent.find("Name")
    table = (name_el.text or "").strip() if name_el is not None else text(ent, "Name")
    display = name_el.attrib.get("LocalizedName", "") if name_el is not None else ""
    label = f"{table} ({display})" if display else table
    info = ent.find("EntityInfo/entity")
    # Table settings: everything under <entity> except attributes
    if info is not None:
        settings = ET.Element("entity", info.attrib)
        for c in info:
            if c.tag != "attributes":
                settings.append(c)
        add(components, Component("Tables", table, label, flatten(settings, noise), {"display": display, "ownership": text(info, "OwnershipTypeMask")}))
        for att in info.findall("attributes/attribute"):
            col = att.attrib.get("PhysicalName") or text(att, "LogicalName")
            flat = flatten(att, noise)
            disp = ""
            dn = att.find("displaynames/displayname")
            if dn is not None:
                disp = dn.attrib.get("description", "")
            extra = {"type": text(att, "Type"), "required": text(att, "RequiredLevel").lower(),
                     "maxlength": text(att, "MaxLength") or text(att, "Length"),
                     "format": text(att, "Format"), "display": disp, "schema": col}
            opts = att.find("optionset")
            if opts is not None:
                extra["options"] = {o.attrib.get("value", ""): (o.find("labels/label").attrib.get("description", "") if o.find("labels/label") is not None else "")
                                    for o in opts.findall("options/option")}
            add(components, Component("Columns", f"{table}.{col}", f"{table}.{col}", flat, extra, table))
    else:
        add(components, Component("Tables", table, label, flatten(ent, noise)))
    for forms in ent.findall("FormXml/forms"):
        ftype = forms.attrib.get("type", "form")
        for form in forms.findall("systemform"):
            fid = text(form, "formid").strip("{}").lower()
            fname = localized_name(form)
            add(components, Component("Forms", f"{table}:{ftype}:{fid}",
                                      f"{table} / {ftype} / {fname or fid}", flatten(form, noise),
                                      {"form_type": ftype, "state": text(form, "FormActivationState")}, table))
    for q in ent.findall("SavedQueries/savedqueries/savedquery"):
        qid = text(q, "savedqueryid").strip("{}").lower()
        add(components, Component("Views", f"{table}:{qid}", f"{table} / {localized_name(q) or qid}",
                                  flatten(q, noise), {"query_type": text(q, "querytype"), "default": text(q, "isdefault"),
                                                      "column_refs": fetch_column_refs(q, table)}, table))
    for v in ent.findall("Visualizations/visualization"):
        vid = text(v, "savedqueryvisualizationid").strip("{}").lower()
        add(components, Component("Charts", f"{table}:{vid}", f"{table} / {localized_name(v) or vid}",
                                  flatten(v, noise), {"column_refs": fetch_column_refs(v, table)}, table))
    ribbon = ent.find("RibbonDiffXml")
    if ribbon is not None and len(ribbon):
        rflat = flatten(ribbon, noise)
        if rflat:  # skip the empty skeleton every export carries
            add(components, Component("Command bars", table, f"{table} ribbon", rflat, {}, table))


CONNECTOR_ID_KEYS = {"connectionName", "connectionname", "apiId", "apiid", "connectionReferenceName", "connectionreferencename"}


def _norm_connector_ids(node):
    """Strip environment-specific instance suffixes (shared_office365-1a2b3c...) only from connector identifier
    fields, so user data that happens to look similar (a file name such as shared_export-12345.csv) still compares."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in CONNECTOR_ID_KEYS and isinstance(v, str):
                out[k] = re.sub(r"^(shared_[a-z0-9]+)-[0-9a-f]{5,}$", r"\1", v)
            else:
                out[k] = _norm_connector_ids(v)
        return out
    if isinstance(node, list):
        return [_norm_connector_ids(v) for v in node]
    return node


def _conn_name(inputs):
    """connectionName from inputs.host when both are objects; Compose inputs can be any JSON value."""
    if not isinstance(inputs, dict):
        return ""
    host = inputs.get("host")
    if not isinstance(host, dict):
        return ""
    v = host.get("connectionName", "")
    return v if isinstance(v, str) else ""


def flow_actions(node, prefix="", out=None):
    if out is None:
        out = OrderedDict()
    if not isinstance(node, dict):
        return out
    for name, body in node.items():
        if not isinstance(body, dict):
            continue
        path = f"{prefix}/{name}" if prefix else name
        clean = {k: v for k, v in body.items() if k not in ("metadata", "runAfter", "actions", "else", "cases", "default")}
        if isinstance(body.get("cases"), dict):
            clean["cases"] = {cn: (c.get("case") if isinstance(c, dict) else c) for cn, c in body["cases"].items()}
        canon = json.dumps(_norm_connector_ids(clean), sort_keys=True, default=str)
        out[path] = {"type": body.get("type", ""), "hash": hashlib.sha256(canon.encode()).hexdigest()[:12],
            "runAfter": {k: (sorted(str(x) for x in v) if isinstance(v, list) else [str(v)]) for k, v in (body.get("runAfter") or {}).items()},
            "leaves": json_leaves(clean),
            "connection": _conn_name(body.get("inputs"))}
        flow_actions(body.get("actions"), path, out)
        if isinstance(body.get("else"), dict):
            flow_actions(body["else"].get("actions"), path + "/else", out)
        if isinstance(body.get("cases"), dict):
            for cname, case in body["cases"].items():
                if isinstance(case, dict):
                    flow_actions(case.get("actions"), f"{path}/case:{cname}", out)
        if isinstance(body.get("default"), dict):
            flow_actions(body["default"].get("actions"), path + "/default", out)
    return out


def json_leaves(node, prefix="", out=None):
    """Flatten JSON to {path: scalar} for old->new reporting. Callers remove designer metadata at the node
    level first; nested `metadata` keys are user data and are kept."""
    if out is None:
        out = OrderedDict()
    if isinstance(node, dict):
        if not node and prefix:
            out[prefix] = "{}"  # an empty object is still a value, and differs from an empty array or a missing key
        for k, v in node.items():
            seg = str(k).replace("~", "~0").replace("/", "~1").replace("[", "~2")  # JSON-pointer style escaping
            json_leaves(v, f"{prefix}/{seg}" if prefix else seg, out)
    elif isinstance(node, list):
        if not node and prefix:
            out[prefix] = "[]"
        for i, v in enumerate(node):
            json_leaves(v, f"{prefix}[{i}]", out)
    else:
        try:
            out[prefix] = json.dumps(node) if isinstance(node, (str, int, float, bool)) or node is None else json.dumps(str(node))
        except (TypeError, ValueError):
            out[prefix] = json.dumps(str(node))
    return out


def _show_path(k: str) -> str:
    """Undo JSON-pointer escaping for display only; JSON output keeps the unambiguous form."""
    return k.replace("~1", "/").replace("~2", "[").replace("~0", "~")


def leaf_diff_lines(old, new, limit=8):
    lines = []
    for k in old:
        if k not in new:
            lines.append(f"{_show_path(k)}: {old[k]} removed")
        elif old[k] != new[k]:
            lines.append(f"{_show_path(k)}: {old[k]} → {new[k]}")
    for k in new:
        if k not in old:
            lines.append(f"{_show_path(k)}: {new[k]} added")
    more = len(lines) - limit
    return lines[:limit] + ([f"… {more} more"] if more > 0 else [])


def _strip_designer_meta(definition):
    """Return a copy of a flow definition without the designer's `metadata` objects (operationMetadataId and
    similar), which sit directly on trigger and action nodes. `metadata` keys anywhere else (inside inputs,
    parameters, or payloads) are user data and are kept."""
    if not isinstance(definition, dict):
        return definition
    def actions(node):
        if not isinstance(node, dict):
            return node
        out = {}
        for name, body in node.items():
            if not isinstance(body, dict):
                out[name] = body
                continue
            b = {k: v for k, v in body.items() if k != "metadata"}
            if isinstance(b.get("actions"), dict):
                b["actions"] = actions(b["actions"])
            if isinstance(b.get("else"), dict) and isinstance(b["else"].get("actions"), dict):
                b["else"] = dict(b["else"], actions=actions(b["else"]["actions"]))
            if isinstance(b.get("default"), dict) and isinstance(b["default"].get("actions"), dict):
                b["default"] = dict(b["default"], actions=actions(b["default"]["actions"]))
            if isinstance(b.get("cases"), dict):
                b["cases"] = {cn: (dict(c, actions=actions(c["actions"])) if isinstance(c, dict) and isinstance(c.get("actions"), dict) else c)
                              for cn, c in b["cases"].items()}
            out[name] = b
        return out
    d = dict(definition)
    if isinstance(d.get("triggers"), dict):
        d["triggers"] = {k: ({kk: vv for kk, vv in v.items() if kk != "metadata"} if isinstance(v, dict) else v) for k, v in d["triggers"].items()}
    if isinstance(d.get("actions"), dict):
        d["actions"] = actions(d["actions"])
    return d


def flow_summary(pkg: Package, json_name: str):
    data = pkg.get(json_name) if json_name else None
    if data is None:
        return None
    try:
        doc = json.loads(data.decode("utf-8-sig"))
    except Exception:
        return {"error": "flow JSON could not be parsed"}
    props = doc.get("properties", {}) if isinstance(doc, dict) else {}
    definition = props.get("definition", {}) or {}
    triggers = {k: {"type": v.get("type", ""), "kind": v.get("kind", ""), "hash": hashlib.sha256(
        json.dumps({kk: vv for kk, vv in v.items() if kk != "metadata"}, sort_keys=True, default=str).encode()
    ).hexdigest()[:12], "leaves": json_leaves({kk: vv for kk, vv in v.items() if kk != "metadata"})}
        for k, v in (definition.get("triggers") or {}).items() if isinstance(v, dict)}
    conns = {}
    for k, v in (props.get("connectionReferences") or {}).items():
        if isinstance(v, dict):
            conns[k] = {"api": (v.get("api") or {}).get("name", ""),
                        "reference": (v.get("connection") or {}).get("connectionReferenceLogicalName", ""),
                        "runtimeSource": v.get("runtimeSource", "")}
    canon = json.dumps(_norm_connector_ids(_strip_designer_meta(definition)), sort_keys=True, default=str)
    return {"triggers": triggers, "actions": flow_actions(definition.get("actions")),
            "connections": conns, "parameters": json_leaves(definition.get("parameters") or {}),
            "bindings": json_leaves(props.get("parameters") or {}) if isinstance(props.get("parameters"), dict) else {},
            "def_hash": hashlib.sha256(canon.encode()).hexdigest()[:12]}


def extract_workflows(root, pkg, noise, components):
    for wf in root.findall("Workflows/Workflow"):
        name = wf.attrib.get("Name") or text(wf, "Name")
        wid = (wf.attrib.get("WorkflowId") or text(wf, "WorkflowId")).strip("{}").lower()
        cat = text(wf, "Category", "")
        ctype = WORKFLOW_CATEGORY.get(cat, "Processes")
        ctype = {"Cloud flow": "Cloud flows", "Desktop flow": "Desktop flows", "Business rule": "Business rules",
                 "Business process flow": "Business process flows", "Classic workflow": "Classic workflows",
                 "Action": "Custom actions", "Dialog": "Dialogs", "AI flow": "AI flows"}.get(ctype, "Processes")
        extra = {"state": text(wf, "StateCode"), "status": text(wf, "StatusCode"),
                 "primary_entity": text(wf, "PrimaryEntity"), "scope": text(wf, "Scope"),
                 "mode": text(wf, "Mode"), "category": cat}
        flat = flatten(wf, noise)
        jf = text(wf, "JsonFileName")
        if jf:
            extra["flow"] = flow_summary(pkg, jf)
            extra["json_hash"] = pkg.hash(jf) or "missing"
        xf = text(wf, "XamlFileName")
        if xf:
            extra["xaml_hash"] = pkg.hash(xf) or "missing"
        add(components, Component(ctype, wid or name, name, flat, extra))


def extract_roles(root, noise, components):
    for role in root.findall("Roles/Role"):
        name = role.attrib.get("name") or text(role, "name")
        privs = {}
        for p in role.findall("RolePrivileges/RolePrivilege"):
            privs[p.attrib.get("name", "")] = p.attrib.get("level", "")
        flat = flatten(role, noise)
        add(components, Component("Security roles", name, name, flat, {"privileges": privs}))


def _extra_for(ctype, el):
    if ctype == "Relationships":
        return {"type": text(el, "EntityRelationshipType"), "referencing": text(el, "ReferencingEntityName"),
                "referenced": text(el, "ReferencedEntityName"), "cascade_delete": text(el, "CascadeDelete"),
                "cascade_assign": text(el, "CascadeAssign"), "cascade_share": text(el, "CascadeShare")}
    if ctype == "Plug-in steps":
        return {"message": text(el, "SdkMessage"), "entity": text(el, "PrimaryEntity"), "stage": text(el, "Stage"),
                "mode": text(el, "Mode"), "filtering": text(el, "FilteringAttributes"), "state": text(el, "StateCode"),
                "plugin_type": text(el, "PluginTypeName")}
    if ctype == "Connection references":
        return {"display": text(el, "connectionreferencedisplayname"), "connector": text(el, "connectorid").rsplit("/", 1)[-1]}
    if ctype == "Choices (global)":
        return {"display": el.attrib.get("localizedName", ""),
                "options": {o.attrib.get("value", ""): (o.find("labels/label").attrib.get("description", "") if o.find("labels/label") is not None else "")
                            for o in el.findall("options/option")}}
    if ctype == "Model-driven apps":
        return {"components": len(el.findall("AppModuleComponents/AppModuleComponent"))}
    return {}


def extract_simple(root, path, ctype, key_attr, components, noise, label_fn=None):
    for el in root.findall(path):
        key = el.attrib.get(key_attr) or text(el, key_attr)
        if not key:
            key = component_key(el)
            if key == el.tag:
                key = f"{el.tag}#{digest(flatten(el, noise))}"
        label = label_fn(el) if label_fn else key
        add(components, Component(ctype, key.strip("{}").lower() if key_attr.lower().endswith("id") else key,
                                  label, flatten(el, noise), _extra_for(ctype, el)))


def extract_customapi_params(root, noise, components):
    """Request parameters and response properties are scoped to their custom API, and names repeat across
    APIs and across the two kinds, so the identity is owning API + kind + unique name."""
    owners = {}
    for api in root.findall("customapis/customapi"):
        aid = (api.attrib.get("customapiid") or text(api, "customapiid")).strip("{}").lower()
        if aid:
            owners[aid] = text(api, "uniquename") or aid
    for path, ctype, kind in (("customapirequestparameters/customapirequestparameter", "Custom API request parameters", "request parameter"),
                              ("customapiresponseproperties/customapiresponseproperty", "Custom API response properties", "response property")):
        for el in root.findall(path):
            pname = text(el, "uniquename") or text(el, "name") or component_key(el)
            owner = ""
            for c in el:
                if c.tag.lower() == "customapiid":
                    guid = (c.text or "").strip().strip("{}").lower()
                    owner = (c.attrib.get("uniquename") or c.attrib.get("name") or c.attrib.get("schemaname")
                             or owners.get(guid, guid))
                    break
            key = f"{owner}/{pname}" if owner else pname
            label = f"{pname} ({kind} of {owner})" if owner else f"{pname} ({kind})"
            add(components, Component(ctype, key, label, flatten(el, noise), _extra_for(ctype, el)))


def extract_webresources(root, pkg, noise, components):
    for wr in root.findall("WebResources/WebResource"):
        name = text(wr, "Name")
        fname = text(wr, "FileName")
        data = pkg.get(fname) if fname else None
        extra = {"type": text(wr, "WebResourceType"), "file": fname,
                 "content_hash": (pkg.hash(fname) if fname else None) or "missing",
                 "size": len(data) if data is not None else 0}
        add(components, Component("Web resources", name, name, flatten(wr, noise), extra))


def _yaml_flatten(text: str):
    """Tolerant indentation-based flattener for pa.yaml: returns {path: scalar}. Handles nested mappings,
    '- Key:' list items (the key becomes the segment), quoted keys, and block scalars (| and >)."""
    out = OrderedDict()
    stack = []  # (indent, key)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        body = raw.strip()
        if body.startswith("- "):
            body = body[2:].strip()
            indent += 2
        while stack and stack[-1][0] >= indent:
            stack.pop()
        m = re.match(r"""^(?:'([^']*)'|"([^"]*)"|([^:#]+?))\s*:(?:\s+(.*))?$""", body)
        if not m:
            if raw.strip().startswith("- ") and body:  # scalar list item, e.g. a group's ControlNames entry
                parent = "/".join(k for _, k in stack)
                out[f"{parent}/{body.strip().strip(chr(34)).strip(chr(39))}" if parent else body] = ""
            continue
        key = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        val = m.group(4)
        path = "/".join([k for _, k in stack] + [key])
        if val is None or val == "":
            stack.append((indent, key))
            continue
        if val.startswith(("|", ">")):
            block = []
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip(" ")) > indent):
                block.append(lines[i].rstrip("\r"))
                i += 1
            # remove only the block's structural indentation (that of its first non-blank line); keep deeper
            # indentation and blank lines inside the scalar, since both are content in a Power Fx string literal
            lead = min((len(x) - len(x.lstrip(" ")) for x in block if x.strip()), default=0)
            body_lines = [x[lead:] if x.strip() else "" for x in block]
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()  # trailing blank lines are chomping, not content
            out[path] = "\n".join(body_lines)
        else:
            out[path] = val.strip().strip('"').strip("'") if not val.startswith("=") else val
    return out


def _json_controls(doc, flat, parent_path, counts, templates, kind=None):
    """Walk a Controls/*.json or Components/*.json TopParent tree into keyed leaves."""
    name = doc.get("Name", "?")
    tmpl = doc.get("Template") or {}
    template = tmpl.get("Name", "")
    if re.fullmatch(r"[0-9a-f]{32}", template or ""):
        template = "component:" + templates.get(template, template[:8])
    if parent_path == "":
        if kind is None:
            if template == "appinfo":
                kind = "app"
            elif tmpl.get("IsComponentDefinition"):
                kind = "component"
            elif "test" in (template or "").lower():
                kind = "test"
            else:
                kind = "screen"
        seg = f"{kind}[{name}]"
        path = seg
        counts[kind + "s"] += 1
    else:
        path = f"{parent_path}/control[{name}]"
        counts["controls"] += 1
    if template:
        flat[f"{path}/@template"] = template
    for rule in doc.get("Rules") or []:
        prop, script = rule.get("Property"), rule.get("InvariantScript")
        if prop is not None and script is not None:
            flat[f"{path}/@{prop}"] = str(script)
    for dp in doc.get("DynamicProperties") or []:  # container layout properties live here, not in Rules
        rule = dp.get("Rule") if isinstance(dp, dict) else None
        if isinstance(rule, dict) and rule.get("Property") is not None and rule.get("InvariantScript") is not None:
            flat[f"{path}/@{rule['Property']}"] = str(rule["InvariantScript"])
    if doc.get("IsGroupControl") or doc.get("GroupedControlsKey"):
        for member in doc.get("GroupedControlsKey") or []:
            flat[f"{path}/member[{member}]"] = ""
    if kind == "component" and parent_path == "":
        for cp in tmpl.get("CustomProperties") or []:  # the component's API: a change here breaks every instance
            if not isinstance(cp, dict) or not cp.get("Name"):
                continue
            base = f"{path}/customproperty[{cp['Name']}]"
            flat.setdefault(base, "")
            for f in ("PropertyDataTypeKey", "PropertyScopeKey", "PropertyKind", "Hidden", "IsResettable", "DefaultValue", "DisplayName", "Category"):
                if cp.get(f) not in (None, ""):
                    flat[f"{base}/@{f}"] = str(cp[f])
            for prm in cp.get("PropertyScopeKey", {}).get("PropertyScopeRulesKey", []) if isinstance(cp.get("PropertyScopeKey"), dict) else []:
                if isinstance(prm, dict) and prm.get("Name"):
                    flat[f"{base}/parameter[{prm['Name']}]/@type"] = str(prm.get("ScopeVariableInfo", {}).get("ScopePropertyDataType", "") if isinstance(prm.get("ScopeVariableInfo"), dict) else "")
    names = [c.get("Name") for c in (doc.get("Children") or []) if isinstance(c, dict) and c.get("Name")]
    if len(names) > 1:
        flat[f"{path}/@child-order"] = " > ".join(str(n) for n in names)  # z-order and auto-layout order
    for child in doc.get("Children") or []:
        if isinstance(child, dict):
            _json_controls(child, flat, path, counts, templates)


def _yaml_entities(y, flat, counts):
    """Map flattened pa.yaml paths onto the same keyed leaves as the JSON format."""
    kinds = {}
    for path in y:
        segs = path.split("/")
        if len(segs) >= 2 and segs[1] == "Control":
            v = str(y[path]).strip()
            kinds[segs[0]] = "app" if v == "App" else "screen" if v == "Screen" else "component" if v.lower().startswith("component") or v.endswith("Component") else "control"
    child_order = OrderedDict()
    for path, val in y.items():
        segs = path.split("/")
        top = segs[0]
        if top in ("Screens", "Components", "ComponentDefinitions") and len(segs) >= 2:
            kind = "screen" if top == "Screens" else "component"
            out = [f"{kind}[{segs[1]}]"]
            rest = segs[2:]
        else:
            kind = kinds.get(top, "app" if top == "App" else "screen")
            out = [f"{kind}[{top}]"]
            rest = segs[1:]
        j = 0
        while j < len(rest):
            seg = rest[j]
            nxt = rest[j + 1] if j + 1 < len(rest) else None
            if seg == "Screens" and nxt is not None:
                out = [f"screen[{nxt}]"]
                j += 2
            elif seg == "Children" and nxt is not None:
                parent = "/".join(out)
                if nxt not in child_order.setdefault(parent, []):
                    child_order[parent].append(nxt)
                out.append(f"control[{nxt}]")
                j += 2
            elif seg == "Properties" and nxt is not None:
                out.append("@" + nxt)
                j += 2
            elif seg == "Control":
                out.append("@template")
                j += 1
            elif seg == "Groups" and nxt is not None:
                out.append(f"group[{nxt}]")
                j += 2
                if j < len(rest) and rest[j] == "ControlNames" and j + 1 < len(rest):
                    out.append(f"member[{rest[j + 1]}]")
                    j += 2
            elif seg in ("CustomProperties", "Parameters") and nxt is not None:
                out.append(f"{'customproperty' if seg == 'CustomProperties' else 'parameter'}[{nxt}]")
                j += 2
            else:
                out.append(("@" + seg) if j == len(rest) - 1 else seg)
                j += 1
        flat["/".join(out)] = str(val)
    for parent, names in child_order.items():  # document order is layout order in auto-layout containers
        if len(names) > 1:
            flat[f"{parent}/@child-order"] = " > ".join(names)
    roots = {k.split("/")[0] for k in flat}
    counts["screens"] = sum(1 for r in roots if r.startswith("screen["))
    counts["components"] = sum(1 for r in roots if r.startswith("component["))
    counts["controls"] = len({k.rsplit("/@", 1)[0] for k in flat if "/control[" in k})


def canvas_model(entries):
    """Normalize a canvas app package into {path: value} plus counts, from JSON controls or pa.yaml source.
    Environment-specific identifiers (connection instance ids, database instance URLs) are left out."""
    flat, counts = OrderedDict(), defaultdict(int)
    if entries is None:
        return None, counts
    skipped = list(entries.get("__skipped__") or [])
    lowered = {k.lower(): k for k in entries if k not in ("__assets__", "__skipped__")}
    templates = {}
    meta_key = lowered.get("componentsmetadata.json")
    if meta_key:
        try:
            for c in json.loads(entries[meta_key].decode("utf-8-sig")).get("Components") or []:
                if isinstance(c, dict) and c.get("TemplateName"):
                    templates[c["TemplateName"]] = c.get("Name", "")
        except Exception:
            pass
    for k in sorted(entries):
        kl = k.lower()
        if kl.startswith(("controls/", "components/")) and kl.endswith(".json"):
            try:
                doc = json.loads(entries[k].decode("utf-8-sig"))
            except Exception:
                skipped.append(f"{k} (unreadable)")
                continue
            top = doc.get("TopParent") if isinstance(doc, dict) else None
            if isinstance(top, dict):
                _json_controls(top, flat, "", counts, templates, "component" if kl.startswith("components/") else None)
            else:
                skipped.append(f"{k} (no TopParent)")
    if not counts["screens"] and not counts["components"]:
        y = OrderedDict()
        for k in sorted(entries):
            if k.lower().startswith("src/") and k.lower().endswith((".yaml", ".yml")):
                try:
                    y.update(_yaml_flatten(entries[k].decode("utf-8-sig")))
                except Exception:
                    continue
        if y:
            _yaml_entities(y, flat, counts)
    props_key = lowered.get("properties.json")
    if props_key:
        try:
            props = json.loads(entries[props_key].decode("utf-8-sig"))
            raw = props.get("LocalConnectionReferences")
            refs = json.loads(raw) if isinstance(raw, str) and raw.strip() else (raw if isinstance(raw, dict) else {})
            for cid, c in (refs.items() if isinstance(refs, dict) else []):
                if not isinstance(c, dict):
                    continue
                cref = c.get("connectionRef") if isinstance(c.get("connectionRef"), dict) else {}
                api = ""
                for cand in (cref.get("id", ""), c.get("connectionInstanceId", ""), c.get("id", "")):
                    m = re.search(r"/apis/([^/]+)", str(cand))
                    if m:
                        api = m.group(1)
                        break
                key = cref.get("logicalName") or _norm_api(api) or cid
                n_dup = 2
                while f"connection[{key}]" in flat:  # two connections to the same connector
                    key = f"{(cref.get('logicalName') or _norm_api(api) or cid)}#{n_dup}"
                    n_dup += 1
                if api:
                    flat[f"connection[{key}]/@connector"] = _norm_api(api)
                if cref.get("displayName"):
                    flat[f"connection[{key}]/@displayName"] = str(cref["displayName"])
                if cref.get("logicalName"):
                    flat[f"connection[{key}]/@reference"] = str(cref["logicalName"])
                for ds in (c.get("dataSources") or []):
                    flat[f"connection[{key}]/datasource[{ds}]"] = ""
                flat.setdefault(f"connection[{key}]", "")
                counts["connections"] += 1
            raw = props.get("LocalDatabaseReferences")
            dbs = json.loads(raw) if isinstance(raw, str) and raw.strip() else (raw if isinstance(raw, dict) else {})
            for dbname, d in (dbs.items() if isinstance(dbs, dict) else []):
                if not isinstance(d, dict):
                    continue
                for tname, t in (d.get("dataSources") or {}).items() if isinstance(d.get("dataSources"), dict) else []:
                    if isinstance(t, dict):
                        tkey = re.sub(r"^environment_[0-9a-f]+$", "environment", tname)
                        flat[f"database[{dbname}]/table[{tkey}]/@logicalName"] = re.sub(r"^environment_[0-9a-f]+$", "environment", str(t.get("logicalName", "")))
                counts["databases"] += 1
            for pk in ("Name", "DocumentLayoutWidth", "DocumentLayoutHeight", "DocumentLayoutOrientation", "DocumentAppType"):
                if pk in props and not isinstance(props[pk], (dict, list)):
                    flat[f"app[App]/@{pk}"] = str(props[pk])
        except Exception:
            pass
    ds_key = lowered.get("references/datasources.json")
    if ds_key:
        try:
            doc = json.loads(entries[ds_key].decode("utf-8-sig"))
            for ds in doc.get("DataSources") or []:
                if not isinstance(ds, dict):
                    continue
                n = ds.get("Name", "?")
                if ds.get("Type") in CONNECTED_DS_TYPES:
                    counts["datasources"] += 1
                for f in ("Type", "ServiceKind", "DatasetName", "TableName", "EntityName", "RelatedEntityName", "ConnectionReferenceLogicalName", "IsSampleData"):
                    if ds.get(f) not in (None, ""):
                        flat[f"datasource[{n}]/@{f}"] = str(ds[f])
                if ds.get("ApiId"):
                    flat[f"datasource[{n}]/@ApiId"] = re.sub(r"^environment_[0-9a-f]+$", "environment", _norm_api(str(ds["ApiId"]).rsplit("/", 1)[-1]))
                flat.setdefault(f"datasource[{n}]", "")
        except Exception:
            pass
    res_key = lowered.get("references/resources.json")
    if res_key:
        try:
            for r in json.loads(entries[res_key].decode("utf-8-sig")).get("Resources") or []:
                if isinstance(r, dict) and r.get("Name") and str(r.get("IsSampleData", "")).lower() != "true":
                    flat[f"resource[{r['Name']}]/@FileName"] = str(r.get("FileName") or r.get("Path", ""))
                    if r.get("Content"):
                        flat[f"resource[{r['Name']}]/@Content"] = str(r["Content"])
                    counts["resources"] += 1
        except Exception:
            pass
    for name, h in (entries.get("__assets__") or {}).items():
        short = re.sub(r"^(Assets|Resources)/", "", name).replace("/", ":")  # keys must not contain path separators
        flat[f"asset[{short}]"] = h
    counts["skipped"] = skipped
    return flat, counts


def extract_canvas(root, pkg, noise, components):
    for app in root.findall("CanvasApps/CanvasApp"):
        name = text(app, "Name")
        hashes = {}
        for tag in ("DocumentUri", "BackgroundImageUri", "SmallIconUri", "LargeIconUri", "MediumIconUri", "WideIconUri"):
            uri = text(app, tag)
            if uri:
                hashes[tag] = pkg.hash(uri) or "missing"
        if not hashes:
            hashes = attached_files(pkg, "CanvasApps", name, text(app, "CanvasAppId"))
        doc_uri = text(app, "DocumentUri")
        if not doc_uri:
            cands = [f for f in pkg.find("CanvasApps/") if f.lower().endswith(".msapp") and os.path.basename(f).lower().startswith(name.lower() + "_")]
            doc_uri = cands[0] if cands else ""
        model, counts = canvas_model(pkg.msapp(doc_uri) if doc_uri else None)
        flat = flatten(app, noise)
        if model is not None:
            for k, v in model.items():
                flat[f"canvas/{k}"] = v
        skipped = counts.get("skipped") or []
        opened = model is not None and not skipped and (counts.get("screens", 0) + counts.get("components", 0)) > 0
        if model is not None and not opened:
            flat = flatten(app, noise)  # do not keep a partial model; the hash fallback applies
        extra = {"display": text(app, "DisplayName"), "app_version": text(app, "AppVersion"), "files": hashes,
                 "opened": opened, "not_opened_reason": ("; ".join(skipped[:3]) if skipped else ("no screens or components found" if model is not None else "package could not be read")) if not opened else "",
                 "screens": counts.get("screens", 0), "components": counts.get("components", 0),
                 "controls": counts.get("controls", 0), "datasources": counts.get("datasources", 0), "connections": counts.get("connections", 0)}
        add(components, Component("Canvas apps", name, extra["display"] or name, flat, extra))


ENV_TYPES = {"100000000": "String", "100000001": "Number", "100000002": "Boolean", "100000003": "JSON",
             "100000004": "Data source", "100000005": "Secret"}


def extract_envvars(root, pkg, noise, components):
    for ev in root.findall("environmentvariabledefinitions/environmentvariabledefinition"):
        schema = ev.attrib.get("schemaname") or text(ev, "schemaname")
        values = [text(v, "value") for v in ev.findall("environmentvariablevalues/environmentvariablevalue")]
        extra = {"type": ENV_TYPES.get(text(ev, "type"), text(ev, "type")), "default": text(ev, "defaultvalue"),
                 "current_values": values, "display": text(ev, "displayname")}
        add(components, Component("Environment variables", schema, schema, flatten(ev, noise), extra))
    # Full exports may carry one folder per definition: environmentvariabledefinition.xml and, when a current value
    # is packaged, environmentvariablevalues.json. Merge both with any inline definition so a change confined to
    # the packaged value is still a change.
    folders = defaultdict(dict)
    for f in pkg.find("environmentvariabledefinitions/"):
        parts = f.split("/")
        if len(parts) >= 3:
            folders[parts[1]][parts[-1].lower()] = f
    for schema, files in folders.items():
        comp = components.get(("Environment variables", schema))
        if comp is None:
            xml_file = next((f for n, f in files.items() if n.endswith(".xml")), None)
            if xml_file:
                try:
                    el = ET.fromstring(pkg.files[xml_file])
                except ET.ParseError:
                    el = None
                if el is not None:
                    comp = Component("Environment variables", schema, schema, flatten(el, noise),
                                     {"type": ENV_TYPES.get(text(el, "type"), text(el, "type")), "default": text(el, "defaultvalue"),
                                      "current_values": [], "display": text(el, "displayname")})
                    add(components, comp)
        if comp is None:
            continue
        for n, f in files.items():
            if not n.endswith(".json"):
                continue
            try:
                doc = json.loads(pkg.files[f].decode("utf-8-sig"))
            except Exception:
                comp.flat[f"packagedvalues/{n}"] = (pkg.hash(f) or "unreadable")
                continue
            vals = []
            def walk(node):
                if isinstance(node, dict):
                    if "value" in node and any(k.lower().startswith(("environmentvariable", "schemaname")) for k in node):
                        vals.append(str(node.get("value")))
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)
            walk(doc)
            if vals:
                comp.extra["current_values"] = list(comp.extra.get("current_values") or []) + vals
                for i, v in enumerate(vals, 1):
                    comp.flat[f"environmentvariablevalue#{i}/value"] = v


HANDLED = {"Entities", "Workflows", "Roles", "WebResources", "CanvasApps", "environmentvariabledefinitions", "SolutionPluginAssemblies",
           "EntityRelationships", "optionsets", "SiteMaps", "AppModules", "Dashboards", "FieldSecurityProfiles",
           "SdkMessageProcessingSteps", "PluginAssemblies", "connectionreferences", "CustomControls",
           "customapis", "customapirequestparameters", "customapiresponseproperties", "bots", "botcomponents",
           "Languages", "Templates", "EntityMaps", "pluginpackages", "Reports", "Connectors", "connectors"}

SIMPLE = [
    ("EntityRelationships/EntityRelationship", "Relationships", "Name"),
    ("optionsets/optionset", "Choices (global)", "Name"),
    ("SiteMaps/SiteMap", "Sitemaps", "SiteMapUniqueName"),
    ("AppModules/AppModule", "Model-driven apps", "UniqueName"),
    ("Dashboards/Dashboard", "Dashboards", "FormId"),
    ("FieldSecurityProfiles/FieldSecurityProfile", "Field security profiles", "name"),
    ("SdkMessageProcessingSteps/SdkMessageProcessingStep", "Plug-in steps", "SdkMessageProcessingStepId"),
    ("PluginAssemblies/PluginAssembly", "Plug-in assemblies", "FullName"),
    ("SolutionPluginAssemblies/PluginAssembly", "Plug-in assemblies", "FullName"),
    ("connectionreferences/connectionreference", "Connection references", "connectionreferencelogicalname"),
    ("CustomControls/CustomControl", "Custom controls (PCF)", "Name"),
    ("customapis/customapi", "Custom APIs", "uniquename"),
    ("bots/bot", "Copilot Studio agents", "schemaname"),
    ("botcomponents/botcomponent", "Copilot Studio agent components", "schemaname"),
    ("EntityMaps/EntityMap", "Entity maps", "EntityMapId"),
]


def _asm_version(fullname: str) -> str:
    m = re.search(r"Version=(\d+)\.(\d+)", fullname or "")
    return f"{m.group(1)}.{m.group(2)}" if m else ""


def reconcile_assemblies(bc, cc):
    """Settle plug-in assembly identities across both packages. One version on each side compares by name (a
    version bump is a modification). When either side carries several versions of one assembly, every entry is
    keyed by name plus major.minor; a lone entry with no exact counterpart is paired with the closest version on
    the other side so it still compares as a modification rather than as a removal plus an addition."""
    def groups(comps):
        g = defaultdict(list)
        for (t, k), c in comps.items():
            if t == "Plug-in assemblies":
                g[c.extra.get("assembly") or k].append(c)
        return g
    gb, gc = groups(bc), groups(cc)
    def vt(c):
        return tuple(int(x) for x in (_asm_version(c.extra.get("fullname", "")) or "0.0").split("."))
    for name in set(gb) | set(gc):
        B, C = gb.get(name, []), gc.get(name, [])
        if len(B) <= 1 and len(C) <= 1:
            for c in B + C:
                c.key = c.label = name
            continue
        for c in B + C:
            c.key = c.label = f"{name} {_asm_version(c.extra.get('fullname', '')) or '?'}"
        for lone, many in ((B, C), (C, B)):
            if len(lone) == 1 and many and lone[0].key not in {m.key for m in many}:
                nearest = min(many, key=lambda m: abs(vt(m)[0] - vt(lone[0])[0]) * 1000 + abs(vt(m)[1] - vt(lone[0])[1]))
                lone[0].key = lone[0].label = nearest.key
    for comps in (bc, cc):
        items = list(comps.items())
        comps.clear()
        for (t, k), c in items:
            comps[(t, c.key if t == "Plug-in assemblies" else k)] = c


def extract_all(pkg: Package, noise: bool):
    components = OrderedDict()
    cdata = pkg.get("customizations.xml")
    if cdata is None:
        sys.exit(f"error: {pkg.label} has no customizations.xml (is this a solution export?)")
    root = parse_xml(cdata)
    for ent in root.findall("Entities/Entity"):
        extract_entity(ent, noise, components)
    extract_workflows(root, pkg, noise, components)
    extract_roles(root, noise, components)
    extract_webresources(root, pkg, noise, components)
    extract_canvas(root, pkg, noise, components)
    extract_customapi_params(root, noise, components)
    extract_envvars(root, pkg, noise, components)
    for path, ctype, key in SIMPLE:
        label_fn = None
        if ctype == "Dashboards":
            label_fn = lambda el: localized_name(el) or text(el, "FormId")
        if ctype == "Plug-in steps":
            label_fn = lambda el: el.attrib.get("Name") or text(el, "Name") or text(el, "SdkMessageProcessingStepId")
        if ctype == "Plug-in assemblies":
            # FullName embeds Version; key on the assembly name so version bumps show as modified. When two
            # versions of one assembly coexist in a package (side-by-side major versions), key each by
            # name plus major.minor so neither record hides the other.
            els = root.findall(path)
            by_name = defaultdict(list)
            for el in els:
                by_name[el.attrib.get("FullName", "").split(",")[0].strip()].append(el)
            for name, group in by_name.items():
                for i, el in enumerate(group):
                    full = el.attrib.get("FullName", "")
                    key = name if len(group) == 1 else f"{name} {_asm_version(full) or '#' + str(i + 1)}"
                    ident = el.attrib.get("PluginAssemblyId") or text(el, "PluginAssemblyId")
                    add(components, Component(ctype, key, key, flatten(el, noise),
                                              {"fullname": full, "assembly": name, "files": attached_files(pkg, "PluginAssemblies", name, ident)}))
            continue
        if ctype == "Custom controls (PCF)":
            for el in root.findall(path):
                name = text(el, "Name")
                add(components, Component(ctype, name, name, flatten(el, noise), {"files": attached_files(pkg, "Controls", name, text(el, "CustomControlId"))}))
            continue
        extract_simple(root, path, ctype, key, components, noise, label_fn)
    seen = defaultdict(list)
    for (t, k), c in components.items():
        if t == "Plug-in steps":
            seen[c.label].append(c)
    for lab, cs in seen.items():
        if len(cs) > 1:
            for c in cs:
                st = {"10": "pre-validation", "20": "pre-operation", "40": "post-operation"}.get(c.extra.get("stage"), c.extra.get("stage"))
                md = {"0": "sync", "1": "async"}.get(c.extra.get("mode"), c.extra.get("mode"))
                c.label = f"{lab} ({st}, {md}) [{c.key[:8]}]"
    for el in root.findall("pluginpackages/pluginpackage"):
        name = el.attrib.get("name") or text(el, "name") or el.attrib.get("uniquename") or text(el, "uniquename")
        add(components, Component("Plug-in packages", name, name, flatten(el, noise), {"files": attached_files(pkg, "pluginpackages", name, text(el, "pluginpackageid"))}))
    for el in root.findall("Reports/Report"):
        name = el.attrib.get("name") or text(el, "name") or text(el, "FileName")
        fname = text(el, "FileName")
        h = pkg.hash(fname) if fname else None
        add(components, Component("Reports", name, name, flatten(el, noise), {"files": {"rdl": h} if h else {}}))
    for coll_tag in ("Connectors", "connectors"):
        for el in root.findall(f"{coll_tag}/*"):
            key = component_key(el)
            name = key[len(el.tag) + 1:-1] if key != el.tag else ""
            add(components, Component("Custom connectors", key, name or key, flatten(el, noise),
                                      {"files": attached_files(pkg, "Connectors", name, text(el, "connectorid"))}))
    for wrapper in root.findall("Templates/*"):
        ctype = {"EmailTemplates": "Email templates", "MailMergeTemplates": "Mail merge templates",
                 "KBArticleTemplates": "Article templates", "ContractTemplates": "Contract templates"}.get(wrapper.tag, f"Templates: {wrapper.tag}")
        for el in wrapper:
            key = component_key(el)
            if key == el.tag:
                key = f"{el.tag}#{digest(flatten(el, noise))}"
            add(components, Component(ctype, key, key, flatten(el, noise)))
    # Generic fallback: any other collection.
    for coll in root:
        if coll.tag in HANDLED:
            continue
        children = list(coll)
        if not children:
            continue
        for el in children:
            key = component_key(el)
            if key == el.tag:
                key = f"{el.tag}#{digest(flatten(el, noise))}"
            label = key
            for c in el:
                if c.tag.lower() in ("name", "displayname", "msdyn_name") and (c.text or "").strip():
                    label = f"{key} ({c.text.strip()})"
                    break
            add(components, Component(f"Other: {coll.tag}", key, label, flatten(el, noise)))
    return components


def parse_manifest(pkg: Package):
    data = pkg.get("solution.xml")
    if data is None:
        return {"error": "solution.xml missing"}
    root = parse_xml(data)
    m = root.find("SolutionManifest")
    if m is None:
        return {"error": "SolutionManifest missing"}
    managed = text(m, "Managed", "0")
    out = {
        "unique_name": text(m, "UniqueName"),
        "display_name": localized_name(m),
        "version": text(m, "Version"),
        "managed": {"0": "Unmanaged", "1": "Managed", "2": "Both"}.get(managed, managed),
        "publisher": text(m.find("Publisher"), "UniqueName"),
        "prefix": text(m.find("Publisher"), "CustomizationPrefix"),
        "root_components": {},
        "missing_dependencies": [],
    }
    for rc in m.findall("RootComponents/RootComponent"):
        key = rc.attrib.get("schemaName") or rc.attrib.get("id", "")
        out["root_components"][f"{component_type_name(rc.attrib.get('type', '?'))}: {key}"] = rc.attrib.get("behavior", "")
    for md in m.findall("MissingDependencies/MissingDependency"):
        req = md.find("Required")
        dep = md.find("Dependent")
        out["missing_dependencies"].append({
            "required": f"{component_type_name(req.attrib.get('type', '?'))} {req.attrib.get('schemaName') or req.attrib.get('displayName') or req.attrib.get('id', '')} (solution {req.attrib.get('solution', '?')})" if req is not None else "?",
            "dependent": f"{component_type_name(dep.attrib.get('type', '?'))} {dep.attrib.get('schemaName') or dep.attrib.get('displayName') or dep.attrib.get('id', '')}" if dep is not None else "?",
        })
    return out


# --------------------------------------------------------------------------
# Comparison and risk flags
# --------------------------------------------------------------------------


def _ids_in(flat, suffixes):
    vals = set()
    for k, v in flat.items():
        if any(k.endswith(sfx) for sfx in suffixes) and v:
            vals.add(str(v).strip("{}").lower())
    return vals


def _keyed(flat, tags):
    """Values captured as keys in path segments such as attribute[p_old] or cell[p_old]."""
    vals = set()
    pat = re.compile(r"(?:^|/)(?:" + "|".join(re.escape(t) for t in tags) + r")\[([^\]]+)\]")
    for k in flat:
        for m in pat.finditer(k):
            vals.add(m.group(1).strip("{}").lower())
    return vals


def build_refs(components):
    """Indexes answering 'what uses X' for the deployment checklist."""
    idx = {"column_users": defaultdict(set), "webresource_users": defaultdict(set),
           "connref_users": defaultdict(set), "id_users": defaultdict(set)}
    for (ctype, key), c in components.items():
        if ctype in ("Forms", "Views", "Charts", "Dashboards"):
            table = c.parent or ""
            if c.extra.get("column_refs") is not None:  # views and charts: each column attributed to its owning table
                for ref in c.extra["column_refs"]:
                    idx["column_users"][ref].add(f"{ctype[:-1].lower()} {c.label}")
            else:
                cols = _ids_in(c.flat, ("/@datafieldname", "/@name", "/@uniqueid")) | _keyed(c.flat, ("attribute", "cell", "condition", "order", "control"))
                for col in cols:
                    if table:
                        idx["column_users"][f"{table}.{col}".lower()].add(f"{ctype[:-1].lower()} {c.label}")
            for lib in _keyed(c.flat, ("Library", "library")) | _ids_in(c.flat, ("/@libraryName", "/@libraryname", "/@library")):
                idx["webresource_users"][lib].add(f"{ctype[:-1].lower()} {c.label}")
        if ctype in ("Model-driven apps", "Dashboards", "Sitemaps"):
            for ident in _ids_in(c.flat, ("/@id", "/@schemaName", "/@Entity", "/@Id")):
                idx["id_users"][ident].add(f"{ctype.rstrip('s').lower()} {c.label}")
            for k in c.flat:
                m = re.search(r"AppModuleComponent\[([^\]]+)\]", k)
                if m:
                    idx["id_users"][m.group(1).strip("{}").lower()].add(f"app {c.label}")
        if ctype == "Cloud flows":
            flow = c.extra.get("flow") or {}
            for conn in (flow.get("connections") or {}).values():
                if conn.get("reference"):
                    idx["connref_users"][conn["reference"]].add(f"flow {c.label}")
        if ctype == "Command bars":
            for k, v in c.flat.items():
                if ("library" in k.lower() or "function" in k.lower()) and v and "$webresource:" in str(v):
                    idx["webresource_users"][str(v).split("$webresource:")[-1].strip().lower()].add(f"command bar {c.label}")
    return idx


def _upgrade_flag(flags, ctype, component, message):
    """Replace the generic 'removed' flag for a component with a more specific one, or add it."""
    for f in flags:
        if f["type"] == ctype and f["component"] == component and f.get("kind") == "removed":
            f["message"] = message
            f["severity"] = "high"
            return
    flag(flags, "high", ctype, component, message, kind="removed")


def cross_reference(results, bc, cc, flags):
    """Attach 'still used by' facts to removed/changed components and raise flags for dangling references."""
    refs_new = build_refs(cc)
    notes = []
    for item in results.get("Columns", {}).get("removed", []):
        users = sorted(refs_new["column_users"].get(item["key"].lower(), []))
        if users:
            item["still_used_by"] = users
            notes.append(f"Removed column {item['key']} is still referenced in the candidate by: {', '.join(users)}")
            _upgrade_flag(flags, "Columns", item["key"], f"removed but still referenced by {', '.join(users[:4])}; import or runtime will fail")
    for (ctype, key), c in cc.items():
        if ctype != "Canvas apps" or not c.extra.get("opened"):
            continue
        formulas = " ".join(str(v) for k, v in c.flat.items() if k.startswith(("canvas/screen[", "canvas/component[", "canvas/app[")) and "/@" in k)
        app_tables = {str(v).lower() for k, v in c.flat.items() if k.startswith("canvas/database[") and k.endswith("/@logicalName")}
        app_tables |= {str(v).lower() for k, v in c.flat.items() if k.startswith("canvas/datasource[") and k.endswith(("/@TableName", "/@EntityName"))}
        removed_tables = {item["key"] for item in results.get("Tables", {}).get("removed", [])}
        for item in results.get("Columns", {}).get("removed", []):
            table, col = item["key"].split(".", 1) if "." in item["key"] else ("", item["key"])
            if table in removed_tables or table.lower() not in app_tables:
                continue  # the app does not use this table, or the whole table went (already flagged)
            disp = (item.get("extra") or {}).get("display", "")
            # schema/logical names: Power Fx shows them in the export's casing (contoso_LegacyCode or contoso_legacycode)
            hit = re.search(r"(?<![A-Za-z0-9_])" + re.escape(col) + r"(?![A-Za-z0-9_'])", formulas, re.IGNORECASE)
            if not hit and disp and disp.lower() != col.lower() and len(disp) > 3:
                hit = re.search(r"'" + re.escape(disp) + r"'", formulas, re.IGNORECASE)  # quoted display name
                if not hit and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", disp):  # bare display identifier, exact case
                    hit = re.search(r"(?<![A-Za-z0-9_'.]|\.)" + re.escape(disp) + r"(?![A-Za-z0-9_'])", formulas) or \
                          re.search(r"\." + re.escape(disp) + r"(?![A-Za-z0-9_'])", formulas)
            if hit:
                item.setdefault("still_used_by", []).append(f"canvas app {c.label}")
                notes.append(f"Removed column {item['key']} is still referenced in formulas of canvas app {c.label}")
                _upgrade_flag(flags, "Columns", item["key"], f"removed but still referenced by {', '.join(item['still_used_by'][:4])}; import or runtime will fail")
        for item in results.get("Connection references", {}).get("added", []) + results.get("Connection references", {}).get("modified", []):
            if any(k.startswith("canvas/connection[") and k.endswith("/@reference") and v == item["key"] for k, v in c.flat.items()):
                item.setdefault("used_by", []).append(f"canvas app {c.label}")
    for t in ("Web resources",):
        for item in results.get(t, {}).get("modified", []) + results.get(t, {}).get("removed", []):
            users = sorted(refs_new["webresource_users"].get(item["key"].lower(), []))
            if users:
                item["used_by"] = users
                notes.append(f"Web resource {item['key']} is used by: {', '.join(users)}")
    for item in results.get("Connection references", {}).get("added", []) + results.get("Connection references", {}).get("modified", []):
        users = sorted(set(item.get("used_by", [])) | set(refs_new["connref_users"].get(item["key"], [])))
        if users:
            item["used_by"] = users
            notes.append(f"Connection reference {item['key']} is used by: {', '.join(users)}")
    for t in ("Views", "Forms"):
        for item in results.get(t, {}).get("removed", []):
            ident = item["key"].split(":")[-1]
            users = sorted(refs_new["id_users"].get(ident, []))
            if users:
                item["still_used_by"] = users
                _upgrade_flag(flags, t, item["label"], f"removed but still referenced by {', '.join(users[:4])}")
                notes.append(f"Removed {t[:-1].lower()} {item['label']} is still referenced by: {', '.join(users)}")
    return notes


def deployment_inputs(r):
    """Derive the checklist inputs an importer must supply, from the comparison."""
    comps = r["components"]
    out = OrderedDict()
    deps = [f["message"] for f in r["flags"] if f["type"] == "Dependencies"]
    if deps:
        out["Dependencies to install first"] = deps
    conns = []
    for item in comps.get("Connection references", {}).get("added", []):
        conns.append(f"{item['key']} (new)" + (f", used by {', '.join(item['used_by'])}" if item.get("used_by") else ""))
    for item in comps.get("Connection references", {}).get("modified", []):
        conns.append(f"{item['key']} (changed)" + (f", used by {', '.join(item['used_by'])}" if item.get("used_by") else ""))
    listed = {item["key"] for item in comps.get("Connection references", {}).get("added", []) + comps.get("Connection references", {}).get("modified", [])}
    for f in r["flags"]:
        if f["type"] == "Cloud flows" and "needs a connection" in f["message"]:
            m = re.search(r"via reference '([^']+)'", f["message"])
            if m and m.group(1) in listed:
                continue  # already listed under its connection reference
            conns.append(f"{f['component']}: {f['message']}")
    if conns:
        out["Connections to bind"] = conns
    envs = []
    for item in comps.get("Environment variables", {}).get("added", []):
        ex = item.get("extra", {})
        envs.append(f"{item['key']} ({ex.get('type', 'unknown type')}; default: {ex.get('default') or 'none'}; packaged value: {'yes' if ex.get('current_values') else 'no'})")
    for item in comps.get("Environment variables", {}).get("modified", []):
        envs.append(f"{item['key']} (changed; check the target value)")
    if envs:
        out["Environment variable values to confirm"] = envs
    code = []
    for t in ("Plug-in assemblies", "Plug-in packages", "Custom controls (PCF)", "Custom connectors", "Reports"):
        for item in comps.get(t, {}).get("added", []) + comps.get(t, {}).get("modified", []):
            code.append(f"{t}: {item['label']}")
    if code:
        out["Binaries that change (not inspected)"] = code
    act = [f"{f['component']}: {f['message']}" for f in r["flags"] if "activation state" in f["message"]]
    if act:
        out["Processes changing activation state"] = act
    removed = []
    for t, bkt in comps.items():
        for item in bkt.get("removed", []):
            removed.append(f"{t}: {item['label']}")
    if removed:
        out["Components removed (managed target needs Upgrade or Stage for upgrade to delete them; Update keeps them)"] = removed[:40] + ([f"… {len(removed) - 40} more"] if len(removed) > 40 else [])
    return out


def version_tuple(v: str):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return None


def flag(flags, severity, ctype, key, message, kind=""):
    flags.append({"severity": severity, "type": ctype, "component": key, "message": message, "kind": kind})


def _norm_api(name: str) -> str:
    """Custom connector api names carry an environment-specific suffix; strip it for comparison."""
    return re.sub(r"-[0-9a-f]{5,}$", "", name or "")


def compare_flow(old, new, flags, key, old_hash=None, new_hash=None):
    detail = []
    if not old or not new or "error" in old or "error" in new:
        side = "candidate" if (not new or "error" in (new or {})) else "baseline"
        detail.append(f"flow definition missing or unparseable in the {side}; compared by file hash only")
        flag(flags, "medium", "Cloud flows", key, f"flow JSON missing or unparseable in the {side}; definition changes cannot be listed")
        if old_hash != new_hash:
            detail.append("definition file content differs")
        return detail
    for t, v in old["triggers"].items():
        if t in new["triggers"] and v.get("kind") != new["triggers"][t].get("kind") and v["type"] == new["triggers"][t]["type"]:
            detail.append(f"trigger kind changed: {t} ({v.get('kind')} -> {new['triggers'][t].get('kind')})")
            flag(flags, "high", "Cloud flows", key, f"trigger '{t}' kind changed {v.get('kind')} -> {new['triggers'][t].get('kind')}")
            continue
        if t not in new["triggers"]:
            detail.append(f"trigger removed: {t} ({v['type']})")
            flag(flags, "high", "Cloud flows", key, f"trigger '{t}' removed")
        elif v != new["triggers"][t]:
            diffs = leaf_diff_lines(v.get("leaves", {}), new["triggers"][t].get("leaves", {}))
            if v["type"] != new["triggers"][t]["type"]:
                detail.append(f"trigger changed: {t} ({v['type']} -> {new['triggers'][t]['type']})")
            else:
                detail.append(f"trigger inputs changed: {t} ({v['type']})")
            detail.extend(f"  {d}" for d in diffs)
            flag(flags, "high", "Cloud flows", key, f"trigger '{t}' changed: " + "; ".join(diffs[:3]))
    for t, v in new["triggers"].items():
        if t not in old["triggers"]:
            detail.append(f"trigger added: {t} ({v['type']})")
            flag(flags, "high", "Cloud flows", key, f"trigger '{t}' added")
    oa, na = old["actions"], new["actions"]
    moved = {}
    for a in oa:
        if a not in na:
            leaf = a.rsplit("/", 1)[-1]
            cands = [b for b in na if b not in oa and b.rsplit("/", 1)[-1] == leaf and na[b]["hash"] == oa[a]["hash"]]
            if cands:
                moved[a] = cands[0]
    for a in oa:
        if a in moved:
            detail.append(f"action moved: {a} -> {moved[a]} ({oa[a]['type']})")
        elif a not in na:
            detail.append(f"action removed: {a} ({oa[a]['type']})")
        else:
            if oa[a]["hash"] != na[a]["hash"] or oa[a]["type"] != na[a]["type"]:
                detail.append(f"action changed: {a} ({oa[a]['type']}" + (f" -> {na[a]['type']}" if oa[a]['type'] != na[a]['type'] else "") + ")")
                detail.extend(f"  {d}" for d in leaf_diff_lines(oa[a].get("leaves", {}), na[a].get("leaves", {}), 6))
        if a in na and a not in moved and oa[a]["runAfter"] != na[a]["runAfter"]:  # independent of input changes
            ora, nra = oa[a]["runAfter"], na[a]["runAfter"]
            if isinstance(ora, dict) and isinstance(nra, dict) and sorted(ora) == sorted(nra):
                conds = [f"{p}: {'/'.join(ora[p])} -> {'/'.join(nra[p])}" for p in sorted(ora) if ora[p] != nra[p]]
                detail.append(f"action run condition changed: {a} ({'; '.join(conds)})")
                flag(flags, "medium", "Cloud flows", key, f"action '{a.rsplit('/', 1)[-1]}' now runs on a different outcome of its predecessor ({'; '.join(conds[:2])})")
            else:
                detail.append(f"action re-ordered: {a} (after {', '.join(sorted(ora)) or 'start'} -> after {', '.join(sorted(nra)) or 'start'})")
    moved_to = set(moved.values())
    for a in na:
        if a not in oa and a not in moved_to:
            conn = f", connection {na[a]['connection']}" if na[a].get("connection") else ""
            detail.append(f"action added: {a} ({na[a]['type']}{conn})")
    removed = [d for d in detail if d.startswith("action removed")]
    if removed:
        flag(flags, "medium", "Cloud flows", key, f"{len(removed)} action(s) removed")
    changed = [d for d in detail if d.startswith("action changed")]
    added = [d for d in detail if d.startswith("action added")]
    if changed or added:
        bits = ([f"{len(changed)} action(s) changed (inputs, type, or case selectors)"] if changed else []) + ([f"{len(added)} action(s) added"] if added else [])
        flag(flags, "medium", "Cloud flows", key, "; ".join(bits) + "; run the flow end to end in a test environment")
    for c, v in new["connections"].items():
        if c not in old["connections"]:
            detail.append(f"connection added: {c} -> {v['api']} via {v['reference'] or 'embedded'}")
            flag(flags, "medium", "Cloud flows", key, f"new connection '{v['api']}' via reference '{v['reference'] or 'embedded'}' needs a connection at deployment")
        else:
            ov = old["connections"][c]
            diffs = []
            if ov.get("reference") != v.get("reference"):
                diffs.append(f"reference {ov.get('reference') or 'embedded'} -> {v.get('reference') or 'embedded'}")
            if ov.get("runtimeSource") != v.get("runtimeSource"):
                diffs.append(f"runtime source {ov.get('runtimeSource')} -> {v.get('runtimeSource')}")
            if _norm_api(ov.get("api")) != _norm_api(v.get("api")):
                diffs.append(f"connector {ov.get('api')} -> {v.get('api')}")
            if diffs:
                detail.append(f"connection changed: {c} ({'; '.join(diffs)})")
                flag(flags, "medium", "Cloud flows", key, f"connection '{c}' changed: {'; '.join(diffs)}")
    for c in old["connections"]:
        if c not in new["connections"]:
            detail.append(f"connection removed: {c}")
    op, npar = old.get("parameters") or {}, new.get("parameters") or {}
    if isinstance(op, dict) and isinstance(npar, dict):
        for p in op:
            if p not in npar:
                detail.append(f"parameter removed: {_show_path(p)}")
            elif op[p] != npar[p]:
                detail.append(f"parameter changed: {_show_path(p)} ({op[p]} -> {npar[p]})")
        for p in npar:
            if p not in op:
                detail.append(f"parameter added: {_show_path(p)} = {npar[p]}")
        pchanged = [d for d in detail if d.startswith("parameter ")]
        if pchanged:
            flag(flags, "medium", "Cloud flows", key, f"{len(pchanged)} flow definition parameter(s) changed; defaults and dependent values change behavior")
    ob, nb = old.get("bindings") or {}, new.get("bindings") or {}
    if isinstance(ob, dict) and isinstance(nb, dict) and ob != nb:
        bl = []
        for b in ob:
            if b not in nb:
                bl.append(f"parameter binding removed: {_show_path(b)}")
            elif ob[b] != nb[b]:
                bl.append(f"parameter binding changed: {_show_path(b)} ({ob[b]} -> {nb[b]})")
        for b in nb:
            if b not in ob:
                bl.append(f"parameter binding added: {_show_path(b)} = {nb[b]}")
        detail.extend(bl)
        flag(flags, "medium", "Cloud flows", key, f"{len(bl)} runtime parameter binding(s) changed (properties.parameters); values used by @parameters() change")
    if not detail and old.get("def_hash") and new.get("def_hash") and old["def_hash"] != new["def_hash"]:
        detail.append("flow definition changed in parts not itemized above (normalized definition digest differs); review the definition JSON")
        flag(flags, "medium", "Cloud flows", key, "definition changed in parts the comparison does not itemize; review the flow JSON and run the flow end to end")
    return detail


REQUIRED = {"required", "applicationrequired", "systemrequired"}


REMOVED_MESSAGES = {
    "Tables": "table removed; its rows, columns, forms, views, and every reference to it go with it on an Upgrade import",
    "Columns": "column removed; forms, views, flows, plug-ins, reports, and integrations that read it break, and its data is deleted on an Upgrade import",
    "Relationships": "relationship removed; lookups and related-record navigation that depend on it break",
    "Choices (global)": "global choice removed; every column using it loses its options",
    "Forms": "form removed; users and apps that open it fall back to another form or fail",
    "Views": "view removed; apps, dashboards, charts, and bookmarks that use it break",
    "Security roles": "role removed; users holding it lose that access on an Upgrade import",
    "Connection references": "connection reference removed; flows that still use it fail to activate",
    "Environment variables": "environment variable removed; flows, apps, and plug-ins that read it fail",
    "Plug-in steps": "plug-in step removed; the validation or side effect it performed silently stops",
    "Cloud flows": "flow removed; automation it performed stops",
    "Custom APIs": "custom API removed; callers and integrations fail",
    "Custom API request parameters": "custom API request parameter removed; existing callers break",
    "Custom API response properties": "custom API response property removed; callers reading it break",
    "Web resources": "web resource removed; forms and commands that load it break",
    "Model-driven apps": "app removed; users lose the navigation surface",
}


def assess(ctype, comp_old, comp_new, status, changes, flags, removed_parents=frozenset(), added_parents=frozenset(), patch=False):
    key = comp_new.key if comp_new else comp_old.key
    label = (comp_new or comp_old).label
    if (comp_new or comp_old).parent in removed_parents:
        return  # the parent table's removal already carries the finding
    if status == "removed" and patch:
        return  # components absent from a patch are not removed by it
    if status == "removed":
        sev = "high" if ctype in {"Tables", "Columns", "Relationships", "Choices (global)", "Security roles",
                                  "Connection references", "Environment variables", "Plug-in steps", "Cloud flows",
                                  "Custom APIs", "Custom API request parameters", "Custom API response properties", "Forms", "Views", "Model-driven apps", "Web resources",
                                  "Business rules", "Business process flows", "Classic workflows", "Custom actions",
                                  "Plug-in assemblies", "Plug-in packages", "Custom connectors"} else "medium"
        flag(flags, sev, ctype, label, REMOVED_MESSAGES.get(ctype, "removed; dependent components and integrations may break"), kind="removed")
        return
    if status == "added":
        if ctype == "Environment variables":
            vals = comp_new.extra.get("current_values") or []
            if comp_new.extra.get("type") in ("Data source", "Secret"):
                flag(flags, "medium", ctype, label, f"new {comp_new.extra.get('type').lower()} variable; bind it in the target at import")
            elif not vals and not comp_new.extra.get("default"):
                flag(flags, "medium", ctype, label, "new variable with no default or current value; set it at deployment")
            else:
                flag(flags, "low", ctype, label, "new variable; confirm the target environment value")
        elif ctype == "Connection references":
            flag(flags, "medium", ctype, label, "new connection reference; a connection must be supplied at import")
        elif ctype == "Columns":
            if comp_new.extra.get("required") in REQUIRED and comp_new.parent not in added_parents:
                flag(flags, "medium", ctype, label, "new required column on an existing table; existing records and integrations that create rows need a value")
        elif ctype in ("Plug-in steps", "Security roles", "Tables"):
            flag(flags, "low", ctype, label, "added; review for intent")
        elif ctype in ("Classic workflows", "Business rules", "Business process flows", "Custom actions", "Cloud flows", "Desktop flows", "Dialogs"):
            if str(comp_new.extra.get("state")) == "1":
                flag(flags, "medium", ctype, label, "new process with activation state activated/on; it starts running after import once its connections are satisfied")
        return
    # modified
    if ctype == "Columns":
        o, n = comp_old.extra, comp_new.extra
        if o.get("type") != n.get("type"):
            flag(flags, "high", ctype, label, f"data type changed {o.get('type')} -> {n.get('type')}; not supported in place on managed targets")
        if o.get("required") != n.get("required") and n.get("required") in REQUIRED and o.get("required") not in REQUIRED:
            flag(flags, "medium", ctype, label, f"required level raised to {n.get('required')}")
        try:
            if o.get("maxlength") and n.get("maxlength") and int(n["maxlength"]) < int(o["maxlength"]):
                flag(flags, "high", ctype, label, f"max length reduced {o['maxlength']} -> {n['maxlength']}; existing data may exceed it")
        except ValueError:
            pass
        if o.get("format") != n.get("format"):
            flag(flags, "low", ctype, label, f"format changed {o.get('format')} -> {n.get('format')}")
    if ctype == "Choices (global)" or (ctype == "Columns" and comp_new.extra.get("type", "").lower() in ("picklist", "state", "status", "multiselectpicklist", "virtual")):
        old_opts, new_opts = comp_old.extra.get("options", {}), comp_new.extra.get("options", {})
        rem = sorted(v for v in old_opts if v not in new_opts)
        if rem:
            desc = ", ".join(f"{v} ('{old_opts[v]}')" if old_opts[v] else v for v in rem)
            flag(flags, "high", ctype, label, f"choice value{'s' if len(rem) > 1 else ''} removed: {desc}; rows holding {'them' if len(rem) > 1 else 'it'} become invalid")
        new_vals = sorted(v for v in new_opts if v not in old_opts)
        if new_vals:
            flag(flags, "low", ctype, label, f"choice value{'s' if len(new_vals) > 1 else ''} added: " + ", ".join(f"{v} ('{new_opts[v]}')" if new_opts[v] else v for v in new_vals))
        relabel = [c for c in changes if c["kind"] == "changed" and "option[" in c["path"] and "@description" in c["path"]]
        if relabel:
            flag(flags, "low", ctype, label, f"{len(relabel)} choice label(s) renamed")
    if ctype == "Security roles":
        o, n = comp_old.extra["privileges"], comp_new.extra["privileges"]
        order = {"None": 0, "Basic": 1, "Local": 2, "Deep": 3, "Global": 4}
        lowered = [p for p in o if p in n and order.get(n[p], 0) < order.get(o[p], 0)]
        dropped = [p for p in o if p not in n]
        raised = [p for p in n if p in o and order.get(n[p], 0) > order.get(o[p], 0)]
        new = [p for p in n if p not in o]
        if lowered or dropped:
            flag(flags, "high", ctype, label, f"privileges reduced or removed: {', '.join(sorted(lowered + dropped))[:300]}")
        if raised or new:
            flag(flags, "medium", ctype, label, f"privileges raised or added: {', '.join(sorted(raised + new))[:300]}")
    if ctype == "Plug-in steps":
        for c in changes:
            tag = c["path"].rsplit("/", 1)[-1].lstrip("@")
            if tag in ("Stage", "Mode", "FilteringAttributes", "SdkMessage", "PrimaryEntity", "Rank", "StateCode"):
                names = {"Stage": {"10": "pre-validation", "20": "pre-operation", "40": "post-operation"}, "Mode": {"0": "synchronous", "1": "asynchronous"}}.get(tag, {})
                flag(flags, "medium", ctype, label, f"{tag} changed {names.get(c.get('old'), c.get('old'))} -> {names.get(c.get('new'), c.get('new'))}")
    if ctype == "Plug-in assemblies":
        what = []
        changes = [c for c in changes if not c["path"].endswith("@FullName")]
        if comp_old.extra.get("fullname") != comp_new.extra.get("fullname"):
            def ver(full):
                m = re.search(r"Version=([\d.]+)", full or "")
                return m.group(1) if m else (full or "?")
            what.append(f"version {ver(comp_old.extra.get('fullname'))} -> {ver(comp_new.extra.get('fullname'))}")
        if comp_old.extra.get("files") != comp_new.extra.get("files"):
            what.append("assembly file content changed")
        if changes:
            what.append("registration metadata changed")
        flag(flags, "medium", ctype, label, "; ".join(what) + "; new code is not inspected, ask for the code change log")
    if ctype in ("Plug-in packages", "Custom connectors", "Custom controls (PCF)", "Reports") and comp_old.extra.get("files") != comp_new.extra.get("files"):
        flag(flags, "medium", ctype, label, "packaged files changed; internal content is not inspected")
    if ctype == "Environment variables":
        o, n = comp_old.extra, comp_new.extra
        if o.get("default") != n.get("default"):
            flag(flags, "medium", ctype, label, f"default value changed; targets without a current value will change behavior")
        if o.get("current_values") != n.get("current_values"):
            flag(flags, "medium", ctype, label, "current value packaged in the solution changed")
    if ctype == "Connection references":
        flag(flags, "medium", ctype, label, "connection reference changed; verify connector and connection at import")
    if ctype == "Relationships":
        for c in changes:
            if "Cascade" in c["path"] or "RelationshipType" in c["path"]:
                flag(flags, "medium", ctype, label, f"{c['path'].rsplit('/',1)[-1]} changed {c.get('old')} -> {c.get('new')}")
    if ctype in ("Classic workflows", "Business rules", "Business process flows", "Custom actions", "Cloud flows", "Desktop flows", "Dialogs"):
        for c in changes:
            if c["path"].rsplit("/", 1)[-1].lstrip("@") == "StateCode":
                state = {"0": "draft/off", "1": "activated/on"}
                flag(flags, "medium", ctype, label, f"activation state changed {state.get(c.get('old'), c.get('old'))} -> {state.get(c.get('new'), c.get('new'))}")
    if ctype == "Canvas apps":
        opened = comp_old.extra.get("opened") and comp_new.extra.get("opened")
        if not opened:
            reason = comp_new.extra.get("not_opened_reason") or comp_old.extra.get("not_opened_reason") or "package could not be read"
            if comp_old.extra.get("files") != comp_new.extra.get("files"):
                flag(flags, "medium", ctype, label, f"canvas app package changed but its content could not be compared ({reason}); compare with pac canvas unpack")
            else:
                flag(flags, "low", ctype, label, "canvas app metadata changed; the packaged .msapp is identical (repackage, not a code change)")
        else:
            cv = [dict(c, path=c["path"][len("canvas/"):], new_path=(c.get("new_path") or "")[len("canvas/"):] if (c.get("new_path") or "").startswith("canvas/") else c.get("new_path", ""))
                  for c in changes if c["path"].startswith("canvas/")]
            def roots(kind, prefix):
                return sorted({re.match(r"^" + prefix + r"\[([^\]]+)\]", c["path"]).group(1) for c in cv
                               if c["kind"] == kind and re.match(r"^" + prefix + r"\[[^\]]+\]$", c["path"])})
            def ds_type(flat, name):
                return flat.get(f"canvas/datasource[{name}]/@Type", "")
            ds_added = [n for n in roots("added", "datasource") if ds_type(comp_new.flat, n) in CONNECTED_DS_TYPES]
            ds_removed = [n for n in roots("removed", "datasource") if ds_type(comp_old.flat, n) in CONNECTED_DS_TYPES]
            cn_added, cn_removed = roots("added", "connection"), roots("removed", "connection")
            if ds_added or cn_added:
                flag(flags, "medium", ctype, label, "new data source(s) or connection(s): " + ", ".join(ds_added + cn_added) + "; users need access and a connection at first run")
            if ds_removed or cn_removed:
                flag(flags, "medium", ctype, label, "data source(s) or connection(s) removed: " + ", ".join(ds_removed + cn_removed) + "; formulas that still use them fail")
            renamed = [c for c in cv if c["kind"] == "renamed"]
            scr_renamed = [c for c in renamed if re.match(r"^(screen|component)\[", c["path"]) and "/" not in c["path"]]
            scr_removed = roots("removed", "screen") + roots("removed", "component")
            if scr_removed:
                flag(flags, "medium", ctype, label, "screen(s) or component(s) removed: " + ", ".join(scr_removed) + "; navigation or instances that target them fail")
            if scr_renamed:
                flag(flags, "medium", ctype, label, "screen(s) or component(s) renamed: " + ", ".join(f"{c['path']} -> {c['new_path']}" for c in scr_renamed) + "; Navigate() calls and component instances must use the new name")
            tests = [c for c in cv if c["path"].startswith("test[")]
            if tests:
                flag(flags, "low", ctype, label, f"Test Studio objects changed ({len(tests)} change(s)); no runtime impact")
            parts = []
            scr_added = roots("added", "screen") + roots("added", "component")
            if scr_added:
                parts.append(f"{len(scr_added)} screen(s)/component(s) added")
            ctrl_added = [c for c in cv if c["kind"] == "added" and c["path"].split("/")[-1].startswith("control[")]
            ctrl_removed = [c for c in cv if c["kind"] == "removed" and c["path"].split("/")[-1].startswith("control[")]
            if ctrl_added:
                parts.append(f"{len(ctrl_added)} control(s) added")
            if ctrl_removed:
                parts.append(f"{len(ctrl_removed)} control(s) removed")
            order = [c for c in cv if c["kind"] == "changed" and c["path"].endswith("/@child-order")]
            if order:
                parts.append(f"{len(order)} control order change(s)")
            props = [c for c in cv if c["kind"] in ("changed", "added", "removed") and "/@" in c["path"] and not c["path"].endswith(("/@template", "/@child-order")) and c["path"].startswith(("screen[", "component[", "app["))]
            if props:
                kinds = {"changed": "changed", "added": "added", "removed": "removed"}
                summary = ", ".join(f"{sum(1 for c in props if c['kind'] == k)} {v}" for k, v in kinds.items() if any(c["kind"] == k for c in props))
                parts.append(f"{len(props)} property formula(s) {summary}" if len(set(c["kind"] for c in props)) > 1 else f"{len(props)} property formula(s) {props[0]['kind']}")
            tmpls = [c for c in cv if c["kind"] == "changed" and c["path"].endswith("/@template")]
            if tmpls:
                parts.append(f"{len(tmpls)} control type or version change(s)")
            cps = [c for c in cv if "/customproperty[" in c["path"]]
            if cps:
                flag(flags, "medium", ctype, label, f"component custom property definition(s) changed ({len(cps)} change(s)); every instance of the component is affected")
            if renamed and not scr_renamed:
                parts.append(f"{len(renamed)} control(s) renamed")
            members = [c for c in cv if "/member[" in c["path"]]
            if members:
                parts.append(f"{len(members)} group membership change(s)")
            media = [c for c in cv if c["path"].startswith(("asset[", "resource["))]
            if media:
                parts.append(f"{len(media)} media or resource change(s)")
            if parts:
                flag(flags, "low", ctype, label, "app content changed: " + ", ".join(parts) + "; test the affected screens")
            if not cv:
                flag(flags, "low", ctype, label, "app re-saved or metadata changed; no screen, control, formula, data source, connection, or media differences found")
    if ctype in ("Forms", "Views", "Dashboards", "Sitemaps"):
        kinds = {"added": 0, "removed": 0, "changed": 0}
        for c in changes:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        parts = [f"{v} {k}" for k, v in kinds.items() if v]
        if parts:
            flag(flags, "low", ctype, label, f"{ctype[:-1].lower()} layout or query changed: {', '.join(parts)}; verify in a test environment")
    if ctype == "Tables":
        for c in changes:
            tag = c["path"].rsplit("/", 1)[-1].lstrip("@")
            if tag in ("OwnershipTypeMask", "IsAuditEnabled", "IsActivity", "EntitySetName", "IsValidForQueue", "ChangeTrackingEnabled"):
                flag(flags, "medium", ctype, label, f"{tag} changed {c.get('old')} -> {c.get('new')}")


def compare(base: Package, cand: Package, noise: bool, limit: int, only_types=None):
    bm, cm = parse_manifest(base), parse_manifest(cand)
    bc, cc = extract_all(base, noise), extract_all(cand, noise)
    reconcile_assemblies(bc, cc)
    warnings, flags = [], []
    bn, cn = bm.get("unique_name", ""), cm.get("unique_name", "")
    strip = lambda n: re.sub(r"_(Patch|Upgrade)(_[0-9a-fA-F]+)?$", "", n)
    is_patch = lambda n: bool(re.search(r"_Patch(_[0-9a-fA-F]+)?$", n or ""))
    patch = is_patch(cn)
    if patch and bn == cn:
        warnings.append(f"Both packages are versions of the patch '{cn}'. A patch carries only changed components: components absent from the candidate are not removed on import, so no removal findings are raised.")
    if bn and cn and bn != cn:
        if strip(cn) == strip(bn) and patch:
            warnings.append(f"Candidate '{cn}' is a patch of '{bn}'. A patch carries only changed components: components absent from it are not removed, so no removal findings are raised.")
        elif patch:
            warnings.append(f"Candidate '{cn}' is a patch, but of a different solution than baseline '{bn}'. Components absent from it are not removed on import; no removal findings are raised.")
        elif strip(cn) == strip(bn):
            warnings.append(f"Candidate '{cn}' is an upgrade holding solution for '{bn}'; results compare it with the base solution.")
        else:
            warnings.append(f"Different solutions: baseline '{bn}' vs candidate '{cn}'. Results compare two distinct solutions, not two versions of one.")
    if bm.get("managed") != cm.get("managed"):
        warnings.append(f"Package types differ: baseline is {bm.get('managed')}, candidate is {cm.get('managed')}. Managed and unmanaged exports differ in metadata; expect extra noise.")
    bv, cv = version_tuple(bm.get("version", "")), version_tuple(cm.get("version", ""))
    if bv and cv and cv <= bv:
        warnings.append(f"Candidate version {cm['version']} is not higher than baseline {bm['version']}. Confirm which package is newer; an import of a lower version onto a managed target is rejected.")
    if bm.get("publisher") != cm.get("publisher"):
        warnings.append(f"Publisher differs: {bm.get('publisher')} vs {cm.get('publisher')}. A solution with the same unique name but a different publisher cannot be imported over the installed one.")
    added_deps = [d for d in cm.get("missing_dependencies", []) if d not in bm.get("missing_dependencies", [])]
    for d in added_deps:
        flag(flags, "high", "Dependencies", d["dependent"], f"new missing dependency on {d['required']}")

    removed_parents = {k for (t, k) in bc if t == "Tables" and (t, k) not in cc}
    added_parents = {k for (t, k) in cc if t == "Tables" and (t, k) not in bc}
    results = OrderedDict()
    preferred = ["Tables", "Columns", "Relationships", "Choices (global)", "Forms", "Views", "Charts", "Command bars",
                 "Dashboards", "Sitemaps", "Model-driven apps", "Canvas apps", "Custom controls (PCF)", "Web resources",
                 "Security roles", "Field security profiles", "Business rules", "Business process flows",
                 "Classic workflows", "Custom actions", "Dialogs", "Cloud flows", "Desktop flows", "AI flows", "Processes",
                 "Custom APIs", "Custom API request parameters", "Custom API response properties", "Plug-in packages", "Plug-in assemblies", "Plug-in steps",
                 "Custom connectors", "Connection references", "Environment variables", "Reports",
                 "Copilot Studio agents", "Copilot Studio agent components", "Email templates", "Mail merge templates",
                 "Article templates", "Contract templates", "Entity maps"]
    present = list(dict.fromkeys([k[0] for k in bc] + [k[0] for k in cc]))
    types = [t for t in preferred if t in present] + sorted(t for t in present if t not in preferred)
    for t in types:
        bucket = {"added": [], "removed": [], "modified": [], "unchanged": 0, "unchanged_names": []}
        keys = list(dict.fromkeys([k for (tt, k) in bc if tt == t] + [k for (tt, k) in cc if tt == t]))
        for k in keys:
            o, n = bc.get((t, k)), cc.get((t, k))
            if o and not n:
                if patch:
                    bucket["unchanged"] += 0  # absent from a patch is not a removal; do not list
                    continue
                bucket["removed"].append({"key": k, "label": o.label, "extra": {kk: vv for kk, vv in o.extra.items() if kk not in ("flow", "options")}})
                assess(t, o, None, "removed", [], flags, removed_parents, added_parents, patch)
            elif n and not o:
                bucket["added"].append({"key": k, "label": n.label, "extra": {kk: vv for kk, vv in n.extra.items() if kk not in ("flow", "options")}})
                assess(t, None, n, "added", [], flags, removed_parents, added_parents, patch)
            else:
                all_changes, total = diff_flat(o.flat, n.flat, 10 ** 9)
                changes = all_changes[:limit]
                ignore = {"flow", "json_hash"} if t == "Cloud flows" else set()
                extra_changed = {kk: vv for kk, vv in o.extra.items() if kk not in ignore} != {kk: vv for kk, vv in n.extra.items() if kk not in ignore}
                detail = []
                if t == "Cloud flows":
                    detail = compare_flow(o.extra.get("flow"), n.extra.get("flow"), flags, o.label, o.extra.get("json_hash"), n.extra.get("json_hash"))
                if t == "Web resources" and o.extra.get("content_hash") != n.extra.get("content_hash"):
                    line = f"file content changed ({o.extra.get('size')} -> {n.extra.get('size')} bytes, hash {o.extra.get('content_hash')} -> {n.extra.get('content_hash')})"
                    od, nd = base.get(o.extra.get("file", "")), cand.get(n.extra.get("file", ""))
                    if od is not None and nd is not None and n.extra.get("type") in ("1", "2", "3", "4", "9", "10", "12"):
                        try:
                            import difflib
                            ol, nl = od.decode("utf-8-sig").splitlines(), nd.decode("utf-8-sig").splitlines()
                            plus = minus = 0
                            for d in difflib.unified_diff(ol, nl, lineterm="", n=0):
                                if d.startswith("+") and not d.startswith("+++"):
                                    plus += 1
                                elif d.startswith("-") and not d.startswith("---"):
                                    minus += 1
                            line += f"; text diff: +{plus} / -{minus} lines"
                        except UnicodeDecodeError:
                            pass
                    detail.append(line)
                if t == "Canvas apps" and not (o.extra.get("opened") and n.extra.get("opened")):
                    all_changes = [c for c in all_changes if not c["path"].startswith("canvas/")]
                    changes = all_changes[:limit]
                    total = len(all_changes)
                if t == "Canvas apps":
                    if o.extra.get("opened") and n.extra.get("opened"):
                        if changes:
                            detail.append(f"app opened: {n.extra.get('screens')} screen(s), {n.extra.get('components')} component(s), {n.extra.get('controls')} control(s), {n.extra.get('datasources')} data source(s), {n.extra.get('connections')} connection(s) in the candidate")
                    elif o.extra.get("files") != n.extra.get("files"):
                        detail.append("packaged app files changed; the .msapp could not be opened for content comparison")
                if t in ("Plug-in assemblies", "Plug-in packages", "Custom connectors", "Custom controls (PCF)", "Reports") and o.extra.get("files") != n.extra.get("files"):
                    changed_files = sorted(set(o.extra.get("files", {})) ^ set(n.extra.get("files", {})) | {f for f in o.extra.get("files", {}) if f in n.extra.get("files", {}) and o.extra["files"][f] != n.extra["files"][f]})
                    detail.append("packaged files changed: " + ", ".join(changed_files[:8]) + (" …" if len(changed_files) > 8 else ""))
                if o.extra.get("xaml_hash") != n.extra.get("xaml_hash"):
                    detail.append("process definition (XAML) changed")
                    flag(flags, "medium", t, o.label, "definition (XAML) changed; the logic is compared by hash only, review it and test the affected records")
                if t != "Cloud flows" and o.extra.get("json_hash") != n.extra.get("json_hash"):
                    detail.append("process definition (JSON) changed")
                    flag(flags, "medium", t, o.label, "definition (JSON) changed; the logic is compared by hash only, review it and test the affected records")
                if all_changes or detail or extra_changed:  # the display limit must never decide the status
                    bucket["modified"].append({"key": k, "label": n.label, "changes": changes, "total_changes": total, "detail": detail,
                                               "extra": {kk: vv for kk, vv in n.extra.items() if kk not in ("flow", "options")}})
                    assess(t, o, n, "modified", all_changes, flags, removed_parents, added_parents, patch)
                else:
                    bucket["unchanged"] += 1
                    if len(bucket["unchanged_names"]) < 12:
                        bucket["unchanged_names"].append(n.label)
        results[t] = bucket
    notes = cross_reference(results, bc, cc, flags)
    brc, crc = bm.get("root_components", {}), cm.get("root_components", {})
    behavior_names = {"0": "include subcomponents", "1": "do not include subcomponents", "2": "shell only"}
    rc_behavior = []
    for k in sorted(set(brc) & set(crc)):
        if brc[k] != crc[k]:
            rc_behavior.append(f"{k}: behavior {brc[k]} ({behavior_names.get(brc[k], '?')}) -> {crc[k]} ({behavior_names.get(crc[k], '?')})")
            flag(flags, "medium", "Solution manifest", k, f"root component behavior changed {brc[k]} -> {crc[k]} ({behavior_names.get(brc[k], '?')} -> {behavior_names.get(crc[k], '?')}); the set of subcomponents the solution ships changes")
    focus = None
    if only_types:
        available = list(results.keys())
        wanted, unmatched = set(), []
        for raw in only_types:
            q = raw.strip().lower()
            if not q:
                continue
            exact = [t for t in available if t.lower() == q]
            loose = exact or [t for t in available if q in t.lower() or q.rstrip("s") in t.lower()]
            if loose:
                wanted.update(loose)
            else:
                unmatched.append(raw.strip())
        if unmatched:
            warnings.append("--types value(s) matched no component type in these packages: " + ", ".join(unmatched)
                            + ". Types present: " + ", ".join(available) + ".")
        focus = [t for t in available if t in wanted]
        results = OrderedDict((t, b) for t, b in results.items() if t in wanted)
        flags = [f for f in flags if f["type"] in wanted or f["type"] in ("Dependencies", "Solution manifest")]
        if focus:
            warnings.append("Focused comparison: only " + ", ".join(focus) + " are reported. Other component types may also have changed; rerun without --types for the full picture.")
    sev_order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda f: (sev_order.get(f["severity"], 9), f["component"].lower(), f["type"]))
    summary = OrderedDict((t, {"added": len(b["added"]), "removed": len(b["removed"]), "modified": len(b["modified"]),
                               "unchanged": b["unchanged"]}) for t, b in results.items())
    totals = {k: sum(v[k] for v in summary.values()) for k in ("added", "removed", "modified", "unchanged")}
    r = {"tool": {"name": "solution_diff.py", "version": TOOL_VERSION},
         "baseline": {"file": base.label, "packaged": base.packaged, **bm}, "candidate": {"file": cand.label, "packaged": cand.packaged, **cm},
         "warnings": warnings, "focus": focus, "summary": summary, "totals": totals, "flags": flags,
         "cross_references": notes, "components": results,
         "root_component_changes": {
             "added": sorted(set(cm.get("root_components", {})) - set(bm.get("root_components", {}))),
             "removed": sorted(set(bm.get("root_components", {})) - set(cm.get("root_components", {}))),
             "behavior_changed": rc_behavior,
         }}
    r["deployment_inputs"] = deployment_inputs(r)
    return r


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def short_path(path: str) -> str:
    """Drop the component's own root segment and unkeyed wrapper segments; keep keyed segments and the leaf."""
    segs = path.split("/")
    if len(segs) <= 1:
        return path
    body, leaf = segs[1:-1], segs[-1]
    kept = [x for x in body if "[" in x]
    return "/".join(kept + [leaf]) if kept else leaf


def meta_line(ctype, extra) -> str:
    """One short line of component facts for added/removed/modified rows."""
    if not extra:
        return ""
    e = extra
    if ctype == "Columns":
        disp = e.get("display") if e.get("display") and e.get("display").lower() not in (e.get("schema", "").lower(), "") else ""
        parts = [disp and f"'{disp}'", e.get("type"), e.get("required") and f"required level {e['required']}",
                 e.get("maxlength") and f"max {e['maxlength']}", e.get("format") and f"format {e['format']}"]
    elif ctype == "Tables":
        parts = [{"1": "user or team owned", "2": "business owned", "4": "organization owned", "8": "none"}.get(e.get("ownership"), e.get("ownership") and f"ownership mask {e['ownership']}")]
    elif ctype == "Relationships":
        parts = [e.get("type"), e.get("referencing") and f"{e['referencing']} → {e['referenced']}",
                 e.get("cascade_delete") and f"cascade delete {e['cascade_delete']}", e.get("cascade_assign") and f"assign {e['cascade_assign']}"]
    elif ctype == "Views":
        parts = [e.get("query_type") and f"query type {e['query_type']}", e.get("default") == "1" and "default view"]
    elif ctype == "Forms":
        parts = [e.get("form_type") and f"{e['form_type']} form", e.get("state") and f"activation state {e['state']}"]
    elif ctype == "Plug-in steps":
        parts = [e.get("plugin_type"), e.get("message") and f"{e['message']} of {e.get('entity') or 'none'}",
                 e.get("stage") and f"stage {e['stage']}", e.get("mode") and f"mode {e['mode']}", e.get("filtering") and f"filtering {e['filtering']}"]
    elif ctype == "Environment variables":
        parts = [e.get("display") and f"'{e['display']}'", e.get("type"), f"default {e.get('default') or 'none'}",
                 "packaged value" if e.get("current_values") else "no packaged value"]
    elif ctype == "Connection references":
        parts = [e.get("display") and f"'{e['display']}'", e.get("connector") and f"connector {e['connector']}"]
    elif ctype in ("Cloud flows", "Desktop flows", "Business rules", "Classic workflows", "Business process flows", "Custom actions", "Dialogs"):
        st = {"0": "draft/off", "1": "activated/on"}.get(e.get("state"), e.get("state"))
        parts = [st and f"state {st}", e.get("primary_entity") and e.get("primary_entity") != "none" and f"table {e['primary_entity']}", e.get("scope") and f"scope {e['scope']}"]
    elif ctype == "Canvas apps":
        parts = [e.get("display") and f"'{e['display']}'", e.get("app_version") and f"app version {e['app_version']}",
                 e.get("opened") and f"{e.get('screens', 0)} screens, {e.get('controls', 0)} controls, {e.get('datasources', 0)} data sources"]
    elif ctype == "Model-driven apps":
        parts = [e.get("components") is not None and f"{e['components']} app components"]
    elif ctype == "Plug-in assemblies":
        parts = [e.get("fullname")]
    else:
        parts = [e.get("display") and f"'{e['display']}'"]
    parts = [str(x) for x in parts if x]
    return (" — " + ", ".join(parts)) if parts else ""


def render_markdown(r, limit: int, brief: bool = False) -> str:
    b, c = r["baseline"], r["candidate"]
    out = []
    out.append(f"# Solution comparison: {c.get('unique_name') or c['file']}")
    out.append("")
    out.append("| | Baseline | Candidate |")
    out.append("| --- | --- | --- |")
    for k, lab in [("file", "Package"), ("packaged", "Packaged on"), ("unique_name", "Unique name"), ("display_name", "Display name"),
                   ("version", "Version"), ("managed", "Type"), ("publisher", "Publisher"), ("prefix", "Prefix")]:
        out.append(f"| {lab} | {md_escape(b.get(k, ''))} | {md_escape(c.get(k, ''))} |")
    out.append("")
    if r["warnings"]:
        out.append("## Warnings")
        out.append("")
        for w in r["warnings"]:
            out.append(f"- {w}")
        out.append("")
    out.append("## Summary by component type")
    out.append("")
    out.append("| Component type | Added | Removed | Modified | Unchanged |")
    out.append("| --- | ---: | ---: | ---: | ---: |")
    ta = tr = tm = tu = 0
    for t, bkt in r["components"].items():
        a, rm, m, u = len(bkt["added"]), len(bkt["removed"]), len(bkt["modified"]), bkt["unchanged"]
        ta, tr, tm, tu = ta + a, tr + rm, tm + m, tu + u
        out.append(f"| {t} | {a} | {rm} | {m} | {u} |")
    out.append(f"| **Total** | **{ta}** | **{tr}** | **{tm}** | **{tu}** |")
    rc = r.get("root_component_changes", {})
    if rc.get("added") or rc.get("removed") or rc.get("behavior_changed"):
        out.append("")
        if rc.get("added"):
            out.append("Root components added in solution.xml: " + "; ".join(rc["added"]))
        if rc.get("removed"):
            out.append("Root components removed from solution.xml: " + "; ".join(rc["removed"]))
        if rc.get("behavior_changed"):
            out.append("Root component behavior changed in solution.xml: " + "; ".join(rc["behavior_changed"]))
    out.append("")
    out.append("## Attention items")
    out.append("")
    if r["flags"]:
        counts = {sv: sum(1 for f in r["flags"] if f["severity"] == sv) for sv in ("high", "medium", "low")}
        out.append(f"{counts['high']} high, {counts['medium']} medium, {counts['low']} low. Items are grouped by component within each severity.")
        out.append("")
        out.append("| # | Severity | Type | Component | Finding |")
        out.append("| --- | --- | --- | --- | --- |")
        for i, f in enumerate(r["flags"], 1):
            f["id"] = f"A{i}"
            out.append(f"| A{i} | {f['severity']} | {md_escape(f['type'])} | {md_escape(f['component'])} | {md_escape(f['message'])} |")
    else:
        out.append("No risk flags raised by the heuristics. Review the detailed changes below.")
    out.append("")
    out.append("Severity is a heuristic from the script, not an organizational rating. Verify each item against the target environment.")
    out.append("")
    if r.get("deployment_inputs"):
        out.append("## Deployment inputs")
        out.append("")
        for title, items in r["deployment_inputs"].items():
            out.append(f"**{title}**")
            for it in items:
                out.append(f"- {md_escape(it)}")
            out.append("")
    if r.get("cross_references"):
        out.append("## Cross-references")
        out.append("")
        for n in r["cross_references"]:
            out.append(f"- {md_escape(n)}")
        out.append("")
    if brief:
        out.append("Details omitted (--brief). Rerun without --brief for the inventory.")
        return "\n".join(out) + "\n"
    out.append("## Details")
    out.append("")
    for t, bkt in r["components"].items():
        if not (bkt["added"] or bkt["removed"] or bkt["modified"]):
            continue
        out.append(f"### {t}")
        out.append("")
        for item in bkt["added"]:
            out.append(f"- **Added:** {md_escape(item['label'])}{md_escape(meta_line(t, item.get('extra')))}")
        for item in bkt["removed"]:
            extra = f" (still referenced by {', '.join(item['still_used_by'])})" if item.get("still_used_by") else ""
            out.append(f"- **Removed:** {md_escape(item['label'])}{md_escape(meta_line(t, item.get('extra')))}{md_escape(extra)}")
        for item in bkt["modified"]:
            extra = f" (used by {', '.join(item['used_by'])})" if item.get("used_by") else ""
            out.append(f"- **Modified:** {md_escape(item['label'])}{md_escape(meta_line(t, item.get('extra')))}{md_escape(extra)}")
            for d in item["detail"]:
                if d.startswith("  "):
                    out.append(f"    - {md_escape(d.strip())}")
                else:
                    out.append(f"  - {md_escape(d)}")
            for ch in item["changes"]:
                sp = short_path(ch["path"])
                if ch["kind"] == "renamed":
                    out.append(f"  - `{sp.replace('`', '')}` renamed to `{short_path(ch['new_path']).replace('`', '')}` ({ch['leaves']} identical values)")
                    continue
                if ch.get("subtree"):
                    vals = ch.get("values") or {}
                    shown = ", ".join(f"{k}={md_escape(v)[:60]}" for k, v in vals.items())
                    more = ch["leaves"] - len(vals)
                    tail = (f" ({shown}" + (f", … {more} more" if more > 0 else "") + ")") if shown else f" ({ch['leaves']} values)"
                    out.append(f"  - `{sp}` {ch['kind']}{tail}")
                    continue
                if ch["kind"] == "changed":
                    out.append(f"  - `{sp.replace('`', '')}`: {md_escape(ch['old'])[:120]} → {md_escape(ch['new'])[:120]}")
                elif ch["kind"] == "added":
                    out.append(f"  - `{sp.replace('`', '')}` added" + (f": {md_escape(ch['new'])[:120]}" if ch["new"] != "" else ""))
                else:
                    out.append(f"  - `{sp.replace('`', '')}` removed" + (f" (was {md_escape(ch['old'])[:120]})" if ch["old"] != "" else ""))
            if item["total_changes"] > len(item["changes"]):
                out.append(f"  - … {item['total_changes'] - len(item['changes'])} more change(s); rerun with --max-changes to see all")
        if bkt.get("unchanged_names"):
            more = bkt["unchanged"] - len(bkt["unchanged_names"])
            out.append(f"- Unchanged ({bkt['unchanged']}): " + ", ".join(md_escape(x) for x in bkt["unchanged_names"]) + (f", … {more} more" if more > 0 else ""))
        out.append("")
    out.append("## Method and limits")
    out.append("")
    out.append("- Components are matched by ID where exports provide one (forms, views, charts, dashboards, plug-in steps, processes), otherwise by schema name, then compared leaf by leaf after dropping known noise fields (introduced version, timestamps, managed flags). Change paths omit the component's root element and unkeyed wrappers that have no attributes; repeated or attributed wrappers such as FetchXML filters keep positional segments. The JSON output has full paths.")
    out.append("- Cloud flows are compared by trigger, action tree (including run-after conditions and switch cases), definition parameters, and connection references from their JSON definitions; a normalized-definition digest reports any remaining change that is not itemized.")
    out.append("- Canvas apps are opened from their .msapp package: screens, controls, property formulas, data sources, and connections are compared by content; media and images only by hash.")
    out.append("- Web resources, plug-in assemblies and packages, PCF control bundles, custom connector files, report definitions, and desktop flow definitions are compared by file hash: the report says they changed, not what changed inside them.")
    out.append("- Behavior differences that come from the target environment (existing data, other layers, missing connections) are outside what the packages can show.")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Compare two Power Platform solution packages.")
    ap.add_argument("baseline", help="older solution (.zip or extracted folder)")
    ap.add_argument("candidate", help="newer solution (.zip or extracted folder)")
    ap.add_argument("--md", help="write the Markdown report here (default: print to stdout)")
    ap.add_argument("--json", help="write the full JSON result here")
    ap.add_argument("--max-changes", type=int, default=25, help="max leaf changes listed per component (default 25)")
    ap.add_argument("--include-noise", action="store_true", help="do not drop introduced-version, timestamp, and managed-flag fields")
    ap.add_argument("--types", help="comma-separated component types to report (focused comparison), e.g. \"Security roles,Cloud flows\"")
    ap.add_argument("--brief", action="store_true", help="summary, attention items, deployment inputs, and cross-references only (pre-import check)")
    args = ap.parse_args()
    base, cand = load_package(args.baseline), load_package(args.candidate)
    only = [t for t in args.types.split(",") if t.strip()] if args.types else None
    result = compare(base, cand, args.include_noise, args.max_changes, only)
    md = render_markdown(result, args.max_changes, args.brief)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, default=str)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"wrote {args.md}" + (f" and {args.json}" if args.json else ""))
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
