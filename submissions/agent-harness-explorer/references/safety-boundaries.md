# Safety Boundaries

The Agent Harness Explorer inspects the runtime; it must never modify it in
surprising ways or leak sensitive data. Safety is enforced at both the
instruction layer (this skill's SKILL.md) and the script layer.

## Probe safety levels

### Passive — may run by default
- Python version and implementation.
- Installed distribution enumeration and package metadata.
- Platform/OS metadata.
- Temp-directory discovery (existence only).
- Visible tool/skill/MCP metadata supplied by the agent.

### Active-safe — run only with a clear, brief explanation
- Create and delete a single temporary file.
- Execute one benign local command (`python -c "print('ok')"`).
- Make a single HTTPS `HEAD` request to an approved endpoint (`https://pypi.org`).
- Test importability of a specific module.

These are gated behind `--active-safe` in `inspect_runtime.py` /
`capture_snapshot.py`. They never run silently.

### Active-sensitive — require explicit user direction every time
- Installing packages.
- Contacting arbitrary external endpoints.
- Scanning directories or reading unrelated user files.
- Executing arbitrary shell commands.
- Testing credentials or authenticated connections.

The shipped scripts do **not** perform any active-sensitive action.

## Redaction rules

Never persist or display:
- Tokens, passwords, cookies, connection strings, private keys.
- Full environment-variable values.
- Private file contents.
- Sensitive, user-specific filesystem paths where avoidable.

Snapshots deliberately record only capability existence, status, versions, and
neutral metadata — not secrets.

## Cleanup guarantees

- The filesystem write probe deletes any temporary file it creates.
- No probe leaves residual state in the harness on success.

## Failure handling

- A probe that cannot observe something records `unknown`, `unverified`, or
  `not-visible` — never `unsupported`.
- Enumeration failures become `warnings`, not silent removals.
