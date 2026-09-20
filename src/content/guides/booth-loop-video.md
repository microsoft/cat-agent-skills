# Booth Loop Video

You need something on the screen behind your stand. Not a slideshow with a
transition every eight seconds, and not a video that needs an editor, a brief, and
three weeks. This skill renders a **silent, looping MP4** — 1920x1080, 30 fps,
one to two minutes — from a description of what you want it to say.

Describe the message, hand over your brand colours, and the agent writes a Python
render script, shows you a still from every scene, and only then renders the video.

## What it does

The agent generates a single self-contained script that paints **every frame** with
Pillow and pipes them to ffmpeg. That means real motion — eased fades, animated
counters, progress bars, typed-text reveals, orbiting nodes — not a set of static
slides with a crossfade.

Because the whole thing is a script, iteration is conversational: "slower orbit",
"make the headline bigger", "swap magenta for green" edits a few constants and
re-renders.

## Why frame-by-frame instead of a slide export

Exporting a deck to video gives you a deck playing at 0.1 fps. This gives you a
motion graphic. The trade-off is that you're writing code rather than dragging
boxes — which is exactly the trade-off an agent is good at absorbing.

## What makes it different

Most of this skill is the accumulated list of things that go wrong, written down so
they don't go wrong again:

- **The z-order rule.** Pillow paints in call order. Draw a hub, then its spokes,
  and the spoke lines run straight across the hub and through your labels. The skill
  forces a two-pass draw — all connectors, then all nodes — for any diagram layout.
  This is the single most common defect and it's invisible until you look at a frame.
- **Preview before render.** A full render takes minutes; a preview PNG takes
  seconds. The agent renders one still per scene and shows them to you inline
  *before* committing to the render.
- **`-pix_fmt yuv420p`.** Without it the MP4 plays fine in VLC and in nothing else —
  not QuickTime, not PowerPoint, not the media player on the screen at the venue.
- **Font probing across platforms.** A hardcoded font path silently falls back to a
  tiny bitmap font and produces a video that looks broken. The skill probes a
  candidate list per weight and reports what actually resolved.
- **Contrast for a show floor.** Dark card on dark background is a design-tool
  favourite and unreadable on a badly calibrated panel under bright lights. Chat and
  quote UI goes on a white card, and contrast gets checked on a rendered frame.
- **Frames go to the system temp folder**, never the working directory — rendering
  thousands of PNGs into a OneDrive- or Dropbox-synced folder stalls the render and
  thrashes the sync client.

## How to use it

1. Tell the agent what the video is for and roughly what it should say — the pitch,
   the three things you want a passer-by to take away, the call to action.
2. Give it your brand colours, or let it use the neutral navy/blue default. It won't
   invent a brand for you.
3. Review the per-scene preview stills it sends back and correct anything that looks
   wrong. This is the cheap moment to fix layout.
4. Approve the render. Output lands at `output/booth_loop.mp4`.
5. Iterate in plain language until it's right.

## Requirements

Python with `pillow`, `imageio`, `imageio-ffmpeg`, and `numpy`. The agent installs
them if they're missing. `imageio-ffmpeg` bundles its own ffmpeg binary, so there's
no system ffmpeg install and nothing to put on `PATH`.

## Tips

- **Write for eight seconds of attention at three metres.** If the opening scene
  doesn't land on its own, nothing after it will.
- Keep it under ~25 words on screen at any moment.
- Make the first and last frames identical so the loop point disappears.
- It's silent by design. Booths are loud and most venue screens are muted anyway.
- The output works as a LinkedIn post or an embedded slide, not just a booth loop.

## Known limitations

- No audio track. Add one afterwards with ffmpeg if you need it.
- No live footage or video-file editing — this generates from scratch.
- Complex scenes at 30 fps take a few minutes to render. Preview stills are the
  answer, not patience.
