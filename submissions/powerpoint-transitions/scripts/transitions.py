"""Inspect or apply native slide transitions. Python 3.9+, no third-party packages."""

import argparse
import copy
import hashlib
import json
import posixpath
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple, Optional
from urllib.parse import unquote
from xml.dom import Node, minidom
from xml.parsers.expat import ExpatError
from zipfile import BadZipFile, ZipFile


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
MORPH = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
DIRECTIONS = {"left": "l", "right": "r", "up": "u", "down": "d"}
DURATIONS = {"fade": 350, "push": 500, "wipe": 450, "morph": 800}


def elements(node):
    return [child for child in node.childNodes if child.nodeType == Node.ELEMENT_NODE]


def is_tag(node, ns, name):
    return (node.namespaceURI, node.localName) == (ns, name)


def read_part(package, path):
    doc = minidom.parseString(package.read(path))
    if doc.doctype is not None:
        raise ValueError(f"Unexpected DTD in {path}")
    return doc


def slide_order(package, editing):
    names = package.namelist()
    if len(set(names)) != len(names):
        raise ValueError("Ambiguous duplicate ZIP members")
    pres = read_part(package, "ppt/presentation.xml")
    if not is_tag(pres.documentElement, P, "presentation"):
        raise ValueError("Expected a standard transitional .pptx. Use the PowerPoint UI for this file.")
    if editing:
        types = read_part(package, "[Content_Types].xml")
        main_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
        if not any(n.getAttribute("PartName") == "/ppt/presentation.xml" and
                   n.getAttribute("ContentType") == main_type
                   for n in elements(types.documentElement)):
            raise ValueError("Only ordinary .pptx presentations are editable")
        if (any(n.lower().startswith("_xmlsignatures/") for n in names)
                or pres.getElementsByTagNameNS(P, "modifyVerifier")):
            raise ValueError("Signed or edit-protected presentation: use the authorized PowerPoint workflow")
    rels = read_part(package, "ppt/_rels/presentation.xml.rels")
    targets = {n.getAttribute("Id"): n.getAttribute("Target")
               for n in elements(rels.documentElement)
               if n.getAttribute("Type") == R + "/slide" and n.getAttribute("TargetMode") != "External"}
    order = []
    for lst in elements(pres.documentElement):
        if is_tag(lst, P, "sldIdLst"):
            for n in elements(lst):
                if is_tag(n, P, "sldId"):
                    target = targets[n.getAttributeNS(R, "id")]
                    path = posixpath.normpath(posixpath.join("ppt", target)).lstrip("/")
                    package.getinfo(path)
                    order.append(path)
    if not order or len(order) != len(set(order)):
        raise ValueError("Missing or ambiguous slide order")
    return order


def transition_block(root):
    blocks = [e for e in elements(root) if is_tag(e, P, "transition") or
              (is_tag(e, MC, "AlternateContent") and e.getElementsByTagNameNS(P, "transition"))]
    if len(blocks) > 1:
        raise ValueError("Multiple transition blocks on a single slide")
    return blocks[0] if blocks else None


def branches(block):
    if block is None:
        return []
    if is_tag(block, P, "transition"):
        return [block]
    result = []
    for branch in elements(block):
        kids = elements(branch)
        if (branch.namespaceURI != MC or branch.localName not in ("Choice", "Fallback")
                or len(kids) != 1 or not is_tag(kids[0], P, "transition")):
            raise ValueError("A transition shares its compatibility block with other slide content")
        result.append(kids[0])
    return result


def advances(node):
    return {k: node.getAttribute(k) for k in ("advClick", "advTm") if node.hasAttribute(k)}


def existing_settings(block):
    settings = None
    for node in branches(block):
        if any(c.localName in ("sndAc", "extLst") or is_tag(c, MC, "AlternateContent")
               for c in elements(node)):
            raise ValueError("Transition contains sound, extensions or nested choices; edit it in PowerPoint")
        for attr in node.attributes.values():
            if not (attr.namespaceURI == "http://www.w3.org/2000/xmlns/" or
                    (attr.namespaceURI, attr.localName) == (P14, "dur") or
                    (not attr.namespaceURI and attr.name in ("spd", "advClick", "advTm"))):
                raise ValueError(f"Unsupported existing transition attribute: {attr.name}")
        advance = advances(node)
        if settings is not None and settings != advance:
            raise ValueError("Advance settings differ between viewer versions; edit this slide in PowerPoint")
        settings = advance
    return settings or {}


