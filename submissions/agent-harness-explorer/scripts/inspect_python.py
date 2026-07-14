#!/usr/bin/env python3
"""Python runtime and installed-package probe (passive, safe by default).

Emits a probe envelope describing the Python runtime and every installed
distribution. This is the highest-priority probe for the Agent Harness
Explorer. Run standalone:

    python inspect_python.py            # pretty JSON envelope
    python inspect_python.py --compact  # single-line JSON

Or import and call `run()` to get the envelope as a dict.
"""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone

PROBE_ID = "python-runtime-packages"
PROBE_VERSION = "0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _runtime_capabilities() -> list[dict]:
    return [
        {
            "id": "python.runtime",
            "status": "available",
            "value": platform.python_version(),
            "details": {
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "pythonVersion": platform.python_version(),
            },
            "confidence": "high",
            "source": "runtime",
        }
    ]


# Preference order for choosing a single home/docs URL from Project-URL labels.
_URL_LABEL_PRIORITY = (
    "documentation",
    "docs",
    "homepage",
    "home page",
    "home",
    "repository",
    "source",
    "source code",
)


def _clean_url(value: str) -> str:
    value = (value or "").strip()
    if value.lower() in ("", "unknown", "none", "n/a", "unknown/unknown"):
        return ""
    return value if value.startswith("http://") or value.startswith("https://") else ""


def _extract_metadata(dist) -> tuple[str, str]:
    """Return (summary, url) from a distribution's own metadata (offline)."""
    meta = dist.metadata
    summary = ""
    try:
        summary = (meta.get("Summary") or "").strip()
    except Exception:
        summary = ""
    if summary.lower() in ("unknown", "none", "n/a"):
        summary = ""

    # Collect candidate URLs keyed by lowercased label.
    candidates: dict[str, str] = {}
    try:
        for raw in meta.get_all("Project-URL") or []:
            if "," in raw:
                label, url = raw.split(",", 1)
            else:
                label, url = "homepage", raw
            url = _clean_url(url)
            if url:
                candidates.setdefault(label.strip().lower(), url)
    except Exception:
        pass
    home = _clean_url(meta.get("Home-page") or "")
    if home:
        candidates.setdefault("home page", home)

    for key in _URL_LABEL_PRIORITY:
        if key in candidates:
            return summary, candidates[key]
    # Fall back to any URL we found.
    for url in candidates.values():
        return summary, url
    return summary, ""


def _iter_distributions():
    """Yield distribution objects, de-duplicated by lowercased name."""
    try:
        from importlib import metadata as importlib_metadata  # py3.8+
    except ImportError:  # pragma: no cover - very old runtimes
        import importlib_metadata  # type: ignore

    seen = set()
    for dist in importlib_metadata.distributions():
        try:
            name = dist.metadata["Name"]
        except Exception:
            name = None
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        yield name, dist


def _package_capabilities() -> tuple[list[dict], list[str]]:
    caps: list[dict] = []
    warnings: list[str] = []
    try:
        for name, dist in sorted(_iter_distributions(), key=lambda p: p[0].lower()):
            summary, url = _extract_metadata(dist)
            caps.append(
                {
                    "id": f"python.package:{name.lower()}",
                    "name": name,
                    "version": dist.version or "",
                    "status": "installed",
                    "confidence": "high",
                    "source": "importlib.metadata",
                    "metaSummary": summary,
                    "metaUrl": url,
                }
            )
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"package enumeration failed: {exc}")
    return caps, warnings


def run() -> dict:
    """Execute the probe and return a normalized envelope."""
    warnings: list[str] = []
    errors: list[str] = []
    capabilities = list(_runtime_capabilities())

    packages, pkg_warnings = _package_capabilities()
    capabilities.extend(packages)
    warnings.extend(pkg_warnings)

    status = "success" if packages else "partial"
    return {
        "probeId": PROBE_ID,
        "probeVersion": PROBE_VERSION,
        "capturedAt": _now(),
        "status": status,
        "safetyLevel": "passive",
        "capabilities": capabilities,
        "warnings": warnings,
        "errors": errors,
    }


def _main(argv: list[str]) -> int:
    envelope = run()
    compact = "--compact" in argv[1:]
    if compact:
        json.dump(envelope, sys.stdout, separators=(",", ":"), ensure_ascii=False)
    else:
        json.dump(envelope, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
