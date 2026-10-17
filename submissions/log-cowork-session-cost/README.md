# Log Cowork Session Cost

Cowork tells you what a session cost, but only once, in the chat, and only if you ask. This skill turns that one number into a record you can actually learn from: a short write-up of what drove the cost, and one row you paste into a running log. After a few weeks you can see which prompts, skills, models, and effort levels are expensive, and do something about it.

## Before you start

- **Your own workbook.** A starter workbook is bundled at `assets/cowork-cost-log-template.xlsx`. Save your own copy to OneDrive or a team SharePoint site before first use. Its `Log` sheet has 13 columns matching the skill's output exactly, 30 formatted rows ready to go, a `Summary` sheet that totals spend and breaks it down by effort level and model, and an `Instructions` sheet.
- **Nothing else.** No connectors, no permissions, no setup. The skill only reads what you paste into the chat.

## How to use it

At the end of a Cowork session:

1. Run `/cost` yourself. It is a UI command, Cowork cannot run it for you. You will get something like `1,259.1 credits used for this task so far`.
2. Say **"log this session's cost"** and paste the credits figure in.
3. Tell the skill which model ran and which effort level was set. `/cost` reports neither, so the skill will ask if you do not say, and it will not assume Medium just because that is the default.

You get back two things: a full write-up in the chat (cost drivers, inefficiencies, recommendations, a one-line verdict), and one pipe-delimited row as plain text on its own line.

Paste that row into a single empty cell in column A of the `Log` sheet, then split it with **Data > Text to Columns > Delimited > Other: |**. It fills columns A to M. Add your own reflections to `Observation Notes` afterwards.

## Effort level

Cowork lets you set an effort level per task, from Light through to Max, with Medium as the default. Higher effort means more thorough responses, but it takes longer and burns credits faster. It is usually the single biggest lever on what a session costs, often bigger than the choice of model, which is why it gets its own column right beside Model.

The `Cost by effort level` block on the Summary sheet gives you sessions, total credits, and average credits per session at each level. That last column is the one to watch. If High and Medium are producing work of the same standard for the same kind of task, your default should come down.

## Good to know

- **It never touches your workbook.** By design. The skill outputs text and you paste it, so nothing can overwrite a log you have been building for months. It will not search OneDrive or SharePoint for the file either.
- **Client names are stripped.** Every entry is anonymised before it is shown, including the quoted prompt and any file names. A cost log tends to get shared around, so it should not carry client names into a spreadsheet.
- **Credits convert at 0.01 USD each.** That is the published Copilot Credits rate. If Microsoft changes it, edit the one line under `Configuration` in `SKILL.md`.
- **Paste the credits figure exactly as Cowork printed it**, separators and all. The skill strips the comma when it writes the row, so `1,259.1` goes in as `1259.1` and the cell stays numeric. Reformatting it yourself first only risks a typo in the one field that has to be exact.
- **There is no token breakdown, and the skill will not invent one.** Cowork's older `/usage` command gave a cache write / cache read / input / output split, and it is no longer available. A single credits figure cannot be split back out, so the cost drivers are reasoned from what the session actually did rather than from token maths. That turns out to be more useful anyway.
- **It will not guess.** If the credits figure, the model, or the effort level is missing, it asks. Fabricating any of them would quietly poison the log.
- **The commentary columns are one phrase each.** The detail belongs in the chat write-up. A spreadsheet cell holding a paragraph is a cell nobody reads.
- **Thirty rows are ready to go.** When you run out, select the last row of the table and drag the fill handle down. The formats and the dropdown come with it.
- **Adding your own columns is fine.** The skill always stops at column M, so anything you add from N onward, your own notes or return figures, is left alone.
