# Classification and confidence — the detail behind Step 4

## The five issue types in full

- **Outdated cross-reference** — the reference points to an existing but wrong
  target, commonly because numbering or structure changed.
- **Referenced provision not found** — the document cites a section, clause,
  paragraph, schedule, annex or exhibit identifier that does not exist in the
  document under review. In the Issue cell, identify the nonexistent reference
  and, when a correction is confident, explain which existing provision appears
  to be intended.
- **Incorrect cross-reference** — the reference identifies the wrong document
  part or uses the wrong label or type, such as "Schedule" instead of "Exhibit".
- **Ambiguous cross-reference** — more than one target is plausible, or the
  intended target cannot be established confidently from the document.
- **Unverifiable reference** — the document under review expressly refers to an
  agreement, schedule, annex, exhibit or other incorporated material whose
  contents are required to verify the reference, but that material is not among
  the files the user uploaded or attached. State what is needed and do not imply
  that the reference is incorrect.

Use the narrowest accurate classification. Do not invent another document part
to make a reference work.

## When a correction is confident

- A correction is confident only when the surrounding text, defined terms,
  heading and document structure identify one intended target, and the
  replacement preserves the substantive legal meaning.
- Treat the correction as confident when the cited identifier does not exist or
  points to the wrong provision **and** exactly one indexed provision matches
  the subject, obligation, procedure, right, definition, schedule, annex or
  exhibit described by the referencing text.
- Do not withhold a suggested correction merely because inferring the intended
  identifier requires comparing the reference's wording with the target index.
  That comparison is the core mechanical task of this skill.
- A correction remains confident when the issue can be fixed by replacing only
  the incorrect identifier and the replacement leaves the surrounding legal
  wording and effect unchanged.
- Classify the issue as ambiguous only when there are two or more plausible
  targets, no indexed target matches the described subject, or selecting a
  target would require resolving a legal, commercial or drafting choice.
- If confidence is insufficient, record **Ambiguous cross-reference**, set the
  suggested correction count to `0 corrections — review required`, and offer no
  suggested wording and no comment for it.
- For an **Unverifiable reference**, set the count to `0 corrections — user
  input required` and offer no suggested wording and no comment.
- Do not ask the user to resolve each ambiguity during the scan. Present it for
  review in the final table.

## Reconciliation checklist before answering

- Every issue appears exactly once in the table.
- Every confident individual replacement is included in a suggested correction
  and counted once, even when several replacements share one entry.
- Ambiguous and unverifiable reference issues have zero corrections and no
  suggested wording.
- The issue list, verified citations and table rows match one-for-one; every
  issue has one citation and its matching reference in the Location cell.
- Where a confident correction is described in the Issue cell, the matching
  suggested correction was actually presented. Never report a confident
  replacement while showing `0 corrections — review required`.
- Issue totals and suggested correction totals are calculated separately. An
  ambiguous issue increases the issue total but adds zero corrections.

## Worked examples

**Outdated reference, confident fix.** The document contains Clause 8.4: "The
Supplier shall comply with the audit procedure in clause 11.2." Clause 11 is now
Notices, while Clause 12.2 is the only audit procedure provision.

- Present one suggested replacement for Clause 8.4, titled `Update audit
  procedure reference`.
- Replace only `clause 11.2` with `clause 12.2`; preserve every other word and
  the existing formatting.
- Reasoning: "clause 11.2" points to Notices. The audit procedure is in clause
  12.2, so the reference should be updated without changing the obligation.
- Report an **Outdated cross-reference** issue at Clause 8.4 with `1
  correction`.

**Two plausible targets.** If both Clauses 12.2 and 14.3 contain plausible audit
procedures and the document does not distinguish them, report an **Ambiguous
cross-reference** at Clause 8.4 with `0 corrections — review required` and
suggest no wording.

**Nonexistent identifier, uniquely identified target.** If Clause 13.2(b) cites a
nonexistent clause but describes the maintenance obligations that appear only in
Clause 13.2(a), treat Clause 13.2(a) as the uniquely identified target. Present
the minimum identifier replacement as suggested wording, report `1 correction`,
and cite Clause 13.2(b) by filename and provision in its Location cell. Do not
downgrade the issue to review required merely because the intended target was
established by comparing the wording with the target index.

**Material not supplied.** If Clause 8.4 instead requires compliance with "clause
6 of the Services Agreement" and the Services Agreement was not uploaded or
attached, report an **Unverifiable reference** with `0 corrections — user input
required` and suggest no wording. Include it in the main table, then add `####
Information needed` with the numbered question: "1. Can you attach or identify
the Services Agreement referenced at Clause 8.4 (Services Terms.docx, Clause 8.4)
so clause 6 can be verified?" Apply the same treatment where an annex, exhibit,
schedule or other incorporated material is referenced but was not provided.
