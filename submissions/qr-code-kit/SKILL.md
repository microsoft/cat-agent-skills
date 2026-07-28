---
name: qr-code-kit
description: Use this skill whenever the user asks to generate, create, or make a QR code — for a URL/link, plain text, WiFi network credentials, a contact/business card (vCard), a pre-filled email, a phone number, an SMS, a map location, a calendar event, or a SEPA/EPC bank payment. Build the correct JSON spec and run scripts/qr_generate.py BEFORE claiming a QR image was produced; never hand-draw or improvise QR matrices yourself. Do NOT use this skill to read, scan, or decode an existing QR code from an image, to generate non-QR barcodes (e.g. EAN/UPC/Code-128/PDF417), or to set up dynamic, hosted, or scan-tracking QR services.
---

# QR Code Kit

Generate **scannable, standard QR codes fully offline** from a single JSON spec.
You (the model) are good at turning a natural-language request into structured
fields; you are unreliable at the actual QR encoding and at the fussy payload
string formats (WiFi escaping, vCard, iCalendar events, SEPA payments). This
skill splits the work: **you fill a small JSON spec, the pinned script does the
exact, deterministic encoding** with a bundled, zero-dependency engine (segno).

## How to use it

Run the script with one JSON object describing what to encode:

```
python scripts/qr_generate.py --json '{"type":"url","data":"https://example.com"}' --out qr.png
```

- Pass the spec inline via `--json '<json>'`, from a file via `--spec spec.json`,
  or piped on stdin via `--json -`.
- `--out <path>` sets the output file (or put `output.out` inside the spec).
- The script prints a **JSON result** to stdout and exits `0` on success, `1` on
  error. Always read that result before telling the user the QR is ready.

### Never do the encoding yourself
Do **not** attempt to draw a QR matrix, output ASCII "QR art", or write your own
encoder — QR encoding needs Reed–Solomon error correction and data masking and
will silently produce an unscannable image if improvised. Always call the script.

## Choosing the `type`

Map the user's intent to exactly one type:

| User wants… | `type` |
|---|---|
| a link / website / "open this page" | `url` |
| arbitrary text / a note / a code | `text` |
| join a WiFi network | `wifi` |
| a contact / business card | `vcard` |
| pre-filled email | `email` |
| dial a phone number | `tel` |
| pre-filled text message | `sms` |
| a map pin / coordinates | `geo` |
| add a calendar event | `event` |
| a SEPA/European bank transfer | `epc` |

If the user just says "make a QR for `<something>`" and it looks like a web
address, use `url` (a bare domain gets `https://` prepended automatically);
otherwise use `text`.

## Spec fields by type

All specs are one JSON object with `"type"` plus these fields:

- **url** — `data` (the link).
- **text** — `data` (any string).
- **email** — `to` (required); optional `cc`, `bcc`, `subject`, `body`.
- **tel** — `number` (required).
- **sms** — `number` (required); optional `message`.
- **wifi** — `ssid` (required); optional `password`, `security` (`WPA` | `WEP` |
  `nopass`), `hidden` (bool). Special characters in SSID/password are escaped for you.
- **vcard** — `name` (required; `"Last;First"` splits into surname/forename);
  optional `displayname`, `org`, `title`, `email`, `phone`, `cellphone`, `url`,
  `memo`, `nickname`, `birthday` (`YYYY-MM-DD`), `street`, `city`, `region`,
  `zipcode`, `country`.
- **geo** — `lat`, `lng` (decimal degrees).
- **event** — `summary` (required), `start` (required, ISO 8601 e.g.
  `2026-08-01T18:00` or `2026-08-01`); optional `end`, `location`, `description`.
  A time with a UTC offset (e.g. `2026-08-01T18:00+02:00`) is honored and
  normalized to UTC; a time without one is left as a floating local time.
- **epc** — `name`, `iban`, `amount` (EUR) all required; exactly **one** of
  `text` (≤140 chars) or `reference`; optional `bic`. Always uses ECC level M per
  the EPC standard.

### Output options (optional `"output"` object)
```json
{ "type": "url", "data": "https://example.com",
  "output": { "out": "qr.png", "format": "png", "scale": 10, "border": 4, "error": "M", "dark": "#000", "light": "#fff" } }
```
- `format`: `png` (default), `svg`, `eps`, or `pdf`. All render offline with no extra libraries.
- `scale`: pixels per module (default 10). `border`: quiet-zone modules (default 4 — keep ≥4 for reliable scanning).
- `error`: `L` | `M` | `Q` | `H` (default `M`; the engine may auto-raise it when capacity allows). Use `Q` or `H` for codes that will be printed, on curved/low-quality surfaces, or may get dirty.
- `dark` / `light`: colors. Keep strong contrast (dark on light); do not invert.

## Examples

```jsonc
{ "type": "wifi", "ssid": "Café Net", "password": "p@ss;word", "security": "WPA" }
{ "type": "vcard", "name": "Lovelace;Ada", "org": "Analytical Engines", "email": "ada@x.com", "phone": "+1-555-0100", "url": "https://ada.dev" }
{ "type": "event", "summary": "Product launch", "start": "2026-08-01T18:00", "end": "2026-08-01T19:30", "location": "HQ, Floor 3" }
{ "type": "epc", "name": "ACME GmbH", "iban": "DE89370400440532013000", "amount": 12.50, "text": "Invoice 42" }
```

## Reading the result

Success looks like:
```json
{ "ok": true, "type": "wifi", "payload": "WIFI:T:WPA;S:Café Net;P:p@ss\\;word;;",
  "file": "/.../qr.png", "format": "png", "version": 4, "error": "Q",
  "designator": "4-Q", "modules": 33, "image_pixels": {"width": 410, "height": 410},
  "engine": "segno (BSD-3, vendored)", "preview": "…block-character preview…" }
```
- Tell the user where the file is (`file`).
- If a `warning` field is present (e.g. a defaulted URL scheme or assumed WiFi
  security), relay it — do not hide it.
- The `payload` is the exact encoded string; you may show it for verification.
- `preview` is a text rendering for a quick eyeball check (omitted for large codes).

On failure: `{ "ok": false, "error": "…" }` — report the error verbatim and ask
the user for the missing/invalid field. Do **not** pretend a QR was created.

## Guardrails / honest boundaries

- This skill **generates** QR codes; it does **not read/scan** existing QR images.
- Output is a static QR encoding whatever you pass. It is **not** a URL shortener,
  a hosted/dynamic QR, or a link-tracking/analytics service, and it does not
  validate that a URL, IBAN, phone number, or email actually exists or is safe.
- Larger data ⇒ denser codes. For long payloads prefer a short URL as the target.
- The encoding engine is **segno** (BSD-3-Clause, © Lars Heuer), vendored under
  `assets/vendor/segno` and used unmodified; its license ships with it.
