# Clipchamp Narrated Demo Video

Turn a live web app or Copilot Studio agent into a polished, narrated demo — real
screen-flow footage (cursor, typing, live responses) under an AI voiceover — without
manually screen-recording or editing anything yourself.

## Before you start

- **Windows only.** This skill drives PowerShell, Win32 window APIs, `msedge.exe`, and ffmpeg's `gdigrab` desktop capture — there's no macOS/Linux capture backend yet.
- **Node.js + Playwright** (`npm install -g playwright`), **ffmpeg/ffprobe**, and
  **edge-tts** (`pip install edge-tts`) should be installed globally so every future
  run just works. The skill checks and installs these once if missing.
- A **logged-in browser session** for whatever you're recording (Copilot Studio, an
  internal app, etc.) — the skill drives your real, authenticated session so it
  captures the actual product, not a mocked one.
- Decide up front which agent/app you want demoed and roughly what it should show
  (an overview, a couple of live test prompts, etc.) — the more specific, the better
  the final narration.

### One-time global installs

**Install these ONCE, globally, so every future run has them without reinstalling.**
Check each first; only install if missing. After changing PATH, refresh the *current*
shell with `$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")`
(new shells pick it up automatically).

| Need | Make it global (persist across runs) |
| ---- | -------------- |
| Node + Playwright (library) | Check: `node -e "require('playwright')"` via global root, or `npm ls -g playwright`. If missing: **`npm install -g playwright`** (global, not in a throwaway work dir). The scripts in `scripts/` resolve it automatically via `npm root -g` (see `scripts/require-playwright.js`) — you don't need to set `NODE_PATH` yourself. |
| ffmpeg + ffprobe | Check: `ffmpeg -version`. If missing: `winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements --disable-interactivity`, then **copy `ffmpeg.exe`/`ffprobe.exe` into `C:\Users\<user>\.copilot\bin` and add that folder to the User PATH** (`[Environment]::SetEnvironmentVariable("Path", $userPath + ";C:\Users\<user>\.copilot\bin", "User")`). The stable folder survives ffmpeg version bumps. |
| edge-tts (Ava neural TTS, headless path) | Check: `python -c "import edge_tts"`. If missing: **`pip install edge-tts`** (user install is fine — `python -m edge_tts` then works in every run). For the bare `edge-tts` CLI, add the Python **Scripts** dir (e.g. `C:\Users\<user>\AppData\Roaming\Python\Python3XX\Scripts`) to the User PATH. Voice: `en-US-AvaNeural`. |
| Logged-in browser | The MCP Playwright browser holds your session. Profile dir typically `C:\Users\<user>\AppData\Local\ms-playwright\mcp-msedge`, Edge at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`. For a **different tenant**, **clone** your real Edge profile to a non-default `User Data` root and launch that with the matching `--profile-directory` — Playwright cannot attach to Edge's default data dir. See `SKILL.md`'s "Pick the right profile / tenant" section for the exact steps. |

## How to use it

Ask for a demo video the way you'd ask a person: *"Record a demo of my Copilot Studio
agent"*, *"make a narrated walkthrough of this app"*, *"turn this into a product demo
video"*. The skill will:

1. Ask you to pick an assembly path: **(A) headless** (ffmpeg + Ava neural TTS —
   fast, deterministic, hands you a finished MP4) or **(B) Clipchamp web UI**
   (slower, but leaves an editable Clipchamp project for hand-tweaking later).
2. Drive a real browser against your logged-in session, record the actual screen
   flow, and trim out dead time (auth screens, long tool-call waits) so the final
   cut only shows the meaningful beats.
3. Generate a natural-sounding voiceover (Ava neural voice) narrating what's on
   screen, timed to the visible beats — not one long monotone block.
4. Hand you back a finished MP4 (headless path) or a ready-to-tweak Clipchamp
   project (UI path), named after your agent/product.

## Good to know

- The recorded frame is the **browser's internal viewport buffer**, not your visible
  screen — so you can keep using your laptop while it records (headless path). The
  one exception is the dual-capture mode (recording your own actions *and* the app
  side-by-side), which does need the desktop free of other windows/notifications.
- Copilot Studio's Build/Preview/Evaluate/Monitor switcher is a dropdown, not tabs —
  the skill already knows to jump straight to the `/preview` URL rather than
  clicking through menus.
- If the recorded video shows your app content in a small corner with a lot of gray
  padding around it, that's the browser window not filling the screen — the skill
  crops and rescales this automatically during post-processing, but it's a good
  sanity check to do yourself on a sample frame before narrating.
- A demo full of red error cards from a sleeping backend is worse than no demo —
  the skill tests one real prompt before the full recording run specifically to
  catch this early.
