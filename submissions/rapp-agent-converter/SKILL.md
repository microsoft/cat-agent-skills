---
name: rapp-agent-converter
description: >-
  Use this skill whenever the user works with RAPP single-file agents (the
  Rapid Agent Prototype Pattern): converting an agent.py cartridge into a
  Copilot Studio / Cowork / Scout Agent Skill, converting a SKILL.md back into
  a runnable agent.py, bringing a RAPP-built agent into Copilot Studio,
  verifying such a conversion lost nothing, or talking to a live RAPP
  brainstem over its /chat endpoint. Always run the bundled deterministic
  converter instead of transforming the files by hand.
---

RAPP `agent.py` to Agent Skill — and back. The same pair works unchanged in
Copilot Studio, Cowork, Scout, and other SKILL.md-reading harnesses, giving
each of them RAPP agent.py compatibility. The Rapid Agent
Prototype Pattern: a capability is **one Python file** — one class, one typed
`metadata` contract, one `perform()` method — and every other shape is a
projection of it. This skill converts between the two shapes with zero
fidelity loss:

- **agent** — a RAPP single-file agent cartridge (`*_agent.py`). The canonical
  form.
- **skill** — an Agent Skill projection shipped as a **pair**: a `SKILL.md`
  with the full Python embedded (plus an `rci-capsule:v1:` comment vaulting the
  byte-exact original, sha256-verified) and a **linked python file beside it
  that literally is the agent.py**. A host with sandbox execution — Copilot
  Studio becomes a first-party user of agent.py this way — runs the linked
  file directly; the SKILL.md alone remains self-sufficient if the linked file
  is missing. Converting back is a checksum-verified restore, never a
  re-render.

Everything routes through one deterministic engine. Do not improvise
conversions, do not hand-edit formats, and do not paraphrase code — model-driven
transformation is exactly the drift this skill exists to prevent.

## Commands

Run from this skill's directory. Stdlib-only Python 3.9+, fully offline — no
pip install, no network, no credentials.

```bash
python3 scripts/toast.py convert <path> --to skill -o out/SKILL.md   # agent.py -> SKILL.md + linked agent
python3 scripts/toast.py convert <path> --to agent                   # SKILL.md -> agent.py
python3 scripts/toast.py roundtrip <path>                            # prove fidelity, exit 1 on drift
python3 scripts/toast.py inspect <path>                              # capsule status, identity, provenance
python3 scripts/toast.py selftest                                    # prove every verdict can fire
```

Always pass `-o` with a path that is not an existing file you care about; the
tool refuses to overwrite its own source file or an existing target with
different bytes without `--force`. A byte-identical existing target is an
idempotent success. Never target this skill's own `SKILL.md`. Without `-o`,
output lands next to the source file (the tool prints the absolute path).

Exit codes: 0 = verified, 1 = drift or refusal (message says which), 2 =
`RAW BREAD` — a capsule-less SKILL.md has no byte-exact return trip yet;
convert it to an agent first, or pass `--allow-raw` to measure
capability-level fidelity only. Treat only exit 1 as drift.

The full lifecycle: the FIRST conversion of a hand-written SKILL.md creates a
runnable launchpad agent without inventing behavior. Instructions travel
verbatim; an explicit `## Parameters` JSON-Schema fence supplies the typed
contract; a Python fence whose info string is
`python # rapp:deterministic` supplies implementation when present. Ordinary
example fences remain documentation. A prose-only skill remains prose-only in
the launchpad. Converting
that agent back embeds it literally inside a new SKILL.md — single-file
shareable — with the agent.py linked beside it, and it still maps back to the
identical agent.py. Both platforms are served by the same pair, and the Python
is preserved byte-exact at every hop.

## Converting agent.py → Agent Skill

1. Run `convert <file> --to skill -o <dir>/SKILL.md`. Two things are emitted:
   the SKILL.md (frontmatter from the agent's own metadata, its docstring as
   instructions, a generated `## Parameters` JSON-Schema fence, a generated
   `## Run this — do not improvise` section with the **entire agent.py
   embedded verbatim**, and the capsule comment) plus the **linked agent
   file** next to it — a byte-exact copy of the source. Ship both in the
   skill's bundle.
