---
name: log-cowork-session-cost
description: |
  Produces a cost record for a Copilot Cowork session from the /cost command's
  Copilot Credits figure, derives an approximate USD cost at 0.01 USD per
  credit, and outputs a copy-paste ready pipe-delimited row for a Copilot
  Cowork cost log workbook. Asks the user for the credits figure, plus the
  model and the effort level that /cost does not report, and never guesses any
  of them. Shows the full entry in chat, then the condensed row as one
  pipe-delimited string to paste into a single Excel cell and split with Text
  to Columns. Does not write to the workbook or ask for observation notes,
  those are added by hand. Use when asked to "log this session", "log this
  cost", "record this session's cost", "add this to the cost log", or after
  running /cost at session end. Do NOT use for general expense reports,
  invoices, or non-Cowork costs, and never to write directly to the workbook.
cowork:
  category: productivity
  icon: ReceiptMoney
---

# Log Cowork session cost

Produce a cost record for a Copilot Cowork session from the `/cost` credits figure, show it in chat, and output one copy-paste ready row for the user's own cost log workbook. This skill never writes to that workbook.

## When NOT to Use

- General expense reports, invoices, or reimbursement claims that have nothing to do with a Copilot Cowork session, use a general expense or bookkeeping skill instead.
- Any request to open, edit, upload, or write to the cost log workbook, or another workbook, directly. This skill only ever produces a row for the user to paste in themselves.
- Requests for a token-level or per-component cost breakdown (cache write, cache read, input, output). A single `/cost` credits figure cannot be split this way, do not fabricate one.
- Tracking cost for tools or platforms other than Copilot Cowork.

## Configuration

This skill never writes to the workbook. It produces a row for the user to paste into the `Log` sheet themselves. Do not search OneDrive or SharePoint for the workbook, and do not open, edit, upload, or copy it.

**Workbook:** the user's own copy of the bundled `assets/cowork-cost-log-template.xlsx`, whose `Log` sheet carries the Step 4 columns 1 to 13 in the same order. Setting that copy up is covered in the README and is not part of this run.

