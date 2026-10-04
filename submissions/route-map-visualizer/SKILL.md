---
name: route-map-visualizer
description: >-
  Use this skill to visualize routes and locations on a map — especially after
  an upstream tool call (routing connector, Azure Maps, Bing Maps connector,
  HERE, Mapbox, Dataverse, CRM, SharePoint, or any connector that returns
  coordinates) has returned ordered stops, coordinates, distances, or road
  geometry. Produces PNG, interactive HTML, GeoJSON, KML, deep links, and QR
  codes. Also use for marker maps (weather, CRM data, site lists) and for any
  request to "show these on a map", "map these locations", or "visualize this
  route". DO NOT use this skill to compute routing — call a routing connector
  first, then pass the result here for visualization.
---

Visualizes pre-ordered routes and location maps via `scripts/map_generator.py`.
Fully offline Python engine — no outbound HTTP from Python. Road geometry
rendered directly when provided by a connector; OSRM used browser-side as a
fallback when it is not.

## Steps

**1. Choose kind**

| Value | Use when |
| --- | --- |
| `"map"` | Plot locations only — no path (weather, CRM records, site lists) |
| `"route"` | Ordered stops + path |
| `"auto"` | Default — infers `map` unless `stops` key or `round_trip` hint |

**2. Resolve coordinates** — per point, in order:
1. `lat`/`lon` already present — from user, connector result, Dataverse, CRM, CSV, etc. **Never overwrite.**
2. Alias match in `assets/place_lookup.json`
3. Web-search the place's lat/lon, then add to payload

Never call external geocoding APIs from the script. Never invent coordinates.

**3. Pass connector route data (when available)**

If an upstream connector (Azure Maps, Bing Maps, etc.) returned routing data,
pass it directly — the visualizer will use it for accurate distances and the
actual road polyline in PNG and HTML:

| Field | Source | Effect |
| --- | --- | --- |
| `route_geometry` | Connector road polyline | Draw actual road path in PNG + HTML |
| `legs` | Connector leg breakdown | Show per-leg distance/time table |
| `route_source` | e.g. `"azure_maps"` | Attribution badge on map and outputs |
| `total_distance_m` | Connector total distance | Accurate distance in header + exports |
| `total_duration_s` | Connector total time | Accurate time in header + exports |

Without these, the PNG uses straight lines (labeled **schematic**) and the
HTML calls OSRM browser-side for road routing.

**4. Point fields**

| Field | Notes |
| --- | --- |
| `lat`, `lon` | Required (or place_lookup match) |
| `name` | Display label |
| `value` | Metric — `"24 C"`, `"$1.2M"`, CRM field, etc. |
| `icon` | See icon list below |
| `color` | Hex (validated — invalid values fall back to default) |
| `order` | Optional sequence number (connector-assigned) |

**5. Call generate()**

```python
import sys; sys.path.insert(0, "scripts")
from map_generator import generate

# Minimal — stops in provided order, schematic PNG, OSRM HTML
result = generate({
    "kind": "route",
    "title": "Delivery run",
    "stops": [
        {"name": "Depot",  "lat": -33.86, "lon": 151.21},
        {"name": "Stop A", "lat": -33.90, "lon": 151.18},
        {"name": "Stop B", "lat": -33.88, "lon": 151.15},
    ],
    # Optional exports (all off by default):
    # "html": True   "csv": True   "geojson": True   "kml": True
    # "map_links": True   "qr_codes": True
})

# With connector road data — produces accurate PNG + no OSRM needed
result = generate({
    "kind": "route",
    "title": "Delivery run — Azure Maps",
    "stops": [...],
    "route_geometry": [              # connector road polyline
        {"lat": -33.860, "lon": 151.210},
        {"lat": -33.865, "lon": 151.208},
        ...
    ],
    "legs": [                        # per-leg breakdown
        {"from": "Depot", "to": "Stop A", "distance_m": 5200,
         "duration_s": 420, "summary": "via Parramatta Rd"},
        {"from": "Stop A", "to": "Stop B", "distance_m": 3100,
         "duration_s": 280, "summary": "via Church St"},
    ],
    "route_source": "azure_maps",
    "total_distance_m": 8300,
    "total_duration_s": 700,
    "html": True,
})
print(result["markdown"])
```

Key result keys: `chart_path` (PNG, always), `html_path`, `csv_path`,
`geojson_path`, `kml_path`, `map_links_path`, `qr_sheet_path`,
`google_maps_url`, `apple_maps_url`, `bing_maps_url`, `has_road_geometry`,
`route_source`, `generated_exports`.

**6. Reply** — paste `result["markdown"]`. It always ends with an **Optional
exports** hint. Clarify:
- **PNG** = road route when `route_geometry` provided, else straight-line schematic
- **HTML** = connector polyline embedded (no OSRM) when geometry provided, else OSRM browser-side
- **`schematic_order: true`** — opt-in offline stop ordering (NN + 2-opt, straight-line estimate); always prefer a connector for real road order

## Icons

`pin` `sunny` `partly-cloudy` `cloudy` `rain` `storm` `snow` `fog` `wind`
`hot` `cold` `office` `home` `factory` `hospital` `school` `warning` `check`
`star` `shop` `truck`

## Guardrails

- Never overwrite `lat`/`lon` from user or prior tools.
- Never call external geocoding/routing APIs from the Python script.
- Never invent coordinates — ask the user or web-search.
- Never reorder stops unless `"schematic_order": true` is explicitly set.

## Bundled files

- `scripts/map_generator.py` — engine (`generate`)
- `assets/place_lookup.json` — place aliases
- `references/cheatsheet.md` — full payload reference + CLI flags
