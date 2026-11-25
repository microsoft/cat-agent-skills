#!/usr/bin/env python3
"""Extract brand tokens from a PowerPoint template or deck (.potx/.pptx/.pptm).

Reads ppt/theme/theme*.xml (color scheme and font scheme), looks for gradient
fills and the largest image on slide masters and layouts (logo candidate), and
emits:
  * a CSS block (light :root tokens plus dark-mode tokens) that replaces the
    "brand:start ... brand:end" block in the sharepoint-site-kit templates
  * a JSON brand summary (colors, fonts, gradient, logo, WCAG AA contrast checks
    and every lightness adjustment made to pass them)

Fallbacks when no deck is supplied:
  --palette palette.json   colors from the site's SharePoint brand kit or any
                           source, keys dk1 lt1 dk2 lt2 accent1..accent6 hlink,
                           optional "major_font" and "minor_font"
  --neutral                built-in neutral palette

Dependencies: Python 3 standard library plus lxml. Pillow is optional (used
only to read logo pixel sizes). The script never executes content from the file.

Usage:
  python extract_brand.py brand.potx --css-out brand.css --json-out brand.json
  python extract_brand.py brand.pptx --inject page.html      # replace the brand block in place
  python extract_brand.py --palette kit.json --css-out brand.css
  python extract_brand.py --neutral --css-out brand.css
  python extract_brand.py brand.potx --logo-out logo.png
"""
from __future__ import annotations

import argparse
import colorsys
import io
import json
import posixpath
import re
import sys
import zipfile

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    sys.exit("lxml is required: pip install lxml")

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"]
SCHEME_ALIAS = {"tx1": "dk1", "bg1": "lt1", "tx2": "dk2", "bg2": "lt2"}
NEUTRAL = {
    "dk1": "16181D", "lt1": "FFFFFF", "dk2": "101A2E", "lt2": "EEF1F5",
    "accent1": "2563EB", "accent2": "0D9488", "accent3": "7C3AED", "accent4": "D97706",
    "accent5": "DB2777", "accent6": "475569", "hlink": "1D4ED8",
}
FALLBACK_STACK_DISPLAY = '"Segoe Sans Display","Segoe UI Variable Display","Segoe UI",system-ui,sans-serif'
FALLBACK_STACK_TEXT = '"Segoe Sans Text","Segoe UI",system-ui,sans-serif'
AA_TEXT = 4.5
AA_LARGE = 3.0


# ---------- color math ----------
def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02X}" for c in rgb)


def norm(h: str) -> str:
    return rgb_to_hex(hex_to_rgb(h))


