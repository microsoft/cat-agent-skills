#!/usr/bin/env python3
"""Route + location map visualizer — renders connector-provided route data.

Accepts pre-ordered stops with coordinates, plus optional road geometry and
leg details from an upstream routing connector (Azure Maps, Bing Maps, HERE,
Mapbox, etc.). Produces PNG, interactive HTML, GeoJSON, KML, deep links, and
QR codes.

Design: this skill does NOT perform routing optimization.  The caller is
responsible for stop order.  When connector road geometry is present the PNG
and HTML render the actual road polyline; without it the PNG falls back to
straight-line schematic rendering and the HTML calls OSRM browser-side.

Location resolution (per point), in order:
1. ``lat``/``lon`` already in the payload — always used as-is (never overwritten).
2. Bundled ``assets/place_lookup.json`` alias match.

If neither works the **agent** must obtain coordinates via a connector or web
search and add ``lat``/``lon`` to the payload — the sandbox cannot call
external geocoders.

Supports two kinds:

* ``map``   — marker map (weather, CRM data, site lists)
* ``route`` — ordered stops + path (connector-provided road polyline or schematic)

Usage::

    from map_generator import generate

    # Minimal — stops in provided order, schematic PNG, OSRM HTML fallback
    result = generate({
        "kind": "route",
        "title": "Delivery run",
        "stops": [
            {"name": "Depot",  "lat": -33.860, "lon": 151.210},
            {"name": "Stop A", "lat": -33.902, "lon": 151.181},
        ],
    })

    # With connector road data — accurate PNG + HTML (no OSRM needed)
    result = generate({
        "kind": "route",
        "title": "Delivery run — Azure Maps",
        "stops": [...],
        "route_geometry": [{"lat": -33.860, "lon": 151.210}, ...],
        "legs": [{"from": "Depot", "to": "Stop A",
                  "distance_m": 5200, "duration_s": 420}],
        "route_source": "azure_maps",
        "total_distance_m": 5200,
        "total_duration_s": 420,
        "html": True,
    })
    print(result["markdown"])
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import textwrap
import xml.etree.ElementTree as ET
from typing import Any, Mapping, Optional, Sequence
from urllib.parse import urlencode

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "matplotlib is required for map PNG output. "
        "Install with: pip install matplotlib"
    ) from exc

import re as _re

_HEX_COLOUR_RE = _re.compile(r'^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$')


def _safe_colour(raw: Optional[str], fallback: str = "#0078d4") -> str:
    """Return raw if it is a valid 3- or 6-digit hex colour, else fallback."""
    if raw and _HEX_COLOUR_RE.match(raw):
        return raw
    return fallback


PROFILES = ("driving", "walking", "cycling")

# Schematic speeds / road factors — used ONLY when connector route data is absent.
_SPEED_MPS   = {"driving": 35_000 / 3600, "walking": 5_000 / 3600, "cycling": 15_000 / 3600}
_ROAD_FACTOR = {"driving": 1.35, "walking": 1.15, "cycling": 1.25}

# Icon catalogue — emoji for HTML/PNG, short label + colour + display name.
ICONS: dict[str, dict[str, str]] = {
    "pin": {"emoji": "📍", "label": "PIN", "name": "Pin", "color": "#0078d4"},
    "sunny": {"emoji": "☀️", "label": "SUN", "name": "Sunny", "color": "#f9a825"},
    "partly-cloudy": {"emoji": "⛅", "label": "PC", "name": "Partly cloudy", "color": "#607d8b"},
    "cloudy": {"emoji": "☁️", "label": "CLD", "name": "Cloudy", "color": "#546e7a"},
    "rain": {"emoji": "🌧️", "label": "RAIN", "name": "Rain", "color": "#1565c0"},
    "storm": {"emoji": "⛈️", "label": "STM", "name": "Storm", "color": "#4527a0"},
    "snow": {"emoji": "❄️", "label": "SNOW", "name": "Snow", "color": "#0288d1"},
    "fog": {"emoji": "🌫️", "label": "FOG", "name": "Fog", "color": "#757575"},
    "wind": {"emoji": "💨", "label": "WIND", "name": "Windy", "color": "#00897b"},
    "hot": {"emoji": "🔥", "label": "HOT", "name": "Hot", "color": "#e53935"},
    "cold": {"emoji": "🥶", "label": "COLD", "name": "Cold", "color": "#0277bd"},
    "office": {"emoji": "🏢", "label": "OFF", "name": "Office", "color": "#5c6bc0"},
    "home": {"emoji": "🏠", "label": "HOME", "name": "Home", "color": "#43a047"},
    "factory": {"emoji": "🏭", "label": "FAC", "name": "Factory", "color": "#6d4c41"},
    "hospital": {"emoji": "🏥", "label": "HOS", "name": "Hospital", "color": "#e53935"},
    "school": {"emoji": "🏫", "label": "SCH", "name": "School", "color": "#ef6c00"},
    "warning": {"emoji": "⚠️", "label": "WRN", "name": "Warning", "color": "#f9a825"},
    "check": {"emoji": "✅", "label": "OK", "name": "OK", "color": "#2e7d32"},
    "star": {"emoji": "⭐", "label": "★", "name": "Star", "color": "#fbc02d"},
    "shop": {"emoji": "🛒", "label": "SHOP", "name": "Shop", "color": "#00838f"},
    "truck": {"emoji": "🚚", "label": "TRK", "name": "Truck", "color": "#546e7a"},
}


def icon_meta(icon: Optional[str]) -> dict[str, str]:
    key = (icon or "pin").strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "sun": "sunny",
        "clear": "sunny",
        "cloud": "cloudy",
        "clouds": "cloudy",
        "partlycloudy": "partly-cloudy",
        "partly": "partly-cloudy",
        "shower": "rain",
        "showers": "rain",
        "thunder": "storm",
        "thunderstorm": "storm",
        "mist": "fog",
        "haze": "fog",
        "default": "pin",
        "marker": "pin",
        "location": "pin",
    }
    key = aliases.get(key, key)
    meta = dict(ICONS.get(key, ICONS["pin"]))
    meta.setdefault("name", meta.get("label", key))
    return meta


def _emoji_fontproperties():
    """Prefer an emoji-capable font when available (Windows / macOS / Noto)."""
    from matplotlib import font_manager

    candidates = (
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Apple Color Emoji",
        "Noto Color Emoji",
        "Noto Emoji",
        "DejaVu Sans",
    )
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return font_manager.FontProperties(family=name)
    return font_manager.FontProperties()


def _spread_label_offsets(
    lons: Sequence[float],
    lats: Sequence[float],
) -> list[tuple[float, float]]:
    """Place labels away from neighbours; fan out dense clusters."""
    n = len(lons)
    if n == 0:
        return []
    if n == 1:
        return [(28.0, 16.0)]

    lon_span = max(max(lons) - min(lons), 1e-6)
    lat_span = max(max(lats) - min(lats), 1e-6)
    cx = sum(lons) / n
    cy = sum(lats) / n

    # Local density = count of neighbours within ~12% of map span.
    density = [0] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = math.hypot(
                (lons[i] - lons[j]) / lon_span,
                (lats[i] - lats[j]) / lat_span,
            )
            if d < 0.12:
                density[i] += 1

    offsets: list[list[float]] = []
    for i in range(n):
        # Prefer direction away from map centroid and nearest neighbour.
        vx = (lons[i] - cx) / lon_span
        vy = (lats[i] - cy) / lat_span
        nearest_d = 1e9
        for j in range(n):
            if i == j:
                continue
            dx = (lons[i] - lons[j]) / lon_span
            dy = (lats[i] - lats[j]) / lat_span
            d = math.hypot(dx, dy)
            if d < nearest_d:
                nearest_d = d
                vx += dx * 1.4
                vy += dy * 1.4
        norm = math.hypot(vx, vy) or 1.0
        vx, vy = vx / norm, vy / norm
        radius = 26.0 + density[i] * 14.0
        offsets.append([vx * radius, vy * radius])

    # Connected clusters of close markers → fan labels around the cluster.
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(
                (lons[i] - lons[j]) / lon_span,
                (lats[i] - lats[j]) / lat_span,
            )
            if d < 0.10:
                union(i, j)

    clusters: dict[int, list[int]] = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)

    for members in clusters.values():
        if len(members) < 2:
            continue
        # Sort north→south so stacked labels read top-to-bottom.
        members = sorted(members, key=lambda i: (-lats[i], lons[i]))
        # Fan toward the side with more empty space (usually east for AU SE).
        cl_lon = sum(lons[i] for i in members) / len(members)
        side = 1.0 if cl_lon < (min(lons) + max(lons)) / 2 else -1.0
        for k, i in enumerate(members):
            # Spread vertically in a column beside the cluster.
            t = k - (len(members) - 1) / 2.0
            offsets[i][0] = side * (48.0 + density[i] * 8.0)
            offsets[i][1] = t * 36.0

    # Final repulsion on label anchors (marker + offset).
    sx = lon_span / 520.0
    sy = lat_span / 460.0
    min_sep = 0.075
    for _ in range(80):
        for i in range(n):
            for j in range(i + 1, n):
                xi = lons[i] + offsets[i][0] * sx
                yi = lats[i] + offsets[i][1] * sy
                xj = lons[j] + offsets[j][0] * sx
                yj = lats[j] + offsets[j][1] * sy
                dx = (xi - xj) / lon_span
                dy = (yi - yj) / lat_span
                dist = math.hypot(dx, dy)
                if dist >= min_sep:
                    continue
                if dist < 1e-9:
                    dx, dy, dist = 0.02, 0.02, math.hypot(0.02, 0.02)
                push = (min_sep - dist) / dist
                offsets[i][0] += dx / max(sx, 1e-12) * lon_span * push * 0.22
                offsets[i][1] += dy / max(sy, 1e-12) * lat_span * push * 0.28
                offsets[j][0] -= dx / max(sx, 1e-12) * lon_span * push * 0.22
                offsets[j][1] -= dy / max(sy, 1e-12) * lat_span * push * 0.28

    return [(float(o[0]), float(o[1])) for o in offsets]

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_LOOKUP = os.path.normpath(
    os.path.join(_SCRIPT_DIR, "..", "assets", "place_lookup.json")
)


# ── Place lookup (offline aliases only — no external APIs) ───────────────────

def load_place_lookup(path: Optional[str] = None) -> dict[str, dict[str, Any]]:
    lookup_path = path or _DEFAULT_LOOKUP
    if not os.path.isfile(lookup_path):
        return {}
    with open(lookup_path, encoding="utf-8") as fh:
        data = json.load(fh)
    places = data.get("places") if isinstance(data, dict) else None
    if not isinstance(places, dict):
        return {}
    return {str(k).lower(): v for k, v in places.items() if isinstance(v, dict)}


def lookup_place(
    text: str,
    places: Mapping[str, Mapping[str, Any]],
) -> Optional[tuple[float, float, str]]:
    """Match name/address against bundled approximate centroids."""
    if not text or not places:
        return None
    key = text.strip().lower()
    for noise in (", australia", ", nsw", " nsw", ", sydney", " sydney"):
        key = key.replace(noise, "")
    key = key.strip(" ,")

    if key in places:
        p = places[key]
        return float(p["lat"]), float(p["lon"]), str(p.get("label") or text)

    best: Optional[tuple[int, str]] = None
    for alias in places:
        if alias in key or key in alias:
            score = len(alias)
            if best is None or score > best[0]:
                best = (score, alias)
    if best:
        p = places[best[1]]
        return float(p["lat"]), float(p["lon"]), str(p.get("label") or text)
    return None


def _customer_coords(raw: Mapping[str, Any]) -> Optional[tuple[float, float]]:
    """Return lat/lon from payload if present (user, prior tools, or agent).

    Always takes precedence over place_lookup. Accepts common aliases used by
    Dataverse/CRM exports (latitude/longitude, lng).
    """
    lat_raw = raw.get("lat", raw.get("latitude"))
    lon_raw = raw.get("lon", raw.get("lng", raw.get("longitude")))
    if lat_raw is None or lon_raw is None:
        return None
    if isinstance(lat_raw, str) and not lat_raw.strip():
        return None
    if isinstance(lon_raw, str) and not lon_raw.strip():
        return None
    try:
        lat, lon = float(lat_raw), float(lon_raw)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Invalid lat/lon values: lat={lat_raw!r}, lon={lon_raw!r}"
        ) from e
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ValueError(f"lat/lon out of range: lat={lat}, lon={lon}")
    return lat, lon


def resolve_points(
    points: Sequence[Mapping[str, Any]],
    *,
    place_lookup_path: Optional[str] = None,
    min_count: int = 1,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Normalise points to lat/lon + optional value/icon (offline only).

    Precedence per point:
    1. ``lat``/``lon`` already in the payload (user, prior tools like Dataverse,
       or agent web search) — always wins
    2. Bundled place lookup on location/address/name

    Does not call external APIs. If unresolved, raises with guidance for the agent
    to obtain coordinates (prior tool or web search) and re-invoke with lat/lon.
    """
    if len(points) < min_count:
        raise ValueError(f"Need at least {min_count} location(s).")
    places = load_place_lookup(place_lookup_path)
    warnings: list[str] = []
    resolved: list[dict[str, Any]] = []

    for i, raw in enumerate(points):
        name = str(raw.get("name") or f"Point {i + 1}")
        location = str(
            raw.get("location")
            or raw.get("address")
            or raw.get("display_name")
            or name
        )
        display = location
        value = raw.get("value", raw.get("label_value"))
        value_num = raw.get("value_num", raw.get("metric"))
        if value_num is not None:
            try:
                value_num = float(value_num)
            except (TypeError, ValueError):
                value_num = None
        icon = str(raw.get("icon") or raw.get("marker") or "pin")
        color = raw.get("color")

        coords = _customer_coords(raw)
        if coords is not None:
            lat, lon = coords
            source = "coords"
            if display == name:
                display = f"{lat:.5f}, {lon:.5f}"
        else:
            query = str(raw.get("location") or raw.get("address") or name)
            hit = lookup_place(query, places) or lookup_place(name, places)
            if hit:
                lat, lon, display = hit
                source = "place_lookup"
                warnings.append(
                    f"{name!r}: used bundled place_lookup centroid (approximate)."
                )
            else:
                raise ValueError(
                    f"Point {i + 1} ({name!r}): no lat/lon and no place_lookup match "
                    f"for {query!r}. The sandbox cannot call external geocoders — "
                    "use lat/lon from a prior tool (e.g. Dataverse) or web-search "
                    "them, then pass lat and lon into the payload."
                )

        meta = icon_meta(icon)
        fill = _safe_colour(str(color) if color else None, meta["color"])
        resolved.append(
            {
                "name": name,
                "lat": lat,
                "lon": lon,
                "address": str(raw.get("address") or raw.get("location") or ""),
                "location": location,
                "display_name": display,
                "coord_source": source,
                "value": None if value is None else str(value),
                "value_num": value_num,
                "icon": (icon or "pin").strip().lower().replace("_", "-"),
                "emoji": meta["emoji"],
                "icon_label": meta["label"],
                "color": fill,
            }
        )
    return resolved, warnings


