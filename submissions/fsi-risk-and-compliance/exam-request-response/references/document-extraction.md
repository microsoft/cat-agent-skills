# Document Extraction — Risk & Compliance

Governs reading any supplied document: policies, control matrices, request lists, SOC 2 reports,
consent orders, rule reprints, onboarding files, committee minutes.

---

## 1. Routes

1. **A configured connector** (DMS, GRC, audit platform), if it holds the document.
2. **The supplied file** — read it directly.
3. **Microsoft 365** — SharePoint, OneDrive, Teams, Outlook attachments.
4. **A retrieval route** for public instruments — see `reg-source-access.md`.
5. **Ask the user to supply it**, by name.
6. `NOT RETRIEVED`. Never reconstruct a document from memory.

**Scanned and photographed documents are a primary path, not a fallback.** SOC 2 reports, consent
orders, and onboarding files arrive as image-only PDFs constantly. Read them directly — an
embedded text layer is not required, and the user is never asked to convert a file first.

---

## 2. Input quality gate

Before extracting, judge whether the document can be read reliably.

| Condition | Action |
|---|---|
| Text legible throughout | Extract |
| Legible but degraded in places | Extract; mark the specific unreadable items `NOT LEGIBLE` |
| Substantially illegible | Stop. Report what is unreadable and ask for a cleaner copy. **Do not extract a partial set and present it as the document** |
| Wrong document supplied | `GAP — supplied document is <what it is>, not <what was requested>` |
| Password-protected or truncated | `NOT RETRIEVED — <reason>` |

**Never guess at an unreadable value, and never silently omit one.** `NOT LEGIBLE` names what
could not be read and where, and states the remedy: a cleaner copy.

A `NOT LEGIBLE` item is **never** reconstructed by inference from surrounding text unless you
state plainly that you did so and show the reasoning. Never do it at all for a citation, section
number, date, identifier, or monetary amount in a regulator-facing artifact.

---

## 3. Cite to the location, always

Every extracted fact carries **document name, version or date, and page or section**. Quotations
are verbatim and marked as quotations.

| Document type | Minimum locator |
|---|---|
| Policy, procedure, standard | Name · version · approval date · section number |
| Control matrix | Name · date · control ID · row |
| SOC 2 | Name · report period · section (II / III / IV) · page |
| Consent order | Agency · docket/file number · paragraph number |
| Request list (PDL/IRL) | Exam name · list date · item number **as printed** |
| Rule reprint | Agency · document number · page |
| Minutes, working paper | Body · meeting date · page |

**Never renumber a request-list item.** Regulators and auditors track by their own numbering; a
register that renumbers items is unusable in the conversation it exists to support. Preserve the
printed identifier exactly, including sub-item lettering, and keep gaps in the sequence visible.

---

## 4. Document-specific extraction rules

### Policies and procedures

Establish, before any content is used:

- **Name, version, approval status, approval date, owner.** An unapproved draft is
  `DRAFT — not approved` and is never the control of record.
- **Effective period.** A superseded version is not the current control — if both are present,
  say which governs and keep the other visible.
- **Scope.** Which entities, business lines, products, and jurisdictions it covers. A policy that
  does not cover the subject in question cannot close a gap for it, no matter what it says.

Where version or approval cannot be established → `GAP — policy version not established`. It is
**not** scored as coverage.

### Request lists (PDL / IRL)

- Preserve item numbering exactly (§ 3).
- Split compound items. One item asking for "policies, procedures, and training materials" is
  **three** evidence obligations; a register that treats it as one will under-deliver. Keep the
  original item number and add sub-letters, stating you did so.
- Capture the **due date per item** where stated, and the overall response date.
- Capture any stated format, period, or population requirement — "for the period 1 Jan to 30 Jun",
  "all instances", "a sample of 25". These determine whether evidence is responsive.
- An item you cannot interpret is `GAP — item text ambiguous`, raised as a clarification question
  for the examiner. Never guess at intent.

