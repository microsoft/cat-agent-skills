# Route Map Generator

A generic **map + route** skill for Copilot Studio.

- **Maps** — plot locations with optional values and icons (weather, sites, stores, CRM records)
- **Routes** — optimise multi-stop visit order and draw a path (route for field workers and teams)

Runs **fully offline** in the Python sandbox. Coordinates come from the user, a **prior tool** (Dataverse, CRM, SharePoint, connectors), or **agent web search**.

## What you get

| Export | Flag | Notes |
| --- | --- | --- |
| PNG map | *(always)* | Inline in markdown; straight-line sketch |
| Interactive HTML | `html: true` | OSM tiles + real road route (OSRM, browser-side) |
| CSV | `csv: true` | Stops/locations table |
| GeoJSON | `geojson: true` | For QGIS, Power BI, ArcGIS |
| KML | `kml: true` | For Google Earth, My Maps |
| Map deep links | `map_links: true` | Google Maps, Apple Maps, Bing Maps |
| QR codes | `qr_codes: true` | Scannable PNG sheet; requires `map_links: true` |

**All exports except PNG are off by default.** Every response includes an "Optional exports" hint listing unused flags.

### PNG vs HTML routes

| Output | Path style |
| --- | --- |
| **PNG** | Straight lines — quick sketch + approximate distance |
| **HTML** | Real road route (OSRM, followed when file is opened in a browser) |

OSRM falls back to straight-line if offline.

## Two kinds

| Kind | When | Output |
| --- | --- | --- |
| `map` | "Show these cities", weather, site list | Markers + values/icons, no path |
| `route` | "Optimise visit order", deliveries | Ordered stops + path |

## Point fields

| Field | Notes |
| --- | --- |
| `lat` / `lon` | Always preferred — from user, prior tools, or web search |
| `name` | Display label |
| `value` | Metric shown on map (`"24 C"`, `"$1.2M"`) |
| `icon` | `sunny`, `rain`, `office`, `pin`, … (see icons below) |
| `color` | Hex colour — validated; invalid values fall back to default |

## Icons

`pin` `sunny` `partly-cloudy` `cloudy` `rain` `storm` `snow` `fog` `wind` `hot` `cold` `office` `home` `factory` `hospital` `school` `warning` `check` `star` `shop` `truck`

## Usage examples

**Weather map**
> Show Sydney, Bondi, Manly, and Parramatta with today's temperatures and weather icons. HTML too.

**After Dataverse**
> Get open service accounts from Dataverse, map them, optimise a visit route, and give me GeoJSON.

**QR codes for mobile**
> Optimise this delivery route and give me QR codes so drivers can open it on their phones.

## Dependencies

- `matplotlib` — PNG rendering (required)
- `reportlab` + `Pillow` — QR code export (both pre-installed in the sandbox; no extra install needed)
- Browser network — HTML loads Leaflet/OSM tiles and OSRM road routes client-side (no Python outbound calls)
