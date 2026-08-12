# QR & Barcode Generator

Generate QR codes and 1D barcodes from any data — URLs, product IDs, record
links, or free text. Pass a single item or a list; get back a labelled PNG
sheet, optional individual PNGs per code, and an optional CSV.

Runs **fully offline** in the Python sandbox. No extra `pip install` — uses
`reportlab` and `Pillow`, both pre-installed.

## Sample output

**QR code sheet** — 6 product page URLs, auto-detected as QR:

![QR sheet sample](assets/sample_qr_sheet.png)

**Barcode sheet** — 8 warehouse SKUs, Code128:

![Barcode sheet sample](assets/sample_barcode_sheet.png)

## Real-world examples

These are everyday situations where people ask an agent for codes — no
special setup required beyond the data you already have.

### Front desk — visitor Wi-Fi QR

> Print a QR for our guest Wi-Fi so visitors don’t have to type the password.

Encode a Wi-Fi string or a short landing page URL as a single large QR. Stick
it on the reception desk or meeting-room door.

```json
{
  "kind": "qr",
  "size": "large",
  "label": "Guest Wi-Fi",
  "data": "WIFI:T:WPA;S:Contoso-Guest;P:Welcome2026;;"
}
```

### Field service — work-order barcodes for technicians

> We have 12 open work orders from Dataverse. Make Code128 barcodes so techs
> can scan them on the van tablet instead of typing WO numbers.

Pull the work-order IDs from Dataverse / CRM, then generate a strip for the
clipboard or a grid for the van printer.

```json
{
  "kind": "barcode",
  "barcode_type": "code128",
  "layout": "strip",
  "title": "Today’s work orders",
  "items": [
    { "label": "WO-10421 — HVAC filter", "data": "WO-10421" },
    { "label": "WO-10422 — Pump seal",   "data": "WO-10422" },
    { "label": "WO-10423 — Door sensor", "data": "WO-10423" }
  ]
}
```

### Retail shelf — EAN-13 labels for a product launch

> New snack line launches Monday. Generate EAN-13 barcodes for these three
> SKUs so packing can print shelf labels tonight.

```json
{
  "kind": "barcode",
  "barcode_type": "ean13",
  "title": "Shelf labels — CrunchBars",
  "items": [
    { "label": "CrunchBar Dark 45g",  "data": "9300675031234" },
    { "label": "CrunchBar Milk 45g",  "data": "9300675031241" },
    { "label": "CrunchBar Nut 45g",   "data": "9300675031258" }
  ]
}
```

### Event team — registration / feedback QR on badges

> Summit starts Friday. Give me a big registration QR for the badge printer,
> and a second QR that opens the post-session feedback form.

```json
{
  "kind": "qr",
  "size": "large",
  "error_correction": "H",
  "title": "Summit 2026 badges",
  "items": [
    { "label": "Register", "data": "https://events.contoso.com/summit2026/register" },
    { "label": "Feedback", "data": "https://forms.office.com/r/summit2026-feedback" }
  ]
}
```

### IT asset tracking — laptop / monitor tags

> Export our asset list from the CMDB and make barcodes for asset tags we can
> stick on each laptop before the refresh.

```json
{
  "kind": "barcode",
  "barcode_type": "code128",
  "layout": "grid",
  "title": "Q3 laptop refresh — asset tags",
  "individual": true,
  "csv": true,
  "items": [
    { "label": "Anna Chen — MacBook",     "data": "AST-88421" },
    { "label": "Sam Okonkwo — Dell 5440", "data": "AST-88422" },
    { "label": "Priya Shah — ThinkPad",   "data": "AST-88423" }
  ]
}
```

`individual: true` gives one PNG per asset for the label printer;
`csv: true` maps each tag back to the person / asset ID for audit.

### Restaurant / café — table QR for digital menus

> Put a QR on each table that opens our lunch menu. Tables 1–8.

