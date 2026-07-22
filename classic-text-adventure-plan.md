# Classic Text Adventure Skill for Copilot Studio — Implementation Plan

## Status and outcome

Build an unpacked gallery submission at `submissions/classic-text-adventure/`.
The gallery importer will turn it into a deterministic ZIP containing a
root-level `SKILL.md` and its supporting files. The skill will run the original
350-point Colossal Cave Adventure offline in the new Copilot Studio experience,
return the game's text without paraphrasing, and attach a deterministic themed
PNG containing the same output on every successful turn.

This plan is ready to execute in the order below. Production implementation is
conditional on the Phase 0 host-contract tests and the licensing release gate.
Those are genuine go/no-go gates: current Microsoft documentation confirms that
a skill ZIP may contain scripts, but does not promise sticky skill activation,
byte-exact access to the current user message, cross-turn filesystem lifetime,
stable conversation/request identifiers, or inline delivery of script-created
PNGs.

The supported target is one game per conversation in the Preview chat of the
new Copilot Studio experience. Other channels, classic Copilot Studio agents,
multiplayer games, natural-language command interpretation, and cross-
conversation cloud saves are out of scope for version 1.

## Fixed decisions

- Use `adventure` 1.7, Brandon Rhodes's Python port of the 350-point game, if
  the licensing gate passes.
- Source the vendored package from `adventure-1.7.tar.gz` on PyPI and verify its
  SHA-256 before extraction:
  `fba584064d3b8b1ef6b62f6df6099092522d6bd3bce0525db002c54dc29ac6a1`.
- Copy the upstream `adventure/` package tree without code changes. Keep all
  adapter, transport, checkpoint, and rendering code outside that tree.
- Use a single-shot runner for every turn, with a durable checkpoint after each
  command. Do not depend on a long-lived subprocess; Copilot Studio does not
  currently document that lifecycle contract.
- Reconstruct the game on each invocation from a fixed per-game random seed and
  the committed raw-command transcript. Do not use upstream pickle saves for
  automatic state: several pending-question callbacks are local functions and
  are not a reliable serialization boundary.
- Use Python 3 and the standard library for the runtime. Use host-supplied Pillow
  only for rendering. Do not install packages or make runtime network requests.
- Bundle JetBrains Mono Regular from the JetBrains Mono 2.304 release under
  OFL-1.1. Record and verify the exact font file SHA-256 during vendoring.
- Use only code-drawn, MIT-licensed theme decoration. Do not include logos,
  screenshots, AI-generated artwork, or other visual assets.
- Treat text as the primary result. A rendering failure must never change,
  delay, or suppress the game text.
- `metadata.json` and the root `README.md` are human-facing sidecars and do not
  enter the ZIP. All required licenses and notices therefore live under
  `references/licenses/`, which is bundled.

## Phase 0 — prove the Copilot Studio host contract

Create a minimal throwaway probe skill before implementing or vendoring the
game. Record the Copilot Studio build/version, test date, observed tool schemas,
commands, outputs, and screenshots in the eventual PR description. Delete the
probe before creating the submission.

The spike must prove all of the following in a real new-experience Preview
conversation:

1. A ZIP with root `SKILL.md` and a bundled Python script uploads and the agent
   can execute the script from the installed skill.
2. The script can read and atomically replace files in a known writable directory
   that persists for at least 25 sequential chat turns. Determine the directory
   from observation; do not assume `/tmp`, `/app/workspace`, the skill directory,
   or the current working directory is writable or durable.
3. Separate Preview conversations either receive isolated writable storage or
   expose a stable conversation identifier that is safe to use as a state key.
4. Each user message exposes a stable request/message identifier, including on a
   retry, so an acknowledged command can be deduplicated. If no such identifier
   exists, confirm that the host guarantees one tool execution per user turn;
   otherwise exactly-once behavior is not supportable.
5. After activation, at least 25 deliberately ambiguous game commands (`n`,
   `look`, `get lamp`, `xyzzy`, `quit`, `no`) are routed back through the skill
   without the orchestrator switching modes or answering them itself.
6. Sentinel inputs containing leading/trailing spaces, repeated spaces, quotes,
   backslashes, punctuation, mixed case, Unicode, and embedded newlines reach the
   runner unchanged. Compare code points or UTF-8 bytes at the runner boundary;
   do not judge this by visual inspection of chat text.
