---
name: "clipchamp-video"
description: >-
  Create narrated demo/explainer videos of a live web app or agent, with real
  screen-flow footage under an AI (Ava neural) voiceover. Use whenever the user
  wants to "make a video", "record a demo", "create a walkthrough", "screen
  record an agent/app and narrate it", "build a Clipchamp video", "produce a
  product demo", or turn a Copilot Studio / web-app flow into a narrated MP4.
  FIRST ask the user which assembly method to use: (A) headless ffmpeg +
  edge-tts Ava — fast, scripted, produces a finished MP4 directly — or (B) the
  Clipchamp web UI — slower, but leaves an editable Clipchamp project for
  hand-tweaking later.
---

# Clipchamp Narrated Demo Video Skill

Produce a polished, narrated demo video: **real screen-flow footage of a live app/agent** under an **AI voiceover**. This captures hard-won lessons — read it fully before starting.

## STEP 0 — ASK THE USER: which assembly method? (do this FIRST, before recording)

The recording step is identical for both. The **assembly + narration** step has two paths — ask the user to pick before you start, e.g. via `m_ask_user`:

> "How should I assemble the video — **(A) Headless (ffmpeg + Ava neural TTS)** — faster (~2–3 min), scripted, precise, produces a finished MP4; or **(B) Clipchamp web UI** — slower (~15–25 min of browser clicks) but gives you an **editable Clipchamp project** to hand-tweak later (transitions, captions, music)?"

Guidance to offer with the question:
- **Default / recommended: (A) Headless** — faster, deterministic, exact narration timing, no session-drop/upload-hook risk. Best when the deliverable is just the finished MP4.
- **Choose (B) Clipchamp** only if the user wants an editable project living in their Clipchamp account, or plans manual edits (transitions, captions, background music, hand re-timing).
- **(B) requires the `playwright-browser_*` MCP tools.** If those tools are not available in the session (they can be disabled/dropped), (B) is impossible — tell the user and either have them re-enable the Browser Control tools / start a new chat, or fall back to (A).

Record the flow the same way either path (§1), then follow **§2 + §2b (headless)** or **§3 (Clipchamp)** based on their choice.

## STEP 0b — ASK: page-only capture, or "your actions + the chat" (dual capture)?

If the user says anything like *"record your actions and the chat at the same time"*, *"show what you're doing while it runs"*, *"a making-of"*, or *"I want to see both"* — they want **the Scout/assistant conversation visible alongside the app**, not just the app. That is a **different capture mode** and you must pick it BEFORE recording:

- **Page-only (default, §1).** Playwright `recordVideo` captures the page's internal buffer. Clean, no browser chrome, immune to other windows / screen switches. **It physically cannot capture the Scout window** — `recordVideo` only ever sees the one page.
- **Dual capture (§1b).** OS-level desktop capture with **ffmpeg `gdigrab`** while Scout and the automated browser sit **side by side**. One capture, so the two halves are perfectly in sync for free.

Do NOT try to satisfy a dual-capture request by recording the page and hoping to add the chat later — you cannot recover the chat pixels after the fact.

## §1b — Dual capture: agent actions + the app, side by side

Verified working (`ffmpeg 8.x`, Windows): `-f gdigrab -framerate 15 -i desktop` produced a clean 1920×1280 H.264 capture.

**Ready-made scripts:** `scripts/arrange.ps1` (side-by-side window placement) and `scripts/dual-capture.js` (starts gdigrab, runs `recorder.js`, stops ffmpeg cleanly, probes the result). Run `node dual-capture.js out.mp4`.

1. **Arrange the two windows first.** Put the automated Edge on one half and the Scout window on the other — see `scripts/arrange.ps1`. It matches Edge by command line (`*edge-tenant*`) and Scout by process name / window title, then `MoveWindow`s each to half the working area.
   **Recompute the device-scale factor for the narrower window** — half-width means the CSS viewport halves too. Re-run the empirical calibration from "Make the window fill the user's screen" against the half-width, or the chat input bar will be cut off. The MANDATORY GATE still applies, at the half-width geometry.
2. **Start ffmpeg detached, before the recorder**, and give it a couple of seconds of lead-in:
   ```powershell
   ffmpeg -y -f gdigrab -framerate 15 -i desktop -c:v libx264 -pix_fmt yuv420p -crf 23 -preset veryfast dual.mp4
   ```
   Capture `desktop` (the whole screen) rather than `-i title=<window>`: per-window gdigrab breaks whenever the window is occluded, moved, or redrawn, and it silently drops frames. Crop later with ffmpeg if you want a tighter frame.
3. **Stop ffmpeg gracefully** — write `q` to its stdin, or it may leave the MP4 without a moov atom (unplayable). If you must kill it, use `Stop-Process -Id <pid>` and then remux: `ffmpeg -y -i broken.mp4 -c copy fixed.mp4`.
4. **Consequences of desktop capture — tell the user up front:**
   - **They must not use the machine while it records.** Unlike `recordVideo`, everything on screen ends up in the video: notifications, other windows, the taskbar.
   - **Toasts and popups will appear.** Enable Focus Assist / Do Not Disturb first.
   - **Anything private on screen is captured.** Close unrelated mail/chat windows before starting.
