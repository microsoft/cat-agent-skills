# Output modes: explanation, message drafts, confidentiality check and delivery

Loaded on demand by `explain-legal-concepts`. Nothing here overrides the guardrails in SKILL.md.

## Mode A — explanation

Provide the complete explanation in chat by default, including for three or more agreements. Create
a `.docx` only where the user explicitly asked for a Word file; length alone is never a file
trigger. For a `.docx`, use Cowork's built-in Word document creator and follow its generation, validation, visual QA
and delivery workflow — the creator owns placement. Confirm the file exists from the creator's report
before naming it, and where the user attached a OneDrive folder, upload that new deliverable there. Never upload a source.

Sections, in this order:

1. **The short version** — three to five bullets: what the deal does, with whom, for how long, at
   what cost.
2. **What we have committed to** — obligations on the reader's side, with clauses.
3. **What the other side has committed to** — obligations on the counterparty's side, with clauses.
4. **Dates and deadlines that matter** — each with its trigger.
5. **Money** — fees, increases, caps, timing, and what changes them.
6. **How this ends** — expiry, renewal, exit rights, notice and conditions.
7. **What you need to do** — actions, owners and dates where stated.
8. **What to check before you act** — every `Check with Legal`, `Business decision` and
   `Not in the documents` item under its exact label, stating what is unresolved and what would
   resolve it.
9. **Where this comes from** — a compact document-and-clause source map.

For a specific question, replace sections 1-6 with the direct answer, the operative wording and its
dependencies, and keep sections 7-9.

## Mode B — email or Teams message draft

Same substance, shorter, and always a draft.

- **Email:** subject; one-line purpose; plain bullets; a "what we need from you" line with a date
  where one exists; a contact line. Aim for 150-250 words.
- **Teams:** under 120 words, three to five bullets, one ask, one contact.
- **Fidelity beats word count.** Where agreements differ, give each its own line. Cut adjectives,
  background and context before cutting a number, condition, exception, coverage gap or caveat.
- Mode B produces two things: the message and the explanation behind it. Build Mode A as well and
  deliver both in chat unless a supported file was explicitly requested. The message carries only
  the useful clause references; the explanation carries the complete references, actions, labels and
  source map.
- Close every draft with one honest line: it summarises the documents, it is not legal advice, and
  Legal should be asked before relying on it.

Always show the draft text in the reply first. "Give me an email I can send" means show the text,
not create or send a mailbox item. Only where the user explicitly asks to put the email in their
mailbox drafts and supplies or approves the recipient, create an Outlook draft, then say
it was not sent and should be reviewed in Outlook. For a message with no recipient use
`[Add recipient]`; where the user names a person, resolve them with an available people or directory
tool before creating a draft — never guess an address. Teams posting is outside this skill's scope
and is deferred to the user.

## Confidentiality check for message drafts

Commercially sensitive detail includes prices, discounts, rebates, liability caps, volume
commitments, concessions, settlements, personal data, and named individual obligations or
guarantees.

- **Narrow distribution** — a named person or small team identified by the user: flag each sensitive
  item in one line and continue drafting.
- **Broad distribution** — a channel, distribution list, unidentified audience, or an audience wider
  than the document's existing readership: stop and ask in a question card before including
  sensitive detail. Name each item and offer to retain, generalise or omit it. Do not decide alone.

Judge sensitivity for that reader: a price shown to the team administering it may be expected;
another customer's rebate or an individual's guarantee is not. Never remove a sensitive item
silently, invent a vaguer figure, or widen the audience beyond the user's request. Personal
identifiers listed in the personal data minimisation guardrail are never included in any draft, at
any distribution width, and the question card is not a route to reinstate them.

## Delivery reply

For an explanation: the Mode A sections in chat or in the delivered `.docx`; the exact filename and
its cloud link or file reference, never a container path; and a closing line giving documents read and
documents not read.

For a message: the draft text and its companion explanation; whether a mailbox draft was created and
that nothing was sent; and the confidentiality items flagged.
