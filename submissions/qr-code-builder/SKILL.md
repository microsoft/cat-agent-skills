---
name: qr-code-builder
description: |
  Use this skill whenever the user asks to "make a QR code", "create a QR code",
  "QR code for this link/website", "QR code with my logo", "branded QR code" or
  "Wi-Fi QR code". Guided walkthrough that builds a scannable QR code (PNG, SVG,
  PDF, JPG, WEBP) with a bundled Python script. Only the web address is required;
  body shapes, corner-eye styles, outer frames, brand colors, a logo and a caption
  are optional. Also makes Wi-Fi, contact card, email, SMS, phone, map, event and
  bulk codes on request. Do NOT use for reading, scanning or decoding an existing
  QR code, or for barcodes other than QR codes. A QR code with a logo is handled
  here, not by general image generation.
---

# QR Code Builder

Make a QR code with as few questions as possible. **The only required input is the web address** (or
the details of a type the user explicitly asked for); every look-and-feel choice is optional and never blocks.

## When NOT to use
| Request | Do instead |
|---|---|
| Read, scan or decode an existing QR code | Out of scope (this skill only makes codes) |
| Other barcodes (Code 128, EAN/UPC, Data Matrix, PDF417, Aztec) | Out of scope |
| General illustrations, logos or artwork with no QR code | Use an image-generation tool instead |
| A flyer, poster, page or slide that contains a QR code | Make the QR code here, then use a document or presentation tool for the layout |
| Rebranding documents or decks | Out of scope — "brand colors" here means the QR code's colors only |
| An interactive QR-generator app | Out of scope (this skill delivers files) |

## Engine rules
| Rule | Detail |
|---|---|
| Skill folder | `<skill-dir>` = the folder this SKILL.md was loaded from. Engine: `scripts/make_qr.py`; style guide: `assets/qr-style-guide.png` (both relative to `<skill-dir>`). If unknown, search `**/qr-code-builder/scripts/make_qr.py` and use its grandparent. Use absolute paths in commands |
| Libraries | Pillow + one QR encoder (ReportLab, `qrcode` or `segno`, first found). **Never** `pip install`; never write your own encoder. The engine reads **CSV only** for bulk (XLSX: see Bulk) |
| No separate check | The generation run reports `encoder` and returns `missing_encoder` / `missing_pillow` itself. Run `python '<skill-dir>/scripts/make_qr.py' --check` ONLY after one of those errors (or another encoder/Pillow error), or on the Customize path to read `vector_pdf` before answering a PDF question |
| One command | `python '<skill-dir>/scripts/make_qr.py' … --scratch '<scratch>' --file-name '<slug>-qr'` in ONE call (the engine creates `<scratch>`; no `mkdir`). No extra verification calls — the JSON is the check |
| **Safe commands (security)** | Never put a user-derived value — URL, caption, frame text, color, logo path, file name, Wi-Fi / contact / event fields, CSV column names — raw or inside double quotes into a shell string: `$(…)`, backticks and `$VAR` still run inside `"…"`. **Prefer an argument list** when the host runs Python: `subprocess.run([sys.executable, script, "--url", url, …])`, one list item per value, never `shell=True`. **In a shell**, wrap every user value in single quotes and write each `'` inside it as `'\''` (e.g. `Bob's` → `'Bob'\''s'`). Quote `<skill-dir>`, `<scratch>` and file paths the same way. Fixed option names (`png`, `fluid`, `small`, `logo`) are safe as-is |
| Fresh folder every run | `<scratch>` = `<qr-root>/<slug>-run<N>` (Platform notes). Use a **NEW** folder for EVERY run and rerun — N = 1, 2, 3 …; never reuse one, never write straight into the delivery location. The engine creates it, refuses a non-empty one (`scratch_not_empty` → next N) and refuses anything outside the working folder (`bad_scratch`). **Never delete files or folders** to make room |
| Safe file names | `--file-name '<slug>-qr'`, where `<slug>` is the web address's host (`contoso.com`), the code type (`wifi`, `contact`, `event`, `text`), or for bulk `links` (bulk file names come from the name column + row number). Never pass a path, folder or a file name the user typed. The engine reduces the name to letters, digits, `.`, `-`, `_` (it reports the final `file_name`), and checks every file stays inside `<scratch>` — quoting alone doesn't stop `../` tricks |
| Images | Standard: never view the PNG. Customize: view the final PNG ONCE, only if the look changed (shape, eyes, frame, logo, colors, caption); after a rerun view only the rerun. The style guide is for the user — don't inspect it |

