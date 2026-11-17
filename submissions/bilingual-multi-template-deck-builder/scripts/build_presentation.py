#!/usr/bin/env python3
"""Generate a new editable PPTX from bundled reference slides, without URL import."""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
import posixpath
import re
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from xml.parsers.expat import ExpatError

VERSION = "1.0.0"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
MISSING = object()
BOUNDARY = re.compile(r"(?<=[\u0590-\u05ff])(?=[A-Za-z])|(?<=[A-Za-z])(?=[\u0590-\u05ff])")
PROTECTED = re.compile(r"(https?://\S+|www\.\S+|[^\s@]+@[^\s@]+)", re.I)
# Boundary spaces belong to the surrounding RTL text, not the LTR phrase.
LTR = re.compile(r"https?://\S+|www\.\S+|[^\s@]+@[^\s@]+|"
                 r"[+-]?[A-Za-z0-9][A-Za-z0-9 \t%+:/@&()_'=.,-]*(?<![ \t])", re.I)
MUTABLE = ("ppt/slides/", "ppt/notesSlides/", "ppt/charts/",
           "ppt/embeddings/", "ppt/diagrams/")
DESIGN = ("ppt/slideMasters/", "ppt/slideLayouts/", "ppt/theme/", "ppt/fonts/")


def require(condition, message):
    if not condition:
        raise ValueError(message)

def parseString(data):
    from defusedxml.minidom import parseString as safe_parse
    return safe_parse(data)


