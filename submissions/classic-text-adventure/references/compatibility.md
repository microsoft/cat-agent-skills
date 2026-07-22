# Compatibility and host contract

## Supported implementation envelope

- Python 3, using only the standard library for gameplay, replay, checkpointing, locking, and the smoke harness.
- Host-supplied Pillow is required for the full supported envelope and optional PNG output. Missing or failed rendering never changes committed text or gameplay state, but the full smoke suite reports the degraded host as a failure.
- No runtime network access and no package installation.
- One Python process per runner invocation; no persistent subprocess or in-memory game state.
- A private writable state root outside the installed skill directory, with atomic replacement and advisory file locking available.
- UTF-8 JSON stdin/stdout and local file attachments when the host supports them.

Local implementation validation on 2026-07-22 used Windows, Python 3.14.0, and Pillow 12.3.0. Repository and bundled smoke tests are repeatable, but this is not evidence of Copilot Studio behavior.

## Copilot Studio release gate

The following host-contract checks have not yet been executed in a real Copilot Studio tenant and must be completed before claiming production support:

1. Upload and invoke a ZIP with root `SKILL.md` and bundled Python scripts.
2. Confirm the installed skill exposes a stable absolute skill root.
3. Confirm Python execution, stdin/stdout JSON, exit codes, and diagnostic stderr.
4. Identify a private persistent writable root and verify atomic replace plus cross-invocation file locking.
5. Measure execution timeout, memory, stdout/stderr, input, and attachment limits.
6. Confirm Pillow version and FreeType behavior without installation.
7. Confirm generated PNG files can be attached and determine whether multiple images are supported.
8. Confirm separate conversations cannot read or collide with each other's session identifiers.
9. Confirm imported root `metadata.json` and root `README.md` are excluded while all bundled support files remain intact.

Record tenant, region, host/runtime versions, observed limits, and evidence with the final pull request. Any failure in execution, persistent storage, locking, or isolation blocks release. Missing image attachment support permits text-only operation if disclosed.

## Operational limits

- Commands may not be blank and may not exceed 16,384 UTF-8 bytes.
- Session IDs are opaque ASCII identifiers of at most 64 characters; request IDs are at most 128 characters.
- Checkpoints deliberately contain the raw command transcript. Treat the state root as private user data and apply the host's retention policy.
- Render hashes are stable only for the same font, Pillow, FreeType, and zlib stack. Re-run the smoke suite after a host upgrade.
- The runner never deserializes upstream pickle saves. The in-game `save` command writes only to an in-memory buffer and is not the persistence mechanism.

## Smoke-test interpretation

Exit `0` means every selected case passed, `1` means one or more product checks failed, and `2` means the harness itself could not run. The JSON report is schema version 1 and includes stable issue codes. Feed every reported issue back to maintainers without including unrelated environment secrets or active-session data.