7. Text returned from a script can be emitted without a preface, summary,
   Markdown fence, corrected spelling, or normalized internal whitespace.
8. A script-created PNG can be attached inline in Preview on the same turn as
   text. Verify whether more than one PNG can be attached and determine the
   maximum accepted file size/dimensions.
9. Python and Pillow are available without installation. Record exact versions,
   OS, architecture, writable-path behavior, and whether subprocess execution is
   available, even though the design does not require a persistent subprocess.

Go only if items 1–3 and 5–9 pass. Item 4 must pass for the exactly-once claim;
if it does not, remove that claim and document at-least-once behavior before
implementation. If item 6 fails, the project may continue only after changing
all user-facing wording from “unchanged” or “verbatim input” to a precise,
tested best-effort limitation. Do not hide a failed capability behind prompt
instructions.

## Phase 1 — licensing and supply-chain gate

### Selected candidate

Use `adventure` 1.7 only after the repository maintainer accepts the evidence.
PyPI identifies the Python engine as Apache-2.0 and contains the upstream
author's statement that `advent.dat`, the original source, and copied original
phrases are public domain. Treat the Python engine and historical game content
as separate components in every inventory and analysis; the Apache license on
the engine does not itself license the game text.

Vendor the entire upstream `adventure/` directory from the verified source
archive so that the engine, data, upstream README, and upstream tests remain an
auditable unit. Do not include the archive, packaging/build files, or an
installed dependency. Generate a per-file SHA-256 manifest after extraction and
assert that each copied file matches the source archive.

### Rejected fallbacks

Document these candidates even though they are not the implementation path:

1. Open Adventure 1.22: BSD-2-Clause C implementation of the 430-point game;
   rejected because using it would require either a native executable that the
   target host is not guaranteed to run or a new Python port with much higher
   regression and licensing-review cost.
2. A fresh port of the original 350-point source/data: rejected because it adds
   substantial implementation risk and does not improve the historical-content
   provenance question.

No GPL, noncommercial, freeware-only, source-available, or unclear-license game,
interpreter, font, or artwork may be incorporated.

### Bundled license material

Create:

- `references/licenses/Apache-2.0.txt` — exact upstream Apache license.
- `references/licenses/adventure-NOTICE.md` — upstream copyright, source archive
  name/URL/hash, copied paths, public-domain statement for historical content,
  modification status, and retrieval date. State that no upstream `NOTICE` file
  was found if that is what the verified archive shows; do not invent one.
- `references/licenses/MIT.txt` — copy of this repository's MIT license covering
  the new wrapper, smoke-test harness/cases, tests, manifest generator, and
  procedural visuals.
- `references/licenses/OFL-1.1.txt` — exact font license.
- `references/licenses/font-NOTICE.md` — font version, upstream URL, exact source
  filename, SHA-256, copyright, bundled path, and modification status.
- `references/licenses/THIRD_PARTY_MANIFEST.json` — generated file-level origin,
  copyright, license, modification status, and SHA-256 inventory.
- `references/licenses/BUNDLE_MANIFEST.json` — every bundled file's origin,
  license, and SHA-256, excluding the manifest itself to avoid a self-hash cycle.
- `references/licenses/MODIFICATIONS.md` — explicitly say whether any upstream
  files were modified; normally “none.”

The licensing gate passes only when the maintainer accepts redistribution of
both the Python code and historical content, all notices are present in the
downloadable bundle, and every redistributed byte appears in the manifest.

## Phase 2 — submission layout

Create exactly this shape:

```text
submissions/classic-text-adventure/
├── metadata.json                         # gallery sidecar; not bundled
├── README.md                             # human guide; not bundled
├── SKILL.md                              # root of generated ZIP
├── assets/
│   └── fonts/
│       └── JetBrainsMono-Regular.ttf
├── references/
│   ├── compatibility.md                  # verified host/runtime envelope
│   └── licenses/
│       ├── Apache-2.0.txt
│       ├── MIT.txt
│       ├── OFL-1.1.txt
│       ├── adventure-NOTICE.md
│       ├── font-NOTICE.md
│       ├── MODIFICATIONS.md
│       ├── THIRD_PARTY_MANIFEST.json
│       └── BUNDLE_MANIFEST.json
└── scripts/
    ├── runner.py                         # one JSON request -> one JSON response
    ├── runtime_adapter.py                # upstream Game wrapper
    ├── checkpoint.py                     # locking, journal, atomic commit
    ├── render.py                         # deterministic PNG renderer
    ├── smoke_test.py                     # agent-invokable installed-skill check
    ├── smoke_cases.json                  # versioned smoke-test definitions
    ├── generate_license_manifest.py
    ├── tests/
    │   ├── test_runtime_adapter.py
    │   ├── test_runner.py
    │   ├── test_checkpoint.py
    │   ├── test_render.py
    │   ├── test_smoke_test.py
    │   └── fixtures/
    └── runtime/
        └── adventure/                    # verbatim tree from 1.7 source archive
```