def read_package(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        require(archive.testzip() is None, "PPTX ZIP integrity check failed")
        require(sum(entry.file_size for entry in archive.infolist()) <= 64 * 1024 * 1024,
                "PPTX exceeds the supported expanded size")
        parts = {}
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            name = entry.filename
            require(not name.startswith("/") and "\\" not in name
                    and posixpath.normpath(name) == name and not name.startswith("../")
                    and not re.match(r"^[A-Za-z]:", name), "Unsafe PPTX part name")
            require(name not in parts, f"Duplicate PPTX package part: {name}")
            parts[name] = archive.read(entry)
    require("ppt/presentation.xml" in parts, "Not a supported, unencrypted PPTX")
    require(not any(name.startswith("_xmlsignatures/") for name in parts),
            "Digitally signed presentations require a signature-aware workflow")
    return parts


def pack(parts):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
    return output.getvalue()


def relationship_part(owner):
    return (posixpath.join(posixpath.dirname(owner), "_rels",
                          posixpath.basename(owner) + ".rels") if owner else "_rels/.rels")


def resolve(owner, target):
    return (target.lstrip("/") if target.startswith("/") else
            posixpath.normpath(posixpath.join(posixpath.dirname(owner), target)))


def children(document, namespace, name):
    return list(document.getElementsByTagNameNS(namespace, name))


def source_slides(parts):
    presentation = parseString(parts["ppt/presentation.xml"])
    relationships = parseString(parts["ppt/_rels/presentation.xml.rels"])
    targets = {node.getAttribute("Id"): resolve("ppt/presentation.xml", node.getAttribute("Target"))
               for node in children(relationships, R, "Relationship")}
    return [targets[node.getAttributeNS(OFFICE_R, "id")]
            for node in children(presentation, P, "sldId")]


class SlideCopies:
    """Clone mutable slide dependencies while sharing immutable template design."""

    def __init__(self, source):
        self.source = source
        self.parts = dict(source)
        self.types = parseString(source["[Content_Types].xml"])
        self.overrides = {
            node.getAttribute("PartName").lstrip("/"): node.getAttribute("ContentType")
            for node in children(self.types, CT, "Override")
        }

    def fresh_name(self, source_name):
        directory, filename = posixpath.split(source_name)
        stem, extension = posixpath.splitext(filename)
        stem = re.sub(r"\d+$", "", stem)
        number = 1
        while posixpath.join(directory, f"{stem}{number}{extension}") in self.parts:
            number += 1
        return posixpath.join(directory, f"{stem}{number}{extension}")

    def clone(self, source_name, memo):
        if source_name in memo:
            return memo[source_name]
        require(source_name in self.source, f"Missing related template part: {source_name}")
        destination = self.fresh_name(source_name)
        memo[source_name] = destination
        self.parts[destination] = self.source[source_name]
        if source_name in self.overrides:
            node = self.types.createElementNS(CT, "Override")
            node.setAttribute("PartName", "/" + destination)
            node.setAttribute("ContentType", self.overrides[source_name])
            self.types.documentElement.appendChild(node)
        relationships_name = relationship_part(source_name)
        if relationships_name in self.source:
            relationships = parseString(self.source[relationships_name])
            for node in children(relationships, R, "Relationship"):
                if node.getAttribute("TargetMode") == "External":
                    continue
                target = resolve(source_name, node.getAttribute("Target"))
                if target.startswith(MUTABLE):
                    target = self.clone(target, memo)
                node.setAttribute("Target", posixpath.relpath(target, posixpath.dirname(destination)))
            self.parts[relationship_part(destination)] = relationships.toxml(encoding="UTF-8")
        return destination

    def create(self, reference_indices):
        slides = source_slides(self.source)
        presentation = parseString(self.source["ppt/presentation.xml"])
        relationships = parseString(self.source["ppt/_rels/presentation.xml.rels"])
        slide_list = children(presentation, P, "sldIdLst")[0]
        for node in list(slide_list.childNodes):
            slide_list.removeChild(node)
        all_relationships = children(relationships, R, "Relationship")
        highest = max((int(node.getAttribute("Id")[3:]) for node in all_relationships
                       if re.fullmatch(r"rId\d+", node.getAttribute("Id"))), default=0)
        for node in all_relationships:
            if node.getAttribute("Type") == OFFICE_R + "/slide":
                node.parentNode.removeChild(node)
        for index, reference in enumerate(reference_indices, 1):
            require(isinstance(reference, int) and not isinstance(reference, bool)
                    and 1 <= reference <= len(slides), "Invalid reference slide index")
            new_slide = self.clone(slides[reference - 1], {})
            identifier = f"rId{highest + index}"
            relationship = relationships.createElementNS(R, "Relationship")
            for name, value in {
                "Id": identifier, "Type": OFFICE_R + "/slide",
                "Target": posixpath.relpath(new_slide, "ppt"),
            }.items():
                relationship.setAttribute(name, value)
            relationships.documentElement.appendChild(relationship)
            slide_id = presentation.createElementNS(P, "p:sldId")
            slide_id.setAttribute("id", str(255 + index))
            slide_id.setAttributeNS(OFFICE_R, "r:id", identifier)
            slide_list.appendChild(slide_id)
        for node in children(presentation, P, "custShowLst"):
            node.parentNode.removeChild(node)
        for node in list(presentation.getElementsByTagName("*")):
            if node.localName == "sectionLst":
                node.parentNode.removeChild(node)
        self.parts["ppt/presentation.xml"] = presentation.toxml(encoding="UTF-8")
        self.parts["ppt/_rels/presentation.xml.rels"] = relationships.toxml(encoding="UTF-8")
        self.parts["[Content_Types].xml"] = self.types.toxml(encoding="UTF-8")
        return self.pruned()

    def pruned(self):
        keep = {"[Content_Types].xml"}
        queue = [""]
        seen = set()
        while queue:
            owner = queue.pop()
            if owner in seen:
                continue
            seen.add(owner)
            if owner:
                require(owner in self.parts, f"Broken package relationship: {owner}")
                keep.add(owner)
            rel_name = relationship_part(owner)
            if rel_name not in self.parts:
                continue
            keep.add(rel_name)
            document = parseString(self.parts[rel_name])
            for node in children(document, R, "Relationship"):
                if node.getAttribute("TargetMode") != "External":
                    queue.append(resolve(owner, node.getAttribute("Target")))
        for node in list(children(self.types, CT, "Override")):
            if node.getAttribute("PartName").lstrip("/") not in keep:
                node.parentNode.removeChild(node)
        self.parts["[Content_Types].xml"] = self.types.toxml(encoding="UTF-8")
        return {name: data for name, data in self.parts.items() if name in keep}


def load_config(root):
    config = json.loads((root / "references" / "templates.json").read_text(encoding="utf-8-sig"))
    require(config.get("schema_version") == 1, "Unsupported template manifest schema")
    for key, profile in config["templates"].items():
        require(profile.get("language") in {"en", "he"}, f"Unsupported language: {key}")
        require(profile.get("direction") == ("rtl" if profile["language"] == "he" else "ltr"),
                f"Language/direction mismatch in profile: {key}")
        require(isinstance(profile.get("layouts"), dict) and profile["layouts"],
                f"No reference layouts configured: {key}")
        for layout_name, layout in profile["layouts"].items():
            require(isinstance(layout.get("reference_slide"), int)
                    and not isinstance(layout["reference_slide"], bool)
                    and layout["reference_slide"] >= 1, f"Invalid reference slide: {layout_name}")
            require(isinstance(layout.get("fields"), dict), f"Invalid fields: {layout_name}")
            for binding in layout["fields"].values():
                require(binding.get("type") in {"text", "chart", "table"}
                        and isinstance(binding.get("shape"), str) and binding["shape"],
                        f"Invalid shape binding: {layout_name}")
        file = (root / profile["asset"]).resolve(strict=True)
        require(file.is_relative_to(root.resolve()), f"Template path escapes skill folder: {key}")
        require(hashlib.sha256(file.read_bytes()).hexdigest() == profile["sha256"],
                f"Template integrity mismatch: {key}; review the file and update its manifest explicitly")
    return config


def lookup(data, path):
    current = data
    for component in path.split("."):
        if isinstance(current, dict) and component in current:
            current = current[component]
        elif isinstance(current, list) and component.isdigit() and int(component) < len(current):
            current = current[int(component)]
        else:
            return MISSING
    return current


def leaves(data, prefix=""):
    if isinstance(data, dict):
        if not data:
            yield prefix
        for key, value in data.items():
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(data, list):
        if not data:
            yield prefix
        for index, value in enumerate(data):
            yield from leaves(value, f"{prefix}.{index}")
    else:
        yield prefix


def validate_plan(plan, profile):
    require(isinstance(plan, dict) and set(plan) == {"language", "slides"},
            "Plan needs exactly language and slides")
    require(plan["language"] == profile["language"], "Plan language does not match the template")
    require(isinstance(plan["slides"], list) and 1 <= len(plan["slides"]) <= 80,
            "slides must contain 1 to 80 entries")
    for index, specification in enumerate(plan["slides"], 1):
        require(isinstance(specification, dict), f"Slide {index} must be an object")
        layout = profile["layouts"].get(specification.get("layout"))
        require(layout is not None, f"Slide {index}: unknown layout")
        fields = layout["fields"]
        allowed = {"layout", "notes", *fields}
        for path in leaves(specification):
            require(any(path == name or path.startswith(name + ".") for name in allowed),
                    f"Slide {index}: unbound content field {path}")
        for path, binding in fields.items():
            value = lookup(specification, path)
            require(value is not MISSING or not binding.get("required", False),
                    f"Slide {index}: missing required field {path}")
            if value is not MISSING and binding["type"] == "text":
                require(isinstance(value, str), f"Slide {index}: {path} must be text")
                require(not binding.get("required", False) or value.strip(),
                        f"Slide {index}: required text is empty: {path}")
                require(len(value) <= binding.get("max_length", 600),
                        f"Slide {index}: {path} is too long; split the content")
        if "notes" in specification:
            require(isinstance(specification["notes"], str), "notes must be text")


def display_runs(text, rtl):
    if not rtl:
        return [(text, True)]
    text = "".join(part if index % 2 else BOUNDARY.sub(" ", part)
                   for index, part in enumerate(PROTECTED.split(text)))
    output, start = [], 0
    for match in LTR.finditer(text):
        if match.start() > start:
            output.append((text[start:match.start()], False))
        output.append((match.group(0), True))
        start = match.end()
    if start < len(text):
        output.append((text[start:], False))
    return output or [("", False)]


def fill_text(frame, value, rtl):
    from pptx.enum.text import PP_ALIGN
    from pptx.oxml.xmlchemy import OxmlElement
    prototype = frame.paragraphs[0]
    original_alignment = prototype.alignment
    paragraph_style = copy.deepcopy(prototype._p.pPr)
    run_style = next((copy.deepcopy(run._r.rPr) for run in prototype.runs
                      if run._r.rPr is not None), None)
    frame.clear()
    frame._txBody.bodyPr.set("rtlCol", "1" if rtl else "0")
    for index, line in enumerate(value.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.clear()
        if paragraph_style is not None:
            existing = paragraph._p.pPr
            if existing is not None:
                paragraph._p.remove(existing)
            paragraph._p.insert(0, copy.deepcopy(paragraph_style))
        paragraph.alignment = (original_alignment if original_alignment is not None
                               else PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT)
        paragraph_rtl = rtl and any(unicodedata.bidirectional(char) in {"R", "AL"} for char in line)
        paragraph._p.get_or_add_pPr().set("rtl", "1" if paragraph_rtl else "0")
        for text, ltr in display_runs(line, rtl):
            run = paragraph.add_run()
            run.text = text
            if text and (text[0].isspace() or text[-1].isspace()):
                run._r.t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            properties = run._r.get_or_add_rPr()
            if run_style is not None:
                properties = copy.deepcopy(run_style)
                run._r.replace(run._r.rPr, properties)
            properties.set("lang", "en-US" if ltr else "he-IL")
            direction = properties.find(f"{{{A}}}rtl")
            if direction is None:
                direction = OxmlElement("a:rtl")
                extension = properties.find(f"{{{A}}}extLst")
                properties.insert(list(properties).index(extension) if extension is not None
                                  else len(properties), direction)
            direction.set("val", "0" if ltr else "1")


def update_chart(shape, value):
    from pptx.chart.axis import ValueAxis
    from pptx.chart.data import CategoryChartData
    from pptx.chart.datalabel import DataLabels
    require(shape.has_chart and isinstance(value, dict), "Chart binding requires a chart payload")
    require(set(value) == {"categories", "series", "number_format"},
            "Chart requires categories, series and explicit number_format")
    categories, series = value["categories"], value["series"]
    require(isinstance(categories, list) and 1 <= len(categories) <= 24
            and all(isinstance(item, str) and item for item in categories), "Invalid chart categories")
    require(not any(item.lstrip().startswith("=") for item in categories),
            "Chart categories must be literal text, not formulas")
    require(isinstance(series, list) and 1 <= len(series) <= 6, "Invalid chart series")
    require(isinstance(value["number_format"], str) and value["number_format"],
            "Chart number_format must be explicit")
    data = CategoryChartData(number_format=value["number_format"])
    data.categories = categories
    for entry in series:
        require(isinstance(entry, dict) and set(entry) == {"name", "values"}, "Invalid series fields")
        require(isinstance(entry["name"], str) and entry["name"], "Series name must be text")
        require(not entry["name"].lstrip().startswith("="),
                "Chart series names must be literal text, not formulas")
        values = entry["values"]
        require(isinstance(values, list) and len(values) == len(categories)
                and all(isinstance(item, (int, float)) and not isinstance(item, bool)
                        and math.isfinite(item) for item in values), "Invalid chart values")
        data.add_series(entry["name"], values)
    shape.chart.replace_data(data)
    if len(series) > 1:
        shape.chart.has_legend = True
    for element in shape.chart._chartSpace.plotArea.valAx_lst:
        axis = ValueAxis(element)
        axis.minimum_scale = None
        axis.maximum_scale = None
        axis.major_unit = None
        axis.minor_unit = None
        axis.tick_labels.number_format = value["number_format"]
    # replace_data preserves (and clones) series/point overrides, which outrank plot labels.
    for labels in shape.chart._chartSpace.xpath(".//c:dLbls"):
        DataLabels(labels).number_format = value["number_format"]
        for number in labels.xpath("./c:dLbl/c:numFmt"):
            number.formatCode = value["number_format"]
            number.sourceLinked = False


def update_table(shape, value, rtl):
    require(shape.has_table and isinstance(value, list), "Table binding requires rows")
    table = shape.table
    require(len(value) == len(table.rows), "Table row count must match the reference; split into more slides")
    for index, row in enumerate(value):
        require(isinstance(row, list) and len(row) == len(table.columns)
                and all(isinstance(cell, str) for cell in row), "Table dimensions or cell types do not match")
        for column, cell in enumerate(reversed(row) if rtl else row):
            fill_text(table.cell(index, column).text_frame, cell, rtl)


def canonical_xml(data):
    from lxml import etree
    node = etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))
    if node.tag == f"{{{R}}}Relationships":
        node[:] = sorted(node, key=lambda child: child.get("Id", ""))
    return etree.tostring(node, method="c14n")