**Credits to USD rate:** 0.01 USD per credit, per [Microsoft's Copilot Credits documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-messages-management). Update this line if Microsoft changes the rate.

## Step 1: Get the raw data

Copilot Cowork reports session cost through the `/cost` command as a single Copilot Credits figure (the older `/usage` command, which gave a token-level breakdown, is no longer available). `/cost` is a UI command the user runs, Cowork cannot run it on the user's behalf, so always ask the user to run it and paste the figure in. Ask for whatever is missing:

- The `/cost` figure, in credits. This is always the total cost of the session. Take it exactly as `/cost` printed it, thousands separators and all, and never ask the user to reformat it. Strip the separators yourself when writing the row, so 1,259.1 is recorded as 1259.1 and the cell stays numeric in Excel.
- Which model actually ran. `/cost` does not report this. If the session ran on Cowork's "auto" model selection, record it as "Auto". If the user has not stated which model ran, always ask, do not guess or leave it unconfirmed.
- Which effort level the session ran at. `/cost` does not report this either. It is set per task in Cowork next to the model, and the options are Light, Medium, High, Extra High, and Max, with Medium as the default. Effort level has a large effect on credits burned, often larger than the choice of model, so a row without it cannot explain its own cost. If the user has not stated it, always ask, do not assume Medium just because it is the default.
- The project/skill context and the prompt used.

**Anonymise sensitive details.** Never include client or organisation names, or other identifying or confidential details (people's names, internal programme or system names, locations, IDs), anywhere in the entry, the Project/Context line, the quoted prompt, file names, the workbook row, or anywhere else. Replace them with a generic placeholder that still conveys the type of work, in the form "[Client] [Task]". Do this even if the detail appears in the prompt or a file name as given, redact it rather than carrying it through.

## Step 2: Derive the USD cost

Derive the USD total from the credits figure using the rate in Configuration:

    Total Cost (USD) = credits x 0.01

For example, 1259.1 credits is 12.59 USD (rounded to cents). A single credits figure cannot be split into cache write, cache read, output, and input, so there is no per-component breakdown, do not fabricate one.

## Step 3: Produce the chat entry

Show the full entry in chat using this structure. This is the detailed, readable record of what happened this session, kept in chat for immediate review even though the row in Step 4 is what gets pasted into the workbook.

```markdown
### [Date], [Anonymised project or context]: [Task or skill run]

**Project / Context:** [What this was for and which skill(s) ran, client name replaced by a generic placeholder.]

**Prompt:**
> "[Prompt used, quoted as given, client name redacted.]"

**Actual cost:**

| Metric | Value |
|---|---|
| Cost (Credits) | [N.N] |
| Total Cost (USD) | $[X.XX] |
| Model | [model, or "Auto"] |
| Effort | [Light, Medium, High, Extra High, or Max] |

**Main cost drivers:**

1. [Driver, one line.]
2. [Driver, one line.]

**Inefficiencies identified:**

- [One line each.]

**Optimisation recommendations:**

1. [Change, estimated saving if derivable.]

**Net assessment:** [One line.]
```

Fill the credits figure, the derived USD, the model (or "Auto" if the session ran on auto model selection), and the effort level. There is no per-component table, do not invent one.

Where the effort level looks like it drove the cost, say so in the cost drivers rather than leaving it to the reader. A high credits figure at Max effort on routine work is a cost driver and usually a recommendation as well.

Before finalising, scan the whole entry, including the Project/Context line, the quoted prompt, and any file names mentioned, for the client name and replace it with the placeholder from Step 1 if it has crept in anywhere. Keep everything else brief:

- 2-4 ranked cost drivers, one line each, reasoned qualitatively from what the session did (there is no token data to rank them by).
- A short list of inefficiencies, one line each. Check each candidate against the three recurring patterns below before treating it as new, and name the pattern if it matches:
  - **Reference relevance.** Files or data pulled into context for one turn stayed in context for later turns that did not need them.
  - **Quality vs cost.** A more capable model, or a longer approach, was used where a cheaper one would have produced the same output.
  - **Skill output mechanism.** The output was written or moved by a roundabout route (extra copy, upload, or path deliberation steps) instead of straight to the output folder.
- 1-3 recommendations, with an estimated saving only where it can reasonably be derived.
- One line for net assessment.

Do not include an observation notes section in the chat entry. That gets added separately to the workbook, by hand, do not ask for it or leave a placeholder.

## Step 4: Condense to a workbook row

Produce one row for the `Log` sheet, in this column order. This table is the single source of truth for the row layout and is reused in Step 5. Every commentary field is a single short phrase or sentence, never a list, the detail already lives in the Step 3 chat entry.

| # | Column | Content |
|---|---|---|
| 1 | Date | Today's date, YYYY-MM-DD |
| 2 | Project / Context | The anonymised Project/Context line from Step 3 |
| 3 | Skills and Plugins | The exact name(s) of any skill(s) or plugins actually invoked during the session (via the Skill tool), comma-separated if more than one, matching the name shown in the workspace's Skills and Plugins list, even if only invoked at the start and the rest of the session was back-and-forth conversation. "None" if no skill or plugin was invoked (for example, when only MCP tools were called directly) |
| 4 | Tools | The MCP tools/connectors actually called during the session, comma-separated by their tool name (for example dataverse-create_record, outlook-GetMessage). "None" if no tool calls were made. |
| 5 | Model | The user-confirmed model, or "Auto" if the session ran on Cowork's auto model selection |
| 6 | Effort | The user-confirmed effort level, exactly one of Light, Medium, High, Extra High, or Max |
| 7 | Cost (Credits) | The `/cost` figure as a plain number, no thousands separators. This is always the session total. |
| 8 | Total Cost (USD) | The derived cost, credits x 0.01, as a plain number, not a string with a $ sign |
| 9 | Top Cost Driver | The single highest-ranked driver from Step 3, condensed to one short phrase |
| 10 | Key Inefficiency | The single most significant inefficiency from Step 3, or "None identified" if there genuinely was none |
| 11 | Top Recommendation | The single highest-value recommendation from Step 3, with the estimated saving if one was given |
| 12 | Net Assessment | The Net assessment line from Step 3 |
| 13 | Observation Notes | Leave blank. Never fill this in, it is added separately by hand. |

If the user's own workbook carries extra columns beyond field 13, for example their own notes or return figures, those are filled in by hand and are none of this skill's business. The row always stops at field 13.

Apply the anonymisation rule to every cell, not only the chat entry.

## Step 5: Output the row for copy and paste

This skill does not write to, upload, or copy the workbook. Produce the Step 4 row as a single pipe-delimited text string, columns in the Step 4 order (1 to 13), separated by `|`.

**The row always has exactly 13 fields and exactly 12 `|` separators.** Field 13, Observation Notes, is always blank, so the string always ends with a `|` and nothing after it. Without that trailing pipe the row splits into 12 columns and the Observation Notes column is never created. Leave any other blank field genuinely empty between its pipes rather than collapsing it. Count the separators before you output the row: 12, every time.

**Output the row as plain text on its own line.** Do not wrap it in a fenced code block, do not indent it, and do not format it as a markdown table. Code blocks do not render reliably in Cowork, and a row inside one is awkward to select and copy.

Three rules keep the row copyable as plain text:

- Put a short label line immediately above it, such as `Row to paste:`, then the row on the next line with nothing else on that line.
- Start the line with the date value, never with a `|`. A line beginning with a pipe can be picked up as a markdown table and rendered as one, which destroys the string.
- Do not also produce a separate labelled table. The pipe-delimited string is the only output format.

The user pastes this string into a single cell in Excel, then splits it into columns themselves using **Data > Text to Columns > Delimited > Other: |**. Include this instruction whenever you output the row.

If the user explicitly asks for a file rather than pasted text, you may write a new single-row CSV to the Cowork output folder. That is the only file this skill ever writes, and it is never the live workbook.

## Step 6: Output

Output the Step 3 chat entry as plain markdown text in the chat, then the Step 5 pipe-delimited row as plain text on its own line under a short label. Nothing in the output is wrapped in a code block.

Close with a one-line reminder that the row is ready to paste into a single Excel cell, to run Text to Columns (Delimited, Other: |) to split it, and that the Observation Notes cell is filled in by hand.

## Writing standards

- Tables carry the detail. Keep prose to single lines.
- Every workbook commentary cell is one short phrase or sentence. If it needs a list, it belongs in the Step 3 chat entry, not the workbook.

## Guardrails

- Never fabricate the credits figure, the model, the effort level, or a per-component cost breakdown. If any of the credits figure, the model, or the effort level is missing, ask for it, do not estimate or guess. In particular, never default the effort level to Medium because it is Cowork's default, the whole point of the column is to record what actually ran.
- Always strip thousands separators from the credits figure before writing it to the row. The user pastes whatever `/cost` printed, separators included, and normalising it is this skill's job, not theirs. `1,259.1` becomes `1259.1`. A separator left in lands the cell as text rather than a number, and the workbook's totals then skip that row without reporting anything.
- Never search for, open, edit, upload, or copy the cost log workbook. This skill outputs text for the user to paste in themselves, and writes nothing else except the optional single-row CSV described in Step 5, on explicit request.
- Always anonymise the client name, everywhere it could appear (Project/Context line, prompt quote, file names), before showing any output.
- Never invent cost drivers, inefficiencies, or recommendations that are not reasoned from what actually happened in the session.
- Leave the Observation Notes cell blank. Never ask for it or fill it in, it is added by hand, separately.
- Never wrap the pipe-delimited row in a fenced code block, and never let it start a line with a `|`. Both stop it rendering as a copyable string in Cowork.
- Never output a row with fewer or more than 12 `|` separators, and never drop the trailing `|` that holds the blank Observation Notes field. A row that does not split into 13 columns is malformed.
