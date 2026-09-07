# Modifications and bundle boundaries

The directory `scripts/runtime/adventure/` is copied from the Adventure 1.7 source distribution. Its otherwise empty `tests/__init__.py` package marker contains a comment because some skill hosts discard zero-byte files; no executable upstream code was changed.

All integration behavior is implemented outside that directory:

- `runtime_adapter.py` reconstructs the game from a seed and transcript, matches the traditional tokenizer, and redirects `save` to an in-memory buffer.
- `checkpoint.py` adds hashed atomic documents, locking, and journal persistence.
- `runner.py` adds the one-shot JSON protocol, session isolation, idempotency, and recovery.
- `smoke_test.py`, `smoke_cases.json`, and `tests/` add validation only.

Generated manifests identify every vendored file and its SHA-256 digest.
