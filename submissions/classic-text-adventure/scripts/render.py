#!/usr/bin/env python3
"""Deterministically render game text as a themed PNG when Pillow is available."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any


WIDTH = 1280
HEIGHT = 960
FONT_SIZE = 28
MARGIN = 56
LINE_HEIGHT = 38

THEMES = {
    "surface": ("#13251d", "#d9efcf", "#8fbe78"),
    "cave": ("#171514", "#eee4d2", "#b69062"),
    "darkness": ("#07080b", "#c5cada", "#596278"),
    "danger": ("#280e10", "#ffe2db", "#d55c52"),
    "endgame": ("#171126", "#f0e4ff", "#b68ce0"),
}


class RenderUnavailable(RuntimeError):
    pass


def _load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RenderUnavailable("Pillow is not installed; text output remains available") from exc
    return Image, ImageDraw, ImageFont


def _wrap_line(draw: Any, line: str, font: Any, max_width: int) -> list[str]:
    if not line:
        return [""]
    chunks: list[str] = []
    remaining = line
    while remaining:
        if draw.textlength(remaining, font=font) <= max_width:
            chunks.append(remaining)
            break
        low, high = 1, len(remaining)
        while low < high:
            middle = (low + high + 1) // 2
            if draw.textlength(remaining[:middle], font=font) <= max_width:
                low = middle
            else:
                high = middle - 1
        cut = max(1, low)
        chunks.append(remaining[:cut])
        remaining = remaining[cut:]
    return chunks


def render_pages(text: str, scene_key: str, font_path: Path) -> list[tuple[bytes, dict[str, Any]]]:
    Image, ImageDraw, ImageFont = _load_pillow()
    if not font_path.is_file():
        raise RenderUnavailable(f"font not found: {font_path}")
    background, foreground, accent = THEMES.get(scene_key, THEMES["cave"])
    font = ImageFont.truetype(str(font_path), FONT_SIZE)
    measuring_image = Image.new("RGB", (1, 1))
    measuring_draw = ImageDraw.Draw(measuring_image)
    lines: list[str] = []
    for logical_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        lines.extend(_wrap_line(measuring_draw, logical_line, font, WIDTH - 2 * MARGIN))
    capacity = (HEIGHT - 2 * MARGIN - LINE_HEIGHT) // LINE_HEIGHT
    page_lines = [lines[index : index + capacity] for index in range(0, len(lines), capacity)] or [[]]
    pages = []
    for page_number, visible in enumerate(page_lines, start=1):
        image = Image.new("RGB", (WIDTH, HEIGHT), background)
        draw = ImageDraw.Draw(image)
        draw.rectangle((MARGIN, MARGIN - 18, WIDTH - MARGIN, MARGIN - 10), fill=accent)
        y = MARGIN
        for line in visible:
            draw.text((MARGIN, y), line, fill=foreground, font=font)
            y += LINE_HEIGHT
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=False, compress_level=9)
        pixels = image.tobytes()
        data = output.getvalue()
        pages.append(
            (
                data,
                {
                    "width": WIDTH,
                    "height": HEIGHT,
                    "scene_key": scene_key,
                    "page": page_number,
                    "pages": len(page_lines),
                    "pixel_sha256": hashlib.sha256(pixels).hexdigest(),
                    "file_sha256": hashlib.sha256(data).hexdigest(),
                },
            )
        )
    return pages


def render_png(text: str, scene_key: str, font_path: Path) -> tuple[bytes, dict[str, Any]]:
    """Compatibility helper returning the first page."""
    return render_pages(text, scene_key, font_path)[0]


def render_to_file(text: str, scene_key: str, font_path: Path, output_path: Path) -> dict[str, Any]:
    data, metadata = render_png(text, scene_key, font_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return {**metadata, "path": str(output_path)}
