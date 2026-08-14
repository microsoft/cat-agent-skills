# Agent Quality Dimensions

Cross-cutting review-and-design dimensions that sit alongside the topic/orchestration
analysis. Each dimension is evaluated in **both** modes: in Mode B, inspect the artifact
and self-report; in Mode A, elicit the requirement and pre-mortem the design.

- **capability-date:** 2026-08
- **review-cadence:** quarterly
- **grounding:** platform facts here are sourced from Microsoft Learn. Fetch the linked
  pages (see `GUIDE-*` in `reference-links.json`) before asserting a
  version-specific detail — memory, guardrails, and multi-agent features are largely
  **preview** and move fast.

These six dimensions are where most *post-ship* agent problems actually live. Topic
collisions cause bad launches; memory, context, handoff, guardrail, access, and feedback
gaps cause bad *operations*. Every dimension maps to a rule ID in `ceiling-rules.md` —
this file is the domain knowledge; that file is the classifier.

---

## 1. Guardrails (safety & control boundaries)

**Rules:** `GOV-01`, `CFG-05` (existing) · `CFG-10` (new, Foundry intervention points).

### What good looks like

**Copilot Studio**
- Content moderation set to a level matching the domain, not left at default.
- Generative answers on regulated content enforce citation-required grounding.
- Sensitive context variables marked **Sensitive** so values are not written to
  transcripts or Application Insights telemetry (note: still stored in Dataverse —
  redact at any downstream destination).

**Azure AI Foundry**
- A **guardrail** (named collection of controls) is explicitly **assigned to the agent** —
  the agent guardrail fully overrides the underlying model's guardrail.
- Controls cover the right **intervention points**: `user input` and `output` always;
  `tool call` and `tool response` (agent preview) whenever the agent calls tools —
  otherwise harmful content passes through tool I/O unscanned.
- Severity thresholds (Off/Low/Medium/High) tuned per risk category — too High blocks
  legitimate content, too Low lets edge cases through.
- **Network egress controls** (preview, hosted agents) restrict outbound destinations to
  an allowlist.
- Backed by Azure AI Content Safety; follow the RAI **Discover → Protect → Govern** loop.

### Review checks
- Is moderation/guardrail configured at all, and does it match `content_safety_tier`?
- For Foundry tool-using agents: are `tool call` / `tool response` intervention points
  enabled?
- Is the guardrail assigned to the *agent*, or is it silently inheriting the model's?
- Are sensitive variables flagged and redacted downstream?

### Failure signature
Harmful or ungrounded output reaching users; a jailbreak succeeding through a tool
response; PII appearing in transcripts/telemetry.

---

## 2. Feedback loops (evaluation & continuous improvement)

**Rules:** `CEIL-04` (existing, automated gating eval) · `CFG-11` (new, missing eval
baseline / user-feedback channel / tracing).

### What good looks like

**Copilot Studio**
- Behavioural tests exist (Test Planner territory — do not duplicate it).
- Analytics reviewed for containment, escalation, and CSAT; a defined path for users to
  report bad answers.

**Azure AI Foundry**
- A **rubric evaluator** generated from the agent's context, paired with **built-in
  evaluators** (task adherence, content safety, groundedness).
- An acceptance **threshold** set (e.g. 85% task-adherence pass rate) and used as a gate
  before release.
- **Risk & safety evaluators** run: prohibited actions, sensitive data leakage (agents),
  code vulnerability, protected materials, XPIA (model). Aggregate **defect rate** tracked.
- **AI Red Teaming Agent** used for adversarial discovery.
- **Tracing + monitoring** in production to detect drift and surface new risks (Govern).
- A **user feedback channel** built into the experience, with human oversight — do not
  rely solely on automated metrics.

### Review checks
- Is there any evaluation at all, or only manual spot-checks?
- Is there a threshold, and does anything gate on it?
- Is there a closed loop: production telemetry → dataset → re-eval → fix?
- Can users report a bad answer, and does anyone see it?

### Failure signature
Quality silently regresses after a prompt/model change; no one notices until users
complain; no dataset to reproduce the regression.

---

## 3. Access (identity, least privilege, isolation)

**Rules:** `GOV-03`, `GOV-06` (existing) · `GOV-08` (new, cross-user memory/state
isolation & connected-agent privilege).

### What good looks like

**Copilot Studio**
- On-behalf-of (OBO) auth for user-scoped data — never a service principal that bypasses
  per-user authorization.
- Memory is **per-user isolated** (each user has a separate store); one user's context
  never surfaces to another.
- Connected agents that hold higher privilege are governed — the parent cannot use a
  child to reach data or actions it is itself denied.
- MCP tools / connectors scoped to least privilege and under tenant DLP.

**Azure AI Foundry**
- Memory `scope` set explicitly per user (`{{$userId}}`) so memories are isolated; the
  low-level memory API requires `scope` on every request.
- **BYO thread storage** in the customer's own Azure Cosmos DB when control/residency
  matter (threads live in the `enterprise_memory` database).
- Note: **VNet integration is not supported for memory stores** — factor this into
  network-isolation requirements.
- Connected/child agents may carry different privileges — apply governance and audit.

### Review checks
- Does any user-scoped read run under a service principal? (→ `GOV-03`)
- Is memory/thread state isolated per user, or could it leak across users? (→ `GOV-08`)
- Can a low-privilege parent reach a high-privilege capability through a connected agent?
- Where is conversation/memory data stored, and does that satisfy residency?

