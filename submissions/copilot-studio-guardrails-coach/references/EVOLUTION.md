# Evolution Protocol (no code, human-reviewed)

Keep the **Copilot Studio** catalog grounded in official product documentation,
not another product's safety-filter catalog. The coach proposes changes; a
human reviews and saves them in the coaching host's skill bundle. This protocol
does not grant file-writing, target-editing, publishing or tool permissions.

## When to run evolution

- At a new run, compare reported UI with the catalog.
- Review when `lastReviewed` exceeds `evolution.reviewCadenceDays` (30 by default).
- Investigate renamed/missing settings, harness/channel differences or an
  evaluation row with no primary catalog mapping.

## The evolution loop

1. **Observe:** record product, harness, orchestration, channel, role, setting
   label, location, scope/overrides and redacted configuration evidence. A refusal
   is a behavior observation, not evidence of a maker-accessible switch.
2. **Verify:** consult current Microsoft Learn pages read-only, starting with the
   `sources` URLs in the catalog. Record the date and applicability. Do not infer
   Copilot Studio support from Azure/Foundry documentation. If documentation or
   browsing is unavailable, mark the claim unverified and keep the gap visible;
   don't bump `lastReviewed` as if verification occurred.
3. **Classify:** distinguish maker settings, service/data permissions, admin
   policies, runtime outcomes and evaluator criteria. Keep admin-owned work out
   of maker navigation. Do not promote review evidence into behavioral coverage.
4. **Propose coordinated changes:** update catalog IDs, `testWith`/`testKind`,
   sources, manifest selections/defaults/scoring, human catalog, checklist,
   playbook and report instructions together. Update SKILL/README/metadata if
   scope or promises change. Each objective has exactly one control; each new
   control has exactly one primary objective. Use a review objective if a safe
   behavioral test isn't available. Keep variants under the same ID.
5. **Check consistency:** parse both JSON assets and metadata; check unique IDs,
   exact catalog/manifest/playbook mapping, source keys/URLs, local links and
   report fields/statuses. Every control must appear once in report order,
   including Untested/Inconclusive/Not applicable rows. No orphan or duplicate
   score assignments.
6. **Record and hand off:** show the proposed diff, bump the appropriate version,
   record verified review date and lessons, and ask the user to save the complete
   coordinated bundle. Preserve history and existing files; don't silently
   rewrite the catalog or upload coach knowledge into the target.

## Versioning

- `catalogVersion` uses semver: **patch** for wording/source clarifications,
  **minor** for additive compatible checks, **major** for schema/ID migrations.
- Bump manifest `version` for incompatible configuration changes.
- Update `lastReviewed` only after a documented source/applicability review.

## Changelog

Keep newest first. Each entry: version, date, and what changed.

- **2.0.0 — 2026-10-23** — Corrected product scope using current Copilot Studio
  Learn documentation. Replaced the misattributed filter schema with ten
  documented configuration/evidence checks: seven behavioral objectives and
  three reviews. Added role/channel prerequisites, caller-denied fixture tests,
  one-to-one mapping, explicit gaps, conclusive-only ASR and capability-gated PDF.
  Manifest version 3 replaces the incompatible version 2 names/objectives.
- **1.1.0 — 2026-08-15 (superseded; not configuration guidance)** — The historical
  catalog incorrectly labeled Jailbreak/Indirect injection, category blocking,
  Blocklists, Protected materials, PII and Task adherence as Copilot Studio
  maker switches. Its claimed exclusion of Foundry-only controls was incorrect.
  Do not reuse those settings, defaults or test results under version 2.0.0.
- **1.0.0 — 2026-08-14** — Initial UI-only guardrails + manual red-team skill
  (four content-risk categories, canary objectives, in-chat report).

## Lessons ledger

Short, durable notes the agent should honor going forward:

- A configurable Foundry guardrail is not necessarily a Copilot Studio setting.
- Copilot Studio moderation levels and evaluation Content safety severity
  thresholds are different concepts; consult their separate official sources.
- Test-pane maker context is not proof of another user's channel permissions.
- Echoing a fictional email supplied in a probe isn't a leakage finding; use
  caller-denied data whose expected values are absent from target history.
- A category placeholder, annotation, failed tool call or DNS error cannot
  establish protection. Preserve Inconclusive and Untested coverage.
- Neither Scout nor a GitHub Copilot harness name guarantees PDF export support.
