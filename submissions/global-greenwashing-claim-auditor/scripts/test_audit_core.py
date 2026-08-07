#!/usr/bin/env python3
import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from audit_core import (
    DEFAULT_RULES,
    Rules,
    audit_text,
    read_csv_units,
    read_docx_units,
    read_pptx_units,
    validate_public_url,
)


class AuditCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = Rules(DEFAULT_RULES)

    def test_region_specific_findings(self):
        result = audit_text(
            "Our eco-friendly product is carbon neutral through carbon offsets.",
            "conversation",
            "test",
            self.rules,
            ["CA", "EU", "UK"],
            date(2026, 9, 27),
            True,
        )
        codes = {finding["finding_code"] for finding in result["findings"]}
        self.assertIn("ANY-VAGUE", codes)
        self.assertIn("CA-MISLEADING", codes)
        self.assertIn("EU-GENERIC", codes)
        self.assertIn("EU-OFFSET-PRODUCT", codes)
        self.assertIn("UK-CLARITY", codes)

    def test_eu_rule_is_date_sensitive(self):
        result = audit_text(
            "An eco-friendly product.",
            "conversation",
            "test",
            self.rules,
            ["EU"],
            date(2026, 9, 26),
            True,
        )
        codes = {finding["finding_code"] for finding in result["findings"]}
        self.assertNotIn("EU-GENERIC", codes)

    def test_csv_locations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claims.csv"
            path.write_text("Title,Body\nOne,Eco-friendly packaging\n", encoding="utf-8")
            units = list(read_csv_units(path, ["Body"], None, self.rules))
        self.assertEqual(units, [("row 2, column Body", "Eco-friendly packaging")])

    def test_red_finding_retains_yellow_matches(self):
        result = audit_text(
            "Our eco-friendly and sustainable product.",
            "conversation",
            "test",
            self.rules,
            [],
            date(2026, 9, 27),
            True,
        )
        finding = next(
            finding
            for finding in result["findings"]
            if finding["finding_code"] == "ANY-VAGUE"
        )
        self.assertEqual(finding["rating"], "Red")
        self.assertEqual(finding["matched_terms"], ["eco-friendly", "sustainable"])

    def test_csv_column_hints_use_custom_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            csv_path = directory_path / "claims.csv"
            csv_path.write_text(
                "Title,CustomClaim\nIgnored,Eco-friendly packaging\n",
                encoding="utf-8",
            )
            rule_data = json.loads(DEFAULT_RULES.read_text(encoding="utf-8"))
            rule_data["text_column_hints"] = ["customclaim"]
            rules_path = directory_path / "rules.json"
            rules_path.write_text(json.dumps(rule_data), encoding="utf-8")
            units = list(read_csv_units(csv_path, [], None, Rules(rules_path)))
        self.assertEqual(
            units,
            [("row 2, column CustomClaim", "Eco-friendly packaging")],
        )

    def test_pptx_location_uses_shape_id_and_name(self):
        slide_xml = """\
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name="Group"/></p:nvGrpSpPr>
    <p:sp>
      <p:nvSpPr><p:cNvPr id="7" name="Claim Box"/></p:nvSpPr>
      <p:txBody><a:p><a:r><a:t>Eco-friendly</a:t></a:r></a:p></p:txBody>
    </p:sp>
  </p:spTree></p:cSld>
</p:sld>
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claims.pptx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", slide_xml)
            units = list(read_pptx_units(path, None))
        self.assertEqual(
            units,
            [("slide 1, shape 7 (Claim Box)", "Eco-friendly")],
        )

    def test_docx_table_paragraph_is_not_duplicated(self):
        document_xml = """\
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:tbl><w:tr><w:tc>
    <w:p><w:r><w:t>Eco-friendly</w:t></w:r></w:p>
  </w:tc></w:tr></w:tbl></w:body>
</w:document>
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claims.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            units = list(read_docx_units(path, None))
        self.assertEqual(units, [("table cell 1", "Eco-friendly")])

    def test_future_only_any_audit_does_not_crash(self):
        result = audit_text(
            "We aim to reduce emissions.",
            "conversation",
            "test",
            self.rules,
            [],
            date(2026, 9, 27),
            True,
        )
        self.assertEqual(
            [finding["finding_code"] for finding in result["findings"]],
            ["ANY-FUTURE"],
        )

    def test_current_net_zero_claim_is_not_a_future_commitment(self):
        result = audit_text(
            "We are net zero today.",
            "conversation",
            "test",
            self.rules,
            ["CA", "EU"],
            date(2026, 9, 27),
            True,
        )
        codes = {finding["finding_code"] for finding in result["findings"]}
        self.assertNotIn("ANY-FUTURE", codes)
        self.assertNotIn("CA-FUTURE", codes)
        self.assertNotIn("EU-FUTURE", codes)

    def test_url_validation_rejects_non_public_addresses(self):
        for url in (
            "http://127.0.0.1/",
            "http://10.0.0.1/",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_public_url(url)


if __name__ == "__main__":
    unittest.main()