5. **Alternative when the user wants both but can't stop working:** record the page-only video (§1), then composite the chat as a separate pass afterwards (screenshots of the conversation as an intro/outro, or a picture-in-picture strip). Sync will be approximate — say so rather than implying frame accuracy.
6. **Compositing two separate sources** (only if you truly captured them separately) — normalize both to the same height and fps first, then stack:
   ```powershell
   ffmpeg -y -i app.mp4 -i chat.mp4 -filter_complex `
     "[0:v]scale=-2:1080,setsar=1,fps=30[l];[1:v]scale=-2:1080,setsar=1,fps=30[r];[l][r]hstack=inputs=2,pad=ceil(iw/2)*2:ceil(ih/2)*2" `
     -c:v libx264 -pix_fmt yuv420p -crf 20 composite.mp4
   ```
   `hstack` **requires identical heights** or it errors out; the trailing `pad=ceil(iw/2)*2:...` keeps dimensions even for yuv420p. For picture-in-picture use `overlay=W-w-40:H-h-40` instead of `hstack`.

## The winning approach (and why)

A slideshow of static screenshots is almost never what the user wants. They want to **see the app move** — cursor, typing, live responses. The reliable way to get that autonomously:

1. **Drive the real app with Playwright** and record **page-only video** (`recordVideo`). This is clean (no browser chrome) and hands-off. Raw OS screen capture is worse: synthetic automation cursors often don't render, and it captures the whole desktop. **Exception:** if the user explicitly wants the assistant conversation in-frame too, `recordVideo` cannot do it — switch to §1b dual capture.
2. **Reuse the user's logged-in browser profile** so auth is preserved (e.g. Copilot Studio, M365). Never spin up a fresh profile — you'll lose the session. **If the target lives in a different tenant than the MCP browser's signed-in account, use the real Edge profile for that tenant instead of signing in interactively** — see "Pick the right profile / tenant" below.
3. **Cut the auth/loading head** from the recording with ffmpeg — the account picker, "Stay signed in", and app "Initializing…" spinner are dead air.
4. **Narrate with the Ava neural voice** — either Clipchamp's built-in Text to speech or edge-tts `en-US-AvaNeural` — split into **several short blocks aligned to on-screen moments**, not one long block. Silence between events feels broken; short blocks with technical call-outs ("here it invokes a skill to query the table") make it feel alive.
5. **Name the export after the agent/product**, not "Video Project 1".

## Prerequisites

**Windows only** (PowerShell, Win32 window APIs, `msedge.exe`, ffmpeg `gdigrab` desktop capture) — this skill does not currently have macOS/Linux capture backends. See `README.md` for the one-time global install steps (Node + Playwright, ffmpeg/ffprobe, edge-tts) and how to check each is already present before installing.

### Ready-made scripts (`scripts/`)

Working, battle-tested versions live next to this file. Copy them into the task's work dir and edit the constants at the top of `common.js` (clone path, env id, agent id, target account) rather than writing new ones from scratch.

| Script | Purpose |
| ------ | ------- |
| `clone.ps1` | Kill real Edge, clone the tenant profile to a non-default root (caches excluded), regex-patch `Preferences`. **Re-run whenever auth breaks.** |
| `prep.ps1` | Between runs: kill stale Edge (cloned profile only) and this workflow's own Node processes, clear `Singleton*` locks, reset `exit_type`/`exited_cleanly`. Run before every launch. |
| `maximize.ps1` | Win32 `MoveWindow`+`SW_MAXIMIZE` on the cloned-profile Edge window (the only thing that reliably resizes it). |
| `arrange.ps1` | Side-by-side placement (browser left, Scout right) for §1b dual capture. |
| `common.js` | Shared launch `ARGS`, the `settle()` auth/stability loop, `dismissPopups()`, `logViewport()`, `maximizeWindow()`. |
| `verify.js` | **The MANDATORY GATE** — loads the target, opens the test pane, sends one real prompt, screenshots the frame. |
| `recorder.js` | The real run: overview → instructions → skills/tools scroll → N live test prompts, with `progress.log` beat markers. |
| `dual-capture.js` | §1b: starts gdigrab, runs `recorder.js`, stops ffmpeg cleanly, probes the output. |
| `findagent.js` | Scrape the agents grid (`[role="row"]`) for names, then open one and harvest its real id from the URL. |
| `diag.js` | When a page renders blank: timed screenshots + console errors + HTTP ≥400 logging. |

### Pick the right profile / tenant (do this BEFORE anything else)

The MCP browser is usually signed in to the user's **primary** work account. If the agent/app lives in a **different tenant** (e.g. a `*.onmicrosoft.com` dev/demo tenant), that session will 404 or bounce to the wrong environment. **Do not try to sign in interactively** and do not ask the user to type a password — the user almost always already has a **second Edge profile** signed in to that tenant. Find it and drive that.