2. Immediately run `roundtrip <file>` on the source agent. Report success only
   on `IDENTICAL`. On `DRIFT`, report the two sha256 prefixes it prints and
   stop — never hand-patch the output to make it match.
3. The output says `SYNTHESISED` (fresh projection) or `RESTORED (byte-exact)`
   (a vaulted original existed). Relay that word to the user — the two must
   never be confused.

## Converting SKILL.md → agent.py

1. Run `convert <file> --to agent`.
   - If the SKILL.md carries a capsule, the agent is **restored byte-exact**
     (sha256-verified; a checksum mismatch aborts — never bypass it).
   - If it is a plain hand-written SKILL.md (no capsule), a launchpad agent is
     **synthesised**: instructions travel verbatim in `INSTRUCTIONS`, typed
     parameters come from a `## Parameters` fence when present, and a fence
     whose info string is `python # rapp:deterministic` is preserved as
     implementation when present. Ordinary Python examples are never
     executable. Otherwise
     `perform()` returns the original instructions plus the supplied inputs;
     it does not infer commands from prose. Say so explicitly — a synthesis is
     a capability projection, not a restoration. A prose-only skill (no
     Parameters fence) synthesises an agent with an EMPTY parameter schema —
     the contract is untyped and nothing is validatable as required; tell the
     user so, and offer to add a `## Parameters` JSON-Schema fence to the source
     skill first if they want a typed contract.
2. The emitted filename ends `_agent.py` (snake_case) so RAPP Brainstem
   auto-discovery loads it unchanged. Contract details:
   [references/rapp-agent-contract.md](references/rapp-agent-contract.md).

## Verifying (mandatory before claiming success)

- `roundtrip` on an agent proves: agent → skill → agent returns the exact
  original bytes, and the projection is a fixed point over repeated cycles.
- `roundtrip` on a converted SKILL.md proves: the vaulted agent restores
  checksum-verified, and the inline Python fence still matches it — editing
  inside the generated markers is detected as INLINE DRIFT, exit 1.
- Behavioural fidelity is graded, never assumed: **EXEC** (host executed the
  file — only claim after `python3 <file> --tool` actually exits 0), **CODE**
  (the code travels in the fence), **SPEC** (typed contract only). Never report
  EXEC without having executed.
- Try it end to end on the bundled sample:
  `python3 scripts/toast.py roundtrip assets/hello_rapp_agent.py`

## Host tiers for the emitted Agent Skill

- **Copilot Studio / Cowork** (sandbox execution): run the linked agent file
  directly — `--tool` for the contract, one JSON object for arguments; if the
  linked file is missing, materialize it verbatim from the fence first. Treat
  stdout as a tool result: collect missing inputs, execute returned `steps` in
  order, follow returned `instructions`, or otherwise use the result verbatim.
  This earns the EXEC tier and makes the host a first-party user of the
  agent.py itself.
- **Scout** and other instruction-driven hosts (no sanctioned script execution
  today): the same SKILL.md still works — treat the Parameters schema and the
  fenced code as the exact specification and never paraphrase a step (CODE
  tier). When the host later gains a sanctioned execution path, the identical
  file upgrades to EXEC. The file does not change — that is the promotion, not
  a port.

## Talking to a live RAPP entity

When a running RAPP brainstem is available, everything rides one wire: `POST
/chat`. Follow [references/rapp1-protocol.md](references/rapp1-protocol.md)
exactly — the response field is `response` (never `assistant_response`), keep
the returned `session_id` for continuity, and never invent sibling REST
routes. Dropping a converted `*_agent.py` into the brainstem's `agents/`
directory hot-loads it with no restart.

## Guardrails

- Never edit content between `<!-- toaster:generated:begin -->` and
  `<!-- toaster:generated:end -->`, and never strip or truncate an
  `rci-capsule:v1:` comment — that is the byte-exact original.
- Never import or execute an agent file in order to read it; the converter
  parses with `ast` only. Executing the agent is a separate, user-visible step.
- Report unconvertible files with the reason; never silently skip or "fix" them.
- Sandbox files do not persist across conversations: return or save the
  converted artifacts in the same turn you produce them.
- The converter carries identity through; it never mints identity from content.
