"""
PowerPoint Deck Designer - main entry point.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

from theme_engine import ThemeEngine
from layout_engine import LayoutEngine
from validators import validate_spec, validate_rendered


DEFAULT_SLIDE_W = Inches(13.333)
DEFAULT_SLIDE_H = Inches(7.5)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_presentation(spec: dict, theme) -> Presentation:
    prs = Presentation()
    prs.slide_width = DEFAULT_SLIDE_W
    prs.slide_height = DEFAULT_SLIDE_H

    engine = LayoutEngine(prs, theme)
    slides = spec.get("slides", [])
    for idx, slide_spec in enumerate(slides, start=1):
        layout_name = slide_spec.get("layout", "content")
        try:
            engine.render(layout_name, slide_spec, slide_number=idx, total=len(slides))
        except Exception as exc:
            raise RuntimeError(
                f"Failed to render slide {idx} ('{slide_spec.get('title', '')}') "
                f"with layout '{layout_name}': {exc}"
            ) from exc
    return prs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate a PowerPoint deck.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--theme", required=True, type=str)
    parser.add_argument("--themes-file", type=Path,
                        default=Path(__file__).parent.parent / "assets" / "themes.json")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)

    spec = load_json(args.input)
    themes = load_json(args.themes_file)
    theme = ThemeEngine(themes).get(args.theme)

    if args.validate:
        issues = validate_spec(spec, theme)
        if issues["errors"]:
            print("Spec validation errors:", file=sys.stderr)
            for e in issues["errors"]:
                print(f"  - {e}", file=sys.stderr)
            return 2
        for w in issues["warnings"]:
            print(f"WARN: {w}")

    prs = build_presentation(spec, theme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(args.output)

    if args.validate:
        for w in validate_rendered(prs, theme)["warnings"]:
            print(f"WARN: {w}")
        print(f"Deck written: {args.output} ({len(prs.slides)} slides, theme='{args.theme}')")
    else:
        print(f"Deck written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
