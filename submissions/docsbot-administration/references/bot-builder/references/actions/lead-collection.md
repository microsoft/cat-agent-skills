# Lead Collection

Read this only from the actions index when configuring lead forms, lead fields, lead messages, or lead-related handoff behavior.

Lead collection is stored on the bot as `leadCollect` and is written with `update_bot`. The widget also uses `labels.leadCollectMessage` for the message shown before the form.

## When To Enable

Enable lead collection when the bot needs follow-up identity or qualification context:

- Presales, demo, quote, trial, or contact-us workflows.
- Support escalation where name/email and issue summary are needed before handoff.
- High-value onboarding or implementation questions.
- Internal handoff workflows where staff need structured fields.

Do not enable lead collection just to collect data. For public bots, keep fields minimal and leave `piiRedaction` false unless the user asks for it or a concrete compliance requirement exists.

## Modes

`mode` must be one of:

- `before_response`: show the form before the bot responds. Use for presales/demo capture or when collecting contact information is the primary goal.
- `before_escalation`: show the form only before human escalation. Use for support bots that should answer first and collect contact info only when a handoff is needed.

## Plan Gates

- Lead collection requires Personal plan or higher.
- Custom fields beyond `name` and `email` require Standard plan or higher.
- If a bot has custom fields and the widget is served to a plan without custom-field access, the widget limits the form to default `name` and `email`.
- When downgrades are relevant, custom lead fields can block downgrade until removed.

## Field Shape

Each field should have:

- `key`: unique input key. Valid characters are letters, digits, `_`, `.`, `:`, `[`, `]`, and `-`; unsafe characters are stripped.
- `label`: user-facing label.
- `type`: field type.
- `required`: boolean.
- `placeholder`: optional for `text`, `email`, `tel`, `url`, `textarea`, and `select`.
- `help`: optional helper text.
- `options`: required for `select`.
- `min`, `max`, `step`: only for `number`, `date`, `time`, `datetime-local`, `month`, and `week`.
- `minLength`, `maxLength`: only for `text`, `email`, `tel`, `url`, and `textarea`.
- `pattern`: only for `text`, `email`, `tel`, and `url`.

Supported field types:

```text
text, email, tel, url, number, textarea, select, date, datetime-local,
time, month, week, color
```

Default fields are:

```json
[
  { "key": "name", "label": "Name", "type": "text", "required": true, "autocomplete": "name" },
  { "key": "email", "label": "Email", "type": "email", "required": true, "autocomplete": "email" }
]
```

Save-time normalization:

- `enabled` defaults to `true` in accepted input, but is stripped from persisted bot settings when enabled.
- `datetime` normalizes to `datetime-local`.
- Duplicate keys are rejected.
- `select` fields require at least one option.
- Select option values are sanitized with the input-key sanitizer; labels may preserve display spacing. Prefer simple option values and verify readback.
- Autocomplete and input mode are inferred for common keys/types.
- Unsupported placeholder, range, length, pattern, and option fields are removed.

## Payload Examples

Basic presales form:

```json
{
  "leadCollect": {
    "mode": "before_response",
    "fields": [
      { "key": "name", "label": "Name", "type": "text", "required": true },
      { "key": "email", "label": "Email", "type": "email", "required": true },
      { "key": "company", "label": "Company", "type": "text", "required": false },
      {
        "key": "interest",
        "label": "What are you interested in?",
        "type": "select",
        "required": true,
        "placeholder": "Choose one",
        "options": [
          { "value": "demo", "label": "Book a demo" },
          { "value": "pricing", "label": "Pricing" },
          { "value": "support", "label": "Support" }
        ]
      }
    ]
  },
  "labels": {
    "leadCollectMessage": "Before we continue, could you share a few details?"
  }
}
```

Support escalation form:

```json
{
  "leadCollect": {
    "mode": "before_escalation",
    "fields": [
      { "key": "name", "label": "Name", "type": "text", "required": true },
      { "key": "email", "label": "Email", "type": "email", "required": true },
      { "key": "issueSummary", "label": "Brief issue summary", "type": "textarea", "required": true, "maxLength": 1000 }
    ]
  },
  "labels": {
    "leadCollectMessage": "Before I hand this off, please share the best contact details and a short issue summary."
  }
}
```

Disable lead collection:

```json
{ "leadCollect": false }
```

## Form Design Rules

- Keep public forms short. Default to `name` and `email`, then add only fields that materially improve routing or follow-up.
- Use `before_escalation` for support unless the user wants lead capture before every answer.
- Use `before_response` for sales/demo bots only when capturing a lead before answering is acceptable.
- Use concise labels and options; long options may be normalized or render poorly.
- Prefer `textarea` for open-ended goals or issue summaries.
- Prefer `select` when routing matters and choices are known.
- Do not collect sensitive personal data unless the user explicitly requests it and the compliance posture is clear.

## Prompt Instructions

Add prompt guidance whenever lead collection affects behavior:

```text
When the user asks for a demo, quote, sales follow-up, or pricing consultation, collect lead details using the configured lead form before continuing. Keep the conversation helpful and explain why the information is needed.
```

```text
For normal support questions, answer from documentation first. If the user asks for a human handoff or the issue cannot be resolved, use escalation and collect the configured lead details before handoff.
```

## Verification

- Read bot settings after save and verify `leadCollect.mode`, fields, labels, required flags, select options, and `labels.leadCollectMessage`.
- Verify saved fields did not lose unsupported properties unexpectedly.
- Verify select option labels/values after normalization.
- After test chats, use `list_leads` to verify captured lead metadata when authorized.
- Use `export_leads` only when the user asks for a CSV export. It returns a signed URL.
- Use `delete_lead` only for explicit cleanup/privacy deletion, or disposable test lead cleanup.
- Verify plan behavior: Personal+ for lead collection, Standard+ for custom fields.
- For public widgets, verify PII redaction choice separately; do not turn it on just because lead collection is enabled.
- Include the configured mode, fields, lead message, and rationale in handoff.
