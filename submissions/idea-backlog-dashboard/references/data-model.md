# Data model

Table `<prefix>_idea` (display "Idea", plural "Ideas", user-owned, notes enabled; entity set `<prefix>_ideas`).

| Column (logical) | Type | Notes |
| --- | --- | --- |
| `<prefix>_title` | Text(200) | Primary name, required |
| `<prefix>_description` | Multiline | |
| `<prefix>_status` | Choice | 100000000 New (default), 100000001 In Progress, 100000002 Completed |
| `<prefix>_priority` | Choice | 100000000 Low, 100000001 Medium (default), 100000002 High |
| `<prefix>_category` | Choice | 100000000 Process, 100000001 Product, 100000002 Technology, 100000003 Customer Experience, 100000004 Other (default) |
| `<prefix>_submittedby` | Text | Submitter name |
| `<prefix>_submitteremail` | Email | |
| `<prefix>_businessvalue` | Multiline | |
| `<prefix>_statusnotes` | Multiline | Updates by owner/team |
| `<prefix>_source` | Text | e.g. "Copilot Studio" |
| `<prefix>_conversationid` | Text | Agent conversation id for traceability |
| `<prefix>_completedon` | Date | Set when status becomes Completed |

Standard `createdon` is used as "Submitted on".