## Platform notes
| Topic | Copilot Cowork | Copilot Studio / other code-interpreter hosts |
|---|---|---|
| Questions | `core-AskUserQuestion` — one card per step; multi-select for Step 3b | ONE chat message per question, numbered options, recommended first; wait for the reply |
| Finding uploads (logo, CSV) | `Glob input/**/*` and `Glob grounding/**/*` | Files attached in this conversation / the host's upload folder |
| Scratch folder | `<qr-root>` = `working/qr`; `<scratch>` = `working/qr/<slug>-run<N>` | `<qr-root>` = `qr_out` (inside the working folder); `<scratch>` = `qr_out/<slug>-run<N>` |
| Showing the style guide | `mkdir -p working/qr/guide && cp '<skill-dir>/assets/qr-style-guide.png' working/qr/guide/`, then ONE `host-CopyArtifact(surface="output", source="working/qr/guide/qr-style-guide.png", destination="qr-style-guide.png", overwrite=true)` | Show it inline, or attach it |
| Delivering files | Deliver EXACTLY the JSON `file_names` (batch: every result's `file_names`), from `<scratch>`. One file: ONE `host-CopyArtifact(surface="output", source="<scratch>/<file>", destination="<file>")`. Several: ONE `host-CopyArtifact(surface="output", source="<scratch>", destination="<slug>-qr", recursive=true)` — only when the JSON says `folder_clean: true`; otherwise copy the listed files one by one. Check `copied` equals the number of listed files. Retry the same call on "source not visible yet"; confirm with ONE `Glob output/**/*` | Return each listed file as an attachment. Only ONE file per response and several made → zip exactly the listed files into `<scratch>.zip` (beside `<scratch>`, paths single-quoted) in the generating command |
| Seeing images | The image viewer shows the agent only; the user sees delivered files | The delivered attachment is the preview |
| Typical libraries | ReportLab: vector PDF, no scan verifier | Varies; PDF may be 300-dpi raster; may have a scan verifier |

## Walkthrough
A standard code takes exactly two questions; Customize adds the menu, ticked follow-ups and a confirm.

### Step 1 — Web address (REQUIRED)
- **Always ask, even when the request contains one:** "Use contoso.com" / "Enter a different address"; none
  given → ask. **Never invent an address**; the script adds `https://`.
- **Empty or cancelled answer → stop:** "No problem — I've stopped; nothing was created." Generate nothing.
- **Other code types** only when explicitly requested: collect that type's real details instead (see Code
  types). Never invent a password, phone number, email or contact detail.

### Step 2 — Standard or Customize (ONE gate question)
- **Standard QR code for https://contoso.com: black squares, PNG (recommended)**
- **Customize the look**

Standard or empty → Step 4 immediately with defaults (PNG, 1000 px, black on white, square); no extra confirm.
If the request already names a customization ("with my logo", "as a PDF", "in brown"), skip this question: go
straight to Customize with those items pre-ticked and still show them in 3b.

### Step 3 — Customize (only if chosen)
- **3a. Show the style guide** (see Platform notes) and say: "Here's the style guide — sections A-E, ★ marks
  the standard choice." Sections: A Body shape (8) · B Eye frame (5) · C Eye center (5) · D Outer frame (4) ·
  E Brand color, caption & logo size. Never rebuild or hand-draw samples.
- **3b. ONE multi-select — "What would you like to change?"** Shape & corners · Brand colors · Logo in the
  middle · Caption · Outer frame · File format & size. (No multi-select tool: numbered list, reply with numbers.)
  Empty → Standard.
- **3c. Follow-ups ONLY for ticked items** — one question per item (one card per group is fine), standard
  option first marked "(recommended)". Empty → the standard choice; continue. **Exception:** a value the
  request already states goes first as the recommended option instead — e.g. "brown" + a logo → "Match my
  logo's color (recommended)", then "Brown #5C3A21", then "Black on white"; "as a PDF" → PDF first.
- **3d. Confirm** a one-line summary, e.g. "contoso.com · Fluid body, Leaf eyes · brown #5C3A21 · small logo ·
  caption 'Visit Contoso' · PNG 1000 px" → "Create it (recommended)" / "Change something". Empty → create.

