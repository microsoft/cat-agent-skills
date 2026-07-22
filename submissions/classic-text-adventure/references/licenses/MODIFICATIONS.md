# Modifications and bundle boundaries

The directory `scripts/runtime/adventure/` is copied verbatim from the Adventure 1.7 source distribution. No upstream file was modified.

All integration behavior is implemented outside that directory:

- `runtime_adapter.py` reconstructs the game from a seed and transcript, matches the traditional tokenizer, and redirects `save` to an in-memory buffer.
- `checkpoint.py` adds hashed atomic documents, locking, and journal persistence.
- `runner.py` adds the one-shot JSON protocol, session isolation, idempotency, recovery, and optional rendering.
- `render.py` adds deterministic text-card rendering.
- `smoke_test.py`, `smoke_cases.json`, and `tests/` add validation only.

The bundled JetBrains Mono font is also unmodified. Generated manifests identify every vendored file and its SHA-256 digest.