def resolve_stops(*args: Any, **kwargs: Any) -> tuple[list[dict[str, Any]], list[str]]:
    kwargs.setdefault("min_count", 2)
    return resolve_points(*args, **kwargs)


# ── Distance / geometry (offline haversine) ──────────────────────────────────

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def offline_table(
    stops: Sequence[Mapping[str, Any]],
    profile: str = "driving",
) -> tuple[list[list[float]], list[list[float]]]:
    """Haversine distances with road factor + speed → (durations, distances)."""
    n = len(stops)
    factor = _ROAD_FACTOR.get(profile, 1.3)
    speed = _SPEED_MPS.get(profile, _SPEED_MPS["driving"])
    distances = [[0.0] * n for _ in range(n)]
    durations = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = haversine_m(stops[i]["lat"], stops[i]["lon"], stops[j]["lat"], stops[j]["lon"])
            d *= factor
            distances[i][j] = d
            durations[i][j] = d / speed
    return durations, distances


def offline_route(
    ordered: Sequence[Mapping[str, Any]],
    profile: str = "driving",
) -> dict[str, Any]:
    """Straight-line segments between ordered stops (GeoJSON LineString)."""
    if not ordered:
        return {
            "distance_m": 0.0,
            "duration_s": 0.0,
            "geometry": {"type": "LineString", "coordinates": []},
        }
    factor = _ROAD_FACTOR.get(profile, 1.3)
    speed = _SPEED_MPS.get(profile, _SPEED_MPS["driving"])
    coords: list[list[float]] = []
    total = 0.0
    for a, b in zip(ordered, ordered[1:]):
        # densify segment for smoother PNG/SVG
        steps = 8
        for t in range(steps + 1):
            if t == 0 and coords:
                continue
            u = t / steps
            lat = a["lat"] + (b["lat"] - a["lat"]) * u
            lon = a["lon"] + (b["lon"] - a["lon"]) * u
            coords.append([lon, lat])
        total += haversine_m(a["lat"], a["lon"], b["lat"], b["lon"]) * factor
    return {
        "distance_m": total,
        "duration_s": total / speed,
        "geometry": {"type": "LineString", "coordinates": coords},
    }


def _parse_connector_geometry(raw: Any) -> dict[str, Any]:
    """Convert connector route geometry to a GeoJSON LineString.

    Accepts:
    - A GeoJSON LineString dict (``{"type": "LineString", "coordinates": [...]}``).
    - A list of ``{lat, lon}`` or ``{latitude, longitude}`` dicts.
    - A list of ``[lon, lat]`` pairs (GeoJSON convention).
    Returns ``{"type": "LineString", "coordinates": []}`` if conversion fails.
    """
    if isinstance(raw, dict):
        if raw.get("type") == "LineString" and isinstance(raw.get("coordinates"), list):
            return raw
        if raw.get("type") == "FeatureCollection":
            for feat in raw.get("features") or []:
                if (feat or {}).get("geometry", {}).get("type") == "LineString":
                    return feat["geometry"]
    if not isinstance(raw, list) or not raw:
        return {"type": "LineString", "coordinates": []}
    coords: list[list[float]] = []
    for pt in raw:
        if isinstance(pt, dict):
            lat = float(pt.get("lat") or pt.get("latitude") or 0)
            lon = float(pt.get("lon") or pt.get("lng") or pt.get("longitude") or 0)
            coords.append([lon, lat])
        elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
            coords.append([float(pt[0]), float(pt[1])])
    return {"type": "LineString", "coordinates": coords}

def _tour_cost(order: list[int], matrix: list[list[float]], round_trip: bool) -> float:
    cost = 0.0
    for a, b in zip(order, order[1:]):
        cost += matrix[a][b]
    if round_trip:
        cost += matrix[order[-1]][order[0]]
    return cost


def _nearest_neighbour(matrix: list[list[float]], start: int, round_trip: bool) -> list[int]:
    n = len(matrix)
    unvisited = set(range(n)) - {start}
    order = [start]
    cur = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: matrix[cur][j])
        unvisited.remove(nxt)
        order.append(nxt)
        cur = nxt
    return order


def _two_opt(order: list[int], matrix: list[list[float]], round_trip: bool) -> list[int]:
    """Improve a tour with 2-opt. Keeps order[0] fixed as start."""
    best = order[:]
    improved = True
    while improved:
        improved = False
        best_cost = _tour_cost(best, matrix, round_trip)
        # Do not reverse across the fixed start at index 0
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                if j - i == 1:
                    continue
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                cost = _tour_cost(candidate, matrix, round_trip)
                if cost + 1e-9 < best_cost:
                    best = candidate
                    best_cost = cost
                    improved = True
                    break
            if improved:
                break
    return best


def optimise_order(
    matrix: list[list[float]],
    start: int = 0,
    round_trip: bool = True,
) -> list[int]:
    if start < 0 or start >= len(matrix):
        raise ValueError("`start` index out of range.")
    seed = _nearest_neighbour(matrix, start, round_trip)
    return _two_opt(seed, matrix, round_trip)


# ── Formatting helpers ───────────────────────────────────────────────────────

def _fmt_km(metres: float) -> str:
    if metres < 1000:
        return f"{metres:.0f} m"
    return f"{metres / 1000:.1f} km"


def _fmt_duration(seconds: float) -> str:
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h} h {m} min"
    if m:
        return f"{m} min"
    return f"{sec} s"


