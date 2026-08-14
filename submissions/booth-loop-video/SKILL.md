---
name: booth-loop-video
description: Use this skill whenever the user asks for a looping booth, kiosk, trade-show, lobby-screen, or silent background video — including requests phrased as "a video loop for our stand", "an animated explainer with no voiceover", "a motion graphic for the monitor", or "turn this pitch into a looping MP4". Generate and run a self-contained Python render script (Pillow + ffmpeg) that outputs a 1920x1080 30fps MP4. Do NOT use this skill for videos that need narration, live footage, or editing of an existing video file.
---

# Booth / kiosk loop video

Produce a silent, looping MP4 (default 1920x1080, 30 fps, 60-135 s) suitable for a
conference stand, a lobby screen, a reception kiosk, a LinkedIn post, or an embedded
slide in a deck.

The output is a **rendered animation**, not a slideshow export. Every frame is painted
in Python, so layout, timing, and easing are fully under your control.

## Execution model — do the work, don't hand out instructions

You have Python and a shell. Never tell the user to open an editor or run the script
themselves. You:

1. Write a single self-contained script at `work/booth_video.py`.
2. Install dependencies if missing: `pip install pillow imageio imageio-ffmpeg numpy`
   (`imageio-ffmpeg` ships its own ffmpeg binary — no system install needed).
3. Render preview PNGs and show them to the user.
4. Only after previews look right, run the full render.
5. Report the output path.

All paths are relative to the current working directory:

```
{CWD}/
  work/
    booth_video.py
    preview/scene_1.png ...
  output/
    booth_loop.mp4
```

Write intermediate frames to the **system temp directory**, not the working folder.
Rendering thousands of PNGs into a cloud-synced folder (OneDrive, Dropbox, iCloud)
will stall the render and thrash the sync client.

## Design defaults

Use these unless the user supplies a brand palette. Ask for their colours if the video
is customer-facing; don't invent a brand.

| | |
|---|---|
| Canvas | 1920x1080, 30 fps |
| Duration | 60-135 s |
| Background | deep navy `#0A1628` |
| Accents | `#0078D4` primary, `#B4009E` secondary |
| Cards | `#112244`, 18 px corner radius, ~86% alpha |
| Type | humanist sans, generous whitespace |
| Motion | 0.5 s fade in, 0.3 s fade out per scene, smooth-step easing |

Dark, low-saturation background with two saturated accents reads well on a bright
show floor and survives poor monitor calibration.

## Script architecture

One file. A `render_frame(t, total)` function that returns a Pillow `Image` for time
`t` in seconds, and a scene table:

```python
SCENES = [
    (0.0,  8.0,  scene_hook),
    (8.0,  22.0, scene_problem),
    (22.0, 40.0, scene_how_it_works),
    # ...
    (108.0, 120.0, scene_cta),
]

def render_frame(t, total):
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for start, end, fn in SCENES:
        if start <= t < end:
            fn(draw, img, t - start, end - start)
    return img
```

Time-relative scene functions (`local_t`, `duration`) make it trivial to reorder or
retime scenes later without touching their internals.

### Animation helpers — always include these

```python
def ease_in_out(t):  return t * t * (3 - 2 * t)
def lerp(a, b, t):   return a + (b - a) * t
def clamp(v, lo, hi): return max(lo, min(hi, v))
def fade(t, start, end): return clamp((t - start) / (end - start + 1e-6), 0.0, 1.0)
```

Combine them: `alpha = ease_in_out(fade(local_t, 0, 0.5)) * (1 - fade(local_t, dur - 0.3, dur))`
gives a clean in/out envelope for any element.

### Cross-platform font loading

Never hardcode a single font path — it will fail on another machine. Probe a
candidate list per weight and fall back gracefully:

```python
import os
from PIL import ImageFont

FONT_DIRS = [
    "C:/Windows/Fonts",                       # Windows
    "/usr/share/fonts/truetype/dejavu",       # Linux
    "/usr/share/fonts/truetype/liberation",   # Linux
    "/System/Library/Fonts/Supplemental",     # macOS
    "/Library/Fonts",                         # macOS
]

CANDIDATES = {
    "light":    ["segoeuil.ttf", "HelveticaNeue.ttc", "DejaVuSans-ExtraLight.ttf", "arial.ttf"],
    "regular":  ["segoeui.ttf", "Helvetica.ttc", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"],
    "semibold": ["seguisb.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf"],
    "bold":     ["segoeuib.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf"],
    "mono":     ["consola.ttf", "Menlo.ttc", "DejaVuSansMono.ttf", "cour.ttf"],
}

def get_font(weight, size):
    for name in CANDIDATES.get(weight, CANDIDATES["regular"]):
        for d in FONT_DIRS:
            p = os.path.join(d, name)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    continue
    return ImageFont.load_default()
```