def luminance(h: str) -> float:
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a: str, b: str, t: float) -> str:
    """t=0 gives a, t=1 gives b."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def set_lightness(h: str, l: float) -> str:
    hh, _, s = colorsys.rgb_to_hls(*hex_to_rgb(h))
    return rgb_to_hex(colorsys.hls_to_rgb(hh, max(0.0, min(1.0, l)), s))


def lightness(h: str) -> float:
    return colorsys.rgb_to_hls(*hex_to_rgb(h))[1]


def fit_contrast(fg: str, bg: str, target: float) -> tuple[str, bool]:
    """Move fg lightness away from bg until the pair reaches target. Returns (color, changed)."""
    if contrast(fg, bg) >= target:
        return norm(fg), False
    darker = luminance(bg) > 0.18
    l = lightness(fg)
    for _ in range(100):
        l = l - 0.01 if darker else l + 0.01
        cand = set_lightness(fg, l)
        if contrast(cand, bg) >= target:
            return cand, True
        if l <= 0 or l >= 1:
            break
    return ("#000000" if darker else "#FFFFFF"), True


def rgba(h: str, alpha: float) -> str:
    r, g, b = (round(c * 255) for c in hex_to_rgb(h))
    return f"rgba({r},{g},{b},{alpha})"


# ---------- OOXML reading ----------
def apply_mods(hexval: str, node) -> str:
    """Apply lumMod/lumOff/tint/shade children of a color node (approximation)."""
    rgb = hex_to_rgb(hexval)
    h, l, s = colorsys.rgb_to_hls(*rgb)
    for child in node:
        tag = etree.QName(child).localname
        val = child.get("val")
        if val is None:
            continue
        v = int(val) / 100000
        if tag == "lumMod":
            l *= v
        elif tag == "lumOff":
            l += v
        elif tag == "tint":
            l = l + (1 - l) * (1 - v)
        elif tag == "shade":
            l *= v
    return rgb_to_hex(colorsys.hls_to_rgb(h, max(0, min(1, l)), s))


def color_of(node, scheme: dict) -> str | None:
    """node holds one of srgbClr / sysClr / schemeClr."""
    for child in node:
        tag = etree.QName(child).localname
        if tag == "srgbClr":
            return apply_mods(child.get("val"), child)
        if tag == "sysClr":
            return apply_mods(child.get("lastClr", "000000"), child)
        if tag == "schemeClr":
            key = SCHEME_ALIAS.get(child.get("val"), child.get("val"))
            if key in scheme:
                return apply_mods(scheme[key], child)
    return None


def rels_for(z: zipfile.ZipFile, part: str) -> dict:
    d, f = posixpath.split(part)
    rp = posixpath.join(d, "_rels", f + ".rels")
    if rp not in z.namelist():
        return {}
    root = etree.fromstring(z.read(rp))
    out = {}
    for r in root.findall("rel:Relationship", NS):
        out[r.get("Id")] = (r.get("Type", ""), posixpath.normpath(posixpath.join(d, r.get("Target", ""))))
    return out


def pick_theme(z: zipfile.ZipFile) -> str | None:
    masters = sorted(n for n in z.namelist() if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n))
    for m in masters:
        for typ, target in rels_for(z, m).values():
            if typ.endswith("/theme") and target in z.namelist():
                return target
    themes = sorted(n for n in z.namelist() if re.match(r"ppt/theme/theme\d+\.xml$", n))
    return themes[0] if themes else None


def read_deck(path: str) -> dict:
    with zipfile.ZipFile(path) as z:
        theme_part = pick_theme(z)
        if not theme_part:
            raise ValueError("No theme part found; is this a PowerPoint file?")
        theme = etree.fromstring(z.read(theme_part))
        scheme: dict[str, str] = {}
        cs = theme.find(".//a:clrScheme", NS)
        scheme_name = cs.get("name") if cs is not None else ""
        if cs is not None:
            for slot in SLOTS:
                node = cs.find(f"a:{slot}", NS)
                if node is not None:
                    c = color_of(node, {})
                    if c:
                        scheme[slot] = norm(c)
        fonts = {}
        for kind in ("majorFont", "minorFont"):
            latin = theme.find(f".//a:fontScheme/a:{kind}/a:latin", NS)
            if latin is not None and latin.get("typeface"):
                fonts[kind] = latin.get("typeface")

        parts = sorted(n for n in z.namelist() if re.match(r"ppt/(slideMasters/slideMaster|slideLayouts/slideLayout)\d+\.xml$", n))
        gradients = []
        images: dict[str, dict] = {}
        for part in parts:
            root = etree.fromstring(z.read(part))
            for gf in root.iter(f"{{{NS['a']}}}gradFill"):
                stops = []
                for gs in gf.findall("a:gsLst/a:gs", NS):
                    c = color_of(gs, scheme)
                    if c:
                        stops.append((int(gs.get("pos", "0")) / 1000, norm(c)))
                lin = gf.find("a:lin", NS)
                angle = int(lin.get("ang", "0")) / 60000 if lin is not None else 0
                if len(stops) >= 2 and len({s[1] for s in stops}) >= 2:
                    gradients.append({"part": part, "angle": angle, "stops": stops})
            rels = rels_for(z, part)
            for blip in root.iter(f"{{{NS['a']}}}blip"):
                rid = blip.get(f"{{{NS['r']}}}embed")
                if rid in rels and rels[rid][1] in z.namelist():
                    target = rels[rid][1]
                    info = images.setdefault(target, {"path": target, "bytes": z.getinfo(target).file_size, "used_in": []})
                    info["used_in"].append(part)
        logo = None
        if images:
            for info in images.values():
                info["pixels"] = None
                try:
                    from PIL import Image  # optional
                    with Image.open(io.BytesIO(z.read(info["path"]))) as im:
                        info["pixels"] = list(im.size)
                except Exception:  # Pillow missing or unreadable image: fall back to byte size
                    info["pixels"] = None
            def area(i):
                return (i["pixels"][0] * i["pixels"][1]) if i["pixels"] else i["bytes"]
            # A full-bleed background photo is not a logo: prefer images that are not huge and wide.
            ranked = sorted(images.values(), key=area, reverse=True)
            logo = ranked[0]
            logo["note"] = "largest image on masters/layouts; confirm it is a logo, not a background"
        return {"source": path, "theme_part": theme_part, "scheme_name": scheme_name, "scheme": scheme,
                "fonts": fonts, "gradients": gradients, "logo": logo, "image_count": len(images)}


def extract_logo(path: str, member: str, out: str) -> None:
    with zipfile.ZipFile(path) as z, open(out, "wb") as fh:
        fh.write(z.read(member))


# ---------- token building ----------
def build_tokens(scheme: dict, fonts: dict, gradient: dict | None) -> tuple[dict, dict, list]:
    s = {**NEUTRAL, **{k: v.lstrip("#") for k, v in scheme.items()}}
    s = {k: norm(v) for k, v in s.items()}
    log: list[dict] = []

    # Pick the light and dark anchors even when a theme swaps dk/lt.
    light_bg = s["lt1"] if luminance(s["lt1"]) >= luminance(s["dk1"]) else s["dk1"]
    dark_fg = s["dk1"] if light_bg == s["lt1"] else s["lt1"]
    navy = s["dk2"] if luminance(s["dk2"]) < 0.08 else set_lightness(s["dk2"], 0.14)
    if navy != s["dk2"]:
        log.append({"token": "--navy", "reason": "dk2 too light for a dark band", "from": s["dk2"], "to": navy})

    light = {
        "--ground": mix(light_bg, s["lt2"], 0.35) if luminance(s["lt2"]) > 0.6 else light_bg,
        "--ground2": s["lt2"] if luminance(s["lt2"]) > 0.6 else mix(light_bg, s["accent1"], 0.06),
        "--card": "#FFFFFF",
        "--ink": dark_fg,
        "--body": mix(dark_fg, light_bg, 0.18),
        "--muted": mix(dark_fg, light_bg, 0.42),
        "--accent": s["accent1"], "--accent-ink": s["accent1"], "--accent2": s["accent2"], "--accent3": s["accent3"],
        "--pale": mix(s["accent1"], "#FFFFFF", 0.86),
        "--navy": navy,
        "--band-ink": mix("#FFFFFF", s["accent1"], 0.12),
        "--band-muted": mix("#FFFFFF", navy, 0.32),
    }
    dark_ground = set_lightness(navy, 0.08)
    dark = {
        "--ground": dark_ground,
        "--ground2": set_lightness(navy, 0.11),
        "--card": set_lightness(navy, 0.13),
        "--ink": "#F2F4F7",
        "--body": "#D4D9E0",
        "--muted": "#A6AEB9",
        "--accent": s["accent1"] if lightness(s["accent1"]) >= 0.6 else mix(s["accent1"], "#FFFFFF", 0.25),
        "--accent-ink": mix(s["accent1"], "#FFFFFF", 0.45),
        "--pale": mix(s["accent1"], dark_ground, 0.78),
        "--navy": set_lightness(navy, 0.06),
    }

    def check(mode, tokens, fg_key, bg_key, target, fix=True, bg_override=None):
        fg = tokens[fg_key]
        bg = bg_override or tokens[bg_key]
        ratio = contrast(fg, bg)
        entry = {"mode": mode, "pair": f"{fg_key} on {bg_key}", "fg": fg, "bg": bg, "ratio": round(ratio, 2), "target": target}
        if ratio < target and fix:
            new, _ = fit_contrast(fg, bg, target)
            tokens[fg_key] = new
            entry.update({"adjusted_to": new, "ratio_after": round(contrast(new, bg), 2)})
        entry["pass"] = contrast(tokens[fg_key], bg) >= target
        log.append(entry)

    # The order matters: muted is checked on the darker of ground and card.
    for mode, tok in (("light", light), ("dark", dark)):
        merged = {**light, **tok} if mode == "dark" else tok
        for fg in ("--ink", "--body", "--muted", "--accent-ink"):
            for bg in ("--ground", "--card", "--ground2"):
                check(mode, tok if fg in tok else merged, fg, bg, AA_TEXT, bg_override=merged[bg])
        check(mode, tok if "--accent-ink" in tok else merged, "--accent-ink", "--pale", AA_TEXT, bg_override=merged["--pale"])
    for fg in ("--band-ink", "--band-muted"):
        check("light", light, fg, "--navy", AA_TEXT)
    # White hero heading and white buttons on the band
    check("light", {"--white": "#FFFFFF", "--navy": light["--navy"]}, "--white", "--navy", AA_LARGE, fix=False)
    on_accent = "#FFFFFF" if contrast("#FFFFFF", light["--accent"]) >= contrast("#16181D", light["--accent"]) else "#16181D"
    light["--on-accent"] = on_accent

    if gradient:
        stops = ",".join(f"{c} {round(p)}%" for p, c in gradient["stops"])
        angle = (gradient["angle"] + 90) % 360  # DrawingML 0deg = left to right; CSS 90deg = left to right
        grad = f"linear-gradient({round(angle)}deg,{stops})"
    else:
        grad = f"linear-gradient(90deg,{light['--accent']},{light['--accent2']} 60%,{light['--accent3']})"
    light["--grad"] = grad

    # v2 design tokens: six rotating card colors and the hero wash.
    for i in range(1, 7):
        c = s[f"accent{i}"]
        light[f"--c{i}"] = c
        dark[f"--c{i}"] = c if lightness(c) >= 0.6 else mix(c, "#FFFFFF", 0.35)
    a1, a2 = s["accent1"], s["accent2"]
    light["--wash"] = (f"linear-gradient(180deg,{mix(a1, '#FFFFFF', 0.70)} 0%,{mix(a1, '#FFFFFF', 0.86)} 38%,"
                       f"{rgba(light['--ground'], 0)} 100%)")
    dark["--wash"] = (f"linear-gradient(180deg,{set_lightness(a1, 0.18)} 0%,{set_lightness(a1, 0.11)} 40%,"
                      f"{rgba(dark['--ground'], 0)} 100%)")
    light["--line"] = rgba(light["--ink"], 0.10)
    light["--shadow"] = f"0 1px 2px {rgba(navy, 0.04)},0 8px 24px {rgba(navy, 0.08)}"
    dark["--line"] = "rgba(255,255,255,.10)"
    dark["--shadow"] = "0 1px 2px rgba(0,0,0,.3),0 10px 28px rgba(0,0,0,.35)"

    major, minor = fonts.get("majorFont"), fonts.get("minorFont")
    light["--fd"] = (f'"{major}",' if major and not major.startswith("+") else "") + FALLBACK_STACK_DISPLAY
    light["--ft"] = (f'"{minor}",' if minor and not minor.startswith("+") else "") + FALLBACK_STACK_TEXT
    return light, dark, log


ORDER_LIGHT = ["--ground", "--ground2", "--card", "--ink", "--body", "--muted", "--line", "--accent", "--accent-ink",
               "--accent2", "--accent3", "--c1", "--c2", "--c3", "--c4", "--c5", "--c6", "--pale", "--navy",
               "--band-ink", "--band-muted", "--on-accent", "--grad", "--wash",
               "--shadow", "--fd", "--ft"]
ORDER_DARK = ["--ground", "--ground2", "--card", "--ink", "--body", "--muted", "--line", "--accent", "--accent-ink",
              "--c1", "--c2", "--c3", "--c4", "--c5", "--c6", "--pale", "--navy", "--wash", "--shadow"]


def css_block(light: dict, dark: dict, source_note: str) -> str:
    lt = ";".join(f"{k}:{light[k]}" for k in ORDER_LIGHT if k in light)
    dk = ";".join(f"{k}:{dark[k]}" for k in ORDER_DARK if k in dark)
    return (
        f"/* brand:start (generated by extract_brand.py from {source_note}) */\n"
        f":root{{color-scheme:light;{lt}}}\n"
        # OS dark mode, unless the page's #mode switch is on (then light)
        f"@media (prefers-color-scheme:dark){{:root:not([data-theme=\"light\"]):not(:has(#mode:checked)){{color-scheme:dark;{dk}}}}}\n"
        # OS light mode with the #mode switch on (then dark)
        f"@media (prefers-color-scheme:light){{:root:not([data-theme=\"light\"]):has(#mode:checked){{color-scheme:dark;{dk}}}}}\n"
        # live pages: the theme bootstrap sets data-theme
        f":root[data-theme=\"dark\"]{{color-scheme:dark;{dk}}}\n"
        f"/* brand:end */"
    )


def inject(html_path: str, block: str) -> None:
    with open(html_path, encoding="utf-8") as fh:
        html = fh.read()
    new, n = re.subn(r"/\* brand:start.*?/\* brand:end \*/", lambda _m: block, html, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"No brand:start ... brand:end block found in {html_path}")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(new)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", nargs="?", help=".potx/.pptx/.pptm brand template")
    ap.add_argument("--palette", help="JSON palette (brand kit fallback)")
    ap.add_argument("--neutral", action="store_true", help="use the neutral default palette")
    ap.add_argument("--css-out")
    ap.add_argument("--json-out")
    ap.add_argument("--inject", help="HTML file whose brand block is replaced in place")
    ap.add_argument("--logo-out", help="write the logo candidate image here")
    args = ap.parse_args(argv)

    if args.deck:
        info = read_deck(args.deck)
        source = "brand template"
    elif args.palette:
        with open(args.palette, encoding="utf-8") as fh:
            pal = json.load(fh)
        fonts = {k2: pal[k1] for k1, k2 in (("major_font", "majorFont"), ("minor_font", "minorFont")) if pal.get(k1)}
        info = {"source": args.palette, "scheme": {k: norm(v) for k, v in pal.items() if k in SLOTS},
                "fonts": fonts, "gradients": [], "logo": None}
        source = "palette file"
    elif args.neutral:
        info = {"source": "neutral default", "scheme": {}, "fonts": {}, "gradients": [], "logo": None}
        source = "neutral default"
    else:
        ap.error("give a deck, --palette or --neutral")

    gradient = max(info["gradients"], key=lambda g: len(g["stops"])) if info.get("gradients") else None
    light, dark, log = build_tokens(info["scheme"], info["fonts"], gradient)
    block = css_block(light, dark, source)

    failures = [e for e in log if "pass" in e and not e["pass"]]
    summary = {
        "source": info["source"], "source_kind": source, "scheme_name": info.get("scheme_name", ""),
        "theme_colors": info["scheme"], "fonts": info["fonts"],
        "font_note": "Brand fonts render only where installed; the stack falls back to Segoe UI and system fonts.",
        "gradient": gradient, "gradients_found": len(info.get("gradients", [])),
        "logo": info.get("logo"), "tokens_light": light, "tokens_dark": dark,
        "contrast_checks": [e for e in log if "pair" in e],
        "adjustments": [e for e in log if "adjusted_to" in e or "reason" in e],
        "aa_pass": not failures,
    }
    if args.css_out:
        with open(args.css_out, "w", encoding="utf-8") as fh:
            fh.write(block + "\n")
    if args.inject:
        inject(args.inject, block)
    if args.logo_out and info.get("logo"):
        extract_logo(args.deck, info["logo"]["path"], args.logo_out)
        summary["logo"]["written_to"] = args.logo_out
    text = json.dumps(summary, indent=2)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    if not (args.css_out or args.json_out or args.inject):
        print(block)
        print(text)
    else:
        print(json.dumps({"aa_pass": summary["aa_pass"], "adjustments": len(summary["adjustments"]),
                          "logo": (info.get("logo") or {}).get("path"), "fonts": info["fonts"]}, indent=2))
    return 0 if not failures else 3


if __name__ == "__main__":
    sys.exit(main())
