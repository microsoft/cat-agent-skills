"""Safer text fitting for python-pptx."""

from __future__ import annotations


CHARS_PER_INCH_AT_10PT = 12.0
LINE_HEIGHT_MULTIPLIER = 1.25


def _lines_needed(text: str, box_width_in: float, pt_size: int) -> int:
    if not text:
        return 0
    chars_per_line = max(1, int(CHARS_PER_INCH_AT_10PT * box_width_in * 10 / pt_size))
    total = 0
    paragraphs = text.splitlines() or [text]
    for para in paragraphs:
        line_count = max(1, -(-len(para) // chars_per_line))
        total += line_count
    return total


def fit_font_size(text: str, box_width_emu: int, box_height_emu: int,
                  start_pt: int, min_pt: int = 12) -> int:
    if not text:
        return start_pt
    box_w_in = box_width_emu / 914400
    box_h_in = box_height_emu / 914400
    for pt_size in range(start_pt, min_pt - 1, -1):
        lines = _lines_needed(text, box_w_in, pt_size)
        line_height_in = (pt_size * LINE_HEIGHT_MULTIPLIER) / 72
        needed_in = lines * line_height_in
        if needed_in <= box_h_in:
            return pt_size
    return min_pt


def truncate_bullets(bullets, max_bullets: int = 6, max_words: int = 14):
    trimmed = []
    for b in (bullets or [])[:max_bullets]:
        words = b.split()
        if len(words) > max_words:
            b = " ".join(words[:max_words]) + "..."
        trimmed.append(b)
    return trimmed