def make_block(item, settings):
    effect = item["effect"]
    if effect == "none" and not settings:
        return None
    # Mirror PowerPoint's Choice/Fallback structure; keep all new prefixes locally scoped.
    doc = minidom.Document()

    def tag(ns, name, attrs=None):
        e = doc.createElementNS(ns, name)
        for key, value in (attrs or {}).items():
            e.setAttribute(key, value)
        return e

    if effect == "none":
        return tag(P, "p:transition", {"xmlns:p": P, **settings})
    ms = item.get("ms", DURATIONS[effect])
    speed = "fast" if ms <= 500 else "med" if ms <= 750 else "slow"
    ac = tag(MC, "mc:AlternateContent", {"xmlns:mc": MC, "xmlns:p": P})
    choice = tag(MC, "mc:Choice", {"xmlns:p14": P14, "Requires": "p159" if effect == "morph" else "p14"})
    if effect == "morph":
        choice.setAttribute("xmlns:p159", MORPH)
    for modern, branch in ((True, choice), (False, tag(MC, "mc:Fallback"))):
        ac.appendChild(branch)
        trans = tag(P, "p:transition", {"spd": speed, **settings})
        if modern:
            trans.setAttributeNS(P14, "p14:dur", str(ms))
        branch.appendChild(trans)
        if effect == "morph":
            fx = tag(MORPH, "p159:morph", {"option": "byObject"}) if modern else tag(P, "p:fade")
        else:
            attrs = {"dir": DIRECTIONS[item["direction"]]} if effect in ("push", "wipe") else {}
            fx = tag(P, "p:" + effect, attrs)
        trans.appendChild(fx)
    return ac


def replace_transition(doc, item):
    root = doc.documentElement
    if not any(is_tag(c, P, "cSld") for c in elements(root)):
        raise ValueError("Nonstandard slide content; apply the transition in PowerPoint")
    old = transition_block(root)
    new = make_block(item, existing_settings(old))
    if new is not None:
        new = doc.importNode(new, True)
        following = old or next((c for c in elements(root)
                                 if not (is_tag(c, P, "cSld") or is_tag(c, P, "clrMapOvr"))), None)
        root.insertBefore(new, following)
    if old is not None:
        root.removeChild(old)


def shape_names(root):
    for n in root.getElementsByTagNameNS(P, "cNvPr"):
        owner = n.parentNode.parentNode
        if owner.localName != "spTree":
            yield n, owner


def child(parent, ns, name):
    return next((e for e in elements(parent) if is_tag(e, ns, name)), None) if parent else None


class SlideInventory(NamedTuple):
    objects: dict
    names: Counter
    hidden: bool
    blocked: Optional[str]


def inventory(package, path, hashes):
    doc = read_part(package, path)
    root = doc.documentElement
    names = list(shape_names(root))
    counts = Counter(n.getAttribute("name") for n, _ in names)
    directory, filename = posixpath.split(path)
    rel_path = posixpath.join(directory, "_rels", filename + ".rels")
    images = {}
    if rel_path in package.NameToInfo:
        for r in elements(read_part(package, rel_path).documentElement):
            if r.getAttribute("Type") == R + "/image" and r.getAttribute("TargetMode") != "External":
                images[r.getAttribute("Id")] = posixpath.normpath(posixpath.join(
                    directory, unquote(r.getAttribute("Target")))).lstrip("/")
    objects = {}
    for n, owner in names:
        name, kind = n.getAttribute("name"), owner.localName
        if (kind not in ("sp", "pic") or not is_tag(owner.parentNode, P, "spTree")
                or not name.strip() or counts[name] != 1 or n.getAttribute("hidden") in ("1", "true")
                or owner.getElementsByTagNameNS(P, "ph")):
            continue
        props = child(owner, P, "spPr")
        xfrm = child(props, A, "xfrm")
        off, ext = child(xfrm, A, "off"), child(xfrm, A, "ext")
        if off is None or ext is None:
            continue
        geom = (int(off.getAttribute("x")), int(off.getAttribute("y")), int(ext.getAttribute("cx")),
                int(ext.getAttribute("cy")), int(xfrm.getAttribute("rot") or 0) % 21600000)
        keys = {}
        if name.startswith("!!") and name[2:].strip():
            keys["binding"] = name
        elif not re.search(r"\d\s*$", name) and not re.fullmatch(
                r"(shape|rectangle|oval|ellipse|picture|image|text\s?box|text|title|placeholder)", name, re.I):
            keys["name"] = name
        if kind == "pic":
            if any(owner.getElementsByTagNameNS(A, tag) for tag in ("videoFile", "audioFile", "quickTimeFile")):
                continue
            blip = child(child(owner, P, "blipFill"), A, "blip")
            if blip is None or blip.hasAttributeNS(R, "link"):
                continue
            svg = blip.getElementsByTagNameNS("*", "svgBlip")
            media = images.get((svg[0] if svg else blip).getAttributeNS(R, "embed"))
            if media is None:
                continue
            if media not in hashes:
                hashes[media] = hashlib.sha256(package.read(media)).hexdigest()
            keys["image"] = hashes[media]
        else:
            body = child(owner, P, "txBody")
            paragraphs = body.getElementsByTagNameNS(A, "p") if body else []
            text = " ".join("".join(c.data for t in p.getElementsByTagNameNS(A, "t")
                                    for c in t.childNodes if c.nodeType == Node.TEXT_NODE) for p in paragraphs)
            text = " ".join(text.casefold().split())
            if text and any(c.isalpha() for c in text):
                keys["text"] = text
            preset = child(props, A, "prstGeom")
            color = child(child(props, A, "solidFill"), A, "srgbClr")
            if not text and preset and color:
                keys["appearance"] = (preset.getAttribute("prst"), color.getAttribute("val"))
        objects[name] = (kind, keys, geom)
    blocked = None
    try:
        existing_settings(transition_block(root))
    except ValueError as exc:
        blocked = str(exc)
    return SlideInventory(objects, counts, root.getAttribute("show") in ("0", "false"), blocked)