def markdown_summary(
    points: Sequence[Mapping[str, Any]],
    *,
    kind: str,
    chart_path: str,
    distance_m: float = 0.0,
    duration_s: float = 0.0,
    round_trip: bool = False,
    profile: str = "driving",
    routing_source: str = "none",
    legs: Optional[Sequence[Mapping[str, Any]]] = None,
    route_source: str = "",
    schematic: bool = True,
) -> str:
    """Markdown the agent can paste inline with the map image."""
    if kind == "map":
        lines = [
            "### Map",
            "",
            f"**Locations:** {len(points)} | **Kind:** marker map (no routing)",
            "",
            "| # | Name | Location | Value | Icon |",
            "| ---: | --- | --- | --- | --- |",
        ]
        for i, s in enumerate(points, start=1):
            loc = s.get("display_name") or s.get("location") or f"{s['lat']:.5f}, {s['lon']:.5f}"
            val = s.get("value") or ""
            icon = s.get("icon") or "pin"
            lines.append(f"| {i} | {s['name']} | {loc} | {val} | {icon} |")
        lines += [
            "",
            f"![Map]({chart_path})",
            "",
            "*Static lat/lon plot (PNG). Open the HTML export for an OpenStreetMap basemap.*",
        ]
        return "\n".join(lines)

    # ── Route summary ─────────────────────────────────────────────────────────
    src_label = route_source or routing_source or "unknown"
    if not schematic and route_source:
        dist_note = f"road distance via {route_source}"
        png_note  = f"Road route from **{route_source}** (connector-provided polyline)"
        html_note = f"Road polyline embedded — no browser-side OSRM needed"
    else:
        dist_note = "straight-line schematic estimate"
        png_note  = "**Schematic** straight-line sketch between stops"
        html_note = "Road-following route via **OSRM** (browser) or straight-line fallback"

    attr_badge = f" | **Source:** {src_label}" if src_label not in ("none", "unknown", "haversine_offline", "") else ""
    lines = [
        "### Route",
        "",
        f"**Profile:** {profile} | **Distance:** {_fmt_km(distance_m)} | "
        f"**Est. time:** {_fmt_duration(duration_s)}"
        + (" | **Round trip**" if round_trip else "")
        + attr_badge,
        "",
    ]

    if not schematic and route_source:
        lines += [
            f"> **Route source:** {route_source}  ",
            f"> PNG = {png_note} | HTML = {html_note}",
            "",
        ]
    else:
        lines += [
            f"> **PNG** = {png_note}  ",
            f"> **HTML** = {html_note}",
            "",
        ]

    lines += [
        "| # | Stop | Location |",
        "| ---: | --- | --- |",
    ]
    for i, s in enumerate(points, start=1):
        loc = s.get("display_name") or s.get("address") or f"{s['lat']:.5f}, {s['lon']:.5f}"
        lines.append(f"| {i} | {s['name']} | {loc} |")
    if round_trip and points:
        lines.append(f"| {len(points) + 1} | *(return)* | {points[0]['name']} |")

    # Per-leg table when connector provided breakdown
    if legs:
        lines += [
            "",
            "**Legs:**",
            "",
            "| # | From | To | Distance | Time | Via |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
        for k, leg in enumerate(legs, start=1):
            frm  = str(leg.get("from") or leg.get("origin") or "")
            to   = str(leg.get("to") or leg.get("destination") or "")
            d_m  = float(leg.get("distance_m") or leg.get("distance") or 0)
            t_s  = float(leg.get("duration_s") or leg.get("duration") or 0)
            via  = str(leg.get("summary") or leg.get("via") or leg.get("road") or "—")
            lines.append(f"| {k} | {frm} | {to} | {_fmt_km(d_m)} | {_fmt_duration(t_s)} | {via} |")

    lines += ["", f"![Route map]({chart_path})"]
    return "\n".join(lines)



# ── PNG map ────────────────────────────────────────────────────────────────────────────────────

def save_png(
    ordered: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    *,
    out: str,
    title: str,
    round_trip: bool = False,
    distance_m: float = 0.0,
    duration_s: float = 0.0,
    kind: str = "route",
    route_source: str = "",
    schematic: bool = True,
) -> str:
    from matplotlib.gridspec import GridSpec
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyBboxPatch

    coords = geometry.get("coordinates") or []
    xs = [c[0] for c in coords] if coords else [s["lon"] for s in ordered]
    ys = [c[1] for c in coords] if coords else [s["lat"] for s in ordered]
    lons = [float(s["lon"]) for s in ordered]
    lats = [float(s["lat"]) for s in ordered]

    n_pts = max(len(ordered), 1)
    # Dense maps (8+ markers, map mode): numbered markers + structured side panel.
    # Sparse maps: emoji markers + callout labels.
    dense_map = kind == "map" and n_pts >= 8

    # ── Figure layout ─────────────────────────────────────────────────────────────────────────────────
    fig_w   = 13.5 if not dense_map else 15.5
    fig_h   = 9.0  if not dense_map else 10.0
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)
    fig.patch.set_facecolor("white")

    title_lines = max(1, len(textwrap.wrap(title or " ", width=64)))
    # Compact header band: just enough for title + subtitle
    header_frac = min(0.095 + 0.028 * (title_lines - 1), 0.15)

    if dense_map:
        gs = GridSpec(
            2, 2, figure=fig,
            height_ratios=[header_frac, 1.0 - header_frac],
            width_ratios=[0.66, 0.34],
            hspace=0.04, wspace=0.0,
        )
        ax_head = fig.add_subplot(gs[0, :])
        ax      = fig.add_subplot(gs[1, 0])
        ax_side = fig.add_subplot(gs[1, 1])
        ax_side.set_axis_off()
        ax_side.set_xlim(0, 1)
        ax_side.set_ylim(0, 1)
    else:
        gs = GridSpec(
            2, 1, figure=fig,
            height_ratios=[header_frac, 1.0 - header_frac],
            hspace=0.04,
        )
        ax_head = fig.add_subplot(gs[0])
        ax      = fig.add_subplot(gs[1])
        ax_side = None

    ax_head.set_axis_off()
    ax_head.set_xlim(0, 1)
    ax_head.set_ylim(0, 1)
    ax.set_facecolor("#f4f7fb")
    emoji_fp = _emoji_fontproperties()

    # ── Route polyline ────────────────────────────────────────────────────────────────────────────────
    if kind == "route" and coords:
        ax.plot(
            [c[0] for c in coords], [c[1] for c in coords],
            color="#0078d4", linewidth=2.6, solid_capstyle="round", zorder=2,
        )

    # ── Markers ───────────────────────────────────────────────────────────────────────────────────
    label_offsets = _spread_label_offsets(lons, lats)
    label_box = dict(
        boxstyle="round,pad=0.28", facecolor="white",
        edgecolor="#c0bebe", linewidth=0.8, alpha=0.97,
    )

    for i, s in enumerate(ordered):
        colour = s.get("color") or (
            "#107c10" if kind == "route" and i == 0
            else ("#d83b01" if kind == "route" and i == len(ordered) - 1 and not round_trip
                  else "#0078d4")
        )
        # Single solid disc + white ring — clean, no donut effect
        ax.scatter(s["lon"], s["lat"], s=580, c=colour,
                   edgecolors="white", linewidths=2.0, zorder=4)

        if kind == "route" or dense_map:
            # White number on coloured disc
            ax.annotate(
                str(i + 1), (s["lon"], s["lat"]),
                ha="center", va="center",
                fontsize=11, fontweight="bold", color="white", zorder=6,
            )
        else:
            ax.annotate(
                str(s.get("emoji") or "📍"), (s["lon"], s["lat"]),
                ha="center", va="center",
                fontsize=15, zorder=6, fontproperties=emoji_fp,
            )

        if not dense_map:
            name  = str(s.get("name") or f"Point {i + 1}")
            value = str(s.get("value") or "").strip()
            label = f"{name}\n{textwrap.fill(value, 24)}" if value else name
            ox, oy = label_offsets[i] if i < len(label_offsets) else (36.0, 22.0)
            r = math.hypot(ox, oy)
            if r < 36:
                ox, oy = ox * 36 / max(r, 1e-6), oy * 36 / max(r, 1e-6)
            ax.annotate(
                label, (s["lon"], s["lat"]),
                textcoords="offset points", xytext=(ox, oy),
                fontsize=9, fontweight="bold", color="#201f1e",
                ha="center", va="center", zorder=5, linespacing=1.25,
                bbox=label_box,
                arrowprops=dict(arrowstyle="-", color="#999", lw=0.7,
                                shrinkA=2, shrinkB=16),
            )

    # ── Axis limits ──────────────────────────────────────────────────────────────────────────────────
    if xs and ys:
        pad_x = max((max(xs) - min(xs)) * 0.18, 0.04)
        pad_y = max((max(ys) - min(ys)) * 0.18, 0.04)
        ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
        ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)

    ax.set_xlabel("Longitude", fontsize=9, color="#605e5c")
    ax.set_ylabel("Latitude",  fontsize=9, color="#605e5c")
    ax.tick_params(labelsize=8, colors="#605e5c")
    ax.grid(True, color="#e1dfdd", linewidth=0.5, zorder=0)
    for spine in ax.spines.values():
        spine.set_color("#d2d0ce")

    # ── Header ─────────────────────────────────────────────────────────────────────────────────────
    wrapped_title = "\n".join(textwrap.wrap(title or " ", width=64))
    if kind == "route":
        if not schematic and route_source:
            subtitle = (
                f"{_fmt_km(distance_m)} | {_fmt_duration(duration_s)} | road route via {route_source}"
                + (" | round trip" if round_trip else "")
            )
        else:
            subtitle = (
                f"{_fmt_km(distance_m)} | {_fmt_duration(duration_s)} | schematic (straight-line)"
                + (" | round trip" if round_trip else "")
            )
    else:
        subtitle = f"{n_pts} locations | marker map"

    ax_head.text(
        0.5, 0.72, wrapped_title,
        transform=ax_head.transAxes, ha="center", va="center",
        fontsize=14, fontweight="bold", color="#201f1e", linespacing=1.2,
    )
    ax_head.text(
        0.5, 0.16, subtitle,
        transform=ax_head.transAxes, ha="center", va="center",
        fontsize=10, color="#605e5c",
    )

    # ── Legend / side panel ─────────────────────────────────────────────────────────────────────────
    # No emoji in matplotlib text (they garble). Use plain text + colour dots.

    if kind == "route":
        path_label = (
            f"Path (road route, {route_source})" if not schematic and route_source
            else "Path (schematic, straight-line)"
        )
        handles = [
            Line2D([0], [0], marker="o", color="w", markerfacecolor="#107c10",
                   markeredgecolor="#107c10", markersize=10, label="Start"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="#0078d4",
                   markeredgecolor="#0078d4", markersize=10, label="Stop"),
            Line2D([0], [0], color="#0078d4", lw=2.5, label=path_label),
        ]
        leg = ax.legend(handles, [h.get_label() for h in handles],
                        loc="upper left", bbox_to_anchor=(1.01, 1.0),
                        frameon=True, fancybox=False, framealpha=0.97,
                        edgecolor="#d2d0ce", fontsize=9,
                        title="Legend", title_fontsize=10,
                        labelspacing=0.65, borderpad=0.7)
        if leg.get_title():
            leg.get_title().set_fontweight("bold")

    elif dense_map and ax_side is not None:
        # Panel background
        ax_side.add_patch(FancyBboxPatch(
            (0.0, 0.0), 1.0, 1.0,
            boxstyle="square,pad=0", linewidth=0.8,
            edgecolor="#d2d0ce", facecolor="#fafafa",
            transform=ax_side.transAxes, zorder=0,
        ))

        seen_keys: dict[str, str] = {}
        seen_names: dict[str, str] = {}
        for s in ordered:
            k = str(s.get("icon") or "pin")
            if k not in seen_keys:
                seen_keys[k]  = s.get("color") or icon_meta(k)["color"]
                seen_names[k] = icon_meta(k).get("name") or k

        # Adapt spacing to fit all entries: tighter when there are many stops
        n_unique = len(seen_keys)
        # Budget: colour key uses ~(0.038 + n_unique*row_h + 0.06) of the panel
        # Remaining for location list: 0.97 - key_budget
        # Each location: name_h + (value_h if show_val) + gap
        show_val = n_pts <= 12   # skip value text for very large lists
        row_h   = 0.040 if n_pts <= 10 else 0.034
        name_h  = 0.028 if n_pts <= 10 else 0.024
        val_h   = 0.022 if n_pts <= 10 else 0.018
        gap_h   = 0.004

        cur_y = 0.97

        ax_side.text(0.07, cur_y, "Colour key",
                     transform=ax_side.transAxes,
                     fontsize=9, fontweight="bold", color="#201f1e", va="top")
        cur_y -= 0.032

        for k, col in seen_keys.items():
            ax_side.scatter([0.095], [cur_y + 0.007], s=60, c=col,
                            edgecolors="white", linewidths=0.9,
                            transform=ax_side.transAxes, zorder=3, clip_on=False)
            ax_side.text(0.185, cur_y + 0.005, seen_names[k],
                         transform=ax_side.transAxes, fontsize=8.5,
                         color="#201f1e", va="center", clip_on=True)
            cur_y -= row_h

        ax_side.add_artist(Line2D(
            [0.05, 0.95], [cur_y + 0.008, cur_y + 0.008],
            transform=ax_side.transAxes, color="#d2d0ce", linewidth=0.7,
        ))
        cur_y -= 0.024

        ax_side.text(0.07, cur_y, "Locations",
                     transform=ax_side.transAxes,
                     fontsize=9, fontweight="bold", color="#201f1e", va="top")
        cur_y -= 0.032

        for i, s in enumerate(ordered, start=1):
            if cur_y < 0.01:
                break
            name  = str(s.get("name") or f"Point {i}")
            value = str(s.get("value") or "").strip()
            ax_side.text(0.07, cur_y, f"{i}. {name}",
                         transform=ax_side.transAxes,
                         fontsize=8.5, fontweight="semibold", color="#201f1e",
                         va="top", clip_on=True)
            cur_y -= name_h
            if value and show_val and cur_y > 0.01:
                wrapped_val = textwrap.fill(value, width=30)
                n_vlines = wrapped_val.count("\n") + 1
                ax_side.text(0.10, cur_y, wrapped_val,
                             transform=ax_side.transAxes,
                             fontsize=7.8, color="#605e5c", va="top",
                             linespacing=1.2, clip_on=True)
                cur_y -= val_h * n_vlines
            cur_y -= gap_h

    elif not dense_map:
        seen2: dict[str, Mapping[str, Any]] = {}
        for s in ordered:
            k = str(s.get("icon") or "pin")
            if k not in seen2:
                seen2[k] = s
        handles2 = []
        for k, s in seen2.items():
            meta = icon_meta(k)
            col  = s.get("color") or meta["color"]
            nm   = meta.get("name") or k
            handles2.append(Line2D([0], [0], marker="o", color="w",
                                   markerfacecolor=col, markeredgecolor=col,
                                   markersize=11, label=nm))
        if handles2:
            leg = ax.legend(handles2, [h.get_label() for h in handles2],
                            loc="upper left", bbox_to_anchor=(1.01, 1.0),
                            frameon=True, fancybox=False, framealpha=0.97,
                            edgecolor="#d2d0ce", fontsize=9,
                            title="Legend", title_fontsize=10,
                            labelspacing=0.65, borderpad=0.7)
            if leg.get_title():
                leg.get_title().set_fontweight("bold")

    # ── Footer ──────────────────────────────────────────────────────────────────────────────────────
    if kind == "route":
        if not schematic and route_source:
            footer = f"Road route from {route_source} — open HTML for interactive map"
        else:
            footer = "Schematic sketch (straight-line, not road route) — open HTML for road path"
    else:
        footer = "Static plot (lat/lon) — open HTML for interactive map"
    ax.text(0.01, 0.012, footer, transform=ax.transAxes,
            fontsize=7.5, color="#8a8886", ha="left", va="bottom", zorder=7)

    fig.savefig(out, facecolor=fig.get_facecolor(), pad_inches=0.22,
                bbox_inches="tight")
    plt.close(fig)
    return out


