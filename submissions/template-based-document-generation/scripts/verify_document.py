"""Independent verifier: judges a candidate against the ORIGINAL snapshot and the compiled operations.

Independence rules, enforced by construction:
  * Inputs are the snapshot bytes, the candidate bytes, the manifest, the plan (for acknowledged
    candidates only), the compiled operations and the policy. The filler's edits are never consulted.
  * The snapshot tree and the candidate tree are walked side by side. Every element of the snapshot
    must reappear identically unless one compiled operation says otherwise: a deleted block is absent,
    a repeated row appears once per item, an insertion follows its anchor, and a paragraph with
    replacements differs only inside the runs that own a replaced span.
  * Expected paragraph text is computed from the snapshot text and the compiled values at the
    recorded offsets; the candidate is never searched for a value.
  * After the structural walk, every output paragraph is scanned with the profile's patterns. A match
    that is not a candidate the plan acknowledged (literal or keep) and does not lie inside an inserted
    value is *residue* and becomes a review item.

Every check returns an outcome; nothing here raises for a bad candidate.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import models as m  # noqa: E402
import namespace_validation as nv  # noqa: E402
import ooxml_common as oc  # noqa: E402

TEXT_TAGS = {oc.T, oc.TAB, oc.BR, oc.CR}
SDT, SDT_PR, SDT_CONTENT, TR, TBL = (oc.w(x) for x in ("sdt", "sdtPr", "sdtContent", "tr", "tbl"))
SHOWING_PLC, RSTYLE, PPR, SECTPR = oc.w("showingPlcHdr"), oc.w("rStyle"), oc.w("pPr"), oc.w("sectPr")
MAX_DIFFS = 8


@dataclass
class VerifyResult:
    checks: list[m.Check]
    review: list[m.ReviewItem]
    changes: list[m.Change]
    candidate_sha256: str
    candidate_size: int
    notes: list[str] = field(default_factory=list)

    def failed(self) -> list[m.Check]:
        return [c for c in self.checks if c.outcome != "passed"]

    @property
    def ok(self) -> bool:
        return bool(self.checks) and not self.failed()


class _Checks:
    def __init__(self) -> None:
        self.items: list[m.Check] = []

    def add(self, check_id: str, ok: bool, detail: str = "") -> bool:
        self.items.append(m.Check(id=check_id, outcome="passed" if ok else "failed", detail=detail[:800]))
        return ok

    def not_performed(self, check_id: str, detail: str) -> None:
        self.items.append(m.Check(id=check_id, outcome="not_performed", detail=detail[:800]))


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _same(a: ET.Element, b: ET.Element, path: str, diffs: list[str], removable=None) -> bool:
    """Exact recursive equality, optionally tolerating the absence in `b` of children `removable(x)`."""
    if len(diffs) >= MAX_DIFFS:
        return False
    if a.tag != b.tag:
        diffs.append(f"{path}: tag {_local(a.tag)} != {_local(b.tag)}"); return False
    if dict(a.attrib) != dict(b.attrib):
        diffs.append(f"{path}: attributes differ on {_local(a.tag)}"); return False
    if (a.text or "") != (b.text or "") or (a.tail or "") != (b.tail or ""):
        diffs.append(f"{path}: text or tail differs in {_local(a.tag)}"); return False
    ca = [x for x in a if not (removable and removable(x))] if removable else list(a)
    if len(ca) != len(b):
        diffs.append(f"{path}: child count {len(ca)} != {len(b)} under {_local(a.tag)}"); return False
    ok = True
    for i, (x, y) in enumerate(zip(ca, b)):
        if not _same(x, y, f"{path}/{_local(x.tag)}[{i}]", diffs, removable):
            ok = False
            if len(diffs) >= MAX_DIFFS:
                break
    return ok


def reference_problems(root: ET.Element) -> set[str]:
    """Document-wide reference invariants, independent of any plan: bookmark and comment ranges pair up
    and identities are unique. Reported as the *set of problems* so a template that is already odd cannot
    fail its own output; only problems the output adds are a failure."""
    bk_start: list[str] = []
    bk_end: list[str] = []
    bk_names: list[str] = []
    comments: dict[str, list[str]] = {"commentRangeStart": [], "commentRangeEnd": [], "commentReference": []}
    object_ids: list[str] = []
    for el in root.iter():
        local = el.tag.split("}")[-1]
        if local == "bookmarkStart":
            bk_start.append(el.get(oc.w("id"), ""))
            bk_names.append(el.get(oc.w("name"), ""))
        elif local == "bookmarkEnd":
            bk_end.append(el.get(oc.w("id"), ""))
        elif local in comments:
            comments[local].append(el.get(oc.w("id"), ""))
        elif local == "docPr":
            object_ids.append(el.get("id", ""))
    problems: set[str] = set()
    if sorted(bk_start) != sorted(bk_end):
        problems.add("bookmark starts and ends do not pair up")
    if len(set(bk_start)) != len(bk_start):
        problems.add("duplicate bookmark id")
    if len(set(bk_names)) != len(bk_names):
        problems.add("duplicate bookmark name")
    if sorted(comments["commentRangeStart"]) != sorted(comments["commentRangeEnd"]):
        problems.add("comment ranges do not pair up")
    if sorted(comments["commentRangeEnd"]) != sorted(comments["commentReference"]):
        problems.add("comment ranges and references do not match")
    if len(set(object_ids)) != len(object_ids):
        problems.add("duplicate drawing object id")
    # Structural invariants Word requires, checked on the output itself rather than inferred from the
    # plan. A plan whose every edit is authorised can still add up to a table with no rows.
    for tbl in root.iter(oc.w("tbl")):
        if not any(True for _ in tbl.iter(oc.w("tr"))):
            problems.add("table with no rows")
    for cell in root.iter(oc.w("tc")):
        if not any(True for _ in cell.iter(oc.P)):
            problems.add("table cell with no paragraph")
    return problems


def expected_text(original: str, spans: list[tuple[int, int, str]]) -> str:
    out = original
    for s, e, value in sorted(spans, key=lambda x: -x[0]):
        out = out[:s] + value + out[e:]
    return out


def _run_text(run: ET.Element) -> str:
    out = []
    for child in run:
        if child.tag == oc.T:
            out.append(child.text or "")
        elif child.tag == oc.TAB:
            out.append("\t")
        elif child.tag in (oc.BR, oc.CR):
            out.append("\n")
    return "".join(out)


def _interleaving(run: ET.Element) -> str:
    out = ""
    for c in run:
        ch = "T" if c.tag in TEXT_TAGS else "N"
        if not (ch == "T" and out.endswith("T")):
            out += ch
    return out


def _placeholder_style(x: ET.Element) -> bool:
    return x.tag == RSTYLE and x.get(oc.w("val")) == "PlaceholderText"


# --------------------------------------------------------------------------------------
# Per-part context: what the compiled operations mean in terms of snapshot elements
# --------------------------------------------------------------------------------------

class _Ctx:
    def __init__(self, part: str, root_a: ET.Element, cp: m.CompiledPart, decl_a: dict, decl_c: dict):
        self.part = part
        self.cp = cp
        self.decl_a, self.decl_c = decl_a, decl_c
        self.parents = oc.parent_map(root_a)
        self.plist = oc.paragraphs(root_a)
        self.pidx = {id(p): i for i, p in enumerate(self.plist)}
        self.deleted: set[int] = set()          # element ids that must be absent from the candidate
        self.cleared: set[int] = set()          # paragraph ids that must survive emptied (sole paragraph of a cell)
        self.repeats: dict[int, m.RowRepeat] = {}
        self.control_sdts: set[int] = set()      # sdt ids whose showingPlcHdr may be gone
        self.problems: list[str] = []
        self.diffs: list[str] = []
        self.text_diffs: list[str] = []
        self.namespace_ok = True
        self.expected_refs: list[str] = []
        self.aligned: list[tuple[int | None, ET.Element, list[tuple[int, int, str]], str]] = []   # (snapshot index, candidate paragraph, spans, kind)
        self.replaced = 0
        self._resolve()

    def _container(self, p: ET.Element) -> tuple[ET.Element | None, ET.Element]:
        return oc.real_container(p, self.parents)

    def _resolve(self) -> None:
        cp = self.cp
        for idx in cp.delete_paragraphs:
            if idx >= len(self.plist):
                self.problems.append(f"paragraph {idx} missing from the snapshot"); continue
            p = self.plist[idx]
            container, block = self._container(p)
            if container is not None and container.tag == oc.w("tc") and block is p and len(list(container.iter(oc.P))) == 1:
                self.cleared.add(id(p))
            else:
                self.deleted.add(id(p))
        for first, last in cp.delete_ranges:
            if first >= len(self.plist) or last >= len(self.plist):
                self.problems.append("range outside the snapshot"); continue
            ca, ba = self._container(self.plist[first])
            cb, bb = self._container(self.plist[last])
            if ca is not cb or ca is None:
                self.problems.append(f"range {first}-{last} spans containers"); continue
            sibs = list(ca)
            i0, i1 = sibs.index(ba), sibs.index(bb)
            for el in sibs[i0:i1 + 1]:
                self.deleted.add(id(el))
        for idx in cp.delete_rows:
            tr = self._nearest(self.plist[idx], TR) if idx < len(self.plist) else None
            if tr is None:
                self.problems.append(f"paragraph {idx} is not in a row"); continue
            self.deleted.add(id(tr))
        for idx, n in cp.delete_breaks:
            if idx >= len(self.plist):
                self.problems.append(f"paragraph {idx} missing from the snapshot"); continue
            breaks = [t for t in oc.paragraph_tokens(self.plist[idx]) if t.kind == "br"]
            if len(breaks) < n:
                self.problems.append(f"paragraph {idx} has no break number {n}"); continue
            self.deleted.add(id(breaks[n - 1].element))     # the generic walk then requires it to be absent
        for rep in cp.repeats:
            tr = self._nearest(self.plist[rep.anchor], TR) if rep.anchor < len(self.plist) else None
            if tr is None:
                self.problems.append(f"paragraph {rep.anchor} is not in a row"); continue
            self.repeats[id(tr)] = rep
        for idx, repls in cp.replacements.items():
            self._note_controls(idx, repls)
        for rep in cp.repeats:
            for copy in rep.copies:
                for idx, repls in copy.items():
                    self._note_controls(idx, repls)

    def _note_controls(self, idx: int, repls: list[m.Replacement]) -> None:
        if idx >= len(self.plist):
            return
        p = self.plist[idx]
        tokens = oc.paragraph_tokens(p)
        for r in repls:
            if not r.control:
                continue
            owners = [t for t in tokens if t.start < r.end and t.end > r.start]
            anchor = owners[0].run if owners and owners[0].run is not None else p
            sdt = self._nearest(anchor, SDT)
            if sdt is not None:
                self.control_sdts.add(id(sdt))

    def _ns_equal(self, a: ET.Element, b: ET.Element) -> bool:
        """Parallel declaration comparison for two subtrees `_same` has already matched structurally.
        Expanded element names hide a lost or added xmlns, so this is checked separately."""
        if self.decl_a.get(a, {}) != self.decl_c.get(b, {}) or len(a) != len(b):
            return False
        return all(self._ns_equal(x, y) for x, y in zip(a, b))

    def _nearest(self, el: ET.Element, tag: str) -> ET.Element | None:
        while el in self.parents:
            el = self.parents[el]
            if el.tag == tag:
                return el
        return None

    # ---- the walk ------------------------------------------------------------------------------
    def walk(self, a: ET.Element, c: ET.Element, path: str, copy: dict[int, list[m.Replacement]] | None) -> None:
        if len(self.diffs) >= MAX_DIFFS:
            return
        if a.tag != c.tag:
            self.diffs.append(f"{path}: tag {_local(a.tag)} != {_local(c.tag)}"); return
        if self.decl_a.get(a, {}) != self.decl_c.get(c, {}):
            self.namespace_ok = False
        for k, v in a.attrib.items():
            if k.startswith(f"{{{oc.R_NS}}}"):
                self.expected_refs.append(v)
        if a.tag == oc.P:
            idx = self.pidx[id(a)]
            repls = (copy if copy is not None else self.cp.replacements).get(idx)
            if repls:
                self._compare_replaced_paragraph(a, c, repls, path, idx, copy is not None)
                return
            self.aligned.append((idx, c, [], "copy" if copy is not None else "same"))
        if dict(a.attrib) != dict(c.attrib):
            self.diffs.append(f"{path}: attributes differ on {_local(a.tag)}"); return
        if (a.text or "") != (c.text or "") or (a.tail or "") != (c.tail or ""):
            self.diffs.append(f"{path}: text or tail differs on {_local(a.tag)}"); return
        self._align_children(a, c, path, copy)

    def _align_children(self, a: ET.Element, c: ET.Element, path: str, copy: dict | None) -> None:
        cc = list(c)
        ci = 0
        for i, x in enumerate(a):
            if len(self.diffs) >= MAX_DIFFS:
                return
            xp = f"{path}/{_local(x.tag)}[{i}]"
            if id(x) in self.deleted:
                continue
            if x.tag == SHOWING_PLC and a.tag == SDT_PR and id(self.parents.get(a)) in self.control_sdts:
                if ci < len(cc) and cc[ci].tag == SHOWING_PLC:
                    self.diffs.append(f"{xp}: showingPlcHdr should have been removed from a filled control")
                continue
            if id(x) in self.cleared:
                if ci >= len(cc):
                    self.diffs.append(f"{xp}: cleared paragraph missing"); return
                self._check_cleared(x, cc[ci], xp); ci += 1
                continue
            if id(x) in self.repeats and copy is None:
                rep = self.repeats[id(x)]
                for n, cpy in enumerate(rep.copies):
                    if ci >= len(cc):
                        self.diffs.append(f"{xp}: repeated row copy {n} missing"); return
                    self.walk(x, cc[ci], f"{xp}(copy {n})", cpy); ci += 1
                continue
            if ci >= len(cc):
                self.diffs.append(f"{xp}: {_local(x.tag)} missing from the candidate"); return
            self.walk(x, cc[ci], xp, copy); ci += 1
            if x.tag == oc.P and copy is None:
                for text in self.cp.inserts.get(self.pidx[id(x)], []):
                    if ci >= len(cc):
                        self.diffs.append(f"{xp}: inserted paragraph missing"); return
                    self._check_inserted(x, cc[ci], text, xp); ci += 1
        if ci != len(cc) and len(self.diffs) < MAX_DIFFS:
            self.diffs.append(f"{path}: {len(cc) - ci} unexpected extra child element(s) under {_local(a.tag)}")

    def _check_cleared(self, x: ET.Element, y: ET.Element, path: str) -> None:
        if y.tag != oc.P or dict(x.attrib) != dict(y.attrib) or self.decl_a.get(x, {}) != self.decl_c.get(y, {}):
            self.diffs.append(f"{path}: cleared paragraph differs in tag or attributes"); return
        ppr = x.find(PPR)
        kids = list(y)
        if ppr is None:
            if kids:
                self.diffs.append(f"{path}: cleared paragraph is not empty")
        elif len(kids) != 1 or not _same(ppr, kids[0], path + "/pPr", self.diffs):
            self.diffs.append(f"{path}: cleared paragraph does not keep its pPr")
        elif not self._ns_equal(ppr, kids[0]):
            self.namespace_ok = False
        self.aligned.append((self.pidx[id(x)], y, [(0, len(oc.paragraph_text(x)), "")], "cleared"))

    def _check_inserted(self, x: ET.Element, y: ET.Element, text: str, path: str) -> None:
        if y.tag != oc.P or y.attrib:
            self.diffs.append(f"{path}: inserted paragraph has an unexpected tag or attributes"); return
        if any(self.decl_c.get(el) for el in y.iter()):
            self.namespace_ok = False
        kids = list(y)
        ppr = x.find(PPR)
        if ppr is not None:
            if not kids or not _same(ppr, kids[0], path + "/pPr", self.diffs, removable=lambda e: e.tag == SECTPR):
                self.diffs.append(f"{path}: inserted paragraph does not inherit the anchor's pPr"); return
            kids = kids[1:]
        if len(kids) != 1 or kids[0].tag != oc.R:
            self.diffs.append(f"{path}: inserted paragraph must contain exactly one run"); return
        run = kids[0]
        first_run = next((r for r in x if r.tag == oc.R), None)
        rpr_a = first_run.find(oc.RPR) if first_run is not None else None
        rpr_c = run.find(oc.RPR)
        if (rpr_a is None) != (rpr_c is None) or (rpr_a is not None and not _same(rpr_a, rpr_c, path + "/rPr", self.diffs)):
            self.diffs.append(f"{path}: inserted run does not inherit the anchor's first run properties"); return
        if any(c.tag not in TEXT_TAGS and c.tag != oc.RPR for c in run) or _run_text(run) != text:
            self.text_diffs.append(f"{path}: inserted paragraph text is not the planned text"); return
        self.aligned.append((None, y, [(0, 0, text)], "inserted"))

    def _compare_replaced_paragraph(self, a: ET.Element, c: ET.Element, repls: list[m.Replacement], path: str, idx: int, is_copy: bool) -> None:
        tokens = oc.paragraph_tokens(a)
        original = "".join(t.text for t in tokens)
        spans = [(r.start, r.end, r.text) for r in sorted(repls, key=lambda r: r.start)]
        if dict(a.attrib) != dict(c.attrib):
            self.diffs.append(f"{path}: attributes differ on the paragraph"); return
        if not tokens:
            self._compare_empty_fill(a, c, spans, path)
            self.aligned.append((idx, c, spans, "copy" if is_copy else "same"))
            return
        ordinals = self._run_ordinals(a)
        owning: set[int] = set()
        first_runs: set[int] = set()
        for s, e, _ in spans:
            owners = [t for t in tokens if t.kind == "t" and t.start < e and t.end > s]
            for i, t in enumerate(owners):
                o = ordinals.get(id(t.run), -1)
                owning.add(o)
                if i == 0:
                    first_runs.add(o)
        control = any(r.control for r in repls)

        def walk(x: ET.Element, y: ET.Element, p: str) -> None:
            if len(self.diffs) >= MAX_DIFFS:
                return
            if x.tag != y.tag:
                self.diffs.append(f"{p}: tag {_local(x.tag)} != {_local(y.tag)}"); return
            if self.decl_a.get(x, {}) != self.decl_c.get(y, {}):
                self.namespace_ok = False
            if x.tag == oc.R and id(x) in ordinals and ordinals[id(x)] in owning:
                self._compare_owning_run(x, y, ordinals[id(x)] in first_runs, control, p)
                return
            if dict(x.attrib) != dict(y.attrib):
                self.diffs.append(f"{p}: attributes differ on {_local(x.tag)}"); return
            if (x.text or "") != (y.text or "") or (x.tail or "") != (y.tail or ""):
                self.diffs.append(f"{p}: text or tail differs on {_local(x.tag)}"); return
            xs = [k for k in x if not (control and k.tag == SHOWING_PLC and x.tag == SDT_PR and id(self.parents.get(x)) in self.control_sdts)]
            ys = list(y)
            if len(xs) != len(ys):
                self.diffs.append(f"{p}: child count {len(xs)} != {len(ys)} under {_local(x.tag)}"); return
            for i, (k, l) in enumerate(zip(xs, ys)):
                walk(k, l, f"{p}/{_local(k.tag)}[{i}]")

        for i, (x, y) in enumerate(zip(list(a), list(c))):
            walk(x, y, f"{path}/{_local(x.tag)}[{i}]")
        if len(a) != len(c):
            self.diffs.append(f"{path}: child count {len(a)} != {len(c)} under the paragraph")
        got = oc.paragraph_text(c)
        want = expected_text(original, spans)
        if got != want:
            self.text_diffs.append(f"{path}: paragraph text is not the expected replacement")
        else:
            ord_c = self._run_ordinals(c)
            if len(ordinals) != len(ord_c):
                self.text_diffs.append(f"{path}: run count changed")
            else:
                runs_a = {v: k for k, v in ordinals.items()}
                elems_a = {id(el): el for el in a.iter(oc.R)}
                elems_c = {v: k for k, v in ord_c.items()}
                all_c = {id(el): el for el in c.iter(oc.R)}
                for o in owning:
                    exp = self._expected_run_text(a, elems_a[runs_a[o]], tokens, spans)
                    if exp != _run_text(all_c[elems_c[o]]):
                        self.text_diffs.append(f"{path}: run {o} does not carry the expected text"); break
                else:
                    self.replaced += len(spans)
        for t in c.iter(oc.T):
            if oc.needs_preserve(t.text or "") and t.get(oc.XML_SPACE) != "preserve":
                self.text_diffs.append(f"{path}: a w:t with edge or double whitespace lacks xml:space=preserve"); break
        for el in a.iter():                      # the paragraph's own attributes were counted by walk()
            if el is a:
                continue
            for k, v in el.attrib.items():
                if k.startswith(f"{{{oc.R_NS}}}"):
                    self.expected_refs.append(v)
        self.aligned.append((idx, c, spans, "copy" if is_copy else "same"))

    def _compare_empty_fill(self, a: ET.Element, c: ET.Element, spans: list[tuple[int, int, str]], path: str) -> None:
        if len(spans) != 1 or spans[0][:2] != (0, 0):
            self.diffs.append(f"{path}: an empty paragraph can only take one value at offset 0"); return
        kids_a, kids_c = list(a), list(c)
        if len(kids_c) != len(kids_a) + 1:
            self.diffs.append(f"{path}: an empty paragraph must gain exactly one run"); return
        for i, (x, y) in enumerate(zip(kids_a, kids_c)):
            if not _same(x, y, f"{path}/{_local(x.tag)}[{i}]", self.diffs):
                return
            if not self._ns_equal(x, y):
                self.namespace_ok = False
        run = kids_c[-1]
        if run.tag != oc.R or self.decl_c.get(run):
            self.diffs.append(f"{path}: the added element is not a plain run"); return
        ppr = a.find(PPR)
        mark_rpr = ppr.find(oc.RPR) if ppr is not None else None
        rpr = run.find(oc.RPR)
        if (mark_rpr is None) != (rpr is None) or (mark_rpr is not None and not _same(mark_rpr, rpr, path + "/rPr", self.diffs)):
            self.diffs.append(f"{path}: the added run must carry the paragraph mark's run properties"); return
        if any(k.tag not in TEXT_TAGS and k.tag != oc.RPR for k in run) or any(self.decl_c.get(k) for k in run):
            self.diffs.append(f"{path}: the added run contains unexpected children"); return
        if _run_text(run) != spans[0][2]:
            self.text_diffs.append(f"{path}: paragraph text is not the expected replacement")
        else:
            self.replaced += 1
        for t in run.iter(oc.T):
            if oc.needs_preserve(t.text or "") and t.get(oc.XML_SPACE) != "preserve":
                self.text_diffs.append(f"{path}: a w:t with edge or double whitespace lacks xml:space=preserve"); break

    def _compare_owning_run(self, ra: ET.Element, rc: ET.Element, is_first: bool, control: bool, path: str) -> None:
        diffs = self.diffs
        if dict(ra.attrib) != dict(rc.attrib) or (ra.tail or "") != (rc.tail or ""):
            diffs.append(f"{path}: run attributes or tail differ"); return
        removable = (lambda e: control and is_first and _placeholder_style(e)) if control else None
        na = [c for c in ra if c.tag not in TEXT_TAGS]
        nc = [c for c in rc if c.tag not in TEXT_TAGS]
        if len(na) != len(nc):
            diffs.append(f"{path}: non-text children {len(na)} != {len(nc)}"); return
        for i, (x, y) in enumerate(zip(na, nc)):
            if not _same(x, y, f"{path}/{_local(x.tag)}[{i}]", diffs, removable):
                return
            if removable:
                # A control fill may drop the placeholder style, so the subtrees differ by design; the
                # declarations on the element itself must still match.
                if self.decl_a.get(x, {}) != self.decl_c.get(y, {}):
                    self.namespace_ok = False
            elif not self._ns_equal(x, y):
                self.namespace_ok = False
        if _interleaving(ra) != _interleaving(rc):
            diffs.append(f"{path}: text/non-text child interleaving changed"); return
        ta = [c for c in ra if c.tag in TEXT_TAGS]
        tc = [c for c in rc if c.tag in TEXT_TAGS]
        if any(self.decl_c.get(c) for c in tc):
            self.namespace_ok = False
        # A tab or newline must be a w:tab or w:br element; inside w:t it is only whitespace to Word.
        def literal(items: list[ET.Element]) -> bool:
            return any(ch in (c.text or "") for c in items if c.tag == oc.T for ch in ("\n", "\t"))
        if literal(tc) and not literal(ta):
            diffs.append(f"{path}: a line break or tab was written as text instead of an element"); return
        if not is_first:
            if [c.tag for c in ta] != [c.tag for c in tc]:
                diffs.append(f"{path}: text element sequence changed in a non-first owning run"); return
            for i, (x, y) in enumerate(zip(ta, tc)):
                ax = {k: v for k, v in x.attrib.items() if k != oc.XML_SPACE}
                ay = {k: v for k, v in y.attrib.items() if k != oc.XML_SPACE}
                if ax != ay or len(x) or len(y):
                    diffs.append(f"{path}: text element {i} changed attributes or gained children"); return
            return
        for c in tc:
            if c.tag not in (oc.T, oc.TAB, oc.BR, oc.CR) or len(c):
                diffs.append(f"{path}: unexpected {_local(c.tag)} in the first owning run"); return
        attributed_a = [(c.tag, {k: v for k, v in c.attrib.items() if k != oc.XML_SPACE}) for c in ta if any(k != oc.XML_SPACE for k in c.attrib)]
        attributed_c = [(c.tag, {k: v for k, v in c.attrib.items() if k != oc.XML_SPACE}) for c in tc if any(k != oc.XML_SPACE for k in c.attrib)]
        if attributed_a != attributed_c:
            diffs.append(f"{path}: attributed text elements changed in the first owning run"); return
        seq_a = [c.tag for c in ta if c.tag != oc.T]
        seq_c = [c.tag for c in tc if c.tag != oc.T]
        it = iter(seq_c)
        if not all(any(x == y for y in it) for x in seq_a):
            diffs.append(f"{path}: an existing break or tab disappeared from the first owning run"); return

    @staticmethod
    def _run_ordinals(p: ET.Element) -> dict[int, int]:
        out: dict[int, int] = {}

        def walk(el: ET.Element) -> None:
            for child in el:
                if child.tag == oc.P:
                    continue
                if child.tag == oc.R:
                    out[id(child)] = len(out)
                walk(child)

        walk(p)
        return out

    @staticmethod
    def _expected_run_text(p: ET.Element, run: ET.Element, tokens: list[oc.Token], spans: list[tuple[int, int, str]]) -> str:
        mine = [t for t in tokens if t.run is run]
        if not mine:
            return ""
        run_start, run_end = mine[0].start, mine[-1].end
        text = "".join(t.text for t in mine)
        edits = []
        for s, e, value in spans:
            a, b = max(s, run_start), min(e, run_end)
            if a < b:
                first_owner_here = any(t.kind == "t" and t.start <= s < t.end for t in mine)
                edits.append((a - run_start, b - run_start, value if first_owner_here else ""))
        for a, b, value in sorted(edits, key=lambda x: -x[0]):
            text = text[:a] + value + text[b:]
        return text


# --------------------------------------------------------------------------------------
# Residue scan
# --------------------------------------------------------------------------------------

def _inserted_regions(spans: list[tuple[int, int, str]]) -> list[tuple[int, int]]:
    """Output-coordinate regions covered by inserted values."""
    out = []
    delta = 0
    for s, e, value in sorted(spans):
        out.append((s + delta, s + delta + len(value)))
        delta += len(value) - (e - s)
    return out


def _to_snapshot_offset(pos: int, spans: list[tuple[int, int, str]]) -> int:
    delta = 0
    for s, e, value in sorted(spans):
        if s + delta + len(value) <= pos:
            delta += len(value) - (e - s)
        else:
            break
    return pos - delta


def residue_scan(ctx: _Ctx, manifest: m.Manifest, plan: m.Plan, limits: dict[str, Any]) -> list[m.ReviewItem]:
    patterns = [(p["name"], re.compile(p["regex"])) for key in ("field_patterns", "instruction_patterns") for p in manifest.profile.get(key, [])]
    acknowledged: dict[int, list[tuple[int, int]]] = {}       # paragraph index -> spans the plan knowingly left in place
    decisions = {d.candidate_id: d.decision for d in plan.decisions}
    for c in manifest.candidates:
        if c.part != ctx.part:
            continue
        d = decisions.get(c.id)
        if d in ("literal", "keep") or (d is None and not c.decision_required) or not c.eligible:
            acknowledged.setdefault(c.paragraph_index, []).append((c.char_start, c.char_end))

    def is_acknowledged(idx: int | None, a: int, b: int, spans: list[tuple[int, int, str]]) -> bool:
        if idx is None:
            return False
        sa, sb = _to_snapshot_offset(a, spans), _to_snapshot_offset(b, spans)
        return any(s <= sa and sb <= e for s, e in acknowledged.get(idx, []))

    items: list[m.ReviewItem] = []
    seen: set[tuple[int | None, int, str]] = set()
    cap = int(limits.get("max_report_text_chars", 240))
    for idx, y, spans, kind in ctx.aligned:
        if kind == "cleared":
            continue
        text = oc.paragraph_text(y)
        regions = _inserted_regions(spans) if kind != "inserted" else [(0, len(text))]
        for pname, rx in patterns:
            for mt in rx.finditer(text):
                a, b = mt.start(), mt.end()
                if b <= a or any(ra <= a and b <= rb for ra, rb in regions):
                    continue
                if is_acknowledged(idx, a, b, spans):
                    continue
                key = (idx, a, pname)
                if key in seen:
                    continue
                seen.add(key)
                where = f"{ctx.part}#p{idx}" if idx is not None else f"{ctx.part} (inserted paragraph)"
                items.append(m.ReviewItem("residue", f"{where}: {pname} match still present: {mt.group(0)[:cap]!r}", where))
    return items


# --------------------------------------------------------------------------------------
# Change list
# --------------------------------------------------------------------------------------

def _removed_summary(texts: list[str], first: int, last: int, cap: int) -> str:
    """What a deletion removes: where it starts, where it ends, and samples between.

    A joined prefix of a long range shows only its beginning, which is precisely where an over-broad
    deletion looks correct. The far end is where it shows. Anyone reading the dry run has to be able to
    see that a range meant to drop a cover page has reached the middle of the document.
    """
    idx = [i for i in range(first, min(last, len(texts) - 1) + 1) if texts[i].strip()]
    if not idx:
        return f"{last - first + 1} paragraphs, none with text"
    picks = [idx[0]]
    if len(idx) > 2:
        picks += [idx[round((len(idx) - 1) * k / 4)] for k in (1, 2, 3)]
    picks.append(idx[-1])
    width = max(24, cap // max(1, len(set(picks))))
    seen: set[int] = set()
    parts: list[str] = []
    for i in picks:
        if i in seen:
            continue
        seen.add(i)
        text = texts[i].strip().replace("\n", "\\n").replace("\t", "\\t")
        parts.append(f"p{i}: {text if len(text) <= width else text[: width - 1] + chr(8230)}")
    return " | ".join(parts)


def describe_changes(snapshot_parts: dict[str, ET.Element], compiled: m.Compiled, limits: dict[str, Any]) -> list[m.Change]:
    cap = int(limits.get("max_report_text_chars", 240))

    def clip(s: str) -> str:
        s = s.replace("\n", "\\n").replace("\t", "\\t")
        return s if len(s) <= cap else s[: cap - 1] + "\u2026"

    changes: list[m.Change] = []
    for part, cp in compiled.parts.items():
        root = snapshot_parts.get(part)
        if root is None:
            continue
        plist = oc.paragraphs(root)
        texts = [oc.paragraph_text(p) for p in plist]
        for idx in sorted(cp.replacements):
            spans = [(r.start, r.end, r.text) for r in cp.replacements[idx]]
            op = "fill_control" if any(r.control for r in cp.replacements[idx]) else "replace_text"
            changes.append(m.Change(op, part, f"{part}#p{idx}", clip(texts[idx]), clip(expected_text(texts[idx], spans))))
        for idx in sorted(cp.delete_paragraphs):
            changes.append(m.Change("delete_paragraph", part, f"{part}#p{idx}", clip(texts[idx]), None))
        for first, last in cp.delete_ranges:
            changes.append(m.Change("delete_range", part, f"{part}#p{first}", _removed_summary(texts, first, last, cap),
                                    None, f"{last - first + 1} paragraphs, {first}-{last}"))
        for idx in cp.delete_rows:
            changes.append(m.Change("delete_row", part, f"{part}#p{idx}", clip(texts[idx]), None))
        for idx, n in cp.delete_breaks:
            before = texts[idx] if idx < len(texts) else ""
            positions = [i for i, ch in enumerate(before) if ch == "\n"]
            after = before[:positions[n - 1]] + before[positions[n - 1] + 1:] if len(positions) >= n else before
            changes.append(m.Change("delete_break", part, f"{part}#p{idx}", clip(before), clip(after), f"break {n}"))
        for rep in cp.repeats:
            row_text = " | ".join(texts[i] for i in range(rep.first, rep.last + 1))
            first_copy = " | ".join(expected_text(texts[i], [(r.start, r.end, r.text) for r in rep.copies[0].get(i, [])]) for i in range(rep.first, rep.last + 1)) if rep.copies else ""
            changes.append(m.Change("repeat_row", part, f"{part}#p{rep.anchor}", clip(row_text), clip(first_copy), f"{len(rep.copies)} copies (first shown)"))
        for idx in sorted(cp.inserts):
            for text in cp.inserts[idx]:
                changes.append(m.Change("insert_paragraph_after", part, f"{part}#p{idx}", None, clip(text)))
    return changes


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------

def verify(snapshot: bytes, candidate: bytes, manifest: m.Manifest, plan: m.Plan, compiled: m.Compiled, policy: dict[str, Any]) -> VerifyResult:
    limits = dict(policy.get("limits", {}))
    checks = _Checks()
    notes: list[str] = []
    review: list[m.ReviewItem] = []
    cand_sha = m.sha256_bytes(candidate)
    read_limits = dict(limits, max_template_bytes=max(int(limits.get("max_output_bytes", 10_000_000)), len(snapshot) * 2, len(candidate) + 1))
    try:
        snap = oc.read_package(snapshot, read_limits)
    except oc.PackageError as exc:
        checks.add("pkg.snapshot_readable", False, str(exc))
        return _finish(checks, review, [], cand_sha, candidate, notes, limits)
    if not checks.add("pkg.snapshot_matches_manifest", snap.sha256 == manifest.template.sha256, "snapshot hash vs manifest"):
        return _finish(checks, review, [], cand_sha, candidate, notes, limits)     # nothing else can be derived from the wrong snapshot
    try:
        cand = oc.read_package(candidate, read_limits)
        checks.add("pkg.zip_readable", True, f"{len(cand.entries)} entries; package structure valid")
    except oc.PackageError as exc:
        checks.add("pkg.zip_readable", False, str(exc))
        return _finish(checks, review, [], cand_sha, candidate, notes, limits)

    ea = [(e.name, e.date_time, e.external_attr, e.create_system, e.compress_type, e.is_dir) for e in snap.entries]
    ec = [(e.name, e.date_time, e.external_attr, e.create_system, e.compress_type, e.is_dir) for e in cand.entries]
    if not checks.add("pkg.entry_set_identical", ea == ec, "entry names, order and per-entry metadata"):
        notes.append("entry differences: " + ", ".join([x[0] for x, y in zip(ea, ec) if x != y][:5] or ["entry count differs"]))

    touched = {part for part, cp in compiled.parts.items()
               if cp.replacements or cp.deleted or cp.repeats or cp.inserts or cp.delete_breaks}
    untouched_bad = [n for n in snap.names() if n not in touched and cand.parts.get(n) != snap.parts.get(n)]
    checks.add("pkg.untouched_parts_identical", not untouched_bad, ", ".join(untouched_bad[:5]) if untouched_bad else f"{len(snap.names()) - len(touched)} parts byte-identical")
    extra = [n for n in cand.names() if n not in snap.parts]
    checks.add("pkg.no_new_parts", not extra, ", ".join(extra[:5]))

    trees: dict[str, tuple[nv.NamespaceTree, nv.NamespaceTree]] = {}
    parse_problems: list[str] = []
    for name in sorted(touched):
        if name not in manifest.parts_in_scope:
            parse_problems.append(f"{name}: outside the parts in scope"); continue
        try:
            trees[name] = (nv.parse_namespaces(snap.parts[name], limits), nv.parse_namespaces(cand.parts[name], limits))
        except (nv.NamespaceError, KeyError):
            parse_problems.append(f"{name}: XML or namespace validation failed")
    checks.add("pkg.in_scope_parts_parse", not parse_problems, "; ".join(parse_problems[:3]) if parse_problems else f"{len(trees)} modified part(s) parse")
    if parse_problems:
        for cid in ("pkg.no_new_relationships", "pkg.namespace_preserved", "ops.structure_matches_plan", "ops.paragraph_texts_expected", "ops.all_replacements_applied"):
            checks.not_performed(cid, "cannot compare: unparseable or out-of-scope part")
        return _finish(checks, review, [], cand_sha, candidate, notes, limits)

    structure_diffs: list[str] = []
    text_diffs: list[str] = []
    rel_bad: list[str] = []
    ref_bad: list[str] = []
    namespace_ok = True
    replaced = 0
    expected_replacements = sum(len(v) for cp in compiled.parts.values() for v in cp.replacements.values()) + \
        sum(len(v) for cp in compiled.parts.values() for rep in cp.repeats for copy in rep.copies for v in copy.values())
    snapshot_roots: dict[str, ET.Element] = {}
    for name, (ta, tc) in trees.items():
        snapshot_roots[name] = ta.root
        added = reference_problems(tc.root) - reference_problems(ta.root)
        if added:
            ref_bad.append(f"{name}: " + "; ".join(sorted(added)))
        ctx = _Ctx(name, ta.root, compiled.parts[name], ta.declarations, tc.declarations)
        if ctx.problems:
            structure_diffs += [f"{name}: {p}" for p in ctx.problems]
            continue
        ctx.walk(ta.root, tc.root, name, None)
        structure_diffs += ctx.diffs
        text_diffs += ctx.text_diffs
        namespace_ok = namespace_ok and ctx.namespace_ok
        replaced += ctx.replaced
        actual_refs = sorted(v for el in tc.root.iter() for k, v in el.attrib.items() if k.startswith(f"{{{oc.R_NS}}}"))
        if sorted(ctx.expected_refs) != actual_refs:
            rel_bad.append(name)
        if not ctx.diffs:
            review += residue_scan(ctx, manifest, plan, limits)
    checks.add("pkg.no_new_relationships", not rel_bad, ", ".join(rel_bad) if rel_bad else "relationship references match the planned operations")
    checks.add("pkg.reference_integrity", not ref_bad, "; ".join(ref_bad[:3]) if ref_bad else "bookmark, comment and object references remain paired and unique")
    checks.add("pkg.namespace_preserved", namespace_ok, "namespace declarations and their element scopes preserved")
    checks.add("ops.structure_matches_plan", not structure_diffs, "; ".join(structure_diffs[:3]) if structure_diffs else "every difference corresponds to a planned operation")
    checks.add("ops.paragraph_texts_expected", not text_diffs, "; ".join(text_diffs[:3]) if text_diffs else "paragraph and run texts match the planned values")
    checks.add("ops.all_replacements_applied", replaced == expected_replacements and not text_diffs, f"{replaced}/{expected_replacements} replacements")
    changes = describe_changes(snapshot_roots, compiled, limits)
    return _finish(checks, review, changes, cand_sha, candidate, notes, limits)


def _finish(checks: _Checks, review: list[m.ReviewItem], changes: list[m.Change], cand_sha: str, candidate: bytes, notes: list[str], limits: dict[str, Any]) -> VerifyResult:
    size_ok = len(candidate) <= int(limits.get("max_output_bytes", 10_000_000))
    checks.add("delivery.document_size", size_ok, f"{len(candidate):,} bytes")
    return VerifyResult(checks.items, review, changes, cand_sha, len(candidate), notes)
