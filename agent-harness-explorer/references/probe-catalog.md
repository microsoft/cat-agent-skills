# Probe Catalog

This file documents the probes shipped with the Agent Harness Explorer. Each
probe returns a common envelope (see `## Probe envelope` below) so results can
be normalized, fingerprinted, and compared consistently.

## Probe envelope

```json
{
  "probeId": "python-runtime-packages",
  "probeVersion": "0.1.0",
  "capturedAt": "2026-07-13T20:42:18Z",
  "status": "success",
  "safetyLevel": "passive",
  "capabilities": [],
  "warnings": [],
  "errors": []
}
```

| Field | Purpose |
| --- | --- |
| `probeId` | Stable probe identifier. |
| `probeVersion` | Version of the probe logic. |
| `capturedAt` | UTC timestamp. |
| `status` | `success`, `partial`, `failed`, or `skipped`. |
| `safetyLevel` | `passive`, `active-safe`, or `active-sensitive`. |
| `capabilities` | Normalized observations, each with a stable `id`. |
| `warnings` | Non-fatal issues. |
| `errors` | Failures or blocked behavior. |

## Stable capability IDs

| Pattern | Meaning |
| --- | --- |
| `python.runtime` | The Python interpreter itself. |
| `python.package:<name>` | An installed distribution (name normalized per PEP 503). |
| `runtime.os` | Operating system metadata. |
| `runtime.filesystem:<feature>` | e.g. `temp-dir`, `write`. |
| `runtime.subprocess:<feature>` | e.g. `exec`. |
| `runtime.network:<feature>` | e.g. `https`. |
| `tool:<name>` | A built-in agent tool. |
| `skill:<name>` | A loaded Agent Skill. |
| `mcp.server:<server>` | A visible MCP server. |
| `mcp.tool:<server>/<tool>` | A visible MCP tool. |

## Shipped probes

### `python-runtime-packages` — `inspect_python.py`
- **Safety:** passive. Runs by default.
- **Discovers:** Python version/implementation/platform and every installed
  distribution via `importlib.metadata`.
- **Notes:** This is the highest-priority probe. Package enumeration failures
  are recorded as warnings, never as removals.

### `runtime-environment` — `inspect_runtime.py`
- **Safety:** passive by default; opt-in `--active-safe` for the write,
  subprocess, and network sub-probes.
- **Discovers:** OS metadata and temp-dir (passive); temp-file write, benign
  subprocess execution, and a single HTTPS `HEAD` to an approved endpoint
  (active-safe only).
- **Notes:** When active-safe probes are not run, their capabilities are
  emitted with status `unverified` so comparisons don't misread them.

### `tool-mcp-visibility` — `inspect_tools.py`
- **Safety:** passive.
- **Discovers:** built-in tools, loaded skills, and MCP servers/tools — but
  only from an *observations* file the agent writes, because a plain Python
  process cannot see the agent's context.
- **Notes:** With no observations the probe returns `status: skipped` and a
  single `tool.visibility: not-visible` capability. Absence is treated as
  `unverified`, never `unsupported`.

## Adding a probe

1. Create `scripts/inspect_<thing>.py` exposing `run(...) -> envelope`.
2. Emit capabilities with stable IDs (add a new namespace above if needed).
3. Call it from `capture_snapshot.py` and merge its capabilities.
4. If it introduces a new namespace, map that namespace to the probe in
   `compare_snapshots.py` (`NAMESPACE_PROBE`) so skipped-probe absences are
   scored as `unverified`.
5. Bump `PROBE_SUITE_VERSION` in `capture_snapshot.py`.
