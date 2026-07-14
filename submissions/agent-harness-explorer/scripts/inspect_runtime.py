#!/usr/bin/env python3
"""Runtime environment probe: OS, filesystem, subprocess, and network.

Safety levels follow the skill's safety boundaries:
- Passive by default: OS/platform metadata and temp-directory discovery.
- Active-safe (opt-in): create+delete a temp file, run a benign command,
  and perform a single HTTPS HEAD request to an approved endpoint.

Active-safe probes only run when explicitly requested:

    python inspect_runtime.py                 # passive only
    python inspect_runtime.py --active-safe   # include active-safe probes

Import and call `run(active_safe=False)` to embed in the capture pipeline.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
from datetime import datetime, timezone

PROBE_ID = "runtime-environment"
PROBE_VERSION = "0.1.0"

# Only a well-known, safe, high-availability endpoint is ever contacted.
APPROVED_ENDPOINT = "https://pypi.org"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _os_capabilities() -> list[dict]:
    return [
        {
            "id": "runtime.os",
            "status": "available",
            "value": platform.system(),
            "details": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "confidence": "high",
            "source": "runtime",
        }
    ]


def _filesystem_capabilities(active_safe: bool) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    tmp = tempfile.gettempdir()
    caps = [
        {
            "id": "runtime.filesystem:temp-dir",
            "status": "available" if os.path.isdir(tmp) else "unknown",
            "value": True if os.path.isdir(tmp) else None,
            "confidence": "high",
            "source": "runtime",
        }
    ]
    if active_safe:
        write_ok = False
        try:
            with tempfile.NamedTemporaryFile("w", delete=False) as fh:
                fh.write("agent-harness-explorer probe")
                path = fh.name
            write_ok = os.path.exists(path)
            os.remove(path)
        except Exception as exc:
            warnings.append(f"filesystem write probe failed: {exc}")
        caps.append(
            {
                "id": "runtime.filesystem:write",
                "status": "available" if write_ok else "restricted",
                "value": write_ok,
                "confidence": "high",
                "source": "active-safe",
            }
        )
    else:
        caps.append(
            {
                "id": "runtime.filesystem:write",
                "status": "unverified",
                "value": None,
                "confidence": "low",
                "source": "skipped",
            }
        )
    return caps, warnings


def _subprocess_capabilities(active_safe: bool) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    if not active_safe:
        return (
            [
                {
                    "id": "runtime.subprocess:exec",
                    "status": "unverified",
                    "value": None,
                    "confidence": "low",
                    "source": "skipped",
                }
            ],
            warnings,
        )
    ok = False
    try:
        import subprocess

        completed = subprocess.run(
            [sys.executable, "-c", "print('ok')"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        ok = completed.returncode == 0 and completed.stdout.strip() == "ok"
    except Exception as exc:
        warnings.append(f"subprocess probe failed: {exc}")
    return (
        [
            {
                "id": "runtime.subprocess:exec",
                "status": "available" if ok else "restricted",
                "value": ok,
                "confidence": "high",
                "source": "active-safe",
            }
        ],
        warnings,
    )


def _network_capabilities(active_safe: bool) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    if not active_safe:
        return (
            [
                {
                    "id": "runtime.network:https",
                    "status": "unverified",
                    "value": None,
                    "confidence": "low",
                    "source": "skipped",
                }
            ],
            warnings,
        )
    ok = False
    try:
        import urllib.request

        req = urllib.request.Request(APPROVED_ENDPOINT, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as resp:
            ok = 200 <= resp.status < 400
    except Exception as exc:
        warnings.append(f"network probe blocked or failed: {exc}")
    return (
        [
            {
                "id": "runtime.network:https",
                "status": "available" if ok else "restricted",
                "value": ok,
                "confidence": "medium",
                "source": "active-safe",
            }
        ],
        warnings,
    )


def run(active_safe: bool = False) -> dict:
    warnings: list[str] = []
    capabilities: list[dict] = []
    capabilities.extend(_os_capabilities())

    fs_caps, fs_warn = _filesystem_capabilities(active_safe)
    sp_caps, sp_warn = _subprocess_capabilities(active_safe)
    net_caps, net_warn = _network_capabilities(active_safe)
    capabilities += fs_caps + sp_caps + net_caps
    warnings += fs_warn + sp_warn + net_warn

    return {
        "probeId": PROBE_ID,
        "probeVersion": PROBE_VERSION,
        "capturedAt": _now(),
        "status": "success",
        "safetyLevel": "active-safe" if active_safe else "passive",
        "capabilities": capabilities,
        "warnings": warnings,
        "errors": [],
    }


def _main(argv: list[str]) -> int:
    active_safe = "--active-safe" in argv[1:]
    json.dump(run(active_safe=active_safe), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
