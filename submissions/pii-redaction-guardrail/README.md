# PII Redaction Guardrail

Before customer emails, support tickets, meeting notes, or survey responses
get turned into a case study, blog post, or shared doc, this skill scans for
personal data that identifies a real person and asks how to handle each one.
It never redacts silently.

## How it's different from phi-deidentifier

This gallery already has [`phi-deidentifier`](../phi-deidentifier), which
covers the 18 HIPAA Safe Harbor identifiers for clinical text specifically.
This skill is the general-purpose counterpart: everyday business content
(sales, support, marketing, HR) that was never clinical to begin with, so
HIPAA's identifier list doesn't apply, but the person in it is still real.

## How it works

`scripts/scan_pii.py` finds email addresses, IPv4 addresses, US SSN-shaped
numbers, and credit card numbers verified with a Luhn checksum (all high
confidence), plus phone-number-shaped digit runs flagged as low confidence,
since phone formats vary too much across countries to match reliably. The
agent adds what the script can't see, such as names, job titles, addresses,
and employee IDs, from context.

## Usage

```bash
python scripts/scan_pii.py path/to/file-or-folder
python scripts/scan_pii.py path/to/file --json
echo "some pasted text" | python scripts/scan_pii.py -
```

No dependencies beyond the Python standard library.

## Limits

Pattern-matching, not a legal determination. A clean scan is not proof of
GDPR, CCPA, or any other regulation's compliance. Phone-number matches in
particular are noisy by design; treat them as "look at this," not "this is
PII."

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
