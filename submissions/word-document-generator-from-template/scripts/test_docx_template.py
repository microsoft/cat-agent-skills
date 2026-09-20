#!/usr/bin/env python3
"""Regression tests for deterministic DOCX template filling."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from docx import Document
from lxml import etree

from build_sample_template import build_sample
from docx_template import (
    TemplateError,
    fill_template,
    inspect_template,
    validate_docx,
)


HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def _build_table_template(
    output: Path,
    headers: list[str],
    tokens: list[str],
) -> None:
    """Build a minimal DOCX with one table: a header row and a template data row."""
    doc = Document()
    table = doc.add_table(rows=2, cols=len(tokens))
    for cell, text in zip(table.rows[0].cells, headers):
        cell.text = text
    for cell, tok in zip(table.rows[1].cells, tokens):
        cell.text = tok
    doc.save(output)


def _build_nested_table_template(
    output: Path,
    outer_token: str,
    inner_token: str,
) -> None:
    """Build a DOCX where an outer table's template row contains a nested w:tbl.

    Column 1 of the template row holds *outer_token* (e.g. ``{{outer[].label}}``);
    column 2 contains a nested inner table whose template row holds *inner_token*
    (e.g. ``{{outer[].inner[].val}}``).  This exercises the Case A (nested-table)
    expansion path in ``_expand_rows_in_subtree``.
    """
    WN = f"{{{W}}}"

    # Build the outer 2-column, 2-row table with python-docx.
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Outer"
    table.rows[0].cells[1].text = "Inner"
    table.rows[1].cells[0].text = outer_token
    doc.save(output)

    # Patch word/document.xml to embed an inner w:tbl in the second template cell.
    parts = _read_zip(output)
    root = etree.fromstring(parts["word/document.xml"])

    outer_tbl = root.findall(f".//{WN}tbl")[0]
    tmpl_row = outer_tbl.findall(f"{WN}tr")[1]
    second_cell = tmpl_row.findall(f"{WN}tc")[1]

    for p in list(second_cell.findall(f"{WN}p")):
        second_cell.remove(p)

    # Inner table: header row + template row.
    inner_tbl = etree.SubElement(second_cell, f"{WN}tbl")

    hdr_tr = etree.SubElement(inner_tbl, f"{WN}tr")
    hdr_tc = etree.SubElement(hdr_tr, f"{WN}tc")
    hdr_p = etree.SubElement(hdr_tc, f"{WN}p")
    etree.SubElement(etree.SubElement(hdr_p, f"{WN}r"), f"{WN}t").text = "Inner"

    tmpl_tr = etree.SubElement(inner_tbl, f"{WN}tr")
    tmpl_tc = etree.SubElement(tmpl_tr, f"{WN}tc")
    tmpl_p = etree.SubElement(tmpl_tc, f"{WN}p")
    etree.SubElement(etree.SubElement(tmpl_p, f"{WN}r"), f"{WN}t").text = inner_token

    # OOXML requires a trailing w:p after a w:tbl inside a w:tc.
    etree.SubElement(second_cell, f"{WN}p")

    parts["word/document.xml"] = etree.tostring(
        root, encoding="UTF-8", xml_declaration=True
    )
    _write_zip(output, parts)


def _read_zip(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _write_zip(path: Path, parts: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in parts.items():
            archive.writestr(name, value)


def _visible_text(xml: bytes) -> str:
    root = etree.fromstring(xml)
    return "".join(root.xpath(".//w:t/text()", namespaces=NS))


class DocxTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.template = self.root / "template.docx"
        build_sample(self.template)
        self.data = json.loads(
            (ASSETS / "sample-data.json").read_text(encoding="utf-8")
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_inspect_finds_split_tokens_arrays_and_fields(self) -> None:
        manifest = inspect_template(self.template)
        self.assertIn("document.title", manifest["scalar_placeholders"])
        self.assertIn("sections.executive_summary", manifest["scalar_placeholders"])
        # Simple findings table contributes "finding", "impact", "owner";
        # the nested hosts table adds "findings.hosts" with "ip" and "name".
        self.assertEqual(
            manifest["repeating_arrays"],
            {
                "findings": ["finding", "impact", "owner"],
                "findings.hosts": ["ip", "name"],
            },
        )
        field_json = json.dumps(manifest["word_fields"])
        self.assertIn("PAGE", field_json)
        self.assertIn("NUMPAGES", field_json)
        self.assertIn("word/header1.xml", manifest["parts"])
        self.assertIn("word/footer1.xml", manifest["parts"])
        for path in ("document.status", "document.type", "document.audience"):
            self.assertIn(path, manifest["conditional_paths"])

    def test_fill_preserves_fields_package_parts_and_original(self) -> None:
        original_hash = hashlib.sha256(self.template.read_bytes()).hexdigest()
        original_parts = _read_zip(self.template)
        output = self.root / "nested" / "filled.docx"

        report = fill_template(self.template, self.data, output)

        self.assertTrue(output.is_file())
        self.assertEqual(
            hashlib.sha256(self.template.read_bytes()).hexdigest(), original_hash
        )
        self.assertTrue(report["field_signature_preserved"])
        # Simple findings table: 3 rows × 1 = 3 outer.
        # Nested hosts table: 3 outer + 5 inner (2+1+2 hosts).
        # repeated_rows["findings"] = 3 (simple) + 3 (nested outer) = 6.
        self.assertEqual(
            report["repeated_rows"],
            {"findings": 6, "findings.hosts": 5},
        )
        self.assertEqual(report["defaulted_fields"], [])
        self.assertTrue(report["validation"]["valid_docx"])

        result_parts = _read_zip(output)
        for name, content in original_parts.items():
            if name not in {
                "word/document.xml",
                "word/header1.xml",
                "word/footer1.xml",
            }:
                self.assertEqual(
                    result_parts[name],
                    content,
                    f"Unmodified package part changed: {name}",
                )

        text = " ".join(
            _visible_text(result_parts[name])
            for name in ("word/document.xml", "word/header1.xml", "word/footer1.xml")
        )
        self.assertIn("Quarterly Operations Report", text)
        self.assertIn("Service response targets were met.", text)
        self.assertNotIn("{{", text)

        document = Document(output)
        findings_table = next(
            table for table in document.tables if table.rows[0].cells[0].text == "Finding"
        )
        self.assertEqual(len(findings_table.rows), 4)  # header + 3 items
        hosts_table = next(
            table
            for table in document.tables
            if table.rows[0].cells[0].text == "Finding (Affected Hosts)"
        )
        self.assertEqual(len(hosts_table.rows), 6)  # header + 5 cross-product rows (2+1+2)

    def test_newlines_become_word_line_breaks(self) -> None:
        output = self.root / "line-breaks.docx"
        fill_template(self.template, self.data, output)
        root = etree.fromstring(_read_zip(output)["word/document.xml"])
        self.assertGreaterEqual(len(root.xpath(".//w:br", namespaces=NS)), 2)

    def test_missing_scalar_uses_fallback_and_reports_it(self) -> None:
        data = copy.deepcopy(self.data)
        del data["document"]["audience"]
        output = self.root / "missing.docx"
        report = fill_template(self.template, data, output)
        self.assertIn("document.audience", report["defaulted_fields"])
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("Not specified in approved sources", text)

    def test_empty_array_removes_sample_row(self) -> None:
        data = copy.deepcopy(self.data)
        data["findings"] = []
        output = self.root / "empty.docx"
        report = fill_template(self.template, data, output)
        self.assertEqual(report["repeated_rows"], {"findings": 0})
        document = Document(output)
        findings_table = next(
            table for table in document.tables if table.rows[0].cells[0].text == "Finding"
        )
        self.assertEqual(len(findings_table.rows), 1)

    def test_wrong_array_type_fails_without_output(self) -> None:
        data = copy.deepcopy(self.data)
        data["findings"] = {"finding": "not an array"}
        output = self.root / "bad-array.docx"
        with self.assertRaisesRegex(TemplateError, "requires a JSON array"):
            fill_template(self.template, data, output)
        self.assertFalse(output.exists())

    def test_complex_scalar_fails_without_output(self) -> None:
        data = copy.deepcopy(self.data)
        data["document"]["title"] = {"nested": "not supported"}
        output = self.root / "bad-scalar.docx"
        with self.assertRaisesRegex(TemplateError, "requires a scalar"):
            fill_template(self.template, data, output)
        self.assertFalse(output.exists())

    def test_input_output_collision_is_rejected(self) -> None:
        with self.assertRaisesRegex(TemplateError, "must differ"):
            fill_template(self.template, self.data, self.template)

    def test_malformed_docx_is_rejected(self) -> None:
        bad = self.root / "bad.docx"
        bad.write_text("not a zip", encoding="utf-8")
        with self.assertRaisesRegex(TemplateError, "Cannot read DOCX"):
            inspect_template(bad)

    def test_write_to_non_writable_path_raises_template_error(self) -> None:
        """fill_template raises TemplateError (not raw OSError) for bad output path."""
        # Use an existing file as the 'parent directory' so mkdir/open both fail.
        blocker = self.root / "blocker"
        blocker.write_text("occupied", encoding="utf-8")
        bad_output = blocker / "output.docx"
        with self.assertRaises(TemplateError):
            fill_template(self.template, self.data, bad_output)

    def test_cli_write_failure_exits_with_code_2(self) -> None:
        """CLI returns exit code 2 (not a traceback) when output cannot be written."""
        data_path = self.root / "data.json"
        data_path.write_text(json.dumps(self.data), encoding="utf-8")
        blocker = self.root / "blocker2"
        blocker.write_text("occupied", encoding="utf-8")
        bad_output = str(blocker / "output.docx")
        result = subprocess.run(
            [
                sys.executable,
                str(HERE / "docx_template.py"),
                "fill",
                str(self.template),
                str(data_path),
                bad_output,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Error:", result.stderr)

    def test_malformed_placeholder_is_rejected(self) -> None:
        parts = _read_zip(self.template)
        root = etree.fromstring(parts["word/document.xml"])
        target = next(
            node
            for node in root.xpath(".//w:t", namespaces=NS)
            if "sections.executive_summary" in (node.text or "")
        )
        target.text = "sections executive_summary"
        parts["word/document.xml"] = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8"
        )
        malformed = self.root / "malformed-token.docx"
        _write_zip(malformed, parts)
        with self.assertRaisesRegex(TemplateError, "Malformed placeholder"):
            inspect_template(malformed)

    def test_unmatched_placeholder_braces_are_rejected(self) -> None:
        parts = _read_zip(self.template)
        root = etree.fromstring(parts["word/document.xml"])
        target = next(
            node
            for node in root.xpath(".//w:t", namespaces=NS)
            if "sections.executive_summary" in (node.text or "")
        )
        target.text = "sections.executive_summary"
        closing = target.getparent().getnext()
        if closing is not None:
            closing_text = closing.find(f"{{{W}}}t")
            if closing_text is not None:
                closing_text.text = ""
        parts["word/document.xml"] = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8"
        )
        malformed = self.root / "unmatched-token.docx"
        _write_zip(malformed, parts)
        with self.assertRaisesRegex(TemplateError, "Malformed placeholder"):
            inspect_template(malformed)

    def test_payload_with_brace_sequences_does_not_raise(self) -> None:
        """A JSON value containing {{...}} must not be mistaken for an unresolved token."""
        data = copy.deepcopy(self.data)
        data["sections"]["executive_summary"] = (
            "Use {{name}} in the payload for dynamic content."
        )
        output = self.root / "brace-value.docx"
        # fill_template and validate_docx must both succeed.
        report = fill_template(self.template, data, output)
        self.assertTrue(output.exists())
        validate_docx(output, template_path=self.template)
        # The ZWSP-escaped text should be present in the output XML.
        doc_xml = _read_zip(output)["word/document.xml"]
        raw = doc_xml.decode("utf-8")
        self.assertIn("{" + "\u200B" + "{", raw)

    def test_leftover_template_token_still_fails(self) -> None:
        """validate_docx must raise when a genuine {{...}} token remains in the output."""
        output = self.root / "filled-for-leftover.docx"
        fill_template(self.template, self.data, output)
        # Inject a raw token into the filled document XML.
        WN = f"{{{W}}}"
        parts = _read_zip(output)
        root = etree.fromstring(parts["word/document.xml"])
        first_p = root.find(f".//{WN}p")
        assert first_p is not None
        run = etree.SubElement(first_p, f"{WN}r")
        t = etree.SubElement(run, f"{WN}t")
        t.text = "{{orphan.token}}"
        parts["word/document.xml"] = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8"
        )
        damaged = self.root / "leftover-damaged.docx"
        _write_zip(damaged, parts)
        with self.assertRaisesRegex(TemplateError, "[Uu]nresolved"):
            validate_docx(damaged, template_path=self.template)

    def test_validate_detects_removed_live_field(self) -> None:
        output = self.root / "filled.docx"
        fill_template(self.template, self.data, output)
        parts = _read_zip(output)
        footer = etree.fromstring(parts["word/footer1.xml"])
        instr = footer.xpath(".//w:instrText", namespaces=NS)[0]
        instr.getparent().remove(instr)
        parts["word/footer1.xml"] = etree.tostring(
            footer, xml_declaration=True, encoding="UTF-8"
        )
        damaged = self.root / "damaged.docx"
        _write_zip(damaged, parts)
        with self.assertRaisesRegex(TemplateError, "field signature"):
            validate_docx(damaged, template_path=self.template)

    # ------------------------------------------------------------------
    # Nested repeating-array tests
    # ------------------------------------------------------------------

    def test_nested_array_inspect_manifest(self) -> None:
        """inspect_template surfaces nested arrays as dotted flat keys."""
        template = self.root / "nested-inspect.docx"
        _build_table_template(
            template,
            headers=["Outer", "Inner"],
            tokens=["{{outer[].label}}", "{{outer[].inner[].val}}"],
        )
        manifest = inspect_template(template)
        self.assertEqual(
            manifest["repeating_arrays"],
            {"outer": ["label"], "outer.inner": ["val"]},
        )

    def test_nested_array_flat_row_expands_to_cross_product(self) -> None:
        """A flat row with nested tokens produces one output row per outer×inner pair."""
        template = self.root / "nested-flat.docx"
        _build_table_template(
            template,
            headers=["Item", "Tag"],
            tokens=["{{items[].name}}", "{{items[].tags[].value}}"],
        )
        data = {
            "items": [
                {"name": "A", "tags": [{"value": "t1"}, {"value": "t2"}]},
                {"name": "B", "tags": [{"value": "t3"}]},
            ]
        }
        output = self.root / "nested-flat-out.docx"
        report = fill_template(template, data, output)

        self.assertEqual(report["repeated_rows"], {"items": 2, "items.tags": 3})
        self.assertEqual(report["defaulted_fields"], [])

        document = Document(output)
        table = document.tables[0]
        self.assertEqual(len(table.rows), 4)  # header + 3 data rows (2+1)
        data_texts = [
            " ".join(cell.text for cell in row.cells)
            for row in table.rows[1:]
        ]
        self.assertIn("A t1", data_texts)
        self.assertIn("A t2", data_texts)
        self.assertIn("B t3", data_texts)

    def test_nested_array_outer_fields_repeat_per_inner_row(self) -> None:
        """Outer leaf fields are duplicated across all inner rows for that item."""
        template = self.root / "nested-outer-repeat.docx"
        _build_table_template(
            template,
            headers=["Name", "Tag"],
            tokens=["{{items[].name}}", "{{items[].tags[].value}}"],
        )
        data = {
            "items": [
                {"name": "X", "tags": [{"value": "a"}, {"value": "b"}]},
            ]
        }
        output = self.root / "nested-outer-repeat-out.docx"
        fill_template(template, data, output)

        document = Document(output)
        table = document.tables[0]
        self.assertEqual(len(table.rows), 3)  # header + 2 rows
        # Both data rows must carry "X" in the name column.
        for row in table.rows[1:]:
            self.assertEqual(row.cells[0].text, "X")

    def test_nested_array_empty_inner_produces_no_rows(self) -> None:
        """An outer item whose inner array is empty contributes zero output rows."""
        template = self.root / "nested-empty-inner.docx"
        _build_table_template(
            template,
            headers=["Item", "Tag"],
            tokens=["{{items[].name}}", "{{items[].tags[].value}}"],
        )
        data = {
            "items": [
                {"name": "A", "tags": []},
                {"name": "B", "tags": [{"value": "t1"}]},
            ]
        }
        output = self.root / "nested-empty-inner-out.docx"
        report = fill_template(template, data, output)

        # items: 2 outer; tags: only 1 inner row generated (A contributes 0).
        self.assertEqual(report["repeated_rows"], {"items": 2, "items.tags": 1})

        document = Document(output)
        table = document.tables[0]
        self.assertEqual(len(table.rows), 2)  # header + 1 data row

    def test_three_level_nesting(self) -> None:
        """Tokens with three [] levels expand recursively via cross-product."""
        template = self.root / "three-level.docx"
        _build_table_template(
            template,
            headers=["Field"],
            tokens=["{{a[].b[].c[].field}}"],
        )
        data = {
            "a": [
                {
                    "b": [
                        {"c": [{"field": "X"}, {"field": "Y"}]},
                    ]
                }
            ]
        }
        output = self.root / "three-level-out.docx"
        report = fill_template(template, data, output)

        self.assertEqual(
            report["repeated_rows"],
            {"a": 1, "a.b": 1, "a.b.c": 2},
        )
        document = Document(output)
        table = document.tables[0]
        self.assertEqual(len(table.rows), 3)  # header + 2 data rows
        values = [row.cells[0].text for row in table.rows[1:]]
        self.assertEqual(sorted(values), ["X", "Y"])

    def test_multiple_inner_arrays_in_same_row_fails(self) -> None:
        """A flat row referencing two distinct inner arrays raises TemplateError."""
        template = self.root / "multi-inner.docx"
        _build_table_template(
            template,
            headers=["F1", "F2"],
            tokens=["{{x[].a[].f1}}", "{{x[].b[].f2}}"],
        )
        data = {
            "x": [
                {"a": [{"f1": "v"}], "b": [{"f2": "w"}]},
            ]
        }
        output = self.root / "multi-inner-out.docx"
        with self.assertRaisesRegex(TemplateError, "only one nested array"):
            fill_template(template, data, output)
        self.assertFalse(output.exists())

    # ------------------------------------------------------------------
    # Case A: nested w:tbl inside an outer repeating row
    # ------------------------------------------------------------------

    def test_nested_table_case_a_expand(self) -> None:
        """Case A: each outer item clones the outer row; inner rows expand per-item."""
        template = self.root / "case-a-expand.docx"
        _build_nested_table_template(
            template,
            outer_token="{{outer[].label}}",
            inner_token="{{outer[].inner[].val}}",
        )
        data = {
            "outer": [
                {"label": "A", "inner": [{"val": "a1"}, {"val": "a2"}]},
                {"label": "B", "inner": [{"val": "b1"}]},
            ]
        }
        output = self.root / "case-a-expand-out.docx"
        report = fill_template(template, data, output)

        self.assertEqual(report["repeated_rows"], {"outer": 2, "outer.inner": 3})
        self.assertEqual(report["defaulted_fields"], [])

        doc_xml = _read_zip(output)["word/document.xml"]
        root = etree.fromstring(doc_xml)
        WN = f"{{{W}}}"

        # Outer table has header + 2 data rows (one per outer item).
        outer_tbl = root.findall(f".//{WN}tbl")[0]
        outer_trs = outer_tbl.findall(f"{WN}tr")
        self.assertEqual(len(outer_trs), 3)

        # Outer label values are present in the output.
        all_text = _visible_text(doc_xml)
        for expected in ("A", "B", "a1", "a2", "b1"):
            self.assertIn(expected, all_text)

        # No unresolved tokens remain.
        self.assertNotIn("{{", all_text)

        # First data row's nested table has header + 2 inner rows (items a1, a2).
        first_data_row = outer_trs[1]
        inner_tbls_first = first_data_row.findall(f".//{WN}tbl")
        self.assertEqual(len(inner_tbls_first), 1)
        inner_trs_first = inner_tbls_first[0].findall(f"{WN}tr")
        self.assertEqual(len(inner_trs_first), 3)  # header + 2

        # Second data row's nested table has header + 1 inner row (item b1).
        second_data_row = outer_trs[2]
        inner_tbls_second = second_data_row.findall(f".//{WN}tbl")
        self.assertEqual(len(inner_tbls_second), 1)
        inner_trs_second = inner_tbls_second[0].findall(f"{WN}tr")
        self.assertEqual(len(inner_trs_second), 2)  # header + 1

    def test_nested_table_case_a_empty_inner_array(self) -> None:
        """Case A: an outer item with an empty inner array still produces one outer row."""
        template = self.root / "case-a-empty-inner.docx"
        _build_nested_table_template(
            template,
            outer_token="{{outer[].label}}",
            inner_token="{{outer[].inner[].val}}",
        )
        data = {"outer": [{"label": "X", "inner": []}]}
        output = self.root / "case-a-empty-inner-out.docx"
        report = fill_template(template, data, output)

        self.assertEqual(report["repeated_rows"], {"outer": 1, "outer.inner": 0})
        self.assertEqual(report["defaulted_fields"], [])

        doc_xml = _read_zip(output)["word/document.xml"]
        root = etree.fromstring(doc_xml)
        WN = f"{{{W}}}"

        # Outer table: header + 1 data row.
        outer_tbl = root.findall(f".//{WN}tbl")[0]
        outer_trs = outer_tbl.findall(f"{WN}tr")
        self.assertEqual(len(outer_trs), 2)

        # The data row's nested inner table has only its header row (template removed).
        data_row = outer_trs[1]
        inner_tbls = data_row.findall(f".//{WN}tbl")
        self.assertEqual(len(inner_tbls), 1)
        inner_trs = inner_tbls[0].findall(f"{WN}tr")
        self.assertEqual(len(inner_trs), 1)

        # Outer label "X" is filled; no unresolved tokens remain.
        all_text = _visible_text(doc_xml)
        self.assertIn("X", all_text)
        self.assertNotIn("{{", all_text)

    def test_cli_inspect_fill_validate(self) -> None:
        data_path = self.root / "data.json"
        data_path.write_text(json.dumps(self.data), encoding="utf-8")
        manifest = self.root / "manifest.json"
        output = self.root / "cli-output.docx"
        summary = self.root / "summary.json"
        validation = self.root / "validation.json"
        script = HERE / "docx_template.py"

        commands = [
            [
                sys.executable,
                str(script),
                "inspect",
                str(self.template),
                "--output",
                str(manifest),
            ],
            [
                sys.executable,
                str(script),
                "fill",
                str(self.template),
                str(data_path),
                str(output),
                "--summary",
                str(summary),
            ],
            [
                sys.executable,
                str(script),
                "validate",
                str(output),
                "--template",
                str(self.template),
                "--output",
                str(validation),
            ],
        ]
        for command in commands:
            result = subprocess.run(
                command, capture_output=True, text=True, encoding="utf-8"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        for path in (manifest, output, summary, validation):
            self.assertTrue(path.exists(), path)
        self.assertTrue(
            json.loads(validation.read_text(encoding="utf-8"))["valid_docx"]
        )


# ---------------------------------------------------------------------------
# Helpers for conditional tests
# ---------------------------------------------------------------------------

def _build_body_conditional_template(
    output: Path,
    paragraphs: list[str],
) -> None:
    """Build a minimal DOCX whose body is a sequence of paragraphs from *paragraphs*."""
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(output)


def _build_table_conditional_template(
    output: Path,
    rows: list[str],
) -> None:
    """Build a DOCX with a single-column table; each entry in *rows* is one row."""
    doc = Document()
    table = doc.add_table(rows=len(rows), cols=1)
    for i, text in enumerate(rows):
        table.rows[i].cells[0].text = text
    doc.save(output)


class ConditionalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    # ------------------------------------------------------------------
    # _parse_condition unit tests (no DOCX needed)
    # ------------------------------------------------------------------

    def test_truthy_check_true(self) -> None:
        from docx_template import _parse_condition, _MISSING
        self.assertTrue(_parse_condition("a", {"a": "yes"}))
        self.assertTrue(_parse_condition("a", {"a": 1}))
        self.assertTrue(_parse_condition("a", {"a": True}))

    def test_truthy_check_false(self) -> None:
        from docx_template import _parse_condition
        self.assertFalse(_parse_condition("a", {"a": ""}))
        self.assertFalse(_parse_condition("a", {"a": 0}))
        self.assertFalse(_parse_condition("a", {"a": False}))
        self.assertFalse(_parse_condition("a", {"a": None}))
        self.assertFalse(_parse_condition("a", {}))  # missing → falsy

    def test_equality_string(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(_parse_condition('a == "permanent"', {"a": "permanent"}))
        self.assertFalse(_parse_condition('a == "permanent"', {"a": "hourly"}))

    def test_inequality_string(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(_parse_condition('a != "permanent"', {"a": "hourly"}))
        self.assertFalse(_parse_condition('a != "permanent"', {"a": "permanent"}))

    def test_equality_bool(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(_parse_condition("a == true", {"a": True}))
        self.assertFalse(_parse_condition("a == true", {"a": False}))
        self.assertTrue(_parse_condition("a == false", {"a": False}))

    def test_equality_null(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(_parse_condition("a == null", {"a": None}))
        self.assertFalse(_parse_condition("a == null", {"a": "x"}))

    def test_equality_number(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(_parse_condition("a == 42", {"a": 42}))
        self.assertFalse(_parse_condition("a == 42", {"a": 0}))

    def test_nested_path(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(
            _parse_condition('employee.type == "permanent"', {"employee": {"type": "permanent"}})
        )

    # ------------------------------------------------------------------
    # Body-level if/else blocks
    # ------------------------------------------------------------------

    def test_if_true_branch_kept(self) -> None:
        template = self.root / "if-true.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.is_active}}',
            'Active employee text',
            '{{/if}}',
        ])
        output = self.root / "if-true-out.docx"
        report = fill_template(template, {"employee": {"is_active": True}}, output)
        self.assertIn("employee.is_active", report["conditional_fields"])
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("Active employee text", text)
        self.assertNotIn("{{", text)

    def test_if_false_branch_removed(self) -> None:
        template = self.root / "if-false.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.is_active}}',
            'Active employee text',
            '{{/if}}',
        ])
        output = self.root / "if-false-out.docx"
        fill_template(template, {"employee": {"is_active": False}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertNotIn("Active employee text", text)
        self.assertNotIn("{{", text)

    def test_if_else_true(self) -> None:
        template = self.root / "if-else-true.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.type == "permanent"}}',
            'Annual salary',
            '{{#else}}',
            'Hourly rate',
            '{{/if}}',
        ])
        output = self.root / "if-else-true-out.docx"
        fill_template(template, {"employee": {"type": "permanent"}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("Annual salary", text)
        self.assertNotIn("Hourly rate", text)
        self.assertNotIn("{{", text)

    def test_if_else_false(self) -> None:
        template = self.root / "if-else-false.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.type == "permanent"}}',
            'Annual salary',
            '{{#else}}',
            'Hourly rate',
            '{{/if}}',
        ])
        output = self.root / "if-else-false-out.docx"
        fill_template(template, {"employee": {"type": "hourly"}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertNotIn("Annual salary", text)
        self.assertIn("Hourly rate", text)
        self.assertNotIn("{{", text)

    def test_if_with_scalar_placeholders(self) -> None:
        """Scalar tokens inside a kept branch are still filled."""
        template = self.root / "if-scalar.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.type == "permanent"}}',
            'Salary: {{employee.salary}}',
            '{{/if}}',
        ])
        output = self.root / "if-scalar-out.docx"
        fill_template(
            template,
            {"employee": {"type": "permanent", "salary": "90000"}},
            output,
        )
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("90000", text)
        self.assertNotIn("{{", text)

    def test_missing_condition_path_is_falsy(self) -> None:
        """A path that doesn't exist in JSON evaluates to false."""
        template = self.root / "if-missing.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.bonus_eligible}}',
            'Bonus info',
            '{{/if}}',
        ])
        output = self.root / "if-missing-out.docx"
        fill_template(template, {"employee": {}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertNotIn("Bonus info", text)
        self.assertNotIn("{{", text)

    # ------------------------------------------------------------------
    # inspect_template surfaces conditional paths
    # ------------------------------------------------------------------

    def test_inspect_reports_conditional_paths(self) -> None:
        template = self.root / "inspect-cond.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.type == "permanent"}}',
            'Salary: {{employee.salary}}',
            '{{/if}}',
            '{{#switch employee.status}}',
            '{{#case "active"}}',
            'Active',
            '{{/switch}}',
        ])
        manifest = inspect_template(template)
        self.assertIn("employee.type", manifest["conditional_paths"])
        self.assertIn("employee.status", manifest["conditional_paths"])
        self.assertIn("employee.salary", manifest["scalar_placeholders"])

    def test_inspect_compound_condition_paths(self) -> None:
        """inspect extracts every JSON path from && / || compound conditions."""
        template = self.root / "inspect-compound.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.type == "permanent" && employee.status == "active"}}',
            'Bonus eligible',
            '{{/if}}',
            '{{#if employee.is_senior || employee.is_lead}}',
            'Leadership allowance',
            '{{/if}}',
        ])
        manifest = inspect_template(template)
        for path in ("employee.type", "employee.status", "employee.is_senior", "employee.is_lead"):
            self.assertIn(path, manifest["conditional_paths"],
                          f"{path!r} missing from conditional_paths")

    # ------------------------------------------------------------------
    # Switch / case
    # ------------------------------------------------------------------

    def test_switch_matching_case(self) -> None:
        template = self.root / "switch-match.docx"
        _build_body_conditional_template(template, [
            '{{#switch employee.type}}',
            '{{#case "permanent"}}',
            'Permanent employee rules',
            '{{#case "hourly"}}',
            'Hourly employee rules',
            '{{/switch}}',
        ])
        output = self.root / "switch-match-out.docx"
        report = fill_template(template, {"employee": {"type": "permanent"}}, output)
        self.assertIn("employee.type", report["conditional_fields"])
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("Permanent employee rules", text)
        self.assertNotIn("Hourly employee rules", text)
        self.assertNotIn("{{", text)

    def test_switch_second_case(self) -> None:
        template = self.root / "switch-second.docx"
        _build_body_conditional_template(template, [
            '{{#switch employee.type}}',
            '{{#case "permanent"}}',
            'Permanent employee rules',
            '{{#case "hourly"}}',
            'Hourly employee rules',
            '{{/switch}}',
        ])
        output = self.root / "switch-second-out.docx"
        fill_template(template, {"employee": {"type": "hourly"}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertNotIn("Permanent employee rules", text)
        self.assertIn("Hourly employee rules", text)
        self.assertNotIn("{{", text)

    def test_switch_no_match_removes_all_cases(self) -> None:
        template = self.root / "switch-nomatch.docx"
        _build_body_conditional_template(template, [
            '{{#switch employee.type}}',
            '{{#case "permanent"}}',
            'Permanent only',
            '{{/switch}}',
        ])
        output = self.root / "switch-nomatch-out.docx"
        fill_template(template, {"employee": {"type": "contractor"}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertNotIn("Permanent only", text)
        self.assertNotIn("{{", text)

    # ------------------------------------------------------------------
    # Table-row-level conditionals
    # ------------------------------------------------------------------

    def test_row_level_if_true(self) -> None:
        template = self.root / "row-if-true.docx"
        _build_table_conditional_template(template, [
            'Header',
            '{{#if show_bonus}}',
            'Bonus row',
            '{{/if}}',
            'Footer row',
        ])
        output = self.root / "row-if-true-out.docx"
        fill_template(template, {"show_bonus": True}, output)
        doc = Document(output)
        texts = [row.cells[0].text for row in doc.tables[0].rows]
        self.assertIn("Bonus row", texts)

    def test_row_level_if_false(self) -> None:
        template = self.root / "row-if-false.docx"
        _build_table_conditional_template(template, [
            'Header',
            '{{#if show_bonus}}',
            'Bonus row',
            '{{/if}}',
            'Footer row',
        ])
        output = self.root / "row-if-false-out.docx"
        fill_template(template, {"show_bonus": False}, output)
        doc = Document(output)
        texts = [row.cells[0].text for row in doc.tables[0].rows]
        self.assertNotIn("Bonus row", texts)
        self.assertIn("Header", texts)
        self.assertIn("Footer row", texts)

    def test_row_level_switch(self) -> None:
        template = self.root / "row-switch.docx"
        _build_table_conditional_template(template, [
            'Header',
            '{{#switch pay_type}}',
            '{{#case "salary"}}',
            'Salary row',
            '{{#case "hourly"}}',
            'Hourly row',
            '{{/switch}}',
        ])
        output = self.root / "row-switch-out.docx"
        fill_template(template, {"pay_type": "salary"}, output)
        doc = Document(output)
        texts = [row.cells[0].text for row in doc.tables[0].rows]
        self.assertIn("Salary row", texts)
        self.assertNotIn("Hourly row", texts)

    # ------------------------------------------------------------------
    # Interaction: conditionals + repeating rows
    # ------------------------------------------------------------------

    def test_conditional_block_with_enclosed_table(self) -> None:
        """A conditional block that wraps an entire table keeps/removes it."""
        from docx import Document as DocxDoc
        template = self.root / "cond-table.docx"
        doc = DocxDoc()
        doc.add_paragraph("{{#if show_table}}")
        tbl = doc.add_table(rows=2, cols=1)
        tbl.rows[0].cells[0].text = "Header"
        tbl.rows[1].cells[0].text = "Data"
        doc.add_paragraph("{{/if}}")
        doc.save(template)

        # show_table=True — table is kept
        out_true = self.root / "cond-table-true.docx"
        fill_template(template, {"show_table": True}, out_true)
        doc_true = DocxDoc(out_true)
        self.assertEqual(len(doc_true.tables), 1)

        # show_table=False — table is removed
        out_false = self.root / "cond-table-false.docx"
        fill_template(template, {"show_table": False}, out_false)
        doc_false = DocxDoc(out_false)
        self.assertEqual(len(doc_false.tables), 0)

    # ------------------------------------------------------------------
    # AND / OR logical operators
    # ------------------------------------------------------------------

    def test_and_both_true(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(
            _parse_condition(
                'employee.type == "permanent" && employee.status == "active"',
                {"employee": {"type": "permanent", "status": "active"}},
            )
        )

    def test_and_one_false(self) -> None:
        from docx_template import _parse_condition
        self.assertFalse(
            _parse_condition(
                'employee.type == "permanent" && employee.status == "active"',
                {"employee": {"type": "permanent", "status": "terminated"}},
            )
        )

    def test_or_first_true(self) -> None:
        from docx_template import _parse_condition
        self.assertTrue(
            _parse_condition(
                "employee.is_senior || employee.is_lead",
                {"employee": {"is_senior": True, "is_lead": False}},
            )
        )

    def test_or_both_false(self) -> None:
        from docx_template import _parse_condition
        self.assertFalse(
            _parse_condition(
                "employee.is_senior || employee.is_lead",
                {"employee": {"is_senior": False, "is_lead": False}},
            )
        )

    def test_and_precedence_over_or(self) -> None:
        """a && b || c  should be read as (a && b) || c."""
        from docx_template import _parse_condition
        # a=false, b=false, c=true  → (false && false) || true = true
        self.assertTrue(
            _parse_condition(
                'a == "x" && b == "y" || c == "z"',
                {"a": "no", "b": "no", "c": "z"},
            )
        )
        # a=true, b=false, c=false → (true && false) || false = false
        self.assertFalse(
            _parse_condition(
                'a == "x" && b == "y" || c == "z"',
                {"a": "x", "b": "no", "c": "no"},
            )
        )

    def test_and_or_in_template(self) -> None:
        """Full fill round-trip with a compound condition."""
        template = self.root / "and-or.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.type == "permanent" && employee.status == "active"}}',
            'Eligible for annual bonus',
            '{{/if}}',
        ])
        output_yes = self.root / "and-or-yes.docx"
        fill_template(
            template,
            {"employee": {"type": "permanent", "status": "active"}},
            output_yes,
        )
        self.assertIn(
            "Eligible for annual bonus",
            _visible_text(_read_zip(output_yes)["word/document.xml"]),
        )

        output_no = self.root / "and-or-no.docx"
        fill_template(
            template,
            {"employee": {"type": "permanent", "status": "terminated"}},
            output_no,
        )
        self.assertNotIn(
            "Eligible for annual bonus",
            _visible_text(_read_zip(output_no)["word/document.xml"]),
        )

    def test_or_in_template(self) -> None:
        """OR condition keeps the branch when either operand is true."""
        template = self.root / "or-tpl.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.is_manager || employee.is_director}}',
            'Leadership allowance',
            '{{/if}}',
        ])
        output = self.root / "or-tpl-out.docx"
        fill_template(
            template,
            {"employee": {"is_manager": False, "is_director": True}},
            output,
        )
        self.assertIn(
            "Leadership allowance",
            _visible_text(_read_zip(output)["word/document.xml"]),
        )

    # ------------------------------------------------------------------
    # Mismatched markers raise TemplateError
    # ------------------------------------------------------------------

    def test_stray_conditional_marker_fails_validation(self) -> None:
        """A stray {{#else}} or {{/if}} left in the output must be detected."""
        template = self.root / "stray-marker.docx"
        _build_body_conditional_template(template, ["Normal paragraph"])
        output = self.root / "stray-marker-out.docx"
        fill_template(template, {}, output)

        # Inject a stray conditional marker into the filled document.
        WN = f"{{{W}}}"
        parts = _read_zip(output)
        root = etree.fromstring(parts["word/document.xml"])
        first_p = root.find(f".//{WN}p")
        assert first_p is not None
        run = etree.SubElement(first_p, f"{WN}r")
        t = etree.SubElement(run, f"{WN}t")
        t.text = "{{#else}}"
        parts["word/document.xml"] = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8"
        )
        damaged = self.root / "stray-marker-damaged.docx"
        _write_zip(damaged, parts)
        with self.assertRaisesRegex(TemplateError, "[Uu]nresolved"):
            validate_docx(damaged, template_path=template)

    def test_hyphenated_switch_path(self) -> None:
        """{{#switch}} and {{#if}} must accept hyphenated path segments."""
        template = self.root / "hyphen-switch.docx"
        _build_body_conditional_template(template, [
            '{{#switch pay-type}}',
            '{{#case "salary"}}',
            'Salary rules',
            '{{#case "hourly"}}',
            'Hourly rules',
            '{{/switch}}',
        ])
        output = self.root / "hyphen-switch-out.docx"
        fill_template(template, {"pay-type": "hourly"}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("Hourly rules", text)
        self.assertNotIn("Salary rules", text)
        self.assertNotIn("{{", text)

    def test_nested_hyphenated_path(self) -> None:
        """Dotted hyphenated paths like employee.pay-type are accepted."""
        template = self.root / "hyphen-nested.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.pay-type == "permanent"}}',
            'Permanent section',
            '{{/if}}',
        ])
        output = self.root / "hyphen-nested-out.docx"
        fill_template(template, {"employee": {"pay-type": "permanent"}}, output)
        text = _visible_text(_read_zip(output)["word/document.xml"])
        self.assertIn("Permanent section", text)
        self.assertNotIn("{{", text)

    def test_unclosed_if_raises(self) -> None:
        template = self.root / "unclosed-if.docx"
        _build_body_conditional_template(template, [
            '{{#if employee.active}}',
            'Some text',
        ])
        output = self.root / "unclosed-if-out.docx"
        with self.assertRaisesRegex(TemplateError, r"\{\{#if\}\}|/if"):
            fill_template(template, {"employee": {"active": True}}, output)

    def test_unclosed_switch_raises(self) -> None:
        template = self.root / "unclosed-switch.docx"
        _build_body_conditional_template(template, [
            '{{#switch employee.type}}',
            '{{#case "x"}}',
            'Some text',
        ])
        output = self.root / "unclosed-switch-out.docx"
        with self.assertRaisesRegex(TemplateError, r"\{\{#switch\}\}|/switch"):
            fill_template(template, {"employee": {"type": "x"}}, output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
