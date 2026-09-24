#!/usr/bin/env python3
"""Offline release check for an exported Dataverse solution .zip.

Reads the package in memory (nothing is extracted to disk) and reports what will
fail or quietly misbehave when it is imported into a clean environment, plus the
steps a person has to take before, during and after the import.

    python3 scripts/check_solution.py SOLUTION.zip
    python3 scripts/check_solution.py SOLUTION.zip --json
    python3 scripts/check_solution.py SOLUTION.zip --format markdown --output report.md

Exit codes: 0 = no blockers, 1 = blockers found, 2 = not a solution export, unreadable,
or a usage error. Python 3.9+ standard library only. No network access. Values of
environment variables, plug-in step configuration and connections are never printed.
"""
from __future__ import annotations

import argparse
import codecs
import json
import os
import re
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET
from xml.parsers import expat

TOOL = "dataverse-solution-release-check"
TOOL_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Version-sensitive values. Each one records the Microsoft Learn page it came
# from and the date it was checked. Re-check the page before relying on them.
# ---------------------------------------------------------------------------
LEARN_CHECKED = "2026-09-23"
PLATFORM_LIBRARIES = {
    "checked": LEARN_CHECKED,
    "source": "https://learn.microsoft.com/power-apps/developer/component-framework/"
              "react-controls-platform-libraries#supported-platform-libraries-list",
    # Versions a ControlManifest may DECLARE: exact values and inclusive ranges.
    "allowed": {
        "React": {"exact": ["16.14.0"], "ranges": []},
        "Fluent": {"exact": ["8.29.0", "8.121.1"], "ranges": [("9.4.0", "9.46.2")]},
    },
    # Versions Learn lists as LOADED at runtime. Not what a manifest declares.
    "loaded": {"React": ["17.0.2", "16.14.0"], "Fluent": ["8.29.0", "8.121.1", "9.68.0"]},
}
PAC_FOR_VIRTUAL_CONTROLS = {
    "checked": LEARN_CHECKED,
    "minimum": "1.37",
    "source": "https://learn.microsoft.com/power-apps/developer/component-framework/"
              "react-controls-platform-libraries",
}
# Learn says "95 MB" without saying whether a megabyte is 10^6 or 2^20 bytes. Above
# 95 * 2^20 bytes is over the limit either way (blocker); between 95 * 10^6 and
# 95 * 2^20 bytes it depends on the reading (warning).
IMPORT_SIZE_LIMIT = {
    "checked": LEARN_CHECKED,
    "bytes": 95 * 1024 * 1024,
    "decimalBytes": 95 * 1000 * 1000,
    "label": "95 MB",
    "source": "https://learn.microsoft.com/power-apps/maker/data-platform/import-update-export-solutions",
}

LEARN = {
    "missing_deps": "https://learn.microsoft.com/troubleshoot/power-platform/dataverse/"
                    "working-with-solutions/missing-dependency-on-solution-import",
    "dependency_tracking": "https://learn.microsoft.com/power-platform/alm/dependency-tracking-solution-components",
    "sitemap_dependency": "https://learn.microsoft.com/power-platform/alm/"
                          "dependency-tracking-solution-components#site-map-sitemap",
    "segmented": "https://learn.microsoft.com/power-platform/alm/segmented-solutions-alm",
    "solution_component": "https://learn.microsoft.com/power-apps/developer/data-platform/reference/"
                          "entities/solutioncomponent",
    "pcf_alm": "https://learn.microsoft.com/power-apps/developer/component-framework/code-components-alm",
    "pcf_build": "https://learn.microsoft.com/power-apps/developer/component-framework/"
                 "code-components-alm#building-pcfproj-code-component-projects",
    "pcf_eval": "https://learn.microsoft.com/power-apps/developer/component-framework/issues-and-workarounds"
                "#when-running-power-apps-checker-with-the-solution-built-using-cli-tooling-in-default-configuration",
    "pcf_dev_builds": "https://learn.microsoft.com/power-apps/developer/component-framework/"
                      "code-components-best-practices#power-apps-component-framework",
    "platform_library_element": "https://learn.microsoft.com/power-apps/developer/component-framework/"
                                "manifest-schema-reference/platform-library",
    "pcf_manifest": "https://learn.microsoft.com/power-apps/developer/component-framework/"
                    "manifest-schema-reference/manifest",
    "pcf_control_element": "https://learn.microsoft.com/power-apps/developer/component-framework/"
                           "manifest-schema-reference/control",
    "checker_eval": "https://learn.microsoft.com/power-apps/maker/data-platform/"
                    "common-issues-resolutions-solution-checker#solution-checker-violations-reported-for-code-components",
    "checker_enforcement": "https://learn.microsoft.com/troubleshoot/power-platform/dataverse/"
                           "working-with-solutions/solution-checker-enforcement-import-issues",
    "checker": "https://learn.microsoft.com/power-apps/maker/data-platform/use-powerapps-checker",
    "checker_rules": "https://learn.microsoft.com/power-apps/maker/data-platform/"
                     "use-powerapps-checker#best-practice-rules-used-by-solution-checker",
    "checker_report": "https://learn.microsoft.com/power-apps/maker/data-platform/"
                      "use-powerapps-checker#review-the-solution-checker-report",
    "checker_sarif": "https://learn.microsoft.com/power-platform/alm/checker-api/overview#report-format",
    "sitemap_icons": "https://learn.microsoft.com/power-apps/maker/model-driven-apps/create-site-map-app",
    "import": "https://learn.microsoft.com/power-apps/maker/data-platform/import-update-export-solutions",
    "pac_import": "https://learn.microsoft.com/power-platform/developer/cli/reference/solution#pac-solution-import",
    "import_options": "https://learn.microsoft.com/power-platform/alm/performance-recommendations",
    "connection_refs": "https://learn.microsoft.com/power-apps/maker/data-platform/create-connection-reference",
    "deployment_settings": "https://learn.microsoft.com/power-platform/alm/conn-ref-env-variables-build-tools",
    "flow_state": "https://learn.microsoft.com/power-automate/import-flow-solution"
                  "#what-will-the-flow-state-be-after-import",
    "workflow_table": "https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/workflow",
    "env_vars": "https://learn.microsoft.com/power-apps/maker/data-platform/environmentvariables",
    "managed_unmanaged": "https://learn.microsoft.com/power-platform/alm/solution-concepts-alm",
    "publisher_prefix": "https://learn.microsoft.com/power-platform/developer/cli/reference/solution#pac-solution-init",
    "publisher_table": "https://learn.microsoft.com/power-apps/developer/data-platform/reference/entities/publisher",
    "version": "https://learn.microsoft.com/power-platform/alm/solution-api",
    "export": "https://learn.microsoft.com/power-apps/maker/data-platform/export-solutions",
    "edit_customizations": "https://learn.microsoft.com/power-platform/alm/when-edit-customization-file",
    "supported_customizations": "https://learn.microsoft.com/power-apps/developer/data-platform/"
                                "supported-customizations#unsupported-customizations",
}
# Not Microsoft Learn: Microsoft's model-apps plugin in microsoft/power-platform-skills,
# pinned to one commit.
MODEL_APPS_PLUGIN = ("https://github.com/microsoft/power-platform-skills/blob/"
                     "76eb664451b4fd8a322567ebf7baaa2f78568cee/plugins/model-apps/scripts/lib/app-spec.js")
MODEL_APPS_PLUGIN_BASIS = "microsoft/power-platform-skills at commit 76eb664"

# Common componenttype codes from Learn's SolutionComponent reference, with Learn's
# labels in maker wording (Entity -> Table, Attribute -> Column, Saved Query -> View,
# Attribute/Entity Image Configuration -> Column/Table image configuration). The list
# is not exhaustive: an unlisted code is unknown, not invalid.
COMPONENT_TYPES = {
    1: "Table", 2: "Column", 3: "Relationship", 9: "Choice (option set)", 10: "Table relationship",
    20: "Security role", 26: "View", 29: "Process or flow", 60: "Form", 61: "Web resource",
    62: "Site map", 66: "Code component", 90: "Plug-in type", 91: "Plug-in assembly",
    92: "Plug-in step", 300: "Canvas app", 371: "Connector", 372: "Connector",
    380: "Environment variable definition", 381: "Environment variable value",
    431: "Column image configuration", 432: "Table image configuration",
}
# Not in Learn's componenttype table; 80 appears on model-driven app root components.
OBSERVED_TYPES = {80: "model-driven app"}
BEHAVIOR_LABELS = {"0": "Include Subcomponents", "1": "Do not include subcomponents",
                   "2": "Include As Shell Only"}

# Reading limits: the zip is read in memory, never extracted. Parsed XML needs about 7
# times the file's size in memory for the real exports we measured, but up to about 30
# times for crafted XML made of many tiny elements, so XML is capped by size and by node
# count (elements plus attributes, checked before the tree is built). With these caps the
# worst crafted packages we built stayed under 500 MB and about 2.5 seconds. Parsed JSON can also
# need many times its size, so it has a lower cap.
MAX_MEMBERS = 50000
MAX_MEMBER_BYTES = 64 * 1024 * 1024   # any file read into memory (XML, code-component bundles)
MAX_XML_NODES = 1000000               # elements plus attributes in solution.xml or customizations.xml
MAX_SMALL_XML_NODES = 200000          # the same for every other XML file
MAX_TOTAL_XML_NODES = 1200000         # all XML files parsed in one run, together
MAX_JSON_BYTES = 8 * 1024 * 1024      # flow definitions and environment variable values
MAX_TOTAL_BYTES = 1024 * 1024 * 1024  # declared size of all entries
MAX_READ_BYTES = 128 * 1024 * 1024    # read into memory in one run, all files together
VERIFY_BUDGET = 256 * 1024 * 1024     # bytes decompressed when reading every entry back once
MAX_RATIO = 50                        # uncompressed / compressed
RATIO_MIN_BYTES = 8 * 1024 * 1024     # the ratio limit applies above this size
MAX_ROWS = 25          # items shown per list in Markdown (JSON has everything)

S0, S1 = "\x02", "\x03"  # marks package-derived values inside report strings


class PackageError(Exception):
    """The file can't be analysed as a solution export (exit code 2)."""

    def __init__(self, code, title, detail, fix=""):
        super().__init__(title)
        self.code, self.title, self.detail, self.fix = code, title, detail, fix


class CheckSkipped(Exception):
    """A single check could not run; reported under 'Not checked'."""


class DamagedEntry(CheckSkipped):
    """A zip entry that can't be read back. Reported once, as a package-integrity
    blocker, rather than under 'Not checked' by every check that needed it."""


class DoctypeRefused(ET.ParseError):
    """The XML declares a DOCTYPE. The document may be well-formed; the check refuses it."""


class TooManyNodes(CheckSkipped):
    """An XML file has more nodes than this check parses."""


class OverBudget(CheckSkipped):
    """The run's total read or parse budget is spent. The file itself may be fine."""


# --------------------------------------------------------------------------- helpers
def v(value):
    """Wrap a value that came from the package so the renderer can quote it safely."""
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value)).strip()
    if len(s) > 200:
        s = s[:197] + "..."
    return S0 + s + S1


def plain(s):
    return s.replace(S0, "").replace(S1, "")


def md(s, table=False):
    """Render a report string as Markdown: package-derived values become code spans,
    so names from the zip can't inject links, HTML or formatting."""
    parts = re.split(S0 + "(.*?)" + S1, s, flags=re.S)
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            val = part.replace("`", "'")
            out.append("`%s`" % val if val else "(empty)")
        else:
            out.append(part)
    res = "".join(out)
    return res.replace("|", "\\|") if table else res


def lc(s):
    return (s or "").strip().lower()


def kids(el, name):
    if el is None:
        return []
    n = name.lower()
    return [c for c in list(el) if isinstance(c.tag, str) and c.tag.lower() == n]


def kid(el, name):
    k = kids(el, name)
    return k[0] if k else None


def walk(el, *names):
    for n in names:
        el = kid(el, n)
        if el is None:
            return None
    return el


def text(el):
    return (el.text or "").strip() if el is not None else ""


def attr(el, name):
    if el is None:
        return ""
    n = name.lower()
    for k, val in el.attrib.items():
        if k.lower() == n:
            return (val or "").strip()
    return ""


def field(el, name):
    """Attribute or child-element value (exports use elements, hand-built zips attributes)."""
    a = attr(el, name)
    return a if a else text(kid(el, name))


def localized(el):
    """First LocalizedNames/LocalizedName@description under el."""
    ln = kid(kid(el, "LocalizedNames"), "LocalizedName")
    return attr(ln, "description")


def version_tuple(s):
    s = (s or "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+){0,3}", s, flags=re.ASCII):
        return None
    t = tuple(int(p) for p in s.split("."))
    return t + (0,) * (4 - len(t))


def is_int(s):
    return bool(re.fullmatch(r"\d+", s or "", flags=re.ASCII))


def type_label(t):
    """Label for a componenttype code. A non-numeric type (for example SettingDefinition)
    comes from the package, so it is returned wrapped for safe rendering."""
    s = (t or "").strip()
    if is_int(s):
        n = int(s)
        if n in COMPONENT_TYPES:
            return COMPONENT_TYPES[n]
        if n in OBSERVED_TYPES:
            return "Component type %d (%s)" % (n, OBSERVED_TYPES[n])
        return "Component type %d" % n
    return v(s) if s else "Component of unknown type"


def fmt_size(n):
    """Binary units (1 MiB = 1,048,576 bytes), labelled MiB/KiB so they aren't mistaken
    for the decimal megabytes of Learn's size limit."""
    if n >= 1024 * 1024:
        return "%.1f MiB" % (n / 1024.0 / 1024.0)
    return "%d KiB" % max(1, round(n / 1024.0))


def ident_values(a, extra=()):
    """Lower-cased identifying values of a Required, Dependent or RootComponent element's
    attributes (already lower-cased keys). Exports vary: schemaName, id, uniquename or
    dotted id.* keys, so read whichever are present."""
    out = set()
    for k, val in a.items():
        if not val:
            continue
        if k in ("schemaname", "id", "uniquename", "name") + tuple(extra) or \
                (k.startswith("id.") and "parent" not in k):
            out.add(lc(val).strip("{}"))
    return out


def head(items, n=MAX_ROWS):
    items = list(items)
    if len(items) <= n:
        return items
    return items[:n] + ["and %d more" % (len(items) - n)]