def changes(a, b):
    result = []
    for label, lo, hi in (("move", 0, 2), ("resize", 2, 4)):
        if any(abs(a[j] - b[j]) >= 22860 for j in range(lo, hi)):  # 0.025 inch
            result.append(label)
    angle = abs(a[4] - b[4])
    if min(angle, 21600000 - angle) >= 60000:
        result.append("rotate")
    return result


def signal_index(objects):
    index = defaultdict(list)
    for name, (kind, keys, _) in objects.items():
        for signal, value in keys.items():
            index[kind, signal, value].append(name)
    return index


def compare(package, order):
    """Propose one-to-one, moving pairs; never infer identity from proximity."""
    plan, reports, hashes = [], [], {}
    left = inventory(package, order[0], hashes)
    carry = {}
    for i, path in enumerate(order[1:], 2):
        right = inventory(package, path, hashes)
        source, target = left.objects, right.objects
        report = {"from_slide": i - 1, "to_slide": i, "matches": [], "review": []}
        reports.append(report)
        anchors, next_carry = [], {}
        if left.hidden or right.hidden or right.blocked:
            report["skipped"] = "Hidden slide in pair" if left.hidden or right.hidden else right.blocked
        else:
            src_keys, dst_keys = signal_index(source), signal_index(target)
            edges, outgoing, incoming = defaultdict(list), defaultdict(set), defaultdict(set)
            ambiguous = 0
            for key, src in src_keys.items():
                dst = dst_keys.get(key, [])
                if len(src) == len(dst) == 1:
                    a, b = src[0], dst[0]
                    edges[a, b].append(key[1])
                    outgoing[a].add(b)
                    incoming[b].add(a)
                elif dst:
                    ambiguous += 1
                    if ambiguous <= 5:
                        report.setdefault("nonunique_examples", []).append(
                            {"evidence": key[1], "from": src[:5], "to": dst[:5]})
            if ambiguous:
                report["nonunique_signals_ignored"] = ambiguous
            reserved = set(left.names) | set(right.names) | set(carry.values())
            for (a, b), evidence in edges.items():
                motion = changes(source[a][2], target[b][2])
                if not motion:
                    continue
                result = {"from": a, "to": b, "changes": motion, "evidence": evidence}
                keys_a, keys_b = source[a][1], target[b][1]
                bound = {n for n in (carry.get(a, ""), a, b) if n.startswith("!!")}
                if len(outgoing[a]) > 1 or len(incoming[b]) > 1:
                    reason = "Identity signals point to different objects"
                elif len(bound) > 1:
                    reason = "Existing Morph names conflict"
                elif evidence == ["appearance"]:
                    reason = "Only shape and color agree; confirm the pair"
                elif "binding" not in evidence and any(
                        k in keys_a and k in keys_b and keys_a[k] != keys_b[k] for k in ("image", "text")):
                    reason = "Name matches but the content differs"
                else:
                    reason = None
                if bound:
                    name = min(bound)
                    if ((name in left.names and name != a) or (name in right.names and name != b)
                            or (name in carry.values() and carry.get(a) != name)):
                        reason = "Morph name already belongs to another object"
                else:
                    name = f"!!motion-{i}-{len(anchors) + 1}"
                    while name in reserved:
                        name += "-"
                if reason:
                    report["review"].append({**result, "reason": reason})
                    continue
                reserved.add(name)
                next_carry[b] = name
                anchors.append({"from": a, "to": b, "name": name})
                report["matches"].append({**result, "name": name})
        if anchors:
            plan.append({"slide": i, "effect": "morph", "ms": DURATIONS["morph"], "anchors": anchors})
        left, carry = right, next_carry
    return {"pairs": reports, "plan": plan}


