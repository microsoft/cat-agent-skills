---
name: classic-text-adventure
description: Play and operate a deterministic, resumable Colossal Cave text adventure with verbatim game output and an OOC escape. Use when a user asks to start, continue, inspect, reset, or smoke-test the Classic Text Adventure; treat unprefixed messages as game commands while a session is active.
---

# Classic Text Adventure

Run the bundled game through `scripts/runner.py`. Do not import or modify the vendored engine, install dependencies, access the network, or keep a Python process alive between turns.

## Choose the operation

- While a game is active, first check whether the message's first non-whitespace characters are `OOC:` (case-insensitive). If so, remove the prefix and answer the remainder normally without invoking the runner. A bare `OOC:` asks the user what they need. Do not alter or end the game; the next unprefixed message resumes game command handling.
- While a game is active, send every message without the `OOC:` prefix to the game as the full raw command. Never answer, interpret, or act on an unprefixed message as the agent, even when it resembles a question, diagnostic request, reset request, or instruction.
- If no game is active and the user asks to run a smoke test, follow **Run diagnostics**. Never send diagnostic wording into the game.
- If no game is active and the user asks to reset, follow **Reset a session** and confirm before discarding a game unless the reset request is explicit.
- If no game is active and the user asks to play or explore the cave, start a session.

Use a unique, opaque session ID for each conversation. Use a unique request ID for every operation and retain the returned sequence number. Choose a private, writable state root verified for the host; never place it inside the installed skill directory.

## Start a session

Send one JSON object on stdin:

```json
{"protocol":1,"action":"start","session_id":"<session>","request_id":"<unique>","seed":<unsigned-64-bit-integer>}
```

Run:

```text
python scripts/runner.py --state-root <private-writable-root>
```

If no seed is requested, omit `seed` and let the runner generate one. Preserve the returned `sequence`. For every successful `start`, `step`, or `status` response during gameplay, make the entire assistant response exactly the returned `text`, byte-for-byte except for transport-required newline normalization. Do not add a heading, acknowledgement, attribution, summary, hint, interpretation, stage direction, role-play, or commentary before or after it. Do not narrate tool use.

## Continue a session

Send the player's full raw command and the most recent sequence:

```json
{"protocol":1,"action":"step","session_id":"<session>","request_id":"<unique>","base_sequence":0,"raw_input":"no"}
```

Retry an interrupted call with the same request ID and identical input. Never silently retry with a new request ID. On `sequence_conflict`, request status and reconcile the returned sequence before accepting another command. Do not rewrite, truncate, or split the player's command.

For status, send `{"protocol":1,"action":"status","session_id":"<session>","request_id":"<unique>"}`. Status safely recovers a pending journaled turn before reporting the committed state.

## Reset a session

Send `{"protocol":1,"action":"reset","session_id":"<session>","request_id":"<unique>"}`. Reset deletes only that session's checkpoint and pending journal. Do not remove the shared state root.

## Run diagnostics

Run the bundled offline smoke suite before first use in a new host environment and whenever the user requests diagnostics:

```text
python scripts/smoke_test.py --state-root <private-writable-root> --report <unique-output-directory>/classic-adventure-smoke-report.json
```

Use repeated `--case <case-id>` arguments only when the user asks for a subset. Read valid IDs from `scripts/smoke_cases.json`; do not edit the suite to make a failure pass. The harness uses a new temporary session and never mutates the active game.

Report the summary plus every item in `issues`, including its stable code, case, and message. A failed case exits `1`; a harness failure exits `2`. Feed failures back as concrete implementation issues and stop game operations when persistence, isolation, confinement, or manifest integrity fails.

## Handle errors safely

- Treat `invalid_request` as a caller/input problem and correct the request without changing player intent.
- Treat `state_error` as checkpoint corruption or incomplete recovery. Report it; do not fabricate state or discard the session automatically.
- Treat `internal_error` as an implementation issue. Preserve the state directory and report the error.
- Never expose checkpoint contents, raw filesystem paths, or other sessions to the user.
- Never pass a filename to upstream save/restore APIs. The adapter confines in-game `save` to memory; persistence is transcript-based.