# ── Interactive HTML (Leaflet + OpenStreetMap) ───────────────────────────────

def save_html(
    ordered: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    *,
    out: str,
    title: str,
    round_trip: bool = False,
    distance_m: float = 0.0,
    duration_s: float = 0.0,
    profile: str = "driving",
    routing_source: str = "haversine_offline",
    kind: str = "route",
    deep_links: dict[str, str] | None = None,
    has_road_geometry: bool = False,
    route_source: str = "",
) -> str:
    """Leaflet + OSM interactive map with markers/icons, optional route, legend."""
    stops_js = json.dumps(
        [
            {
                "n": i + 1,
                "name": s["name"],
                "lat": s["lat"],
                "lon": s["lon"],
                "display": s.get("display_name") or s.get("location") or s.get("address") or "",
                "value": s.get("value") or "",
                "icon": s.get("icon") or "pin",
                "emoji": s.get("emoji") or "📍",
                "color": s.get("color") or "#0078d4",
            }
            for i, s in enumerate(ordered)
        ],
        ensure_ascii=False,
    )
    geom_js = json.dumps(
        geometry or {"type": "LineString", "coordinates": []}, ensure_ascii=False
    )
    title_esc = (
        title.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    is_route = kind == "route"
    if is_route:
        if has_road_geometry and route_source:
            method_label = f"Road route from {route_source}"
        elif has_road_geometry:
            method_label = "Road route (connector-provided)"
        else:
            method_label = "Loading road route…"
        chips = (
            f'<div class="chip" id="chipDistance"><strong>{_fmt_km(distance_m)}</strong> distance</div>'
            f'<div class="chip" id="chipDuration"><strong>{_fmt_duration(duration_s)}</strong> est. time</div>'
            f'<div class="chip"><strong>{profile}</strong> profile</div>'
            f'<div class="chip"><strong>'
            f'{"Round trip" if round_trip else "One way"}</strong></div>'
            f'<div class="chip" id="chipRouteSrc"><strong>'
            f'{route_source or ("connector" if has_road_geometry else "OSRM")}</strong> road path</div>'
        )
        panel_title = "Visit order"
        hint = (
            "Click a stop to fly to it. "
            + (
                f"Blue line = road route from {route_source}."
                if has_road_geometry and route_source
                else "Blue line = real road route (OSRM). Falls back to straight lines if offline."
            )
        )
        route_btn_display = "inline-block"
        point_word = "stops"
    else:
        method_label = "Marker map (no routing)"
        chips = (
            f'<div class="chip"><strong>{len(ordered)}</strong> locations</div>'
            f'<div class="chip"><strong>Icons / values</strong> supported</div>'
        )
        panel_title = "Locations"
        hint = "Click a location to fly to its marker."
        route_btn_display = "none"
        point_word = "points"

    if deep_links is None:
        deep_links = {}
    if deep_links:
        deep_links_html = (
            '<div class="deeplinks">'
            "<h2>Open route in</h2>"
            f'<a class="deeplink" href="{deep_links["google_maps"]}" target="_blank" rel="noopener">Google Maps</a>'
            f'<a class="deeplink" href="{deep_links["apple_maps"]}" target="_blank" rel="noopener">Apple Maps</a>'
            f'<a class="deeplink" href="{deep_links["bing_maps"]}" target="_blank" rel="noopener">Bing Maps</a>'
            "</div>"
        )
    else:
        deep_links_html = ""

    has_geom_js = "true" if has_road_geometry else "false"
    route_src_js = json.dumps(route_source or "")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title_esc}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<style>
  :root {{
    --bg: #eef2f6; --card: #ffffff; --text: #1b1a19; --muted: #605e5c;
    --accent: #0078d4; --border: #d8d6d4; --shadow: 0 8px 28px rgba(15, 23, 42, 0.10);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    font-family: "Segoe UI", system-ui, sans-serif; color: var(--text);
    background:
      radial-gradient(1200px 500px at 10% -10%, #d6e8f8 0%, transparent 55%),
      radial-gradient(900px 400px at 100% 0%, #e7f2ea 0%, transparent 50%),
      var(--bg);
  }}
  .shell {{ max-width: 1180px; margin: 0 auto; padding: 18px 16px 28px; }}
  header {{
    display: flex; flex-wrap: wrap; gap: 12px 20px; align-items: flex-end;
    justify-content: space-between; margin-bottom: 14px;
  }}
  h1 {{ margin: 0 0 4px; font-size: 1.45rem; letter-spacing: -0.02em; }}
  .sub {{ color: var(--muted); font-size: 0.92rem; }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .chip {{
    background: var(--card); border: 1px solid var(--border); border-radius: 999px;
    padding: 6px 12px; font-size: 0.82rem; color: var(--muted);
  }}
  .chip strong {{ color: var(--text); font-weight: 600; }}
  .layout {{ display: grid; grid-template-columns: 320px 1fr; gap: 14px; }}
  @media (max-width: 860px) {{ .layout {{ grid-template-columns: 1fr; }} }}
  .panel, .map-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; box-shadow: var(--shadow);
  }}
  .panel {{ padding: 14px; max-height: 72vh; overflow: auto; }}
  .panel h2 {{ margin: 0 0 10px; font-size: 0.95rem; }}
  .hint {{ color: var(--muted); font-size: 0.78rem; margin: -4px 0 12px; }}
  ol.stops {{ margin: 0; padding: 0; list-style: none; }}
  ol.stops li {{
    display: grid; grid-template-columns: 34px 1fr; gap: 10px;
    padding: 9px 8px; margin: 0 0 4px; border-radius: 10px; cursor: pointer;
  }}
  ol.stops li:hover, ol.stops li.active {{ background: #f3f8fd; }}
  .badge {{
    width: 32px; height: 32px; border-radius: 50%; background: var(--accent);
    color: #fff; font: 700 14px/32px "Segoe UI", sans-serif; text-align: center;
  }}
  ol.stops .meta {{ color: var(--muted); font-size: 0.76rem; margin-top: 2px; }}
  ol.stops .val {{ font-weight: 600; color: var(--text); font-size: 0.84rem; }}
  .deeplinks {{ margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); }}
  .deeplinks h2 {{ margin: 0 0 8px; font-size: 0.95rem; }}
  .deeplink {{
    display: block; margin: 0 0 6px; padding: 8px 10px; border-radius: 8px;
    border: 1px solid var(--border); background: #f8fafc; color: var(--accent);
    text-decoration: none; font-size: 0.84rem; font-weight: 600;
  }}
  .deeplink:hover {{ background: #eef6fc; }}
  .map-card {{ position: relative; overflow: hidden; min-height: 520px; }}
  #map {{ height: 72vh; min-height: 520px; width: 100%; }}
  .legend {{
    position: absolute; z-index: 1000; right: 12px; bottom: 28px;
    background: rgba(255,255,255,.96); border: 1px solid var(--border);
    border-radius: 12px; padding: 10px 12px; box-shadow: var(--shadow);
    font-size: 0.78rem; min-width: 170px; max-width: 230px;
  }}
  .legend h3 {{ margin: 0 0 6px; font-size: 0.8rem; }}
  .legend-row {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
  .swatch {{
    width: 16px; height: 16px; border-radius: 50%; border: 2px solid #fff;
    box-shadow: 0 0 0 1px rgba(0,0,0,.12); display:inline-flex; align-items:center;
    justify-content:center; font-size: 10px;
  }}
  .swatch.line {{ width: 22px; height: 4px; border-radius: 2px; border: none; box-shadow: none; }}
  .toolbar {{
    position: absolute; z-index: 1000; top: 12px; left: 52px; display: flex; gap: 6px;
  }}
  .toolbar button {{
    border: 1px solid var(--border); background: rgba(255,255,255,.96);
    border-radius: 8px; padding: 7px 11px; cursor: pointer; font-size: 0.8rem;
  }}
  .foot {{ margin-top: 12px; font-size: 0.75rem; color: var(--muted); }}
  .foot a {{ color: var(--accent); }}
  .marker-pin {{
    width: 34px; height: 34px; border-radius: 50%; color: #fff;
    font: 700 14px/34px "Segoe UI", sans-serif; text-align: center;
    border: 3px solid #fff; box-shadow: 0 3px 10px rgba(0,0,0,.28);
  }}
  .marker-pin.icon {{ font-size: 18px; line-height: 34px; }}
  .stop-label {{
    background: rgba(255,255,255,.96); border: 1px solid #d8d6d4;
    border-radius: 6px; padding: 2px 7px; color: #1b1a19;
    font: 600 11px/1.3 "Segoe UI", system-ui, sans-serif;
    box-shadow: 0 2px 8px rgba(15,23,42,.12);
  }}
  .stop-label::before {{ display: none; }}
</style>
</head>
<body>
<div class="shell">
  <header>
    <div>
      <h1>{title_esc}</h1>
      <div class="sub" id="methodLabel">{method_label} on OpenStreetMap</div>
    </div>
    <div class="chips">
      {chips}
      <div class="chip"><strong>{len(ordered)}</strong> {point_word}</div>
    </div>
  </header>
  <div class="layout">
    <aside class="panel">
      <h2>{panel_title}</h2>
      <p class="hint">{hint}</p>
      <ol class="stops" id="stopList"></ol>
      {deep_links_html}
    </aside>
    <div class="map-card">
      <div class="toolbar">
        <button type="button" id="btnFit">Fit all</button>
        <button type="button" id="btnToggleRoute" style="display:{route_btn_display}">Toggle route</button>
        <button type="button" id="btnToggleLabels">Toggle labels</button>
      </div>
      <div id="map"></div>
      <div class="legend" id="legend"><h3>Legend</h3></div>
    </div>
  </div>
  <p class="foot">
    Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>
    · <a href="https://leafletjs.com/" target="_blank" rel="noopener">Leaflet</a>
    · Road routes via <a href="http://project-osrm.org/" target="_blank" rel="noopener">OSRM</a> (browser) when no connector geometry present
  </p>
</div>
<script>
const STOPS = {stops_js};
const GEOM = {geom_js};
const ROUND = {str(round_trip).lower()};
const PROFILE = {json.dumps(profile)};
const KIND = {json.dumps(kind)};
const IS_ROUTE = KIND === 'route';
const OSRM_PROFILE = ({{ driving: 'driving', walking: 'foot', cycling: 'bike' }})[PROFILE] || 'driving';
const HAS_ROAD_GEOMETRY = {has_geom_js};
const ROUTE_SOURCE = {route_src_js};
const markers = [];
let routeLayer = null;
let labelsOn = true;

function fmtKm(m) {{
  const km = Number(m) / 1000;
  return (km < 10 ? km.toFixed(1) : Math.round(km).toString()) + ' km';
}}
function fmtDuration(s) {{
  const sec = Math.max(0, Math.round(Number(s)));
  const h = Math.floor(sec / 3600);
  const m = Math.round((sec % 3600) / 60);
  if (h <= 0) return m + ' min';
  return h + ' h ' + m + ' min';
}}
function esc(s) {{
  return String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}
function setMethod(text) {{
  const el = document.getElementById('methodLabel');
  if (el) el.textContent = text;
}}
function setChip(id, text) {{
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}}

function markerIcon(s) {{
  const useEmoji = s.icon && s.icon !== 'pin';
  const inner = useEmoji ? esc(s.emoji) : String(s.n);
  const cls = useEmoji ? 'marker-pin icon' : 'marker-pin';
  return L.divIcon({{
    className: '',
    html: `<div class="${{cls}}" style="background:${{s.color}}">${{inner}}</div>`,
    iconSize: [34, 34], iconAnchor: [17, 17], popupAnchor: [0, -18]
  }});
}}

const list = document.getElementById('stopList');
const legend = document.getElementById('legend');
const seenIcons = new Map();
STOPS.forEach((s, i) => {{
  const li = document.createElement('li');
  li.dataset.idx = String(i);
  const badge = (s.icon && s.icon !== 'pin') ? esc(s.emoji) : String(s.n);
  li.innerHTML = `<span class="badge" style="background:${{s.color}}">${{badge}}</span>
    <div><strong>${{s.n}}. ${{esc(s.name)}}</strong>
    ${{s.value ? `<div class="val">${{esc(s.value)}}</div>` : ''}}
    <div class="meta">${{esc(s.display || (s.lat.toFixed(5)+', '+s.lon.toFixed(5)))}}</div></div>`;
  li.addEventListener('click', () => focusStop(i));
  list.appendChild(li);
  if (!seenIcons.has(s.icon)) seenIcons.set(s.icon, s);
}});
if (IS_ROUTE && ROUND && STOPS.length) {{
  const li = document.createElement('li');
  li.innerHTML = `<span class="badge" style="background:#8764b8">↩</span>
    <div><strong>Return to start</strong><div class="meta">Back to 1. ${{esc(STOPS[0].name)}}</div></div>`;
  li.addEventListener('click', () => focusStop(0));
  list.appendChild(li);
}}
if (IS_ROUTE) {{
  legend.innerHTML += `
    <div class="legend-row"><span class="swatch" style="background:#107c10"></span> Start</div>
    <div class="legend-row"><span class="swatch" style="background:#0078d4"></span> Stop</div>
    <div class="legend-row"><span class="swatch line" style="background:#0f6cbd"></span> Road route</div>`;
}} else {{
  seenIcons.forEach((s) => {{
    legend.innerHTML += `<div class="legend-row"><span class="swatch" style="background:${{s.color}}">${{s.emoji}}</span> ${{s.icon}}</div>`;
  }});
}}

const map = L.map('map', {{ zoomControl: true }});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 19, attribution: '&copy; OpenStreetMap'
}}).addTo(map);

function drawRoute(latlngs, {{ road }}) {{
  if (routeLayer) map.removeLayer(routeLayer);
  routeLayer = null;
  if (!latlngs || latlngs.length < 2) return;
  routeLayer = L.polyline(latlngs, {{
    color: '#0f6cbd',
    weight: road ? 5 : 5,
    opacity: 0.92,
    dashArray: road ? null : '10 8',
  }}).addTo(map);
}}

function fallbackRoute() {{
  const latlngs = (GEOM.coordinates || []).map(c => [c[1], c[0]]);
  drawRoute(latlngs, {{ road: false }});
  setMethod('Approximate path (OSRM unavailable) on OpenStreetMap');
  setChip('chipRouteSrc', 'Offline straight-line est.');
}}

function loadEmbeddedRoute() {{
  const latlngs = (GEOM.coordinates || []).map(c => [c[1], c[0]]);
  if (latlngs.length >= 2) {{
    drawRoute(latlngs, {{ road: true }});
  }}
  const srcLabel = ROUTE_SOURCE || 'connector';
  setMethod(srcLabel + ' road route on OpenStreetMap');
  setChip('chipRouteSrc', srcLabel);
  fitAll();
}}

async function loadRoadRoute() {{
  if (!IS_ROUTE || STOPS.length < 2) return;
  const pts = STOPS.map(s => s.lon.toFixed(6) + ',' + s.lat.toFixed(6));
  if (ROUND) pts.push(STOPS[0].lon.toFixed(6) + ',' + STOPS[0].lat.toFixed(6));
  // Public OSRM demo — used only from the browser (not the Python sandbox).
  const url = 'https://router.project-osrm.org/route/v1/' + OSRM_PROFILE + '/'
    + pts.join(';') + '?overview=full&geometries=geojson&steps=false';
  try {{
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    if (data.code !== 'Ok' || !data.routes || !data.routes[0]) {{
      throw new Error(data.code || 'no route');
    }}
    const route = data.routes[0];
    const latlngs = (route.geometry.coordinates || []).map(c => [c[1], c[0]]);
    drawRoute(latlngs, {{ road: true }});
    setChip('chipDistance', fmtKm(route.distance) + ' distance');
    setChip('chipDuration', fmtDuration(route.duration) + ' drive time');
    setChip('chipRouteSrc', 'OSRM road path');
    setMethod('Road-following route (OSRM) on OpenStreetMap');
    fitAll();
  }} catch (err) {{
    console.warn('OSRM road route failed; using approximate path', err);
    fallbackRoute();
    fitAll();
  }}
}}

STOPS.forEach((s, i) => {{
  const m = L.marker([s.lat, s.lon], {{ icon: markerIcon(s), riseOnHover: true }});
  const valHtml = s.value ? `<div style="margin-top:4px"><strong>${{esc(s.value)}}</strong></div>` : '';
  m.bindPopup(`<strong>${{s.n}}. ${{esc(s.name)}}</strong>${{valHtml}}
    <div style="color:#605e5c;margin-top:4px">${{esc(s.display || '')}}</div>`);
  m.on('click', () => highlightList(i));
  m.addTo(map);
  markers.push(m);
}});

function labelText(s) {{
  return s.value ? (esc(s.name) + ' · ' + esc(s.value)) : esc(s.name);
}}
function applyLabels(on) {{
  markers.forEach((m, i) => {{
    if (m.getTooltip()) m.unbindTooltip();
    if (on) {{
      m.bindTooltip(labelText(STOPS[i]), {{
        permanent: true,
        direction: 'top',
        offset: [0, -16],
        className: 'stop-label',
        opacity: 1,
      }});
    }}
  }});
  labelsOn = on;
  const btn = document.getElementById('btnToggleLabels');
  if (btn) btn.textContent = on ? 'Hide labels' : 'Show labels';
}}

function fitAll() {{
  const layers = [...markers];
  if (routeLayer) layers.push(routeLayer);
  if (layers.length) map.fitBounds(L.featureGroup(layers).getBounds().pad(0.18));
  else map.setView([-33.87, 151.21], 11);
}}
function highlightList(i) {{
  document.querySelectorAll('#stopList li').forEach(el => el.classList.remove('active'));
  const el = document.querySelector('#stopList li[data-idx="' + i + '"]');
  if (el) el.classList.add('active');
}}
function focusStop(i) {{
  const m = markers[i]; if (!m) return;
  highlightList(i);
  map.flyTo(m.getLatLng(), Math.max(map.getZoom(), 13), {{ duration: 0.7 }});
  m.openPopup();
}}
document.getElementById('btnFit').onclick = fitAll;
document.getElementById('btnToggleRoute').onclick = () => {{
  if (!routeLayer) return;
  if (map.hasLayer(routeLayer)) map.removeLayer(routeLayer); else routeLayer.addTo(map);
}};
document.getElementById('btnToggleLabels').onclick = () => applyLabels(!labelsOn);
applyLabels(true);
fitAll();
if (IS_ROUTE) {{
  if (HAS_ROAD_GEOMETRY) {{ loadEmbeddedRoute(); }} else {{ loadRoadRoute(); }}
}}
</script>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


# ── GeoJSON / KML ────────────────────────────────────────────────────────────

def save_geojson(
    ordered: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    *,
    out: str,
    title: str,
    round_trip: bool,
    distance_m: float,
    duration_s: float,
    profile: str,
    route_source: str = "",
) -> str:
    features: list[dict[str, Any]] = []
    coords = (geometry or {}).get("coordinates") or []
    if coords:
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "name": title,
                    "profile": profile,
                    "distance_m": distance_m,
                    "duration_s": duration_s,
                    "round_trip": round_trip,
                    "route_source": route_source or "",
                },
            }
        )
    for i, s in enumerate(ordered, start=1):
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [s["lon"], s["lat"]],
                },
                "properties": {
                    "name": s["name"],
                    "sequence": i,
                    "address": s.get("display_name") or s.get("address") or "",
                    "value": s.get("value"),
                    "icon": s.get("icon"),
                },
            }
        )
    doc = {
        "type": "FeatureCollection",
        "features": features,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    return out


def save_kml(
    ordered: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    *,
    out: str,
    title: str,
    round_trip: bool,
    distance_m: float,
    duration_s: float,
    profile: str,
) -> str:
    kml_ns = "http://www.opengis.net/kml/2.2"
    ET.register_namespace("", kml_ns)
    kml = ET.Element(f"{{{kml_ns}}}kml")
    doc = ET.SubElement(kml, f"{{{kml_ns}}}Document")
    ET.SubElement(doc, f"{{{kml_ns}}}name").text = title
    ET.SubElement(doc, f"{{{kml_ns}}}description").text = (
        f"{profile} | {_fmt_km(distance_m)} | {_fmt_duration(duration_s)}"
        + (" | round trip" if round_trip else "")
    )

    coords = (geometry or {}).get("coordinates") or []
    if coords:
        route_pm = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
        ET.SubElement(route_pm, f"{{{kml_ns}}}name").text = "Route"
        line = ET.SubElement(route_pm, f"{{{kml_ns}}}LineString")
        ET.SubElement(line, f"{{{kml_ns}}}tessellate").text = "1"
        ET.SubElement(line, f"{{{kml_ns}}}coordinates").text = " ".join(
            f"{c[0]},{c[1]},0" for c in coords
        )

    for i, s in enumerate(ordered, start=1):
        pm = ET.SubElement(doc, f"{{{kml_ns}}}Placemark")
        ET.SubElement(pm, f"{{{kml_ns}}}name").text = f"{i}. {s['name']}"
        bits = [
            s.get("display_name") or s.get("address") or "",
            f"value={s['value']}" if s.get("value") else "",
            f"icon={s['icon']}" if s.get("icon") else "",
        ]
        desc = " | ".join(b for b in bits if b)
        if desc:
            ET.SubElement(pm, f"{{{kml_ns}}}description").text = desc
        point = ET.SubElement(pm, f"{{{kml_ns}}}Point")
        ET.SubElement(point, f"{{{kml_ns}}}coordinates").text = (
            f"{s['lon']},{s['lat']},0"
        )

    tree = ET.ElementTree(kml)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


# ── Deep route links (Google / Apple / Bing) ─────────────────────────────────

def _coord_pair(stop: Mapping[str, Any]) -> str:
    return f"{float(stop['lat']):.6f},{float(stop['lon']):.6f}"


def _travel_modes(profile: str) -> dict[str, str]:
    """Map skill profile → provider travel-mode query values."""
    p = (profile or "driving").lower()
    if p == "walking":
        return {"google": "walking", "apple": "walking", "bing": "W"}
    if p in ("cycling", "bicycling", "bike"):
        return {"google": "bicycling", "apple": "driving", "bing": "D"}
    return {"google": "driving", "apple": "driving", "bing": "D"}


def build_map_links(
    ordered: Sequence[Mapping[str, Any]],
    *,
    profile: str = "driving",
    round_trip: bool = False,
) -> dict[str, str]:
    """Build deep-link URLs that open the ordered stops in native map apps.

    Requires ≥2 points with lat/lon. Round-trip sets destination back to start.
    """
    stops = [s for s in ordered if s.get("lat") is not None and s.get("lon") is not None]
    if len(stops) < 2:
        return {}

    modes = _travel_modes(profile)
    origin = _coord_pair(stops[0])
    if round_trip:
        destination = origin
        via = stops[1:]
    else:
        destination = _coord_pair(stops[-1])
        via = stops[1:-1]

    # Google Maps Directions URL
    # https://developers.google.com/maps/documentation/urls/get-started#directions-action
    g_params: dict[str, str] = {
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": modes["google"],
    }
    if via:
        g_params["waypoints"] = "|".join(_coord_pair(s) for s in via)
    google = "https://www.google.com/maps/dir/?" + urlencode(g_params, safe=",|")

    # Apple Maps unified directions URL
    # https://developer.apple.com/documentation/mapkit/unified-map-urls
    a_params: list[tuple[str, str]] = [
        ("source", origin),
        ("destination", destination),
        ("mode", modes["apple"]),
    ]
    for s in via:
        a_params.append(("waypoint", _coord_pair(s)))
    apple = "https://maps.apple.com/directions?" + urlencode(a_params, safe=",")

    # Bing Maps multi-stop route URL
    # https://learn.microsoft.com/en-us/bingmaps/articles/create-a-custom-map-url
    bing_pts = list(stops)
    if round_trip:
        bing_pts = list(stops) + [stops[0]]
    rtp = "~".join(
        f"pos.{float(s['lat']):.6f}_{float(s['lon']):.6f}" for s in bing_pts
    )
    bing = "https://www.bing.com/maps?" + urlencode(
        {"rtp": rtp, "mode": modes["bing"]},
        safe=".~_",
    )

    return {
        "google_maps": google,
        "apple_maps": apple,
        "bing_maps": bing,
    }


def save_map_links(
    links: Mapping[str, str],
    *,
    out: str,
    title: str,
    profile: str,
    round_trip: bool,
) -> str:
    """Write map deep links as JSON (same optional-export pattern as GeoJSON/KML)."""
    doc = {
        "title": title,
        "profile": profile,
        "round_trip": round_trip,
        "links": dict(links),
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
    return out


def _qr_to_image(data: str, box: int = 8, border: int = 4) -> "Image.Image":
    """Rasterise *data* to a QR-code PIL Image using reportlab + Pillow.

    Uses ``reportlab.graphics.barcode.qrencoder`` (always available in the
    sandbox) so no extra ``pip install`` is required.  Error-correction level M
    (~15 % recovery capacity) is a good default for URLs.
    """
    try:
        from reportlab.graphics.barcode.qrencoder import QRCode, QRErrorCorrectLevel as _ECL
    except ImportError:
        from reportlab.graphics.barcode.qrencoder import QRCode, ErrorCorrectLevel as _ECL  # type: ignore[no-redef]
    from PIL import Image as _Image

    qr = QRCode(None, _ECL.M)   # None = auto-select version
    qr.addData(data)
    qr.make()
    matrix = qr.modules                       # list[list[bool]]
    n      = len(matrix)
    side   = (n + 2 * border) * box
    img    = _Image.new("RGB", (side, side), "white")
    pixels = img.load()
    for r, row in enumerate(matrix):
        for c, dark in enumerate(row):
            if dark:
                px = (border + c) * box
                py = (border + r) * box
                for dy in range(box):
                    for dx in range(box):
                        pixels[px + dx, py + dy] = (0, 0, 0)
    return img


def save_qr_codes(
    links: Mapping[str, str],
    *,
    prefix: str,
    title: str = "",
) -> dict[str, str]:
    """Generate QR code PNGs for each map deep link and a combined sheet.

    Returns a dict with keys ``google_maps``, ``apple_maps``, ``bing_maps``
    (individual files) and ``sheet`` (combined image), all pointing to absolute
    file paths.  Any key whose link is absent is omitted from the result.

    Uses ``reportlab`` + ``Pillow`` — both pre-installed in the sandbox.
    """
    from PIL import Image, ImageDraw, ImageFont

    # (dict-key, short filename label, display label)
    LABELS: list[tuple[str, str, str]] = [
        ("google_maps", "google", "Google Maps"),
        ("apple_maps",  "apple",  "Apple Maps"),
        ("bing_maps",   "bing",   "Bing Maps"),
    ]
    QR_SIZE = 280        # px per individual QR image (data area)
    MARGIN  = 20         # px margin inside each cell
    LABEL_H = 34         # px reserved below each QR for its text label
    CELL_W  = QR_SIZE + MARGIN * 2
    CELL_H  = QR_SIZE + MARGIN * 2 + LABEL_H
    BG      = (255, 255, 255)
    FG      = (30,  30,  30)
    MUTED   = (96,  94,  92)

    paths: dict[str, str] = {}
    cells: list[tuple[Image.Image, str]] = []   # (qr_img, display_label) for sheet

    for key, short, label in LABELS:
        url = links.get(key)
        if not url:
            continue

        img: Image.Image = _qr_to_image(url)
        img = img.resize((QR_SIZE, QR_SIZE), Image.NEAREST)

        dest = os.path.abspath(f"{prefix}_qr_{short}.png")
        img.save(dest, "PNG")
        paths[key] = dest
        cells.append((img, label))

    if not cells:
        return paths

    # ── Combined sheet ────────────────────────────────────────────────────────
    n = len(cells)
    TITLE_H = 52 if title else 0
    sheet_w = CELL_W * n
    sheet_h = CELL_H + TITLE_H
    sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
    draw  = ImageDraw.Draw(sheet)

    # Try to load a legible system font; fall back to default
    font_large: ImageFont.ImageFont | ImageFont.FreeTypeFont
    font_title: ImageFont.ImageFont | ImageFont.FreeTypeFont
    try:
        font_large = ImageFont.truetype("arial.ttf",  16)
        font_title = ImageFont.truetype("arialbd.ttf", 18)
    except OSError:
        try:
            font_large = ImageFont.truetype("DejaVuSans.ttf", 16)
            font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        except OSError:
            font_large = font_title = ImageFont.load_default()

    # Title bar
    if title:
        title_text = title if len(title) <= 55 else title[:52] + "…"
        bbox = draw.textbbox((0, 0), title_text, font=font_title)
        tw   = bbox[2] - bbox[0]
        draw.text(((sheet_w - tw) // 2, 14), title_text, fill=FG, font=font_title)
        draw.line([(0, TITLE_H - 2), (sheet_w, TITLE_H - 2)], fill=(220, 210, 206), width=1)

    # QR cells
    for idx, (qr_img, lbl) in enumerate(cells):
        x0 = idx * CELL_W
        y0 = TITLE_H

        # Thin cell border except last right edge
        if idx > 0:
            draw.line([(x0, y0 + 6), (x0, y0 + CELL_H - 6)], fill=(220, 210, 206), width=1)

        # Paste QR
        sheet.paste(qr_img, (x0 + MARGIN, y0 + MARGIN))

        # Label below QR
        bbox = draw.textbbox((0, 0), lbl, font=font_large)
        lw   = bbox[2] - bbox[0]
        lx   = x0 + (CELL_W - lw) // 2
        ly   = y0 + MARGIN + QR_SIZE + 6
        draw.text((lx, ly), lbl, fill=MUTED, font=font_large)

    sheet_path = os.path.abspath(f"{prefix}_qr_sheet.png")
    sheet.save(sheet_path, "PNG")
    paths["sheet"] = sheet_path
    return paths


def _map_links_markdown(links: Mapping[str, str], qr_paths: Mapping[str, str] | None = None) -> str:
    if not links:
        return ""
    lines = [
        "",
        "### Open in maps",
        "",
        "Deep links for the optimised stop order (opens in the map app / site):",
        "",
    ]
    labels = (
        ("google_maps", "Google Maps"),
        ("apple_maps", "Apple Maps"),
        ("bing_maps", "Bing Maps"),
    )
    for key, label in labels:
        url = links.get(key)
        if url:
            lines.append(f"- [{label}]({url})")
    lines.append("")
    if qr_paths:
        lines += [
            "**QR codes** — scan to open the route on your phone:",
            "",
        ]
        sheet = qr_paths.get("sheet")
        if sheet:
            lines.append(f"![QR code sheet]({sheet})")
            lines.append("")
        else:
            for key, label in labels:
                p = qr_paths.get(key)
                if p:
                    lines.append(f"- {label}: `{p}`")
            lines.append("")
    return "\n".join(lines)


_FORMULA_CHARS = frozenset("=+-@|%`")


def _csv_cell(val: str) -> str:
    """Quote a CSV cell; prefix with tab if it starts with a formula trigger char."""
    safe = val.replace('"', "'")
    if safe and safe[0] in _FORMULA_CHARS:
        safe = "\t" + safe
    return f'"{safe}"'


def save_stops_csv(ordered: Sequence[Mapping[str, Any]], out: str) -> str:
    """Write stop data to CSV; sanitizes formula-injection characters."""
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("sequence,name,lat,lon,location,value,icon\n")
        for i, s in enumerate(ordered, start=1):
            name = str(s.get("name") or "")
            loc  = s.get("display_name") or s.get("location") or s.get("address") or ""
            val  = str(s.get("value") or "")
            icon = str(s.get("icon") or "pin")
            fh.write(
                f'{i},{_csv_cell(name)},{s["lat"]:.6f},{s["lon"]:.6f},'
                f'{_csv_cell(str(loc))},{_csv_cell(val)},{_csv_cell(icon)}\n'
            )
    return out


def _available_options_markdown(payload: Mapping[str, Any], kind: str) -> str:
    """Return a brief hint listing optional exports the user has not yet enabled.

    Always appended to result["markdown"] so users and downstream agents can
    discover what's available and enable it in subsequent calls or agent instructions.
    """
    _f = payload.get   # shorthand

    opts: list[tuple[str, str]] = []

    if not _f("html"):
        road = " — real road-following route in the browser (OSRM)" if kind == "route" else ""
        opts.append(("html", f'`"html": true` — interactive OpenStreetMap{road}'))

    if not (_f("csv") or _f("csv_path")):
        opts.append(("csv", '`"csv": true` — CSV table of all stops/locations'))

    if not (_f("geojson") or _f("geojson_path")):
        opts.append(("geojson", '`"geojson": true` — GeoJSON for QGIS, Power BI, or any GIS tool'))

    if not (_f("kml") or _f("kml_path")):
        opts.append(("kml", '`"kml": true` — KML for Google Earth / My Maps / ArcGIS'))

    if kind == "route":
        has_links = any(_f(k) for k in ("map_links", "maps_links",
                                        "google_maps", "apple_maps", "bing_maps"))
        if not has_links:
            opts.append(("map_links",
                         '`"map_links": true` — deep links to open the route in '
                         'Google Maps, Apple Maps, and Bing Maps'))

        has_qr = _f("qr_codes") or _f("qr")
        if not has_qr:
            opts.append(("qr_codes",
                         '`"qr_codes": true` — QR code sheet '
                         '(scan on phone to open the route in any map app)'))

    if not opts:
        return ""

    lines = [
        "",
        "---",
        "**Optional exports** — not generated this run. "
        "Add any flag to your payload (or ask the agent) to enable it:",
        "",
    ]
    for _, desc in opts:
        lines.append(f"- {desc}")
    lines += [
        "",
        "> **Tip for downstream actions:** set these flags permanently in your "
        "agent's system instructions so every map includes the exports your "
        "workflow needs — e.g. always output GeoJSON for a Power Automate flow, "
        "or always include QR codes when the result is sent to a mobile user.",
        "",
        "> **Tip for accurate road routes:** pass `route_geometry` from an upstream "
        "routing connector (Azure Maps, Bing Maps, etc.) to render the actual road "
        "polyline in both PNG and HTML — no browser-side OSRM call needed.",
        "",
    ]
    return "\n".join(lines)


# ── Orchestration ────────────────────────────────────────────────────────────
def _as_payload(source: Any) -> dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)
    if isinstance(source, str):
        with open(source, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        raise TypeError("payload must be a dict or path to a JSON file")
    if isinstance(data, list):
        raise TypeError("payload JSON must be an object, not an array")
    if not isinstance(data, dict):
        raise TypeError("payload must be a JSON object")
    return data


def _detect_kind(payload: Mapping[str, Any]) -> str:
    kind = str(payload.get("kind", "auto")).lower()
    if kind in ("map", "markers", "marker"):
        return "map"
    if kind == "route":
        return "route"
    if payload.get("optimize") is False or payload.get("route") is False:
        return "map"
    if payload.get("optimize") is True or payload.get("route") is True:
        return "route"
    if payload.get("round_trip") is True:
        return "route"
    if payload.get("points") and not payload.get("stops"):
        return "map"
    return "map"


def generate(data: Mapping[str, Any] | str) -> dict[str, Any]:
    """Visualize a route or marker map. Returns paths + markdown."""
    payload = _as_payload(data)
    points_in = payload.get("points") or payload.get("stops") or payload.get("locations")
    if not isinstance(points_in, list) or not points_in:
        raise ValueError(
            "`points` (or `stops` / `locations`) must be a non-empty list."
        )

    kind = _detect_kind(payload)
    profile = str(payload.get("profile", "driving")).lower()
    if profile not in PROFILES:
        raise ValueError(f"`profile` must be one of {PROFILES}.")

    round_trip = bool(payload.get("round_trip", False))
    title = str(
        payload.get("title")
        or payload.get("chart_title")
        or ("Route" if kind == "route" else "Map")
    )
    prefix = str(payload.get("out_prefix", "map" if kind == "map" else "route"))
    # Sample payloads use out/... — ensure the parent exists before any writes.
    _prefix_dir = os.path.dirname(prefix)
    if _prefix_dir:
        os.makedirs(_prefix_dir, exist_ok=True)
    lookup_path = payload.get("place_lookup_path")

    # ── Connector-provided route data ─────────────────────────────────────────
    _geom_raw       = payload.get("route_geometry") or payload.get("geometry_coords")
    _legs           = list(payload.get("legs") or [])
    _route_source   = str(payload.get("route_source") or "")
    _total_dist_m   = payload.get("total_distance_m")
    _total_dur_s    = payload.get("total_duration_s")
    # schematic_order: opt-in offline NN+2opt ordering (legacy alias: optimize)
    _schematic_order = bool(payload.get("schematic_order") or payload.get("optimize"))

    # Fully offline — no external geocoding/routing APIs in the sandbox.
    resolved, warnings = resolve_points(
        points_in,
        place_lookup_path=lookup_path,
        min_count=2 if kind == "route" else 1,
    )

    routing_source = "none"
    ordered = list(resolved)
    route: dict[str, Any] = {
        "distance_m": 0.0,
        "duration_s": 0.0,
        "geometry": {"type": "LineString", "coordinates": []},
    }
    has_road_geometry = False
    schematic = True

    if kind == "route":
        start = payload.get("start", 0)
        if isinstance(start, str):
            names = [s["name"].lower() for s in resolved]
            if start.lower() not in names:
                raise ValueError(f"start stop {start!r} not found in stop names.")
            start_idx = names.index(start.lower())
        else:
            start_idx = int(start)

        if _schematic_order:
            # Offline NN+2opt on straight-line distances — opt-in only.
            durations, _distances = offline_table(resolved, profile=profile)
            order_idx = optimise_order(durations, start=start_idx, round_trip=round_trip)
            ordered = [resolved[i] for i in order_idx]
            warnings.append(
                "schematic_order: stop sequence is a straight-line heuristic. "
                "For real road order, use a routing connector upstream."
            )

        # Build geometry + distances from connector data when available.
        if _geom_raw:
            geom = _parse_connector_geometry(_geom_raw)
            if geom.get("coordinates"):
                has_road_geometry = True
                schematic = False
                routing_source = _route_source or "connector"

                # Distances: prefer connector totals → leg sums → haversine
                if _total_dist_m is not None:
                    total_d = float(_total_dist_m)
                elif _legs:
                    total_d = sum(
                        float(lg.get("distance_m") or lg.get("distance") or 0)
                        for lg in _legs
                    )
                else:
                    total_d = 0.0
                if _total_dur_s is not None:
                    total_t = float(_total_dur_s)
                elif _legs:
                    total_t = sum(
                        float(lg.get("duration_s") or lg.get("duration") or 0)
                        for lg in _legs
                    )
                else:
                    total_t = 0.0

                route = {"distance_m": total_d, "duration_s": total_t, "geometry": geom}
            else:
                warnings.append(
                    "route_geometry was provided but contained no parseable coordinates — "
                    "falling back to schematic straight-line rendering."
                )

        if not has_road_geometry:
            # Schematic fallback — straight-line segments between stops.
            route_stops = ordered + ([ordered[0]] if round_trip and len(ordered) > 1 else [])
            route = offline_route(route_stops, profile=profile)
            # Override with connector distance/duration if supplied without geometry
            if _total_dist_m is not None:
                route["distance_m"] = float(_total_dist_m)
            if _total_dur_s is not None:
                route["duration_s"] = float(_total_dur_s)
            routing_source = _route_source or "schematic"

    chart_path = str(payload.get("chart_path", f"{prefix}_map.png"))
    save_png(
        ordered,
        route["geometry"],
        out=chart_path,
        title=title,
        round_trip=round_trip,
        distance_m=route["distance_m"],
        duration_s=route["duration_s"],
        kind=kind,
        route_source=_route_source,
        schematic=schematic,
    )

    # CSV is opt-in — only written when explicitly requested
    want_csv = bool(payload.get("csv", False) or payload.get("csv_path"))
    csv_path: str | None = None
    if want_csv:
        csv_path = str(payload.get("csv_path", f"{prefix}_points.csv"))
        save_stops_csv(ordered, csv_path)

    md = markdown_summary(
        ordered,
        kind=kind,
        chart_path=os.path.abspath(chart_path),
        distance_m=route["distance_m"],
        duration_s=route["duration_s"],
        round_trip=round_trip,
        profile=profile,
        routing_source=routing_source,
        legs=_legs or None,
        route_source=_route_source,
        schematic=schematic,
    )
    md_path = str(payload.get("markdown_path", f"{prefix}_summary.md"))
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    if kind == "route":
        if has_road_geometry:
            method = f"connector road geometry ({_route_source})" if _route_source else "connector road geometry"
            attribution = f"PNG: road route | HTML: connector polyline embedded (no OSRM)"
        else:
            method = "schematic straight-line (no connector geometry provided)"
            attribution = "PNG: schematic sketch | HTML: road-following route via OSRM (browser)"
    else:
        method = "marker map (no routing)"
        attribution = "PNG is a static lat/lon plot; OSM tiles only in the HTML export"

    result: dict[str, Any] = {
        "title": title,
        "kind": kind,
        "profile": profile,
        "routing_source": routing_source,
        "route_source": _route_source,
        "has_road_geometry": has_road_geometry,
        "round_trip": round_trip if kind == "route" else False,
        "distance_m": route["distance_m"],
        "distance_label": _fmt_km(route["distance_m"]),
        "duration_s": route["duration_s"],
        "duration_label": _fmt_duration(route["duration_s"]),
        "stop_order": [s["name"] for s in ordered],
        "points": ordered,
        "stops": ordered,
        "chart_path": os.path.abspath(chart_path),
        "csv_path": os.path.abspath(csv_path) if csv_path else None,
        "markdown_path": os.path.abspath(md_path),
        "markdown": md,
        "method": method,
        "attribution": attribution,
        "warnings": warnings,
    }

    if bool(payload.get("html", False)):
        html_path = str(payload.get("html_path", f"{prefix}_map.html"))
        _html_deep_links: dict[str, str] = {}
        if bool(payload.get("map_links") or payload.get("maps_links")
                or payload.get("google_maps") or payload.get("apple_maps") or payload.get("bing_maps")):
            _html_deep_links = build_map_links(
                ordered, profile=profile,
                round_trip=round_trip if kind == "route" else False,
            )
        save_html(
            ordered,
            route["geometry"],
            out=html_path,
            title=title,
            round_trip=round_trip,
            distance_m=route["distance_m"],
            duration_s=route["duration_s"],
            profile=profile,
            routing_source=routing_source,
            kind=kind,
            deep_links=_html_deep_links,
            has_road_geometry=has_road_geometry,
            route_source=_route_source,
        )
        result["html_path"] = os.path.abspath(html_path)

    if bool(payload.get("geojson", False)):
        gj_path = str(payload.get("geojson_path", f"{prefix}.geojson"))
        save_geojson(
            ordered,
            route["geometry"],
            out=gj_path,
            title=title,
            round_trip=round_trip,
            distance_m=route["distance_m"],
            duration_s=route["duration_s"],
            profile=profile,
            route_source=_route_source,
        )
        result["geojson_path"] = os.path.abspath(gj_path)

    if bool(payload.get("kml", False)):
        kml_path = str(payload.get("kml_path", f"{prefix}.kml"))
        save_kml(
            ordered,
            route["geometry"],
            out=kml_path,
            title=title,
            round_trip=round_trip,
            distance_m=route["distance_m"],
            duration_s=route["duration_s"],
            profile=profile,
        )
        result["kml_path"] = os.path.abspath(kml_path)

    # Optional deep route links
    want_links = bool(
        payload.get("map_links")
        or payload.get("maps_links")
        or payload.get("google_maps")
        or payload.get("apple_maps")
        or payload.get("bing_maps")
    )
    if want_links:
        links = build_map_links(
            ordered,
            profile=profile,
            round_trip=round_trip if kind == "route" else False,
        )
        if not (
            payload.get("map_links") or payload.get("maps_links")
        ) and (
            payload.get("google_maps")
            or payload.get("apple_maps")
            or payload.get("bing_maps")
        ):
            selected: dict[str, str] = {}
            if payload.get("google_maps") and links.get("google_maps"):
                selected["google_maps"] = links["google_maps"]
            if payload.get("apple_maps") and links.get("apple_maps"):
                selected["apple_maps"] = links["apple_maps"]
            if payload.get("bing_maps") and links.get("bing_maps"):
                selected["bing_maps"] = links["bing_maps"]
            links = selected

        if links:
            links_path = str(payload.get("map_links_path", f"{prefix}_map_links.json"))
            save_map_links(
                links,
                out=links_path,
                title=title,
                profile=profile,
                round_trip=round_trip if kind == "route" else False,
            )
            result["map_links"] = links
            result["map_links_path"] = os.path.abspath(links_path)
            result["google_maps_url"] = links.get("google_maps")
            result["apple_maps_url"] = links.get("apple_maps")
            result["bing_maps_url"] = links.get("bing_maps")

            want_qr = bool(payload.get("qr_codes") or payload.get("qr"))
            qr_paths: dict[str, str] = {}
            if want_qr:
                try:
                    qr_paths = save_qr_codes(links, prefix=prefix, title=title)
                    result["qr_paths"] = qr_paths
                    result["qr_sheet_path"] = qr_paths.get("sheet")
                except ImportError as exc:
                    warnings.append(str(exc))
                    result["warnings"] = warnings

            md = (result["markdown"] or "") + _map_links_markdown(links, qr_paths or None)
            result["markdown"] = md
            with open(md_path, "w", encoding="utf-8") as fh:
                fh.write(md)
        else:
            warnings.append(
                "map_links requested but need ≥2 points with lat/lon to build route URLs."
            )
            result["warnings"] = warnings

    # Available-options hint for users and downstream agents
    hint = _available_options_markdown(payload, kind)
    if hint:
        full_md = (result["markdown"] or "") + hint
        result["markdown"] = full_md
        result["available_options_hint"] = hint
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(full_md)

    result["generated_exports"] = {
        "png":        True,
        "html":       bool(result.get("html_path")),
        "csv":        bool(result.get("csv_path")),
        "geojson":    bool(result.get("geojson_path")),
        "kml":        bool(result.get("kml_path")),
        "map_links":  bool(result.get("map_links_path")),
        "qr_codes":   bool(result.get("qr_sheet_path")),
    }

    return result


def plan_route(data: Mapping[str, Any] | str) -> dict[str, Any]:
    """Backward-compatible alias — visualises stops in provided order."""
    payload = _as_payload(data)
    if "kind" not in payload:
        payload = dict(payload)
        payload.setdefault("kind", "route")
    return generate(payload)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Route map visualizer — render connector route data as maps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--payload", required=True, help="Path to JSON payload.")
    p.add_argument("--kind", choices=["auto", "map", "route"], default=None)
    p.add_argument("--profile", choices=list(PROFILES), default=None)
    p.add_argument("--round-trip", dest="round_trip", action="store_true", default=None)
    p.add_argument("--one-way", dest="round_trip", action="store_false")
    p.add_argument("--title", default=None)
    p.add_argument("--out-prefix", default=None, dest="out_prefix")
    p.add_argument("--html", action="store_true")
    p.add_argument("--csv", action="store_true", help="Write a CSV of all stops/locations.")
    p.add_argument("--geojson", action="store_true")
    p.add_argument("--kml", action="store_true")
    p.add_argument(
        "--map-links",
        action="store_true",
        help="Emit Google / Apple / Bing Maps deep route links.",
    )
    p.add_argument(
        "--qr-codes",
        action="store_true",
        dest="qr_codes",
        help="Generate QR code PNGs for the map deep links (requires --map-links).",
    )
    p.add_argument("--json-out", action="store_true", help="Print full result JSON.")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    data = _as_payload(args.payload)
    if args.kind is not None:
        data["kind"] = args.kind
    if args.profile is not None:
        data["profile"] = args.profile
    if args.round_trip is not None:
        data["round_trip"] = args.round_trip
    if args.title is not None:
        data["title"] = args.title
    if args.out_prefix is not None:
        data["out_prefix"] = args.out_prefix
    if args.html:
        data["html"] = True
    if args.csv:
        data["csv"] = True
    if args.geojson:
        data["geojson"] = True
    if args.kml:
        data["kml"] = True
    if args.map_links:
        data["map_links"] = True
    if args.qr_codes:
        data["qr_codes"] = True

    result = generate(data)

    print(result["markdown"])
    print()
    print(f"Kind:     {result.get('kind')}")
    print(f"Routing:  {result.get('routing_source')}")
    print(f"PNG:      {result['chart_path']}")
    if result.get("csv_path"):
        print(f"CSV:      {result['csv_path']}")
    if result.get("html_path"):
        print(f"HTML:     {result['html_path']}")
    if result.get("geojson_path"):
        print(f"GeoJSON:  {result['geojson_path']}")
    if result.get("kml_path"):
        print(f"KML:      {result['kml_path']}")
    if result.get("map_links_path"):
        print(f"MapLinks: {result['map_links_path']}")
    if result.get("qr_sheet_path"):
        print(f"QR sheet: {result['qr_sheet_path']}")
    if result.get("google_maps_url"):
        print(f"Google:   {result['google_maps_url']}")
    if result.get("apple_maps_url"):
        print(f"Apple:    {result['apple_maps_url']}")
    if result.get("bing_maps_url"):
        print(f"Bing:     {result['bing_maps_url']}")
    exports = result.get("generated_exports") or {}
    not_generated = [k for k, v in exports.items() if not v]
    if not_generated:
        print(f"Not generated (add flag to enable): {', '.join(not_generated)}")
    for w in result.get("warnings") or []:
        print(f"Warning:  {w}")

    if args.json_out:
        slim = {k: v for k, v in result.items() if k != "markdown"}
        print()
        print(json.dumps(slim, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
