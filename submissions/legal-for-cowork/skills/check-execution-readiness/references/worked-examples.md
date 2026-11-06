# Worked examples — execution readiness

Two findings that show the boundary between a **missing fact** (which may be
asked about under `Information needed`) and a **judgement matter** (which is
reported in the table and never pushed to the user as a question).

## 1. Incomplete signature block — a missing fact

The Supplier signature block contains `[NAME OF SIGNATORY]` and the document
does not identify that person anywhere.

Correct handling:

- Report the incomplete field and state that the signatory's name is required
  before execution.
- Quote the exact signature block wording, and attribute it in the Location cell
  to the exact filename plus the signature block — for example
  `Supplier signature block, "Okafor Consultancy Agreement v7.docx": "Name:
  [NAME OF SIGNATORY]"`.
- Ask, under `#### Information needed`:
  `1. Who is the authorized signatory for the Supplier?`

Note what is **not** done: no name is proposed, no signatory is inferred from a
party clause or a covering email, and no view is given on whether that person
would have authority to sign.

## 2. Drafting note about the form of execution — a judgement matter

The document contains `[Drafting note: consider whether execution as a deed is
required]`.

Correct handling:

- Report that the form of execution requires review, quoting the drafting note
  and attributing it to its location.
- In `What is needed before execution`, state the decision that must be
  resolved — whether the instrument is to be executed as a deed — without
  proposing the answer.
- Do **not** ask the user a question under `Information needed`: this is not a
  missing fact, and the skill does not advise on execution formalities.

## 3. Signature block containing personal details — completeness without values

A witness block is laid out as `Witness name: …  Witness address: …  Date of
birth: 14 March 1971`.

Correct handling:

- Report the field state only: "the witness address field is blank; the witness
  name and date of birth fields are completed."
- Cite the signature block as the Location. Do **not** quote the date of birth,
  the address, or any identifier value anywhere in the answer, even if the user
  asks for a column or list of them.
- Where a quotation would otherwise carry such a value, quote the surrounding
  label instead and say that the field is completed at that location.

This is the Personal data minimisation guardrail applied at the one place this
skill is most exposed: a signature block holds personal data by definition, and
confirming that it is complete never requires reproducing it.
