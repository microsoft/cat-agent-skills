# QR & Barcode Generator — Cheatsheet

## Payload reference

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `kind` | string | `"auto"` | `"qr"` \| `"barcode"` \| `"auto"` |
| `barcode_type` | string | `"code128"` | `code128` \| `code39` \| `ean13` \| `ean8` \| `upca` \| `i2of5` |
| `items` | list | — | List of `{"label": …, "data": …}` objects |
| `data` | string | — | Shorthand for single-item — skips `items` list |
| `label` | string | — | Shorthand caption for single-item |
| `layout` | string | `"auto"` | `"single"` \| `"grid"` \| `"strip"` \| `"auto"` |
| `columns` | int | `0` (auto) | Grid columns override |
| `title` | string | `""` | Sheet heading |
| `caption` | bool | `true` | Show label below each code |
| `size` | string | `"medium"` | `"small"` \| `"medium"` \| `"large"` |
| `error_correction` | string | `"M"` | QR only: `L` / `M` / `Q` / `H` |
| `individual` | bool | `false` | Save a PNG per code |
| `csv` | bool | `false` | Export CSV |
| `output_prefix` | string | `"/tmp/codes"` | Path prefix for all output files |

## Item field aliases

`data` also accepted as `value`, `url` · `label` also accepted as `name`

## Result dict keys

| Key | Type | Notes |
| --- | --- | --- |
| `markdown` | str | Inline sheet image + summary table + optional-exports hint |
| `sheet_path` | str | Combined sheet PNG (always present) |
| `individual_paths` | list[str] | Per-item PNGs (when `individual: true`) |
| `csv_path` | str | CSV file path (when `csv: true`) |
| `item_count` | int | Number of items processed |
| `kind` | str | Human-readable kind summary |
| `generated_exports` | dict | `{"individual": bool, "csv": bool}` |
| `error` | str\|None | Top-level error message, if any |

---

## Minimal QR sheet

```python
import sys; sys.path.insert(0, "scripts")
from code_generator import generate

result = generate({
    "title": "Product Links",
    "items": [
        {"label": "Laptop",  "data": "https://shop.com/laptop"},
        {"label": "Monitor", "data": "https://shop.com/monitor"},
        {"label": "Keyboard","data": "https://shop.com/keyboard"},
    ]
})
print(result["markdown"])
# Sheet: result["sheet_path"]
```

## Minimal barcode sheet

```python
result = generate({
    "kind": "barcode",
    "barcode_type": "code128",
    "title": "Warehouse SKUs",
    "items": [
        {"label": "Widget A", "data": "WGT-001"},
        {"label": "Widget B", "data": "WGT-002"},
    ]
})
```

## Single QR code

```python
result = generate({
    "kind": "qr",
    "data":  "https://teams.microsoft.com/l/channel/...",
    "label": "Team Channel",
})
```

## All options enabled

```python
result = generate({
    "kind":             "auto",
    "barcode_type":     "code128",
    "title":            "My Codes",
    "items":            [...],
    "layout":           "grid",
    "columns":          3,
    "size":             "large",
    "error_correction": "H",
    "caption":          True,
    "individual":       True,   # saves {prefix}_001_label.png etc.
    "csv":              True,   # saves {prefix}_codes.csv
    "output_prefix":    "/tmp/my_codes",
})
print(result["sheet_path"])                    # combined sheet
print(result["individual_paths"])              # list of per-item PNGs
print(result["csv_path"])                      # CSV
```

---

## CLI usage

```bash
# QR sheet from a payload file
python scripts/code_generator.py --payload assets/sample_qr.json

# Barcode sheet, large size, individual PNGs + CSV
python scripts/code_generator.py \
  --payload assets/sample_barcode.json \
  --kind barcode --barcode-type code128 \
  --size large --individual --csv \
  --out /tmp/warehouse

# Override layout
python scripts/code_generator.py \
  --payload assets/sample_qr.json \
  --layout strip --no-caption
```

---

## Downstream actions / agent instructions

Lock flags in your agent's system instructions so every call produces the
outputs your workflow needs:

> *"When calling the QR & Barcode Generator, always include:*
> - *`"individual": true` if the result will be attached per-record in Power Automate*
> - *`"csv": true` if the result will be uploaded to SharePoint or Excel*
> - *`"kind": "qr"` when the data contains URLs or long strings*"

### Per-record PNGs in Power Automate

```python
result = generate({..., "individual": True})
for path in result["individual_paths"]:
    # Upload path to SharePoint / attach to Dataverse record
    pass
```

### Attach codes to Dataverse records

```python
# After querying Dataverse for records:
items = [{"label": r["name"], "data": r["url"]} for r in dataverse_records]
result = generate({"items": items, "individual": True, "csv": True})
# result["individual_paths"][i] corresponds to items[i]
```

### QR codes as part of a route map

When the route-map-generator produces deep links, feed them here:

```python
from code_generator import generate as gen_codes

codes = gen_codes({
    "kind": "qr",
    "items": [
        {"label": "Google Maps", "data": result["google_maps_url"]},
        {"label": "Apple Maps",  "data": result["apple_maps_url"]},
        {"label": "Bing Maps",   "data": result["bing_maps_url"]},
    ],
    "title": "Route QR Codes",
})
```

(Or simply use the route-map-generator's built-in `"qr_codes": true` flag.)
