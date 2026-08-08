# Route Map Generator — Cheat Sheet

```python
from map_generator import generate
result = generate({ ... })
print(result["markdown"])
```

Sandbox: **no external APIs** from Python. Resolve lat/lon via user input,
**prior tool results** (Dataverse, CRM, lists, connectors), `place_lookup.json`,
or **agent web search**, then pass them in.

HTML routes: when opened in a browser, the page calls the public **OSRM** demo
API and draws a **road-following** polyline (real streets).

- **PNG** → straight lines between stops (approximate)
- **HTML** → actual road path (falls back to straight lines if OSRM is offline)

## Payload

| Field | Default | Notes |
| --- | --- | --- |
| `kind` | `auto` | `map` \| `route` \| `auto` |
| `points` / `stops` / `locations` | — | list of place objects |
| `round_trip` / `profile` / `optimize` | — | route options |

### Optional exports — all opt-in

| Flag | Default | What it produces |
| --- | --- | --- |
| `"html": true` | off | Interactive OSM map; real road-following route (OSRM, browser-side) |
| `"csv": true` | off | CSV table of all stops/locations |
| `"geojson": true` | off | GeoJSON for QGIS, Power BI, ArcGIS, or any GIS tool |
| `"kml": true` | off | KML for Google Earth / My Maps |
| `"map_links": true` | off | Deep links to open route in Google Maps, Apple Maps, Bing Maps |
| `"google_maps"` / `"apple_maps"` / `"bing_maps"` | off | Individual provider deep link only |
| `"qr_codes": true` | off | QR code PNGs per provider + combined sheet (requires `map_links: true`) |

> **PNG is always generated.** Everything else is off by default — add flags to your payload to enable them.

### Point object

| Field | Notes |
| --- | --- |
| `lat`, `lon` | **always win** when set (prefer these) |
| `name`, `location`, `address` | labels; optional place_lookup match |
| `value`, `value_num` | optional metrics |
| `icon`, `color` | marker style |

### Icons

`pin`, `sunny`, `partly-cloudy`, `cloudy`, `rain`, `storm`, `snow`, `fog`,
`wind`, `hot`, `cold`, `office`, `home`, `factory`, `hospital`, `school`,
`warning`, `check`, `star`, `shop`, `truck`

## CLI

```bash
# Default — PNG only (no optional exports)
python scripts/map_generator.py --payload assets/sample_weather_map.json

# Add whatever exports you need
python scripts/map_generator.py --payload assets/sample_stops.json \
    --kind route --html --csv --geojson --kml

# Route + deep links + QR codes
python scripts/map_generator.py --payload assets/sample_stops.json \
    --kind route --html --map-links --qr-codes
```

### Map deep links + QR codes

```python
result = generate({
    "kind": "route",
    "stops": [...],   # with lat/lon
    "round_trip": True,
    "map_links": True,   # or google_maps / apple_maps / bing_maps
    "qr_codes": True,    # QR PNG per provider + combined sheet
})
print(result["google_maps_url"])
print(result["apple_maps_url"])
print(result["bing_maps_url"])
print(result["qr_sheet_path"])    # combined PNG — embed with ![QR codes](path)
# result["qr_paths"] has individual paths: google_maps, apple_maps, bing_maps
```

**Dependency:** built-in — uses `reportlab` + `Pillow` (both pre-installed in the sandbox)

### Downstream actions / agent instructions

Add flags permanently to an agent's system instructions so every map call
automatically includes the exports your workflow needs:

> *"When calling the route map generator, always include:*
> - *`"html": true` for the interactive OSM map*
> - *`"geojson": true` to load results in Power BI*
> - *`"qr_codes": true` so field staff can scan on their phones"*

`result["generated_exports"]` — dict of booleans showing which exports were
produced (useful for conditional downstream logic).

```bash
# Route + deep links + QR codes (CLI)
python scripts/map_generator.py --payload assets/sample_stops.json --kind route --html --map-links --qr-codes
```