# --------------------------------------------------------------------------- package
# A namespaced element needs an xmlns declaration or the reserved xml: prefix.
XMLNS_MARKERS = tuple(m.encode(e) for m in ("xmlns", "xml:") for e in ("utf-8", "utf-16-le", "utf-16-be"))
# A prefixed element name (<p:name, where the name can't hold "<") or a default namespace
# declaration (xmlns=). Linear: each match attempt stops at the next "<" or delimiter.
NAMESPACED_ELEMENT = re.compile(rb"<[^\s/>!?=\"'<]*:|xmlns\s*=")


def _refuse_dtd(*_args):
    raise DoctypeRefused("document type declarations are not accepted")


def parse_xml(data, max_nodes=MAX_SMALL_XML_NODES):
    """Parse XML bytes. Refuses any DTD and any document with more than max_nodes
    elements plus attributes, and strips namespaces. Returns (root, node count), where the
    count is exact or an upper bound.

    Both refusals happen inside expat, on the parser's own view of the document, before
    ElementTree builds anything, so they hold for every encoding expat detects (including
    UTF-16 without a byte order mark) and cost linear time."""
    guard = expat.ParserCreate()
    guard.StartDoctypeDeclHandler = _refuse_dtd
    guard.EntityDeclHandler = _refuse_dtd
    nodes = [0]

    def count(_name, attrs):
        nodes[0] += 1 + len(attrs)
        if nodes[0] > max_nodes:
            raise TooManyNodes("the file has more than %s elements and attributes, more than this check parses"
                               % format(max_nodes, ","))
    # Every element needs a "<" and every attribute a "=". In every encoding expat accepts,
    # those characters are the bytes 0x3C and 0x3D (other characters' bytes can only add to
    # the count), so the byte counts bound the node count from above. Only a document that
    # might be over the cap pays for exact counting.
    bound = data.count(b"<") + data.count(b"=")
    if bound > max_nodes:
        guard.StartElementHandler = count
    try:
        guard.Parse(data, True)
    except expat.ExpatError as e:
        raise ET.ParseError(str(e))
    del guard
    root = ET.fromstring(data)
    if may_have_namespaced_elements(data):
        for el in root.iter():
            t = el.tag
            if isinstance(t, str) and t[:1] == "{":
                el.tag = t[t.index("}") + 1:]
    return root, (nodes[0] if bound > max_nodes else bound)


def may_have_namespaced_elements(data):
    """False only when no element can be in a namespace, so the tree needs no stripping.
    An element is namespaced only with a prefix (<p:name) or a default xmlns="..." in scope.
    In the 8-bit and UTF-8 encodings expat reads, ASCII markup is plain ASCII bytes, so a
    byte search is exact; for UTF-16 only the absence of any xmlns or xml: text is trusted."""
    if data[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE) or b"\x00" in data[:4]:
        return any(m in data for m in XMLNS_MARKERS)
    return bool(NAMESPACED_ELEMENT.search(data))


# Errors a zip entry can raise while being read back: damaged or truncated data, a bad
# CRC, an unsupported compression method or an encrypted entry.
ENTRY_ERRORS = (zlib.error, EOFError, zipfile.BadZipFile, NotImplementedError, RuntimeError, OSError, ValueError)


def same_path(name):
    """An entry name with spellings of the same path folded together, to spot duplicates: no
    case, backslashes read as slashes, empty and "." segments dropped, ".." applied, and
    trailing spaces and dots removed from each segment."""
    out = []
    for seg in name.replace("\\", "/").lower().split("/"):
        if seg == "..":
            if out:
                out.pop()
            continue
        seg = seg.rstrip(" .")
        if seg:
            out.append(seg)
    return "/".join(out)


class Package:
    def __init__(self, path):
        self.path = path
        self.size = os.path.getsize(path)
        self.zf = zipfile.ZipFile(path)
        infos = self.zf.infolist()
        if len(infos) > MAX_MEMBERS:
            raise PackageError("too-many-entries", "The zip has too many entries to check",
                               "%d entries (limit %d)." % (len(infos), MAX_MEMBERS))
        self.infos = {}
        paths = {}   # same_path() form -> entry names as stored
        for i in infos:
            if i.filename.endswith("/"):
                continue
            key = i.filename.replace("\\", "/").lstrip("/").lower()
            paths.setdefault(same_path(i.filename), []).append(i.filename)
            self.infos.setdefault(key, i)
        # Entries whose names point at the same path make the package ambiguous. load_solution()
        # refuses it once solution.xml is found, so the wrong-upload checks run first.
        self.duplicates = sorted((k, names) for k, names in paths.items() if len(names) > 1)
        declared = sum(i.file_size for i in self.infos.values())
        if declared > MAX_TOTAL_BYTES:
            raise PackageError("too-large", "The zip is too large for this offline check",
                               "Its entries expand to %s; this check reads at most %s. The export may still "
                               "be valid." % (fmt_size(declared), fmt_size(MAX_TOTAL_BYTES)),
                               "Check the package another way, for example with Solution checker or a test "
                               "import into a non-production environment.")
        self.read_total = 0
        self.xml_nodes = 0  # nodes parsed so far, against MAX_TOTAL_XML_NODES
        self.damaged = {}   # lower-cased entry name -> error text
        self.unverified = {"ratio": [], "budget": []}   # entries verify() didn't read back
        self.read_ok = set()   # entries read() already read in full

    def verify(self):
        """Read every entry back in chunks (nothing is kept) and record the ones that fail.
        Runs after the checks and skips entries they already read in full.

        An entry that expands more than MAX_RATIO times (above RATIO_MIN_BYTES) isn't read
        back, and reading stops once VERIFY_BUDGET bytes have been decompressed, so a small
        zip can't make this step decompress up to MAX_TOTAL_BYTES."""
        spent = 0
        for key, info in self.infos.items():
            if key in self.damaged or key in self.read_ok:
                continue
            if info.file_size > RATIO_MIN_BYTES and info.file_size > MAX_RATIO * max(1, info.compress_size):
                self.unverified["ratio"].append(key)
                continue
            if spent + info.file_size > VERIFY_BUDGET:
                self.unverified["budget"].append(key)
                continue
            spent += info.file_size   # zipfile never returns more than the declared size
            try:
                with self.zf.open(info) as f:
                    while f.read(1024 * 1024):
                        pass
            except ENTRY_ERRORS as e:
                self.damaged[key] = "%s: %s" % (e.__class__.__name__, e)

    def xml(self, name, max_nodes=MAX_SMALL_XML_NODES):
        """Read and parse one XML entry within its own node cap and the run's total, so many
        small crafted files can't add up to more parsing than one large one."""
        total = OverBudget("the package's XML files have more than %s elements and attributes in total, more "
                           "than this check parses" % format(MAX_TOTAL_XML_NODES, ","))
        left = MAX_TOTAL_XML_NODES - self.xml_nodes
        if left <= 0:
            raise total
        data = self.read(name)
        cap = min(max_nodes, left)
        try:
            root, n = parse_xml(data, cap)
        except TooManyNodes:
            self.xml_nodes += cap   # that much was counted; a refused file still uses up the budget
            if cap == max_nodes:
                raise
            raise total
        self.xml_nodes += n
        return root

    def names(self):
        """Lower-cased, forward-slash entry names."""
        return list(self.infos)

    def original(self, key):
        """Entry name as stored in the zip, with forward slashes."""
        return self.infos[key].filename.replace("\\", "/").lstrip("/")

    def has(self, name):
        return name.replace("\\", "/").lstrip("/").lower() in self.infos

    def read(self, name, limit=MAX_MEMBER_BYTES):
        key = name.replace("\\", "/").lstrip("/").lower()
        info = self.infos[key]
        if key in self.damaged:
            raise DamagedEntry("%s can't be read back from the zip (%s)" % (v(info.filename), v(self.damaged[key])))
        if info.file_size > limit:
            raise CheckSkipped("%s is %s, more than the %s this check reads into memory"
                               % (v(info.filename), fmt_size(info.file_size), fmt_size(limit)))
        if info.file_size > RATIO_MIN_BYTES and info.file_size > MAX_RATIO * max(1, info.compress_size):
            raise CheckSkipped("%s expands from %s to %s (more than %dx), which this check doesn't read into memory"
                               % (v(info.filename), fmt_size(info.compress_size), fmt_size(info.file_size),
                                  MAX_RATIO))
        if self.read_total + info.file_size > MAX_READ_BYTES:
            raise OverBudget("%s wasn't read: this check reads at most %s of the package into memory in total"
                             % (v(info.filename), fmt_size(MAX_READ_BYTES)))
        try:
            with self.zf.open(info) as f:
                data = f.read(limit + 1)
        except ENTRY_ERRORS as e:
            self.damaged[key] = "%s: %s" % (e.__class__.__name__, e)
            raise DamagedEntry("%s can't be read back from the zip (%s)" % (v(info.filename), v(self.damaged[key])))
        if len(data) > limit:
            raise CheckSkipped("%s is more than the %s this check reads into memory" % (v(info.filename), fmt_size(limit)))
        self.read_total += len(data)
        self.read_ok.add(key)
        return data


# --------------------------------------------------------------------------- report
class Report:
    def __init__(self, input_name):
        self.input_name = input_name
        self.package = {}
        self.findings = []
        self.prerequisites = []
        self.checklist = []
        self.not_checked = []
        self.fatal = None

    def add(self, fid, severity, title, evidence, why, fix, sources=(), version_sensitive=False,
            component=None, component_type=None):
        basis = None
        if version_sensitive:
            basis = (MODEL_APPS_PLUGIN_BASIS if MODEL_APPS_PLUGIN in sources
                     else "Microsoft Learn as checked on %s" % LEARN_CHECKED)
        self.findings.append({
            "id": fid, "severity": severity, "title": title, "evidence": evidence, "why": why,
            "fix": fix, "sources": list(sources), "versionSensitive": bool(version_sensitive),
            "versionBasis": basis, "component": component, "componentType": component_type,
        })

    def action(self, aid, when, title, items, why, sources=()):
        self.checklist.append({"id": aid, "when": when, "title": title, "items": list(items),
                               "why": why, "sources": list(sources)})

    def skipped(self, check, reason):
        self.not_checked.append({"check": check, "reason": reason})

    def count(self, severity):
        return sum(1 for f in self.findings if f["severity"] == severity)

    def exit_code(self):
        if self.fatal:
            return 2
        return 1 if self.count("blocker") else 0


# --------------------------------------------------------------------------- context
class Context:
    def __init__(self, pkg, sol_root, manifest, cust):
        self.pkg = pkg
        self.sol_root = sol_root
        self.manifest = manifest
        self.cust = cust
        self.unique_name = text(kid(manifest, "UniqueName"))
        pub = kid(manifest, "Publisher")
        self.prefix = lc(text(kid(pub, "CustomizationPrefix")))
        self.managed = text(kid(manifest, "Managed"))
        self.roots = [dict((k.lower(), (val or "").strip()) for k, val in rc.attrib.items())
                      for rc in kids(kid(manifest, "RootComponents"), "RootComponent")]
        self.root_index = {}            # (type, lower identifier) -> root attributes
        for r in self.roots:
            for x in ident_values(r):
                self.root_index.setdefault((r.get("type", ""), x), r)
        self.webresource_names = set(lc(text(kid(w, "Name")))
                                     for w in kids(kid(cust, "WebResources"), "WebResource"))
        self.unpackaged_controls = {}   # lower name -> blocker finding (for de-duplication)
        self.external_controls = set()  # type 66 identifiers another named solution provides
        self.packaged_missing = {}      # (type, key) -> {"root", "label", "entries"} for roots also listed missing
        self.owned_missing = {}         # lower identifier -> owned-missing-dependency finding
        self.prerequisite_ids = set()   # lower identifiers of components another named solution provides
        self.env = None                 # environment_variables() result, computed once
        self.conn_refs = None           # connection_references() result, computed once
        self.conn_ref_unreadable = []   # (entry name, reason) for connectionreferences/*.xml it couldn't read
        self.env_unreadable_defs = []   # environment variable definition files it couldn't read
        self.env_unmatched = []         # type 380 roots with no definition file it recognises
        self.control_manifests = None   # manifest_info() result, computed once

    def owned(self, name):
        n = lc(name)
        return bool(self.prefix) and n.startswith(self.prefix + "_")


# --------------------------------------------------------------------------- loading
def folder_error(path):
    """Explain a folder passed instead of the exported .zip, without reading file contents."""
    found, seen = set(), 0
    for dirpath, dirnames, filenames in os.walk(path):
        rel = os.path.relpath(dirpath, path).replace("\\", "/").lower()
        if rel != "." and rel.count("/") >= 3:
            dirnames[:] = []
        for fn in filenames:
            seen += 1
            n = (fn.lower() if rel == "." else rel + "/" + fn.lower())
            if n.endswith("other/solution.xml"):
                found.add("unpacked")
            elif n.endswith("solution.yml"):
                found.add("yaml")
            elif n == "solution.xml":
                found.add("extracted")
        if seen > 20000:
            break
    if "unpacked" in found:
        return PackageError("unpacked-source", "This is a folder of unpacked solution source, not an export zip",
                            "The folder holds Other/Solution.xml (SolutionPackager or pac solution unpack layout).",
                            "Pack it (pac solution pack) or export the solution again, then check that .zip.")
    if "yaml" in found:
        return PackageError("yaml-source", "This is a folder of solution source in YAML format, not an export zip",
                            "The folder holds solution.yml files.",
                            "Pack it (pac solution pack) or export the solution again, then check that .zip.")
    if "extracted" in found:
        return PackageError("folder", "This is a folder of extracted export files, not the export zip",
                            "The folder holds solution.xml at its top level, so it looks like an export that was "
                            "unzipped.", "Check the original .zip the export produced.")
    return PackageError("folder", "This is a folder, not a solution export zip",
                        "The path is a folder with no solution files the check recognises.",
                        "Export the solution (Power Apps Solutions > Export, or pac solution export) and check the "
                        ".zip that export produces.")


SARIF_SOURCES = ("Solution checker results come as SARIF: the checker web API and PowerShell module return a zip of "
                 "SARIF reports (pac solution check runs the same checker service), and the results link in a "
                 "Managed Environments enforcement message downloads a SARIF file.")


