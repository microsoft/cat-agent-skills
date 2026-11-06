---
name: improve-legal-prompt
description: >-
  Turns a rough request or an existing draft into one ready-to-use Cowork
  prompt, preserving the user's original legal objective while making document
  scope, party perspective, constraints, missing information handling and
  expected output explicit. Returns the prompt plus two or three improvement
  notes, and never runs it. Use when the user asks to "optimize my prompt",
  "rewrite my prompt for reviewing this agreement", "improve this prompt", "how
  should I ask Cowork to revise the termination clause", "clarify this
  instruction before I run it", or "why isn't my prompt working". Do NOT use for
  the legal work itself — "rewrite this clause" or "make this paragraph clearer"
  is edit-contract, a reasoned answer on a legal question is legal-reasoning,
  and reviewing an agreement is review-contract.
metadata:
  displayName: Improve legal prompt
  category: productivity
  icon: Scales
---

# Improve legal prompt

Convert the user's rough request or existing prompt into one ready-to-use prompt for
Cowork. Preserve the original objective while clarifying the intended legal outcome,
document scope, constraints, required inputs, handling of missing information, and
expected response format.

This skill optimizes the prompt. It does not perform the legal analysis, review,
drafting or editing the prompt describes, and it never guarantees a legal outcome.

## When NOT to Use

Use this skill **only** when the user explicitly asks to create, improve, clarify,
diagnose or rewrite a prompt, instruction or request for Cowork.

- `Rewrite my prompt for reviewing this agreement` — prompt optimization. In scope.
- `How should I ask Cowork to revise the termination clause?` — prompt optimization.
  In scope.
- `Rewrite this clause`, `make this paragraph clearer`, `improve the termination
  provision` — document editing. Use `edit-contract`.
- `Is this clause enforceable?`, `what does this mean for us?` — use
  `legal-reasoning`, or `explain-legal-concepts` for a plain language explanation.
- `Review this agreement` — use `review-contract`.
- A vague legal request does not become a prompt-optimization request merely because
  a better prompt might improve the result.

