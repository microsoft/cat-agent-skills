#!/usr/bin/env python3
"""Dependency-free first-pass greenwashing claim auditor."""

from __future__ import annotations

import argparse
import csv
import html
import ipaddress
import json
import re
import socket
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES = SKILL_ROOT / "references" / "greenwashing-rules.json"
RISK_ORDER = {"Green": 0, "Yellow": 1, "Red": 2}
VALID_JURISDICTIONS = ("CA", "EU", "UK")
EU_RULE_DATE = date(2026, 9, 27)


def phrase_pattern(phrase: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in re.split(r"[\s-]+", phrase.strip()) if part]
    return re.compile(r"\b" + r"[\s-]+".join(parts) + r"\b", re.IGNORECASE)


class Rules:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.data = data
        self.red = [(phrase, phrase_pattern(phrase)) for phrase in data["red_terms"]]
        self.yellow = [(phrase, phrase_pattern(phrase)) for phrase in data["yellow_terms"]]
        self.comparisons = [
            (phrase, phrase_pattern(phrase)) for phrase in data["comparison_terms"]
        ]
        self.future = [re.compile(pattern, re.IGNORECASE) for pattern in data["future_patterns"]]
        self.absolute = [
            re.compile(pattern, re.IGNORECASE) for pattern in data["absolute_patterns"]
        ]
        self.labels = [(phrase, phrase_pattern(phrase)) for phrase in data["label_terms"]]
        self.offsets = [(phrase, phrase_pattern(phrase)) for phrase in data["offset_terms"]]
        self.neutrality = [
            (phrase, phrase_pattern(phrase)) for phrase in data["neutrality_terms"]
        ]
        self.false_positives = [phrase.lower() for phrase in data["false_positive_phrases"]]

    def matches(self, text: str, patterns: list[tuple[str, re.Pattern[str]]]) -> list[str]:
        lowered = text.lower()
        hits = []
        for phrase, pattern in patterns:
            if pattern.search(text) and not any(
                phrase in false_positive and false_positive in lowered
                for false_positive in self.false_positives
            ):
                hits.append(phrase)
        return sorted(set(hits))


def add_finding(
    findings: list[dict],
    tag: str,
    code: str,
    rating: str,
    source_type: str,
    reason: str,
    matched_terms: list[str] | None = None,
    effective_date: str | None = None,
) -> None:
    key = (tag, code, reason)
    if any((f["tag"], f["finding_code"], f["reason"]) == key for f in findings):
        return
    finding = {
        "tag": tag,
        "finding_code": code,
        "source_type": source_type,
        "rating": rating,
        "reason": reason,
    }
    if matched_terms:
        finding["matched_terms"] = matched_terms
    if effective_date:
        finding["effective_date"] = effective_date
    findings.append(finding)


