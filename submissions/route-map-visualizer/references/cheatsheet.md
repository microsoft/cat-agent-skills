# Route Map Visualizer — Cheatsheet

## Minimum viable payload

```json
{
  "kind": "route",
  "stops": [
    { "name": "A", "lat": -33.86, "lon": 151.21 },
    { "name": "B", "lat": -33.90, "lon": 151.18 }
  ]
}
```

For a marker map, use `"kind": "map"` and `"points": [...]`.

---

## Top-level fields

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `kind` | `"map"` \| `"route"` \| `"auto"` | `"auto"` | Route kind |
| `title` | string | `"Route"` / `"Map"` | Chart heading |
| `profile` | `"driving"` \| `"walking"` \| `"cycling"` | `"driving"` | Travel mode |
| `round_trip` | bool | `false` | Return leg |
| `start` | int or string | `0` | Index or name of first stop (route only) |
| `out_prefix` | string | `"route"` / `"map"` | Output filename prefix |

### Connector route data (optional — makes PNG + HTML accurate)

| Field | Type | Notes |
| --- | --- | --- |
| `route_geometry` | `[{lat, lon}]` or GeoJSON LineString | Road polyline from connector |
| `legs` | `[{from, to, distance_m, duration_s, summary}]` | Per-leg breakdown |
| `route_source` | string | Attribution badge (`"azure_maps"`, `"bing_maps"`, …) |
| `total_distance_m` | number | Connector-reported road distance |
| `total_duration_s` | number | Connector-reported travel time |

### Schematic fallback (opt-in)

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `schematic_order` | bool | `false` | Run NN+2opt ordering (straight-line, approximate) |

---

## Per-stop / per-point fields

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Display label |
| `lat`, `lon` | float | Required coordinates |
| `value` | string | Metric shown in popup/legend (e.g. `"24 C"`, `"$1.2M"`) |
| `icon` | string | Icon key (see list below) |
| `color` | string | Hex colour — validated, falls back to icon default |
| `address` | string | Human-readable address |

### Icons

`pin` `sunny` `partly-cloudy` `cloudy` `rain` `storm` `snow` `fog` `wind`
`hot` `cold` `office` `home` `factory` `hospital` `school` `warning` `check`
`star` `shop` `truck`

---

## Optional exports (all off by default)

| Flag | Type | Output |
| --- | --- | --- |
| `html` | bool | Interactive Leaflet + OSM HTML |
| `geojson` | bool | GeoJSON FeatureCollection |
| `kml` | bool | KML (Google Earth) |
| `csv` | bool | Stop list CSV |
| `map_links` | bool | Deep links: Google Maps, Apple Maps, Bing Maps |
| `qr_codes` | bool | QR code sheet for each deep link |

Custom output paths: `html_path`, `geojson_path`, `kml_path`, `csv_path`,
`map_links_path`, `chart_path`, `markdown_path`.

---

## Result dict keys

| Key | Notes |
| --- | --- |
| `chart_path` | Absolute PNG path (always present) |
| `markdown` | Full markdown — paste in chat response |
| `has_road_geometry` | `true` when connector polyline was used |
| `route_source` | Attribution string |
| `distance_label` | Formatted distance string |
| `duration_label` | Formatted duration string |
| `html_path` | When `html: true` |
| `geojson_path` | When `geojson: true` |
| `kml_path` | When `kml: true` |
| `csv_path` | When `csv: true` |
| `map_links_path` | When `map_links: true` |
| `qr_sheet_path` | When `qr_codes: true` |
| `google_maps_url` | Direct Google Maps URL |
| `apple_maps_url` | Direct Apple Maps URL |
| `bing_maps_url` | Direct Bing Maps URL |
| `generated_exports` | Dict of booleans for all output types |
| `warnings` | List of non-fatal issues |

---

## CLI

```bash
cd submissions/route-map-visualizer

# With connector geometry (accurate road route)
python scripts/map_generator.py --payload assets/sample_with_geometry.json

# Schematic (no connector geometry — straight-line fallback)
python scripts/map_generator.py --payload assets/sample_stops_coords.json

# Weather marker map
python scripts/map_generator.py --payload assets/sample_weather_map.json

# Custom prefix and HTML
python scripts/map_generator.py --payload assets/sample_with_geometry.json \
    --out-prefix out/run1 --html
```

---

## Downstream action patterns

### Always include GeoJSON for a Power Automate flow
Add to agent system instructions:
```
When using the route-map-visualizer skill, always include "geojson": true in the payload.
```

### Always include QR codes for mobile users
```
When using the route-map-visualizer skill, include "map_links": true and "qr_codes": true
so users can scan to open the route on their phone.
```

### Pass Azure Maps connector result
```
After calling the Azure Maps route connector, extract:
- ordered stops (with lat/lon)
- route_geometry (polyline points)
- legs (per-leg distance/duration)
- total_distance_m and total_duration_s
Then pass them all to the route-map-visualizer skill.
```

---

## route_geometry formats accepted

```json
// List of {lat, lon} dicts (recommended)
[{"lat": -33.86, "lon": 151.21}, {"lat": -33.88, "lon": 151.18}]

// GeoJSON LineString (also accepted)
{"type": "LineString", "coordinates": [[151.21, -33.86], [151.18, -33.88]]}

// List of [lon, lat] arrays (GeoJSON convention)
[[151.21, -33.86], [151.18, -33.88]]
```