Do not add a ZIP, root-level changelog, PR notes, cache, generated game state,
`__pycache__`, or local screenshots to the submission. The importer packages
every file except the root `metadata.*` and optional root `README.md` verbatim.

Before implementation is complete, replace all metadata placeholders with the
actual contributor name and URL. Use only `platforms: ["Copilot Studio"]`, a
kebab-case `name: classic-text-adventure` in `SKILL.md`, lowercase catalog tags,
and a semantic version in `metadata.json`.

## Phase 3 — runtime and transport contract

### Adapter API

`runtime_adapter.py` exposes:

```python
start(seed: int | None = None) -> tuple[bytes, RuntimeResult]
step(state: bytes, raw_input: str) -> tuple[bytes, RuntimeResult]
inspect_state(state: bytes) -> SceneState
```

`RuntimeResult` is an immutable record containing:

```python
text: str          # exact upstream output; no wrapper prose
finished: bool     # upstream Game.is_finished
scene_key: str     # surface | cave | darkness | danger | endgame
```

`state` is canonical UTF-8 JSON containing only a schema version,
`adventure-1.7`, a generated 64-bit seed, and the ordered raw-command
transcript. Validate every field and bound before replay. To restore, create a
fresh `Game(seed)`, load the vendored data, call `start()`, and replay the
transcript through the adapter. A fixed seed makes the upstream random stream
reproducible, so the reconstructed inventory, score, pending question, deaths,
turn counters, hazards, and cave-closing state must match uninterrupted play.
Return only the newest command's output. Never use `pickle.loads()` or accept a
state/save blob from chat, an attachment, or an arbitrary path.

Pass `raw_input` unchanged into the adapter and append it to the state only after
a successful turn. At the game-parser boundary only, apply the same tokenization
and case handling as upstream 1.7 traditional mode. One chat message is one game
command; multiline or commands producing more than two tokens receive the
upstream “not understood” behavior rather than LLM interpretation. Reject a
blank/whitespace-only input with `empty_input` and any input over 16,384 UTF-8
bytes with `input_too_large`; neither error advances state.

The upstream `save <filename>` command is a special safety case. Preserve the
command and its upstream output, but replace the filename token at the engine
boundary with a fresh in-memory `io.BytesIO`; never let a user-supplied filename
reach a filesystem API. Discard the resulting upstream pickle bytes. Automatic
transcript checkpoints are the only supported restore mechanism, and the README
must explain that a native “GAME SAVED” confirmation does not create a named
cross-conversation save slot.

### Runner protocol

`runner.py` is invoked once per chat turn. It reads exactly one UTF-8 JSON object
from stdin, writes exactly one compact UTF-8 JSON object plus `\n` to stdout,
and writes diagnostics only to stderr. It has four actions:

```json
{"protocol":1,"action":"start","session_id":"...","request_id":"..."}
{"protocol":1,"action":"step","session_id":"...","request_id":"...","base_sequence":0,"raw_input":"..."}
{"protocol":1,"action":"status","session_id":"...","request_id":"..."}
{"protocol":1,"action":"reset","session_id":"...","request_id":"..."}
```

A successful response is:

```json
{
  "protocol": 1,
  "ok": true,
  "session_id": "...",
  "request_id": "...",
  "sequence": 0,
  "text": "WELCOME TO ADVENTURE!!  WOULD YOU LIKE INSTRUCTIONS?\n",
  "finished": false,
  "scene_key": "surface",
  "image_paths": [".../classic-adventure-t0000-p01.png"],
  "replayed": false
}
```

