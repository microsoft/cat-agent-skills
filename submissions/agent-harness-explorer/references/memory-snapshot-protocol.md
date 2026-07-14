# Memory Snapshot Protocol

Agent memory is the **default** persistence mechanism for snapshots. It
requires no maker setup and keeps history user-specific. External persistence
(SharePoint, Dataverse, GitHub, Blob) is always optional and only offered when
a compatible tool is visible.

## What to store in memory

Store the **compact** snapshot, not raw probe output. The compact record holds
only what comparison needs:

- `snapshotId`
- `capturedAt`
- `probeSuiteVersion`
- `fingerprint`
- Stable capability IDs with their `status` and (for packages) `version`

Never store secrets or raw environment values in memory.

## Memory record types

### Snapshot index
A single record tracking:
- `latestSnapshotId`
- `baselineSnapshotId`
- Known snapshot IDs with their timestamps and fingerprints
- Optional labels

### Compact snapshot
One per retained snapshot (fields listed above).

### Human summary
A short natural-language description of a snapshot and its most recent
comparison result.

## Baseline handling

- The user designates one snapshot as the **baseline** ("save this as my
  baseline").
- "Compare with my baseline" retrieves the baseline compact snapshot and
  compares it to a freshly captured one.

## Retention

Default recommendation (do not silently delete beyond this without asking):
- Keep the designated baseline.
- Keep the latest eight weekly snapshots.
- Keep one monthly snapshot for older history.

## Retrieval and comparison workflow

1. On "capture a snapshot", retrieve the latest compact snapshot from memory.
2. Capture the current snapshot with the probe suite.
3. Compare the two by stable capability ID.
4. Store the new compact snapshot and update the snapshot index.
5. Present the change summary.

## Fingerprints

The fingerprint (`sha256:...`) is computed over the canonical, volatile-field-
stripped capability set (see `scripts/canonicalize_snapshot.py`). Identical
fingerprints mean the observable capability set is unchanged — a fast way to
answer "did anything change since last week?" before diffing in detail.

## Durability caveat

Always remind users that agent memory is user-specific and may not be durable
or shareable. Encourage **exporting** snapshots (JSON + Markdown) for durable
or team-shared retention.
