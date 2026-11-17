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
- **Execution.** The GitHub Copilot harness sandbox can run Python, so run `scripts/reconcile.py` directly (same as Cowork/Scout) whenever files are available in-session. This is the primary path because it preserves full determinism, scale, and formula-driven workbook output.
- **Workbook creation.** The script writes the `.xlsx` itself; no Excel Online connector choreography is required for standard runs.
- **Plain results companion.** The script also writes `<out>.results.json` and `<out>.results.csv` (or paths passed via `--results-json` / `--results-csv`) so agents can summarize computed numbers without relying on Excel formula recalculation.
- **Fallback when code execution is unavailable.** If a specific harness run cannot execute Python, fall back to the analytical method over in-memory tables and state the scale caveat (best for modest datasets, typically a few hundred rows per source). Never silently reconcile only the first N rows.
- **Output.** Script path: formula-driven `.xlsx` plus machine-readable JSON/CSV (and optional `.html`). Fallback path: inline report tables (or tool-generated file if the host exposes that capability).

## Binding the capability, not the tool name

Do not hardcode a specific file-read or code-execution tool name; inspect what the running session exposes and bind to it. Prefer direct Python execution of `scripts/reconcile.py` whenever available; if execution fails in a supposedly code-capable host, fall back to the analytical method with its scale caveat rather than aborting.

## Determinism across platforms

Given the same two sources and the same config, every platform must produce the same classifications. The analytical path and the scripted path implement one method; they must not diverge in how a tie is broken, how tolerances are applied, or when an item is sent to Needs Review.
