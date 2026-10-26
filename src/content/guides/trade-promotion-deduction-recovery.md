# Trade Promotion & Deduction Recovery

For deduction analysts and trade managers on the brand side, where retailers deduct against
invoices and the backup arrives as PDFs and portal exports that someone matches by hand
against trade terms and the promotion calendar.

Valid deductions get paid. Invalid ones get written off because chasing them costs more than
they are worth — which is the loss this plugin is built to stop.

It extracts the deduction records and claim backup, matches each claim to the governing
promotion, allowance or trade term, classifies validity deterministically and quantifies the
disputable amount with the calculation shown, and drafts the dispute packet and post-event
brief.

## How it works

1. Extracts and normalises the deduction records and claim backup.
2. Retrieves the governing promotion, allowance or trade term.
3. Matches each claim to its governing term.
4. Classifies validity and quantifies the disputable amount.
5. Drafts the dispute packet and post-event brief.

## Example scenario

*"$25.9k, write it off, the account manager wants no friction."* The arithmetic disagrees:

- One claim bills **12% of volume against a signed term of 8%** — partially valid, with
  $7,300 disputable and the calculation shown.
- A **$4,000 compliance penalty arrives with no backup document at all** — unsupported, and
  fully disputable pending that backup.
- Total disputable: **$11,300**. The write-off decision now happens with the number in front
  of a human, which is the entire point.

## What you bring

ERP deduction and AR records, customer claim backup and portal exports, trade terms and
customer agreements, the promotion calendar, and TPM system records.

## Boundaries

It determines and drafts. It does not post credits, write off deductions, approve trade spend,
change a term or authorise a payment.

Promotion-lift analysis requires account-level financial data and consistent definitions.
Without that foundation, the plugin assesses deduction validity without lift analysis.