def looks_like_sarif(path):
    """A bare SARIF file: by name, or JSON whose start has SARIF's "runs" and "version" keys."""
    name = os.path.basename(path).lower()
    if name.endswith(".sarif") or name.endswith(".sarif.json"):
        return True
    try:
        with open(path, "rb") as f:
            head_bytes = f.read(64 * 1024)
    except OSError:
        return False
    enc = "utf-16" if head_bytes[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE) else "utf-8-sig"
    s = head_bytes.decode(enc, errors="ignore").lstrip()
    if not s.startswith("{"):
        return False
    return bool(re.search(r'"runs"\s*:\s*\[', s)) and (bool(re.search(r'"version"\s*:', s)) or "sarif" in s.lower())


def open_package(path, rep):
    if os.path.isdir(path):
        raise folder_error(path)
    if not os.path.isfile(path):
        raise PackageError("file-not-found", "File not found", "No file at the path given.",
                           "Check the path, or save the uploaded file somewhere the script can read it.")
    try:
        if not zipfile.is_zipfile(path):
            if looks_like_sarif(path):
                raise PackageError("not-a-solution", "This is Solution checker results in SARIF format, not a solution",
                                   "The file is SARIF results, not a zip. " + SARIF_SOURCES,
                                   "Export the solution from Power Apps (Solutions > Export) or with pac solution "
                                   "export, and check the .zip that export produces.")
            raise zipfile.BadZipFile("not a zip")
        pkg = Package(path)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, ValueError) as e:
        raise PackageError("not-a-zip", "This file is not a readable zip archive",
                           "The file could not be opened as a zip (%s)." % e.__class__.__name__,
                           "Export the solution again and upload the .zip the export produced.")
    rep.package["file"] = {"name": os.path.basename(path), "bytes": pkg.size, "entries": len(pkg.names())}
    return pkg


def not_a_solution(pkg):
    names = pkg.names()
    fix = ("Export the solution from Power Apps (Solutions > Export) or with pac solution export, "
           "and check the .zip that export produces.")
    if any(n.endswith("other/solution.xml") for n in names):
        return PackageError("unpacked-source", "This is unpacked solution source, not an export zip",
                            "The zip holds Other/Solution.xml (SolutionPackager or pac solution unpack "
                            "layout) instead of solution.xml at the root.",
                            "Pack it (pac solution pack) or export the solution again, then check that zip.")
    if any(n.endswith("solution.yml") for n in names):
        return PackageError("yaml-source", "This is solution source in YAML format, not an export zip",
                            "The zip holds solution.yml instead of solution.xml at the root.", fix)
    nested = [n for n in names if n.endswith("/solution.xml")]
    if nested:
        return PackageError("nested-folder", "The solution files are inside a folder, not at the zip root",
                            "Found %s; an export has solution.xml at the root." % v(pkg.original(nested[0])),
                            "Upload the original export zip, or zip the contents of that folder rather "
                            "than the folder itself.")
    inner = [n for n in names if n.endswith(".zip")]
    if inner:
        return PackageError("zip-in-zip", "This zip contains other zips, not a solution",
                            "Inner zip files: %s." % ", ".join(v(pkg.original(n)) for n in inner[:5]),
                            "Check the inner solution .zip itself.")
    sarif = [n for n in names if n.endswith(".sarif")]
    if sarif:
        return PackageError("not-a-solution", "This is Solution checker results in SARIF format, not a solution",
                            "The zip holds %s and no solution.xml. %s"
                            % (", ".join(v(pkg.original(n)) for n in sarif[:3]), SARIF_SOURCES), fix)
    if names and all(n.endswith(".xlsx") for n in names):
        return PackageError("not-a-solution", "This looks like a Solution checker report from Power Apps, not a solution",
                            "The zip holds only Excel files (%s) and no solution.xml. Solution checker's Download "
                            "results in Power Apps gives a zip with an Excel report."
                            % ", ".join(v(pkg.original(n)) for n in names[:3]), fix)
    shown = ", ".join(v(pkg.original(n)) for n in names[:8]) or "nothing"
    return PackageError("not-a-solution", "This zip is not a Dataverse solution export",
                        "No solution.xml at the zip root. Entries: %s%s."
                        % (shown, " ..." if len(names) > 8 else ""), fix)


def load_xml(pkg, name):
    try:
        return pkg.xml(name, MAX_XML_NODES)   # only solution.xml and customizations.xml come here
    except DamagedEntry as e:
        raise PackageError("unreadable-entry", "%s is damaged and can't be read from the zip" % name,
                           "%s." % str(e), "Export the solution again and check the new .zip.")
    except CheckSkipped as e:
        msg = str(e)
        raise PackageError("too-large", "%s is too large for this offline check" % name,
                           "%s. The export may still be valid." % (msg[:1].upper() + msg[1:]),
                           "Check the package another way, for example with Solution checker or a test import "
                           "into a non-production environment.")
    except DoctypeRefused:
        raise PackageError("%s-doctype" % name.replace(".", "-"),
                           "%s contains a DOCTYPE, which this check doesn't accept" % name,
                           "The file has a document type declaration. The check refuses any DOCTYPE, so that entity "
                           "definitions in a crafted file can't expand, and doesn't read the rest of the file.",
                           "Export the solution again and check the .zip the export produces, without editing it.")
    except (ET.ParseError, UnicodeDecodeError, ValueError) as e:
        raise PackageError("%s-unparseable" % name.replace(".", "-"), "%s is not well-formed XML" % name,
                           "Parser error: %s." % v(e), "Export the solution again; the file is damaged "
                           "or was edited by hand.")
    except ENTRY_ERRORS as e:
        raise PackageError("unreadable-entry", "%s is damaged and can't be read from the zip" % name,
                           "%s: %s." % (e.__class__.__name__, v(e)), "Export the solution again and check the new .zip.")


def duplicate_entries(pkg):
    """Refuse a package whose entry names point at the same path more than once: every lookup
    is by name, so a second copy would be silently ignored, and which copy counts is ambiguous."""
    shown = ["%s (%d entries)" % (", ".join(head(dict.fromkeys(v(n) for n in names), 3)), len(names))
             for _key, names in pkg.duplicates]
    n = len(pkg.duplicates)
    return PackageError("duplicate-entries", "The zip has duplicate entries, so it can't be checked reliably",
                        "%d name%s appear%s more than once: %s. Names are compared without case, with backslashes "
                        "read as slashes, empty and \".\" path segments ignored, \"..\" applied, and trailing spaces "
                        "and dots removed. The package is ambiguous: the check can't tell which copy counts, so it "
                        "doesn't check the package."
                        % (n, "" if n == 1 else "s", "s" if n == 1 else "", "; ".join(head(shown, 10))),
                        "Export the solution again and check the .zip the export produces, without editing or "
                        "re-zipping it.")


def load_solution(pkg, rep):
    if not pkg.has("solution.xml"):
        raise not_a_solution(pkg)
    if pkg.duplicates:
        raise duplicate_entries(pkg)
    root = load_xml(pkg, "solution.xml")
    manifest = kid(root, "SolutionManifest")
    if root.tag != "ImportExportXml" or manifest is None:
        raise PackageError("not-a-solution", "solution.xml is not a Dataverse solution manifest",
                           "Root element is %s; an export has %s containing %s."
                           % (v("<" + str(root.tag) + ">"), v("<ImportExportXml>"), v("<SolutionManifest>")),
                           "Export the solution again from Power Apps or with pac solution export.")
    missing = manifest_gaps(manifest)
    if missing:
        detail = ("%s %s. Every export we've seen has a unique name, a version, Managed 0 or 1, a publisher "
                  "with a unique name and customization prefix, and a %s element whose components each have "
                  "a type." % (v("<SolutionManifest>"), "; ".join(missing), v("<RootComponents>")))
        fix = ("Export the solution again from Power Apps or with pac solution export, and check the .zip that "
               "export produces without editing it.")
        if text(kid(manifest, "Managed")) == "2":
            # Managed 2 is what SolutionPackager (pac solution unpack --packagetype Both) writes into
            # unpacked source; exports carry 0 or 1.
            detail += (" Managed 2 is the value unpacked solution source carries when it was unpacked as both "
                       "managed and unmanaged, so this looks like source zipped up rather than an export.")
            fix = ("Pack it (pac solution pack --packagetype Managed or Unmanaged) or export the solution again, "
                   "then check that .zip.")
        raise PackageError("not-a-solution", "solution.xml is not a complete solution manifest", detail, fix)
    return root, manifest


def manifest_gaps(manifest):
    """What a <SolutionManifest> lacks that every export we've seen has, as a list of phrases
    (empty when it is complete). A present but oddly formatted version or prefix is left to
    check_identity(), which reports it as a warning."""
    gaps = []

    def need(el, name, label):
        child = kid(el, name)
        if child is None:
            gaps.append("has no %s" % v(label))
        elif not text(child):
            gaps.append("has no value in %s" % v(label))

    need(manifest, "UniqueName", "<UniqueName>")
    need(manifest, "Version", "<Version>")
    managed = text(kid(manifest, "Managed"))
    if managed not in ("0", "1"):
        gaps.append("has %s rather than Managed 0 or 1" % (("Managed " + v(managed)) if managed else "no " + v("<Managed>")))
    pub = kid(manifest, "Publisher")
    if pub is None:
        gaps.append("has no %s" % v("<Publisher>"))
    else:
        need(pub, "UniqueName", "<Publisher><UniqueName>")
        need(pub, "CustomizationPrefix", "<Publisher><CustomizationPrefix>")
    rcs = kid(manifest, "RootComponents")
    if rcs is None:
        gaps.append("has no %s" % v("<RootComponents>"))
    else:
        # Only a missing type counts as malformed. Identifiers vary: most components carry a
        # schemaName or id, some only a parentId, and the classic site map (type 62) none at all.
        bad = [rc for rc in kids(rcs, "RootComponent") if not attr(rc, "type")]
        if bad:
            gaps.append("has %d %s element%s without a type"
                        % (len(bad), v("<RootComponent>"), "" if len(bad) == 1 else "s"))
    return gaps


# --------------------------------------------------------------------------- 1. summary
def summarise(ctx, rep):
    m, pub = ctx.manifest, kid(ctx.manifest, "Publisher")
    managed = {"0": "Unmanaged", "1": "Managed"}.get(
        ctx.managed, "Unknown (Managed=%s)" % (v(ctx.managed) if ctx.managed else "missing"))
    rep.package.update({
        "uniqueName": ctx.unique_name,
        "displayName": localized(m),
        "version": text(kid(m, "Version")),
        "packageType": managed,
        "publisher": {
            "uniqueName": text(kid(pub, "UniqueName")),
            "displayName": localized(pub),
            "customizationPrefix": text(kid(pub, "CustomizationPrefix")),
            "optionValuePrefix": text(kid(pub, "CustomizationOptionValuePrefix")),
        },
        # Learn's code-components ALM page calls ImportExportXml/Version the solution version,
        # but in exports we've seen the solution version is <SolutionManifest><Version> and this
        # attribute matches the source environment's OrganizationVersion. Reported as-is.
        "importExportXmlVersion": attr(ctx.sol_root, "version"),
        "generatedBy": attr(ctx.sol_root, "generatedBy"),
    })
    counts = {}
    for r in ctx.roots:
        key = r.get("type", "")
        b = r.get("behavior", "")
        row = counts.setdefault(key, {"type": key, "label": type_label(key), "0": 0, "1": 0, "2": 0, "other": 0})
        row[b if b in ("0", "1", "2") else "other"] += 1
    rep.package["rootComponents"] = sorted(counts.values(), key=lambda r: (not is_int(r["type"]),
                                           int(r["type"]) if is_int(r["type"]) else 0, r["type"]))
    rep.package["contents"] = inventory(ctx)


def inventory(ctx):
    c = ctx.cust
    ents = kids(kid(c, "Entities"), "Entity")
    forms = sum(len(kids(f, "systemform")) for e in ents for f in kids(kid(e, "FormXml"), "forms"))
    views = sum(len(kids(kid(kid(e, "SavedQueries"), "savedqueries"), "savedquery")) for e in ents)
    wfs = kids(kid(c, "Workflows"), "Workflow")
    flows = [w for w in wfs if field(w, "Category") == "5"]
    bpfs = [w for w in wfs if field(w, "Category") == "4"]
    folders = {}
    for n in ctx.pkg.names():
        top = n.split("/", 1)[0] if "/" in n else ""
        if top in ("customapis", "uxagentprojects", "duplicaterules", "dvtablesearchs", "formulas"):
            folders[top] = folders.get(top, 0) + 1
    out = [
        ("Tables in customizations.xml", len(ents)),
        ("Forms", forms),
        ("Views", views),
        ("Global choices", len(kids(kid(c, "optionsets"), "optionset"))),
        ("Security roles", len(kids(kid(c, "Roles"), "Role"))),
        ("Web resources", len(ctx.webresource_names)),
        ("Code components", len(kids(kid(c, "CustomControls"), "CustomControl"))),
        ("Model-driven apps", len(kids(kid(c, "AppModules"), "AppModule"))),
        ("Site maps", len(kids(kid(c, "AppModuleSiteMaps"), "AppModuleSiteMap"))),
        ("Cloud flows", len(flows)),
        ("Business process flows", len(bpfs)),
        ("Other processes", len(wfs) - len(flows) - len(bpfs)),
        ("Plug-in assemblies", len(kids(kid(c, "SolutionPluginAssemblies"), "PluginAssembly"))),
        ("Plug-in steps", len(kids(kid(c, "SdkMessageProcessingSteps"), "SdkMessageProcessingStep"))),
        ("Connection references", len(connection_references(ctx))),
        ("Environment variable definitions", len(environment_variables(ctx)[0])),   # cached on ctx
    ]
    labels = {"customapis": "Custom API files", "uxagentprojects": "Generative page files",
              "duplicaterules": "Duplicate rule files", "dvtablesearchs": "Table search files",
              "formulas": "Formula files"}
    out += [(labels[k], folders[k]) for k in sorted(folders)]
    return [{"item": k, "count": n} for k, n in out if n]