def audit_text(
    text: str,
    location: str,
    source: str,
    rules: Rules,
    jurisdictions: list[str],
    publication_date: date,
    applicability_confirmed: bool,
) -> dict | None:
    normalized = " ".join(text.split())
    if not normalized:
        return None

    red_hits = rules.matches(normalized, rules.red)
    yellow_hits = rules.matches(normalized, rules.yellow)
    comparison_hits = rules.matches(normalized, rules.comparisons)
    label_hits = rules.matches(normalized, rules.labels)
    offset_hits = rules.matches(normalized, rules.offsets)
    neutrality_hits = rules.matches(normalized, rules.neutrality)
    future_hit = any(pattern.search(normalized) for pattern in rules.future)
    absolute_hit = any(pattern.search(normalized) for pattern in rules.absolute)

    if not any(
        (
            red_hits,
            yellow_hits,
            comparison_hits,
            label_hits,
            offset_hits,
            neutrality_hits,
            future_hit,
            absolute_hit,
        )
    ):
        return None

    findings: list[dict] = []
    if red_hits:
        add_finding(
            findings,
            "ANY",
            "ANY-VAGUE",
            "Red",
            "vocabulary",
            "High-risk or broadly framed environmental vocabulary requires exact scope and evidence.",
            sorted(set(red_hits + yellow_hits)),
        )
    elif yellow_hits:
        add_finding(
            findings,
            "ANY",
            "ANY-VAGUE",
            "Yellow",
            "vocabulary",
            "Context-dependent environmental vocabulary requires clarification and substantiation.",
            yellow_hits,
        )
    if absolute_hit:
        add_finding(
            findings,
            "ANY",
            "ANY-ABSOLUTE",
            "Red",
            "vocabulary",
            "Absolute or zero-impact wording is unlikely to be supportable across an undefined boundary.",
        )
    if comparison_hits:
        add_finding(
            findings,
            "ANY",
            "ANY-OMISSION",
            "Yellow",
            "vocabulary",
            "Comparative wording requires a comparator, baseline, method, period, and magnitude.",
            comparison_hits,
        )
    if label_hits:
        add_finding(
            findings,
            "ANY",
            "ANY-LABEL",
            "Yellow",
            "vocabulary",
            "Certification or approval wording requires verification of the scheme, scope, and status.",
            label_hits,
        )
    if future_hit:
        add_finding(
            findings,
            "ANY",
            "ANY-FUTURE",
            "Yellow",
            "vocabulary",
            "Future environmental commitments require a defined scope, measurable milestones, and a credible delivery plan.",
        )

    if "CA" in jurisdictions:
        if red_hits or yellow_hits:
            add_finding(
                findings,
                "CA",
                "CA-MISLEADING",
                "Yellow",
                "law_and_guidance",
                "Review literal meaning and general impression against claim-matched evidence.",
                sorted(set(red_hits + yellow_hits)),
            )
        add_finding(
            findings,
            "CA",
            "CA-PRODUCT-TEST",
            "Yellow",
            "law",
            "If this is a product environmental-benefit claim, adequate and proper pre-claim testing is required.",
        )
        if future_hit:
            add_finding(
                findings,
                "CA",
                "CA-FUTURE",
                "Yellow",
                "law_and_guidance",
                "Future environmental claims require substantiation and a concrete, realistic, verifiable plan.",
            )
        if comparison_hits:
            add_finding(
                findings,
                "CA",
                "CA-COMPARISON",
                "Yellow",
                "guidance",
                "The comparator and extent of the environmental difference must be specific.",
                comparison_hits,
            )

    if "EU" in jurisdictions:
        eu_active = publication_date >= EU_RULE_DATE
        if eu_active and ({"green", "eco-friendly", "environmentally friendly", "biodegradable", "bio-based", "energy efficient"} & set(red_hits + yellow_hits)):
            add_finding(
                findings,
                "EU",
                "EU-GENERIC",
                "Red",
                "law",
                "Generic environmental claim requires recognized excellent environmental performance relevant to the claim.",
                sorted(set(red_hits + yellow_hits)),
                EU_RULE_DATE.isoformat(),
            )
        if eu_active and label_hits:
            add_finding(
                findings,
                "EU",
                "EU-LABEL",
                "Red",
                "law",
                "Sustainability labels must be established by a public authority or qualifying certification scheme.",
                label_hits,
                EU_RULE_DATE.isoformat(),
            )
        if eu_active and offset_hits and neutrality_hits:
            add_finding(
                findings,
                "EU",
                "EU-OFFSET-PRODUCT",
                "Red",
                "law",
                "A product greenhouse-gas neutrality, reduction, or positive-impact claim cannot rely on offsetting outside the value chain.",
                sorted(set(offset_hits + neutrality_hits)),
                EU_RULE_DATE.isoformat(),
            )
        if future_hit:
            add_finding(
                findings,
                "EU",
                "EU-FUTURE",
                "Yellow" if not eu_active else "Red",
                "law",
                "Future performance claims require public verifiable commitments, a detailed plan, measurable targets, resources, and independent review.",
                effective_date=EU_RULE_DATE.isoformat(),
            )
        if comparison_hits:
            add_finding(
                findings,
                "EU",
                "EU-COMPARISON",
                "Yellow",
                "law",
                "Environmental comparisons require transparent method, compared subjects, suppliers, and update measures.",
                comparison_hits,
                EU_RULE_DATE.isoformat(),
            )

    if "UK" in jurisdictions:
        if red_hits or yellow_hits:
            add_finding(
                findings,
                "UK",
                "UK-CLARITY",
                "Yellow",
                "law_and_guidance",
                "The claim must be clear, unambiguous, truthful, and accurate.",
                sorted(set(red_hits + yellow_hits)),
            )
            add_finding(
                findings,
                "UK",
                "UK-EVIDENCE",
                "Yellow",
                "guidance",
                "The claim requires up-to-date, credible evidence matching its scope and overall impression.",
            )
        if comparison_hits:
            add_finding(
                findings,
                "UK",
                "UK-COMPARISON",
                "Yellow",
                "guidance",
                "The comparison must be fair, meaningful, and clear.",
                comparison_hits,
            )
        if any(term in yellow_hits for term in ("recyclable", "compostable", "biodegradable", "reusable")):
            add_finding(
                findings,
                "UK",
                "UK-OMISSION",
                "Yellow",
                "law_and_guidance",
                "Disposal conditions, required consumer action, and realistic infrastructure access must be prominent.",
            )

    if not findings:
        return None
    overall = max((f["rating"] for f in findings), key=RISK_ORDER.get)
    return {
        "source": source,
        "location": location,
        "claim_text": normalized[:4000],
        "applicable_jurisdictions": jurisdictions,
        "regional_applicability_confirmed": applicability_confirmed,
        "publication_date": publication_date.isoformat(),
        "findings": findings,
        "overall_risk_rating": overall,
        "required_action": "legal_review" if overall == "Red" else "substantiate",
    }


