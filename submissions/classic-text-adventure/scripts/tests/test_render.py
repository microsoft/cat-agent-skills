import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
SKILL_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import render


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            render._load_pillow()
        except render.RenderUnavailable as exc:
            raise unittest.SkipTest(str(exc))
        cls.font = SKILL_ROOT / "assets" / "fonts" / "JetBrainsMono-Regular.ttf"

    def test_every_theme_is_deterministic(self):
        hashes = set()
        for theme in render.THEMES:
            first, first_meta = render.render_png("LINE ONE\nLINE TWO\n", theme, self.font)
            second, second_meta = render.render_png("LINE ONE\nLINE TWO\n", theme, self.font)
            self.assertEqual(first, second)
            self.assertEqual(first_meta, second_meta)
            hashes.add(first_meta["pixel_sha256"])
        self.assertEqual(len(hashes), len(render.THEMES))

    def test_blank_long_and_hard_wrapped_text(self):
        for text in ("", "short", "x" * 1000, "\n".join(str(i) for i in range(100))):
            data, metadata = render.render_png(text, "cave", self.font)
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(metadata["width"], 1280)

    def test_long_output_paginates_without_reusing_page_numbers(self):
        pages = render.render_pages("\n".join(f"LINE {index}" for index in range(100)), "cave", self.font)
        self.assertGreater(len(pages), 1)
        self.assertEqual([metadata["page"] for _, metadata in pages], list(range(1, len(pages) + 1)))
        self.assertTrue(all(metadata["pages"] == len(pages) for _, metadata in pages))


if __name__ == "__main__":
    unittest.main()