def check_identity(ctx, rep):
    p = rep.package
    size = ctx.pkg.size
    lim = IMPORT_SIZE_LIMIT
    if size > lim["decimalBytes"]:
        over = size > lim["bytes"]
        rep.add("solution-too-large", "blocker" if over else "warning",
                "The zip is larger than the import limit" if over else "The zip is at the import size limit",
                "The file is %s bytes (%s); the limit Learn gives is %s (checked %s). %s"
                % (format(size, ","), fmt_size(size), lim["label"], lim["checked"],
                   "That is over the limit whether a megabyte is read as 1,000,000 or 1,048,576 bytes." if over else
                   "That is over %s bytes but under %s bytes, so it depends on how the limit counts a megabyte."
                   % (format(lim["decimalBytes"], ","), format(lim["bytes"], ","))),
                "Learn gives the maximum size of a solution file as %s." % lim["label"],
                "Split the solution, or move large files (for example images or big web resources) out of it.",
                [lim["source"]], version_sensitive=True)
    ver = p.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", ver, flags=re.ASCII):
        rep.add("solution-version-format", "warning", "The solution version is not major.minor.build.revision",
                "%s is %s." % (v("<SolutionManifest><Version>"), v(ver) if ver else "empty"),
                "Learn describes a solution version as four parts, major.minor.build.revision (for example 1.0.0.0).",
                "Set a four-part version on the solution and export again.", [LEARN["version"]])
    prefix = p.get("publisher", {}).get("customizationPrefix", "")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,7}", prefix, flags=re.ASCII) or prefix.lower().startswith("mscrm"):
        rep.add("publisher-prefix", "warning", "The publisher prefix breaks the documented rules",
                "%s is %s." % (v("<CustomizationPrefix>"), v(prefix) if prefix else "empty"),
                "A publisher prefix is 2 to 8 alphanumeric characters, starts with a letter and can't start "
                "with mscrm.", "Use a publisher whose prefix follows the rules.", [LEARN["publisher_prefix"]])
    ovp = p.get("publisher", {}).get("optionValuePrefix", "")
    if not (re.fullmatch(r"\d+", ovp, flags=re.ASCII) and 10000 <= int(ovp) <= 99999):
        rep.add("publisher-option-value-prefix", "warning", "The publisher option value prefix is out of range",
                "%s is %s." % (v("<CustomizationOptionValuePrefix>"), v(ovp) if ovp else "empty"),
                "Learn's Publisher table reference gives the option value prefix as an integer from 10000 to 99999.",
                "Use a publisher whose option value prefix is in range.", [LEARN["publisher_table"]])


# --------------------------------------------------------------------------- 2. missing dependencies
def dep_parts(el):
    a = dict((k.lower(), (val or "").strip()) for k, val in el.attrib.items())
    ids = sorted(k for k in a if k.startswith("id.") and a[k])
    parent_ids = [k for k in ids if "parent" in k]
    own_ids = [k for k in ids if "parent" not in k]
    name = (a.get("schemaname") or (a[own_ids[-1]] if own_ids else "") or a.get("displayname")
            or a.get("id") or "(unnamed)")
    parent = a.get("parentschemaname") or a.get("parentdisplayname") or (a[parent_ids[0]] if parent_ids else "")
    display = a.get("displayname", "")
    return a, name, parent, display


def dep_label(el):
    a, name, parent, display = dep_parts(el)
    s = "%s %s" % (type_label(a.get("type")), v(name))
    if parent:
        s += " on %s" % v(parent)
    if display and display != name and len(display) <= 80 and "=" not in display:
        s += " (%s)" % v(display)
    return s


def check_missing_dependencies(ctx, rep):
    groups, platform = {}, []
    owned = {}   # (type, name, parent) -> one blocker per missing component, however many entries list it
    for md_el in kids(kid(ctx.manifest, "MissingDependencies"), "MissingDependency"):
        req, dep = kid(md_el, "Required"), kid(md_el, "Dependent")
        if req is None:
            continue
        a, name, parent, _ = dep_parts(req)
        sol = a.get("solution", "")
        sol_name = sol.split("(")[0].strip()
        values = [a.get("schemaname", ""), a.get("parentschemaname", "")] + \
                 [val for k, val in a.items() if k.startswith("id.")]
        prefixed = any(ctx.owned(x) for x in values)
        needed_by = dep_label(dep) if dep is not None else "(dependent not listed)"
        rtype = a.get("type", "")
        if lc(sol_name) == "active" or (sol_name and lc(sol_name) == lc(ctx.unique_name)) or (prefixed and not sol_name):
            root = next((ctx.root_index[(rtype, x)] for x in sorted(ident_values(a))
                         if (rtype, x) in ctx.root_index), None)
            if root is not None:
                # In the package as a root component, but recorded as a missing dependency
                # anyway (typically a table packaged with behavior 1 or 2). Reported with
                # the table-packaging finding, or on its own, as a warning.
                key = (rtype, lc(root.get("schemaname") or root.get("id") or name).strip("{}"))
                entry = ctx.packaged_missing.setdefault(key, {"root": root, "label": dep_label(req), "entries": []})
                entry["entries"].append("solution=%s, needed by %s" % (v(sol or "(none)"), needed_by))
                continue
            key = (rtype, lc(name), lc(parent))
            g = owned.get(key)
            if g is None:
                g = owned[key] = {"attrs": a, "name": name, "parent": parent, "label": dep_label(req),
                                  "prefixed": prefixed, "sols": {}, "dependents": {}, "entries": 0}
            g["entries"] += 1
            g["sols"][sol or "(none)"] = True
            g["dependents"][needed_by] = True
            continue
        pkg_el = kid(req, "package")
        package = ""
        if pkg_el is not None:
            package = " ".join(x for x in (attr(pkg_el, "appName"), attr(pkg_el, "version")) if x)
        entry = {"required": dep_label(req), "neededBy": needed_by}
        if rtype == "66" and sol_name:
            # A code component another named solution provides: a prerequisite, not a
            # packaging gap in this solution (see check_code_components).
            ctx.external_controls |= ident_values(a, extra=("displayname",))
        ctx.prerequisite_ids |= ident_values(a) | {lc(name)}
        if lc(sol_name) == "system":
            platform.append(entry)
            continue
        key = sol or "(solution not named)"
        g = groups.setdefault(key, {"solution": key, "package": package, "samePublisher": False, "components": []})
        g["samePublisher"] = g["samePublisher"] or prefixed
        if package and not g["package"]:
            g["package"] = package
        g["components"].append(entry)
    for g in owned.values():
        a, name = g["attrs"], g["name"]
        what = "%s %s%s" % (type_label(a.get("type")), v(name), " on %s" % v(g["parent"]) if g["parent"] else "")
        if g["prefixed"]:
            f_title = "Missing component from this publisher: %s" % what
            reason = "It carries this publisher's prefix (%s) and isn't in this package" % v(ctx.prefix + "_")
        else:
            f_title = "Missing component with no installable source: %s" % what
            reason = ("solution.xml names no solution you could install first for it (solution=%s), and it "
                      "isn't in this package" % " or ".join(v(s) for s in g["sols"]))
        dependents = list(g["dependents"])
        listed = ("" if g["entries"] == 1 else " in %d entries" % g["entries"])
        rep.add("owned-missing-dependency", "blocker", f_title,
                "solution.xml %s lists Required %s, solution=%s%s, needed by %s."
                % (v("<MissingDependencies>"), g["label"], " or ".join(v(s) for s in g["sols"]), listed,
                   "; ".join(head(dependents, 8))),
                reason + ", so a clean target won't have it. Import fails when a required component is "
                "neither in the solution nor in the target.",
                "Add the component to this solution and export again, or install the solution that contains "
                "it in the target first. If it's no longer needed, remove the reference from the dependent "
                "component%s." % ("" if len(dependents) == 1 else "s"),
                [LEARN["missing_deps"], LEARN["dependency_tracking"]],
                component=name, component_type=a.get("type"))
        for x in ident_values(a) | {lc(name)}:
            ctx.owned_missing.setdefault(x, rep.findings[-1])
    rep.prerequisites = sorted(groups.values(), key=lambda g: (not g["samePublisher"], -len(g["components"]), g["solution"]))
    if platform:
        rep.add("platform-missing-dependency", "info",
                "%d missing-dependency %s the platform's System solution"
                % (len(platform), "entry names" if len(platform) == 1 else "entries name"),
                "Required: %s." % "; ".join(head(unique_required({"components": platform}), 10)),
                "These come from the platform's own System solution rather than an app or solution you install. "
                "An entry fails the import only if the target lacks the component too. Learn advises keeping "
                "environments aligned to the same Dataverse and app versions to avoid version-related missing "
                "dependency errors.",
                "Confirm the target's Dataverse version is at least the source environment's.", [LEARN["missing_deps"]])


def unique_required(group):
    """Distinct Required labels in a prerequisite group, in first-seen order."""
    return list(dict.fromkeys(c["required"] for c in group["components"]))


# --------------------------------------------------------------------------- 3. table behavior
def check_owned_tables(ctx, rep):
    entities = {}
    for e in kids(kid(ctx.cust, "Entities"), "Entity"):
        for n in (text(kid(e, "Name")), attr(walk(e, "EntityInfo", "entity"), "Name")):
            if n:
                entities.setdefault(lc(n), e)
    for r in ctx.roots:
        if r.get("type") != "1" or not ctx.owned(r.get("schemaname")):
            continue
        b = r.get("behavior", "")
        if b not in ("1", "2"):
            continue
        name = r.get("schemaname")
        e = entities.get(lc(name))
        ent = walk(e, "EntityInfo", "entity")
        if ent is None:
            shape = "customizations.xml has no table definition for it"
        else:
            others = [c for c in list(ent) if isinstance(c.tag, str) and c.tag.lower() != "attributes"]
            cols = len(kids(kid(ent, "attributes"), "attribute"))
            if not others:
                shape = ("customizations.xml carries only %d column%s for it, with no table definition"
                         % (cols, "" if cols == 1 else "s"))
            elif kid(e, "FormXml") is None and kid(e, "SavedQueries") is None:
                shape = "customizations.xml carries the table metadata but not its forms or views"
            else:
                shape = "customizations.xml carries the table metadata"
        listed = ctx.packaged_missing.pop(("1", lc(name)), None)
        also = ""
        if listed:
            also = (" solution.xml also lists it under %s as a Required component (%s)."
                    % (v("<MissingDependencies>"), "; ".join(head(listed["entries"], 5))))
        rep.add("owned-table-not-behavior-0", "warning",
                "Your table %s is packaged with behavior %s (%s)" % (v(name), b, BEHAVIOR_LABELS[b]),
                "solution.xml RootComponent type 1 %s behavior=%s; %s.%s" % (v(name), b, shape, also),
                "A table that doesn't exist in the target, or has never been imported into it, must be added with "
                "'Include all objects', otherwise the import fails with a missing dependency error. This check "
                "can't see the target: it's fine if the target already has the table (for example from a base "
                "solution you install first).",
                "If the target may not have the table, add it to the solution with 'Include all objects' and "
                "export again. Learn notes that choice can't be undone without removing the table and adding it "
                "again.", [LEARN["segmented"], LEARN["missing_deps"], LEARN["solution_component"]],
                component=name, component_type="1")


def report_packaged_missing(ctx, rep):
    """Root components of this package that solution.xml also lists as missing dependencies
    and that the table-packaging check didn't already report."""
    for (rtype, key), info in sorted(ctx.packaged_missing.items()):
        r = info["root"]
        b = r.get("behavior", "")
        name = r.get("schemaname") or r.get("id") or key
        rep.add("packaged-component-listed-missing", "warning",
                "%s is in this package but also listed as a missing dependency" % info["label"],
                "solution.xml RootComponent type %s %s behavior=%s%s; %s also lists it as Required (%s)."
                % (v(rtype), v(name), v(b), " (%s)" % BEHAVIOR_LABELS[b] if b in BEHAVIOR_LABELS else "",
                   v("<MissingDependencies>"), "; ".join(head(info["entries"], 5))),
                "solution.xml records it as a missing dependency even though it is a root component of this "
                "package. Import fails when a required component is neither in the solution nor in the target, so "
                "treat it as something the target must already have unless you include it in full.",
                "If the target may not have it, include it in full (for a table, 'Include all objects') and export "
                "again.", [LEARN["missing_deps"], LEARN["segmented"]], component=name, component_type=rtype)
    ctx.packaged_missing.clear()


# --------------------------------------------------------------------------- 4. code components
def control_folders(ctx):
    folders = {}
    for n in ctx.pkg.names():
        parts = n.split("/")
        if len(parts) >= 3 and parts[0] == "controls":
            folders.setdefault(parts[1], set()).add("/".join(parts[2:]))
    return folders


def form_control_usages(ctx):
    usages = {}
    seen = set()
    for e in kids(kid(ctx.cust, "Entities"), "Entity"):
        table = text(kid(e, "Name")) or attr(walk(e, "EntityInfo", "entity"), "Name")
        for forms in kids(kid(e, "FormXml"), "forms"):
            for sf in kids(forms, "systemform"):
                where = "form %s (%s) on %s" % (v(localized(sf) or text(kid(sf, "formid"))),
                                                v(attr(forms, "type") or "form"), v(table))
                for cc in sf.iter("customControl"):
                    seen.add(id(cc))
                    n = attr(cc, "name")
                    if n:
                        usages.setdefault(lc(n), {"name": n, "where": []})
                        if where not in usages[lc(n)]["where"]:
                            usages[lc(n)]["where"].append(where)
    for cc in ctx.cust.iter("customControl"):
        n = attr(cc, "name")
        if n and id(cc) not in seen:
            usages.setdefault(lc(n), {"name": n, "where": []})
            if "customizations.xml outside a table form" not in usages[lc(n)]["where"]:
                usages[lc(n)]["where"].append("customizations.xml outside a table form")
    return usages


def manifests(ctx):
    """(entry key, control folder name as stored) for each Controls/<name>/ControlManifest.xml."""
    for n in ctx.pkg.names():
        parts = n.split("/")
        if len(parts) == 3 and parts[0] == "controls" and parts[2] == "controlmanifest.xml":
            yield n, ctx.pkg.original(n).split("/")[1]


def manifest_file_paths(root):
    """The code, css, resx and img paths a ControlManifest.xml names, relative to its folder."""
    return [attr(el, "path") for tag in ("code", "css", "resx", "img") for el in root.iter(tag)]


# Attributes Learn's control element reference marks as required. description-key, control-type
# and preview-image are optional there, so their absence isn't a problem.
CONTROL_REQUIRED_ATTRS = ("namespace", "constructor", "version", "display-name-key")
CONTROL_TYPES = ("standard", "virtual")