1. **Detect the mismatch early.** Open the target URL in the MCP browser; a blank page, `404` on `api.bap.microsoft.com/.../environments/<id>`, or a redirect to `~personal`/a different environment ID means wrong tenant. Confirm the signed-in identity (in Copilot Studio: click `[data-testid="account-profile-button-trigger"]`).
2. **Enumerate the real Edge profiles and their accounts** — map `Default`, `Profile 1`, `Profile 2`… to emails by reading each profile's `Preferences`:
   ```powershell
   $ud = "$env:LOCALAPPDATA\Microsoft\Edge\User Data"
   Get-ChildItem $ud -Directory | Where-Object { $_.Name -eq 'Default' -or $_.Name -like 'Profile*' } | ForEach-Object {
     $p = Join-Path $_.FullName 'Preferences'
     if (Test-Path $p) { try { $j = Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json
       [PSCustomObject]@{ Dir=$_.Name; Name=$j.profile.name; Email=$j.account_info[0].email } } catch {} }
   } | Format-Table -AutoSize
   ```
   Note the **directory name** (`Profile 1`), *not* the display name (`Profile 2`) — they routinely disagree, and Playwright needs the directory.
3. **CLONE the profile to a non-default User Data root — do NOT drive the real one.** Edge **refuses remote debugging on its default data directory** and `launchPersistentContext` dies after 180 s with:
   `Timeout 180000ms exceeded` + `[err] DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.`
   Cloning also frees you from the real-Edge profile lock. Copy only what carries auth — skip the caches, which are the bulk (a 3 GB profile drops to ~300 MB, and `Service Worker` alone was 2 GB):
   ```powershell
   $src = "$env:LOCALAPPDATA\Microsoft\Edge\User Data"; $dst = "C:\Users\<user>\.copilot\video-work\edge-tenant"
   New-Item -ItemType Directory -Force -Path $dst | Out-Null
   Copy-Item "$src\Local State" "$dst\Local State" -Force
   robocopy "$src\Profile 1" "$dst\Profile 1" /E /NFL /NDL /NJH /NJS /R:0 /W:0 /XJ `
     /XD "Service Worker" "Cache" "Code Cache" "GPUCache" "Shared Dictionary" "DawnGraphiteCache" "DawnWebGPUCache" "Crashpad" "optimization_guide_model_store"
   ```
   Keep `Network\Cookies`, `Login Data`, `Local Storage`, `IndexedDB`, `WebStorage`, `Preferences` — that's what preserves the session. Then launch `launchPersistentContext(<clone root>, { args: ['--profile-directory=Profile 1', ...] })` — still the **root**, never the profile subfolder.
   **The clone is a snapshot, not a link.** If auth later breaks, have the user load the target URL in their own Edge and then **re-clone** — that is the fastest repair, and far more reliable than any scripted sign-in (see the passkey pitfall below). Close the real Edge only while cloning (files are locked mid-copy).
4. **Close the real Edge only while cloning** (files are locked mid-copy). Kill only the non-Playwright `msedge.exe` processes, delete `Singleton*` under the target root, and patch `Profile 1\Preferences` (`exit_type`→`Normal`, `exited_cleanly`→`true`) so no "Restore pages?" bubble appears in-frame.
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
     Where-Object { $_.CommandLine -notlike '*m-playwright-profiles*' -and $_.CommandLine -notlike '*ms-playwright*' } |
     ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
   ```
   Filtering by command line matters: killing everything also kills the MCP browser you may still need.
5. Real profiles can be **multi-GB** and slower to boot than `mcp-msedge` — allow generous first-navigation timeouts (90–120 s) and a long post-load settle before recording.
6. **Wait for auth with a stability loop, never a fixed sleep.** MSAL bounces *back* to `login.microsoftonline.com/…/oauth2/v2.0/authorize` for a silent token refresh **after** you appear to have landed on the app — a one-shot "am I on the app host?" check passes, then the very next screenshot is a login URL with 200 chars of body text. Poll every 2 s and require **N consecutive good polls** (host matches AND `document.body.innerText.length` is large AND no `Initializing|Loading your|Getting things ready` spinner). Handle the sign-in UI inside the same loop:
   ```js
   async function settle(page, budgetMs = 240000, needStable = 4) {
     const t0 = Date.now(); let stable = 0;
     while (Date.now() - t0 < budgetMs) {
       const u = page.url();
       if (u.includes('login.microsoftonline.com')) {           // "Stay signed in?"
         stable = 0;
         const cb = page.locator('#KmsiCheckboxField').first();
         if (await cb.isVisible({ timeout: 400 }).catch(() => false)) await cb.check({ timeout: 2000 }).catch(() => {});
         const yes = page.locator('#idSIButton9').first();       // the Yes/Next button
         if (await yes.isVisible({ timeout: 800 }).catch(() => false)) { await yes.click({ timeout: 3000 }); await page.waitForTimeout(4000); continue; }
         const tile = page.locator('div[role="button"]:has-text("user@"), small:has-text("user@")').first();
         if (await tile.isVisible({ timeout: 600 }).catch(() => false)) { await tile.click({ timeout: 3000 }); await page.waitForTimeout(4000); continue; }
         await page.waitForTimeout(2000); continue;
       }
       if (u.includes('<app-host>')) {
         const len = await page.evaluate(() => document.body.innerText.length).catch(() => 0);
         const busy = await page.locator('text=/Initializing|Loading your|Getting things ready/i').count().catch(() => 0);
         if (len > 400 && !busy) { stable++; if (stable >= needStable) return true; } else stable = 0;
       } else stable = 0;
       await page.waitForTimeout(2000);
     }
     return false;
   }
   ```
   Use the account **tile** selectors (`div[role="button"]:has-text("user@")`, `small:has-text("user@")`) — `[data-test-id*="…"]` attributes on the account picker are unstable. Check `#KmsiCheckboxField` ("Don't show this again") before clicking `#idSIButton9` so the prompt stops recurring on later runs.