An operational failure returns `ok: false`, a stable machine-readable error
code, and a short safe message; it never fabricates game text. Never include a
traceback, environment value, state blob, filesystem root, or user input in the
chat-facing error.

Validate `session_id` and `request_id` against a conservative length and
character allowlist before using them. Derive each state path beneath the
Phase 0-verified writable root, resolve it, and prove it remains beneath that
root. Create directories and private files with restrictive permissions.

### Transaction and recovery rules

For each session, hold an exclusive lock for the entire request. The committed
checkpoint contains protocol/schema version, runtime version, sequence,
request ID, hash of the exact input, seed, ordered raw-command transcript,
exact response text, finished/scene fields, image status, and planned image
paths. Validate `base_sequence` against the current committed sequence before
applying a new command.

For `step`:

1. Acquire the session lock and read the last valid committed checkpoint.
2. If `request_id` matches the last committed request, require the same input
   hash and return the cached response with `replayed: true` without advancing
   the game.
3. Write and fsync a same-directory pending journal containing the pre-turn
   transcript, exact new raw input, input hash, base sequence, and request ID.
4. Reconstruct the pre-turn game, apply the command exactly once, and capture
   the new transcript and response.
5. Atomically write/fsync/replace the committed checkpoint, then fsync its parent
   directory and remove the pending journal.
6. Render images from the committed response into the planned paths. Atomically
   write each PNG and then mark image status complete. Image failure is logged
   and returns an empty image list; it does not roll back or replay the game
   turn. A duplicate retry may regenerate missing images but never reapply the
   command.

On startup, validate schema and hashes. If a pending journal exists without a
commit for its request, restore its pre-turn state and safely retry that request.
If the committed checkpoint is corrupt, do not replay it or silently start a new
game; return a recoverable corruption error and retain the files for diagnosis.
Reject concurrent or out-of-order requests rather than guessing.

`start` creates sequence 0 and returns the initial game question. The activation
message is never used as a game command. A second `start` on an unfinished
session returns its cached current response; `reset` is the only destructive
restart and is used only after an explicit user request. Routing stops when
`finished` is true. A later explicit “play again” creates a fresh game through
`reset` followed by `start`.

## Phase 4 — deterministic PNG rendering

Render only from the committed `RuntimeResult`; never ask the model to choose a
theme or rewrite text.

- Canvas: 1280 × 960 RGB pixels.
- Font: bundled `JetBrainsMono-Regular.ttf`, 28 px.
- Margins: 56 px; fixed line height: 38 px.
- Text color and procedural border/background palette come from `scene_key`.
- Preserve every output character and blank line. Wrap visually only at Unicode
  code-point boundaries and never insert, delete, or replace characters in the
  source `text`.
- Paginate at line boundaries. Use filenames
  `classic-adventure-t{sequence:04d}-p{page:02d}.png`; sequence numbers make
  every delivered path unique.
- Draw no text other than the runtime output. Theme decoration is geometric and
  cannot obscure the text area.
- Save as PNG with explicit mode, dimensions, compression level, and
  `optimize=False`; omit timestamps and variable metadata.
- Define determinism as byte-identical output on the pinned test stack and
  pixel-identical output on the verified host stack. Pillow or zlib upgrades may
  change compressed bytes without changing pixels, so record both a file hash
  and a decoded-pixel hash in tests.
- If Phase 0 shows that only one image can be returned, concatenate pages into
  one vertically stacked PNG only while it remains within the measured host
  limits. Otherwise return the first page and expose the complete text in chat;
  document the image pagination limitation.

Select `scene_key` from engine state with a fixed precedence: `endgame` when
finished/closing, then `danger` for active dwarf/pirate or immediate hazard,
then `darkness`, then `surface` for above-ground rooms, otherwise `cave`. Tests
must cover every branch.

## Phase 5 — `SKILL.md`, README, and catalog behavior

### Agent-invokable smoke test

Bundle `scripts/smoke_test.py` so a maker can ask the installed skill to “run
the Classic Text Adventure smoke test” directly in the agent. This is a
diagnostic mode, not a game command. It must work before a game starts, during
an active game, and after game over without reading, changing, resetting, or
advancing the user's real session.

