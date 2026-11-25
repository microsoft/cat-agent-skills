#!/usr/bin/env python3
"""Shared helpers for the pptx-template-applier scripts.

- open_deck(): opens .pptx, .pptm, .potx and .potm with python-pptx (a template
  is opened from an in-memory copy with the presentation content type; the
  file on disk is never changed).
- classify_layout() and classify_source_slide(): the layout kinds used by the
  mapping rules (title, section, content, two_content, comparison, picture,
  title_only, blank, caption_content).
- theme helpers: read the color map and theme colors of a deck, nearest theme
  slot for an RGB color, WCAG contrast.

Standard library plus python-pptx. Never executes content from a deck.
"""
from __future__ import annotations

import io
import re
import zipfile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "{%s}" % A_NS
P = "{%s}" % P_NS
R = "{%s}" % R_NS

TEMPLATE_CT = b"application/vnd.openxmlformats-officedocument.presentationml.template.main+xml"
MACRO_TEMPLATE_CT = b"application/vnd.ms-powerpoint.template.macroEnabled.main+xml"
MACRO_CT = b"application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml"
PRES_CT = b"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"

SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6"]
ALIAS = {"tx1": "dk1", "bg1": "lt1", "tx2": "dk2", "bg2": "lt2"}

TITLE_TYPES = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.VERTICAL_TITLE}
SUBTITLE_TYPES = {PP_PLACEHOLDER.SUBTITLE}
TEXT_TYPES = {PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.VERTICAL_BODY}
CONTENT_TYPES = {PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.VERTICAL_OBJECT, PP_PLACEHOLDER.TABLE,
                 PP_PLACEHOLDER.CHART, PP_PLACEHOLDER.ORG_CHART, PP_PLACEHOLDER.MEDIA_CLIP}
PICTURE_TYPES = {PP_PLACEHOLDER.PICTURE, PP_PLACEHOLDER.BITMAP}
META_TYPES = {PP_PLACEHOLDER.DATE, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.HEADER}

# Layout type attribute (p:sldLayout/@type) to layout kind.
TYPE_KIND = {
    "title": "title", "secHead": "section", "obj": "content", "tx": "content", "txAndObj": "two_content",
    "objAndTx": "two_content", "twoObj": "two_content", "twoColTx": "two_content",
    "twoTxTwoObj": "comparison", "titleOnly": "title_only", "blank": "blank", "objTx": "caption_content",
    "picTx": "picture", "vertTx": "content", "tbl": "content", "chart": "content", "dgm": "content",
    "obj_only": "content", "objOnly": "content",
}
KINDS = ["title", "section", "content", "two_content", "comparison", "picture", "caption_content",
         "title_only", "blank"]


def open_deck(path: str):
    """Open a deck or template read-only. Returns a python-pptx Presentation."""
    with open(path, "rb") as fh:
        data = fh.read()
    zin = zipfile.ZipFile(io.BytesIO(data))
    ct = zin.read("[Content_Types].xml")
    if TEMPLATE_CT in ct or MACRO_TEMPLATE_CT in ct or MACRO_CT in ct:
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                buf = zin.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    buf = buf.replace(TEMPLATE_CT, PRES_CT).replace(MACRO_TEMPLATE_CT, PRES_CT).replace(MACRO_CT, PRES_CT)
                if item.filename.lower().endswith("vbaproject.bin"):
                    continue  # never carry macros into the output
                zout.writestr(item, buf)
        out.seek(0)
        return Presentation(out)
    return Presentation(io.BytesIO(data))


def emu_box(shape):
    try:
        if shape.left is None or shape.width is None:
            return None
        return (int(shape.left), int(shape.top), int(shape.width), int(shape.height))
    except (AttributeError, ValueError, KeyError):
        return None


def ph_type(shape):
    try:
        return shape.placeholder_format.type
    except (ValueError, AttributeError):
        return None


def role_of(pt):
    if pt in TITLE_TYPES:
        return "title"
    if pt in SUBTITLE_TYPES:
        return "subtitle"
    if pt in TEXT_TYPES:
        return "text"
    if pt in CONTENT_TYPES:
        return "content"
    if pt in PICTURE_TYPES:
        return "picture"
    if pt in META_TYPES:
        return "meta"
    return "other"


def layout_placeholders(layout):
    """List of dicts for the non-meta placeholders of a layout, left to right then top to bottom."""
    out = []
    for ph in layout.placeholders:
        pt = ph_type(ph)
        role = role_of(pt)
        if role == "meta":
            continue
        box = emu_box(ph)
        out.append({"idx": ph.placeholder_format.idx, "type": str(pt).split(".")[-1].split(" ")[0],
                    "role": role, "box": box, "name": ph.name})
    return out