#### Customize options and flags
| Item | Options (standard first) | Flags |
|---|---|---|
| Body shape (A) | 1 Square (recommended — most reliable), 2 Rounded, 3 Dots, 4 Diamond, 5 Fluid, 6 Vertical bars, 7 Horizontal bars, 8 Mosaic | `--style square\|rounded\|dots\|diamond\|fluid\|vertical-bars\|horizontal-bars\|small-squares` (Mosaic = `small-squares`) |
| Eye frame (B) | 1 Square (recommended), 2 Rounded, 3 Extra rounded, 4 Circle, 5 Leaf | `--eye-frame square\|rounded\|extra-rounded\|circle\|leaf` |
| Eye center (C) | 1 Square (recommended), 2 Rounded, 3 Circle, 4 Diamond, 5 Leaf | `--eye-center square\|rounded\|circle\|diamond\|leaf` |
| Brand colors | Black on white (recommended) / Match my logo's color (only when a logo is chosen) / Enter a hex (e.g. `#5C3A21`). Optional separate eye color. Always a dark code on a light background | `--fg HEX\|logo --bg HEX` · `--eye-color HEX\|logo` · `--bg transparent` (PNG/WEBP/SVG only) |
| Logo | "Use [filename]" per uploaded image / "I'll attach one" (nothing arrives or skipped → no logo). Size: Medium (recommended) / Small (subtle) / Large. Say it switches on error correction H automatically. PNG/JPG best; SVG logos only if self-contained (no links to web addresses or other files — those are refused) | `--logo 'PATH' --logo-size small\|medium\|large` (0.15 / 0.22 / 0.28 of width; overrides `--logo-scale`) |
| Caption | Free text under the code, e.g. "Visit Contoso" (plain Latin text is safest) | `--caption '...'` (single-quoted — see Safe commands) |
| Outer frame (D) | None (recommended) / Box / Rounded box / Banner. Banner text: "SCAN ME" (default) / caption text / other. Optional frame color (default = code color) | `--frame none\|box\|rounded-box\|banner` · `--frame-text '...'` · `--frame-color HEX\|logo` |
| Format & size | PNG (recommended) / SVG / PDF / JPG / WEBP, several allowed; SVG/PDF stay plain square. Size 1000 px (recommended) or custom (exact; frame/caption add space). PDF 216 pt (3 in). Too small for the content → `size_too_small` with the minimum | `--format png,svg,pdf` · `--size 1000` · `--pdf-size 216` |

`logo` as a color value needs `--logo` (else error `no_logo`).

#### Code types (only when explicitly requested)
| Type | Ask for | Flags |
|---|---|---|
| Web link (default) | Web address | `--type url --url` |
| Plain text | The text | `--type text --text` |
| Wi-Fi | Network name, password, security: WPA (recommended — covers WPA/WPA2/WPA3) / WEP / open (no password), hidden? Work/school (enterprise) Wi-Fi isn't supported | `--type wifi --ssid --password --auth WPA\|WEP\|nopass [--hidden]` (WPA2/WPA3 are accepted as WPA) |
| Contact card | Name; optional org, title, phone, email, website, address | `--type vcard --name --org --title --phone --email --url --address` |
| Email | Address; optional subject, body | `--type email --email --subject --body` |
| Text message | Phone; optional message | `--type sms --phone --body` |
| Phone call | Phone number | `--type phone --phone` |
| Map location | Latitude, longitude (geocode only a user-given address; confirm) | `--type geo --lat --lon` |
| Calendar event | Title, start, end (`20261015T190000`, or `20261015` for all-day — then the end is the day AFTER the last day), optional location. End must be after start | `--type event --summary --start --end --location` |
| Bulk | Uploaded CSV (or XLSX, converted first — below); which column holds the data and which the file name | `--batch FILE.csv --data-column COL --name-column COL --scratch DIR` |