def read_csv_units(
    path: Path,
    text_columns: list[str],
    max_items: int | None,
    rules: Rules,
):
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        headers = reader.fieldnames or []
        if text_columns:
            missing = [column for column in text_columns if column not in headers]
            if missing:
                raise ValueError(f"Columns not found: {missing}; available columns: {headers}")
            selected = text_columns
        else:
            hints = rules.data["text_column_hints"]
            selected = [
                header for header in headers
                if any(hint in header.lower() for hint in hints)
            ] or headers
        for row_number, row in enumerate(reader, start=2):
            if max_items and row_number - 1 > max_items:
                break
            for column in selected:
                value = row.get(column)
                if value and str(value).strip():
                    yield f"row {row_number}, column {column}", str(value)


def xml_text(element: ET.Element) -> str:
    return " ".join(text.strip() for text in element.itertext() if text and text.strip())


def read_docx_units(path: Path, max_items: int | None):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    count = 0
    paragraph_index = 0
    table_cell_index = 0
    table_paragraphs = {
        id(paragraph)
        for cell in root.iter()
        if cell.tag.rsplit("}", 1)[-1] == "tc"
        for paragraph in cell.iter()
        if paragraph.tag.rsplit("}", 1)[-1] == "p"
    }
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1]
        if local == "p":
            paragraph_index += 1
            if id(element) in table_paragraphs:
                continue
            text = xml_text(element)
            if text:
                count += 1
                yield f"paragraph {paragraph_index}", text
        elif local == "tc":
            table_cell_index += 1
            text = xml_text(element)
            if text:
                count += 1
                yield f"table cell {table_cell_index}", text
        if max_items and count >= max_items:
            return