def manifest_problem(root):
    """Why a parsed ControlManifest.xml doesn't have the shape Learn's manifest schema reference
    gives, or "": a <manifest> root holding exactly one <control>, with the required namespace, constructor,
    version and display-name-key attributes, a control-type (if any) of standard or virtual, and
    exactly one <resources> element."""
    if lc(root.tag) != "manifest":
        return "its root element is %s, not %s" % (v("<%s>" % root.tag), v("<manifest>"))
    ctrls = kids(root, "control")
    if not ctrls:
        return "%s has no %s element" % (v("<manifest>"), v("<control>"))
    if len(ctrls) > 1:
        return "%s has %d %s elements, not exactly one" % (v("<manifest>"), len(ctrls), v("<control>"))
    ctrl = ctrls[0]
    missing = [a for a in CONTROL_REQUIRED_ATTRS if not attr(ctrl, a)]
    if missing:
        return "its %s element has no %s attribute%s" % (
            v("<control>"), ", ".join(missing[:-1]) + (" or " if len(missing) > 1 else "") + missing[-1],
            "" if len(missing) == 1 else "s")
    ctype = attr(ctrl, "control-type")
    if ctype and lc(ctype) not in CONTROL_TYPES:
        return "its %s control-type is %s, not standard or virtual" % (v("<control>"), v(ctype))
    resources = len(kids(ctrl, "resources"))
    if resources != 1:
        return "its %s element has %d %s elements, not exactly one" % (v("<control>"), resources, v("<resources>"))
    return ""


def manifest_info(ctx):
    """Every packaged Controls/<name>/ControlManifest.xml, read and validated once and cached on ctx,
    as {lower-cased control name: info}. info["state"] is one of:
      valid    well-formed, with the shape manifest_problem() checks (info["root"], info["control_el"])
      invalid  not well-formed, or the wrong shape (info["reason"])
      refused  a DOCTYPE, or this file alone is over a size or node limit (info["reason"])
      damaged  can't be read back from the zip; reported once, as package-entry-damaged
      budget   not read because the run's total read or parse budget was spent first; the file
               itself may be fine, so it is listed under Not checked"""
    if ctx.control_manifests is not None:
        return ctx.control_manifests
    out = {}
    for key, control in manifests(ctx):
        info = out[lc(control)] = {"key": key, "control": control, "path": ctx.pkg.original(key),
                                   "state": "invalid", "reason": "", "root": None, "control_el": None}
        try:
            root = ctx.pkg.xml(key)
        except DamagedEntry:
            info["state"] = "damaged"
            continue
        except OverBudget as e:
            info["state"], info["reason"] = "budget", str(e)
            continue
        except DoctypeRefused:
            info["state"] = "refused"
            info["reason"] = "it has a document type declaration (DOCTYPE), which this check refuses"
            continue
        except CheckSkipped as e:   # this file alone is over a size or node limit
            info["state"], info["reason"] = "refused", str(e)
            continue
        except (ET.ParseError, UnicodeDecodeError, ValueError) as e:
            info["reason"] = "it isn't well-formed XML (%s)" % v(e)
            continue
        problem = manifest_problem(root)
        if problem:
            info["reason"] = problem
            continue
        info.update(state="valid", root=root, control_el=kids(root, "control")[0])
    ctx.control_manifests = out
    return out


def check_code_components(ctx, rep):
    folders = control_folders(ctx)
    mans = manifest_info(ctx)   # validated here, before the form check relies on it
    declared = {}
    for cc in kids(kid(ctx.cust, "CustomControls"), "CustomControl"):
        n = text(kid(cc, "Name"))
        if n:
            declared[lc(n)] = n
    roots = dict((lc(r.get("schemaname")), r.get("schemaname")) for r in ctx.roots
                 if r.get("type") == "66" and r.get("schemaname"))
    usages = form_control_usages(ctx)
    state = {True: "present", False: "missing"}

    def places(key, name):
        """The three places a packaged control appears, each present or missing."""
        info = mans.get(key)
        path = v("Controls/%s/ControlManifest.xml" % (info["control"] if info else name))
        if info is None:
            first = "%s missing%s" % (path, " (the folder has other files)" if key in folders else "")
        elif info["state"] in ("invalid", "refused"):
            first = "%s present, but %s" % (path, info["reason"])
        else:
            first = "%s present" % path
        return [first, "%s entry %s" % (v("<CustomControls>"), state[key in declared]),
                "RootComponent type 66 %s" % state[key in roots]]

    for key, u in sorted(usages.items()):
        if not ctx.owned(u["name"]) or key in ctx.external_controls:
            # key in external_controls: solution.xml names another solution that provides it,
            # so it is listed under prerequisites instead.
            continue
        if key in mans and key in declared and key in roots:
            # In all three places. An unusable manifest is reported below, as a blocker; one the
            # run's total read or parse limit stopped is listed under Not checked.
            continue
        partly = key in folders or key in declared or key in roots
        rep.add("form-control-not-packaged", "blocker",
                "Code component %s is used on a form but isn't %s" % (v(u["name"]),
                                                                      "fully packaged" if partly else "in the package"),
                "Used on %s. In the package: %s. solution.xml names no other solution that provides it."
                % ("; ".join(head(u["where"], 8)), "; ".join(places(key, u["name"]))),
                "A form that binds a code component needs that component in the target. In exports we've seen, "
                "a packaged code component appears in three places: its %s folder with a ControlManifest.xml, a %s "
                "entry in customizations.xml and a type 66 root component in solution.xml. %s Learn: when solutions "
                "depend on a code component solution, that solution must be installed in the target first."
                % (v("Controls/<name>/"), v("<CustomControls>"),
                   "This one is missing from at least one of them, so the check doesn't count it as packaged."
                   if partly else "This one is in none of them, so a clean target won't have it."),
                "Add the code component to this solution and export again, or install the solution that "
                "contains it in the target first.", [LEARN["pcf_alm"], LEARN["dependency_tracking"]],
                component=u["name"], component_type="66")
        ctx.unpackaged_controls[key] = rep.findings[-1]
    reported = set()   # controls whose manifest problem is reported below, at either severity
    for key, info in mans.items():
        u = usages.get(key)
        if info["state"] == "budget":
            rep.skipped("Code components on forms", "%s wasn't read (%s), so its shape, platform libraries and "
                        "resource files weren't checked%s." % (
                            v(info["path"]), info["reason"],
                            ", and the check couldn't confirm that this code component, which is used in "
                            "customizations.xml, is packaged" if u else ""))
        if info["state"] not in ("invalid", "refused") or key in ctx.unpackaged_controls:
            continue
        owned = ctx.owned(info["control"])
        external = key in ctx.external_controls
        in_package = [p for p, present in (("a %s entry" % v("<CustomControls>"), key in declared),
                                           ("a type 66 root component", key in roots)) if present]
        if u:
            where = "Used on %s." % "; ".join(head(u["where"], 8))
        else:
            where = "Not used in customizations.xml; %s this publisher's prefix." % (
                "it carries" if owned else "it doesn't carry")
        if external:
            # solution.xml names another solution that provides this control (a prerequisite, as
            # in the form check above), so the copy in this package is only a warning.
            severity, reason = "warning", (
                " solution.xml names another solution that provides this code component, so it is listed under "
                "prerequisites and this is a warning.")
        elif u:
            severity, reason = "blocker", " A form that binds a code component needs that component in the target."
        elif owned:
            severity, reason = "blocker", (" It carries this publisher's prefix, so the check treats it as your own "
                                           "component.")
        elif in_package:
            severity, reason = "blocker", (" The package also has %s for it, so the check treats it as part of this "
                                           "package." % " and ".join(in_package))
        else:
            severity, reason = "warning", (
                " It isn't used in customizations.xml, has no %s entry or type 66 root component, and doesn't carry "
                "this publisher's prefix, so this is a warning." % v("<CustomControls>"))
        rep.add("control-manifest-invalid", severity,
                "Code component %s has %s" % (v(info["control"]), "an invalid ControlManifest.xml"
                                              if info["state"] == "invalid" else
                                              "a ControlManifest.xml this check can't read"),
                "%s: %s. %s In the package: %s." % (v(info["path"]), info["reason"], where,
                                                    "; ".join(places(key, info["control"])[1:])),
                "Learn's manifest schema reference defines a code component's manifest as a %s element holding one "
                "%s element, whose namespace, constructor, version and display-name-key attributes are required, "
                "whose control-type (if set) is standard or virtual, and which holds one resources element; the "
                "ControlManifest.xml files in exports we've seen have that shape. %s, so it doesn't count the "
                "control as packaged, and the "
                "platform-library and resource-file checks skip it.%s"
                % (v("<manifest>"), v("<control>"),
                   "The check can't confirm this one does" if info["state"] == "invalid" else
                   "The check refuses to read this one (the file may still be valid) and can't confirm its shape",
                   reason),
                "Export the solution again and check the new .zip; don't edit the export by hand. " + (
                    "Install the solution that provides this code component in the target first (see prerequisites)."
                    if external else
                    "If a new export has the same file, rebuild the code component and add it to the solution again."),
                [LEARN["pcf_manifest"], LEARN["pcf_control_element"], LEARN["edit_customizations"]],
                component=info["control"], component_type="66")
        reported.add(key)
        if severity == "blocker":
            # merge_duplicates() folds an owned type 66 missing-dependency blocker into this one;
            # a warning must never absorb a blocker.
            ctx.unpackaged_controls[key] = rep.findings[-1]
    for key in sorted(set(mans) | set(declared) | set(roots)):
        if key in ctx.unpackaged_controls or key in reported or not ctx.owned(key):
            continue
        present = {"folder": key in mans, "declared": key in declared, "root": key in roots}
        if all(present.values()):
            continue
        name = declared.get(key) or roots.get(key) or mans[key]["control"]
        desc = ["%s %s" % (v("Controls/%s/ControlManifest.xml" % name), state[present["folder"]]),
                "%s entry %s" % (v("<CustomControls>"), state[present["declared"]]),
                "RootComponent type 66 %s" % state[present["root"]]]
        rep.add("control-packaging-inconsistent", "warning",
                "Code component %s is only partly packaged" % v(name),
                "; ".join(desc) + ".",
                "In exports we've seen, each code component appears in three places: its %s folder, a %s entry "
                "in customizations.xml and a type 66 root component in solution.xml. When one is missing, the "
                "zip was probably edited after export. Learn lists a few supported edits to an exported "
                "customizations.xml (ribbon, site map, FormXml, saved queries, ISV.config); defining other "
                "components by editing it isn't supported." % (v("Controls/<name>/"), v("<CustomControls>")),
                "Export the solution again rather than editing the zip by hand.",
                [LEARN["supported_customizations"], LEARN["edit_customizations"]],
                component=name, component_type="66")


# --------------------------------------------------------------------------- 5. platform libraries
def allowed_text(lib):
    a = PLATFORM_LIBRARIES["allowed"][lib]
    parts = list(a["exact"]) + ["%s to %s" % r for r in a["ranges"]]
    return ", ".join(parts)


def version_allowed(lib, ver):
    t = version_tuple(ver)
    if t is None:
        return False
    a = PLATFORM_LIBRARIES["allowed"][lib]
    if any(t == version_tuple(x) for x in a["exact"]):
        return True
    return any(version_tuple(lo) <= t <= version_tuple(hi) for lo, hi in a["ranges"])


def check_platform_libraries(ctx, rep):
    for info in manifest_info(ctx).values():
        if info["state"] != "valid":
            continue    # reported by the code-component check, as package-entry-damaged, or under Not checked
        root, ctrl, control, path = info["root"], info["control_el"], info["control"], info["path"]
        majors = set()
        for pl in root.iter("platform-library"):
            lib, ver = attr(pl, "name"), attr(pl, "version")
            if lib not in PLATFORM_LIBRARIES["allowed"]:
                rep.add("platform-library-unknown", "warning",
                        "%s declares an unknown platform library %s" % (v(control), v(lib)),
                        "%s declares platform-library name=%s version=%s." % (v(path), v(lib), v(ver)),
                        "Learn documents React and Fluent as the platform library names.",
                        "Remove the element or correct the name, rebuild and export again.",
                        [LEARN["platform_library_element"]], version_sensitive=True, component=control)
                continue
            t = version_tuple(ver)
            if lib == "Fluent" and t:
                majors.add(t[0])
            if version_allowed(lib, ver):
                continue
            hint = ""
            if ver in PLATFORM_LIBRARIES["loaded"].get(lib, []):
                hint = " %s is a version Learn lists as loaded at runtime, which is not what a manifest declares." % v(ver)
            rep.add("platform-library-version", "blocker",
                    "%s declares %s %s, outside the allowed versions" % (v(control), lib, v(ver or "(no version)")),
                    "%s declares platform-library name=%s version=%s. Allowed declarations (Learn, checked %s): "
                    "%s.%s" % (v(path), lib, v(ver), PLATFORM_LIBRARIES["checked"], allowed_text(lib), hint),
                    "Learn's supported platform libraries list gives an allowed version range for each library and "
                    "is where Learn points for valid platform-library versions. This declaration is outside that "
                    "range.",
                    "Declare a version inside the allowed range in the control's source manifest "
                    "(ControlManifest.Input.xml), rebuild in production mode, repackage and export again. Re-check "
                    "the Learn table first: the ranges change.",
                    [PLATFORM_LIBRARIES["source"]], version_sensitive=True, component=control, component_type="66")
        if {8, 9} <= majors:
            rep.add("platform-library-version", "blocker",
                    "%s declares both Fluent 8 and Fluent 9" % v(control),
                    "%s declares Fluent platform libraries from both major versions." % v(path),
                    "Learn: Fluent 8 and Fluent 9 are each supported but can't both be specified in the same manifest.",
                    "Keep one Fluent version, rebuild and export again.",
                    [PLATFORM_LIBRARIES["source"]], version_sensitive=True, component=control, component_type="66")
        built = next(root.iter("built-by"), None)
        pac = attr(built, "version")
        if ctrl is not None and lc(attr(ctrl, "control-type")) == "virtual" and lc(attr(built, "name")) == "pac":
            t, minimum = version_tuple(pac), version_tuple(PAC_FOR_VIRTUAL_CONTROLS["minimum"])
            if t is not None and t < minimum:
                rep.add("pcf-built-with-old-pac", "warning",
                        "%s was built with Power Platform CLI %s" % (v(control), v(pac)),
                        "%s: control-type=virtual, built-by pac version %s." % (v(path), v(pac)),
                        "Learn advises rebuilding and redeploying existing virtual (React) controls with Power "
                        "Platform CLI %s or later to support future platform React upgrades."
                        % PAC_FOR_VIRTUAL_CONTROLS["minimum"],
                        "Rebuild the control with a current Power Platform CLI and export again.",
                        [PAC_FOR_VIRTUAL_CONTROLS["source"]], version_sensitive=True, component=control)