Bulk: find the upload (ask if none); show the headers, ask for the two columns. Bare domains get `https://`, and every web link (bare or `http(s)://`) gets the same
checks as a single link; cells starting with `mailto:`, `tel:`, `smsto:`, `geo:`, `WIFI:` or `BEGIN:` are encoded as given; a bad
or empty row doesn't stop the batch and is reported (never skipped). Every file name ends with its row number
(e.g. `Alpha_001.png`), so names never collide. Non-UTF-8 CSVs (Excel's classic "CSV (Comma delimited)") are read
as Windows text with a warning.

**XLSX uploads** — the engine is CSV-only, so convert first, and ONLY if a reader is importable. Run this ONE command
(paths passed as arguments, single-quoted); it never installs anything:
```bash
mkdir -p '<qr-root>' && python - '<upload>.xlsx' '<qr-root>/<slug>-sheet-run<N>.csv' <<'PY'
import sys, csv
src, dst = sys.argv[1], sys.argv[2]
try:
    import openpyxl
    rows = list(openpyxl.load_workbook(src, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
except ImportError:
    try:
        import pandas as pd
        rows = pd.read_excel(src, sheet_name=0, header=None, dtype=str).fillna("").values.tolist()
    except ImportError:
        print("NO_XLSX_READER"); sys.exit(0)
    except Exception:
        print("NO_XLSX_READER"); sys.exit(0)  # pandas present but no Excel engine
except Exception:
    print("XLSX_UNREADABLE"); sys.exit(0)
with open(dst, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([["" if v is None else str(v) for v in r] for r in rows])
print("CONVERTED")
PY
```
| Result | Do |
|---|---|
| `CONVERTED` | Continue with `<qr-root>/<slug>-sheet-run<N>.csv` — kept OUTSIDE `<scratch>`, which must stay empty for the engine (first sheet only — say so if the workbook has several) |
| `NO_XLSX_READER` | Stop the bulk flow; don't guess or hand-parse. Say: "I can't open Excel files here. In Excel choose **File › Save As › CSV UTF-8 (Comma delimited)** and upload that file." |
| `XLSX_UNREADABLE` | Same message, noting the file couldn't be opened (it may be damaged or password-protected) |

Older `.xls`, `.ods` or `.numbers` files: ask for a CSV UTF-8 export directly (the engine returns `not_csv` for them).

### Step 4 — Generate, read JSON, deliver
1. **Run** in ONE command, into a NEW `<scratch>` (Engine rules → Fresh folder every run; a rerun uses the next
   `-run<N>`). `--file-name` is a plain base name without extension (dots like `contoso.com-qr` are kept).
   Pass every user value safely (Engine rules → Safe commands): single quotes in a shell, `'` → `'\''`:
   ```bash
   python '<skill-dir>/scripts/make_qr.py' --type url --url 'contoso.com' --format png \
     --scratch 'working/qr/contoso.com-run1' --file-name 'contoso.com-qr'
   python '<skill-dir>/scripts/make_qr.py' --url 'contoso.com' --style fluid \
     --eye-frame leaf --eye-center leaf --frame banner --frame-text 'SCAN ME' --logo '<logo>.png' \
     --logo-size small --fg logo --caption 'Visit Contoso'\''s open house' --format png,svg,pdf \
     --scratch 'working/qr/contoso.com-run2' --file-name 'contoso.com-qr'
   ```
   Where the host runs Python directly, use an argument list instead (no shell, no quoting needed):
   ```python
   import subprocess, sys
   r = subprocess.run([sys.executable, "<skill-dir>/scripts/make_qr.py", "--url", url, "--caption", caption,
                       "--format", "png", "--scratch", scratch, "--file-name", slug + "-qr"],
                      capture_output=True, text=True)
   ```
2. **Read the JSON** printed on stdout:

   | Field | Meaning / what to do |
   |---|---|
   | `files` / `file_names` | Paths written / their plain names — deliver EXACTLY these, nothing else |
   | `file_name`, `folder_clean` | Final (safe) base name; `true` = `<scratch>` holds only this run's files. `false` → deliver the listed files one by one (never the folder) |
   | `payload` | What the code contains; show it for Wi-Fi/vCard. A Wi-Fi password is already masked (`P:********`) — show as-is |
   | `warnings` | Explain each in plain words (list below) |
   | `readback_check` | `modules_obscured_pct` vs `error_correction_budget_pct` → `verdict` good / risky / likely to fail (corner eyes excluded). Risky or worse → offer `--logo-size small` and/or `--style square`, rerun |
   | `scan_verified` | `null` = no QR reader installed (estimate only). Else `{engine, decoded, matches_content}`; `false` = failure → offer square / smaller logo / more contrast, rerun |
   | Batch | `{"rows", "count", "failed", "results", "folder_clean"}` (`rows` = every data row; `count` + `failed` = `rows`); failed rows carry `row`, `name`, `error`, `message` (`missing_data` = empty cell) → report, offer to fix those rows |

3. **Errors** (exit code 2, `{"error": code, "message": "..."}`): relay the message in plain words, re-ask ONLY
   that item, rerun.

   | Code | Action |
   |---|---|
   | `invalid_url` / `missing_url` | Re-ask the web address |
   | `missing_field` / `invalid_field` | Re-ask ONLY the field the message names (e.g. Wi-Fi password unless the network is open; a supported Wi-Fi security type; a real event date/time like `20261015T190000` with the end after the start; latitude/longitude numbers) |
   | `bad_column` / `batch_not_found` | Show the spreadsheet's columns (listed in the message) and re-ask / ask for the file again |
   | `not_csv` / `bad_csv` | Ask for a "CSV UTF-8 (Comma delimited)" export (for `.xlsx`, try the Bulk conversion first) |
   | `bad_color` | Re-ask that color (offer black or a hex) |
   | `logo_not_found` / `logo_unreadable` | Re-ask the logo, or continue without one (a fully transparent logo can't supply a color — offer a hex) |
   | `logo_svg` | Ask for a PNG or JPG logo |
   | `bad_format` | Re-ask the format (png, svg, pdf, jpg, webp) |
   | `no_logo` | Use black, say so |
   | `too_long` | Ask for a shorter link or less text |
   | `size_too_small` | The chosen size can't fit this much content — rerun with the minimum size the message gives (or shorter content); say so |
   | `bad_option` | An option is out of range or invalid (the message names it) — fix that value; if it came from the user, re-ask it |
   | `cannot_write` | The scratch folder isn't writable — rerun ONCE with the next `-run<N>`; if it fails again, say so |
   | `scratch_not_empty` | The folder was already used — rerun with the next `-run<N>` (never empty or delete the old one) |
   | `bad_scratch` | The folder path is unsafe or outside the working folder — rerun with `<qr-root>/<slug>-run<N>` exactly as in Platform notes |
   | `too_large` | Rerun with a smaller `--size` |
   | `internal_error` | Say something went wrong; rerun ONCE with the standard look. If it fails again, stop and tell the user (never show the `detail` field) |
   | `missing_encoder` / `missing_pillow` | "This environment can't make QR codes (a required image or QR library is missing)." Stop; ask nothing more (optionally one `--check` to confirm) |

   **Warnings to explain** (batch: a top-level `warnings` list may also note the CSV encoding): low contrast (code, eyes, frame); inverted light-on-dark; margin under 4 squares;
   Wi-Fi password length looks wrong / password ignored for an open network; emoji/CJK text may show as boxes; caption shown smaller on several lines / banner text too long (offer to shorten); error correction raised for the logo;
   "fg taken from logo: #…" (name it); "The SVG/PDF leaves out: …" (name each listed option; offer PNG for the styled version); PDF is a 300-dpi image (fine for print); failed
   scan test. Tiny caption text in the preview = no TrueType font here; say so.
4. **Preview (Customize only):** follow the Images rule. If only SVG/PDF was chosen, add a PNG preview run in
   the SAME command into its own new folder `<scratch>-preview` (never inside `<scratch>`) and view that.
5. **Deliver** every final file (not previews) per Platform notes. If a name is already taken in the delivery
   location, pick a new name and say so.
6. **Test-scan reminder:** always say "Scan it with your phone camera before you print or share it."

## Output
- Chat: 3-6 bullets — what the code contains, exact file names, the readability verdict in plain words,
  warnings explained, and the test-scan reminder.
- Files: `<file_name>.<ext>` per chosen format (bulk: one per row per format) — exactly the JSON `file_names`.

## Guardrails
- Never generate before Step 1 is answered; always show what will be made before generating (Step 2 option /
  Step 3d).
- Never invent a URL, Wi-Fi password, phone number, email or contact detail — ask.
- Keep a dark code on a light background; if the user insists on light-on-dark, warn that many scanners fail.
- Never claim a code "scans" or is "verified" unless `scan_verified.matches_content` is true — otherwise call
  the readability result an estimate.
- The payload already masks Wi-Fi passwords; never echo the `--password` value in chat, and never put
  passwords or other secrets in captions, frame text or file names.
- Never silently overwrite a user's file in the delivery location.
- Files go ONLY into a fresh `<qr-root>/<slug>-run<N>` folder — never a path or file name taken from the user, an
  upload or a spreadsheet. Deliver only the files the JSON lists. Never delete files or folders.
  If the user asks for a particular location or file name, use the safe name anyway and say: "I saved it as
  `<file>` in its own folder — I can't write to locations you type, but you can rename it after downloading."
- Never interpolate user values raw or in double quotes into a shell command — use an argument list, or single
  quotes with `'` written as `'\''` (Engine rules → Safe commands). This applies to every value and every command.
- Never `pip install`. On a script error, relay the message in plain words — no tracebacks, and never
  hand-draw a QR code.
