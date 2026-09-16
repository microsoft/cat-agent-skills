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


if __name__ == "__main__":
    unittest.main(verbosity=2)