### Make the window fill the user's screen (they WILL be watching it)

The user sees the automated window while it records; a tiny 800×600 window that can't be moved or resized is a real complaint. Three separate traps:

1. **`viewport: {width, height}` locks the window.** Playwright *emulates* a fixed viewport and the window becomes unresizable. Use **`viewport: null`** so the page tracks the real window — then control size via launch args. (`recordVideo` still captures the page buffer, so the recording stays clean.)
2. **`--start-maximized` and `--window-size` are BOTH silently ignored on a profile that has saved window bounds** — you get a stubborn 800×600. Removing `browser.window_placement` from the clone's `Preferences` is *not* reliable either, and CDP `Browser.setWindowBounds` fails under `launchPersistentContext` (`Protocol error: Browser window not found`). **What actually works: resize the real Win32 window after launch.** Call this right after launch, and again after each navigation (the app can re-trigger a resize):
   ```powershell
   # maximize.ps1 - maximize the Edge window belonging to our cloned profile
   Add-Type @"
   using System; using System.Runtime.InteropServices;
   public class Win {
     [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
     [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int t, bool r);
     [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
   }
   "@ -ErrorAction SilentlyContinue
   Add-Type -AssemblyName System.Windows.Forms
   $wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
   Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
     Where-Object { $_.CommandLine -like '*edge-tenant*' } | ForEach-Object {
       $p = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
       if ($p -and $p.MainWindowHandle -ne 0 -and [Win]::IsWindowVisible($p.MainWindowHandle)) {
         [Win]::ShowWindow($p.MainWindowHandle, 9) | Out-Null              # SW_RESTORE
         [Win]::MoveWindow($p.MainWindowHandle, $wa.X, $wa.Y, $wa.Width, $wa.Height, $true) | Out-Null
         [Win]::ShowWindow($p.MainWindowHandle, 3) | Out-Null              # SW_MAXIMIZE
       } }
   ```
   Filter by command line (`*edge-tenant*`) so you only touch your own window, and invoke it from Node with `child_process.execSync('powershell -NoProfile -ExecutionPolicy Bypass -File maximize.ps1')`.
3. **Measure the screen correctly — logical ≠ physical.** `[System.Windows.Forms.Screen]` reports **logical** px (already divided by the Windows display scale), while `screen.width` in the browser reports **physical**. A machine reporting `1536×1024` from PowerShell was really `2400×1600` at 156 % scale. Reconcile before computing sizes, or you will undersize the window by the scale factor.

   **Calibrate empirically instead of deriving it.** Launch once at a known `--force-device-scale-factor`, maximize, and read the CSS width; CSS width scales as `1/dsf`, so:
   `dsf_target = dsf_measured × (cssWidth_measured / cssWidth_wanted)`
   Worked example: at `dsf 0.8` the maximized window measured **2376 CSS px** wide. For a 1920-wide capture: `0.8 × 2376/1920 = 0.99`. Relaunching at `--force-device-scale-factor=0.99` produced **1916×1162** — a full-screen window *and* a ~1920 px capture buffer.
   ```
   '--force-device-scale-factor=0.99', '--start-maximized',
   ```
   Read the real numbers from the browser, not from PowerShell, and log them every run:
   ```js
   await page.evaluate(() => ({ w: innerWidth, h: innerHeight, dpr: devicePixelRatio, sw: screen.width, sh: screen.height }))
   ```

## Workflow

### 1. Record the real flow

> ⛔ **MANDATORY GATE — DO NOT RECORD until the chat input bar is verified fully visible.**
> The single most common defect is the chat input bar (and the end of the last message) being cut off at the bottom of the frame. You **MUST** pass this gate before every recording run — no exceptions, even if a previous run "looked fine":
> 1. Run **`scripts/verify.js`** (same launch args/viewport as the recorder). It opens the target, dismisses popups, handles the account picker, sends ONE test message, and screenshots the **viewport buffer** (which is exactly what gets recorded — NOT the on-screen window).
> 2. **View that screenshot** and confirm ALL of these are visible in-frame: the header, the latest message bubble's END, the chat **input bar** ("Ask a question…"), and the disclaimer line. Do not rely on the on-screen window (it may be cut by the physical screen/taskbar); judge only from the screenshot.
> 3. If ANY of them is cut off → **adjust the viewport height and re-run verify.js. Repeat until the screenshot passes.** Never proceed to the real recording on a failed/uncertain frame.
> 4. Use the SAME `viewport` and launch `args` in `recorder.js` that passed the gate.
>
> Reference that passes for Copilot Studio at 1920 wide: viewport **1920×880**. Treat this as a starting point, still verify per app/screen.

