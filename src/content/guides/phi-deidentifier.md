# PHI De-identifier

Redact the **18 HIPAA Safe Harbor identifiers** from clinical text — notes,
transcripts, referral letters, intake records — and get back the scrubbed text
plus an **audit manifest** of exactly what was removed. Built for the locked
agent Python sandbox: **standard library only, no pip, no network.**

## Why it exists

Agents in health & life sciences routinely handle PHI — summarizing a note,
drafting a referral, prepping a record for analytics, or building teaching
material — so the *risk* of an identifier slipping into an outbound action is
ever-present. This skill gives an agent a **deterministic, auditable** way to
strip identifiers *before* that content leaves a trusted boundary or lands in an
outbound action (Send Email, Create Record, Export).

## Where it fits

Think of it as the **de-identification step an agent runs right before data
crosses a trust boundary** — a guardrail wired into the agent's flow, not a
tool a person invokes by hand. It's most valuable when called *just before*:

- **An outbound action** — Send Email, Post to Teams/Slack, Create/Update a
  record in a downstream system, or Export to a file the agent is about to hand
  off. Scrub first, act second.
- **A submission or ticket** — attaching a case to a support ticket, a research
  intake form, a registry, or a vendor portal that isn't cleared for raw PHI.
- **Handing content to a less-trusted step** — another model, a third-party
  connector, an analytics pipeline, or a logging/telemetry sink that shouldn't
  see identifiers.
- **Generating shareable material** — teaching cases, conference abstracts, demo
  data, or test fixtures built from real records.

A natural agent instruction is simply: *"Before any action that sends, exports,
or shares patient content, run it through the PHI de-identifier and relay
anything flagged for human review."* The user never has to ask for
de-identification by name — the agent treats it as a reflex.

## How it works — a hybrid you can defend

- **Deterministic core (system of record).** A regex + offline-lexicon engine
  removes structured identifiers — SSN, MRN, phone/fax, email, URLs, IPs, dates
  (reduced to year), ZIP (truncated to 3 digits), street/city, account, license,
  and device numbers — reproducibly, every run.
- **Model recall booster.** For unusual person names in free prose that a regex
  would miss, the agent passes the names it spotted; the engine still redacts
  them deterministically. The model can only *add* redactions — it can't silently
  change the audit trail.
- **Built-in guard.** After redacting, it verifies the identifiers it detected
  actually vanished from the output, and lists anything that needs a human's eyes
  under `needs_human_review`.

## What you get back

1. The **de-identified text** with consistent pseudonym tokens
   (`[NAME-1]`, `[DATE:1959]`, `[ORG-1]`, `[ZIP:441XX]`).
2. An **audit manifest**: per-category counts, salted hashes of removed values,
   items flagged for human review, and a plain-language notes section.

Two standards are supported: **Safe Harbor** (default) and **Limited Data Set**
(retains dates and city/state/ZIP). Structured input (JSON / `Field: value`)
is redacted by **field name** in record mode; free prose uses the name-recall
pass.

## Example

**In:**

```
Patient Maria Gonzalez (MRN 55810342), DOB 04/12/1959, seen 03/03/2025.
Call (216) 555-0147 or maria.g@example.com. Lives at 88 Oak St,
Cleveland, OH 44113. Discussed with Dr. Alan Reyes.
```

**Out (Safe Harbor):**

```
Patient [NAME-1] (MRN [MRN-1]), DOB [DATE:1959], seen [DATE:2025].
Call [PHONE-1] or [EMAIL-1]. Lives at [STREET-1], [GEO-1], OH [ZIP:441XX].
Discussed with Dr. [NAME-2].
```

Note the transformations that keep data useful: dates collapse to **year**, ZIP
truncates to its **first three digits**, the **state is retained**, and each
identifier gets a **stable token** so the same person maps to the same label
throughout. Alongside this, the run emits an audit manifest
(`10 identifiers removed` — NAME ×2, DATE ×2, MRN, PHONE, EMAIL, STREET, GEO, ZIP).

## Honest boundaries

This tool **reduces risk and accelerates human review — it does not certify
compliance, and it is not perfect.** No automated de-identifier is: regex and an
offline lexicon will miss a misspelled name, an unusual identifier format, or a
quasi-identifier that only becomes re-identifying in context. It does not, on its
own, satisfy the Safe Harbor "no actual knowledge" clause or perform an Expert
Determination, and it covers **text only** (no images, scans, or biometrics).

Treat the output as a **strong first pass, not a final release**. A qualified
human must review it — especially anything under `needs_human_review` — before
the content leaves a trusted boundary.

## Extending it

The engine is intentionally small and hackable so you can tune it to your
population, locale, and risk tolerance:

- **Name coverage** — add first/last names to `assets/name_lexicon.txt` (one per
  line). This is the highest-leverage change for most teams; it directly widens
  what the deterministic pass catches without touching code.
- **New identifier patterns** — add or tighten regexes in `scripts/deidentify.py`
  (e.g. an internal patient-ID or accession-number format specific to your EHR).
  Each pattern carries a priority so overlaps resolve predictably.
- **Field-name rules** — for structured/record input, extend the field-label map
  so your own JSON keys (e.g. `subscriberId`, `guarantorName`) redact correctly.
- **Standards** — the Limited Data Set mode is a starting point; adjust which
  categories it retains to match your data-use agreement.
- **Stronger recall (optional)** — the model recall pass is where an NER model
  (e.g. spaCy) can be dropped in if your sandbox allows it; the code already
  treats model-supplied names as *additive* so it can't corrupt the audit trail.

Because the deterministic core is the system of record, any extension you add is
still verified by the built-in guard on every run.

## Files

- `SKILL.md` — the agent-facing contract and run instructions.
- `scripts/deidentify.py` — the offline engine (stdlib only).
- `assets/name_lexicon.txt` — bundled offline name gazetteer.
- `references/hipaa-safe-harbor.md` — the Safe Harbor identifier reference.
