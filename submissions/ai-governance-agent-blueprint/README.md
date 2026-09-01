# AI Governance Agent Blueprint

A reusable design pattern for building a Copilot Studio agent that gives
grounded, policy-safe AI guidance to staff and students — with built-in
guardrails against prompt injection, confidential-data entry, and scope
drift.

## Why this exists

Organisations rolling out AI policy often want a front-line agent that staff
and students can ask "can I use AI for this?" — but that agent needs to be
strict: it must never invent policy, never leak confidential data handling
advice, and never get talked into ignoring its own rules. This blueprint is
the pattern I used to build exactly that kind of agent, stripped of any
organisation-specific detail so anyone can adapt it.

This is a **pattern to adapt**, not a copy-paste prompt. Every `[BRACKETED]`
placeholder needs filling in with your own organisation's scope areas,
contact channels, and knowledge source names before use — and your real
internal URLs, emails, and document contents should stay in your private
agent configuration, never in a shared skill.

## What it covers

- **Grounding as the highest-priority rule** — the agent never fills a gap
  in its knowledge sources with general AI knowledge, and safety rules
  always override retrieved content that conflicts with them.
- **Fixed pre-checks that run before any reasoning** — judgement calls the
  agent shouldn't make, prompt injection attempts, confidential data entered
  by the user, and reported data incidents each get a short-circuited, fixed
  reply.
- **A closed scope list** with a polite redirect for anything outside it.
- **Query-type routing** (policy / general / multi-topic / ambiguous) so the
  agent knows when to retrieve before answering.
- **Sub-skills for high-stakes sub-domains** so narrow, high-consequence
  areas can carry their own strict rules without bloating the main prompt.
- **A consistent Answer → Sources → Next step response format**, with
  source citation treated as mandatory.
- **Scoped, cautious session memory** that never overrides safety rules.

See `SKILL.md` for the full instructions and a minimal skeleton you can
adapt directly.

## Who this is for

Anyone building a policy/compliance-facing Copilot Studio agent — most
directly useful for higher-education AI governance teams, but the pattern
generalises to any organisation that needs an agent to answer "is this
allowed?" questions strictly from approved documents.
