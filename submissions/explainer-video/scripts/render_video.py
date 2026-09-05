#!/usr/bin/env python3
"""Assemble narration + cards into a finished 1080p explainer video.

Usage:
  python render_video.py storyboard.json --cards working/cards \
      --audio output/narration.mp3 --out working/explainer.mp4 [--no-captions]

Timing: the narration is ONE audio file whose turns match the storyboard beats
1:1. The script finds the silent gaps between turns and cuts on them, so scene
changes land exactly on the narration. If the gap count does not match the beat
count it falls back to splitting proportionally by narration length.

Captions are generated from the beat narration text and burned in.
"""
import argparse, json, os, re, subprocess, textwrap

FPS = 30
XFADE = 0.6
BROLL_SHARE = 0.40          # b-roll interlude share of a section beat
FFMPEG = "ffmpeg"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def audio_duration(path):
    try:
        out = subprocess.run(
            [FFMPEG, "-i", path], capture_output=True, text=True
        ).stderr
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is required to render the explainer video.") from exc
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if not m:
        detail = out.strip()[-500:] or "ffmpeg returned no diagnostic output"
        raise RuntimeError(f"Could not read audio duration from {path!r}: {detail}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def silence_boundaries(path, want, noise=-35, mind=0.45):
    """Midpoints of the silent gaps between narration turns."""
    out = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", path, "-af",
         f"silencedetect=noise={noise}dB:d={mind}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    total = audio_duration(path)
    gaps = [(s, e) for s, e in zip(starts, ends) if s > 0.5 and e < total - 0.5]
    if len(gaps) != want:
        return None
    return [(s + e) / 2 for s, e in gaps]


def beat_windows(sb, audio):
    total = audio_duration(audio)
    beats = sb["beats"]
    cuts = silence_boundaries(audio, len(beats) - 1)
    if cuts is None:                                    # proportional fallback
        weights = [max(20, len(b.get("narration", ""))) for b in beats]
        acc, cuts, s = sum(weights), [], 0.0
        for w in weights[:-1]:
            s += w / acc * total
            cuts.append(s)
    starts = [0.0] + cuts
    ends = cuts + [total]
    return list(zip(starts, ends)), total


def srt_time(t):
    h, rem = divmod(max(0.0, t), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def write_srt(sb, windows, path):
    cues, n = [], 0
    for beat, (s, e) in zip(sb["beats"], windows):
        text = " ".join(beat.get("narration", "").split())
        if not text:
            continue
        words = text.split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 9 or w.endswith((".", "?", "!", ":")):
                chunks.append(" ".join(cur))
                cur = []
        if cur:
            chunks.append(" ".join(cur))
        span = (e - s) / max(1, sum(len(c) for c in chunks))
        t = s
        for c in chunks:
            d = len(c) * span
            n += 1
            cues.append(f"{n}\n{srt_time(t)} --> {srt_time(min(t + d, e))}\n"
                        f"{chr(10).join(textwrap.wrap(c, 46))}\n")
            t += d
    open(path, "w").write("\n".join(cues))
    return path


def segments(sb, windows, cards_dir):
    """(card_path, duration, motion) in playback order, matching compose_cards."""
    segs, idx = [], 0
    for i, (beat, (s, e)) in enumerate(zip(sb["beats"], windows), 1):
        dur, kind = e - s, beat.get("kind", "content")
        if kind == "section" and beat.get("photo"):
            segs.append((f"{cards_dir}/beat{i:02d}a.png", dur * BROLL_SHARE, "zoom"))
            segs.append((f"{cards_dir}/beat{i:02d}b.png", dur * (1 - BROLL_SHARE), "still"))
        elif kind == "section":
            segs.append((f"{cards_dir}/beat{i:02d}b.png", dur, "still"))
        else:
            motion = "zoom" if kind in ("title", "closing") and beat.get("photo") else "still"
            segs.append((f"{cards_dir}/beat{i:02d}.png", dur, motion))
    for p, _, _ in segs:
        if not os.path.exists(p):
            raise SystemExit(f"missing card: {p} — run compose_cards.py first")
    return segs


def build(segs, audio, out, srt=None):
    n = len(segs)
    cmd = [FFMPEG, "-y"]
    for i, (path, dur, _) in enumerate(segs):
        cmd += ["-loop", "1", "-t", f"{dur + (XFADE if i < n - 1 else 0):.3f}", "-i", path]
    cmd += ["-i", audio]

    filt = []
    for i, (path, dur, motion) in enumerate(segs):
        clip = dur + (XFADE if i < n - 1 else 0)
        frames = int(clip * FPS) + 2
        if motion == "zoom":
            z = 0.10 / frames
            filt.append(f"[{i}:v]scale=3840:-1,zoompan=z='min(1.02+{z:.6f}*on,1.13)'"
                        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:"
                        f"fps={FPS},format=yuv420p,setsar=1[v{i}]")
        else:
            filt.append(f"[{i}:v]format=yuv420p,fps={FPS},setsar=1[v{i}]")
    prev, off = "v0", 0.0
    for i in range(1, n):
        off += segs[i - 1][1]
        filt.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XFADE}"
                    f":offset={off - XFADE / 2:.3f}[x{i}]")
        prev = f"x{i}"
    if srt:
        style = ("FontName=Carlito,Fontsize=22,PrimaryColour=&H00FFFFFF,"
                 "BorderStyle=3,Outline=1,Shadow=0,BackColour=&HB0000000,MarginV=48")
        filt.append(f"[{prev}]subtitles={srt}:force_style='{style}'[vout]")
        prev = "vout"

    cmd += ["-filter_complex", ";".join(filt), "-map", f"[{prev}]", "-map", f"{n}:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-shortest", out]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--cards", default="working/cards")
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", default="working/explainer.mp4")
    ap.add_argument("--no-captions", action="store_true")
    a = ap.parse_args()

    sb = json.load(open(a.storyboard))
    windows, total = beat_windows(sb, a.audio)
    srt = None if a.no_captions else write_srt(sb, windows, "working/captions.srt")
    build(segments(sb, windows, a.cards), a.audio, a.out, srt)
    print(json.dumps({"output": a.out, "duration_seconds": round(total, 1),
                      "captions": srt, "scenes": len(sb["beats"])}, indent=2))


if __name__ == "__main__":
    main()