```json
{
  "kind": "qr",
  "title": "Table menu QR codes",
  "items": [
    { "label": "Table 1", "data": "https://menu.contoso.cafe/lunch?table=1" },
    { "label": "Table 2", "data": "https://menu.contoso.cafe/lunch?table=2" },
    { "label": "Table 3", "data": "https://menu.contoso.cafe/lunch?table=3" },
    { "label": "Table 4", "data": "https://menu.contoso.cafe/lunch?table=4" }
  ]
}
```

### Clinic / lab — specimen IDs for the morning run

> Generate barcodes for today’s specimen list so phlebotomy can scan into the LIS.

```json
{
  "kind": "barcode",
  "barcode_type": "code128",
  "layout": "strip",
  "title": "Specimen labels — 12 Aug",
  "items": [
    { "label": "Patient A — CBC",  "data": "SPC-20260812-001" },
    { "label": "Patient B — Lipid","data": "SPC-20260812-002" },
    { "label": "Patient C — HbA1c","data": "SPC-20260812-003" }
  ]
}
```

### Facilities — QR that opens a “report an issue” Form per room

> Each meeting room should have a QR that opens a Microsoft Form pre-filled
> with the room name.

```json
{
  "kind": "qr",
  "title": "Report a facilities issue",
  "items": [
    { "label": "Boardroom A", "data": "https://forms.office.com/r/facilities?room=BoardroomA" },
    { "label": "Boardroom B", "data": "https://forms.office.com/r/facilities?room=BoardroomB" },
    { "label": "Training 3",  "data": "https://forms.office.com/r/facilities?room=Training3" }
  ]
}
```

## What you get

| Output | Flag | Notes |
| --- | --- | --- |
| PNG sheet | *(always)* | Labelled grid — inline in markdown |
| Individual PNGs | `individual: true` | One PNG per code — useful for per-record workflows |
| CSV | `csv: true` | `#, label, data, kind, file_path` |

**All exports except the sheet are off by default.** Every response includes an
"Optional exports" hint listing unused flags.

## Two code kinds

| `kind` | Best for | Auto-detected when |
| --- | --- | --- |
| `qr` | URLs, long text, mobile scanning | data starts with `http(s)://` or is > 25 chars |
| `barcode` | Short IDs, product codes, legacy scanners | short alphanumeric data |
| `auto` | Mixed lists | *(default)* — resolved per item |

## Barcode types (`barcode_type`)

| Value | Symbology | Data rules |
| --- | --- | --- |
| `code128` | Code 128 (default) | Any ASCII |
| `code39` | Code 39 | A-Z, 0-9, `- . $ / + %` |
| `ean13` | EAN-13 | Exactly **13 digits** |
| `ean8` | EAN-8 | Exactly **8 digits** |
| `upca` | UPC-A | Exactly **12 digits** |
| `i2of5` | Interleaved 2-of-5 | Even number of digits |

## Layout options

| `layout` | Description |
| --- | --- |
| `auto` | `single` for 1 item, `grid` for multiple *(default)* |
| `single` | One code, centred |
| `grid` | N-column grid; `columns` sets width (auto if omitted) |
| `strip` | Single-column vertical list — good for label sheets |

## Before you start

`reportlab` and `Pillow` must be available in the sandbox.  Both are
pre-installed — nothing extra to install.

## How to use it

### 1. Single QR code from a URL

Just ask:
> Give me a QR code for https://teams.microsoft.com/l/channel/19%3Ameeting_abc123

The agent passes:
```json
{ "kind": "qr", "data": "https://teams.microsoft.com/l/channel/19%3Ameeting_abc123", "label": "Team Channel" }
```
You get a single centred QR code PNG, ready to paste or share.

---

### 2. QR code sheet for a list of links

> Generate QR codes for our Sydney, Melbourne, and Brisbane office check-in pages.

```json
{
  "kind": "qr",
  "title": "Office Check-in QR Codes",
  "items": [
    { "label": "Sydney",    "data": "https://checkin.contoso.com/sydney" },
    { "label": "Melbourne", "data": "https://checkin.contoso.com/melbourne" },
    { "label": "Brisbane",  "data": "https://checkin.contoso.com/brisbane" }
  ]
}
```
Result: a 3-column labelled grid sheet, inline in the chat.