Print which font actually resolved on the first call. A silent fall back to
`load_default()` produces a tiny bitmap font and a video that looks broken —
you want to know before the full render, not after.

## Z-order rule — the one that bites

**Pillow paints in call order: later calls sit on top. Draw connectors before the
things they connect.**

For any hub-and-spoke, node-and-edge, or step-and-arrow layout, split into two passes:

```python
# Pass 1 — background layer: every connector
for item in items:
    draw.line([hub_xy, item.xy], fill=LINE, width=2)

# Pass 2 — foreground layer: every node
draw_hub(draw, hub_xy)
for item in items:
    draw_card(draw, item.xy, item.label)
```

Interleaving the two passes draws lines across cards and through label text. This is
the single most common defect in generated diagrams-in-motion, and it is invisible
until you look at a rendered frame — which is why previews are mandatory.

## Scene planning

Design for someone walking past at 3 m who gives you eight seconds.

1. **Hook (0-8 s)** — one bold headline, one idea. No body copy. If a passer-by
   can't get the point from this scene alone, the video has already failed.
2. **Body scenes (8 s onward)** — one concept per scene, 10-18 s each. Card layouts,
   animated counters, progress bars, typed-text reveals. Never more than ~25 words
   on screen at once.
3. **CTA (last 8-12 s)** — what to do next, plus a name, booth number, or short URL.

End the CTA so it cuts cleanly back to the hook — the loop point should be invisible.
Either fade fully to background colour, or make the first and last frames identical.

## Contrast rules

- Dark card on dark background is unreadable on a show floor. For any chat, answer,
  or quote UI, put the response on a **white or near-white card** with dark text.
- Never place accent-coloured text on the accent-coloured fill.
- Check contrast on a **preview PNG**, not in your head. Show-floor lighting and
  cheap panels both crush shadow detail.

## Preview before rendering

Full renders take minutes. Preview takes seconds. Always:

```python
if PREVIEW:
    os.makedirs("work/preview", exist_ok=True)
    for i, (start, end, _) in enumerate(SCENES, 1):
        mid = (start + end) / 2
        render_frame(mid, TOTAL).convert("RGB").save(f"work/preview/scene_{i}.png")
    raise SystemExit
```

Display every preview inline to the user with markdown image syntax and get
confirmation before the full render. URL-encode any spaces in the path.

## Render loop

```python
import imageio, numpy as np

writer = imageio.get_writer(
    output_path, fps=FPS, codec="libx264",
    output_params=["-crf", "18", "-pix_fmt", "yuv420p"],
)
for idx in range(int(TOTAL * FPS)):
    t = idx / FPS
    writer.append_data(np.array(render_frame(t, TOTAL).convert("RGB")))
    if idx % max(1, int(TOTAL * FPS / 20)) == 0:
        print(f"{100 * idx / (TOTAL * FPS):.0f}%", flush=True)
writer.close()
```

`-pix_fmt yuv420p` is not optional — without it the file will not play in QuickTime,
PowerPoint, or most hardware media players, even though VLC handles it fine.

## Iteration

After the first render, offer to tweak and accept plain-language feedback
("slower orbit", "bigger headline", "green instead of magenta"). Edit the script,
re-render the affected scene as a **preview PNG** first, then re-render the video.
Never re-render the full video to check a colour change.

## Quality checklist before delivering

- [ ] Resolved a real TrueType font, not `load_default()`
- [ ] No text overflowing a card boundary or the canvas
- [ ] No label collisions in radial / orbit layouts
- [ ] All connectors drawn before all nodes (z-order)
- [ ] Readable contrast on every scene's preview PNG
- [ ] Loop point is seamless — last frame flows into first
- [ ] Encoded with `yuv420p`; plays outside VLC
- [ ] Reasonable file size (< 200 MB for ~120 s)
- [ ] Reported the absolute output path to the user
