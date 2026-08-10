# RAPP Agent Converter

RAPP to Microsoft Copilot Studio. This skill converts a **RAPP single-file
agent** (`agent.py` — one file, one class, one typed metadata contract, one
`perform()` method; the Rapid Agent Prototype Pattern) into an **Agent Skill**
and back, with **zero fidelity loss**. The emitted projection is a pair: a
`SKILL.md` carrying the complete Python inline plus an invisible
`rci-capsule:v1:` comment vaulting the byte-exact original, and a **linked
python file beside it that literally is the agent.py** — so Copilot Studio
runs the real implementation first-party instead of re-deriving it from prose.
Converting back is a checksum-verified *restore*, never a re-render. Nothing is
translated, so nothing can drift.

## Why

Teams prototype agents locally as RAPP cartridges — fast, testable, typed — and
then need the same capability in Copilot Studio, Cowork, or Scout. Skills alone
drift: prose gets paraphrased, steps get reordered, and a capability that works
for one person gets hand-rebuilt for the next. The fix is the *skinny skill*
pattern: keep the deterministic work in Python, let the SKILL.md carry the exact
code and link the runnable file beside it, and make every conversion provable.

- Hosts with sandbox execution (Copilot Studio, Cowork) run the linked agent.py
  directly — deterministic behaviour, verbatim output, first-party use of the
  cartridge.
- Instruction-driven hosts (Scout today) read the identical SKILL.md as an
  exact spec. When a host gains a sanctioned execution path, the same file
  upgrades from spec to execution. **The file does not change — that is the
  promotion, not a port.**

It also works starting from an existing skill: the first SKILL.md → agent.py
conversion lays down the deterministic layer (typed parameters + steps
interpreted from the prose into a runnable launchpad agent); converting that
agent back embeds the layer literally in a new SKILL.md that still maps back to
the identical agent.py.

## A universal pattern, not a Copilot Studio exclusive

Copilot Studio is the flagship target, not the boundary. Drop this skill into
**any** product that consumes `SKILL.md` — Cowork, Scout, or another
SKILL.md-reading harness — and *that* product gains RAPP agent.py
compatibility: on-the-fly conversion in both directions, infinite round trips
with zero drift, and single-file shareability between machines. Any
SKILL.md-based system that doesn't want drift or fidelity loss as capabilities
move between hosts can adopt the same pair unchanged.

## What's in the box

| Path | What it is |
|------|------------|
| `SKILL.md` | The agent-facing instructions for driving conversions. |
| `scripts/toast.py` | The deterministic converter — stdlib-only Python 3.9+, offline, AST-based (agent files are never imported or executed to read them). |
| `references/rapp-agent-contract.md` | The RAPP agent contract: required structure, portability shim, loader-enforced rules. |
| `references/rapp1-protocol.md` | The rapp/1 wire: the `/chat` envelope and interop rules for talking to a live brainstem. |
| `assets/hello_rapp_agent.py` | A complete minimal cartridge to try the round trip on. |

## Try it

```bash
cd rapp-agent-converter
python3 scripts/toast.py selftest                                # every verdict fires
python3 scripts/toast.py convert assets/hello_rapp_agent.py --to skill -o /tmp/SKILL.md
python3 scripts/toast.py roundtrip assets/hello_rapp_agent.py    # IDENTICAL, or exit 1
python3 assets/hello_rapp_agent.py '{"person": "Ada"}'           # the cartridge itself runs anywhere
```

`roundtrip` is the honest half: it proves the round trip returns the **exact
original bytes** and that the projection holds under repeated cycles.
`selftest` additionally proves the failure verdicts can fire (a corrupted
capsule is refused by checksum; tampering inside the generated fence is
detected as inline drift; a capsule-less file is refused by the oracle; edits
to a generated agent are honored, never ignored) — a comparison that has never
detected a mismatch is indistinguishable from one that cannot.

## Format interop

Conversion follows `rapp-capability-interchange/1.0` — the capsule, the
generated-content delimiters, and the drift oracle are the same contract used by
the reference implementation at
[kody-w/rapp-toaster](https://github.com/kody-w/rapp-toaster), so artifacts
produced here are readable by the wider toolchain and vice versa. The agent
contract is documented in
[references/rapp-agent-contract.md](references/rapp-agent-contract.md), and the
live-entity wire protocol in
[references/rapp1-protocol.md](references/rapp1-protocol.md).

---

<sub>RAPP is a personal, independent open project by the author — not an
official Microsoft product; named here to describe interoperability. RAPP™
compound marks are claimed by Wildhaven Homes LLC; the RAPP stem standing alone
is deliberately unclaimed.</sub>