### Failure signature
One user seeing another's data via shared memory/thread; an agent surfacing records the
asking user has no right to; a connected-agent path around an approval gate.

---

## 4. Memory (persistence of knowledge across turns and sessions)

**Rules:** `CEIL-05` (existing, durable/cross-session state) · `CFG-09` (new, memory
on/off, retention/TTL, sensitive-data hygiene).

### What good looks like

**Copilot Studio**
- **Memory (preview)** turned on only when continuity adds value; off when it does not
  (it consumes Copilot Credits). Lifecycle is Capture → Store → Apply, per-user.

**Azure AI Foundry**
- Distinguish **short-term** (thread/session context, managed by the runtime) from
  **long-term** (memory store across sessions).
- Long-term memory types chosen deliberately: **user profile**, **chat summary**,
  **procedural**. Retrieve profile early in the conversation; summary per turn.
- **Retention** configured: store-level default **TTL**, item-level CRUD for correction
  and deletion — required for compliance.
- `user_profile_details` used to **include** what matters and **exclude** sensitive data
  (age, financials, precise location, credentials).
- Memory protected against **prompt injection and memory corruption**: validate content
  entering/leaving memory with Content Safety + jailbreak detection; run adversarial tests.

### Review checks
- Is memory on where continuity is needed / off where it is pure cost?
- Is there a retention/TTL policy, or does memory grow unbounded?
- Can memory be poisoned by untrusted content, and is that content scanned?
- Is sensitive data excluded from what memory extracts?

### Failure signature
Agent forgets context users already gave (memory off when needed); memory grows forever
with no TTL; a poisoned memory steering later answers; PII persisted in a memory store.

---

## 5. Context management (fitting the right state into the window)

**Rules:** `DSN-05` (existing, variable lifecycle) · `DSN-09` (new, context/thread window
mismanagement; escalates to `CEIL-05`).

### What good looks like

**Copilot Studio**
- Global vs topic **variable scope** used deliberately; a single topic dedicated to
  collecting externally-set globals.
- **Timeouts** set on variables that receive values from external/late sources so the
  agent does not block or read empty.

**Azure AI Foundry**
- Threads sized sensibly — they **auto-truncate** to fit the model context window, so
  very long threads silently drop early context and add latency (up to 100k messages/thread
  is the hard cap, but practical limits are far lower).
- A **new thread** started for a new topic or a different user rather than one ever-growing
  thread.
- Long tool-call chains watched: deep chained MCP/tool sequences can exhaust context and
  cause runs to stall — budget the number of chained calls.

### Review checks
- Are variables read-without-set or set-without-read? (→ `DSN-05`)
- Are threads unbounded, risking truncation of the very context the task needs?
- Do deep tool chains fit the context budget, or do they fail at depth?
- Escalate to `CEIL-05` only when the requirement is durability *beyond* a session, not a
  fixable windowing/thread-hygiene problem.

### Failure signature
Agent "forgets" something said earlier in a long thread (truncated); rising latency on
long conversations; multi-tool runs that stall partway with no user-visible answer.

---

## 6. Session handoff (continuity across agents, humans, and sessions)

**Rules:** `DSN-07`, `GOV-04`, `CFG-03` (existing) · `DSN-10` (new, handoff continuity —
context carried across the boundary).

### What good looks like

**Copilot Studio**
- **Connected agents** pass conversation history by default; the parent additionally
  passes known parameters (e.g. the user's name) so the child does not re-ask.
- Each connected agent has a **clear description** of when it should be used (the parent
  treats it as an agentic tool).
- **Contextual handoff** to another M365/LOB agent or human passes both the conversation
  history and the original prompt — no "please repeat your question".
- **A2A** handoffs carry a `contextId` and full chat history in the payload.
- Human **escalation** carries context variables (e.g. the created ticket number) to the
  representative.

**Azure AI Foundry**
- **Connected agents** enable multi-agent systems without an external orchestrator; use
  the **handoff orchestration** pattern (routing/triage/transfer) where full control
  moves to the specialist.
- **Long-term memory** provides continuity across sessions/devices; **threads** provide
  within-session continuity.

### Review checks
- On delegation/escalation, is context (history + key parameters) actually carried, or is
  the user forced to repeat themselves? (→ `DSN-10`)
- Is each handoff target's responsibility, input, and failure behaviour specified?
  (→ `DSN-07`)
- Is there a human handoff at all for irreversible actions and dead ends?
  (→ `GOV-04`, `CFG-03`)
- Does cross-session continuity rely on memory that is actually configured?

### Failure signature
User repeats their whole request after a handoff; a specialist agent answers without the
context the front door already collected; an escalation drops the case number.

---

## How to use in a report

- Add a short **"Operational readiness"** subsection to the findings register covering
  these six dimensions, even when the finding is "adequate" — stating a dimension was
  checked and is sound is itself a credibility signal.
- Classify every dimension finding through `ceiling-rules.md` (GOVERNANCE → CEILING →
  COST → DESIGN → CONFIG, first match wins). Memory/context/handoff issues are usually
  DESIGN or CONFIG; access/guardrail issues are usually GOVERNANCE; only true
  cross-session durability is CEILING (`CEIL-05`).
- Do **not** let these dimensions become a migration argument on their own. They are
  almost always fixable in place — that is the point.
