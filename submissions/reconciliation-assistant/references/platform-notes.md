# Platform notes

The reconciliation **method** is identical on every platform. What differs is how the two sources arrive and whether the host can run code. Bind to the mechanism the running session supports.

## Cowork

- **Inputs.** Local or cloud files (`.xlsx`, `.xlsm`, `.csv`, `.tsv`), a sheet within a workbook, or files the user attaches.
- **Execution.** Code execution is available. Drive `scripts/reconcile.py` with the resolved config; it reads both sources, runs the tiered match, ties out, and writes a **formula-driven** workbook (Dashboard + Reconciliation + both source tabs, every number a live Excel formula). Pass `--html <path>` (or set `output.emitHtml`) to also emit the styled HTML dashboard from the same computation. Deterministic and suitable for large files (tens of thousands of rows and beyond).
- **Output.** A new `.xlsx` written next to the inputs (or to a path the user names), optionally alongside a self-contained `.html` dashboard. Sources are never modified.

## Scout

- **Inputs.** Same file types as Cowork. On Scout, cloud documents in OneDrive/SharePoint should be grounded through the host's Microsoft 365 document path when the file is not synced locally; a locally synced or downloaded copy can be read directly.
- **Execution.** Code execution is available. Same `scripts/reconcile.py` path as Cowork, including the optional `--html` dashboard.
- **Output.** A new `.xlsx` (and optional `.html`) in the working directory or a user-named path. Sources are never modified. If the user asks for the result in Teams or email, deliver a link or attachment to the generated file - never paste large tables inline.

## Copilot Studio (GitHub Copilot harness)

- **Inputs.** Tables the user pastes into the conversation, rows returned by a connector the agent has already called, or content from an attached/knowledge document. There is no local file system to browse.
- **Producing the workbook.** On the GitHub Copilot harness, the skill can deliver a real `.xlsx`, not just inline tables. Prefer the capabilities in this order, using whichever the running agent actually exposes:
  1. **Native file creation** (the harness produces files as a conversation output - a "created file" the user downloads). When available, describe the reconciliation workbook and let the harness write it. This is the simplest path and needs no connector wiring. Note it is a preview capability and may require the tenant to have the relevant model access enabled; if it is not available, fall through.
  2. **Excel Online (Business) + OneDrive/SharePoint tools.** The Excel Online connector has no "create a new workbook" action of its own - it operates on an existing file. So create the file first with the OneDrive for Business (or SharePoint) **Create file** action, then populate it with Excel Online **Create worksheet**, **Create table**, and **Add a row into a table** (or a single **Run script** Office Script for richer formatting). Bind to whichever of these tools the agent has been given.
  3. **Inline tables.** If neither native file creation nor the Excel/OneDrive tools are available (for example on the standard harness), render the report sections as tables in the response.
- **Execution of the method.** There is no general Python execution, so perform the **same tiered method analytically** over the tables in context: normalize, match Tier 1-2 exactly, apply the similarity and grouped tiers with the configured thresholds, tie out, and assemble the sections. The workbook (paths 1-2) or the inline tables (path 3) are just how the finished result is delivered.
- **Scale limit.** Analytical reconciliation is reliable for **modest datasets** - as a rule of thumb, up to a few hundred rows per source. Beyond that, accuracy and speed degrade. When the sources are larger, say so plainly and recommend running the skill on a code-capable host (Cowork or Scout) rather than truncating the data or guessing. Never silently reconcile only the first N rows.
- **Output.** A generated `.xlsx` when a file-creation path is available; otherwise the report sections rendered inline - the **Dashboard** blocks (control panel, reconciliation summary, open items by difference type and by root cause, difference by account, difference by company and period, headlines) and the **Reconciliation** detail table for record-to-record mode, or the **Tie-out**, **Detail**, and **Orphans** tables for control-total mode. The same section values can also be delivered as the styled HTML dashboard.

## Binding the capability, not the tool name

Do not hardcode a specific file-read or code-execution tool name; inspect what the running session exposes and bind to it. If the host claims to be code-capable but the execution attempt fails, fall back to the analytical method with its scale caveat rather than aborting - a smaller reconciliation done by reasoning is still useful, an error is not.

## Determinism across platforms

Given the same two sources and the same config, every platform must produce the same classifications. The analytical path and the scripted path implement one method; they must not diverge in how a tie is broken, how tolerances are applied, or when an item is sent to Needs Review.
