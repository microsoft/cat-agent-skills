---
name: PHI De-identifier
description: Redact the 18 HIPAA Safe Harbor identifiers from clinical text (or produce a Limited Data Set) with consistent pseudonym tokens and an audit manifest of what was removed.
agentDescription: "Use this skill whenever the user asks to de-identify, redact, anonymise, scrub, or remove PHI/PII from clinical text, notes, transcripts, or documents before sharing, exporting, or using them for analytics, testing, or demos — e.g. \"de-identify this note\", \"strip patient info\", \"make this HIPAA Safe Harbor compliant\", \"produce a limited data set\". It removes the 18 HIPAA Safe Harbor identifiers and emits an audit manifest of what was removed. Run the bundled scripts/deidentify.py — do NOT hand-write redaction regexes yourself. This skill prepares de-identified text and an audit trail for human review; it does NOT certify legal compliance or make a formal expert determination."
platforms: [Cowork, Copilot Studio, Scout]
tags: [healthcare, hls, phi, privacy, redaction, hipaa, compliance, scripts]
author: Rafael Lopez Alcaraz
authorUrl: "https://github.com/rafalcaraz"
authorGithub: rafalcaraz
version: 1.0.0
createdAt: 2026-07-19
updatedAt: 2026-07-19
bundle: bundles/phi-deidentifier.zip
---
# PHI De-identifier

De-identify clinical / health text to the **HIPAA Safe Harbor** standard (or a
**Limited Data Set**) using the bundled, offline `scripts/deidentify.py`. Every
run produces two things: the **redacted text** and an **audit manifest** listing
what was removed, by category, plus anything that needs human review.

## When to use

- "De-identify / anonymise / scrub / redact this note (or file / folder)."
- "Remove patient identifiers before I share this."
- "Make this Safe Harbor compliant" or "produce a limited data set."
- Preparing PHI-free samples for demos, test fixtures, analytics, or model prompts.

Do **not** use it to answer clinical questions or to claim legal certification —
it is a mechanical redactor plus an audit trail for a human to verify.

## How to run it

Always call the bundled script; never improvise redaction logic.

```bash
# Safe Harbor (default): writes NOTE.deid.txt + NOTE.manifest.json next to input
python scripts/deidentify.py NOTE.txt

# Limited Data Set: retains dates and city/state/ZIP, strips direct identifiers
python scripts/deidentify.py NOTE.txt --mode limited

# Inline text, machine-readable result to stdout
python scripts/deidentify.py --text "John Doe, SSN 123-45-6789" --json

# HYBRID name recall: pass the person names YOU (the agent) spotted in free prose
python scripts/deidentify.py --text "<text>" --names "Rafael Alcaraz,Ngozi Okafor" --json

# STRUCTURED / JSON input: redact by FIELD NAME (MRN, City, Employer, DOB, ...)
# Use this whenever the input is a JSON object or a key/value record — NOT free text.
python scripts/deidentify.py intake_record.json --format record --json

# ALSO emit a reversible token->value crosswalk (SENSITIVE — re-identifying)
python scripts/deidentify.py NOTE.txt --map crosswalk.json
```

Steps:

1. Identify the input (a file path, a folder, or inline text) and the target
   standard: **Safe Harbor** (default) or **Limited Data Set** (`--mode limited`).
