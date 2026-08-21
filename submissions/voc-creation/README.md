# VoC Creation

Use this Scout skill to turn customer asks into CLS CRM Voice of Customer product feedback records. It is designed for customer-facing teams that need consistent CRM entries, customer association records, and explicit review before anything is saved.

The skill emphasizes safe defaults: it creates top-level Product Feedback records first, links customer accounts afterward, sets Post to ADO for customer association rows, and never writes CRM-visible content until the user approves the exact payload.

## What it helps with

- Drafting CRM-ready Voice of Customer product feedback from user notes and optional work context.
- Structuring feedback into the expected problem, desired outcome, and impact sections.
- Choosing practical default classifications when the user has not supplied them.
- Previewing every CRM-visible field before creating any record.
- Verifying the parent VoC record and customer association after save.

## Requirements

- Scout with access to the user's authenticated CLS CRM environment.
- Permission to create `cls_productfeedback` records and link `cls_accountproductfeedback` customer rows.
- Access to customer account records in CRM.
- Optional Microsoft 365 access if the user asks the agent to use recent emails, meetings, chats, or transcripts as context.

## Safety model

The skill treats CRM as a shared system of record. It requires an explicit approval step before creation, avoids unnecessary private work details, does not create test records, and never sends outbound communications.
