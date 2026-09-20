#!/usr/bin/env python3
"""Compose the still cards for an explainer video from a JSON storyboard.

Usage:  python compose_cards.py storyboard.json --out working/cards

Every beat in the storyboard becomes one or two 1920x1080 PNG cards:
  title      -> 1 card  (full-bleed photo, centred title)
  section    -> 2 cards (b-roll lower-third, then a detail card with the photo
                         panelled down the right-hand side)
  screenshot -> 1 card  (user-supplied screenshot, framed, never redrawn)
  table      -> 1 card  (blurred photo background, coloured recap rows)
  closing    -> 1 card  (same treatment as title)

The card filenames are printed in order, one per line, so render_video.py can
consume them.
"""
import argparse, json, os, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080


def resolve_font(weight):
    filename = f"Carlito-{weight}.ttf"
    candidates = [
        f"/usr/share/fonts/metric-compat/{filename}",
        f"/usr/share/fonts/truetype/crosextra/{filename}",
        f"/usr/share/fonts/truetype/carlito/{filename}",
        f"/usr/share/fonts/truetype/liberation2/LiberationSans{'-Bold' if weight == 'Bold' else ''}.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise RuntimeError(
        f"Required {weight.lower()} font not found. Install Carlito or Liberation Sans."
    )


FB = resolve_font("Bold")
FR = resolve_font("Regular")

ACCENTS = {"blue": (0, 120, 212), "green": (22, 138, 40), "purple": (146, 92, 224),
           "orange": (214, 96, 24), "teal": (0, 140, 150), "red": (196, 60, 60)}

THEMES = {
    "dark":  dict(bg=(16, 24, 40), card=(26, 37, 60), text=(255, 255, 255),
                  muted=(176, 190, 212), veil=(8, 12, 22), veil_top=70, veil_bot=110),
    "light": dict(bg=(245, 247, 250), card=(255, 255, 255), text=(23, 30, 44),
                  muted=(90, 103, 124), veil=(255, 255, 255), veil_top=40, veil_bot=70),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def accent_of(beat):
    a = beat.get("accent", "blue")
    return ACCENTS.get(a, ACCENTS["blue"]) if isinstance(a, str) else tuple(a)


def cover(path, w, h):
    im = Image.open(path).convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * r + 1)), max(1, int(im.height * r + 1))), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def veil(img, th, top, bottom):
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), int(top + (bottom - top) * (y / H)))
    return Image.composite(Image.new("RGB", img.size, th["veil"]), img, g.resize(img.size))


def scrim(img, th, start=470, strength=300, cap=235):
    g = Image.new("L", (1, H))
    for y in range(H):
        g.putpixel((0, y), 0 if y < start else int(min(cap, (y - start) / (H - start) * strength)))
    return Image.composite(Image.new("RGB", (W, H), th["veil"]), img, g.resize((W, H)))


def base(th, accent):
    img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=accent)
    return img, d


