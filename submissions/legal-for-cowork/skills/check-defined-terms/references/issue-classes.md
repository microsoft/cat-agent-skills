# The five issue classes — the detail behind Step 4

Classify every problem into exactly one of these five classes. Use these
plain English names in the report exactly as written, never in capital letters.

## Used but not defined

A term is used as though defined — capitalised in a non-sentence-initial
position in a way that signals definitional status, or written in the same form
as other defined terms — but no definition exists anywhere in the document or by
cross-reference.

- Report the term and every place it is used, or the first few uses when there
  are many.
- Watch for the common cause: the definition was deleted in an earlier round of
  negotiation while the usages survived.
- Do **not** report a term as undefined where the document defines it by
  cross-reference to another document or schedule. That is a deliberate drafting
  choice.
- Do **not** report ordinary proper nouns, statute names, month names, product
  names or party names that are simply capitalised.

## Defined but not used

A term is defined but never used again anywhere in the operative text.

- The definition itself does not count as a usage. Neither does a table of
  contents entry or a heading.
- Report it: an unused definition is dead weight and often signals a clause that
  was removed.
- Be careful before recommending deletion — the term may be used only in a
  schedule or annex that is not part of the text you can see. Say so where that
  is possible.

## Defined twice

The same term is defined more than once.

- Report every location, and state plainly whether the definitions are
  **identical** (harmless but untidy) or **substantively different** (a real
  defect — the meaning of the term is now ambiguous).
- A substantively different duplicate is the most serious issue in this audit.
  Say so.

## Inconsistent use

The term is defined once, but used in a form that does not match the definition.

- **Case mismatch** — defined as `Confidential Information`, used as
  `confidential information`. The lower-case use arguably falls outside the
  defined meaning.
- **Variant wording** — defined as `Disclosing Party`, used as `disclosing
  party`, `Discloser`, or `Disclosing party`.
- **A different label for the same concept** — the document defines
  `Confidential Information`, but a clause refers to `Evaluation Material` or
  `Proprietary Information`. This is the fingerprint of a clause pasted from
  another precedent with a different house label. Before reporting any term as
  *used but not defined*, check whether the document already defines a term for
  the same concept: if it does, this is the class to use, and the fix is to
  replace the stray label with the defined term rather than to write a new
  definition. Where the stray label might carry a genuinely different scope,
  report it for decision instead of correcting it, and say why.
- **Singular/plural drift** — defined as `Party`, used as `Parties` where the
  document has not defined the plural.
- **Quotation mark drift** — the anchor uses curly quotes in one place and
  straight quotes in another.

Do not report a case mismatch where the lower-case use is plainly the ordinary
English word in its ordinary sense. Judgement is required; when the reading is
genuinely unclear, report it and say the reading is unclear.

## Definition depends on an undefined term

A definition is itself well formed, but its content relies on another term that
is never defined — `"Affiliate" means an entity controlled by a Group Company`,
where *Group Company* appears nowhere else. The definition looks sound read on
its own, so this defect survives every other check in this list.

- Treat the **depending** definition as the issue and name the missing term
  inside it. Do not also report the missing term under *used but not defined*;
  that gives the reader two rows for one defect.
- Follow the chain more than one step where you need to. A definition that
  depends on a second definition that is itself hollow is still hollow.
- Say what the term is left meaning in practice — usually nothing determinate.
- A term defined by cross-reference to another document or schedule is **not**
  this defect. Its content lives elsewhere by design.

## A note, not a row

While building the definition list, note any term used substantially before it
is defined where the definition sits in the body rather than in a definitions
clause or schedule. That is a readability problem rather than a defect in
meaning, so mention it in your notes rather than giving it a table row.

## Tracked changes

A contract under negotiation usually carries unresolved tracked changes. Where
the file exposes them, insertions and deletions are marked with their author.
**Plain-text extraction usually flattens that markup**: struck-through wording
and its replacement come back as one continuous string with nothing to tell them
apart. Use the extraction route that preserves revision marks where one is
available, and where you cannot tell whether a passage is inserted or deleted,
say so in your notes rather than guessing.

Audit the **accepted working view**: read every insertion as present and every
deletion as absent, regardless of author. That is the document the parties are
converging on, and it is the one whose defined terms must hang together. Applied
to the classes:

- **Not a duplicate definition** where one of the two definitions sits inside a
  deletion. The old wording is on its way out.
- **Not "defined but not used"** where the only uses are inside deleted runs —
  but this is worth a note, because the amendments have left a definition
  stranded.
- **Not "used but not defined"** where the definition itself is inside an
  insertion. It is being added, and in the accepted working view it exists.
- **Do check the inserted wording**: a term first defined in an insertion still
  has to match how the term is used elsewhere, and newly inserted uses are where
  capitalisation drift most often enters.

Where a passage sits wholly inside a deletion, leave it alone: it is absent from
the accepted working view, so do not propose replacing or removing it. This
skill does not accept or reject tracked changes. If the real answer to a finding
is "accept the counterparty's deletion", report it for decision and say so
rather than proposing wording. Where tracked changes materially affect what you
found, say so in your notes, so the reader knows the audit reflects the
marked-up document rather than the original.