- Confirm the target URL and the scenario steps (prompts to type / buttons to click) with the user.
- **Free the browser profile first.** Only one process can lock the persistent profile. Kill any Edge processes using the profile dir before launching the recorder (see `scripts/prep.ps1`, which also clears stale `Singleton*` lock files and normalizes the crash-restore flags), otherwise `launchPersistentContext` fails with "Failed to launch… Opening in existing browser session".
- Run `scripts/recorder.js` (template provided) **only after the visibility gate passes**. It launches the logged-in profile, records page video, drives the chat/app with human-like typing, waits for each response to stabilize, holds for readability, then closes to flush the `.webm`.
- **Submit reliably:** prefer clicking the Send button and confirm the input box empties; pressing Enter alone can concatenate prompts into one bubble. The template's `submit()` handles this.
- **Copilot Studio's Build/Preview/Evaluate/Monitor switcher is a `menuitemradio` DROPDOWN behind a single "Build" button, not tabs.** `getByRole('tab', {name: /Preview/i})` will silently find nothing and `openTestPane()` will time out waiting for the chat input. Two fixes, prefer the first:
  1. **Just navigate directly to `${AGENT_URL}/preview`** (`page.goto`) — clicking the option once reveals the URL pattern is stable (`/agents/<id>/preview`), and a direct `goto` is far more reliable than menu-click choreography. This is what `openTestPane()` in the shared `recorder.js`/`verify.js` templates now does.
  2. If you must click through the UI: click the button whose accessible name is the *current* tab label (e.g. `Build`) to open the menu, then click the `menuitemradio` named `Preview` inside it (`page.getByRole('menuitemradio', {name: /^Preview$/i})`).
  - **Diagnose this class of bug fast:** if a locator search for the expected tab/button comes back empty, don't guess — take a `browser_snapshot`/screenshot of the live page (via the `playwright-browser_*` MCP tools, reusing the same signed-in tenant profile) to see the actual accessibility tree before patching the recorder script blind.

#### Robust, clean capture (learned the hard way — bake these into the recorder)
- **Suppress Edge nag UI with launch args** so no banners/bubbles pollute the frame:
  `--test-type` (kills the yellow "unsupported command-line flag" infobar), `--disable-infobars`, `--hide-crash-restore-bubble`, `--disable-session-crashed-bubble`, `--no-first-run`.
- **Kill the "Restore pages?" bubble at the source:** after force-killing Edge between runs, patch the profile `Default/Preferences` before relaunch — replace `"exit_type":"..."` → `"exit_type":"Normal"` and `"exited_cleanly":false` → `"exited_cleanly":true`.
- **Auto-handle the Microsoft account picker.** If a sign-in/account chooser appears, click the correct account by regex on its email/tenant (ask the user which account once, then match it) — otherwise the run stalls. See `pickAccountIfNeeded()` in the template.
- **Dismiss product coach-marks / NPS / cookie popups.** Loop over buttons named `Close`, `Got it`, `Dismiss`, `No thanks`, `Skip`, `Not now`, `Accept`, `OK`, then press `Escape`. Call it after load AND after opening the chat/preview pane. See `dismissPopups()`.
- **Size the viewport so the chat input bar is fully in-frame (see the MANDATORY GATE above).** The recorded frame is the *viewport buffer*, not the on-screen window, so it can exceed the physical screen. For Copilot Studio at 1920-wide, a viewport of **1920×880** shows the header, messages, the "Ask a question" input bar, and the disclaimer line. This is NOT optional guesswork — you must prove it with `verify.js` and a screenshot before recording, and re-run until it passes.
- **Scroll to the END of each response before typing the next turn** so the full answer is on screen, and pin to bottom during holds — this also hides the floating "Scroll to bottom" down-arrow. See `scrollBottom()` + `readHold()`.
- **You can keep using the laptop / switch screens during recording.** `recordVideo` captures the page's internal buffer, not your monitor, so other windows, screen switches, or minimizing never appear. Only avoid closing the automated Edge window or sleeping the machine.
- **Run detached with synchronous file logging.** Long recordings (slow tool calls, timeouts) can outlive a tool call; launch the recorder detached so it survives, and have it `fs.appendFileSync` a timestamped `progress.log` per step (console output to a redirected file is block-buffered and looks "stuck"). Poll `progress.log` + node/edge process counts to track real progress.