2. **Pick the right mode for the shape of the input.** If the input is a
   **structured record** — a JSON object, or clear `Field: value` key/value pairs
   (e.g. an intake record, an API payload, an exported row) — run it with
   `--format record`. Record mode maps each field by its NAME (MRN, City,
   Employer, DOB, SSN, …) and redacts deterministically; free-text mode will
   MISS quoted/structured identifiers like `"MRN": "33108876"` because there is
   no adjacent label to anchor on. Use the default (free-text) mode only for
   prose. Still run the name-recall pass on any free-text field VALUES (e.g. a
   `ChiefComplaint` or `Notes` field that contains a person's name).
3. **Name-recall pass (do this every time on free prose).** Before running, read
   the text yourself and list every PERSON name and PLACE (city / facility) you
   can identify — including unusual or non-English names that a regex or the
   bundled lexicon would miss (e.g. "Rafael Alcaraz", "Okafor"). This is the
   model/agent contribution to the hybrid; you are the recall booster.
4. Run `scripts/deidentify.py`, passing the names from step 3 via
   `--names "Name One,Name Two"` (or a `--names-file` with `{"names":[...],
   "places":[...],"orgs":[...]}`). The script deterministically redacts every
   occurrence, tokenizes consistently, runs its guard, and writes the manifest.
   The script — not your paraphrase — is the auditable system of record.
5. Return the **redacted text** exactly as produced, and summarise the
   **manifest**: how many identifiers of each category were removed.
6. **Surface `needs_human_review`.** Names caught heuristically, and any unknown
   capitalised text flagged for review, are listed there — tell the user these
   must be verified before release, and that bare names in free prose may still
   be missed.
7. Only write the `--map` crosswalk when the user explicitly needs to
   re-identify later; warn that it is sensitive and must be stored securely,
   separately from the de-identified output.

## Use as a safety net before an outbound action

Agents often carry actions that emit content — **Send Email, Create Record,
Post Message, Export**. When an agent maker points one of those actions at this
skill (e.g. an instruction like *"before Send Email, de-identify the content
using phi-deidentifier"*), apply this skill as a gate:

1. Take the exact text about to leave the agent (e.g. the email Subject + Body,
   or the field values of the record).
2. De-identify it with the steps above (including the name-recall pass).
3. Populate the action's inputs from the **redacted** result only — never from
   the original text.
4. If `needs_human_review` is non-empty, **do not fire the action**; show the
   redacted draft plus the review items and ask the user to confirm first.
5. On success, tell the user the content was de-identified and how many
   identifiers were removed. Never place the `--map` crosswalk in the outbound
   content or in chat.

The maker only needs to reference this skill by name in the action's instruction;
the operational steps above live here, in the skill, so they do not have to be
re-written per agent.

## What it removes (HIPAA Safe Harbor, 18 identifiers)

Handled **deterministically by regex** (high confidence): names in labelled
fields and after titles, street addresses, city + state, geographic ZIP
(truncated to 3 digits; restricted prefixes zeroed), all date elements finer
than year, ages 90+ (aggregated), phone, fax, email, URL, IP address, SSN, MRN,
health-plan / account / member numbers, certificate / license / DEA / NPI
numbers, device serial numbers, VIN.

Handled **best-effort** and flagged for review: person names in free prose.
Names are caught by (a) title/label patterns ("Patient: …", "Dr. …") and (b) a
bundled offline **name lexicon** (`assets/name_lexicon.txt`) that catches many
bare names with no title or label — all fully local, no network or extra
packages, so it works in locked-down agent sandboxes (e.g. the Copilot Studio
Python container where you cannot `pip install`). Names not in the lexicon can
still be missed and word-like names may be over-redacted, so **human review of
free text is required**; extend the lexicon for your population. (If a runtime
already ships spaCy it is used automatically as a bonus, but installation is
never assumed.) City/state written without a comma or trailing ZIP may also be
missed. **Full-face photos and biometric identifiers are out of scope** — this
skill processes text only; call that out if the source contains images.

## Transformations (so downstream data stays useful)

- **Consistent pseudonyms:** each distinct value maps to a stable token, e.g.
  every occurrence of the same MRN becomes `[MRN-1]`, so linkage is preserved
  without exposing the value.
- **Dates → year only:** `03/15/1985` → `[DATE:1985]` (Safe Harbor keeps year).
- **Ages:** ≤89 retained; 90+ → `[AGE:90+]`.
- **ZIP → first 3 digits:** `98104` → `[ZIP:981XX]`; HHS-restricted low-population
  prefixes → `[ZIP:000]`.
- **Limited Data Set mode** keeps dates and city/state/ZIP intact while still
  removing names, contacts, SSN, MRN, and account numbers.

## The audit manifest

`NOTE.manifest.json` records the mode, a per-category count summary, one entry
per token with a **salted hash** of the original value (never the plaintext),
the `needs_human_review` list, and explanatory notes. Use it as the evidence
trail for a reviewer — it answers "what did the tool remove, and what still
needs eyes?" without itself containing PHI.

## Guardrails

- **Never claim compliance.** Report what was removed; a qualified human makes
  the Safe Harbor / expert-determination call.
- **Never invent or "restore" content.** Only redact.
- **Do not paste the crosswalk into chat** or co-locate it with the output; it
  re-identifies the data.
- **Always relay `needs_human_review`** and remind the user to review free text —
  regex cannot guarantee every bare name or unusual identifier is caught.
- Text only: if the source has images/scans, say so and recommend a separate
  image-redaction step.

## References

- `references/hipaa-safe-harbor.md` — the 18 identifiers, ZIP/date/age rules,
  and Safe Harbor vs Limited Data Set, as implemented here.
