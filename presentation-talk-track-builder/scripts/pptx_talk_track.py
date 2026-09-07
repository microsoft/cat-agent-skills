#!/usr/bin/env python3
"""Extract slide text from a PPTX and write generated speaker notes back.

This helper intentionally uses only the Python standard library so it can run in
restricted agent sandboxes. It reads/writes PPTX packages directly as OOXML zip
files.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import zipfile
from html import escape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}

REL_NOTES_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
REL_NOTES_MASTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster"
REL_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
NOTES_SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"

for prefix, uri in NS.items():
    if prefix not in {"rel", "ct"}:
        ET.register_namespace(prefix, uri)


def natural_slide_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(zf.read(name))


def text_runs(root: ET.Element) -> list[str]:
    return [node.text or "" for node in root.findall(".//a:t", NS)]


def paragraph_xml(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    if not lines:
        lines = [""]
    parts = []
    for line in lines:
        if not line:
            parts.append("<a:p/>")
        else:
            parts.append(
                "<a:p><a:r><a:rPr lang=\"en-US\" dirty=\"0\" smtClean=\"0\"/>"
                f"<a:t>{escape(line)}</a:t></a:r><a:endParaRPr lang=\"en-US\" dirty=\"0\"/></a:p>"
            )
    return "".join(parts)


def get_slide_files(zf: zipfile.ZipFile) -> list[str]:
    slides = [
        name
        for name in zf.namelist()
        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
    ]
    return sorted(slides, key=natural_slide_key)


def slide_rels_path(slide_path: str) -> str:
    slide_name = Path(slide_path).name
    return f"ppt/slides/_rels/{slide_name}.rels"


def notes_rels_path(notes_path: str) -> str:
    notes_name = Path(notes_path).name
    return f"ppt/notesSlides/_rels/{notes_name}.rels"


def extract_deck(pptx: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(pptx, "r") as zf:
        slides = []
        for index, slide_path in enumerate(get_slide_files(zf), start=1):
            slide_root = read_xml(zf, slide_path)
            visible_text = "\n".join(t for t in text_runs(slide_root) if t.strip()).strip()
            title = next((t.strip() for t in text_runs(slide_root) if t.strip()), f"Slide {index}")
            notes_text = ""
            rel_path = slide_rels_path(slide_path)
            if rel_path in zf.namelist():
                rel_root = read_xml(zf, rel_path)
                for rel in rel_root.findall("rel:Relationship", NS):
                    if rel.get("Type") == REL_NOTES_SLIDE:
                        target = rel.get("Target", "")
                        notes_path = "ppt/notesSlides/" + Path(target).name
                        if notes_path in zf.namelist():
                            notes_root = read_xml(zf, notes_path)
                            notes_text = "\n".join(t for t in text_runs(notes_root) if t.strip()).strip()
                        break
            slides.append(
                {
                    "slide": index,
                    "title": title,
                    "visibleText": visible_text,
                    "existingNotes": notes_text,
                    "speakerNotes": "",
                }
            )
        return slides


def load_notes(notes_file: Path) -> dict[int, str]:
    data = json.loads(notes_file.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "slides" in data:
        data = data["slides"]
    if isinstance(data, dict):
        return {int(key): str(value) for key, value in data.items()}
    if isinstance(data, list):
        notes: dict[int, str] = {}
        for item in data:
            if not isinstance(item, dict) or "slide" not in item:
                raise ValueError("Each notes item must include a slide number.")
            text = item.get("speakerNotes") or item.get("notes") or item.get("script") or ""
            notes[int(item["slide"])] = str(text)
        return notes
    raise ValueError("Notes JSON must be an object, a {slides: [...]} object, or a list.")


def next_rid(rel_root: ET.Element) -> str:
    ids = []
    for rel in rel_root.findall("rel:Relationship", NS):
        rid = rel.get("Id", "")
        match = re.fullmatch(r"rId(\d+)", rid)
        if match:
            ids.append(int(match.group(1)))
    return f"rId{(max(ids) if ids else 0) + 1}"


def find_notes_master(zf: zipfile.ZipFile) -> str:
    masters = sorted(
        name for name in zf.namelist() if re.fullmatch(r"ppt/notesMasters/notesMaster\d+\.xml", name)
    )
    if not masters:
        raise RuntimeError(
            "This deck does not contain a notes master. Open and save the deck in PowerPoint, "
            "then rerun this command, or add notes to one slide first."
        )
    return masters[0]


def existing_notes_slide(zf: zipfile.ZipFile, slide_path: str) -> str | None:
    rel_path = slide_rels_path(slide_path)
    if rel_path not in zf.namelist():
        return None
    rel_root = read_xml(zf, rel_path)
    for rel in rel_root.findall("rel:Relationship", NS):
        if rel.get("Type") == REL_NOTES_SLIDE:
            return "ppt/notesSlides/" + Path(rel.get("Target", "")).name
    return None


def make_notes_slide_xml(notes: str) -> bytes:
    xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:notes xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Notes Placeholder 1"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="body" idx="1"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          {paragraph_xml(notes)}
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:notes>
"""
    return xml.encode("utf-8")