### 2. Post-process with ffmpeg
- Probe duration & sample frames every few seconds to **map when each scenario happens** and **find where auth ends**:
  ```powershell
  ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 in.webm
  ffmpeg -y -i in.webm -vf "fps=1/5" frame_%03d.png    # then view frames
  ```
- **Cut auth + crop empty margins**, convert to H.264 MP4 (Clipchamp-friendly). Example: drop first 30s, crop to content:
  ```powershell
  ffmpeg -y -ss 30 -i in.webm -vf "crop=1280:600:0:0,setsar=1" -c:v libx264 -pix_fmt yuv420p -crf 20 -preset medium out.mp4
  ```
- **If `maximize.ps1` couldn't fill the physical screen** (small/low-res display, or a screen-resolution change since the empirical DSF calibration), the recorded buffer will show the real app content only in a small corner with a large flat-gray dead zone around it — check a sampled frame BEFORE narrating, not after. Fix by cropping to the actual content bounding box (read it off a sample frame — e.g. `crop=782:600:0:0`), then `scale` up to a target size and `pad` onto a white/black canvas to reach a standard resolution (16:9 for a normal video deliverable):
  ```powershell
  ffmpeg -y -i in.webm -vf "crop=782:600:0:0,scale=1303:1000,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white" -c:v libx264 -pix_fmt yuv420p -crf 20 out.mp4
  ```
  Do this crop/scale/pad **per trimmed segment inside the same `trim`+`concat` filter_complex** (not as a separate pass) so segments stay in sync — see the worked multi-segment example below.
- **Hit a target length (e.g. ≤ 2 min) by cutting DEAD TIME, not content.** Agent demos have long dead gaps during slow tool calls / timeouts. Don't speed-ramp the whole clip — instead pick keep-windows around each meaningful beat (question asked, skill loads, result appears) and drop the multi-second waits between them. Extract each window with `-ss <start> -t <dur>`, normalize them all to the same size/fps (`scale=...,pad=1920:1080,setsar=1,fps=30`), then concat. Use the recorder's `progress.log` timestamps to locate beats fast.
  - concat gotcha: `ffmpeg -f concat` resolves `file '...'` paths **relative to the concat file's own directory** — list bare filenames and run from that dir, or use absolute paths.
- Note the trimmed clip's exact duration and each segment's start offset — you'll align narration to these.

### 2b. Narration without the Clipchamp UI (headless, reliable fallback)
### 2b. PATH (A) — Narration without the Clipchamp UI (headless, fast, recommended default)
When the browser/Clipchamp UI isn't available (or you just want a deterministic build), generate the voiceover with **edge-tts** (same Ava neural voice) and mux with ffmpeg:
- Write one text block per beat with `(start_time, max_dur, text)`. Generate each: `python -m edge_tts --voice en-US-AvaNeural --text "..." --write-media bNN.mp3` (in code, bump `rate` `+8%`/`+15%`/… until a block fits its `max_dur`).
- Build a single voice track by delaying each block to its start: `[i:a]adelay=START_ms|START_ms,apad[ai]` then `amix=inputs=N:normalize=0` and `atrim=0:TOTAL`.
- Mux onto the trimmed video: `ffmpeg -i cut.mp4 -i voice.m4a -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest final.mp4`.
- Name the output after the agent/product and copy it into the user's workspace/OneDrive folder so it renders inline and syncs.