**Hand-off rule.** If a request, or part of one, matches an item above that names
another skill, do not do that part here — even when the documents are already open
and the work looks quick. Name the skill that handles it (for example, "That part
is a job for `edit-contract`") and stop that part; finish only what belongs to
this skill. If the named skill is not installed, say so plainly and do not attempt
it here.

## Step 1: Identify the source request

- Treat text the user pastes, quotes, labels as a prompt, or describes as their
  instruction as the source.
- Where the turn refers to a prompt from the recent conversation, use the most recent
  unambiguous prompt under discussion.
- If the user gives a target task but no draft prompt, write the prompt from scratch.
- If neither a source prompt nor a target task is identifiable, ask exactly:
  `What prompt would you like me to optimize?`
- Preserve exact values, defined labels, clause numbers, field names, schemas,
  allowed values, word limits, exceptions and formatting requirements unless the user
  asks to change them. Never carry a personal identifier through into the optimized
  prompt: an optimized prompt is re-run downstream, so a national insurance or social
  security number, bank or payment card detail, home address, date of birth, salary or
  health datum copied out of the source request or a supplied document propagates into
  every later run. Replace it with a role or a neutral placeholder, keep the
  instruction intact, and say what you replaced and why; where the source prompt asks
  for such a field as an output, drop that field from the optimized prompt and say so.
  See **Personal data minimisation** in Guardrails.

## Step 2: Use the supplied documents only to resolve context

Read only what is needed to make the prompt accurate. Use `Glob` over `input/**/*`
and `grounding/**/*`, check for an attached OneDrive folder, and
read it in full. When opening a document, use a method that shows tracked changes and comments, and check whether any are present before relying on the text. Refer to
each file by its exact filename.

- Use available context directly when it clearly resolves document type, party names,
  clause names, defined terms, or the location the user means.
- Read the specific file the user points at; read further files, or more of a long
  one, only to resolve an otherwise ambiguous reference or verify exact terminology.
- Include specific document terms in the optimized prompt where they materially
  improve precision.
- Do not broaden the optimization into a document review, and never infer which party
  the user represents or invent a legal or commercial position from the document.

## Step 3: Decide whether clarification is essential

Pause before optimizing when an ambiguity could materially change the legal outcome
or cause Cowork to act on the wrong text. Ask only for the material gaps that apply,
using a question card:

- which party the user represents, or whose position the prompt should advance;
- which clause, section, document, attachment or passage is in scope;
- what outcome words such as `better`, `stronger`, `fairer` or `market standard` are
  intended to achieve;
- which jurisdiction applies, where the task depends on jurisdiction-specific law or
  execution requirements;
- which required commercial value, drafting position, remedy, fallback or source
  precedent should be used.

Do not ask about preferences a sensible default covers, such as minor formatting or
whether the explanation runs to two or three bullets. Ask the smallest set of
questions needed, group related ones, and never repeat what the user already supplied
or the document already establishes. When clarification is essential, ask and **stop**
— do not also supply a knowingly unreliable prompt in the same answer.

## Step 4: Build the Cowork prompt

- Lead with the outcome the user wants Cowork to achieve.
- State the document scope precisely: a complete supplied document named by filename,
  a named provision, a quoted passage, specified attachments or precedents, or a
  general legal question.
- Include party perspective, legal or commercial objective, jurisdiction, audience,
  constraints and source material, where supplied or clarified.
- Separate hard requirements from preferences, so Cowork does not treat a stylistic
  preference as an inviolable legal constraint.
- State what Cowork must do when information is missing, inconsistent, ambiguous or
  requires judgement: identify the gap or ask, never guess.
- Make the expected response explicit — analysis, cited answer, issue table, proposed
  edits, questions for the user, draft language, or another named deliverable.
- For analysis or review, require conclusions grounded in the document text, with
  findings distinguished from assumptions and matters requiring judgement.
- For editing, state the intended legal effect and require the smallest necessary
  change, preserving unaffected wording, defined terms, numbering, formatting and
  substantive meaning.
- For drafting, identify what to create, the source material to follow, the intended
  position, and the facts Cowork must obtain rather than invent.

## Step 5: Preserve the objective, then audit

Keep every meaningful requirement from the source unless it conflicts with the user's
clarified goal. Remove repetition, vague filler and contradictions without changing
the legal position, ambition or scope. Do not add role-play, unnecessary disclaimers,
elaborate process, or deliverables the user did not request. If the user asked only
for clarity, improve clarity without turning the request into a different legal task.

Before answering, check that: Cowork can tell what to do, what material to use, what
not to assume or change, and what to return; the prompt cannot reasonably be misread
as edit-when-analysis-was-wanted, analyse-when-edits-were-wanted, whole-document-when
one provision is in scope, or ask-the-user when an internal assessment was intended;
and no meaningful requirement, exact value, exception or output constraint was lost
against the source.

## Step 6: Output format

When essential information is missing, reply with exactly:

```text
### Clarification needed

[one to three concise, targeted questions]
```

and include no optimized prompt until the user answers. Otherwise reply with exactly
these two sections:

```text
### Optimized prompt

[complete ready-to-copy prompt for Cowork]

### Improvements made

- [specific improvement]
- [specific improvement]
- [optional third specific improvement]
```

Keep the explanation to two or three bullets explaining how the optimization
clarified behavior, scope, required inputs, missing information handling or output
shape — not generic prompt writing advice. Do not answer or execute the optimized
prompt, do not offer multiple variants unless asked, and stop after the improvement
bullets rather than offering to run it.

## Guardrails

- **Read-only, context only.** Inspect documents solely to resolve prompt context,
  reading only supplied files and only when necessary.
- **Never write to a document.** Do not edit, comment on or otherwise modify any
  document; optimizing a prompt must not change the document.
- **Not a legal answer.** Do not produce citations, answer metadata or a
  document-grounded legal conclusion — the output is a prompt.
- **No downstream execution.** Do not hand off to a review, relevance-generation or
  playbook-extraction workflow, and do not open progress tasks to run the downstream work.
- **Personal data minimisation.** Report what the documents say, not who people are.
  Never carry national insurance or social security numbers, bank or payment card
  details, home addresses, dates of birth, salary or health data into an answer, a
  table, a cell, a quotation, a summary, a draft or a suggested wording — including
  the optimized prompt itself and any example it embeds — even where they sit inside
  a matter document and even when the user names the field or asks for the column.
  Refer to individuals by name and role only. If such a detail is material to a
  finding, say that the source contains it and cite the provision rather than
  reproducing it; leave the requested field out and deliver the rest.
- **No assumed perspective.** Never infer the represented party merely because the
  document names the parties.
- **No guarantees.** Never claim the optimized prompt assures a correct legal
  outcome.

## Worked examples

**Essential party perspective is missing.** Source:
`Rewrite my prompt: review this agreement and tell me which clauses I should push
back on.` The agreement identifies a Customer and a Supplier, which does not
establish whom the user represents. Reply with `### Clarification needed` and the
single question "Which party do you represent in this agreement: the Customer or the
Supplier?", and do not optimize until answered.

**Clear, document-aware editing prompt.** Source: `Improve my prompt: revise clause
12 so the Customer gets 30 days to cure a payment breach. Keep everything else the
same.` The optimized prompt reads: "Revise clause 12 of the supplied agreement so
that the Customer has 30 days to cure a payment breach before the Supplier may
exercise the termination right addressed in that clause. Make only the minimum
changes needed to implement that cure period. Preserve all unaffected wording,
defined terms, numbering, formatting, and the clause's other legal effects. If clause
12 does not contain the relevant payment breach termination right, or the requested
change conflicts with another provision, identify the issue rather than guessing or
editing unrelated text. Return the proposed change as a reviewable edit." The
improvement bullets then note that the optimization fixed the target provision, the
exact legal outcome, the preservation requirements, conflict handling and the
expected edit output.
