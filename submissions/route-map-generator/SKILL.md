---
name: route-map-generator
description: "Plot locations on a map or optimise multi-stop routes. Use whenever the user asks to map places, show markers with values/icons (weather, CRM records, etc.), optimise visit order for field workers and onsite teams, or export a map as PNG/HTML/GeoJSON/KML/Route Barcodes. Trigger phrases: 'show these on a map', 'weather map for', 'best order to visit', 'optimise this route', 'route to deliver field services'. Also use after knowledge search or another tool call (Dataverse, SharePoint, CRM, connector, APIs, CSV) which returns rows that include latitude/longitude."
---

Generates **marker maps** and **optimised routes** via `scripts/map_generator.py`. Fully offline — no outbound HTTP from Python. Coordinates must be in the payload; HTML loads OSM tiles and OSRM road routes in the user's browser.

## Steps

**1. Choose kind**

| Value | Use when |
| --- | --- |
| `"map"` | plot locations only (no routing) |
| `"route"` | optimise visit order and draw a path |
| `"auto"` | default; infers map unless `round_trip`/`optimize` hints route |

**2. Resolve coordinates** — per point, in order:
1. `lat`/`lon` already present — from the user, a prior knowledge source, a prior tool (Dataverse, Dynamics, CRM, lists, CSV, API response), or a prior agent step. **Never overwrite these.**
2. Alias match in `assets/place_lookup.json`
3. Web-search the place's lat/lon, then add to payload

Never call external geocoding APIs from the script — they fail in the sandbox. Never invent coordinates.

**3. Point fields**

| Field | Notes |
| --- | --- |
| `lat`, `lon` | Required (or place_lookup match) |
| `name` | Display label |
| `value` | Metric — `"24 C"`, `"$1.2M"`, CRM field, etc. |
| `icon` | See icon list below |
| `color` | Hex (optional, validated — invalid values fall back to default) |

**4. Call generate()**

```python
import sys; sys.path.insert(0, "scripts")
from map_generator import generate

result = generate({
    "kind": "route",        # or "map"
    "title": "My route",
    "stops": [              # also: "points" or "locations"
        {"name": "A", "lat": -33.86, "lon": 151.21},
        {"name": "B", "lat": -33.87, "lon": 151.20},
    ],
    "round_trip": True,
    # Optional exports (all off by default — add what you need):
    # "html": True       "csv": True         "geojson": True
    # "kml": True        "map_links": True   "qr_codes": True
})
print(result["markdown"])   # includes inline PNG + optional-exports hint
```

Key result keys: `chart_path` (PNG, always), `html_path`, `csv_path`, `geojson_path`, `kml_path`, `map_links_path`, `qr_sheet_path`, `google_maps_url`, `apple_maps_url`, `bing_maps_url`, `generated_exports` (dict of booleans).

**5. Reply** — paste `result["markdown"]`. It always ends with an **Optional exports** hint listing every unused flag with a description. Surface this to the user. Clarify:
- **PNG** = straight-line sketch (approximate)
- **HTML** = real road route (OSRM in browser; needs internet). Always add `html: true` for route requests.
- **QR codes** — enable with `map_links: true` + `qr_codes: true`. Embed `result["qr_sheet_path"]` inline.
- **Downstream automations** — users can lock flags in their agent's system instructions so every call includes them (e.g. `"geojson": true` for Power Automate, `"qr_codes": true` for mobile). See `references/cheatsheet.md`.

## Icons

`pin` `sunny` `partly-cloudy` `cloudy` `rain` `storm` `snow` `fog` `wind` `hot` `cold` `office` `home` `factory` `hospital` `school` `warning` `check` `star` `shop` `truck`

## Guardrails

- Never overwrite `lat`/`lon` from user or prior tools.
- Never call external geocoding/routing APIs from the Python script.
- Never invent coordinates — ask the user or web-search.

## Bundled files

- `scripts/map_generator.py` — engine (`generate`)
- `assets/place_lookup.json` — Sydney-area aliases
- `references/cheatsheet.md` — full payload reference, all CLI flags