def classify_layout(layout, slide_w, slide_h) -> tuple[str, str]:
    """Return (kind, reason). Placeholder signature wins over the type attribute when they disagree."""
    phs = layout_placeholders(layout)
    roles = [p["role"] for p in phs]
    has_title = "title" in roles
    n_sub = roles.count("subtitle")
    n_text = roles.count("text")
    n_content = roles.count("content")
    n_pic = roles.count("picture")
    attr = layout._element.get("type")
    name = (layout.name or "").lower()
    if not has_title and not (n_text or n_content or n_pic or n_sub):
        return "blank", "no placeholders besides date, footer and slide number"
    if has_title and n_sub and not (n_content or n_pic):
        return "title", "title plus subtitle placeholders"
    if has_title and n_pic:
        return "picture", "picture placeholder"
    if has_title and n_content + n_text >= 4:
        return "comparison", f"{n_text} text and {n_content} content placeholders"
    bodies = [p for p in phs if p["role"] in ("text", "content")]
    if has_title and len(bodies) == 3:
        return "caption_content", "content with caption"
    if has_title and len(bodies) == 2:
        a, b = bodies[0]["box"], bodies[1]["box"]
        if a and b and abs(a[1] - b[1]) < slide_h * 0.08:
            return "two_content", "two side-by-side content placeholders"
        if attr == "objTx" or "caption" in name:
            return "caption_content", "content with caption"
        return "two_content", "two content placeholders"
    if has_title and len(bodies) == 1:
        body = bodies[0]
        if attr == "secHead" or "section" in name or "divider" in name or (
                body["role"] == "text" and body["box"] and body["box"][3] < slide_h * 0.25):
            return "section", "title plus short text placeholder (section header)"
        if attr == "title" or ("title" in name and "content" not in name and body["role"] == "text"
                               and body["box"] and body["box"][3] < slide_h * 0.35):
            return "title", "title layout with a text placeholder"
        return "content", "title plus one content placeholder"
    if has_title:
        return "title_only", "title placeholder only"
    if attr in TYPE_KIND:
        return TYPE_KIND[attr], f"layout type '{attr}'"
    return "blank", "no title placeholder"


def text_of(shape) -> str:
    return shape.text_frame.text if getattr(shape, "has_text_frame", False) and shape.has_text_frame else ""


# ---------- theme helpers ----------

def theme_part(prs):
    return prs.slide_master.part.part_related_by(RT.THEME)


def theme_colors(prs) -> dict:
    """Theme color scheme of the first master as {'dk1': 'RRGGBB', ...}."""
    from lxml import etree
    root = etree.fromstring(theme_part(prs).blob, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    out = {}
    scheme = root.find(f".//{A}clrScheme")
    if scheme is None:
        return out
    for el in scheme:
        slot = el.tag.split("}")[-1]
        srgb = el.find(f"{A}srgbClr")
        sysc = el.find(f"{A}sysClr")
        if srgb is not None:
            out[slot] = srgb.get("val").upper()
        elif sysc is not None:
            out[slot] = (sysc.get("lastClr") or ("000000" if slot.startswith("dk") else "FFFFFF")).upper()
    return out


def theme_fonts(prs) -> dict:
    from lxml import etree
    root = etree.fromstring(theme_part(prs).blob, parser=etree.XMLParser(resolve_entities=False, no_network=True))
    out = {}
    for key, tag in (("major", "majorFont"), ("minor", "minorFont")):
        el = root.find(f".//{A}fontScheme/{A}{tag}/{A}latin")
        if el is not None:
            out[key] = el.get("typeface")
    return out


def clr_map(prs) -> dict:
    el = prs.slide_master._element.find(f"{P}clrMap")
    m = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2"}
    if el is not None:
        for k in ("bg1", "tx1", "bg2", "tx2"):
            if el.get(k):
                m[k] = el.get(k)
    return m


def rgb_tuple(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(h):
    def lin(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb_tuple(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def nearest_slot(hexval, colors: dict, slots=SLOTS) -> tuple[str, float]:
    r, g, b = rgb_tuple(hexval)
    best, bd = None, 1e9
    for s in slots:
        if s not in colors:
            continue
        r2, g2, b2 = rgb_tuple(colors[s])
        d = ((r - r2) * 0.3) ** 2 + ((g - g2) * 0.59) ** 2 + ((b - b2) * 0.11) ** 2
        if d < bd:
            best, bd = s, d
    return best, bd ** 0.5


def apply_mods(hexval, el):
    """Apply lumMod/lumOff/tint/shade children of a color element (approximation)."""
    r, g, b = rgb_tuple(hexval)
    import colorsys
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    for ch in el:
        tag = ch.tag.split("}")[-1]
        try:
            v = int(ch.get("val", "100000")) / 100000
        except ValueError:
            continue
        if tag == "lumMod":
            l *= v
        elif tag == "lumOff":
            l += v
        elif tag == "tint":
            l = l + (1 - l) * (1 - v)
        elif tag == "shade":
            l = l * v
    l = max(0, min(1, l))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def resolve_color(el, colors: dict, cmap: dict):
    """Resolve an a:srgbClr / a:schemeClr / a:sysClr / a:prstClr element to RRGGBB, or None."""
    if el is None:
        return None
    tag = el.tag.split("}")[-1]
    if tag == "srgbClr":
        return apply_mods(el.get("val", "000000").upper(), el)
    if tag == "sysClr":
        return apply_mods((el.get("lastClr") or "000000").upper(), el)
    if tag == "schemeClr":
        v = el.get("val")
        v = cmap.get(v, v)
        v = ALIAS.get(v, v)
        if v in colors:
            return apply_mods(colors[v], el)
        return None
    if tag == "prstClr":
        return {"black": "000000", "white": "FFFFFF"}.get(el.get("val"), None)
    return None


def first_color_child(parent):
    if parent is None:
        return None
    for ch in parent:
        if ch.tag.split("}")[-1] in ("srgbClr", "schemeClr", "sysClr", "prstClr"):
            return ch
    return None


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-") or "deck"