def title_card(beat, th):
    accent = accent_of(beat)
    if beat.get("photo"):
        img = veil(cover(beat["photo"], W, H), th, 170, 205).filter(ImageFilter.GaussianBlur(2))
    else:
        img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=accent)
    d.text((W // 2, 400), beat["title"], font=font(FB, 100), fill=th["text"], anchor="mm")
    if beat.get("sub"):
        d.text((W // 2, 545), beat["sub"], font=font(FR, 44), fill=th["text"], anchor="mm")
    d.rectangle([W // 2 - 130, 635, W // 2 + 130, 641], fill=accent)
    if beat.get("foot"):
        d.text((W // 2, 725), beat["foot"], font=font(FR, 38), fill=th["muted"], anchor="mm")
    return img


def broll_card(beat, th):
    accent = accent_of(beat)
    img = scrim(veil(cover(beat["photo"], W, H), th, 60, 60), th)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=accent)
    d.rectangle([140, 700, 152, 940], fill=accent)
    if beat.get("tag"):
        d.text((196, 700), beat["tag"], font=font(FB, 32), fill=accent)
    d.text((196, 752), beat["title"], font=font(FB, 78), fill=th["text"])
    if beat.get("kicker"):
        d.text((196, 866), beat["kicker"], font=font(FR, 46), fill=th["text"])
    return img


def content_card(beat, th):
    accent = accent_of(beat)
    img, d = base(th, accent)
    if beat.get("photo"):
        pw = 780
        img.paste(veil(cover(beat["photo"], pw, H), th, th["veil_top"], th["veil_bot"]), (W - pw, 0))
        grad = Image.linear_gradient("L").rotate(270, expand=True).resize((360, H))
        img.paste(Image.new("RGB", (360, H), th["bg"]), (W - pw, 0), grad)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 12], fill=accent)
    if beat.get("tag"):
        d.text((140, 120), beat["tag"], font=font(FB, 32), fill=accent)
    y = 176
    for line in textwrap.wrap(beat["title"], 26):
        d.text((140, y), line, font=font(FB, 72), fill=th["text"])
        y += 84
    if beat.get("kicker"):
        d.text((140, y + 18), beat["kicker"], font=font(FR, 42), fill=th["muted"])
        y += 130
    else:
        y += 70
    for b in beat.get("bullets", []):
        lines = textwrap.wrap(b, 40)
        d.ellipse([146, y + 18, 168, y + 40], fill=accent)
        for i, line in enumerate(lines):
            d.text((205, y + i * 52), line, font=font(FR, 44), fill=th["text"])
        y += 52 * len(lines) + 46
    if beat.get("example"):
        d.rounded_rectangle([140, 900, 1120, 1000], 16, fill=th["card"])
        d.rectangle([140, 900, 150, 1000], fill=accent)
        ex = textwrap.wrap(beat["example"], 52)
        d.text((186, 950 - (len(ex) - 1) * 22), "\n".join(ex), font=font(FR, 36),
               fill=th["text"], anchor="lm")
    return img


def screenshot_card(beat, th):
    """Frame a user-supplied screenshot. The pixels are never regenerated."""
    accent = accent_of(beat)
    img, d = base(th, accent)
    shot = Image.open(beat["image"]).convert("RGB")
    box_w, box_h = 1500, 720
    r = min(box_w / shot.width, box_h / shot.height)
    shot = shot.resize((int(shot.width * r), int(shot.height * r)), Image.LANCZOS)
    x, y = (W - shot.width) // 2, 250 + (box_h - shot.height) // 2
    d.rounded_rectangle([x - 14, y - 14, x + shot.width + 14, y + shot.height + 14], 14,
                        fill=th["card"], outline=accent, width=3)
    img.paste(shot, (x, y))
    d = ImageDraw.Draw(img)
    if beat.get("tag"):
        d.text((140, 110), beat["tag"], font=font(FB, 32), fill=accent)
    d.text((W // 2, 180), beat["title"], font=font(FB, 62), fill=th["text"], anchor="mm")
    if beat.get("caption"):
        d.text((W // 2, 1020), beat["caption"], font=font(FR, 38), fill=th["muted"], anchor="mm")
    for cal in beat.get("callouts", []):     # {"x","y","w","h"} in screenshot pixels, pre-scale
        d.rounded_rectangle([x + cal["x"] * r, y + cal["y"] * r,
                             x + (cal["x"] + cal["w"]) * r, y + (cal["y"] + cal["h"]) * r],
                            8, outline=accent, width=5)
    return img


def table_card(beat, th):
    accent = accent_of(beat)
    if beat.get("photo"):
        img = veil(cover(beat["photo"], W, H).filter(ImageFilter.GaussianBlur(9)), th, 205, 225)
    else:
        img = Image.new("RGB", (W, H), th["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=accent)
    d.text((W // 2, 170), beat["title"], font=font(FB, 80), fill=th["text"], anchor="mm")
    y, rows = 300, beat.get("rows", [])
    for row in rows:
        col = ACCENTS.get(row.get("accent", "blue"), accent)
        d.rounded_rectangle([200, y, W - 200, y + 130], 18, fill=th["card"])
        d.rectangle([200, y, 212, y + 130], fill=col)
        d.text((256, y + 65), row["left"], font=font(FR, 44), fill=th["text"], anchor="lm")
        d.text((W - 256, y + 65), row["right"], font=font(FB, 44), fill=col, anchor="rm")
        y += 158
    return img


BUILDERS = {"title": title_card, "closing": title_card, "screenshot": screenshot_card,
            "table": table_card, "content": content_card}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--out", default="working/cards")
    a = ap.parse_args()
    sb = json.load(open(a.storyboard))
    style = sb.get("style", "dark")
    if style not in THEMES:
        raise ValueError(
            f"Unsupported storyboard style {style!r}; choose one of: {', '.join(THEMES)}"
        )
    th = THEMES[style]
    os.makedirs(a.out, exist_ok=True)
    made = []
    for i, beat in enumerate(sb["beats"], 1):
        kind = beat.get("kind", "content")
        if kind == "section":
            if beat.get("photo"):
                p = f"{a.out}/beat{i:02d}a.png"
                broll_card(beat, th).save(p)
                made.append(p)
            p = f"{a.out}/beat{i:02d}b.png"
            content_card(beat, th).save(p)
            made.append(p)
        else:
            p = f"{a.out}/beat{i:02d}.png"
            BUILDERS[kind](beat, th).save(p)
            made.append(p)
    print("\n".join(made))


if __name__ == "__main__":
    main()
