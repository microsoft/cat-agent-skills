"""Filler: snapshot + manifest + compiled edits -> candidate .docx bytes.

Edits the raw bytes of the parts in scope and rebuilds the archive with the original entry order and
metadata. Refuses to run unless the snapshot hash matches the manifest and every paragraph it is about
to touch still hashes to what the inspector recorded. Structural deletions obey a few generic OOXML
safety rules (a cell keeps at least one paragraph, a container keeps at least one block, section
breaks and unbalanced bookmark or comment ranges are never removed).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import models as m  # noqa: E402
import ooxml_common as oc  # noqa: E402


class ApplyRefused(Exception):
    """Preconditions failed; nothing was produced. The message is safe to show to a user."""


@dataclass
class ApplyResult:
    candidate: bytes
    parts_modified: list[str]
    notes: list[str] = field(default_factory=list)


def _replacement_edits(raw: oc.RawPart, p: oc.RawNode, repls: list[m.Replacement]) -> list[oc.Edit]:
    tokens = raw.tokens(p)
    edits: list[oc.Edit] = []
    if not tokens:
        if len(repls) != 1 or repls[0].start != 0 or repls[0].end != 0:
            raise ApplyRefused(f"{raw.part}: paragraph {p.index} has no text but the plan addresses a span inside it")
        edits.append(oc.empty_paragraph_fill_edit(raw, p, repls[0].text))
    else:
        edits += oc.plan_paragraph_edits(raw, p, [(r.start, r.end, r.text) for r in repls])
    for r in repls:
        if not r.control:
            continue
        owners = [t for t in tokens if t.start < r.end and t.end > r.start]
        anchor: oc.RawNode = owners[0].run if owners and owners[0].run is not None else p
        sdt = next((a for a in anchor.ancestors() if a.name == "sdt"), None)
        if sdt is not None:
            edits += oc.control_placeholder_edits(raw, sdt, owners[0].run if owners else None)
    return edits


def _own_rows(raw: oc.RawPart, tbl: oc.RawNode) -> list[oc.RawNode]:
    out: list[oc.RawNode] = []

    def walk(n: oc.RawNode) -> None:
        for c in n.children:
            if c.name == "tr":
                out.append(c)
            elif c.name != "tbl":
                walk(c)

    walk(tbl)
    return out


def apply(snapshot: bytes, manifest: m.Manifest, compiled: m.Compiled, policy: dict[str, Any]) -> ApplyResult:
    limits = policy.get("limits", {})
    if manifest.blocked:
        raise ApplyRefused("the manifest marks this template as blocked; nothing is filled")
    if m.sha256_bytes(snapshot) != manifest.template.sha256:
        raise ApplyRefused("the snapshot does not match the manifest's template hash")
    pkg = oc.read_package(snapshot, limits)
    para_hash = {(p.part, p.index): p.text_sha256 for p in manifest.paragraphs}
    new_parts = dict(pkg.parts)
    modified: list[str] = []
    notes: list[str] = []

    for part, cp in compiled.parts.items():
        if not (cp.replacements or cp.deleted or cp.repeats or cp.inserts or cp.delete_breaks):
            continue
        if part not in pkg.parts:
            raise ApplyRefused(f"part {part} named in the plan is not in the snapshot")
        if part not in manifest.parts_in_scope:
            raise ApplyRefused(f"part {part} is outside the parts in scope")
        raw = oc.RawPart(pkg.parts[part], part)
        for idx in sorted(cp.touched()):
            if idx >= len(raw.paragraphs):
                raise ApplyRefused(f"{part}: paragraph {idx} does not exist in the snapshot")
            if oc.text_sha256(raw.text(raw.paragraphs[idx])) != para_hash.get((part, idx)):
                raise ApplyRefused(f"{part}: paragraph {idx} no longer matches the manifest (text hash differs)")

        edits: list[oc.Edit] = []
        for idx, repls in cp.replacements.items():
            edits += _replacement_edits(raw, raw.paragraphs[idx], repls)

        repeat_rows: list[tuple[m.RowRepeat, oc.RawNode]] = []
        for rep in cp.repeats:
            if rep.anchor >= len(raw.paragraphs):
                raise ApplyRefused(f"{part}: paragraph {rep.anchor} does not exist in the snapshot")
            tr = raw.row_of(raw.paragraphs[rep.anchor])
            if tr is None:
                raise ApplyRefused(f"{part}: paragraph {rep.anchor} is not in a table row")
            first, last = raw.first_paragraph_in(tr), raw.last_paragraph_in(tr)
            if first is None or last is None or first.index != rep.first or last.index != rep.last:
                raise ApplyRefused(f"{part}: the row of paragraph {rep.anchor} does not match the manifest")
            if rep.copies:
                # Copying the row's bytes would duplicate any identity these constructs carry (a bookmark
                # name, a comment id, a drawing id). There is no safe automatic remapping: a rename breaks
                # cross-references and a duplicate is invalid, so the template must not carry them here.
                clash = raw.identity_constructs_in((tr.start, tr.end))
                if clash:
                    raise ApplyRefused(f"{part}: the repeated row of paragraph {rep.anchor} contains w:{clash[0]}, whose identity "
                                       f"cannot be duplicated; remove it from the template row or fill the row without repeating")
            repeat_rows.append((rep, tr))

        deleted_nodes: list[oc.RawNode] = []
        cleared_nodes: list[oc.RawNode] = []
        for idx in cp.delete_paragraphs:
            p = raw.paragraphs[idx]
            ppr = p.child("pPr")
            if ppr is not None and ppr.child("sectPr") is not None:
                raise ApplyRefused(f"{part}: paragraph {idx} carries a section break and cannot be deleted")
            if p.parent is not None and p.parent.name == "sdtContent" and raw.paragraph_count_in(p.parent) == 1:
                raise ApplyRefused(f"{part}: paragraph {idx} is the only paragraph of a content control; delete a range covering the control instead")
            container, block = raw.real_container(p)
            if container is not None and container.name == "tc" and block is p and raw.paragraph_count_in(container) == 1:
                cleared_nodes.append(p)                             # a cell keeps one (empty) paragraph
                notes.append(f"{part}: paragraph {idx} cleared rather than removed (sole paragraph of its cell)")
                continue
            deleted_nodes.append(p)
        for first, last in cp.delete_ranges:
            a, b = raw.paragraphs[first], raw.paragraphs[last]
            ca, ba = raw.real_container(a)
            cb, bb = raw.real_container(b)
            if ca is None or ca is not cb:
                raise ApplyRefused(f"{part}: paragraphs {first} and {last} are not in the same container")
            siblings = ca.children
            i0, i1 = siblings.index(ba), siblings.index(bb)
            if i0 > i1:
                raise ApplyRefused(f"{part}: range {first}-{last} is reversed")
            deleted_nodes += siblings[i0:i1 + 1]
        for idx in cp.delete_rows:
            tr = raw.row_of(raw.paragraphs[idx])
            if tr is None:
                raise ApplyRefused(f"{part}: paragraph {idx} is not in a table row")
            tbl = next((a for a in tr.ancestors() if a.name == "tbl"), None)
            if tbl is None or len(_own_rows(raw, tbl)) < 2:
                raise ApplyRefused(f"{part}: the table has only one row; remove the table with delete_range instead")
            deleted_nodes.append(tr)
        for node in deleted_nodes:
            for n in [node] + _descendant_paragraphs(node):
                ppr = n.child("pPr") if n.name == "p" else None
                if ppr is not None and ppr.child("sectPr") is not None:
                    raise ApplyRefused(f"{part}: the deleted region contains a section break")
        # Every construct that disappears goes through one check, whichever operation removes it:
        # a deleted block, the content of a cleared paragraph, or a row whose input list is empty.
        removed_regions = [(n.start, n.end) for n in deleted_nodes + cleared_nodes]
        removed_regions += [(tr.start, tr.end) for rep, tr in repeat_rows if not rep.copies]
        if removed_regions:
            problems = raw.markers_in(removed_regions)
            if problems:
                raise ApplyRefused(f"{part}: cannot remove that content: {problems[0]}")
        edits += [oc.clear_paragraph_edit(raw, n) for n in cleared_nodes]
        touched_containers = {raw.real_container(n)[0] for n in deleted_nodes}
        for container in touched_containers:
            if container is None:
                continue
            remaining = [c for c in container.children if c not in deleted_nodes and raw.first_paragraph_in(c) is not None]
            if not remaining:
                what = "table cell" if container.name == "tc" else container.name
                raise ApplyRefused(f"{part}: the deletion would leave a {what} with no paragraph; delete the row or clear the text instead")
        edits += [oc.delete_edit(n) for n in deleted_nodes]

        for rep, tr in repeat_rows:
            copies: list[list[oc.Edit]] = []
            for copy in rep.copies:
                ce: list[oc.Edit] = []
                for idx, repls in copy.items():
                    ce += _replacement_edits(raw, raw.paragraphs[idx], repls)
                copies.append(_dedupe(ce))
            edits.append(oc.repeat_row_edit(raw, tr, copies, budget=int(limits.get("max_part_bytes", 52_428_800))))

        for idx, n in cp.delete_breaks:
            breaks = [t for t in raw.tokens(raw.paragraphs[idx]) if t.kind == "br"]
            if len(breaks) < n:
                raise ApplyRefused(f"{part}: paragraph {idx} has no break number {n}")
            edits.append(oc.delete_edit(breaks[n - 1].node))

        for idx, texts in cp.inserts.items():
            p = raw.paragraphs[idx]
            if p in deleted_nodes or any(p in _descendant_paragraphs(n) for n in deleted_nodes):
                raise ApplyRefused(f"{part}: cannot insert after paragraph {idx}, which is deleted")
            edits.append(oc.insert_after_edit(raw, p, texts))

        try:
            new_data = oc.apply_edits(raw.data, _dedupe(edits))
        except oc.PackageError as exc:
            raise ApplyRefused(f"{part}: {exc}") from exc
        oc.parse_xml(new_data, limits, part)          # a malformed part never leaves the filler
        new_parts[part] = new_data
        modified.append(part)
        notes.append(f"{part}: {sum(len(v) for v in cp.replacements.values())} replacement(s), {len(deleted_nodes)} deletion(s), "
                     f"{len(cp.delete_breaks)} break(s) removed, {len(cp.repeats)} repeated row(s), "
                     f"{sum(len(v) for v in cp.inserts.values())} insertion(s)")

    return ApplyResult(candidate=oc.write_package(pkg, new_parts), parts_modified=modified, notes=notes)


def _descendant_paragraphs(node: oc.RawNode) -> list[oc.RawNode]:
    out: list[oc.RawNode] = []

    def walk(n: oc.RawNode) -> None:
        for c in n.children:
            if c.name == "p":
                out.append(c)
            walk(c)

    walk(node)
    return out


def _dedupe(edits: list[oc.Edit]) -> list[oc.Edit]:
    seen: set[tuple[int, int, bytes]] = set()
    out: list[oc.Edit] = []
    for e in edits:
        key = (e.start, e.end, e.replacement)
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out