The smoke test runs entirely offline against a new fixed-seed session in a
private temporary directory beneath the Phase 0-verified writable root. It must
clean up that directory on success and failure, except for the final report
artifact. It may not download anything, install packages, contact telemetry,
open an external issue, include secrets/environment values, or inspect other
conversation state. Set a default overall timeout of 30 seconds and terminate
individual cases cleanly when their budget expires.

This is a fast installed-package diagnostic, not a substitute for the complete
unit, integration, fault-injection, licensing, repository, or host acceptance
tests. Passing it means the deployed skill's critical path works in the current
agent environment; it does not expand the documented support envelope.

Keep the ordered, versioned case definitions in `scripts/smoke_cases.json` and
cover at least:

1. Bundle integrity: required files exist and every applicable entry in
   `BUNDLE_MANIFEST.json` and `THIRD_PARTY_MANIFEST.json` matches its SHA-256.
2. Runtime imports: the vendored engine, wrapper modules, Pillow, and bundled
   font load; record safe version identifiers in the report.
3. Startup and gameplay: verify the fixed-seed initial prompt, instructions,
   movement, inventory, an invalid command, a pending yes/no question, and quit
   confirmation against exact expected text.
4. Replay and persistence: separate runner invocations reconstruct the same
   state and output from the committed transcript.
5. Idempotency: a repeated request ID with identical input returns the cached
   result, while the same ID with different input returns the expected conflict
   without advancing state.
6. Session isolation: two temporary session IDs cannot read or alter each
   other's sequence, transcript, response, or images.
7. Save confinement: `save` inputs containing absolute or traversal paths
   produce the upstream game response without creating a file at the requested
   path.
8. Rendering: create at least one PNG, validate its dimensions/mode and decoded
   pixel hash, rerender it, and confirm deterministic pixels.
9. Recovery sanity: leave a controlled pending journal, invoke recovery, and
   prove that the command is committed once.

Each case has a stable ID such as `CTA-SMOKE-RUNTIME-001`, a description,
timeout, prerequisites, and expected result. Required cases fail rather than
skip when a promised dependency or capability is absent. Cases may be skipped
only when they exercise an explicitly optional Phase 0 capability, and every
skip must name that capability.

Invoke the harness with one command whose output location is unique to the
current request:

```bash
python scripts/smoke_test.py \
  --state-root <verified-writable-root> \
  --report <unique-output-path>/classic-adventure-smoke-report.json \
  --json-summary
```

Exit `0` only when all required cases pass, `1` when one or more cases fail,
and `2` when the smoke-test harness itself cannot run. Write progress and
diagnostics only to stderr. Write one compact summary object to stdout and the
complete UTF-8 JSON report atomically to `--report`, even when tests fail.

The report schema contains:

```json
{
  "schema_version": 1,
  "suite_version": "1.0.0",
  "overall_status": "pass|fail|error",
  "environment": {"python": "...", "pillow": "...", "platform": "..."},
  "summary": {"total": 9, "passed": 9, "failed": 0, "skipped": 0},
  "cases": [
    {"id": "CTA-SMOKE-RUNTIME-001", "status": "pass", "duration_ms": 0,
     "message": "..."}
  ],
  "issues": []
}
```

For every failure or harness error, add an `issues[]` entry with a stable issue
code, failing case ID, component, concise symptom, sanitized expected/observed
evidence, exact reproduction command, likely cause when known, and a concrete
next diagnostic or fix. Include only exception types and skill-relative stack
frames; exclude absolute paths, raw environment values, state transcripts,
user messages, and secrets. Keep case ordering and issue ordering deterministic
so two reports can be diffed.

When invoked through `SKILL.md`, the agent must run the suite once, return a
short pass/fail count, list each failure by issue code and next action, and
attach the JSON report when the host permits. It must not paraphrase away
expected/observed evidence or claim a failed case passed. If report attachment
is unavailable, present the sanitized `issues[]` entries in chat. The feedback
stays in the current conversation; sending telemetry or filing an external
issue requires a separate explicit user request.

`SKILL.md` must instruct the agent to:

1. Activate when the user explicitly starts the adventure, on every follow-up
   message in the same active game conversation, or when the user asks to run
   the bundled smoke test.
2. Treat a smoke-test request as diagnostic control input: run
   `scripts/smoke_test.py`, report its result as specified above, and never pass
   that request to the game or mutate an active game session.
3. Resolve the verified session and request IDs; never invent reusable global
   IDs or combine two conversations.