### 3. PATH (B) — Assemble in Clipchamp (browser automation; editable project)
Only if the user chose (B) in STEP 0 AND the `playwright-browser_*` tools are available.
Read **[clipchamp-ui.md](clipchamp-ui.md)** for the exact click targets, selectors, and gotchas. High level:
1. Open https://app.clipchamp.com → open (or recover) the project, or create a new one.
2. **Import media** → file chooser → `browser_file_upload` the trimmed MP4 (+ any intro screenshot). If a permission hook blocks uploads, ask the user to enable **Settings → Permissions → Allow agent file uploads**.
3. Add media to the timeline via each item's "Add to timeline" button (drops at the playhead).
4. Optionally add an intro still (e.g. a "Build"/architecture screenshot) so the video opens on context.
5. **Voiceover:** open **Record & create → Text to speech** (or select an existing TTS clip's **Text to speech** tab), pick **Ava Multilingual**, type the block text, **Save** to render. New TTS blocks drop **at the playhead** — set the playhead precisely first via the time input spinbuttons (Minutes/Seconds), then create the block.
6. Cover any black tail after the video ends with a closing still so the final voiceover has a visual.

### 4. Export
- **Export → set the File name to the agent/product** (e.g. `Contoso IT Assistant - Demo`), 1080p, keep "Store in the cloud" → **Export**. If prompted about an existing name, choose **Keep both** or **Replace** as the user prefers.
- Output lands in OneDrive: `Videos/Clipchamp/<project>/Exports/<name>.mp4`. It may not sync to the local folder immediately; the export screen's **Copy link** / **Save to your computer** are the fallbacks.

## Narration authoring tips
- One block per on-screen beat; ~1–3 short sentences each. Keep total pacing tight — aim for little dead air.
- Add **technical call-outs** that describe the mechanics the viewer is seeing: which skill/tool fired, what data source it hit ("queries the knowledge table", "calls the create-record tool", "reads the live schedule").
- Keep it **generic** if asked — strip customer/company names.
- End on a **hero voiceover line** (no card needed) that names the value prop and the tech, e.g. "That's the power of AI, combining X and Y to turn Z into one seamless, autonomous experience."
- Remove leftover title-text overlays if the intro screenshot already shows the name.

## Common pitfalls (all learned the hard way)
- **`Timeout 180000ms exceeded` on `launchPersistentContext` + `DevTools remote debugging requires a non-default data directory`** → you pointed Playwright at Edge's **default** `User Data` root. Edge blocks remote debugging there. **Clone the profile to a separate root** (see "Pick the right profile / tenant" step 3) and launch against the clone.
- **App renders a totally blank page, `document.body.innerText.length === 0`, `outerHTML` is ~1 MB, and the network log shows `404` on `api.bap.microsoft.com/.../environments/<id>`** → the app shell loaded but **MSAL silently issued a token for the wrong tenant**. Confirm by reading the MSAL cache instead of guessing:
  ```js
  await page.evaluate(() => { const o = [];
    for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i);
      try { const j = JSON.parse(localStorage.getItem(k)); if (j && (j.username || j.tenantId)) o.push({ u: j.username, t: j.tenantId }); } catch {} }
    return o; });
  ```
  A `tenantId` of `72f988bf-86f1-41af-91ab-2d7cd011db47` is the **Microsoft corp** tenant — i.e. it authenticated as the primary work account, not the dev/demo tenant. Clearing `localStorage`/`sessionStorage` and the app's cookies does **not** fix it: the `login.microsoftonline.com` session cookie still defaults to the primary account, so it silently re-SSOs to the same wrong identity.
  **Fix:** force the picker by navigating to the tenant-scoped authorize endpoint with `prompt=select_account` + `login_hint` before loading the app:
  ```
  https://login.microsoftonline.com/<tenant>.onmicrosoft.com/oauth2/v2.0/authorize
    ?client_id=<app spa client id>&response_type=code
    &redirect_uri=<url-encoded app redirect>&response_mode=fragment
    &scope=openid%20profile%20offline_access
    &prompt=select_account&login_hint=<user@tenant>
  ```
  Read the SPA `client_id` straight out of the MSAL localStorage key (`msal.<client-id>.active-account-filters`). Then click the tenant tile — `div[data-test-id="<full upn>"]` is the reliable selector on the "Pick an account" screen.
- **Never test "did we land on the app?" with `url.includes('<app-host>')`** → the authorize URL embeds the app host inside its own `redirect_uri` query param, so `includes()` returns true while you are still sitting on the login page, and your picker loop exits before clicking anything. Compare `new URL(u).host` instead. Apply this to `settle()` too.
- **Sign-in loop spins forever re-clicking the account tile and the host becomes `login.microsoft.com/<tenant>/bridge/fido`** → the account requires **passkey / Windows Hello**, which cannot be automated. The cookie-based SSO you cloned has expired.
  **Do not burn time scripting around this.** An automated `prompt=select_account` flow will *still* silently resolve back to the Windows-connected primary account (`Connected to Windows` on the picker always wins), so the MSAL cache stays on the wrong tenant no matter how many times you clear storage.
  **The reliable fix — always prefer it:** ask the user to open **their own normal Edge** on the target URL and confirm it loads. Then **re-clone the profile** (the clone captures the freshly-minted cookies) and every subsequent automated run works. This takes one message and ~2 minutes; driving an in-Playwright interactive sign-in is slower, and the user may not notice the window at all — an unattended "waiting for user" poller will just time out.
  Note `login.microsoft.com` and `login.microsoftonline.com` are **different hosts** — match both when detecting auth pages. Treat the clone as a **cache of the user's live session**: whenever auth looks wrong, re-run the clone step before debugging anything else.
- **Do NOT round-trip Chromium `Preferences` through `ConvertFrom-Json`/`ConvertTo-Json`** → it reorders keys and retypes values, and can leave the profile in a broken state. Patch it with **targeted regex string replacement** only:
  ```powershell
  $c = Get-Content $pf -Raw -Encoding UTF8
  $c = $c -replace '"exit_type":"[^"]*"','"exit_type":"Normal"' -replace '"exited_cleanly":false','"exited_cleanly":true'
  [System.IO.File]::WriteAllText($pf, $c, (New-Object System.Text.UTF8Encoding($false)))
  ```
- **User asks for "your actions and the chat at the same time" and you already recorded page-only** → `recordVideo` captured only the page buffer; the assistant conversation was never in those pixels and cannot be added retroactively. You must re-record with **§1b dual capture** (gdigrab + side-by-side windows). Ask which capture mode they want *before* recording.
- **gdigrab MP4 won't play / has no duration** → ffmpeg was killed instead of being asked to stop, so the moov atom was never written. Send `q` to stdin to stop it; recover an existing file with `ffmpeg -i broken.mp4 -c copy fixed.mp4`.
- **`hstack` fails with "Input link parameters do not match"** → the two sources have different heights or SAR. Scale both to the same height and `setsar=1` before stacking.
- **Chat input bar cut off after switching to side-by-side windows** → halving the window width changes the CSS viewport, so the previously-calibrated device-scale factor no longer holds. Re-calibrate and re-run the visibility gate at the new geometry.
- **Copilot Studio agent tabs are `Build | Preview | Evaluate | Monitor`** → the test chat is under **Preview** (not "Test"). The agent's overview page under **Build** already lists Instructions, Model, **Skills**, **Tools**, and **Knowledge** in one scrollable column — one slow scroll covers the whole "what this agent is" section, no tab-hopping needed.
- **A tool call in the demo returns a red error card (e.g. `Request validation · 400`)** → the backing system may be asleep (some dev/sandbox backends hibernate) or the action is genuinely misconfigured. **Check this during the visibility gate, not after recording** — send one real test prompt and read the answer. If the backend is down, tell the user and get it woken up before the real run; a demo video full of error cards is worthless.
- **The agent you want isn't in the agents list** → the list only shows agents in *that* environment, and a broken-tenant session renders an empty body so **every** agent looks missing. Confirm auth first, then try the direct `/agents/<id>` URL — an agent can load fine by id even when you can't spot it in the list. Harvest names/ids by scraping `[role="row"]` from the grid.
- **Window is tiny (800×600), can't be moved or resized, user complains they can't see it** → three causes, check all: (a) `viewport: {w,h}` locks the window — use `viewport: null`; (b) saved `browser.window_placement` in the cloned `Preferences` overrides `--window-size` **and** `--start-maximized` — delete that key before launch; (c) you sized from `[System.Windows.Forms.Screen]` (logical px) instead of `screen.width` (physical px) and undersized by the display-scale factor. Always log `innerWidth/innerHeight/devicePixelRatio` from inside the page to confirm.
- **`Browser.getWindowForTarget` → `Protocol error: Browser window not found`** → CDP window control is unreliable under `launchPersistentContext`; fix the profile `Preferences` + launch args instead.
- **App "loads", then the next screenshot is a login page with ~200 chars of text** → MSAL redirected back to `/oauth2/v2.0/authorize` for a silent token refresh after your one-shot check passed. Use the **N-consecutive-stable-polls `settle()` loop**, never a fixed `waitForTimeout`.
- **Wrong tenant / blank page / 404 on the environment** → the MCP browser is signed in to a different account than the one that owns the agent. Don't sign in interactively; enumerate the real Edge profiles, find the one whose `account_info[0].email` matches the tenant, clone it, and relaunch with `--profile-directory=<dir>` against the clone root (see "Pick the right profile / tenant").
- **`--profile-directory` picked the wrong profile** → the profile's *display name* and its *folder name* differ (folder `Profile 1` can be shown as "Profile 2"). Always use the folder name from `Get-ChildItem`.
- **Profile lock** → recorder can't launch. Kill stale Edge procs on the profile dir first, and remove any `Singleton*` lock files under the profile dir. Filter by command line so you don't also kill the MCP browser.
- **Recorder looks "stuck" at an early turn** → it's usually block-buffered redirected console output, not a hang. Use synchronous `fs.appendFileSync` logging to `progress.log` and check node/edge process counts to see real progress.
- **Yellow "unsupported command-line flag" banner in-frame** → add `--test-type` (+ `--disable-infobars`).
- **"Restore pages?" bubble in-frame** → patch the profile `Preferences` (`exit_type`→`Normal`, `exited_cleanly`→`true`) before relaunch, and pass `--hide-crash-restore-bubble --disable-session-crashed-bubble`.
- **Account picker / sign-in stalls the run** → auto-click the right account by email/tenant regex (`pickAccountIfNeeded`).
- **Chat input bar half-cut / off-screen** → the recorded frame is the viewport buffer, not the physical window; size the viewport tall enough (e.g. 1920×880 for Copilot Studio) and verify with a pre-record viewport screenshot.
- **Video too long** → cut dead tool-call/timeout gaps into per-beat keep-windows and concat; don't speed-ramp the whole thing.
- **Browser session drops mid-session** → the MCP browser can be relaunched with `browser_navigate`; the Clipchamp project autosaves to the cloud, so reopen it from the home page. If the browser tools are removed entirely mid-task, fall back to the **§2b headless edge-tts + ffmpeg** narration path — same narrated-MP4 deliverable.
- **Enter-to-send concatenation** → use the Send button + confirm the box cleared.
- **TTS block lands in the wrong place** (Clipchamp UI) → it drops at the playhead; set the time input first. Delete a misplaced block and recreate rather than dragging.
- **Black tail** at the end when the last voiceover outlasts the footage → extend the last clip or add a closing still.
- **ffmpeg not on PATH** → install once to `C:\Users\<user>\.copilot\bin` and add it to the User PATH (persists across chats); in the current shell refresh `$env:Path` from Machine+User.
