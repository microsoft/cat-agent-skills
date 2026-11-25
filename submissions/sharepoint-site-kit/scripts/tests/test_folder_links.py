import contextlib
import html
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_folder_links as folders


SITE = "https://example.com/sites/demo"


class FolderLinkTests(unittest.TestCase):
    def test_round_trip_decodes_query_value_only_once(self):
        for name in ("Revenue%20Plan", "Literal%2FSlash", "Literal%2520", "Q&A + Planning", "Plan/Sub%2FFolder"):
            with self.subTest(name=name):
                link = folders.folder_link(SITE, name)
                self.assertEqual(folders.folder_from_link(html.escape(link), SITE, "Shared Documents"), name)

    def test_encoded_site_path_is_normalized_once(self):
        for site in ("https://example.com/sites/Program Hub", "https://example.com/sites/Program%20Hub"):
            with self.subTest(site=site):
                link = folders.folder_link(site, "Revenue%20Plan", "Documents partages")
                parsed = urlsplit(link)
                self.assertEqual(parsed.path, "/sites/Program%20Hub/Documents%20partages/Forms/AllItems.aspx")
                self.assertEqual(parse_qs(parsed.query)["id"],
                                 ["/sites/Program Hub/Documents partages/Revenue%20Plan"])
                self.assertEqual(folders.folder_from_link(link, site, "Documents partages"), "Revenue%20Plan")
        literal_site = "https://example.com/sites/Program%2520Hub"
        link = folders.folder_link(literal_site, "Literal%2FFolder")
        self.assertIn("/sites/Program%2520Hub/Shared%20Documents/", link)
        self.assertEqual(parse_qs(urlsplit(link).query)["id"],
                         ["/sites/Program%20Hub/Shared Documents/Literal%2FFolder"])
        self.assertEqual(folders.folder_from_link(link, literal_site, "Shared Documents"), "Literal%2FFolder")

    def test_links_cli_uses_resolved_library_url_name(self):
        for library in ("Dokumente", "Documents partag\u00e9s"):
            with self.subTest(library=library):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = folders.main(["links", "--site", "https://example.com/sites/Program%20Hub",
                                         "--library", library, "--names", "Activate"])
                self.assertEqual(code, 0)
                link = json.loads(output.getvalue())[0]["link"]
                self.assertEqual(parse_qs(urlsplit(link).query)["id"],
                                 [f"/sites/Program Hub/{library}/Activate"])
                self.assertNotIn("Shared", link)

    def check(self, root, names, current, *args, site=SITE, library="Shared Documents"):
        page = root / "page.html"
        listing = root / "folders.json"
        fixed = root / "fixed.html"
        original = "\n".join(
            f'<a data-folder="{html.escape(name)}" href="{html.escape(folders.folder_link(site, name, library))}">{html.escape(name)}</a>'
            for name in names)
        page.write_text(original, encoding="utf-8")
        listing.write_text(json.dumps(current), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = folders.main(["check", "--site", site, "--library", library, "--page", str(page), "--folders", str(listing),
                                 "--fix-out", str(fixed), *args])
        self.assertEqual(page.read_text(encoding="utf-8"), original)
        return code, json.loads(output.getvalue()), fixed.read_text(encoding="utf-8"), original

    def test_percent_escapes_do_not_trigger_false_repairs(self):
        with tempfile.TemporaryDirectory() as temp:
            names = ["Revenue%20Plan", "Literal%2FSlash"]
            code, report, fixed, original = self.check(Path(temp), names, names)
            self.assertEqual(code, 0)
            self.assertCountEqual(report["ok"], names)
            self.assertEqual(report["changed_links"], 0)
            self.assertEqual(fixed, original)

    def test_localized_library_upkeep_handles_encoded_site_and_folder_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            site = "https://example.com/sites/Program%20Hub"
            library = "Documents partages"
            code, report, fixed, _ = self.check(
                Path(temp), ["Revenue%20Plan", "Old"], ["Revenue%20Plan", "New"],
                "--rename", "Old=New", site=site, library=library)
            self.assertEqual(code, 0)
            self.assertEqual(report["ok"], ["Revenue%20Plan"])
            self.assertEqual(report["changed_links"], 1)
            self.assertIn('data-folder="New"', fixed)
            self.assertIn(html.escape(folders.folder_link(site, "New", library)), fixed)
            self.assertNotIn("Shared%20Documents", fixed)

    def test_only_confirmed_and_case_only_renames_are_rewritten(self):
        with tempfile.TemporaryDirectory() as temp:
            code, report, fixed, _ = self.check(Path(temp), ["Plan", "Kickstarter", "adopt"],
                                                 ["Plans", "Activate", "Adopt"],
                                                 "--rename", "Kickstarter=Activate")
            self.assertEqual(code, 1)
            self.assertEqual(report["changed_links"], 2)
            self.assertIn('data-folder="Plan"', fixed)
            self.assertIn(html.escape(folders.folder_link(SITE, "Plan")), fixed)
            self.assertNotIn('data-folder="Plans"', fixed)
            self.assertIn('data-folder="Activate"', fixed)
            self.assertIn(html.escape(folders.folder_link(SITE, "Activate")), fixed)
            self.assertIn('data-folder="Adopt"', fixed)
            self.assertNotIn('data-folder="adopt"', fixed)
            suggestion = next(r for r in report["renamed"] if r["link_folder"] == "Plan")
            self.assertFalse(suggestion["fixable"])
            self.assertIn(suggestion, report["broken"])
            self.assertIn("Plans", [u["folder"] for u in report["unlinked"]])

    def test_similarity_only_produces_suggestions(self):
        with tempfile.TemporaryDirectory() as temp:
            code, report, fixed, original = self.check(Path(temp), ["Plan"], ["Plans"])
            self.assertEqual(code, 1)
            self.assertEqual(report["changed_links"], 0)
            self.assertEqual(report["renamed"][0]["suggested_folder"], "Plans")
            self.assertEqual(fixed, original)


if __name__ == "__main__":
    unittest.main()