def restore_design(original, output):
    for name in original:
        if not name.startswith(DESIGN):
            continue
        require(name in output, f"Template design part was lost: {name}")
        if original[name] != output[name]:
            require(name.endswith((".xml", ".rels"))
                    and canonical_xml(original[name]) == canonical_xml(output[name]),
                    f"Template design or font data changed: {name}")
            output[name] = original[name]
    for name, data in output.items():
        if name.startswith("ppt/media/"):
            require(original.get(name) == data, f"Template media changed: {name}")


def update_document_counts(parts, count):
    name = "docProps/app.xml"
    if name not in parts:
        return
    document = parseString(parts[name])
    namespace = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
    for node in list(document.documentElement.childNodes):
        if node.nodeType != node.ELEMENT_NODE:
            continue
        if node.localName in {"TitlesOfParts", "HeadingPairs"}:
            node.parentNode.removeChild(node)
        elif node.localName in {"Slides", "Notes", "HiddenSlides"}:
            while node.firstChild:
                node.removeChild(node.firstChild)
            value = (sum(name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")
                         for name in parts) if node.localName == "Notes" else
                     0 if node.localName == "HiddenSlides" else count)
            node.appendChild(document.createTextNode(str(value)))
    if not children(document, namespace, "Slides"):
        prefix = document.documentElement.prefix
        node = document.createElementNS(namespace, f"{prefix}:Slides" if prefix else "Slides")
        node.appendChild(document.createTextNode(str(count)))
        document.documentElement.appendChild(node)
    parts[name] = document.toxml(encoding="UTF-8")