def read_pptx_units(path: Path, max_items: int | None):
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            (
                name for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=lambda name: int(re.search(r"(\d+)", Path(name).stem).group(1)),
        )
        count = 0
        for slide_name in slide_names:
            slide_number = int(re.search(r"(\d+)", Path(slide_name).stem).group(1))
            root = ET.fromstring(archive.read(slide_name))
            shape_number = 0
            for shape in root.iter():
                if shape.tag.rsplit("}", 1)[-1] not in ("sp", "graphicFrame"):
                    continue
                shape_number += 1
                text = xml_text(shape)
                if text:
                    properties = next(
                        (
                            child
                            for child in shape.iter()
                            if child.tag.rsplit("}", 1)[-1] == "cNvPr"
                        ),
                        None,
                    )
                    shape_id = properties.get("id") if properties is not None else None
                    shape_name = properties.get("name") if properties is not None else None
                    if shape_id and shape_name:
                        shape_location = f"shape {shape_id} ({shape_name})"
                    elif shape_id:
                        shape_location = f"shape {shape_id}"
                    elif shape_name:
                        shape_location = f"shape {shape_number} ({shape_name})"
                    else:
                        shape_location = f"shape {shape_number}"
                    count += 1
                    yield f"slide {slide_number}, {shape_location}", text
                    if max_items and count >= max_items:
                        return


def column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def read_xlsx_units(path: Path, sheet: str | None, max_items: int | None):
    namespaces = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(path) as archive:
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = [xml_text(item) for item in root.findall("main:si", namespaces)]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("pkg:Relationship", namespaces)
        }
        sheets = []
        for item in workbook.findall("main:sheets/main:sheet", namespaces):
            name = item.attrib["name"]
            relationship_id = item.attrib[f"{{{namespaces['rel']}}}id"]
            target = targets[relationship_id].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            sheets.append((name, target))
        selected = [item for item in sheets if sheet is None or item[0] == sheet]
        if sheet and not selected:
            raise ValueError(f"Worksheet not found: {sheet}; available: {[name for name, _ in sheets]}")

        count = 0
        for sheet_name, target in selected:
            root = ET.fromstring(archive.read(target))
            for cell in root.findall(".//main:c", namespaces):
                reference = cell.attrib.get("r", "")
                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", namespaces)
                inline = cell.find("main:is", namespaces)
                value = ""
                if inline is not None:
                    value = xml_text(inline)
                elif value_node is not None and value_node.text is not None:
                    value = value_node.text
                    if cell_type == "s":
                        value = shared_strings[int(value)]
                if value and re.search(r"[A-Za-z]{3}", value):
                    count += 1
                    yield f"sheet {sheet_name}, cell {reference}", value
                    if max_items and count >= max_items:
                        return


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden_depth = 0
        self.blocks: list[str] = []
        self.current: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.hidden_depth += 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "div", "section", "article"):
            self.flush()

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.hidden_depth:
            self.hidden_depth -= 1
        if tag in ("p", "li", "h1", "h2", "h3", "h4", "div", "section", "article"):
            self.flush()

    def handle_data(self, data):
        if not self.hidden_depth and data.strip():
            self.current.append(data.strip())

    def flush(self):
        text = html.unescape(" ".join(self.current)).strip()
        if text:
            self.blocks.append(text)
        self.current = []


def validate_public_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Only public HTTP/HTTPS URLs are supported.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must contain a public hostname without credentials.")
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError as error:
        raise ValueError("URL contains an invalid port.") from error

    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(
                parsed.hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as error:
        raise ValueError(f"Unable to resolve URL hostname: {parsed.hostname}") from error
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("URL hostname must resolve only to public IP addresses.")


class PublicUrlRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_url_units(url: str, max_items: int | None):
    validate_public_url(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "GlobalGreenwashingClaimAuditor/1.0"},
    )
    opener = urllib.request.build_opener(PublicUrlRedirectHandler())
    with opener.open(request, timeout=30) as response:
        validate_public_url(response.geturl())
        content_type = response.headers.get_content_type()
        if content_type not in ("text/html", "application/xhtml+xml", "text/plain"):
            raise ValueError(f"Unsupported URL content type: {content_type}")
        body = response.read(5_000_000).decode(response.headers.get_content_charset() or "utf-8", "replace")
    if content_type == "text/plain":
        blocks = [line.strip() for line in body.splitlines() if line.strip()]
    else:
        parser = VisibleTextParser()
        parser.feed(body)
        parser.flush()
        blocks = parser.blocks
    for index, block in enumerate(blocks, start=1):
        if max_items and index > max_items:
            break
        yield f"web block {index}", block


