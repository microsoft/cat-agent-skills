# Output schema

`working/entries.json` must contain a JSON array. Every object supports:

| Field | Required | Rules |
|---|---:|---|
| `id` | no | Stable slug; generated when omitted |
| `title` | yes | Specific, useful, and free of unsupported claims |
| `captureType` | yes | `how-to`, `decision`, `customer-voice`, `demo-highlight`, `lesson-learned`, `onboarding`, or `custom` |
| `session` | yes | Meeting/session title supplied by the user or source |
| `date` | no | ISO `YYYY-MM-DD` when known |
| `presenter` | no | Use only when evidenced; otherwise `Unattributed` |
| `startSeconds` | yes | Non-negative number from transcript timing; milliseconds are preserved |
| `endSeconds` | no | Number greater than `startSeconds` |
| `durationSeconds` | no | Generated from start/end when omitted |
| `recordingUrl` | yes | Automatically resolved HTTPS recording/recap URL |
| `outcome` | yes | One sentence explaining the reusable value |
| `category` | no | User-approved grouping |
| `verification` | yes | `verified`, `needs-review`, or `blocked` |
| `approval` | yes | `approved`, `held`, or `rejected` |
| `evidenceNote` | no | Short provenance note without full transcript text |
| `sourceLabel` | no | Human label, not a local filesystem path |

The builder rejects any entry without a validated HTTPS recording URL. All three final
outputs contain only entries that are verified, explicitly approved, recording-linked,
and free of validation issues. Held, rejected, needs-review, and blocked candidates remain
only in the review conversation or temporary working data and never appear in downloadable
HTML, CSV, or JSON.