# --------------------------------------------------------------------------- 6. development bundles
DEVTOOL_BANNER = re.compile(rb'The "eval" devtool')
EVAL_COUNT_CAP = 10000   # eval( occurrences looked at per file


def line_leading_evals(data):
    """How many of the first EVAL_COUNT_CAP eval( occurrences start a line (after optional
    spaces or tabs). Uses bytes.split and rstrip, which run in linear time whatever the input."""
    if b"eval(" not in data:
        return 0
    n = 0
    pieces = data.split(b"eval(", EVAL_COUNT_CAP)
    for i, before in enumerate(pieces[:-1]):
        rest = before.rstrip(b" \t")
        if (i == 0 and not rest) or rest.endswith(b"\n"):
            n += 1
    return n


def check_dev_bundles(ctx, rep):
    for n in ctx.pkg.names():
        parts = n.split("/")
        if len(parts) < 3 or parts[0] != "controls" or not n.endswith(".js"):
            continue
        try:
            data = ctx.pkg.read(n)
        except DamagedEntry:
            continue    # reported once as package-entry-damaged
        except CheckSkipped as e:
            rep.skipped("Development builds", str(e))
            continue
        banner = bool(DEVTOOL_BANNER.search(data))
        evals = line_leading_evals(data)
        if not banner and not evals:
            continue
        markers = []
        if banner:
            markers.append("webpack's 'The \"eval\" devtool has been used' banner")
        if evals:
            markers.append("%s line-leading eval( call%s" % (
                format(evals, ",") + (" or more" if evals >= EVAL_COUNT_CAP else ""), "" if evals == 1 else "s"))
        original = ctx.pkg.original(n)
        control = original.split("/")[1]
        rep.add("dev-bundle-eval", "warning",
                "%s looks like a development build" % v(control),
                "%s (%s) contains %s." % (v(original), fmt_size(len(data)), " and ".join(markers)),
                "Webpack's development mode emits eval(), so this is likely a development build. Solution checker "
                "reports it as web-avoid-eval (rule avoid-eval, severity Critical), and where solution checker "
                "enforcement is in Block mode on a Managed Environment, critical violations block the import. "
                "Learn also advises against deploying a development build: it is often too large to import and "
                "can slow runtime performance.",
                "Rebuild the control in production mode (npm run build -- --buildMode production, or msbuild "
                "/p:configuration=Release for a solution project), repackage and export again.",
                [LEARN["pcf_eval"], LEARN["checker_rules"], LEARN["pcf_build"], LEARN["pcf_dev_builds"],
                 LEARN["checker_eval"], LEARN["checker_enforcement"]],
                component=control, component_type="66")


# --------------------------------------------------------------------------- 7. site map icons
def webresource_path_name(value):
    val = value.split("?", 1)[0].split("#", 1)[0].strip()
    m = re.match(r"(?i)^/?webresources/(.+)$", val)
    return m.group(1) if m else ""


def sitemap_subareas(ctx):
    seen = set()
    for sm in kids(kid(ctx.cust, "AppModuleSiteMaps"), "AppModuleSiteMap"):
        name = text(kid(sm, "SiteMapUniqueName")) or localized(sm)
        for sa in sm.iter("SubArea"):
            seen.add(id(sa))
            yield name, sa
    for sa in ctx.cust.iter("SubArea"):
        if id(sa) not in seen:
            yield "(site map)", sa


def check_sitemap(ctx, rep):
    for sitemap, sa in sitemap_subareas(ctx):
        sid = attr(sa, "Id") or "(no Id)"
        icon, vector = attr(sa, "Icon"), attr(sa, "VectorIcon")
        is_svg = icon.split("?", 1)[0].split("#", 1)[0].lower().endswith(".svg")
        if is_svg and not vector:
            rep.add("sitemap-svg-icon-without-vectoricon", "warning",
                    "Site map subarea %s puts an SVG in Icon and has no VectorIcon" % v(sid),
                    "Site map %s: SubArea Id=%s Icon=%s, no VectorIcon." % (v(sitemap), v(sid), v(icon)),
                    "Microsoft's model-apps plugin (microsoft/power-platform-skills, not Microsoft Learn) treats Icon "
                    "as the legacy raster slot and VectorIcon as the modern SVG slot, and says an SVG in Icon renders "
                    "as a placeholder in the modern navigation. Learn documents only the Icon property, and says the "
                    "Area icon applies only to the deprecated web client site map.",
                    "Set VectorIcon on the subarea to the SVG web resource (a /WebResources/... path or a "
                    "$webresource: reference). A raster Icon can stay as a fallback.",
                    [MODEL_APPS_PLUGIN, LEARN["sitemap_icons"]], version_sensitive=True, component=sid)
        if vector and attr(sa, "Entity") and not (vector.startswith("/") or lc(vector).startswith("$webresource:")):
            rep.add("sitemap-vectoricon-not-a-path", "warning",
                    "Site map subarea %s has a VectorIcon that is neither a path nor a $webresource: reference" % v(sid),
                    "Site map %s: SubArea Id=%s VectorIcon=%s." % (v(sitemap), v(sid), v(vector)),
                    "Microsoft's model-apps plugin (microsoft/power-platform-skills, not Microsoft Learn) expects a "
                    "table subarea's VectorIcon to be a /WebResources/... path or a $webresource: reference, not a "
                    "bare name.", "Point VectorIcon at the SVG web resource by path or with $webresource:.",
                    [MODEL_APPS_PLUGIN], version_sensitive=True, component=sid)
        for a_name in ("Icon", "VectorIcon", "Url"):
            val = attr(sa, a_name)
            wr = webresource_path_name(val)
            if not wr or not ctx.owned(wr) or lc(wr) in ctx.webresource_names:
                continue
            rep.add("sitemap-webresource-not-packaged", "warning",
                    "Site map subarea %s points at %s by path, and it isn't in the package" % (v(sid), v(wr)),
                    "Site map %s: SubArea Id=%s %s=%s; no web resource named %s in customizations.xml."
                    % (v(sitemap), v(sid), a_name, v(val), v(wr)),
                    "Learn documents that a site map creates a published dependency on a web resource when the "
                    "$webresource: directive is used. A plain /WebResources/ path isn't covered by that, so it may "
                    "not be listed as a missing dependency. The file has to be in this package or already in the "
                    "target.",
                    "Add the web resource to this solution, or confirm the target already has it.",
                    [LEARN["sitemap_dependency"]], component=wr, component_type="61")


# --------------------------------------------------------------------------- package integrity
def check_package_files(ctx, rep):
    refs = []
    c = ctx.cust
    for w in kids(kid(c, "WebResources"), "WebResource"):
        refs.append(("Web resource", text(kid(w, "Name")), text(kid(w, "FileName"))))
    for cc in kids(kid(c, "CustomControls"), "CustomControl"):
        refs.append(("Code component", text(kid(cc, "Name")), text(kid(cc, "FileName"))))
    for pa in kids(kid(c, "SolutionPluginAssemblies"), "PluginAssembly"):
        refs.append(("Plug-in assembly", attr(pa, "FullName").split(",")[0], text(kid(pa, "FileName"))))
    for w in kids(kid(c, "Workflows"), "Workflow"):
        for f in ("JsonFileName", "XamlFileName"):
            refs.append(("Process or flow", attr(w, "Name"), field(w, f)))
    missing = ["%s %s: %s" % (kind, v(name), v(path)) for kind, name, path in refs if path and not ctx.pkg.has(path)]
    # Each packaged ControlManifest.xml names its own resources (code, css, resx, img),
    # relative to the control's folder.
    for info in manifest_info(ctx).values():   # parsed once, by the code-component check
        if info["state"] != "valid":
            continue    # reported by the code-component check, as package-entry-damaged, or under Not checked
        folder = "Controls/%s/" % info["control"]
        for raw in manifest_file_paths(info["root"]):
            p = re.sub(r"^(?:\./)+", "", raw.replace("\\", "/")).lstrip("/")
            if p and not ctx.pkg.has(folder + p):
                missing.append("Code component %s: %s" % (v(info["control"]), v(folder + p)))
    if missing:
        rep.add("package-file-missing", "blocker", "Files the package refers to are missing from the zip",
                "Missing: %s." % "; ".join(head(missing, 15)),
                "customizations.xml or a code component's ControlManifest.xml refers to files the package doesn't "
                "contain, so the package is incomplete. That usually means the zip was damaged or edited after "
                "export; Learn warns that incorrect definitions in a hand-edited solution can prevent the import.",
                "Export the solution again rather than editing the zip by hand.",
                [LEARN["edit_customizations"], LEARN["export"]])


def report_damaged_entries(ctx, rep):
    """Every entry that can't be read back, found by reading the whole zip once."""
    ctx.pkg.verify()
    for kind, keys in (("ratio", ctx.pkg.unverified["ratio"]), ("budget", ctx.pkg.unverified["budget"])):
        if not keys:
            continue
        one = len(keys) == 1
        if kind == "ratio":
            reason = "%s more than %d times (above %s)" % ("expands" if one else "expand", MAX_RATIO,
                                                            fmt_size(RATIO_MIN_BYTES))
        else:
            reason = "came after the %s this check decompresses for that" % fmt_size(VERIFY_BUDGET)
        rep.skipped("Package files", "%d entr%s %s read back to check %s intact, because %s %s: %s."
                    % (len(keys), "y" if one else "ies", "wasn't" if one else "weren't", "it's" if one else "they're",
                       "it" if one else "they", reason, ", ".join(head([v(ctx.pkg.original(k)) for k in keys], 10))))
    if not ctx.pkg.damaged:
        return
    items = ["%s (%s)" % (v(ctx.pkg.original(k)), v(err)) for k, err in sorted(ctx.pkg.damaged.items())]
    rep.add("package-entry-damaged", "blocker", "Files in the zip are damaged or can't be read",
            "%d entr%s can't be read back: %s." % (len(items), "y" if len(items) == 1 else "ies", "; ".join(head(items, 10))),
            "The zip isn't intact as shipped: these files fail their checksum, are truncated, or are stored in a way "
            "a zip reader can't open. Checks that needed them skipped them.",
            "Export the solution again and check the new .zip. Don't re-zip or edit the export by hand.",
            [LEARN["export"], LEARN["edit_customizations"]])


# --------------------------------------------------------------------------- 8. import checklist
def connection_references(ctx):
    """Connection references in the package, computed once and cached on ctx."""
    if ctx.conn_refs is not None:
        return ctx.conn_refs
    refs = {}
    for el in kids(kid(ctx.cust, "connectionreferences"), "connectionreference"):
        name = attr(el, "connectionreferencelogicalname") or text(kid(el, "connectionreferencelogicalname"))
        if name:
            refs[lc(name)] = {"name": name, "display": text(kid(el, "connectionreferencedisplayname")),
                              "connector": text(kid(el, "connectorid")).rsplit("/", 1)[-1]}
    for n in ctx.pkg.names():
        if n.startswith("connectionreferences/") and n.endswith(".xml"):
            try:
                el = ctx.pkg.xml(n)
            except (ET.ParseError, CheckSkipped, UnicodeDecodeError, ValueError) as e:
                # Kept, so the import checklist can say which files it couldn't read rather than
                # silently leaving their connection references out.
                ctx.conn_ref_unreadable.append((ctx.pkg.original(n), str(e)))
                continue
            items = [el] if el.tag.lower() == "connectionreference" else list(el.iter("connectionreference"))
            for it in items:
                name = attr(it, "connectionreferencelogicalname") or text(kid(it, "connectionreferencelogicalname"))
                if name and lc(name) not in refs:
                    refs[lc(name)] = {"name": name, "display": text(kid(it, "connectionreferencedisplayname")),
                                      "connector": text(kid(it, "connectorid")).rsplit("/", 1)[-1]}
    ctx.conn_refs = refs
    return refs


def _has_value_key(obj):
    """True if any object in the parsed JSON has a "value" key. Iterative, so deep nesting is safe."""
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if any(isinstance(k, str) and lc(k) == "value" for k in o):
                return True
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    return False


def environment_variables(ctx):
    """Find definitions wherever they are; never keep their values. Returns (defs, notes).
    Computed once per package and cached on ctx."""
    if ctx.env is not None:
        return ctx.env
    defs, notes = {}, []
    names = ctx.pkg.names()
    value_files = {}   # folder -> values .json files directly inside it, indexed in one pass
    for n in names:
        if "/" in n and n.endswith(".json") and "environmentvariablevalue" in n:
            value_files.setdefault(n.rsplit("/", 1)[0], []).append(n)

    def add(el, folder):
        schema = attr(el, "schemaname") or text(kid(el, "schemaname")) or (folder.rsplit("/", 1)[-1] if folder else "")
        if not schema:
            return
        has_default = bool(text(kid(el, "defaultvalue")))
        has_value, unreadable = False, False
        for f in value_files.get(folder, []) if folder else []:
            try:
                has_value = has_value or _has_value_key(
                    json.loads(ctx.pkg.read(f, limit=MAX_JSON_BYTES).decode("utf-8-sig")))
            except Exception:   # damaged, too large, not JSON or nested too deeply
                unreadable = True
                notes.append("The value file %s for %s could not be read, so whether it ships a value is unknown."
                             % (v(ctx.pkg.original(f)), v(schema)))
        defs[lc(schema)] = {"name": schema, "display": attr(kid(el, "displayname"), "default"),
                            "hasDefault": has_default, "hasCurrentValue": has_value,
                            # A value file that couldn't be read: neither "has a value" nor "has none".
                            "valueUnknown": unreadable and not has_value}

    for n in names:
        if n.rsplit("/", 1)[-1] == "environmentvariabledefinition.xml":
            try:
                el = ctx.pkg.xml(n)
            except Exception as e:   # damaged, too large or not well-formed
                notes.append("%s could not be parsed (%s)." % (v(ctx.pkg.original(n)), v(e)))
                ctx.env_unreadable_defs.append(ctx.pkg.original(n))
                continue
            add(el, n.rsplit("/", 1)[0] if "/" in n else "")
    for holder in kids(ctx.cust, "EnvironmentVariableDefinitions"):
        for el in kids(holder, "environmentvariabledefinition"):
            add(el, "")
    listed = [r.get("schemaname") for r in ctx.roots if r.get("type") == "380" and r.get("schemaname")]
    # A definition whose file couldn't be read is already listed by that file (its folder is named
    # after the schema name), so don't list it again as having no file.
    unreadable_folders = {lc(p.rsplit("/", 2)[-2]) for p in ctx.env_unreadable_defs if p.count("/") >= 1}
    unmatched = [x for x in listed if lc(x) not in defs and lc(x) not in unreadable_folders]
    ctx.env_unmatched = unmatched
    if unmatched:
        notes.append("%d environment variable definition%s listed in solution.xml (type 380) had no definition "
                     "file this check recognises: %s. Check their values by hand."
                     % (len(unmatched), "" if len(unmatched) == 1 else "s", ", ".join(v(x) for x in unmatched[:10])))
    ctx.env = (defs, notes)
    return ctx.env


