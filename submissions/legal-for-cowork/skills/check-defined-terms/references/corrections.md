# Suggested corrections — the detail behind Step 6

You cannot change the user's document, and nothing in this skill edits it. Set
out a suggested correction — clearly labelled as suggested wording for the user
to apply themselves — only where the correct fix is unambiguous from the
document itself.

## Suggest a correction for

- **Inconsistent use** — a case, variant, or quotation mark mismatch where the
  definition makes the intended form certain. Give the corrected wording for
  each affected passage, changing only the term. One correction per passage; do
  not restate the clause.
- **Defined twice, identically** — suggest deleting the redundant later
  definition, or give replacement wording for the passage that removes just the
  duplicated definitional sentence where the passage carries other operative
  text.

## Do not propose a correction for

- **Used but not defined** — you cannot know what the parties intended the term
  to mean. Report it and, if useful, say in prose where a definition would sit.
- **Defined but not used** — deleting a definition is a substantive decision,
  and the term may be used in material you cannot see. Suggest deletion only if
  the user explicitly asks you to remove unused definitions.
- **Defined twice, differently** — choosing between two meanings is the user's
  decision. Report both, explain the difference, and ask which should govern.
- **Definition depends on an undefined term** — you cannot know what the missing
  term was meant to mean, so you cannot repair the definition that relies on it.

Set out corrections **grouped by term**, taking terms in the order of your report
tables, so all the corrections for one term sit together. Every location may
carry at most one suggested correction. Never tell the user a correction has
been made, applied or accepted — the document is unchanged until they apply the
wording themselves.

## What each suggested correction says

The reader may act on a correction without re-reading the report, so each one
must stand on its own.

**Label** — follow this schema exactly: `<Fix type> — <term>`. Use these fix-type
labels and nothing else, so the corrections read as a consistent list:

| Fix type | Use it when |
| --- | --- |
| `Capitalisation` | The term is used in the wrong case for the defined form. |
| `Wrong term used` | A near-miss variant is used where the defined term was meant. |
| `Quotation marks` | The anchor uses curly quotes in one place and straight quotes in another. Never for a later use that is simply unquoted — that is the normal pattern, not a defect. |
| `Duplicate definition` | The same definition is stated twice and the later one is redundant. |

So: `Capitalisation — Confidential Information`, `Wrong term used — Business
Day`, `Duplicate definition — Affiliate`. Never write "Fix inconsistency",
"Suggested edit" or "Update text", which say nothing when stacked ten deep. Keep
the whole label under 80 characters; shorten a long term with an ellipsis rather
than dropping the fix type. Do not append the clause reference to the label. If
a correction genuinely fits no label above, do not invent one — that is a sign
the fix is a matter of judgement, so report it in prose instead.

**Where to apply it** — the document name and the clause, section, schedule or
page, and a short verbatim quote of the wording as it currently stands.

**Suggested wording** — the corrected passage in full, verbatim, clearly labelled
as suggested wording the user applies, with nothing changed but the term.

**Reasoning** — one sentence on why the change is right, in the voice of a lawyer
explaining to another lawyer: "The term is defined in capitals at cl 1.1, so the
lower-case use here arguably falls outside the defined meaning." Never "as
requested" or "the user asked".

## Volume

A defined terms audit can produce far more corrections than any other request
here — a single mis-capitalised term may recur twenty times. Set out every
correction that qualifies. A partly corrected document is the worse outcome,
because afterwards the reader cannot tell which uses were checked and which were
never reached.

- Order corrections by the consequence of the defect, taking terms in the order
  of your report tables.
- Never silently drop a correction. If you genuinely cannot set them all out in
  one turn, say plainly how many remain and offer to continue — "There are 14
  further uses of the same mismatch in the schedules; say the word and I'll
  suggest those too." Then give the rest if the user asks.
- Report every issue you found, even where you suggest no correction for it.

Where the user explicitly asks you to comment, flag, annotate or leave a note,
give the notes as a clearly labelled list keyed to the document name and clause,
rather than as replacement wording. You cannot insert comments into the user's
document.

## Chat reply voice

The reply the user reads is separate from the suggested corrections themselves.

- Write it in the present tense as a live recommendation — "Here are suggested
  corrections for the inconsistent uses of *Disclosing Party*."
- Never narrate the tooling: no "I staged…", "I have staged…", "I applied the
  change…". The user applies each suggestion themselves.
- Refer to them as "suggested corrections" or "suggestions" — never "edits I
  made" or "changes to your document".
- These rules apply equally when you suggest nothing: describe what you found
  and why no correction is offered.

Follow the drafting conventions the user has given — in the conversation, in the
document, or in their personal instructions — and match the document's existing
house style, numbering and spelling in any wording you suggest.

## Worked examples

**Example 1 — "Check the defined terms in this NDA."**

`NDA.docx` (extract):
- cl 1: "This Agreement is made between Acme Ltd (the "Disclosing Party") and Beta Inc (the "Receiving Party")."
- cl 1.1: ""Confidential Information" means all non-public information disclosed by the Disclosing Party to the Receiving Party."
- cl 4.1: "The Receiving Party shall not disclose any confidential information to any third party."
- cl 9.2: "The Receiving Party shall return all Materials on termination."

Suggested correction:

> `Capitalisation — Confidential Information`
> Where to apply it: NDA.docx, cl 4.1 — "The Receiving Party shall not disclose any confidential information to any third party."
> Suggested wording: "The Receiving Party shall not disclose any Confidential Information to any third party."
> Reasoning: The confidentiality obligation uses the lower-case phrase, which arguably falls outside the defined meaning and narrows the protection; capitalising it ties the obligation to the definition. Change nothing else in the paragraph.

Final reply: prose, no tables — two issues do not justify them. Two or three
sentences: the confidentiality obligation at NDA.docx, cl 4.1 uses the
lower-case phrase, so a correction is suggested capitalising it to match the
definition; and `Materials` carries a return obligation on termination at
NDA.docx, cl 9.2 but is never defined, so no correction is offered and the user
must say what it covers. End there: no closing tally.

**Example 2 — "Any duplicate definitions?"**

`Supply Agreement.docx` (extract):
- cl 1.1: ""Business Day" means a day other than a Saturday, Sunday or public holiday in England."
- Sch 2: ""Business Day" means a day on which banks are open for general business in New York."

No correction is suggested: the two definitions differ substantively, so
choosing between England and New York is the user's decision. Report the
conflict, quoting both definitions and citing Supply Agreement.docx, cl 1.1 and
Sch 2; explain that any deadline calculated by Business Days is now ambiguous,
and ask which definition should govern.
