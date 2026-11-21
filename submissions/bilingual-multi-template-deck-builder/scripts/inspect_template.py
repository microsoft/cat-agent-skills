#!/usr/bin/env python3
"""Inspect local template structure for binding configuration."""
import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation


def inspect(file, include_text=False):
    presentation = Presentation(file)
    slides = []
    for index, slide in enumerate(presentation.slides, 1):
        shapes = []
        for shape in slide.shapes:
            item = {"name": shape.name, "id": shape.shape_id,
                    "type": "chart" if shape.has_chart else "table" if shape.has_table
                    else "text" if shape.has_text_frame else str(shape.shape_type),
                    "box_inches": [round(value / 914400, 3) for value in
                                   (shape.left, shape.top, shape.width, shape.height)]}
            if shape.is_placeholder:
                item["placeholder_idx"] = shape.placeholder_format.idx
            if include_text and shape.has_text_frame:
                item["text"] = shape.text
            shapes.append(item)
        slides.append({"reference_slide": index, "layout_name": slide.slide_layout.name,
                       "shapes": shapes})
    return {"filename": file.name, "masters": len(presentation.slide_masters),
            "layouts": [layout.name for layout in presentation.slide_layouts], "slides": slides}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-text", action="store_true",
                        help="Include actual slide text; review before sharing the inventory")
    arguments = parser.parse_args()
    result = json.dumps(inspect(arguments.template, arguments.include_text),
                        ensure_ascii=False, indent=2) + "\n"
    if arguments.output:
        with arguments.output.open("x", encoding="utf-8") as output:
            output.write(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