4. Call `start` when no game exists. Do not feed the activation request to the
   game.
5. For an active game, place the current user message unchanged in `raw_input`
   and call `step` exactly once.
6. When `ok: true`, emit the `text` field first and exactly, without Markdown
   fences, labels, commentary, spelling changes, or whitespace normalization;
   then attach every returned image path.
7. Never answer a game command itself, suggest a command unless the engine does,
   translate input/output, summarize output, or use general knowledge to alter
   gameplay.
8. Stop unconditional routing only after `finished: true`. Handle an explicit
   restart through `reset`, not by deleting files directly.
9. On `ok: false`, report the safe operational error and recovery action; never
   pretend it is game output.

The human `README.md` covers upload steps, supported Preview target, activation
examples, one-message/one-command semantics, automatic checkpointing, image
behavior, how to invoke and interpret the smoke test, tested environment,
privacy/storage behavior, reset behavior, limitations from Phase 0,
architecture, and a plain-language licensing summary. It must not claim support
for untested channels or promise persistent saves beyond the observed container
lifetime.

`metadata.json` supplies the human display name and catalog description,
`platforms: ["Copilot Studio"]`, lowercase search tags, actual contributor
attribution, semantic version, and dates. Do not add importer-owned fields such
as `bundle`.

## Phase 6 — tests and acceptance criteria

### Unit and integration tests

- Run the complete upstream 1.7 test suite from the copied package tree.
- Golden-test startup, instructions yes/no, movement, inventory, invalid input,
  magic words, scoring, each death path, resurrection questions, quit
  confirmation, cave closing, and game over with a fixed seed.
- Run both upstream walkthrough transcripts to completion.
- Verify that raw case, punctuation, spaces, quotes, backslashes, Unicode,
  newlines, and a maximum-size message reach the adapter boundary unchanged.
- Verify upstream tokenizer semantics separately from transport exactness.
- Verify blank input returns `empty_input`, oversized input returns
  `input_too_large`, and malformed JSON returns a bounded protocol error;
  none may change state.
- Round-trip state at startup, ordinary play, a pending question, after death,
  during danger, and during endgame; compare subsequent transcript output and
  random events with an uninterrupted control run.
- Replay a 1,000-command transcript on the verified host within the measured
  per-tool-call timeout, with a target below two seconds; document a lower tested
  turn limit if the host cannot meet that target.
- Fault-inject before journal write, after journal fsync, after engine step,
  during checkpoint replace, after checkpoint commit, and during PNG creation.
  Prove no committed command is applied twice.
- Retry the same request ID with the same input and verify cached replay; retry
  it with different input and verify a conflict error.
- Run two sessions concurrently and prove isolation and locking.
- Test path traversal and absolute paths in session IDs, corrupt checkpoints,
  tampered hashes, malicious transcript JSON, and `save` commands containing
  filesystem paths.
- Golden-test every renderer theme, blank/short/long output, hard wraps,
  pagination, punctuation, and blank lines. Assert decoded pixels and text layout
  in addition to PNG hashes.
- Verify that renderer failure preserves the committed text response.
- Unit-test smoke-case schema validation, deterministic ordering, exit codes,
  timeout handling, cleanup, report atomicity, sanitization, and one induced
  failure whose `issues[]` entry is sufficient to reproduce the problem.
- Run the complete smoke test locally from the built submission and require all
  mandatory cases to pass.

### Host acceptance tests

- Upload the gallery-generated ZIP, not a hand-built package.
- Complete the Phase 0 sequence again against the final package.
- Play at least one full walkthrough in Preview and test a second concurrent
  conversation.
- Confirm every chat response before `finished` contains only exact game text
  followed by the expected image attachment(s).
- Kill/restart the available execution context at safe checkpoints and verify
  documented recovery behavior.
- Confirm image readability, inline display, unique filenames, and measured host
  size limits.
- Invoke the bundled smoke test from chat before starting a game, during an
  active game, and after game over. Confirm all mandatory cases pass, the JSON
  report is returned, failures are actionable, and the active game is unchanged.

### Repository and bundle checks

Run from a clean worktree:

