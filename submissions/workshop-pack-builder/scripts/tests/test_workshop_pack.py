"""Regression checks: python -B -m unittest discover -s scripts/tests."""
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_deck
import build_docs
import build_source_map
import check_pack
import deck_preview
from pypdf import PdfWriter

SKILL = Path(__file__).resolve().parents[2]
EXAMPLE = SKILL / "assets" / "example"


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


class WorkshopPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec = json.loads((EXAMPLE / "workshop.example.json").read_text(encoding="utf-8"))
        self.smap = build_source_map.build(
            [str(EXAMPLE / "contoso-journey-mapping-guide.md")], {}, 6000)

    def test_documented_build_order_and_example_materials(self):
        deck = self.root / "new" / "pack" / "deck.pptx"
        count = build_deck.Deck(self.spec, self.smap, None, None).build(str(deck))
        self.assertTrue(deck.is_file())
        self.assertEqual(len(build_deck.Presentation(deck).slides), count)
        cite = build_docs.Cite(self.spec, self.smap)
        build_docs.build_guide(self.spec, cite, None, str(deck.parent))
        build_docs.build_workbook(self.spec, cite, None, str(deck.parent))
        guide = "\n".join(check_pack.docx_text(deck.parent / "facilitator-guide.docx"))
        workbook = "\n".join(check_pack.docx_text(deck.parent / "participant-workbook.docx"))
        slides = "\n".join(check_pack.pptx_text(deck))
        for snippet in ("A: The returns team checks the order", "B: I find my order on the website"):
            self.assertIn(snippet, slides)
            self.assertIn(snippet, guide)
        for output in (slides, guide, workbook):
            self.assertIn("entering an order number twice", output)
            self.assertNotIn("slide 12", output)
            self.assertNotIn("evidence cards", output.lower())
            self.assertNotIn("Exercise sheet 3", output)
        self.assertIn("Exercise sheet 1:", workbook)
        self.assertIn("Exercise sheet 2:", workbook)
        self.assertIn("Your work", workbook)
        findings = check_pack.check(self.spec, self.smap, str(deck.parent), str(deck))
        self.assertEqual([r for r in findings if r["level"] == "FAIL"], [])

    def test_html_font_names_cannot_escape_style_or_css_strings(self):
        payload = 'A";}body{background:url(https://example.invalid)}/*\n</style><script>alert(1)</script><style>\\'
        brand = {"fonts": {"major": payload, "minor": payload}}
        path = build_docs.build_html(
            self.spec, build_docs.Cite(self.spec, self.smap), brand, str(self.root))[0]
        page = Path(path).read_text(encoding="utf-8")
        parser = Tags()
        parser.feed(page)
        self.assertEqual(parser.tags.count("style"), 1)
        self.assertNotIn("script", parser.tags)
        self.assertNotIn(payload, page)
        self.assertIn(r"\3c \2f style\3e ", page)
        self.assertIn(r"\22 ", page)
        self.assertIn(r"\5c ", page)

    def test_html_rejects_non_hex_brand_colors(self):
        for value in ("red; background:url(https://example.invalid)", "</style><script>alert(1)</script>", "#gggggg"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "expected #RRGGBB"):
                build_docs.build_html(
                    self.spec, build_docs.Cite(self.spec, self.smap),
                    {"colors": {"accent1": value}}, str(self.root))

    def test_supplied_map_is_authoritative_for_bare_and_unit_citations(self):
        self.spec["sources"].append({"id": "S99"})
        for smap in (self.smap, {"sources": []}, {}):
            for ref in ("S99", "S99.sec1", "S1.missing"):
                with self.subTest(smap=smap, ref=ref):
                    spec = copy.deepcopy(self.spec)
                    spec["modules"][0]["key_points"][0]["sources"] = [ref]
                    findings = check_pack.check(spec, smap, None, None)
                    self.assertTrue(any(r["check"] == "citations" and r["where"] == "M1.kp1"
                                        for r in findings))
        for ref in ("S1", "S1.sec2"):
            self.spec["modules"][0]["key_points"][0]["sources"] = [ref]
            findings = check_pack.check(self.spec, self.smap, None, None)
            self.assertFalse(any(r["check"] == "citations" for r in findings))
        self.spec["modules"][0]["key_points"][0]["sources"] = ["S99"]
        findings = check_pack.check(self.spec, None, None, None)
        self.assertFalse(any(r["check"] == "citations" for r in findings))

    def test_unreadable_pdfs_are_reported_and_fail_when_only_input(self):
        for kind in ("corrupt", "encrypted", "empty", "blank"):
            path = self.root / f"{kind}.pdf"
            if kind == "corrupt":
                path.write_bytes(b"not a PDF")
            else:
                writer = PdfWriter()
                if kind != "empty":
                    writer.add_blank_page(width=100, height=100)
                if kind == "encrypted":
                    writer.encrypt("not-the-empty-password")
                writer.write(path)
            # Exercise the case where both readers fail, without requiring pdfplumber.
            with self.subTest(kind=kind), patch.dict(sys.modules, {"pdfplumber": None}), \
                    redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                result = build_source_map.build([str(path)], {}, 6000)
                self.assertEqual(result["sources"], [])
                self.assertEqual(result["errors"][0]["path"], str(path))
                self.assertIn("no extractable text", result["errors"][0]["error"])
                self.assertIn("Could not read", build_source_map.to_markdown(result))
                self.assertEqual(build_source_map.main([str(path)]), 1)
                mixed = build_source_map.build(
                    [str(path), str(EXAMPLE / "contoso-journey-mapping-guide.md")], {}, 6000)
                self.assertEqual(len(mixed["sources"]), 1)
                self.assertEqual(len(mixed["errors"]), 1)

    def test_pdf_fallback_with_readable_text_still_succeeds(self):
        fallback = MagicMock()
        fallback.open.return_value.__enter__.return_value.pages = [
            MagicMock(extract_text=lambda: "Readable fallback text")]
        with patch("pypdf.PdfReader", side_effect=ValueError("reader failed")), \
                patch.dict(sys.modules, {"pdfplumber": fallback}):
            units, _ = build_source_map.read_pdf("fallback.pdf")
        self.assertEqual(units[0]["text"], "Readable fallback text")

    def test_render_requires_successful_fresh_pdf(self):
        pdf = self.root / "deck.pdf"
        for exit_code, write_pdf, succeeds in ((1, False, False), (0, False, False),
                                               (1, True, False), (0, True, True)):
            with self.subTest(exit_code=exit_code, write_pdf=write_pdf):
                pdf.write_bytes(b"stale PDF")

                def convert(argv, **kwargs):
                    if "--convert-to" in argv:
                        self.assertFalse(pdf.exists())
                        if write_pdf:
                            pdf.write_bytes(b"fresh PDF")
                    return subprocess.CompletedProcess(argv, exit_code, "", "conversion detail")

                with patch.object(deck_preview.shutil, "which", side_effect=lambda name: name), \
                        patch.object(deck_preview.subprocess, "run", side_effect=convert) as run:
                    result, error = deck_preview.render("deck.pptx", str(self.root), 60)
                if succeeds:
                    self.assertIsNone(error)
                    self.assertEqual(result["pdf"], str(pdf))
                    self.assertEqual(run.call_count, 2)
                else:
                    self.assertIsNone(result)
                    self.assertIn("PDF conversion failed", error)
                    self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