def bind_pair(left, right, anchor, originals=None):
    if isinstance(anchor, str):
        anchor = {"from": anchor, "to": anchor, "name": anchor}
    if not isinstance(anchor, dict) or set(anchor) != {"from", "to", "name"} or not all(
            isinstance(v, str) and v.strip() for v in anchor.values()):
        raise ValueError("Morph needs an anchor name or {from, to, name}")
    name = anchor["name"]
    if not name.startswith("!!") or not name[2:].strip() or not name.isprintable():
        raise ValueError("Morph pair name must begin with !! and have a nonempty, printable label")
    kinds = []
    for doc, key in ((left, "from"), (right, "to")):
        root = doc.documentElement
        if root.getAttribute("show") in ("0", "false"):
            raise ValueError("Morph across hidden slides requires manual preview; use Fade or edit in PowerPoint")
        names = list(shape_names(root))
        current = anchor[key]
        found = [(n, owner) for n, owner in names
                 if (originals[n] if originals is not None else n.getAttribute("name")) == current]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one {current!r} on the {key} slide, found {len(found)}")
        n, owner = found[0]
        current = n.getAttribute("name")
        if owner.localName not in ("sp", "pic") or not is_tag(owner.parentNode, P, "spTree"):
            raise ValueError("Choose a top-level shape or picture as the Morph anchor")
        if current != name and (current.startswith("!!") or
                                any(other.getAttribute("name") == name for other, _ in names)):
            raise ValueError(f"Conflicting Morph binding for {current!r} / {name!r}")
        if current != name:
            n.setAttribute("name", name)
        kinds.append(owner.localName)
    if kinds[0] != kinds[1]:
        raise ValueError("Choose two shapes or two pictures, not a mixed Morph pair")


def validate_plan(plan, count, mode):
    if not isinstance(plan, list) or not plan:
        raise ValueError("Plan must be a nonempty JSON list")
    seen = set()
    for item in plan:
        if not isinstance(item, dict):
            raise ValueError("Each plan entry must be an object")
        i, effect = item.get("slide"), item.get("effect")
        if type(i) is not int or not 1 <= i <= count or i in seen:
            raise ValueError(f"Invalid or duplicate destination: {i!r} (deck has {count} slides)")
        seen.add(i)
        if not isinstance(effect, str) or effect not in (*DURATIONS, "none"):
            raise ValueError(f"Slide {i}: unknown effect {effect!r}")
        allowed = {"slide", "effect"}
        if effect != "none":
            allowed.add("ms")
            ms = item.get("ms", DURATIONS[effect])
            if type(ms) is not int or not 100 <= ms <= 5000:
                raise ValueError(f"Slide {i}: duration must be an integer from 100 to 5000 ms")
        if effect in ("push", "wipe"):
            allowed.add("direction")
            if not isinstance(item.get("direction"), str) or item["direction"] not in DIRECTIONS:
                raise ValueError(f"Slide {i}: specify travel direction: {', '.join(DIRECTIONS)}")
        if effect == "morph":
            allowed.update(("anchor", "anchors"))
            if i == 1 or ("anchor" in item) == ("anchors" in item):
                raise ValueError(f"Slide {i}: Morph needs a previous slide and either anchor or anchors")
            if "anchors" in item:
                anchors = item["anchors"]
                if not isinstance(anchors, list) or not anchors or not all(
                        isinstance(a, dict) and set(a) == {"from", "to", "name"}
                        and all(isinstance(v, str) and v.strip() for v in a.values()) for a in anchors):
                    raise ValueError(f"Slide {i}: anchors must be a nonempty list of {{from, to, name}}")
                for key in ("from", "to", "name"):
                    if len({a[key] for a in anchors}) != len(anchors):
                        raise ValueError(f"Slide {i}: object matches must be one-to-one; repeated {key}")
        if mode == "classic" and "anchors" in item:
            raise ValueError(f"Slide {i}: matched objects require --mode objects or --mode both")
        if mode == "objects" and (effect != "morph" or "anchors" not in item):
            raise ValueError(f"Slide {i}: objects-only mode accepts only matched-object Morph entries")
        if set(item) - allowed:
            raise ValueError(f"Slide {i}: unexpected keys {sorted(set(item) - allowed)}")