def render_markdown(report: dict) -> str:
    lines = [
        "# Global Greenwashing Claim Audit",
        "",
        f"- Source: `{report['source']}`",
        f"- Publication date: `{report['publication_date']}`",
        f"- Jurisdictions: {', '.join(report['jurisdictions']) or 'ANY only'}",
        f"- Units scanned: {report['units_scanned']}",
        f"- Flagged units: {len(report['results'])}",
        "",
        "## Findings",
        "",
        "| Location | Claim | Tag | Finding | Risk | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for result in report["results"]:
        claim = result["claim_text"].replace("|", "\\|").replace("\n", " ")
        for finding in result["findings"]:
            reason = finding["reason"].replace("|", "\\|")
            lines.append(
                f"| {result['location']} | {claim[:240]} | {finding['tag']} | "
                f"{finding['finding_code']} | {finding['rating']} | {reason} |"
            )
    if not report["results"]:
        lines.append("| - | No candidate environmental claims detected | ANY | - | Green | No issue detected by keyword triage |")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Keyword and pattern triage is not a legal conclusion.",
            "- Review imagery, omissions, evidence, scope, lifecycle, and context manually.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser(input_kind: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Audit {input_kind} content for greenwashing claim risk.")
    if input_kind in ("csv", "xlsx", "docx", "pptx"):
        parser.add_argument("input", type=Path)
    elif input_kind == "url":
        parser.add_argument("url")
    elif input_kind == "text":
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--text")
        group.add_argument("--text-file", type=Path)
    parser.add_argument("--jurisdictions", nargs="*", choices=VALID_JURISDICTIONS, default=list(VALID_JURISDICTIONS))
    parser.add_argument("--publication-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--jurisdiction-unconfirmed", action="store_true")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    if input_kind == "csv":
        parser.add_argument("--text-column", action="append", default=[])
    if input_kind == "xlsx":
        parser.add_argument("--sheet")
    return parser


def run(input_kind: str, argv=None) -> int:
    args = build_parser(input_kind).parse_args(argv)
    rules = Rules(args.rules)
    source = ""
    if input_kind == "csv":
        source = str(args.input)
        units = read_csv_units(args.input, args.text_column, args.max_items, rules)
    elif input_kind == "xlsx":
        source = str(args.input)
        units = read_xlsx_units(args.input, args.sheet, args.max_items)
    elif input_kind == "docx":
        source = str(args.input)
        units = read_docx_units(args.input, args.max_items)
    elif input_kind == "pptx":
        source = str(args.input)
        units = read_pptx_units(args.input, args.max_items)
    elif input_kind == "url":
        source = args.url
        units = read_url_units(args.url, args.max_items)
    else:
        if args.text_file:
            source = str(args.text_file)
            text = args.text_file.read_text(encoding="utf-8", errors="replace")
        else:
            source = "conversation"
            text = args.text
        units = (("conversation content", text),)

    results = []
    scanned = 0
    for location, text in units:
        scanned += 1
        result = audit_text(
            text=text,
            location=location,
            source=source,
            rules=rules,
            jurisdictions=args.jurisdictions,
            publication_date=args.publication_date,
            applicability_confirmed=not args.jurisdiction_unconfirmed,
        )
        if result:
            results.append(result)

    report = {
        "tool": "global-greenwashing-claim-auditor",
        "source": source,
        "publication_date": args.publication_date.isoformat(),
        "jurisdictions": args.jurisdictions,
        "units_scanned": scanned,
        "results": results,
    }
    output = render_markdown(report) if args.format == "markdown" else json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
        print(f"Wrote {args.out} ({len(results)} flagged units from {scanned} scanned).")
    else:
        print(output, end="")
    return 0


def entrypoint(input_kind: str) -> None:
    try:
        raise SystemExit(run(input_kind))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)
