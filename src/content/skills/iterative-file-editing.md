---
name: Iterative File Editing
description: "In Copilot Studio, re-sending an edited file under the same name fails to deliver it — the change is made but never reaches the user. This skill gives each iteration a new version-numbered filename (report_v1.docx, report_v2.docx…) so every update actually lands in the chat as its own attachment."
agentDescription: "Use this skill whenever you create or edit ANY file for the user in the Copilot Studio container — a document, spreadsheet, slide deck, code file, data export, anything. It keeps your work-in-progress durable and shows the user an updated version after every change, so the two of you refine the same file together across turns — the user sees real progress each round, earlier work is never lost, and neither of you has to start over. Apply it from the very first file you make."
platforms: [Copilot Studio]
tags: [files, iteration, workflow, collaboration, productivity]
author: Adi Leibowitz
authorUrl: "https://github.com/adilei"
authorGithub: adilei
version: 1.0.0
createdAt: 2026-07-21
updatedAt: 2026-07-21
featured: true
---
When you send the user an updated version of a file you've **already** sent them,
give it a new filename with an incremented version number — `report_v2.docx`,
`report_v3.docx`, and so on. If you reuse the filename the user has already
received, the delivery event won't fire and they'll never get the update, even
though the file changed. A filename they haven't seen before is what triggers the
send.

So annotate each iteration with the next version number, and the user receives
every version as its own attachment.

## Example
```
report_v1.docx   first version sent to the user
report_v2.docx   the same file after "make the timeline more detailed"
report_v3.docx   after "also add a budget table"
```
