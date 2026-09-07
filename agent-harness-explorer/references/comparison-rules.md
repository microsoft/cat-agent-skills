# Comparison Rules

The comparison engine (`scripts/compare_snapshots.py`) compares two normalized
snapshots by stable capability ID. These rules keep comparisons honest — a
probe that couldn't run must never masquerade as a capability that disappeared.

## Change types

| Type | Meaning |
| --- | --- |
| `added` | A capability ID present in the new snapshot but not the old. |
| `removed` | A capability ID present in the old snapshot, absent in the new, **and** its responsible probe actually ran. |
| `versionChanged` | Same capability ID, different package version. Highlighted prominently. |
| `statusChanged` | Same capability ID, different status (e.g. `available` → `restricted`). |
| `unverified` | Absent or newly `unknown`/`not-visible` because the responsible probe was skipped/failed/partial. |
| `probeChanged` | The probe suite version differs between snapshots. |

## Core rules

- **A failed or skipped probe is not proof of removal.** If a capability is
  missing from the new snapshot but the probe responsible for its namespace was
  `skipped`, `failed`, or `partial`, classify it as `unverified`.
- **A status flip into an unverified state is not a regression.** When a
  capability moves from a verified status to `unverified`/`not-visible`/
  `unknown` (e.g. an active-safe probe wasn't run this time), classify it as
  `unverified`, not `statusChanged`.
- **Probe version changes must be surfaced.** A changed `probeSuiteVersion`
  sets `probeChanged: true` so differences aren't mistaken for harness changes.
- **Package version changes are highlighted.** They are the most actionable
  signal for makers.
- **Catalog edits are not harness changes.** Description and documentation-URL
  differences come from the curated catalog and are excluded from the
  fingerprint and from behavior comparisons.

## Namespace → probe mapping

A missing capability is only a `removed` if the probe that would have observed
it actually ran. The comparator maps ID namespaces to probes:

| ID prefix | Responsible probe |
| --- | --- |
| `python.package:`, `python.runtime` | `python-runtime-packages` |
| `runtime.` | `runtime-environment` |
| `tool:`, `skill:`, `mcp.`, `tool.visibility` | `tool-mcp-visibility` |

## Output shape

```json
{
  "fromSnapshotId": "2026-07-06T15-10-02Z",
  "toSnapshotId": "2026-07-13T20-42-18Z",
  "identical": false,
  "probeChanged": false,
  "added": [],
  "removed": [],
  "versionChanged": [],
  "statusChanged": [],
  "unverified": []
}
```
