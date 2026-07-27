---
name: pii-redaction-guardrail
description: >-
  Use this skill before publishing, sending externally, or feeding to a
  third-party service any text that came from real people, such as customer
  emails, support tickets, survey responses, meeting notes, or case studies,
  to catch personal data that needs redacting first. For clinical or
  health-record text specifically, use the phi-deidentifier skill instead,
  which covers the full HIPAA Safe Harbor identifier set.
---

Scan for personal data before content leaves the conversation, and always ask
before deciding what to do with a finding. Redacting real people's data is a
judgment call, not something to automate silently.

## Instructions

1. This applies whenever content derived from real individuals is about to be
   published, sent to someone outside the original context, or passed to a
   third-party API/service that shouldn't see it: blog posts drawn from
   customer interactions, anonymized case studies, shared meeting notes,
   exported survey data, anything pasted into a public forum or a prompt to
   another tool.

2. Run the bundled scanner when a Python environment is available:

   ```bash
   python scripts/scan_pii.py <file-or-directory>
   ```

   It also reads stdin for pasted text. Without Python, read the content
   directly and check for the categories below.

3. The scanner finds: email addresses, US SSN-shaped numbers, IPv4 addresses,
   and credit-card numbers confirmed with a Luhn checksum (all high
   confidence), plus phone-number-shaped digit sequences (low confidence,
   since phone formats vary too much by country to be precise). Treat every
   phone hit as "check this," not "this is one."

4. Add what the scanner cannot see: full names, job titles combined with a
   company (often enough to identify someone), physical addresses, dates of
   birth, national ID numbers outside the US SSN format, employee/customer
   ID numbers, and anything else that could identify a specific person in
   context even without matching a regex.

5. Report findings and ask how to handle each one. Options are typically:
   remove entirely, replace with a role description ("the customer", "a
   support engineer"), or replace with a consistent pseudonym if the same
   person is referenced more than once and the narrative needs to stay
   coherent. Don't pick silently; the right choice depends on what the
   content is for.

6. When a consistent pseudonym is used, keep a mapping for the duration of the
   task so the same real person maps to the same pseudonym throughout, but
   don't persist that mapping anywhere the user hasn't asked it to be saved.

## Guardrails

- Never publish or send content containing an unresolved finding. Get a
  decision on every item first.
- Never invent a redaction that changes the meaning of the surrounding text
  (e.g., turning "the CFO" into a role that's no longer true doesn't count as
  successful anonymization if the identifying detail was the *company*, not
  the title).
- Phone-number matches are low-confidence by design. Don't present them with
  the same certainty as an email or a Luhn-valid card number.
- This is not a legal compliance determination (GDPR, CCPA, etc.). It catches
  patterns; it doesn't certify the result meets a specific regulation's bar.

## Tone

Practical and specific: what was found, why it identifies someone, what the
options are. No boilerplate privacy lecture.