def _obj(x):
    return x if isinstance(x, dict) else {}


def flow_references(ctx, flow):
    """Connection references and environment variables a cloud flow's JSON uses, and how
    many names were skipped because they aren't text."""
    path = field(flow, "JsonFileName")
    if not path or not ctx.pkg.has(path):
        return None
    data = json.loads(ctx.pkg.read(path, limit=MAX_JSON_BYTES).decode("utf-8-sig"))
    props = _obj(_obj(data).get("properties"))
    conns, envs, skipped = set(), set(), 0
    for ref in _obj(props.get("connectionReferences")).values():
        name = _obj(_obj(ref).get("connection")).get("connectionReferenceLogicalName")
        if isinstance(name, str) and name.strip():
            conns.add(name)
        elif name is not None:
            skipped += 1
    for p in _obj(_obj(props.get("definition")).get("parameters")).values():
        name = _obj(_obj(p).get("metadata")).get("schemaName")
        if isinstance(name, str) and name.strip():
            envs.add(name)
        elif name is not None:
            skipped += 1
    return conns, envs, skipped


def check_import_checklist(ctx, rep):
    c = ctx.cust
    # Before import
    if ctx.managed == "0":
        rep.action("unmanaged-target", "before-import", "Unmanaged package: confirm the target is a development environment",
                   [], "Unmanaged solutions are for development; managed solutions are for every other environment. "
                   "An unmanaged import overwrites existing customizations to the same components, and that can't be "
                   "undone.", [LEARN["managed_unmanaged"], LEARN["import"]])
    elif ctx.managed == "1":
        rep.action("managed-target", "before-import", "Managed package: don't import it into the environment it was built in",
                   [], "A managed solution can't be imported into the environment that holds the originating unmanaged "
                   "solution. Its changes arrive already published.", [LEARN["managed_unmanaged"], LEARN["import"]])
    if rep.prerequisites:
        rep.action("install-prerequisites", "before-import",
                   "Confirm the target has the prerequisite solutions and apps at the versions listed",
                   ["%s (%d component%s)" % (v(g["solution"]), n, "" if n == 1 else "s")
                    for g, n in ((g, len(unique_required(g))) for g in rep.prerequisites)],
                   "Confirm the target has each solution at the version listed, or later. Install any that are missing "
                   "and update any that are older before importing. Learn: missing dependency errors also occur when "
                   "an app was upgraded in the source environment but not in the target, and it advises keeping "
                   "environments aligned to the same Dataverse and app versions.",
                   [LEARN["missing_deps"]])
    assemblies = kids(kid(c, "SolutionPluginAssemblies"), "PluginAssembly")
    if assemblies:
        rep.action("plugin-assembly-privilege", "before-import", "Import as a System Administrator",
                   [v(attr(a, "FullName").split(",")[0]) for a in assemblies],
                   "The package has plug-in assemblies. By default the System Customizer role has no create privilege "
                   "on the Plug-in Assembly table, so the import needs System Administrator or an equivalent grant.",
                   [LEARN["import"]])
    # During import
    refs = connection_references(ctx)
    for path, why in ctx.conn_ref_unreadable:
        rep.skipped("Connection references", "%s could not be read (%s); any connection reference it defines isn't "
                    "listed in the import checklist." % (v(path), v(why)))
    if refs or ctx.conn_ref_unreadable:
        rep.action("connection-reference-needs-connection", "during-import",
                   "Pick a connection for each connection reference",
                   ["%s (%s, connector %s)" % (v(r["name"]), v(r["display"]) if r["display"] else "no display name",
                                                  v(r["connector"]) if r["connector"] else "unknown")
                    for r in sorted(refs.values(), key=lambda x: lc(x["name"]))] +
                   ["%s (this check couldn't read the file: pick a connection for any connection reference it "
                    "defines too)" % v(path) for path, _why in ctx.conn_ref_unreadable],
                   "The import asks for a connection for each connection reference, or lets you create one. Flows "
                   "that were on when exported should turn on during the import when their connection references get "
                   "connections. For automated imports, supply the connections in a deployment settings file (pac "
                   "solution create-settings, then pac solution import --settings-file). The import validates that "
                   "the connections are owned by, or shared with, the connection reference owner.",
                   [LEARN["import"], LEARN["deployment_settings"], LEARN["pac_import"], LEARN["flow_state"]])
    defs, notes = environment_variables(ctx)
    for note in notes:
        rep.skipped("Environment variables", note)
    no_value = [d for d in defs.values() if not d["hasDefault"] and not d["hasCurrentValue"] and not d["valueUnknown"]]
    unknown = [d for d in defs.values() if not d["hasDefault"] and d["valueUnknown"]]
    unread = (["%s%s (its value file couldn't be read: check whether it has a value)"
               % (v(d["name"]), " (%s)" % v(d["display"]) if d["display"] else "")
               for d in sorted(unknown, key=lambda x: lc(x["name"]))] +
              ["%s (this check couldn't read the definition file: check this environment variable's value by hand)"
               % v(p) for p in ctx.env_unreadable_defs] +
              ["%s (listed in solution.xml, but no definition file this check recognises: check its value by hand)"
               % v(x) for x in ctx.env_unmatched])
    if no_value or unread:
        rep.action("env-var-without-value", "during-import", "Provide values for environment variables that have none",
                   ["%s%s" % (v(d["name"]), " (%s)" % v(d["display"]) if d["display"] else "")
                    for d in sorted(no_value, key=lambda x: lc(x["name"]))] + unread,
                   "These definitions ship with no default value and no current value. The import prompts for a value "
                   "only when neither the solution nor the target has one; supply it at import or in the deployment "
                   "settings file. Shipping definitions without values is what Microsoft advises, so this is expected."
                   + (" Items this check couldn't read are listed too, so check them by hand." if unread else ""),
                   [LEARN["env_vars"]])
    with_value = sorted(d["name"] for d in defs.values() if d["hasCurrentValue"])
    if with_value:
        rep.add("env-var-value-included", "info",
                "%d environment variable%s ship%s a current value" % (len(with_value), "" if len(with_value) == 1 else "s",
                                                                    "s" if len(with_value) == 1 else ""),
                "Current value present for: %s. Values are not shown." % ", ".join(v(x) for x in head(with_value, 15)),
                "Microsoft advises including the definition but not the value. A value shipped in a managed solution "
                "can only be removed by an upgrade that excludes it, and a current value overrides the default.",
                "If the value is environment-specific, remove it before export and supply it at import instead.",
                [LEARN["env_vars"]])
    steps = kids(kid(c, "SdkMessageProcessingSteps"), "SdkMessageProcessingStep")
    wfs = kids(kid(c, "Workflows"), "Workflow")
    flows = [w for w in wfs if field(w, "Category") == "5"]
    if steps or flows:
        rep.action("enable-steps-and-flows-option", "during-import",
                   "Import with plug-in steps and flows activated", [],
                   "In the Power Apps import wizard, 'Enable Plugin steps and flows included in the solution' is on by "
                   "default. With pac solution import it is off unless you pass --activate-plugins; Pipelines in Power "
                   "Platform activate by default. Without it, the import doesn't activate plug-in steps that arrive "
                   "inactive; clearing the wizard option doesn't deactivate flows.",
                   [LEARN["import"], LEARN["pac_import"], LEARN["import_options"]])
    # After import
    if ctx.managed == "0":
        rep.action("publish-after-unmanaged-import", "after-import", "Publish all customizations", [],
                   "An unmanaged import brings changes in as drafts. Publish them (pac solution import "
                   "--publish-changes, or Publish all) before they take effect.", [LEARN["import"], LEARN["pac_import"]])
    if steps:
        sync = sum(1 for s in steps if field(s, "Mode") == "0")
        asynchronous = sum(1 for s in steps if field(s, "Mode") == "1")
        images = sum(1 for s in steps if kids(kid(s, "SdkMessageProcessingStepImages"), "SdkMessageProcessingStepImage"))
        tables = sorted(set(field(s, "PrimaryEntity") for s in steps if field(s, "PrimaryEntity")))
        items = ["%d step%s: %d synchronous, %d asynchronous, %d with images; tables: %s"
                 % (len(steps), "" if len(steps) == 1 else "s", sync, asynchronous, images,
                    ", ".join(head([v(t) for t in tables], 12)) or "none named")]
        names = ["%s (stage %s, %s)" % (v(attr(s, "Name") or "(unnamed step)"), v(field(s, "Stage") or "?"),
                                        {"0": "sync", "1": "async"}.get(field(s, "Mode"), "mode ?"))
                 for s in steps]
        items += head(names, 10)
        rep.action("plugin-steps-inventory", "after-import", "Check the plug-in steps are enabled", items,
                   "If the import ran without activation (the wizard option cleared, or pac solution import without "
                   "--activate-plugins), steps that arrive inactive stay inactive.",
                   [LEARN["import"], LEARN["pac_import"]])
    if flows:
        items, unpacked_conn, unpacked_env = [], [], []
        flow_users = {}   # id(owned-missing-dependency finding) -> (finding, {flow name: True})
        for w in flows:
            flow_name = attr(w, "Name") or field(w, "Name") or "(unnamed flow)"
            state = field(w, "StateCode")
            label = {"0": "off when exported", "1": "on when exported",
                     "2": "suspended when exported"}.get(state, "state not recorded")
            if state == "2" and field(w, "StatusCode") == "3":
                label += ", status reason CompanyDLPViolation"
            items.append("%s (%s)" % (v(flow_name), label))
            try:
                found = flow_references(ctx, w)
            except DamagedEntry:
                continue    # reported once as package-entry-damaged
            except Exception as e:   # too large, not JSON, nested too deeply or an unexpected shape
                rep.skipped("Cloud flow references", "Flow %s: JSON could not be read (%s: %s)."
                            % (v(flow_name), e.__class__.__name__, v(e)))
                continue
            if not found:
                continue
            conns, envs, skipped = found
            if skipped:
                rep.skipped("Cloud flow references", "Flow %s: %d connection reference or environment variable "
                            "name%s in its JSON %s not text, so %s checked."
                            % (v(flow_name), skipped, "" if skipped == 1 else "s", "is" if skipped == 1 else "are",
                               "it wasn't" if skipped == 1 else "they weren't"))
            for kind, names, packaged in (("connection reference", conns, refs), ("environment variable", envs, defs)):
                for x in sorted(names):
                    if lc(x) in packaged or lc(x) in ctx.prerequisite_ids:
                        continue    # in the package, or a prerequisite another named solution provides
                    blocker = ctx.owned_missing.get(lc(x))
                    if blocker is not None:
                        # Already a blocker from solution.xml: say which flows use it, don't warn twice.
                        flow_users.setdefault(id(blocker), (blocker, {}))[1][flow_name] = True
                        continue
                    (unpacked_conn if kind == "connection reference" else unpacked_env).append((flow_name, x))
        rep.action("cloud-flows-present", "after-import", "Check each cloud flow is in the state you expect", items,
                   "The import attempts to restore each flow to its state at export; a flow that was on should turn "
                   "on when its connection references get connections. Importing an update doesn't change an existing "
                   "flow's state. If the importing user doesn't have permission to all of a flow's connections, the "
                   "connections need to be shared with them before the flow can be turned on.",
                   [LEARN["flow_state"], LEARN["workflow_table"]])
        for blocker, used_by in flow_users.values():
            # Only flows the evidence doesn't already name as dependents.
            extra = [v(n) for n in used_by if v(n) not in blocker["evidence"]]
            if extra:
                blocker["evidence"] += " Also used by cloud flow%s %s." % ("" if len(extra) == 1 else "s",
                                                                          "; ".join(head(extra, 8)))
        for flow_name, x in unpacked_conn:
            rep.add("flow-connection-reference-not-packaged", "warning",
                    "Flow %s uses connection reference %s, which isn't in the package" % (v(flow_name), v(x)),
                    "The flow JSON names connectionReferenceLogicalName %s; the package has no connection reference "
                    "with that name." % v(x),
                    "The target must already have this connection reference, or the flow can't get a connection. "
                    "Import fails when a required component is neither in the solution nor in the target.",
                    "Add the connection reference to this solution and export again, or confirm the target has it.",
                    [LEARN["connection_refs"], LEARN["missing_deps"]], component=x)
        for flow_name, x in unpacked_env:
            rep.add("flow-environment-variable-not-packaged", "warning",
                    "Flow %s uses environment variable %s, which isn't in the package" % (v(flow_name), v(x)),
                    "The flow JSON has a parameter with schemaName %s; the package has no definition for it." % v(x),
                    "The target must already have this environment variable definition.",
                    "Add the environment variable to this solution and export again, or confirm the target has it.",
                    [LEARN["env_vars"]], component=x)


# --------------------------------------------------------------------------- orchestration
CHECKS = [
    ("Package identity", check_identity),
    ("Missing dependencies", check_missing_dependencies),
    ("Table packaging behavior", check_owned_tables),
    ("Missing dependencies", report_packaged_missing),
    ("Code components on forms", check_code_components),
    ("PCF platform libraries", check_platform_libraries),
    ("Development builds", check_dev_bundles),
    ("Site map icons", check_sitemap),
    ("Package files", check_package_files),
    ("Import checklist", check_import_checklist),
    ("Package files", report_damaged_entries),
]


