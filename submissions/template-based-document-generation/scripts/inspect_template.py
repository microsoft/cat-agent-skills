"""Inspector: template bytes + policy + profile -> Manifest.

Read-only. Inventories every paragraph in the parts in scope, emits *candidates* (text that looks like a
field, an author instruction, an empty cell, or a content control) from the profile's patterns, and
records policy findings. It decides nothing: whether a candidate is a field, literal text or an
instruction to act on is the plan's job.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import unicodedata
from typing import Any
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import models as m  # noqa: E402
import namespace_validation as nv  # noqa: E402
import ooxml_common as oc  # noqa: E402

SIGNATURE_REL = "http://schemas.openxmlformats.org/package/2006/relationships/digital-signature/origin"
CT_SIGNATURE_ORIGIN = "application/vnd.openxmlformats-package.digital-signature-origin"
CT_VBA = "application/vnd.ms-office.vbaProject"
COMMENT_PARTS = ("word/comments.xml", "word/commentsExtended.xml", "word/commentsIds.xml", "word/commentsExtensible.xml")
REVISION_TAGS = {oc.w(x) for x in ("ins", "del", "moveFrom", "moveTo", "rPrChange", "pPrChange", "tblPrChange", "trPrChange", "tcPrChange", "sectPrChange", "numberingChange")}
EMBED_TAGS = {oc.w("object"), oc.w("control"), "{urn:schemas-microsoft-com:office:office}OLEObject"}
SDT, SDT_PR, SDT_CONTENT, TBL, TR, TC = (oc.w(x) for x in ("sdt", "sdtPr", "sdtContent", "tbl", "tr", "tc"))
SDT_TYPE_LOCALS = ("text", "richText", "date", "dropDownList", "comboBox", "picture", "group", "citation", "docPartObj",
                   "docPartList", "equation", "bibliography", "checkbox", "repeatingSection", "repeatingSectionItem", "entityPicker")
TEXT_CONTROL_TYPES = ("text", "richText")
CONTEXT_CHARS = 40


class Findings:
    """Collects policy findings: one per code, first evidence wins the `part`, details accumulate."""

    def __init__(self, policy: dict[str, Any]):
        self.constructs: dict[str, Any] = policy.get("constructs", {})
        self.items: dict[str, m.Finding] = {}

    def severity(self, code: str, default: str = "report") -> str:
        sev = self.constructs.get(code, default)
        return sev if sev in m.FINDING_SEVERITIES else default

    def add(self, code: str, part: str | None, detail: str, severity: str | None = None) -> None:
        sev = severity or self.severity(code)
        if sev == "allow":
            return
        if code in self.items:
            f = self.items[code]
            if detail and detail not in f.detail:
                f.detail = (f.detail + "; " + detail)[:400]
            return
        self.items[code] = m.Finding(code=code, severity=sev, part=part, detail=detail[:400])

    def external_relationship(self, rel_type: str, part: str, target: str) -> None:
        table = self.constructs.get("external_relationships", {})
        sev = table.get(rel_type, table.get("*", "report"))
        if sev == "allow":
            return
        short = rel_type.rsplit("/", 1)[-1]
        self.add("external_relationships", part, f"{short} -> {target[:120]}", severity=sev)

    def blocking(self) -> bool:
        return any(f.severity == "block" for f in self.items.values())

    def as_list(self) -> list[m.Finding]:
        return list(self.items.values())


# Latin letters that NFKD does not decompose, so an accent-stripping fold alone loses them.
LATIN_FOLD = {"ß": "ss", "æ": "ae", "œ": "oe", "ø": "o", "đ": "d",
              "ł": "l", "þ": "th", "ð": "d", "ı": "i"}


def slug(label: str) -> str | None:
    """A field name from a placeholder label: 'Client Name' -> client_name.

    A field name must be an ASCII identifier, but a label need not be Latin at all. When folding leaves
    nothing usable - Chinese, Japanese, Korean, Arabic, Cyrillic, Greek - the name is derived from the
    label's own characters instead of being abandoned. That keeps two properties that matter: distinct
    labels get distinct names, so nothing is silently merged, and one label always yields the same name,
    so a genuinely repeated placeholder still shares a single field. The readable original stays in the
    candidate's `label`, which is what a reader maps from.
    """
    folded = "".join(LATIN_FOLD.get(ch, ch) for ch in label.lower())
    folded = unicodedata.normalize("NFKD", folded)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    s = re.sub(r"_+", "_", s)[:64].strip("_")
    if s:
        return ("f_" + s if s[0].isdigit() else s)[:64]
    stripped = label.strip()
    # Only a label that carries letters or digits in *some* script earns a derived name. Punctuation and
    # a row of underscores name nothing, so they stay nameless rather than gaining an opaque one.
    if not any(ch.isalnum() for ch in stripped):
        return None
    return "f_" + hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:8]


def sanitize_name(name: str) -> str:
    base = os.path.basename(name.replace("\\", "/")) or "template.docx"
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:120]


def _content_types(pkg: oc.Package, limits: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    root = oc.parse_xml(pkg.parts["[Content_Types].xml"], limits, "[Content_Types].xml")
    defaults, overrides = {}, {}
    for el in root:
        if el.tag == f"{{{oc.CT_NS}}}Default":
            defaults[el.get("Extension", "").lower()] = el.get("ContentType", "")
        elif el.tag == f"{{{oc.CT_NS}}}Override":
            overrides[el.get("PartName", "")] = el.get("ContentType", "")
    return defaults, overrides


def _scan_relationships(pkg: oc.Package, limits: dict[str, Any], findings: Findings) -> None:
    for name, data in pkg.parts.items():
        if not name.endswith(".rels"):
            continue
        root = oc.parse_xml(data, limits, name)
        for rel in root:
            rel_type = rel.get("Type", "")
            target = rel.get("Target", "")
            if rel_type == SIGNATURE_REL:
                findings.add("digital_signatures", target.lstrip("/") or name, f"relationship in {name}")
            if rel.get("TargetMode", "").lower() == "external":
                findings.external_relationship(rel_type, name, target)


def _scan_package(pkg: oc.Package, limits: dict[str, Any], findings: Findings, notes: list[str]) -> None:
    defaults, overrides = _content_types(pkg, limits)
    for name in pkg.names():
        if name.startswith("_xmlsignatures/"):
            findings.add("digital_signatures", name, "signature part present")
        if name.startswith("word/embeddings/"):
            findings.add("embedded_objects", name, "embedded object part")
        if name == "word/vbaProject.bin":
            findings.add("macros", name, "VBA project part")
        if name in COMMENT_PARTS:
            findings.add("comments", name, "comments part present")
        if name == "docMetadata/LabelInfo.xml":
            notes.append("sensitivity label metadata present; preserved byte-for-byte")
        if name == "docProps/custom.xml":
            notes.append("custom document properties present; preserved byte-for-byte")
    for ext, ct in defaults.items():
        if ct == CT_SIGNATURE_ORIGIN:
            findings.add("digital_signatures", "[Content_Types].xml", f"content type default for .{ext}")
    for part, ct in overrides.items():
        if ct == CT_VBA:
            findings.add("macros", part.lstrip("/"), "VBA content type")
        if "oleObject" in ct or "activex" in ct.lower():
            findings.add("embedded_objects", part.lstrip("/"), ct)


def _sdt_info(sdt: ET.Element) -> dict[str, str]:
    info = {"tag": "", "alias": "", "type": "text", "data_bound": "false", "placeholder": "false"}
    pr = sdt.find(SDT_PR)
    if pr is None:
        return info
    for child in pr:
        local = child.tag.split("}")[-1]
        if local == "tag":
            info["tag"] = child.get(oc.w("val"), "")
        elif local == "alias":
            info["alias"] = child.get(oc.w("val"), "")
        elif local == "dataBinding":
            info["data_bound"] = "true"
        elif local == "showingPlcHdr":
            info["placeholder"] = "true"
        elif local in SDT_TYPE_LOCALS:
            info["type"] = local
    return info


def _compile_patterns(profile: dict[str, Any], key: str) -> list[tuple[str, re.Pattern, str]]:
    out = []
    for p in profile.get(key, []):
        out.append((p["name"], re.compile(p["regex"]), p.get("confidence", "medium")))
    return out


class _Match:
    __slots__ = ("kind", "pattern", "confidence", "start", "end", "text", "label", "control", "order")

    def __init__(self, kind: str, pattern: str, confidence: str, start: int, end: int, text: str, label: str, order: int, control: dict[str, str] | None = None):
        self.kind, self.pattern, self.confidence = kind, pattern, confidence
        self.start, self.end, self.text, self.label, self.order, self.control = start, end, text, label, order, control

    def overlaps(self, other: "_Match") -> bool:
        return self.start < other.end and other.start < self.end and not (self.start == self.end == other.start)


def _accept_non_overlapping(matches: list[_Match], taken: list[_Match]) -> list[_Match]:
    """Greedy by (pattern order, position): earlier patterns win where matches overlap."""
    accepted: list[_Match] = []
    for mt in sorted(matches, key=lambda x: (x.order, x.start, -(x.end - x.start))):
        if any(mt.overlaps(a) for a in taken) or any(mt.overlaps(a) for a in accepted):
            continue
        accepted.append(mt)
    return accepted


def inspect(template: bytes, policy: dict[str, Any], policy_sha256: str, profile: dict[str, Any], job_id: str, source_name: str) -> m.Manifest:
    """Inspect a template. Raises PackageError only when the bytes cannot be read as a package at
    all; every other problem becomes a finding or a note in the manifest."""
    limits = policy.get("limits", {})
    pkg = oc.read_package(template, limits)
    scope = profile.get("parts_in_scope", [])
    findings = Findings(policy)
    notes: list[str] = []
    max_candidates = int(limits.get("max_candidates", 5000))
    max_paragraphs = int(limits.get("max_paragraphs", 200000))
    max_text = int(limits.get("max_paragraph_text_chars", 300))
    max_ctext = int(limits.get("max_candidate_text_chars", 200))
    field_patterns = _compile_patterns(profile, "field_patterns")
    instruction_patterns = _compile_patterns(profile, "instruction_patterns")
    fmt_conf = profile.get("instruction_formatting", {}) or {}
    blank_conf = profile.get("blank_cells", "low")

    _scan_package(pkg, limits, findings, notes)
    _scan_relationships(pkg, limits, findings)
    scanned = [n for n in pkg.names() if n.endswith(".rels") or n == "[Content_Types].xml"]
    parts_digest = [m.PartDigest(name=n, sha256=m.sha256_bytes(pkg.parts[n]), size_bytes=len(pkg.parts[n]), in_scope=oc.in_scope(n, scope)) for n in pkg.names()]

    paragraphs: list[m.ParagraphInfo] = []
    rows: list[m.RowInfo] = []
    candidates: list[m.Candidate] = []
    candidate_total = 0
    controls_seen = 0

    word_xml = [n for n in pkg.names() if n.startswith("word/") and n.endswith(".xml") and not n.endswith(".rels")]
    for name in word_xml:
        scoped = oc.in_scope(name, scope)
        try:
            tree = nv.parse_namespaces(pkg.parts[name], limits)
        except nv.NamespaceError:
            findings.add("unreadable_part", name, "XML part is not well-formed, uses forbidden declarations, or has invalid namespace references", severity="block")
            continue
        root = tree.root
        scanned.append(name)
        has_fields = False
        for el in root.iter():
            tag = el.tag
            if tag in REVISION_TAGS:
                findings.add("tracked_changes", name, f"{tag.split('}')[1]} element")
            elif tag in (oc.w("commentRangeStart"), oc.w("commentReference")):
                findings.add("comments", name, "comment markers in body")
            elif tag in EMBED_TAGS:
                findings.add("embedded_objects", name, tag.split("}")[1])
            elif tag in (oc.w("fldSimple"), oc.w("fldChar")):
                has_fields = True
        if has_fields:
            findings.add("field_codes_present", name, "field codes present (their text is not fillable)")
        if not scoped:
            if any(rx.search(oc.paragraph_text(p)) for p in oc.paragraphs(root) for _, rx, _ in field_patterns):
                findings.add("candidates_outside_scope", name, "field-like text in a part the profile does not put in scope", severity="report")
            continue

        parents = oc.parent_map(root)
        field_state = oc.field_state_by_run(root)
        plist = oc.paragraphs(root)
        if len(paragraphs) + len(plist) > max_paragraphs:
            findings.add("too_many_paragraphs", name, f"more than {max_paragraphs} paragraphs", severity="block")
            continue
        # The filler edits bytes while eligibility is decided on the parsed tree. If the two views of a
        # part disagree - a non-UTF-8 encoding, several aliases for the WordprocessingML namespace - then
        # nothing downstream can be trusted, so the part is refused here rather than at apply time.
        try:
            raw_view = oc.RawPart(pkg.parts[name], name)
            raw_texts = [raw_view.text(rp) for rp in raw_view.paragraphs]
        except (oc.PackageError, UnicodeError) as exc:
            findings.add("unsupported_part_markup", name, str(exc)[:200], severity="block")
            continue
        if raw_texts != [oc.paragraph_text(x) for x in plist]:
            findings.add("unsupported_part_markup", name, "the byte-level and parsed views of this part disagree; "
                         "it uses markup the filler cannot edit safely", severity="block")
            continue
        pidx = {id(p): i for i, p in enumerate(plist)}
        ordinals: dict[int, str] = {}
        counters: dict[str, int] = {}
        for el in root.iter():
            if el.tag in oc.REAL_CONTAINERS or el.tag in (TBL, TR):
                local = el.tag.split("}")[1]
                counters[local] = counters.get(local, 0) + 1
                ordinals[id(el)] = f"{local}{counters[local] - 1}"

        def subtree_range(el: ET.Element) -> tuple[int, int]:
            idxs = [pidx[id(x)] for x in el.iter(oc.P)]
            return (min(idxs), max(idxs)) if idxs else (-1, -1)

        # rows: identity, extent and count within their own table
        row_id_of: dict[int, str] = {}
        for tbl in root.iter(TBL):
            own_rows = [tr for tr in tbl.iter(TR) if _nearest(tr, parents, TBL) is tbl]
            for r_ord, tr in enumerate(own_rows):
                first, last = subtree_range(tr)
                rid = f"{name}#{ordinals[id(tbl)]}/tr{r_ord}"
                row_id_of[id(tr)] = rid
                rows.append(m.RowInfo(id=rid, part=name, first_index=first, last_index=last, row_ordinal=r_ord, row_count=len(own_rows), table_id=f"{name}#{ordinals[id(tbl)]}"))

        block_cache: dict[int, tuple[int, int]] = {}
        for pi, p in enumerate(plist):
            tokens = oc.paragraph_tokens(p)
            text = "".join(t.text for t in tokens)
            container_el, block = oc.real_container(p, parents)
            if id(block) not in block_cache:
                block_cache[id(block)] = subtree_range(block) if block is not p else (pi, subtree_range(p)[1])
            b_first, b_last = block_cache[id(block)]
            if container_el is None:
                c_kind, c_id = "other", f"{name}#root"
            else:
                c_kind, c_id = oc.CONTAINER_KIND.get(container_el.tag, "other"), f"{name}#{ordinals.get(id(container_el), 'x')}"
            ppr = p.find(oc.w("pPr"))
            style = None
            flags: list[str] = []
            if ppr is not None:
                ps = ppr.find(oc.w("pStyle"))
                style = ps.get(oc.w("val")) if ps is not None else None
                if ppr.find(oc.w("sectPr")) is not None:
                    flags.append("section_break")
            p_mark_revised = any(c.tag in (oc.w("ins"), oc.w("del")) for rpr in p.findall(f"{oc.w('pPr')}/{oc.w('rPr')}") for c in rpr)
            chain = oc.ancestors(p, parents)
            if p_mark_revised or any(a.tag in REVISION_TAGS for a in chain) or any(el.tag in REVISION_TAGS for el in p.iter()):
                flags.append("tracked_change")
            if any(el.tag in (oc.w("fldChar"), oc.w("fldSimple")) for el in p.iter()):
                flags.append("field_code")
            if any(el.tag == oc.w("bookmarkStart") for el in p.iter()):
                flags.append("bookmark")
            if any(el.tag in (oc.w("commentRangeStart"), oc.w("commentRangeEnd"), oc.w("commentReference")) for el in p.iter()):
                flags.append("comment_marker")
            if any(el.tag in (oc.w("drawing"), oc.w("pict")) for el in p.iter()):
                flags.append("drawing")
            if any(a.tag == SDT for a in chain):
                flags.append("in_control")
            if not text:
                flags.append("empty")
            text_runs = [t.run for t in tokens if t.kind == "t" and t.run is not None and t.text.strip()]
            if text_runs and all(oc.run_is_hidden(r) for r in text_runs):
                flags.append("hidden")
            if text_runs and all(oc.run_is_highlighted(r) for r in text_runs):
                flags.append("highlighted")
            row_el = _nearest(p, parents, TR)
            paragraphs.append(m.ParagraphInfo(
                id=f"{name}#p{pi}", part=name, index=pi, text_sha256=oc.text_sha256(text), text=text[:max_text],
                truncated=len(text) > max_text, break_count=sum(1 for t in tokens if t.kind == "br"),
                style=style, container=c_kind, container_id=c_id,
                block_first=b_first, block_last=b_last, row_id=row_id_of.get(id(row_el)) if row_el is not None else None, flags=flags,
            ))

            # ---- candidates -------------------------------------------------------------------------
            instr: list[_Match] = []
            for order, (pname, rx, conf) in enumerate(instruction_patterns):
                for mt in rx.finditer(text):
                    if mt.end() > mt.start():
                        instr.append(_Match("instruction", pname, conf, mt.start(), mt.end(), mt.group(0), mt.group(0), order))
            for kind_flag, key in (("hidden", "hidden_text"), ("highlighted", "highlighted_text")):
                conf = fmt_conf.get(key)
                if conf not in m.CONFIDENCES:
                    continue
                check = oc.run_is_hidden if kind_flag == "hidden" else oc.run_is_highlighted
                start = None
                for t in tokens + [None]:
                    on = t is not None and t.kind == "t" and t.run is not None and check(t.run)
                    if on and start is None:
                        start = t.start
                    elif not on and start is not None:
                        end = t.start if t is not None else len(text)
                        if text[start:end].strip():
                            instr.append(_Match("instruction", key, conf, start, end, text[start:end], text[start:end], 1000))
                        start = None
            fields: list[_Match] = []
            for order, (pname, rx, conf) in enumerate(field_patterns):
                for mt in rx.finditer(text):
                    if mt.end() > mt.start():
                        # An alternation leaves the groups it did not take unmatched, so take the first
                        # that actually matched: `(NAME)|(____)` must not hand None to the label.
                        label = next((g for g in (mt.groups() or ()) if g is not None), mt.group(0))
                        fields.append(_Match("field", pname, conf, mt.start(), mt.end(), mt.group(0), label.strip(), order))
            accepted_instr = _accept_non_overlapping(instr, [])
            accepted_fields = _accept_non_overlapping(fields, accepted_instr)
            controls: list[_Match] = []
            inner_sdts = [el for el in p.iter(SDT) if _nearest(el, parents, oc.P) is p]
            for sdt in inner_sdts:
                info = _sdt_info(sdt)
                owned = [t for t in tokens if sdt in oc.ancestors(t.element, parents)]
                if not owned:
                    continue
                s, e = min(t.start for t in owned), max(t.end for t in owned)
                controls.append(_Match("control", "content_control", "high", s, e, text[s:e], info["alias"] or info["tag"] or text[s:e], 0, info))
            block_sdt = next((a for a in chain if a.tag == SDT), None)
            if block_sdt is not None and not inner_sdts:
                info = _sdt_info(block_sdt)
                controls.append(_Match("control", "content_control", "high", 0, len(text), text, info["alias"] or info["tag"] or text, 0, info))
            blanks: list[_Match] = []
            if not text and c_kind == "cell" and not controls and blank_conf in m.CONFIDENCES:
                blanks.append(_Match("blank", "empty_cell", blank_conf, 0, 0, "", "", 0))

            for mt in accepted_instr + accepted_fields + controls + blanks:
                candidate_total += 1
                if len(candidates) >= max_candidates:
                    continue
                reason: str | None = None
                owners = [t for t in tokens if t.start < mt.end and t.end > mt.start]
                if mt.start == mt.end:
                    if tokens:
                        reason = "empty span inside a paragraph that has text"
                elif any(t.kind != "t" for t in owners):
                    reason = "span covers a tab or break"
                elif any(t.run is None for t in owners):
                    reason = "text outside a run"
                if reason is None:
                    # A span with no tokens still sits somewhere: an empty cell inside a tracked insertion
                    # is no more fillable than text inside one, so the paragraph stands in for the anchor.
                    for el in ([t.element for t in owners] or [p]):
                        achain = oc.ancestors(el, parents)
                        denied = [a.tag.split("}")[1] for a in achain if a.tag in oc.DENIED_ANCESTORS]
                        if denied:
                            reason = f"inside w:{denied[0]}"
                            break
                    for t in owners:
                        if field_state.get(t.run, False):
                            reason = reason or "inside a complex field"
                            break
                        if t.run is not None and any(tree.declarations.get(child) for child in t.run if child.tag in (oc.T, oc.TAB, oc.BR, oc.CR)):
                            reason = reason or "namespace declaration on a text element"     # the run is rebuilt
                            break
                    if reason is None and p_mark_revised:
                        reason = "tracked paragraph mark"
                # The enclosing content control decides fillability for every candidate kind, not just for
                # the control candidate itself: a field inside a date picker or a bound control is no more
                # fillable than the control is, and filling one inside a placeholder-showing control must
                # also clear that placeholder state.
                if mt.kind == "control" and mt.control is not None:
                    controls_seen += 1
                    control_info: dict[str, str] | None = mt.control
                    if mt.control["type"] not in TEXT_CONTROL_TYPES:
                        reason = reason or f"control type {mt.control['type']} is not fillable as text"
                    if mt.control["data_bound"] == "true":
                        reason = reason or "data-bound content control"
                    # A control is no more fillable than the controls it sits inside. Word repopulates a
                    # bound control from its custom XML part on open, so anything written into a control
                    # nested under one is discarded without a word. Only the binding is inherited this
                    # way: a text control legitimately nests inside a repeatingSection or a group.
                    anchor_el = owners[0].element if owners else p
                    if any(_sdt_info(a)["data_bound"] == "true" for a in oc.ancestors(anchor_el, parents) if a.tag == SDT):
                        reason = reason or "inside a data-bound content control"
                else:
                    # Every token the span covers, and the whole control ancestry above each: a rich-text
                    # control nested in a data-bound one is still bound, and a span running from ordinary
                    # text into a date picker would rewrite that picker. One protected control anywhere
                    # under the span makes the whole replacement ineligible.
                    enclosing: list[dict[str, str]] = []
                    for el in ([t.element for t in owners] or [p]):
                        enclosing += [_sdt_info(a) for a in oc.ancestors(el, parents) if a.tag == SDT]
                    control_info: dict[str, str] | None = enclosing[0] if enclosing else None
                    for info in enclosing:
                        if info["data_bound"] == "true":
                            reason = reason or "inside a data-bound content control"
                            break
                        if info["type"] not in TEXT_CONTROL_TYPES:
                            reason = reason or f"inside a {info['type']} content control, which does not hold free text"
                            break
                mixed = len({oc.rpr_signature(t.run) for t in owners}) > 1
                overlapped_by_field = mt.kind == "control" and any(f.overlaps(mt) for f in accepted_fields)
                required = reason is None and mt.confidence in ("high", "medium") and mt.kind != "blank" and not overlapped_by_field
                if mt.kind == "control" and mt.control is not None:
                    guess = slug(mt.control["tag"] or mt.control["alias"] or "") or f"control_{controls_seen}"
                elif mt.kind == "field":
                    guess = slug(mt.label)
                else:
                    guess = None
                candidates.append(m.Candidate(
                    id=f"{mt.kind[0]}:{name}#p{pi}#{mt.start}-{mt.end}", kind=mt.kind, part=name, paragraph_index=pi,
                    char_start=mt.start, char_end=mt.end, text=mt.text[:max_ctext], label=mt.label[:max_ctext], name_guess=guess,
                    pattern=mt.pattern, confidence="low" if overlapped_by_field else mt.confidence, decision_required=required,
                    eligible=reason is None, ineligibility_reason=reason, mixed_formatting=mixed,
                    context_before=text[max(0, mt.start - CONTEXT_CHARS):mt.start], context_after=text[mt.end:mt.end + CONTEXT_CHARS],
                    control=control_info,
                ))

    notes += disambiguate_by_preceding_label(candidates, paragraphs)
    for detail in unrecognised_repeated_text(candidates, paragraphs, profile):
        findings.add("repeated_text", None, detail)
    foreign = [n for n in pkg.names() if not oc.is_part_name(n) and n != "[Content_Types].xml"]
    if foreign:
        notes.append(f"{len(foreign)} zip entr{'y' if len(foreign) == 1 else 'ies'} are not package parts "
                     f"(no content type, no relationship); preserved byte-for-byte")
    skipped = [n for n in pkg.names() if n not in scanned]
    if candidate_total > max_candidates:
        findings.add("too_many_candidates", None, f"{candidate_total} candidates; the manifest records the first {max_candidates}", severity="block")
    if not candidates and not findings.blocking():
        findings.add("no_candidates", None, "no field-like text, instructions, empty cells or content controls in the parts in scope", severity="report")
    if not any(c.eligible for c in candidates) and candidates:
        notes.append("no candidate is eligible; the template can be copied through but nothing can be filled")

    return m.Manifest(
        schema=m.SCHEMA_MANIFEST, skill_version=m.SKILL_VERSION, contract_version=m.CONTRACT_VERSION, job_id=job_id,
        created_utc=m.utc_now(), policy_sha256=policy_sha256, template=m.TemplateInfo(source_name=source_name, sha256=pkg.sha256, size_bytes=pkg.size_bytes),
        profile=profile, blocked=findings.blocking(), parts_in_scope=[n for n in pkg.names() if oc.in_scope(n, scope)],
        parts=parts_digest, paragraphs=paragraphs, rows=rows, candidates=candidates, findings=findings.as_list(),
        coverage=m.InspectionCoverage(parts_scanned=scanned, parts_skipped=skipped, notes=notes),
    )


def disambiguate_by_preceding_label(candidates: list[m.Candidate], paragraphs: list[m.ParagraphInfo]) -> list[str]:
    """Rename field candidates that all guess the same name, using the label that precedes each one.

    The commonest real layout is label then value: a cell holding "Position Title:" beside a cell holding a
    prompt like `<insert here>`, or a paragraph "General Role Statement:" above one. Every such prompt
    guesses the same name, so a plan built from the draft would write one value into all of them. The label
    is the field name, so it is used instead.

    Deliberately conservative. It fires only when a distinct label is found for *every* candidate in the
    group, and a paragraph that holds a field of its own is never treated as a label. A genuinely repeated
    placeholder such as `{{ client_name }}` therefore keeps one shared name, which is the documented
    behaviour, because its neighbours either hold fields or repeat.
    """
    notes: list[str] = []
    by_name: dict[str, list[m.Candidate]] = {}
    for c in candidates:
        if c.kind == "field" and c.name_guess:
            by_name.setdefault(c.name_guess, []).append(c)
    holds_field = {(c.part, c.paragraph_index) for c in candidates if c.kind == "field"}
    by_part: dict[str, list[m.ParagraphInfo]] = {}
    for p in paragraphs:
        by_part.setdefault(p.part, []).append(p)

    def label_for(c: m.Candidate) -> str | None:
        here = by_part.get(c.part, [])
        for p in reversed([x for x in here if x.index < c.paragraph_index]):
            if not p.text.strip():
                continue                                   # spacer paragraph: keep looking back
            if (p.part, p.index) in holds_field:
                return None                                # the neighbour is a value too, not a label
            return slug(p.text)
        return None

    renamed: dict[int, str] = {}
    for name, group in sorted(by_name.items()):
        if len(group) < 2:
            continue
        derived = [label_for(c) for c in group]
        if not all(derived) or len(set(derived)) != len(derived):
            continue
        renamed.update({id(c): str(d) for c, d in zip(group, derived)})
        shown = ", ".join(str(d) for d in derived[:6])
        notes.append(f"{len(group)} candidates all named {name!r} were renamed from the label preceding each "
                     f"({shown}{' ...' if len(derived) > 6 else ''}); confirm every mapping")
    if not renamed:
        return notes
    # Two candidates in one paragraph share the label above them, and two conventions in one document
    # are renamed independently, so a derived name can collide across groups. Sharing a name means one
    # value fills both spans, so the later span is suffixed. A name nobody derived is left alone, which
    # is what keeps a genuinely repeated placeholder on its single shared field.
    taken = {c.name_guess for c in candidates if c.kind == "field" and c.name_guess and id(c) not in renamed}
    for c in sorted((x for x in candidates if id(x) in renamed), key=lambda x: (x.part, x.paragraph_index, x.char_start)):
        base = name = renamed[id(c)]
        suffix = 1
        while name in taken:
            suffix += 1
            name = f"{base}_{suffix}"
        taken.add(name)
        c.name_guess = name
    return notes


def unrecognised_repeated_text(candidates: list[m.Candidate], paragraphs: list[m.ParagraphInfo],
                               profile: dict[str, Any]) -> list[str]:
    """Short paragraph texts that repeat and that no pattern claimed.

    This is the one way the skill can hand over a wrong document quietly: a fill marker whose convention
    the profile does not know is invisible to every stage, so nobody decides it and the residue scan
    cannot recognise it. Repetition is a convention-independent signal, because a template author writes
    the same prompt into every slot. On the two real templates this package has seen, the only short texts
    repeating three or more times were exactly the markers ("Not provided" twelve times, "xxx" eight).

    It cannot be decided mechanically whether "Not provided" is a marker or an answer, so this reports
    rather than blocks. Declaring a pattern for it in the profile turns it into a candidate and the
    finding goes away by itself.
    """
    settings = profile.get("repeated_text")
    if not isinstance(settings, dict):
        return []
    minimum = int(settings.get("min_occurrences", 3))
    max_chars = int(settings.get("max_chars", 40))
    claimed = {(c.part, c.paragraph_index) for c in candidates if c.kind in ("field", "control")}
    counts: dict[str, int] = {}
    for p in paragraphs:
        text = p.text.strip()
        # A label such as "Position Title:" legitimately repeats; it names a slot rather than filling one.
        if not text or p.truncated or len(text) > max_chars or text.endswith(":") or (p.part, p.index) in claimed:
            continue
        counts[text] = counts.get(text, 0) + 1
    repeated = sorted(((n, t) for t, n in counts.items() if n >= minimum), reverse=True)
    if not repeated:
        return []
    shown = ", ".join(f"{t!r} x{n}" for n, t in repeated[:4]) + (" ..." if len(repeated) > 4 else "")
    return [f"{len(repeated)} short text(s) repeat and match no pattern: {shown}. If these are fill markers, "
            f"declare a pattern for them in the profile; if they are content, say so in the review"]


def _nearest(el: ET.Element, parents: dict[ET.Element, ET.Element], tag: str) -> ET.Element | None:
    while el in parents:
        el = parents[el]
        if el.tag == tag:
            return el
    return None


def draft_plan(manifest: m.Manifest) -> m.Plan:
    """A plan skeleton: one decision per candidate that needs one, one field per distinct name guess.
    Field sources are left empty on purpose; the plan does not validate until they are mapped."""
    decisions: list[m.Decision] = []
    names: dict[str, None] = {}
    for c in manifest.candidates:
        if not c.decision_required:
            continue
        if c.kind in ("field", "control") and c.name_guess:
            decisions.append(m.Decision(candidate_id=c.id, decision="field", field=c.name_guess, reason=None))
            names.setdefault(c.name_guess, None)
        else:
            decisions.append(m.Decision(candidate_id=c.id, decision=None, field=None, reason=None))
    return m.Plan(
        schema=m.SCHEMA_PLAN, contract_version=m.CONTRACT_VERSION, template_sha256=manifest.template.sha256,
        manifest_sha256=m.sha256_document(manifest), locale={}, decisions=decisions,
        fields=[m.FieldSpec(name=n, type="string", source=None) for n in names], operations=[],
        notes="Decide every candidate with decision null; map every field's source to a path in values.json (or give a literal). This note is optional; remove or replace it.",
    )


def listing(manifest: m.Manifest, max_lines: int = 400) -> list[str]:
    """A compact, human-readable view of the manifest for the console."""
    lines: list[str] = []
    cands: dict[tuple[str, int], list[m.Candidate]] = {}
    for c in manifest.candidates:
        cands.setdefault((c.part, c.paragraph_index), []).append(c)
    current_part = None
    for p in manifest.paragraphs:
        here = cands.get((p.part, p.index), [])
        if not here and not p.text.strip():
            continue
        if p.part != current_part:
            lines.append(f"--- {p.part}")
            current_part = p.part
        where = "" if p.container == "body" else f" [{p.container}{'/' + p.row_id.rsplit('#', 1)[1] if p.row_id else ''}]"
        style = f" ({p.style})" if p.style else ""
        flag = " {" + ",".join(f for f in p.flags if f not in ("empty",)) + "}" if [f for f in p.flags if f != "empty"] else ""
        lines.append(f"p{p.index}{style}{where}{flag}: {p.text!r}{' ...' if p.truncated else ''}")
        for c in here:
            mark = "!" if c.decision_required else ("x" if not c.eligible else "?")
            extra = f" -> {c.name_guess}" if c.name_guess else ""
            why = f" ineligible: {c.ineligibility_reason}" if not c.eligible else ""
            lines.append(f"   {mark} {c.id}  {c.kind}/{c.pattern}/{c.confidence}  {c.text!r}{extra}{why}")
        if len(lines) >= max_lines:
            lines.append(f"... listing truncated at {max_lines} lines; see manifest.json")
            break
    return lines