def replace_notes_text(xml_bytes: bytes, notes: str) -> bytes:
    root = ET.fromstring(xml_bytes)
    body = None
    for shape in root.findall(".//p:sp", NS):
        placeholder = shape.find(".//p:ph", NS)
        if placeholder is not None and placeholder.get("type") == "body":
            body = shape.find("p:txBody", NS)
            break
    if body is None:
        body = root.find(".//p:txBody", NS)
    if body is None:
        return make_notes_slide_xml(notes)
    for child in list(body):
        if child.tag.endswith("}p"):
            body.remove(child)
    for para in ET.fromstring(f"<root xmlns:a=\"{NS['a']}\">{paragraph_xml(notes)}</root>"):
        body.append(para)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def add_content_type(content_types: bytes, part_name: str) -> bytes:
    root = ET.fromstring(content_types)
    wanted = "/" + part_name
    for override in root.findall("ct:Override", NS):
        if override.get("PartName") == wanted:
            override.set("ContentType", NOTES_SLIDE_CT)
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)
    override = ET.SubElement(root, f"{{{NS['ct']}}}Override")
    override.set("PartName", wanted)
    override.set("ContentType", NOTES_SLIDE_CT)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_notes(pptx: Path, notes_file: Path, output: Path) -> None:
    notes_by_slide = load_notes(notes_file)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(pptx, "r") as source:
            source.extractall(tmp_path)
            slide_files = get_slide_files(source)
            notes_master = find_notes_master(source)

        notes_master_target = f"../notesMasters/{Path(notes_master).name}"

        for slide_index, notes in notes_by_slide.items():
            if slide_index < 1 or slide_index > len(slide_files):
                raise ValueError(f"Slide {slide_index} is outside the deck's slide range.")
            slide_path = slide_files[slide_index - 1]
            slide_abs = tmp_path / slide_path
            rel_path = tmp_path / slide_rels_path(slide_path)
            rel_path.parent.mkdir(parents=True, exist_ok=True)
            if rel_path.exists():
                rel_root = ET.parse(rel_path).getroot()
            else:
                rel_root = ET.Element(f"{{{NS['rel']}}}Relationships")

            notes_path = existing_notes_slide_from_tree(rel_root)
            if notes_path is None:
                notes_path = next_available_notes_path(tmp_path)
                rid = next_rid(rel_root)
                rel = ET.SubElement(rel_root, f"{{{NS['rel']}}}Relationship")
                rel.set("Id", rid)
                rel.set("Type", REL_NOTES_SLIDE)
                rel.set("Target", f"../notesSlides/{Path(notes_path).name}")
            notes_abs = tmp_path / notes_path
            notes_abs.parent.mkdir(parents=True, exist_ok=True)

            if notes_abs.exists():
                notes_abs.write_bytes(replace_notes_text(notes_abs.read_bytes(), notes))
            else:
                notes_abs.write_bytes(make_notes_slide_xml(notes))

            ET.ElementTree(rel_root).write(rel_path, encoding="utf-8", xml_declaration=True)

            notes_rel_abs = tmp_path / notes_rels_path(notes_path)
            notes_rel_abs.parent.mkdir(parents=True, exist_ok=True)
            notes_rel_root = ET.Element(f"{{{NS['rel']}}}Relationships")
            slide_rel = ET.SubElement(notes_rel_root, f"{{{NS['rel']}}}Relationship")
            slide_rel.set("Id", "rId1")
            slide_rel.set("Type", REL_SLIDE)
            slide_rel.set("Target", f"../slides/{slide_abs.name}")
            master_rel = ET.SubElement(notes_rel_root, f"{{{NS['rel']}}}Relationship")
            master_rel.set("Id", "rId2")
            master_rel.set("Type", REL_NOTES_MASTER)
            master_rel.set("Target", notes_master_target)
            ET.ElementTree(notes_rel_root).write(notes_rel_abs, encoding="utf-8", xml_declaration=True)

            ct_path = tmp_path / "[Content_Types].xml"
            ct_path.write_bytes(add_content_type(ct_path.read_bytes(), notes_path))

        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as dest:
            for path in tmp_path.rglob("*"):
                if path.is_file():
                    dest.write(path, path.relative_to(tmp_path).as_posix())


def existing_notes_slide_from_tree(rel_root: ET.Element) -> str | None:
    for rel in rel_root.findall("rel:Relationship", NS):
        if rel.get("Type") == REL_NOTES_SLIDE:
            return "ppt/notesSlides/" + Path(rel.get("Target", "")).name
    return None


def next_available_notes_path(tmp_path: Path) -> str:
    notes_dir = tmp_path / "ppt" / "notesSlides"
    notes_dir.mkdir(parents=True, exist_ok=True)
    used = {
        int(match.group(1))
        for path in notes_dir.glob("notesSlide*.xml")
        if (match := re.fullmatch(r"notesSlide(\d+)\.xml", path.name))
    }
    index = 1
    while index in used:
        index += 1
    return f"ppt/notesSlides/notesSlide{index}.xml"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="Extract slide text to JSON.")
    extract.add_argument("pptx", type=Path)
    extract.add_argument("output_json", type=Path)

    template = sub.add_parser("template", help="Create a notes JSON template from a PPTX.")
    template.add_argument("pptx", type=Path)
    template.add_argument("output_json", type=Path)

    apply = sub.add_parser("apply", help="Write generated notes JSON back into a PPTX.")
    apply.add_argument("pptx", type=Path)
    apply.add_argument("notes_json", type=Path)
    apply.add_argument("output_pptx", type=Path)

    args = parser.parse_args(argv)

    if args.command in {"extract", "template"}:
        slides = extract_deck(args.pptx)
        args.output_json.write_text(
            json.dumps({"slides": slides}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return 0

    if args.command == "apply":
        if args.output_pptx.resolve() == args.pptx.resolve():
            backup = args.pptx.with_suffix(".backup.pptx")
            shutil.copy2(args.pptx, backup)
        write_notes(args.pptx, args.notes_json, args.output_pptx)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