```bash
PYTHONPATH=submissions/classic-text-adventure/scripts/runtime \
  python -m unittest discover submissions/classic-text-adventure/scripts/runtime/adventure
python -m unittest discover submissions/classic-text-adventure/scripts/tests
python submissions/classic-text-adventure/scripts/smoke_test.py \
  --state-root .smoke-state \
  --report .smoke-state/classic-adventure-smoke-report.json \
  --json-summary
npm run check:submissions
npm test
npm run import:submissions
npm run build
```

Then inspect `public/bundles/classic-text-adventure.zip` and prove:

- `SKILL.md` is at ZIP root.
- `metadata.json` and root `README.md` are absent.
- no cache, state, PR-description, archive, secret, absolute path, or unexpected
  file is present.
- every bundled file except `BUNDLE_MANIFEST.json` matches its entry in that
  manifest, and every third-party file also matches
  `THIRD_PARTY_MANIFEST.json`.
- the ZIP uploads successfully to Copilot Studio.
- a second import produces a byte-identical ZIP.

Implementation is complete only when every applicable test passes, Phase 0 and
licensing gates are signed off, the PR description matches the actual bundle,
and no placeholders or unresolved claims remain.

## PR licensing record

Create `classic-text-adventure-pr-description.md` at the repository root as an
untracked, human-only artifact. Do not add it to the submission or commit it
elsewhere. Its text must be ready to paste verbatim into the PR body and must
include:

- an executive conclusion describing exactly what is redistributed and why the
  contributor believes redistribution is permitted, while stating that the
  record is not legal advice;
- the complete component inventory: upstream engine, historical data/text,
  first-party wrapper/tests/procedural visuals, font, host-supplied Pillow, and
  Python standard library;
- for every redistributed third-party component: exact name/version, owner,
  canonical URL, source filename and SHA-256, SPDX identifier (use a defined
  `LicenseRef-Public-Domain` for the historical content), copyright/notice,
  exact bundle paths, verbatim/modified status, and license/notice paths;
- separate engine and game-content provenance analyses, including uncertainty
  or conflicting evidence rather than an unsupported claim of certainty;
- short operative upstream quotations with primary-source links and retrieval
  dates, within quotation limits;
- an Apache-2.0 obligation matrix covering license inclusion, copyright
  retention, upstream `NOTICE` handling, modification marking, patent terms,
  and no trademark grant;
- an OFL-1.1 font obligation review and reserved-font-name check;
- confirmation that first-party files remain under this repository's MIT license
  and that the root MIT license is not used to relicense Apache/public-domain/OFL
  components;
- all three game candidates and the rejection reasons;
- confirmation that no GPL/unclear game, logo, screenshot, AI-generated image,
  or unlicensed art is included;
- supply-chain controls, artifact and file hashes, offline execution, no runtime
  download, and the generated file-level manifest;
- exact commands used to fetch/verify/extract the source artifacts, regenerate
  the manifest, run tests, generate/inspect the ZIP, and reproduce host tests;
- confirmation that the importer excludes `metadata.json` and root `README.md`
  while bundled license notices remain present;
- Phase 0 evidence, supported operating envelope, known limitations, and every
  unresolved question;
- the final in-agent smoke-test summary, report schema/suite version, any issue
  codes encountered and their resolution, and confirmation that the harness
  performs no telemetry or external issue creation;
- a maintainer checklist with separate confirmations for host feasibility,
  provenance, license compatibility, notices, trademarks/artwork, bundle
  contents, security, and reproducibility; and
- a final request for any additional Microsoft open-source-compliance evidence
  required before merge.

Cross-check every path, version, hash, quoted statement, and claim against the
finished bundle immediately before opening the PR.

## Authoritative references

- Repository submission rules: [`CONTRIBUTING.md`](../CONTRIBUTING.md) and
  [`submissions/README.md`](../submissions/README.md).
- Microsoft skill package format and upload flow (preview; retrieved
  2026-07-22):
  [Skills overview](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-overview)
  and
  [Add an existing skill](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-add-existing).
- `adventure` 1.7 release, hashes, license, and historical-content statement
  (retrieved 2026-07-22):
  [PyPI](https://pypi.org/project/adventure/).
- Upstream source and Apache license:
  [brandon-rhodes/python-adventure](https://github.com/brandon-rhodes/python-adventure).
- Font source and license:
  [JetBrains Mono 2.304](https://github.com/JetBrains/JetBrainsMono/releases/tag/v2.304).
