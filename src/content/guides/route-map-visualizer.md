# Route Map Visualizer

A Copilot Studio skill that **visualizes pre-ordered routes and location
collections** as richly formatted maps — PNG for chat, interactive HTML for
the browser, plus optional GeoJSON/KML exports, deep links, and QR codes.

## When to use this skill

Use it **after** an upstream connector call returns coordinates, road geometry,
or leg details:

- An Azure Maps / Bing Maps / HERE / Mapbox connector has returned the ordered
  stops, distances, and a road polyline → pass them all here for visualization.
- A Dataverse / CRM / SharePoint query has returned a list of locations with
  lat/lon → plot them on a marker map.
- The agent web-searched a set of addresses and resolved their coordinates →
  visualize the result.

> **Design principle:** This skill does **not** perform routing optimization.
> It trusts the caller to supply the correct stop order and, optionally, the
> road geometry. Offline straight-line rendering is retained as an explicitly
> schematic fallback.

---

## Features

| Feature | Default | Enable |
| --- | --- | --- |
| PNG map (always) | ✅ | — |
| Interactive HTML (Leaflet + OSM) | off | `"html": true` |
| GeoJSON export | off | `"geojson": true` |
| KML export | off | `"kml": true` |
| Deep links (Google Maps / Apple Maps / Bing Maps) | off | `"map_links": true` |
| QR codes for deep links | off | `"qr_codes": true` |
| CSV stop list | off | `"csv": true` |

Road geometry from a connector makes PNG and HTML more accurate. Without it,
PNG uses straight lines (labeled **schematic**) and HTML calls OSRM
browser-side.

---

## Payload

### Minimal — route (stops in provided order)

```json
{
  "kind": "route",
  "title": "Delivery run",
  "stops": [
    { "name": "Depot",  "lat": -33.8600, "lon": 151.2100 },
    { "name": "Stop A", "lat": -33.9021, "lon": 151.1814 },
    { "name": "Stop B", "lat": -33.8825, "lon": 151.1490 }
  ]
}
```

### With connector road data

```json
{
  "kind": "route",
  "title": "Delivery run — Azure Maps",
  "stops": [
    { "name": "Depot",  "lat": -33.860, "lon": 151.210, "icon": "home" },
    { "name": "Stop A", "lat": -33.902, "lon": 151.181, "icon": "shop" },
    { "name": "Stop B", "lat": -33.882, "lon": 151.149, "icon": "shop" }
  ],
  "route_geometry": [
    { "lat": -33.860, "lon": 151.210 },
    { "lat": -33.864, "lon": 151.207 },
    { "lat": -33.872, "lon": 151.195 },
    { "lat": -33.882, "lon": 151.181 },
    { "lat": -33.902, "lon": 151.181 }
  ],
  "legs": [
    { "from": "Depot",  "to": "Stop A", "distance_m": 5200, "duration_s": 420, "summary": "via Parramatta Rd" },
    { "from": "Stop A", "to": "Stop B", "distance_m": 3100, "duration_s": 280, "summary": "via Church St" }
  ],
  "route_source": "azure_maps",
  "total_distance_m": 8300,
  "total_duration_s": 700,
  "profile": "driving",
  "html": true,
  "map_links": true
}
```

### Marker map (weather / CRM data / site list)

```json
{
  "kind": "map",
  "title": "Field site weather",
  "points": [
    { "name": "Sydney CBD",    "lat": -33.8688, "lon": 151.2093, "value": "28 C", "icon": "sunny" },
    { "name": "Parramatta",    "lat": -33.8150, "lon": 151.0020, "value": "31 C", "icon": "hot" },
    { "name": "Bondi Beach",   "lat": -33.8915, "lon": 151.2767, "value": "24 C", "icon": "partly-cloudy" },
    { "name": "Manly",         "lat": -33.7969, "lon": 151.2870, "value": "22 C", "icon": "cloudy" }
  ]
}
```

### Schematic ordering (opt-in offline fallback)

Add `"schematic_order": true` to let the script sort stops with a
nearest-neighbour + 2-opt heuristic (uses straight-line distances — suitable
only when a routing connector is unavailable):

```json
{
  "kind": "route",
  "title": "Estimated visit order",
  "stops": [...],
  "schematic_order": true,
  "round_trip": true
}
```

---

## Payload field reference

### Top-level

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `kind` | `"map"` \| `"route"` \| `"auto"` | `"auto"` | Map kind |
| `title` | string | `"Map"` / `"Route"` | Chart title |
| `profile` | `"driving"` \| `"walking"` \| `"cycling"` | `"driving"` | Travel mode |
| `round_trip` | bool | `false` | Add a return leg |
| `route_geometry` | `[{lat, lon}]` | — | Connector road polyline |
| `legs` | array | — | Connector per-leg breakdown |
| `route_source` | string | — | Attribution (`"azure_maps"`, `"bing_maps"`, etc.) |
| `total_distance_m` | number | — | Road distance in metres |
| `total_duration_s` | number | — | Travel time in seconds |
| `schematic_order` | bool | `false` | Opt-in offline stop ordering |
| `html` | bool | `false` | Write interactive HTML |
| `geojson` | bool | `false` | Write GeoJSON |
| `kml` | bool | `false` | Write KML |
| `csv` | bool | `false` | Write CSV |
| `map_links` | bool | `false` | Generate deep links |
| `qr_codes` | bool | `false` | QR code sheet for deep links |

### Per stop / point

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Display label |
| `lat`, `lon` | float | Required (or place_lookup alias match) |
| `value` | string | Metric — shown in popup + legend |
| `icon` | string | `pin`, `sunny`, `office`, `shop`, `truck`, … |
| `color` | string | Hex colour (validated, default = icon default) |
| `address` | string | Human-readable address (shown in sidebar) |

---

## Result keys

| Key | Type | Notes |
| --- | --- | --- |
| `chart_path` | string | Absolute path to PNG |
| `markdown` | string | Paste this in the chat response |
| `has_road_geometry` | bool | `true` when connector geometry was used |
| `route_source` | string | Attribution from payload |
| `distance_label` | string | e.g. `"8.3 km"` |
| `duration_label` | string | e.g. `"11 min"` |
| `html_path` | string | If `html: true` |
| `geojson_path` | string | If `geojson: true` |
| `kml_path` | string | If `kml: true` |
| `csv_path` | string | If `csv: true` |
| `map_links_path` | string | If `map_links: true` |
| `qr_sheet_path` | string | If `qr_codes: true` |
| `google_maps_url` | string | Direct Google Maps route URL |
| `apple_maps_url` | string | Direct Apple Maps route URL |
| `bing_maps_url` | string | Direct Bing Maps route URL |
| `generated_exports` | dict | Flags for all outputs actually produced |

---

## Dependencies

```
matplotlib>=3.8.0       # PNG map
Pillow>=10.0.0          # QR code rasterization
reportlab>=3.6.0        # QR encoder (qrencoder module)
```

---

## CLI (for local testing)

```bash
cd submissions/route-map-visualizer
python scripts/map_generator.py --payload assets/sample_with_geometry.json
python scripts/map_generator.py --payload assets/sample_stops_coords.json --out-prefix out/test
```
