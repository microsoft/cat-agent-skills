# Agent Harness Capability Report

> Template for the Markdown report produced by
> `scripts/generate_markdown_report.py`. Placeholders in `{{ }}` are filled
> from a snapshot JSON file.

- **Observation date:** {{capturedAt}}
- **Snapshot ID:** `{{snapshotId}}`
- **Python version:** {{runtime.pythonVersion}}
- **Platform:** {{runtime.platform}}
- **Skill version:** {{skillVersion}}
- **Probe suite version:** {{probeSuiteVersion}}
- **Fingerprint:** `{{fingerprint}}`

## Capability summary

| Metric | Count |
| --- | ---: |
| Python libraries | {{summary.libraries}} |
| Uncataloged libraries | {{summary.uncataloged}} |
| Available capabilities | {{summary.available}} |
| Visible tools / skills / MCP | {{summary.visible}} |
| Restricted | {{summary.restricted}} |
| Unknown / unverified | {{summary.unknown}} |

## Runtime and environment capabilities

| Capability | Status | Value |
| --- | --- | --- |
| `{{capability.id}}` | {{capability.status}} | {{capability.value}} |

## Python libraries

> Full, category-grouped table lives in the library inventory produced by
> `scripts/generate_library_inventory.py`.

| Library | Version | Description | Documentation |
| --- | ---: | --- | --- |
| {{library.name}} | {{library.version}} | {{library.description}} | [Documentation]({{library.documentationUrl}}) |

## Comparison summary

_Present when compared against a previous snapshot (see
`scripts/compare_snapshots.py`)._

- Added: {{comparison.added}}
- Removed: {{comparison.removed}}
- Version changed: {{comparison.versionChanged}}
- Status changed: {{comparison.statusChanged}}
- Unverified: {{comparison.unverified}}