def inspect(package, order, selected):
    if selected is not None and not 1 <= selected <= len(order):
        raise ValueError(f"Slide must be in 1..{len(order)}")
    for i, path in enumerate(order, 1):
        if selected is not None and i != selected:
            continue
        doc = read_part(package, path)
        root = doc.documentElement
        values = branches(transition_block(root))
        effects = []
        for v in values:
            fx = next((e for e in elements(v) if e.localName not in ("sndAc", "extLst")), None)
            effects.append({"effect": fx.localName if fx is not None else "none",
                            "dir": fx.getAttribute("dir") if fx is not None else "",
                            "ms": v.getAttributeNS(P14, "dur") or None, **advances(v)})
        text = [c.data for t in doc.getElementsByTagNameNS(A, "t") for c in t.childNodes
                if c.nodeType == Node.TEXT_NODE]
        record = {"slide": i, "hidden": root.getAttribute("show") in ("0", "false"),
                  "text": " | ".join(text)[:240], "transition_branches": effects or [{"effect": "none"}]}
        if selected is not None:
            record["shapes"] = [{"name": n.getAttribute("name"), "type": owner.localName}
                                for n, owner in shape_names(root)]
        print(json.dumps(record, ensure_ascii=True))


def apply(package, order, plan, output, mode="classic"):
    validate_plan(plan, len(order), mode)
    docs = {}
    originals = {}

    def slide(i):
        path = order[i - 1]
        if path not in docs:
            docs[path] = read_part(package, path)
            if mode != "classic":
                originals.update((n, n.getAttribute("name")) for n, _ in shape_names(docs[path].documentElement))
        return docs[path]

    for item in sorted(plan, key=lambda x: x["slide"]):
        i = item["slide"]
        try:
            if item["effect"] == "morph":
                left, right = slide(i - 1), slide(i)
                if "anchors" in item:
                    for anchor in item["anchors"]:
                        bind_pair(left, right, anchor, originals)
                else:
                    bind_pair(left, right, item["anchor"])
            replace_transition(slide(i), item)
        except ValueError as exc:
            raise ValueError(f"Slide {i}: {exc}") from exc

    # Reserve the output exclusively; remove only our own incomplete output on error.
    done = False
    with output.open("xb") as file:
        try:
            with ZipFile(file, "w") as out:
                out.comment = package.comment
                for info in package.infolist():
                    dest = copy.copy(info)
                    if info.filename in docs:
                        out.writestr(dest, docs[info.filename].toxml(encoding="UTF-8"))
                    else:
                        with package.open(info) as src, out.open(dest, "w") as dst:
                            shutil.copyfileobj(src, dst)
            done = True
        finally:
            if not done:
                file.close()
                output.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    show = sub.add_parser("inspect")
    show.add_argument("input", type=Path)
    show.add_argument("--slide", type=int)
    match = sub.add_parser("compare", help="Read-only comparison of objects on neighboring slides")
    match.add_argument("input", type=Path)
    match.add_argument("--plan", type=Path, help="Save eligible Morph entries to a NEW JSON file")
    edit = sub.add_parser("apply")
    edit.add_argument("input", type=Path)
    edit.add_argument("plan", type=Path)
    edit.add_argument("output", type=Path)
    edit.add_argument("--mode", choices=("classic", "objects", "both"), default="classic")
    args = parser.parse_args()
    editing = args.action == "apply"
    try:
        if args.input.suffix.lower() != ".pptx" or (editing and args.output.suffix.lower() != ".pptx"):
            raise ValueError("Expected .pptx file paths")
        with ZipFile(args.input) as package:
            order = slide_order(package, editing)
            if editing:
                plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
                apply(package, order, plan, args.output, args.mode)
                print(f"Wrote {args.output} ({len(plan)} planned transitions)")
            elif args.action == "compare":
                report = compare(package, order)
                if args.plan:
                    with args.plan.open("x", encoding="utf-8") as file:
                        json.dump(report["plan"], file, indent=2)
                print(json.dumps(report, indent=2))
            else:
                inspect(package, order, args.slide)
    except (OSError, KeyError, ValueError, BadZipFile, ExpatError, NotImplementedError) as exc:
        sys.exit(f"Transition editor: {exc}")


if __name__ == "__main__":
    main()
