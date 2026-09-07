#!/usr/bin/env python3
"""Tool / Agent Skill / MCP visibility probe.

A plain Python process cannot see the agent's tools, loaded skills, or MCP
servers — only the agent (model) can enumerate those from its own context.
This probe therefore accepts an *observations* file that the agent writes
based on what it can currently see, and normalizes it into capabilities.

    # Agent writes observations.json, then:
    python inspect_tools.py --input observations.json

With no input, the probe returns a `skipped` envelope whose capabilities are
marked `not-visible` (never `unsupported`) so comparisons treat them as
`unverified` rather than removals.

observations.json shape (all keys optional, all lists of strings — except
mcpTools which is a list of {server, tool}):

    {
      "tools": ["view", "edit", "grep"],
      "skills": ["pdf", "xlsx"],
      "mcpServers": ["github-mcp-server", "playwright"],
      "mcpTools": [{"server": "playwright", "tool": "browser_click"}]
    }
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

PROBE_ID = "tool-mcp-visibility"
PROBE_VERSION = "0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(value: str) -> str:
    return str(value).strip()


def capabilities_from_observations(obs: dict) -> list[dict]:
    caps: list[dict] = []
    for tool in obs.get("tools", []) or []:
        caps.append(
            {
                "id": f"tool:{_slug(tool)}",
                "name": _slug(tool),
                "status": "available",
                "confidence": "high",
                "source": "agent-observed",
            }
        )
    for skill in obs.get("skills", []) or []:
        caps.append(
            {
                "id": f"skill:{_slug(skill)}",
                "name": _slug(skill),
                "status": "available",
                "confidence": "high",
                "source": "agent-observed",
            }
        )
    for server in obs.get("mcpServers", []) or []:
        caps.append(
            {
                "id": f"mcp.server:{_slug(server)}",
                "name": _slug(server),
                "status": "available",
                "confidence": "high",
                "source": "agent-observed",
            }
        )
    for item in obs.get("mcpTools", []) or []:
        server = _slug(item.get("server", ""))
        tool = _slug(item.get("tool", ""))
        caps.append(
            {
                "id": f"mcp.tool:{server}/{tool}",
                "name": f"{server}/{tool}",
                "status": "available",
                "confidence": "high",
                "source": "agent-observed",
            }
        )
    return caps


def run(observations: dict | None = None) -> dict:
    if not observations:
        return {
            "probeId": PROBE_ID,
            "probeVersion": PROBE_VERSION,
            "capturedAt": _now(),
            "status": "skipped",
            "safetyLevel": "passive",
            "capabilities": [
                {
                    "id": "tool.visibility",
                    "status": "not-visible",
                    "value": None,
                    "confidence": "low",
                    "source": "no-observations",
                }
            ],
            "warnings": [
                "No observations provided; the agent must enumerate tools, "
                "skills, and MCP servers from its own context."
            ],
            "errors": [],
        }
    caps = capabilities_from_observations(observations)
    return {
        "probeId": PROBE_ID,
        "probeVersion": PROBE_VERSION,
        "capturedAt": _now(),
        "status": "success" if caps else "partial",
        "safetyLevel": "passive",
        "capabilities": caps,
        "warnings": [],
        "errors": [],
    }


def _main(argv: list[str]) -> int:
    observations = None
    args = argv[1:]
    if "--input" in args:
        path = args[args.index("--input") + 1]
        with open(path, encoding="utf-8") as fh:
            observations = json.load(fh)
    json.dump(run(observations), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
