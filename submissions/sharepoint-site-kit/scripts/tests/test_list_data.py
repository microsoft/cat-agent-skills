import contextlib
import copy
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import allowlist_from_list as allowlist
import build_list_view as builder


SOURCE = {"kind": "list", "spItemUrl": "list:https://example.com/sites/demo/resources",
          "webUrl": "https://example.com/sites/demo", "listId": "resources", "label": "Resources"}


def config(key="resources"):
    return {"key": key, "source": dict(SOURCE),
            "columns": {"id": ["ID"], "title": ["Title"], "url": ["Link"],
                        "description": [], "people": ["Owners"], "date": []},
            "filters": [{"key": "owners", "columns": ["Owners"], "type": "personOrGroup",
                         "multi": True}], "sensitive": []}


def section(cfg, snapshot=None):
    key = cfg["key"]
    return (f'<!-- list-view:{key}:start -->\n<section data-list-view="{key}">'
            f'<script type="application/json" class="lv-config">{json.dumps(cfg)}</script>'
            f'<script type="application/json" class="lv-snapshot">{json.dumps(snapshot)}</script>'
            f'</section>\n<!-- list-view:{key}:end -->\n')


def page(gallery=False, configs=()):
    sources = {c["source"]["spItemUrl"]: c["source"] for c in configs}
    if gallery:
        sources[SOURCE["spItemUrl"]] = SOURCE
    head = (f'<script type="application/json" class="ka-livedata-manifest">'
            f'{json.dumps(list(sources.values()))}</script>')
    if gallery:
        head += (f'<script type="application/json" id="site-page-config">'
                 f'{json.dumps({"publicationSource": SOURCE})}</script>'
                 '<script type="application/json" id="snapshot-data">null</script>')
    return (f'<html><head><title>Test</title>{head}<style></style></head>'
            '<body><main><div>' + "".join(section(c) for c in configs)
            + '<!-- list-view:insert --></div></main>' + allowlist.nav_block([])
            + '</body></html>')


def script_json(text, selector):
    return json.loads(re.search(
        rf'<script type="application/json" {selector}>(.*?)</script>', text, re.S
    ).group(1).replace("<\\/", "</"))


def snapshot_rows(snapshot):
    return json.loads(snapshot["payload"]["content"])


class ListDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "page.html"

    def write_json(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def refresh(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            code = allowlist.main([*args, "--page", str(self.path)])
        return code, output.getvalue()

    def test_gallery_requires_approved_columns_without_writing(self):
        original = page(gallery=True)
        self.path.write_text(original, encoding="utf-8")
        items = self.write_json("items.json", [{"ID": 1, "Title": "Public", "Secret": "private"}])
        code, error = self.refresh("--items", items, "--snapshot")
        self.assertEqual(code, 2)
        self.assertIn("audience-approved", error)
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_gallery_filters_fields_before_both_outputs(self):
        data = {"value": [{"id": "1", "fields": {
            "Title": "Public", "Link": "https://example.com/public",
            "InternalNotes": "private-marker", "PrivateUrl": "https://example.com/private"}}]}
        for shape in (data, {"headers": ["ID", "Title", "Link", "InternalNotes", "PrivateUrl"],
                             "rows": [[1, "Public", "https://example.com/public",
                                       "private-marker", "https://example.com/private"]]}):
            with self.subTest(shape=type(shape)):
                self.path.write_text(page(gallery=True), encoding="utf-8")
                items = self.write_json("items.json", shape)
                self.assertEqual(self.refresh("--items", items, "--columns", "ID", "Title", "Link", "--snapshot")[0], 0)
                result = self.path.read_text(encoding="utf-8")
                saved = snapshot_rows(script_json(result, 'id="snapshot-data"'))
                self.assertEqual(saved["headers"], ["ID", "Title", "Link"] if "headers" in shape else ["Title", "Link", "ID"])
                self.assertNotIn("private", result)
                self.assertIn('href="https://example.com/public"', result)

    def test_combined_gallery_and_section_refresh_rebuilds_union(self):
        cfg = config()
        cfg["source"]["spItemUrl"] += "-other"
        self.path.write_text(page(gallery=True, configs=[cfg]), encoding="utf-8")
        gallery = self.write_json("gallery.json", [{"ID": 1, "Title": "Gallery",
                                                  "Link": "https://example.com/gallery", "Secret": "private-gallery"}])
        resources = self.write_json("resources.json", [{"ID": 2, "Title": "Section",
                                                        "Link": "https://example.com/section", "Owners": "Alex",
                                                        "Secret": "private-section"}])
        args = ["--items", gallery, resources, "--view", "@gallery", "resources",
                "--columns", "ID", "Title", "Link", "--snapshot"]
        self.assertEqual(self.refresh(*args)[0], 0)
        result = self.path.read_text(encoding="utf-8")
        self.assertIn('href="https://example.com/gallery"', result)
        self.assertIn('href="https://example.com/section"', result)
        self.assertNotIn("private-", result)
        self.assertNotIn("Owners", snapshot_rows(script_json(result, 'id="snapshot-data"'))["headers"])
        self.assertIn("Owners", snapshot_rows(script_json(result, 'class="lv-snapshot"'))["headers"])
        Path(gallery).write_text(json.dumps([{"ID": 1, "Title": "New", "Link": "https://example.com/new"}]), encoding="utf-8")
        self.assertEqual(self.refresh(*args)[0], 0)
        result = self.path.read_text(encoding="utf-8")
        self.assertNotIn("https://example.com/gallery", result)
        self.assertIn('href="https://example.com/new"', result)
        self.assertIn('href="https://example.com/section"', result)

    def test_partial_or_duplicate_refresh_does_not_replace_allowlist(self):
        original = page(gallery=True, configs=[config()])
        items = self.write_json("items.json", [{"ID": 1, "Title": "Public"}])
        for args in (["--items", items, "--view", "resources"],
                     ["--items", items, "--columns", "ID", "Title"],
                     ["--items", items, items, "--view", "resources", "resources"]):
            with self.subTest(args=args):
                self.path.write_text(original, encoding="utf-8")
                self.assertEqual(self.refresh(*args)[0], 2)
                self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_section_snapshot_excludes_sensitive_fields(self):
        cfg = config()
        cfg["columns"]["description"] = ["InternalNotes"]
        cfg["sensitive"] = ["internalnotes"]
        self.path.write_text(page(configs=[cfg]), encoding="utf-8")
        items = self.write_json("items.json", [{"ID": 1, "Title": "Public", "Owners": "Alex",
                                               "InternalNotes": "https://example.com/private"}])
        self.assertEqual(self.refresh("--items", items, "--view", "resources", "--snapshot")[0], 0)
        self.assertNotIn("https://example.com/private", self.path.read_text(encoding="utf-8"))

    def test_unresolved_lookup_values_rejected(self):
        for fields in ({"OwnersLookupId": "12"}, {"OwnersLookupId": ["12", "13"]},
                       {"Owners": [{"LookupId": 12}]},
                       {"Owners": '[{"LookupId":12}]'}):
            with self.subTest(fields=fields):
                items = [{"ID": 1, "Title": "Public", **fields}]
                cols = [{"name": "Title", "text": {}}, {"name": "Owners", "personOrGroup": {}}]
                with self.assertRaisesRegex(ValueError, "expanded tool payload"):
                    builder.propose(cols, items, set(), set(), None, 3)
                self.path.write_text(page(configs=[config()]), encoding="utf-8")
                path = self.write_json("items.json", items)
                code, error = self.refresh("--items", path, "--view", "resources", "--snapshot")
                self.assertEqual(code, 2)
                self.assertIn("expanded tool payload", error)

    def test_expanded_people_propose_and_survive_snapshot(self):
        items = [{"ID": i, "Title": f"Item {i}", "OwnersLookupId": str(i),
                  "Owners": [{"LookupId": i, "LookupValue": name}]}
                 for i, name in enumerate(("Alex", "Jordan"), 1)]
        cols = [{"name": "Title", "text": {}}, {"name": "Owners", "personOrGroup": {}}]
        proposal = builder.propose(cols, items, set(), set(), None, 3)
        self.assertEqual(proposal["columns"]["people"], ["Owners"])
        self.assertEqual(proposal["distinct"], [2])
        self.path.write_text(page(configs=[config()]), encoding="utf-8")
        path = self.write_json("items.json", items)
        self.assertEqual(self.refresh("--items", path, "--view", "resources", "--snapshot")[0], 0)
        result = self.path.read_text(encoding="utf-8")
        saved = snapshot_rows(script_json(result, 'class="lv-snapshot"'))
        self.assertNotIn("OwnersLookupId", saved["headers"])
        owner_index = saved["headers"].index("Owners")
        self.assertEqual([builder.values_of({"Owners": r[owner_index]}, "Owners") for r in saved["rows"]],
                         [["Alex"], ["Jordan"]])

    def test_build_refresh_and_static_conversion_with_expanded_people(self):
        columns = self.write_json("columns.json", [
            {"name": "Title", "text": {}}, {"name": "Link", "hyperlinkOrPicture": {}},
            {"name": "Owners", "personOrGroup": {"allowMultipleSelection": True}}])
        items = self.write_json("items.json", [
            {"ID": 1, "Title": "First", "Link": "https://example.com/first", "Owners": "Alex"},
            {"ID": 2, "Title": "Second", "Link": "https://example.com/second", "Owners": "Jordan"}])
        template = Path(builder.HERE).parent / "assets" / "static-page-template.html"
        self.path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        args = ["--columns", columns, "--items", items, "--label", "Resources",
                "--web-url", SOURCE["webUrl"], "--list-id", SOURCE["listId"],
                "--key", "resources", "--into", str(self.path)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(builder.main(args), 0)
        self.assertEqual(self.refresh("--items", items, "--view", "resources", "--snapshot")[0], 0)
        result = self.path.read_text(encoding="utf-8")
        cfg = script_json(result, 'class="lv-config"')
        self.assertEqual(cfg["filters"][0]["columns"], ["Owners"])
        self.assertEqual(len(snapshot_rows(script_json(result, 'class="lv-snapshot"'))["rows"]), 2)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(builder.main([*args, "--static-snapshot"]), 0)
        result = self.path.read_text(encoding="utf-8")
        self.assertIn("Alex", result)
        self.assertIn("Jordan", result)
        self.assertNotIn('class="ka-livedata-manifest"', result)
        self.assertNotIn('id="list-view-runtime"', result)

    def test_static_conversion_keeps_shared_manifest_consumers(self):
        for gallery, configs, keep in ((True, [config()], True),
                                       (False, [config(), config("another")], True),
                                       (False, [config()], False)):
            with self.subTest(gallery=gallery, sections=len(configs)):
                result, _ = builder.make_static(page(gallery, configs), "resources", SOURCE,
                                               '<section class="lv-static">Saved</section>', builder.parts())
                if keep:
                    self.assertIn(SOURCE, script_json(result, 'class="ka-livedata-manifest"'))
                else:
                    self.assertNotIn('class="ka-livedata-manifest"', result)
                self.assertEqual('id="site-page-config"' in result, gallery)

    def test_static_conversion_preserves_unrelated_manifest_entry(self):
        other = config("other")
        other["source"]["spItemUrl"] += "-other"
        result, _ = builder.make_static(page(configs=[config(), other]), "resources", SOURCE,
                                       '<section>Saved</section>', builder.parts())
        self.assertEqual(script_json(result, 'class="ka-livedata-manifest"'), [other["source"]])

    def test_rebuild_keeps_snapshot_only_for_compatible_config(self):
        cfg = config()
        snapshot = {"savedOn": "2026-01-01", "payload": {"private-marker": "old-data"}}
        original = page(configs=[cfg]).replace(section(cfg), section(cfg, snapshot))
        for field in (None, "source", "columns", "filters", "sensitive"):
            new = copy.deepcopy(cfg)
            if field == "source":
                new[field]["listId"] = "different"
                new[field]["spItemUrl"] += "-different"
            elif field == "columns":
                new[field]["people"] = []
            elif field == "filters":
                new[field] = []
            elif field == "sensitive":
                new[field] = ["Owners"]
            with self.subTest(field=field):
                result, _ = builder.insert_into(original, "resources", new["source"], section(new), builder.parts())
                self.assertEqual(script_json(result, 'class="lv-snapshot"'), snapshot if field is None else None)
                self.assertEqual("old-data" in result, field is None)

    def test_incomplete_graph_page_is_rejected(self):
        incomplete = {"value": [{"id": "1", "fields": {"Title": "First"}}],
                      "@odata.nextLink": "https://graph.microsoft.com/next"}
        items = self.write_json("items.json", incomplete)
        original = page(gallery=True)
        self.path.write_text(original, encoding="utf-8")
        code, error = self.refresh("--items", items, "--columns", "ID", "Title", "--snapshot")
        self.assertEqual(code, 2)
        self.assertIn("@odata.nextLink", error)
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)
        self.assertEqual(len(builder.load_items(items)), 1)
        with self.assertRaisesRegex(ValueError, "@odata.nextLink"):
            builder.load_items(items, complete=True)

    def test_complete_export_includes_items_beyond_first_200(self):
        items = self.write_json("items.json", {"value": [
            {"id": str(i), "fields": {"Title": f"Item {i}", "Link": f"https://example.com/items/{i}"}}
            for i in range(1, 202)]})
        self.path.write_text(page(gallery=True), encoding="utf-8")
        code, _ = self.refresh("--items", items, "--columns", "ID", "Title", "Link", "--snapshot")
        self.assertEqual(code, 0)
        result = self.path.read_text(encoding="utf-8")
        self.assertEqual(len(snapshot_rows(script_json(result, 'id="snapshot-data"'))["rows"]), 201)
        self.assertIn('href="https://example.com/items/201"', result)


if __name__ == "__main__":
    unittest.main()