def probe(root):
    config = load_config(root)
    dependencies = {name: importlib.util.find_spec(name) is not None
                    for name in ("pptx", "defusedxml", "lxml")}
    available = all(dependencies.values())
    if dependencies["pptx"]:
        import pptx
        dependency = pptx.__version__
    else:
        dependency = None
    if available:
        parseString(b"<probe/>")
    return {"ok": available, "version": VERSION, "mode": "read-only-probe",
            "python_pptx_available": dependencies["pptx"], "python_pptx_version": dependency,
            "dependencies": dependencies,
            "template_keys": sorted(config["templates"]), "changes_made": False,
            "artifact_publication": "Must be provided and verified by the host"}


def build(root, key, plan, output):
    from pptx import Presentation
    config = load_config(root)
    require(key in config["templates"], "Unknown template key")
    profile = config["templates"][key]
    validate_plan(plan, profile)
    source = (root / profile["asset"]).resolve()
    source_data = source.read_bytes()
    output = output.resolve()
    require(output.suffix.lower() == ".pptx" and not output.is_relative_to(root.resolve()),
            "Use a NEW .pptx output outside the skill folder")
    require(not output.exists(), "Output already exists; choose a NEW filename")
    require(output.parent.is_dir(), "Output directory must already exist and be host-approved")
    original = read_package(source_data)
    copies = SlideCopies(original)
    reference_indices = [profile["layouts"][slide["layout"]]["reference_slide"]
                         for slide in plan["slides"]]
    presentation = Presentation(io.BytesIO(pack(copies.create(reference_indices))))
    rtl = profile["direction"] == "rtl"
    for index, (slide, specification) in enumerate(zip(presentation.slides, plan["slides"]), 1):
        slide._element.attrib.pop("show", None)
        fields = profile["layouts"][specification["layout"]]["fields"]
        for path, binding in fields.items():
            matches = [shape for shape in slide.shapes if shape.name == binding["shape"]]
            require(len(matches) == 1, f"Missing or ambiguous bound shape: {binding['shape']}")
            shape = matches[0]
            value = lookup(specification, path)
            if value is MISSING:
                require(binding["type"] == "text", "Only text fields can be optional")
                shape._element.getparent().remove(shape._element)
            elif binding["type"] == "text":
                require(shape.has_text_frame, "Text binding refers to a non-text shape")
                fill_text(shape.text_frame, value, rtl)
            elif binding["type"] == "chart":
                update_chart(shape, value)
            elif binding["type"] == "table":
                update_table(shape, value, rtl)
            else:
                raise ValueError(f"Unknown binding type: {binding['type']}")
        for field in slide._element.iter(f"{{{A}}}fld"):
            if field.get("type") == "slidenum":
                for text in field.iter(f"{{{A}}}t"):
                    text.text = str(index)
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame
            if notes is not None:
                fill_text(notes, specification.get("notes", ""), rtl)
        elif specification.get("notes"):
            fill_text(slide.notes_slide.notes_text_frame, specification["notes"], rtl)
    presentation.core_properties.title = next(
        (slide.get("title", "") for slide in plan["slides"] if slide.get("title")), "Presentation")
    temporary = io.BytesIO()
    presentation.save(temporary)
    result_parts = read_package(temporary.getvalue())
    restore_design(original, result_parts)
    update_document_counts(result_parts, len(presentation.slides))
    result = pack(result_parts)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".template-", suffix=".pptx", dir=output.parent)
    created = False
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(result)
        with output.open("xb") as destination:
            created = True
            destination.write(Path(temporary_name).read_bytes())
    except OSError:
        if created:
            output.unlink(missing_ok=True)
        raise
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    require(source.read_bytes() == source_data, "Source template unexpectedly changed")
    return {"ok": True, "version": VERSION, "mode": "direct-pptx",
            "template_key": key, "template_filename": source.name, "output": str(output),
            "slides": len(presentation.slides), "masters": len(presentation.slide_masters),
            "source_unchanged": True, "design_parts_preserved": True,
            "embedded_font_parts": sum(name.startswith("ppt/fonts/") for name in result_parts),
            "active_canvas_updated": False,
            "delivery_status": "Local output exists; host must actually publish it"}


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--template")
    parser.add_argument("--content", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.probe:
            result = probe(arguments.skill_root)
        else:
            require(arguments.template and arguments.content and arguments.output,
                    "Provide --template, --content and --output, or use --probe")
            result = build(arguments.skill_root, arguments.template,
                           json.loads(arguments.content.read_text(encoding="utf-8-sig")),
                           arguments.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 3
    except (ValueError, KeyError, TypeError, ImportError, OSError, RuntimeError,
            ExpatError, zipfile.BadZipFile) as error:
        print(json.dumps({"ok": False, "error_type": type(error).__name__,
                          "error": str(error)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
