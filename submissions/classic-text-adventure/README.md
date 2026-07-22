# Classic Text Adventure

A deterministic, resumable packaging of Brandon Rhodes's Python port of the classic Colossal Cave Adventure for Copilot Studio skills.

The skill stores an unsigned 64-bit seed and raw command transcript, reconstructing the game for each turn. It includes hashed atomic checkpoints, request idempotency, session isolation, in-memory save interception, optional deterministic PNG rendering, and an offline agent-invokable smoke suite.

## Operation

The installed agent invokes `scripts/runner.py` once per request with a protocol-v1 JSON object on stdin. `start`, `step`, `status`, and `reset` are the only actions. A turn is accepted only when its `base_sequence` matches the latest committed sequence, and a retried request ID must carry byte-for-byte equivalent input.

Checkpoints and pending journals live beneath a host-verified private writable state root, outside the installed skill. They contain the seed and raw player transcript, so apply the host's user-data retention policy. `reset` removes only the named session's checkpoint, journal, and images.

The native command `save <filename>` deliberately returns Adventure's `GAME SAVED` text but writes only to an in-memory buffer. It does not create a named save slot; automatic transcript checkpoints are the sole restore mechanism.

## Diagnostics

Ask the installed agent to “run the Classic Text Adventure smoke test,” or invoke it directly:

```text
python scripts/smoke_test.py --state-root <private-root> --report <unique-output>/classic-adventure-smoke-report.json --json-summary
```

The nine offline cases use a new temporary session and do not inspect, advance, reset, or expose an active game. Exit `0` means all selected cases passed, `1` reports product failures, and `2` reports a harness failure. The JSON report's stable `issues` entries are intended to be fed back to maintainers for resolution. Use repeated `--case CTA-SMOKE-...` arguments to run a requested subset from `scripts/smoke_cases.json`.

## Local validation

```text
python submissions/classic-text-adventure/scripts/generate_license_manifest.py
python -m unittest discover -s submissions/classic-text-adventure/scripts/tests -v
python submissions/classic-text-adventure/scripts/smoke_test.py --state-root .smoke-state --report .smoke-state/classic-adventure-smoke-report.json
npm run check:submissions
```

Pillow must be supplied by the host to produce PNG cards. Gameplay and persistence use only Python's standard library. No runtime network access or package installation is performed.

Copilot Studio host-contract validation remains a release gate; see `references/compatibility.md`.