---

### 3. Warehouse barcode sheet (Code128)

> Make Code128 barcodes for these SKUs: WGT-001, WGT-002, WGT-003, WGT-004. Print-ready strip layout.

```json
{
  "kind": "barcode",
  "barcode_type": "code128",
  "layout": "strip",
  "title": "Warehouse Pick List",
  "items": [
    { "label": "Widget A", "data": "WGT-001" },
    { "label": "Widget B", "data": "WGT-002" },
    { "label": "Widget C", "data": "WGT-003" },
    { "label": "Widget D", "data": "WGT-004" }
  ]
}
```
Result: a single-column vertical strip with human-readable text below each bar.

---

### 4. Retail EAN-13 barcode sheet

> Generate EAN-13 barcodes for product codes 5901234123457, 4006381333931, 5000112637939.

```json
{
  "kind": "barcode",
  "barcode_type": "ean13",
  "title": "Retail Product Barcodes",
  "items": [
    { "label": "Sparkling Water 500ml", "data": "5901234123457" },
    { "label": "AA Batteries x4",       "data": "4006381333931" },
    { "label": "Sticky Notes 100pk",    "data": "5000112637939" }
  ]
}
```
⚠ EAN-13 requires exactly 13 digits — the agent validates each item and shows a
red placeholder for any that don't match, so the rest of the sheet still renders.

---

### 5. Mixed list — URLs and short codes together

> I have a mix of product page URLs and short internal IDs. Generate codes for all of them.

```json
{
  "kind": "auto",
  "title": "Product Codes",
  "items": [
    { "label": "Laptop Pro",  "data": "https://shop.contoso.com/laptop-pro" },
    { "label": "Mouse",       "data": "https://shop.contoso.com/mouse" },
    { "label": "Spare Part A","data": "SP-4421" },
    { "label": "Spare Part B","data": "SP-4422" }
  ]
}
```
`auto` kind detects URLs → QR codes, short IDs → Code128 barcodes, all on one sheet.

---

### 6. After a Dataverse / CRM query — individual PNGs for Power Automate

> Get all open service accounts from Dataverse, generate a QR code for each record URL, and give me individual PNGs so I can attach them in Power Automate.

```json
{
  "kind": "qr",
  "title": "Service Account QR Codes",
  "individual": true,
  "csv": true,
  "items": [
    { "label": "Contoso Ltd",   "data": "https://org.crm.dynamics.com/main.aspx?id=a1b2c3" },
    { "label": "Fabrikam Inc",  "data": "https://org.crm.dynamics.com/main.aspx?id=d4e5f6" },
    { "label": "Northwind",     "data": "https://org.crm.dynamics.com/main.aspx?id=g7h8i9" }
  ]
}
```
Result:
- `sheet_path` — combined PNG for the chat
- `individual_paths[0]` → `001_contoso_ltd.png`, `[1]` → `002_fabrikam_inc.png`, etc.
- `csv_path` — CSV mapping each label, URL, and file path (ready to feed a Power Automate loop)

---

### 7. Event / meeting QR code — large size, high error correction

> Give me a large, high-quality QR code for our event registration link, suitable for printing on a banner.

```json
{
  "kind": "qr",
  "data": "https://events.contoso.com/register/summit2026",
  "label": "Summit 2026 — Register",
  "size": "large",
  "error_correction": "H"
}
```
`H` level error correction means the code is still scannable even if up to 30% of
it is obscured (by a logo, fold, or wear).

## Good to know

- Validation errors (e.g. wrong digit count for EAN-13) are shown in the cell
  as a red placeholder — the sheet still renders all valid items.
- `auto` kind is resolved **per item** — a mixed list of URLs and short codes
  will produce QR codes for the URLs and barcodes for the short codes.
- For downstream Power Automate flows, add `"individual": true` to get a file
  path per record, then attach or upload each PNG in a loop.
- Lock flags in your agent's system instructions (e.g. `"individual": true`) so
  every call automatically includes the exports your workflow needs.