### SOC 2 reports

These are the most misread documents in third-party risk. Extract all of:

| Field | Why it is load-bearing |
|---|---|
| **Type I or Type II** | Type I tests **design at a point in time**. It says nothing about operating effectiveness |
| **Report period** | A period ending before your review period leaves an uncovered gap — state it |
| **Trust services criteria in scope** | Security only, or also Availability / Confidentiality / Processing Integrity / Privacy. Out-of-scope criteria are untested, not passed |
| **Systems and locations in scope** | A report covering a different product than the one you are buying is `GAP — scope mismatch` |
| **Opinion type** | Unqualified / qualified / adverse / disclaimer. **Quote it — never paraphrase** |
| **Exceptions and deviations** | Each with the auditor's description and management's response, quoted |
| **CUECs** | See below |
| **Subservice organizations** | And whether treated **inclusive** or **carve-out**. A carve-out means those controls were **not tested** |

**Complementary user-entity controls are the point of the exercise.** A CUEC is a control the
vendor assumes *you* operate. An unadopted CUEC is an **open risk owned by the firm**, not by the
vendor. Extract every CUEC and mark each `adopted` / `not adopted` / `NOT DETERMINED — owner must
confirm`. Never mark one adopted without evidence.

A clean opinion with twelve unadopted CUECs is not a clean result. Say so.

### Consent orders and enforcement actions

- Separate **alleged conduct** from **findings** from **agreed corrective action**. Most orders
  settle **without admission or denial** — if that language is present, quote it and carry it
  into every statement about the respondent.
- Capture the **rules actually cited** in the order, and retrieve them (`reg-source-access.md`) —
  do not rely on the order's characterisation of what the rule requires.
- Capture penalty amounts, remediation obligations, deadlines, and any monitor or reporting
  requirement.
- **Never restate an allegation as established fact.** Write "the order alleges", not "the firm
  did".

### Onboarding and entity documents

- Extract identifiers exactly as printed: registration number, jurisdiction, incorporation date,
  registered address, officers, owners, and stated percentages.
- An identifier that is partly illegible is `NOT LEGIBLE` — **never** partially reconstructed.
  Identity resolution (`house-rules.md` § 7) depends on these being exact.
- Ownership percentages that do not sum to 100% are reported as stated, with the discrepancy
  flagged. Never normalised.
- A document's date and its currency are different questions. A certificate of incorporation is
  current as to formation and says nothing about present ownership.

---

## 5. Cross-document consistency

When more than one document is in scope:

- **Same subject, different documents** → reconcile explicitly. Where they conflict, report both
  with citations and flag the conflict. **Never pick one silently**, and never average.
- **Same document, different versions** → the approved current version governs; the other stays
  visible.
- **A document referenced but not supplied** → `NOT RETRIEVED — <name> referenced in <source> but
  not provided` where it was requested and not supplied; where it was never requested,
  `GAP - <name> retrieval not attempted (Gn)`. A referenced-but-absent policy is a gap, never an assumption of coverage.
- **Amendment chains** → where amendments are numbered and one is missing, the set is incomplete.
  Say which is missing and mark affected terms as potentially superseded.

---

## 6. Numbers

Where a document carries figures — penalty amounts, sample sizes, exception counts, ownership
percentages, transaction thresholds:

- Record the **scale and currency as printed**. "$ in thousands" missed is a silent 1,000× error.
- Record sign conventions as printed; parentheses mean negative.
- Any total you compute is computed with a live formula, never pasted, and the components are
  shown.
- Where a printed total does not equal the sum of its printed components, **re-read first** —
  most failures are extraction errors. If confirmed as printed, report it as a **finding**, with
  both figures and the difference. **Never adjust a component to force a tie, and never plug a
  total.**
- Counts of findings, exceptions, or items **exclude** rows carrying markers, and the count states
  how many rows it covers.