def merge_duplicates(ctx, rep):
    """An owned code component missing from the package is usually also listed as a
    type 66 missing dependency. Report it once, under the form check."""
    keep = []
    for f in rep.findings:
        key = lc(f.get("component"))
        if f["id"] == "owned-missing-dependency" and f.get("componentType") == "66" and key in ctx.unpackaged_controls:
            target = ctx.unpackaged_controls[key]
            note = " solution.xml also lists it under %s." % v("<MissingDependencies>")
            if note not in target["evidence"]:
                target["evidence"] += note
            continue
        keep.append(f)
    rep.findings = keep


def analyse(path):
    rep = Report(os.path.basename(path))
    try:
        pkg = open_package(path, rep)
        sol_root, manifest = load_solution(pkg, rep)
        if not pkg.has("customizations.xml"):
            ctx = Context(pkg, sol_root, manifest, ET.Element("ImportExportXml"))
            summarise(ctx, rep)
            raise PackageError("customizations-xml-missing", "customizations.xml is missing",
                               "solution.xml is present but customizations.xml is not, so the package can't be "
                               "imported and most checks can't run.", "Export the solution again.")
        cust = load_xml(pkg, "customizations.xml")
        if cust.tag != "ImportExportXml":
            # Like solution.xml, customizations.xml in an export has an <ImportExportXml> root. Anything
            # else would leave every check with nothing to read and a misleading "No blockers found".
            ctx = Context(pkg, sol_root, manifest, ET.Element("ImportExportXml"))
            summarise(ctx, rep)
            raise PackageError("not-a-solution", "customizations.xml is not a Dataverse customizations file",
                               "Root element is %s; an export's customizations.xml has %s."
                               % (v("<" + str(cust.tag) + ">"), v("<ImportExportXml>")),
                               "Export the solution again from Power Apps or with pac solution export, and check "
                               "the .zip that export produces without editing it.")
        ctx = Context(pkg, sol_root, manifest, cust)
        try:
            summarise(ctx, rep)
        except Exception as e:  # keep going: the summary is informational
            rep.skipped("Package summary", "%s: %s" % (e.__class__.__name__, v(e)))
        for name, fn in CHECKS:
            try:
                fn(ctx, rep)
            except DamagedEntry:
                pass    # the damaged entry is reported once, as package-entry-damaged
            except CheckSkipped as e:
                rep.skipped(name, str(e))
            except Exception as e:  # never crash on unexpected XML; say what wasn't checked
                rep.skipped(name, "%s: %s" % (e.__class__.__name__, v(e)))
        merge_duplicates(ctx, rep)
    except PackageError as e:
        rep.fatal = {"id": e.code, "title": e.title, "detail": e.detail, "fix": e.fix}
    return rep


# --------------------------------------------------------------------------- rendering
SEVERITY_ORDER = ["blocker", "warning", "info"]
WHEN_TITLES = [("before-import", "Before import"), ("during-import", "During import"), ("after-import", "After import")]


def to_json(rep):
    def clean(o):
        if isinstance(o, str):
            return plain(o)
        if isinstance(o, list):
            return [clean(x) for x in o]
        if isinstance(o, dict):
            return dict((k, clean(x)) for k, x in o.items()
                        if k not in ("component", "componentType", "versionBasis") or x)
        return o
    code = rep.exit_code()
    out = {
        "tool": TOOL, "toolVersion": TOOL_VERSION, "input": rep.input_name,
        "result": {0: "no-blockers", 1: "blockers", 2: "not-checked"}[code], "exitCode": code,
        "counts": {"blocker": rep.count("blocker"), "warning": rep.count("warning"), "info": rep.count("info"),
                   "prerequisiteSolutions": len(rep.prerequisites), "checklistItems": len(rep.checklist),
                   "notChecked": len(rep.not_checked)},
        "fatal": rep.fatal, "package": rep.package,
        "findings": sorted(rep.findings, key=lambda f: SEVERITY_ORDER.index(f["severity"])),
        "prerequisites": rep.prerequisites, "checklist": rep.checklist, "notChecked": rep.not_checked,
        "versionSensitive": {"platformLibraries": {k: PLATFORM_LIBRARIES[k] for k in ("checked", "source", "allowed")},
                             "pacForVirtualControls": PAC_FOR_VIRTUAL_CONTROLS, "importSizeLimit": IMPORT_SIZE_LIMIT,
                             "vectorIcon": {"source": MODEL_APPS_PLUGIN, "basis": MODEL_APPS_PLUGIN_BASIS}},
    }
    return json.dumps(clean(out), indent=2, ensure_ascii=False) + "\n"


def to_markdown(rep):
    L = []
    p = rep.package
    title = p.get("uniqueName") or rep.input_name
    L.append("# Solution release check: %s %s" % (md(v(title)), md(v(p["version"])) if p.get("version") else ""))
    L.append("")
    if rep.fatal:
        L.append("**Not checked: %s.**" % md(rep.fatal["title"]))
        L.append("")
        L.append("- **File:** %s" % md(v(rep.input_name)))
        L.append("- **Why:** %s" % md(rep.fatal["detail"]))
        if rep.fatal.get("fix"):
            L.append("- **What to do:** %s" % md(rep.fatal["fix"]))
        L.append("")
        if not p.get("uniqueName"):
            return "\n".join(L).rstrip() + "\n"
    else:
        b, w = rep.count("blocker"), rep.count("warning")
        if b:
            L.append("**Not ready: %d blocker%s.** Fix %s and export again before importing." %
                     (b, "" if b == 1 else "s", "it" if b == 1 else "them"))
        else:
            L.append("**No blockers found.**")
        L.append("")
        L.append("%d warning%s, %d prerequisite solution%s to confirm, %d checklist item%s, %d not checked. "
                 "This is a static, offline check of the zip: it can't see the target environment, so it can't "
                 "promise the import will succeed." %
                 (w, "" if w == 1 else "s", len(rep.prerequisites), "" if len(rep.prerequisites) == 1 else "s",
                  len(rep.checklist), "" if len(rep.checklist) == 1 else "s", len(rep.not_checked)))
        L.append("")
    # Package
    L.append("## Package")
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    pub = p.get("publisher", {})
    f = p.get("file", {})
    rows = [
        ("Solution", "%s%s" % (md(v(p.get("uniqueName", "")), True),
                               " (%s)" % md(v(p["displayName"]), True) if p.get("displayName") and p.get("displayName") != p.get("uniqueName") else "")),
        ("Version", md(v(p.get("version", "")), True)),
        ("Package type", md(p.get("packageType", ""), True)),
        ("Publisher", "%s, prefix %s, option value prefix %s" % (md(v(pub.get("uniqueName", "")), True),
                                                                 md(v(pub.get("customizationPrefix", "")), True),
                                                                 md(v(pub.get("optionValuePrefix", "")), True))),
        ("`<ImportExportXml>` version", md(v(p.get("importExportXmlVersion", "")), True)),
        ("File", "%s, %s, %d entries" % (md(v(f.get("name", rep.input_name)), True), fmt_size(f.get("bytes", 0)),
                                         f.get("entries", 0))),
    ]
    for k, val in rows:
        L.append("| %s | %s |" % (k, val))
    L.append("")
    if p.get("contents"):
        L.append("Contents: " + ", ".join("%s %d" % (c["item"], c["count"]) for c in p["contents"]) + ".")
        L.append("")
    if p.get("rootComponents"):
        L.append("Root components in solution.xml by type and behavior (0 %s, 1 %s, 2 %s):" %
                 (BEHAVIOR_LABELS["0"], BEHAVIOR_LABELS["1"], BEHAVIOR_LABELS["2"]))
        L.append("")
        L.append("| Type | Component | 0 | 1 | 2 | Other |")
        L.append("|---|---|---|---|---|---|")
        for r in p["rootComponents"]:
            L.append("| %s | %s | %s | %s | %s | %s |" % (md(v(r["type"]), True), md(r["label"], True),
                                                        r["0"] or "", r["1"] or "", r["2"] or "", r["other"] or ""))
        L.append("")
    if rep.fatal:
        return "\n".join(L).rstrip() + "\n"
    # Findings
    n = 0
    for sev, heading in (("blocker", "Blockers"), ("warning", "Warnings"), ("info", "For information")):
        items = [x for x in rep.findings if x["severity"] == sev]
        if not items and sev == "info":
            continue
        L.append("## %s" % heading)
        L.append("")
        if not items:
            L.append("None found.")
            L.append("")
            continue
        for x in items[:50]:
            n += 1
            L.append("### %d. %s" % (n, md(x["title"])))
            L.append("")
            L.append("- **Evidence:** %s" % md(x["evidence"]))
            L.append("- **Why it matters:** %s" % md(x["why"]))
            L.append("- **Fix:** %s" % md(x["fix"]))
            if x["sources"]:
                L.append("- **Source:** %s" % " ; ".join("<%s>" % s for s in x["sources"]))
            if x["versionSensitive"]:
                L.append("- **Version-sensitive:** based on %s; re-check the source." % x["versionBasis"])
            L.append("")
        if len(items) > 50:
            L.append("%d more %s findings are in the --json output." % (len(items) - 50, sev))
            L.append("")
    # Prerequisites
    L.append("## Prerequisites in the target environment")
    L.append("")
    if rep.prerequisites:
        L.append("solution.xml lists these components from other solutions as missing dependencies. The import fails "
                 "only if the target doesn't have them either, for example because a solution is missing or older "
                 "than the version shown. Source: <%s>" % LEARN["missing_deps"])
        L.append("")
        L.append("| Solution named in the package | Installed with | Components needed |")
        L.append("|---|---|---|")
        for g in rep.prerequisites:
            comps = head(unique_required(g), 6)
            sol = md(v(g["solution"]), True) + (" (same publisher prefix)" if g["samePublisher"] else "")
            L.append("| %s | %s | %s |" % (sol, md(v(g["package"]), True) if g["package"] else "",
                                           md("; ".join(comps), True)))
        L.append("")
    else:
        L.append("None listed.")
        L.append("")
    # Checklist
    L.append("## Import checklist")
    L.append("")
    for when, heading in WHEN_TITLES:
        items = [a for a in rep.checklist if a["when"] == when]
        if not items:
            continue
        L.append("### %s" % heading)
        L.append("")
        for a in items:
            L.append("- [ ] **%s.** %s%s" % (md(a["title"]), md(a["why"]),
                                            (" Source: " + " ; ".join("<%s>" % s for s in a["sources"])) if a["sources"] else ""))
            for it in head(a["items"]):
                L.append("  - %s" % md(it))
        L.append("")
    # Not checked
    L.append("## Not checked")
    L.append("")
    if rep.not_checked:
        for x in rep.not_checked:
            L.append("- **%s:** %s" % (x["check"], md(x["reason"])))
    else:
        L.append("Every check ran.")
    L.append("")
    L.append("## Scope")
    L.append("")
    L.append("- Static, offline check of the zip. It can't see the target environment (installed solutions, existing "
             "tables, data, licences), so \"no blockers\" doesn't mean the import will succeed.")
    L.append("- It doesn't replace Solution checker, the online Power Apps checker service that analyses plug-in and "
             "web resource code, flows and more. A Solution checker pass doesn't guarantee import success either. "
             "Source: <%s>" % LEARN["checker"])
    L.append("- Version-sensitive values: the PCF platform library versions, the %s import limit and the Power "
             "Platform CLI %s rebuild advice (Microsoft Learn, checked %s), and the VectorIcon guidance (Microsoft's "
             "model-apps plugin, %s, not Learn)." % (IMPORT_SIZE_LIMIT["label"], PAC_FOR_VIRTUAL_CONTROLS["minimum"],
                                                     LEARN_CHECKED, MODEL_APPS_PLUGIN_BASIS))
    L.append("")
    L.append("_%s %s_" % (TOOL, TOOL_VERSION))
    return "\n".join(L).rstrip() + "\n"


# --------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Offline release check for an exported Dataverse solution .zip. Exit codes: 0 no "
                    "blockers, 1 blockers found, 2 not a solution export, unreadable, or a usage error.")
    ap.add_argument("zip", help="path to the exported solution .zip")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown", help="report format (default markdown)")
    ap.add_argument("--json", action="store_true", help="shortcut for --format json")
    ap.add_argument("--output", help="write the report to this new file instead of standard output")
    args = ap.parse_args(argv)
    fmt = "json" if args.json else args.format

    def internal_error(e):
        r = Report(os.path.basename(args.zip))
        r.fatal = {"id": "internal-error", "title": "The checker hit an unexpected error",
                   "detail": "%s: %s" % (e.__class__.__name__, v(e)), "fix": "Report the error with the file's shape "
                   "(not its contents)."}
        return r

    try:
        rep = analyse(args.zip)
    except Exception as e:  # last resort: still produce a report
        rep = internal_error(e)
    try:
        out = to_json(rep) if fmt == "json" else to_markdown(rep)
    except Exception as e:
        rep = internal_error(e)
        out = to_json(rep) if fmt == "json" else to_markdown(rep)
    if args.output:
        target = os.path.abspath(args.output)
        # Encode first, so a name that can't be encoded (for example a non-UTF-8 file name on
        # Linux) is replaced rather than failing halfway through the write.
        data = out.encode("utf-8", errors="replace")
        try:
            # Mode "x" creates the file and fails if it already exists, in one step.
            fh = open(target, "xb")
        except FileExistsError:
            print("Refusing to overwrite %s; choose a new file name." % args.output, file=sys.stderr)
            return 2
        except (OSError, ValueError) as e:
            print("Can't write %s (%s: %s); choose a folder you can write to."
                  % (args.output, e.__class__.__name__, getattr(e, "strerror", None) or e), file=sys.stderr)
            return 2
        try:
            with fh:
                fh.write(data)
        except Exception as e:
            try:
                os.remove(target)   # don't leave a partial report behind
            except OSError:
                pass
            print("Can't write %s (%s: %s); choose a folder you can write to."
                  % (args.output, e.__class__.__name__, getattr(e, "strerror", None) or e), file=sys.stderr)
            return 2
        print("Report written to %s (exit code %d)." % (args.output, rep.exit_code()), file=sys.stderr)
    else:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
        sys.stdout.write(out)
    return rep.exit_code()


if __name__ == "__main__":
    sys.exit(main())
