# Snapshot history

Timestamped, browsable harness captures kept so past state can be **referenced
and reviewed without regenerating a fresh report**.

Each capture is written as a matched set that shares one date-based name:

```
2026-07-14-agent-harness-snapshot.json   # canonical snapshot (source of truth)
2026-07-14-agent-harness-snapshot.md     # Markdown inventory (diff-friendly review)
2026-07-14-agent-harness-snapshot.html   # self-contained visual report
```

A second capture on the same day gets a `-2`, `-3`, ... suffix so nothing is
overwritten. An `index.md` lists every capture (newest first) with library
counts and the snapshot fingerprint. Historical files are **never overwritten**
— they are the record of how the harness changed over time.

## Generate a capture

```bash
python scripts/archive_snapshot.py --out-dir <archive-folder>
# from an existing snapshot, or a subset of formats:
python scripts/archive_snapshot.py --snapshot snapshot.json --out-dir <folder>
python scripts/archive_snapshot.py --out-dir <folder> --formats json,md
```

## Where captures live

This folder ships in the published skill bundle, so it holds only **one or a few
representative example captures** for reviewers. Point `--out-dir` here when
producing that example.

For an ongoing, growing archive, pass an `--out-dir` **outside** the published
bundle (e.g. a `snapshot-archive/` folder in your own repo or reports area) so
the gallery skill stays lean.
