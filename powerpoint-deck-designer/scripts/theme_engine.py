"""Theme loading, validation and colour helpers."""

from __future__ import annotations

from dataclasses import dataclass

from pptx.dml.color import RGBColor


REQUIRED_COLOR_KEYS = ["background", "surface", "primary",
                       "secondary", "accent", "text", "muted"]
REQUIRED_FONT_KEYS = ["heading", "body"]


def hex_to_rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Invalid hex colour: {hex_str}")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


@dataclass
class Theme:
    slug: str
    name: str
    colors: dict
    fonts: dict
    sizes: dict

    def rgb(self, key: str) -> RGBColor:
        return hex_to_rgb(self.colors[key])


class ThemeEngine:
    def __init__(self, themes_doc):
        self._themes = {t["slug"]: t for t in themes_doc.get("themes", [])}
        if not self._themes:
            raise ValueError("themes.json contains no themes.")

    def get(self, slug: str) -> Theme:
        if slug not in self._themes:
            available = ", ".join(sorted(self._themes))
            raise KeyError(f"Theme '{slug}' not found. Available: {available}")
        raw = self._themes[slug]
        self._validate(raw)
        return Theme(
            slug=raw["slug"],
            name=raw["name"],
            colors=raw["colors"],
            fonts=raw["fonts"],
            sizes=raw.get("sizes", {"title": 40, "subtitle": 22,
                                    "heading": 28, "body": 18, "caption": 12}),
        )

    @staticmethod
    def _validate(raw) -> None:
        for k in REQUIRED_COLOR_KEYS:
            if k not in raw.get("colors", {}):
                raise ValueError(f"Theme '{raw.get('slug')}' missing colors.{k}")
        for k in REQUIRED_FONT_KEYS:
            if k not in raw.get("fonts", {}):
                raise ValueError(f"Theme '{raw.get('slug')}' missing fonts.{k}")
