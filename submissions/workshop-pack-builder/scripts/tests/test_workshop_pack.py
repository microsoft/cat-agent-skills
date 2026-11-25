"""Regression checks: python -B -m unittest discover -s scripts/tests."""
import copy
import io
import json
import re
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
import extract_brand
import timing
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
        build_docs.build_agenda(self.spec, cite, None, str(deck.parent))
        build_docs.build_guide(self.spec, cite, None, str(deck.parent))
        build_docs.build_workbook(self.spec, cite, None, str(deck.parent))
        build_docs.build_preread(self.spec, cite, None, str(deck.parent))
        build_docs.build_survey(self.spec, cite, None, str(deck.parent))
        build_docs.build_email(self.spec, str(deck.parent))
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

    def test_gate_rejects_missing_core_and_requested_optional_files(self):
        spec_path = self.root / "workshop.json"
        spec_path.write_text(json.dumps(self.spec), encoding="utf-8")
        pack = self.root / "pack"
        deck = pack / "deck.pptx"
        build_deck.Deck(self.spec, self.smap, None, None).build(str(deck))
        with redirect_stdout(io.StringIO()):
            build_docs.main([str(spec_path), "--out-dir", str(pack), "--html"])
            self.assertEqual(check_pack.main(
                [str(spec_path), "--pack-dir", str(pack), "--deck", str(deck), "--html"]), 0)
        for path in sorted(pack.iterdir()):
            with self.subTest(missing=path.name):
                content = path.read_bytes()
                path.unlink()
                findings = check_pack.check(self.spec, self.smap, str(pack), None, require_html=True)
                self.assertTrue(any(r["level"] == "FAIL" and r["check"] == "pack"
                                    and r["where"] == path.name for r in findings))
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(check_pack.main(
                        [str(spec_path), "--pack-dir", str(pack), "--html"]), 1)
                path.write_bytes(content)
        for name in ("pre-read.docx", "feedback-survey.docx", "follow-up-email-draft.md", "workshop.html"):
            (pack / name).unlink()
        core_spec = copy.deepcopy(self.spec)
        for key in ("pre_read", "survey", "follow_up_email"):
            del core_spec[key]
        findings = check_pack.check(core_spec, self.smap, str(pack), None)
        self.assertFalse(any(r["level"] == "FAIL" for r in findings))
        notes_only = self.root / "notes-only"
        notes_only.mkdir()
        (notes_only / "notes.txt").write_text("Notes", encoding="utf-8")
        findings = check_pack.check(core_spec, self.smap, str(notes_only), str(deck))
        self.assertEqual(sum(r["check"] == "pack" and r["level"] == "FAIL" for r in findings), 5)
        self.assertTrue(any(r["level"] == "FAIL" for r in
                            check_pack.check(core_spec, self.smap, None, None, require_html=True)))

    def test_workbook_cites_source_units_on_each_exercise_sheet(self):
        exercises = [a for m in self.spec["modules"] for a in m.get("activities", [])
                     if a["kind"] == "exercise"]
        exercises[0]["sources"] = ["S2.sec1"]
        self.smap["sources"].append({
            "id": "S2", "title": "Second source",
            "units": [{"ref": "S2.sec1", "heading": "Mapping practice"}]})
        cite = build_docs.Cite(self.spec, self.smap)
        path = build_docs.build_workbook(self.spec, cite, None, str(self.root))[0]
        text = "\n".join(check_pack.docx_text(path))
        sheets = re.split(r"(?m)^Exercise sheet \d+:", text)
        self.assertIn("Grounded in: (S2: Mapping practice)", sheets[1])
        self.assertNotIn("S1: Pilot results", sheets[1])
        self.assertIn("Grounded in: (S1: Finding pain points; S1: Moments that matter; S1: Pilot results)",
                      sheets[2])

    def test_source_map_creates_missing_output_directories(self):
        json_path = self.root / "working" / "source_map.json"
        md_path = self.root / "separate" / "index" / "source_map.md"
        with redirect_stdout(io.StringIO()):
            code = build_source_map.main([
                str(EXAMPLE / "contoso-journey-mapping-guide.md"),
                "--json-out", str(json_path), "--md-out", str(md_path)])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(json_path.read_text(encoding="utf-8"))["sources"]), 1)
        self.assertIn("S1.sec8", md_path.read_text(encoding="utf-8"))

    def test_blank_only_template_is_rejected_for_all_slide_types(self):
        template = self.root / "blank-only.pptx"
        prs = build_deck.Presentation()
        master = prs.slide_masters[0]
        layout_ids = master.slide_layouts._sldLayoutIdLst
        for layout_id in list(layout_ids):
            if master.part.related_slide_layout(layout_id.rId).name != "Blank":
                master.part.drop_rel(layout_id.rId)
                layout_ids.remove(layout_id)
        prs.save(template)
        for kind in ("title", "section", "content", "titleonly"):
            with self.subTest(kind=kind):
                deck = build_deck.Deck(self.spec, self.smap, None, str(template))
                with self.assertRaisesRegex(ValueError, "layout 'Blank'.*omit --template"):
                    deck._new(kind)
        spec_path = self.root / "workshop.json"
        spec_path.write_text(json.dumps(self.spec), encoding="utf-8")
        out = self.root / "deck.pptx"
        error = io.StringIO()
        with redirect_stderr(error):
            self.assertEqual(build_deck.main(
                [str(spec_path), "--out", str(out), "--template", str(template)]), 1)
        self.assertIn("missing required text placeholder", error.getvalue())
        self.assertFalse(out.exists())

    def test_standard_template_preserves_required_slide_text(self):
        template = self.root / "standard.pptx"
        build_deck.Presentation().save(template)
        path = self.root / "deck.pptx"
        build_deck.Deck(self.spec, self.smap, None, str(template)).build(str(path))
        slides = build_deck.Presentation(path).slides
        texts = ["\n".join(sh.text for sh in slide.shapes if sh.has_text_frame) for slide in slides]
        self.assertIn(self.spec["title"], texts[0])
        self.assertIn(self.spec["subtitle"], texts[0])
        self.assertTrue(any("Agenda" in text for text in texts))
        self.assertTrue(any("Break: 5 min" in text and "Back at 11:00" in text for text in texts))
        for i, module in enumerate((m for m in self.spec["modules"] if m["type"] != "break"), 1):
            self.assertTrue(any(f"{i}. {module['title']}" in text
                                and f"{module['minutes']} min" in text for text in texts))

    def test_closing_only_mentions_requested_optional_outputs(self):
        for survey, email in ((False, False), (False, True), (True, False), (True, True)):
            with self.subTest(survey=survey, email=email):
                spec = copy.deepcopy(self.spec)
                if not survey:
                    spec.pop("survey")
                if not email:
                    spec.pop("follow_up_email")
                deck = build_deck.Deck(spec, self.smap, None, None)
                deck.closing()
                slide = deck.prs.slides[0]
                text = "\n".join(sh.text for sh in slide.shapes if sh.has_text_frame)
                notes = slide.notes_slide.notes_text_frame.text
                for content in (text, notes):
                    self.assertEqual("survey" in content, survey)
                    self.assertEqual("follow-up" in content, email)
                self.assertIn("Check your commitment", text)

    def test_html_uses_readable_header_and_chip_foregrounds(self):
        for background in ("#FFFFFF", "#FFFFDD", "#777777", "#000000", "#0F2A44"):
            with self.subTest(background=background):
                path = build_docs.build_html(
                    self.spec, build_docs.Cite(self.spec, self.smap),
                    {"colors": {"dk2": background, "accent1": background}}, str(self.root))[0]
                page = Path(path).read_text(encoding="utf-8")
                for selector in ("header", r"\.chip"):
                    match = re.search(selector + r"\{background:(#[0-9A-Fa-f]{6});color:(#[0-9A-Fa-f]{6});", page)
                    self.assertIsNotNone(match)
                    bg, fg = match.groups()
                    self.assertEqual(bg, background)
                    self.assertGreaterEqual(extract_brand.contrast(bg, fg), 4.5)
                    if background == "#FFFFFF":
                        self.assertEqual(fg, "#000000")
                    elif background == "#000000":
                        self.assertEqual(fg, "#FFFFFF")

    def test_preread_validates_supplied_refs_but_allows_preparation_without_sources(self):
        for refs, valid in ((["S99.sec1"], False), (["S1.missing"], False),
                            (["S1.sec2"], True), (["S1"], True), ([], True)):
            with self.subTest(refs=refs):
                self.spec["pre_read"]["items"][0]["sources"] = refs
                findings = check_pack.check(self.spec, self.smap, None, None)
                citations = [r for r in findings if r["check"] == "citations"
                             and r["where"].startswith("pre_read.")]
                self.assertEqual(not citations, valid)
                if not valid:
                    self.assertEqual(citations[0]["where"], "pre_read.item1")
        self.spec.pop("pre_read")
        self.assertFalse(any(r["check"] == "citations" for r in
                             check_pack.check(self.spec, self.smap, None, None)))

    def test_fractional_draft_minutes_return_validation_findings_from_both_clis(self):
        self.spec["total_minutes"] = 15
        self.spec["modules"] = [self.spec["modules"][0]]
        self.spec["modules"][0]["minutes"] = 12.5
        spec_path = self.root / "workshop.json"
        spec_path.write_text(json.dumps(self.spec), encoding="utf-8")
        for main, args in ((timing.main, ["check", str(spec_path), "--json"]),
                           (check_pack.main, [str(spec_path), "--json"])):
            with self.subTest(cli=main.__module__):
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main(args), 1)
                result = json.loads(output.getvalue())
                self.assertFalse(result["passed"])
                details = "\n".join(r["detail"] for r in result["results"])
                self.assertIn("use 15", details)
                self.assertIn("diff -2.5", details)

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
