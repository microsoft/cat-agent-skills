# QR Code Kit

**Turn a plain-language request into a real, scannable QR code — fully offline, from one small JSON spec.**

You say what you want ("a QR to join our WiFi", "a QR for this invoice"); the skill fills a structured spec, encodes it with a bundled zero-dependency engine, and hands back a PNG (or SVG/EPS/PDF).

## Why it exists

A language model can't reliably make a QR code on its own. Free-hand, it draws QR-ish images that won't scan (encoding needs Reed–Solomon error-correction and masking). Even with a code interpreter, a locked sandbox like Copilot Studio **can't `pip install`** a proven library and has no network — so the model hand-rolls an untested encoder and silently emits a dead image, and mis-formats the fiddly payloads (WiFi escaping, vCard, iCalendar, SEPA).

This skill removes both failures: it **vendors a pinned, zero-dependency engine** ([segno](https://github.com/heuer/segno)) so the same tested encoder runs offline every time, plus a **validation layer** so escaping, required fields, capacity, and timezones are done deterministically — not guessed.

## What it does

- **Encodes 10 types** to their correct standard format: `url`, `text`, `email`, `tel`, `sms`, `wifi`, `vcard`, `geo`, `event`, `epc` (SEPA payment).
- **Builds the strings models get wrong** — WiFi escaping, vCard fields, iCalendar events (timezones normalized to UTC), strict EPC/SEPA format.
- **Runs fully offline** — no `pip`, no network; engine vendored and pinned, results reproducible.
- **Outputs PNG/SVG/EPS/PDF** with control over error-correction (`L`/`M`/`Q`/`H`), scale, quiet-zone, and colors.
- **Fails loudly, never silently** — a missing SSID, bad coordinates, or a broken EPC rule returns a clear error, not a dead QR.

## Example

> **"Make a QR to join our office WiFi — network `Acme Guest`, password `welcome123`, WPA."**

The agent fills one spec and runs the script:

```bash
python scripts/qr_generate.py --json '{"type":"wifi","ssid":"Acme Guest","password":"welcome123","security":"WPA"}' --out qr.png
```

```json
{ "ok": true, "type": "wifi", "file": "/…/qr.png", "designator": "3-M", "modules": 29, "engine": "segno (BSD-3, vendored)" }
```

The model fills the spec; the pinned script does the exact encoding. `file` is the absolute path to the saved image (the host picks the working dir); the agent hands that file back to the user. It triggers on natural "make a QR for…" asks and deliberately stays out of decoding existing QRs, non-QR barcodes, and dynamic/hosted QR services. See [`SKILL.md`](./SKILL.md) for the full field list and options.

## Honest boundaries

- **Generates, doesn't scan.** It creates QR codes; it does not read/decode an existing QR from an image.
- **Static encoding, not a service.** No URL shortening, dynamic/hosted QR, or scan analytics, and it doesn't verify a URL/IBAN/phone is real or safe. Garbage in, faithfully-encoded garbage out.
- **Doesn't re-scan its own output.** Verifying that needs a compiled scanner (zbar/OpenCV) that can't install in a no-`pip` sandbox. Correctness rests on segno's ISO/IEC 18004 conformance (1500+ tests), this skill's payload validation, and an ASCII preview you can eyeball. (Every type *was* scan-verified with OpenCV during development — that check just isn't shipped.)
- **Density grows with data.** Long payloads make dense codes; prefer pointing the QR at a short URL.

> 💡 **Tip:** Test before you trust — I do my best but I'm human, so try any skill and give it a once-over before relying on it (PRs welcome if you spot a fix and/or an enhancement). Solid habit for anything you pull off the internet. 🙂

## When to use something else

- Need **dynamic QR codes, editable destinations, or scan analytics**? Use a hosted QR platform — this skill is deliberately static and offline.
- Need to **decode/read** a QR from an image? Use a scanner/reader library or app; this only generates.
- Already have your own **QR library or service** and don't need the offline/no-`pip` guarantee or the validated payload builders? A direct call is fine.

## Credits & license

Encoding by [**segno**](https://github.com/heuer/segno) (Lars Heuer), **BSD-3-Clause**, vendored under `assets/vendor/segno/` with its license file included and Lars Heuer's copyright notices retained (the year range aligned to the author's current LICENSE). The payload-builder, validation, and agent integration are this skill's original contribution.

## Files

- `SKILL.md` — agent-facing trigger, type-selection, and result-handling instructions.
- `scripts/qr_generate.py` — the payload builder + validation layer that drives the engine.
- `assets/vendor/segno/` — the vendored segno engine (BSD-3) and its license.
