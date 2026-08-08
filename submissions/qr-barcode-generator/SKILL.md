---
name: qr-barcode-generator
description: >-
  Use this skill whenever the user asks to generate QR codes or barcodes for
  URLs, product codes, record IDs, or any text data — including single items or
  lists. Also use after a tool call (Dataverse, SharePoint, CRM, CSV, connector)
  that returns rows needing scannable codes. Trigger phrases: "generate QR codes
  for these links", "make barcodes for this list", "create a QR sheet for my
  products", "turn these IDs into barcodes", "give me a scannable code for this
  URL", "QR codes for all records".
---

Generates QR codes and 1D barcodes from a payload and returns a labelled PNG
sheet, optional individual PNGs, and optional CSV. Fully offline — uses
`reportlab` + `Pillow`, both pre-installed in the sandbox.

## Steps

**1. Determine kind**

| `kind` | Use when |
| --- | --- |
| `"qr"` | URLs, vCards, deep links, free text, data > 25 chars |
| `"barcode"` | Product codes, IDs, short alphanumeric strings |
| `"auto"` | Default — infers `qr` for URLs or long text, `barcode` otherwise |

**2. Build the items list**

Each item needs:
- `"data"` — the string to encode (required)
- `"label"` — display caption shown below the code (recommended)

Accepted field aliases: `data` / `value` / `url`; `label` / `name`.

For a single item, skip the list — pass `"data"` and `"label"` directly.

**3. Call generate()**

```python
import sys; sys.path.insert(0, "scripts")
from code_generator import generate

result = generate({
    "kind": "auto",               # "qr" | "barcode" | "auto"
    "items": [
        {"label": "Product A",  "data": "https://contoso.com/products/123"},
        {"label": "Product B",  "data": "SKU-456-789"},
    ],
    "title": "Product Codes",
    # Optional — all off by default:
    # "barcode_type": "code128",  # code128|code39|ean13|ean8|upca|i2of5
    # "layout": "grid",           # single|grid|strip|auto
    # "columns": 3,               # grid columns (0 = auto)
    # "size": "medium",           # small|medium|large
    # "error_correction": "M",    # QR only: L|M|Q|H
    # "caption": True,            # label below each code
    # "individual": True,         # save a PNG per code
    # "csv": True,                # export CSV
    # "output_prefix": "/tmp/codes"
})
print(result["markdown"])
```

Key result keys: `sheet_path` (combined PNG, always), `individual_paths` (list,
if `individual: true`), `csv_path` (if `csv: true`), `item_count`, `kind`,
`generated_exports`.

**4. Reply**

Paste `result["markdown"]`. It embeds the sheet image inline and ends with an
**Optional exports** hint listing unused flags. Surface this to the user.

Clarify when helpful:
- **`qr`** — best for URLs, long text, mobile scanning
- **`barcode`** — best for short IDs and product codes; choose `barcode_type`
  to match the scanner (most scanners read Code128 by default)
- **`individual: true`** — useful for downstream flows that attach a code per
  record (Power Automate, SharePoint, Dataverse)
- **`csv: true`** — exports `#, label, data, kind, file` for spreadsheet use
  or as a downstream action input

## Barcode types

| `barcode_type` | Use case | Data format |
| --- | --- | --- |
| `code128` | General alphanumeric (default) | Any ASCII |
| `code39` | Legacy scanners, uppercase only | A-Z, 0-9, `- . $ / + %` |
| `ean13` | Retail products | Exactly 13 digits |
| `ean8` | Small retail items | Exactly 8 digits |
| `upca` | North American retail | Exactly 12 digits |
| `i2of5` | Numeric, even-length | Even number of digits |

## Layout modes

| `layout` | Description |
| --- | --- |
| `"single"` | One code, centred, large |
| `"grid"` | N-column grid (columns auto-calculated or set via `"columns"`) |
| `"strip"` | Single-column vertical list — good for label printing |
| `"auto"` | Default; `single` for 1 item, `grid` for multiple |

## Guardrails

- Never invent data — encode exactly what the user or prior tool provides.
- Never call external APIs from the script.
- Validation errors (e.g. wrong digit count for EAN-13) are shown in the cell,
  not raised as exceptions — the sheet still renders all valid items.
- Invalid `color` or unknown `barcode_type` values silently fall back to
  defaults — do not crash.
