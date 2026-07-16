# Reference: Commenting a Word Document (.docx)

When the attached file is a `.docx`, follow these steps:

1. Open and analyze the .docx file using the built-in Copilot Studio Analyze skill. Extract the main topic, key claims, structure, and tone.
2. Identify locations throughout the document that would benefit from a native Word comment — including unsupported assertions, unclear statements, missing context, outdated information, contradictions, or places where a citation would strengthen the content.
3. Research the document's topic using any available sources — including internal documents, emails, Microsoft Teams messages, approved knowledge sources, and web research tools — to gather relevant facts, definitions, recent updates, and citations.
4. **Before authoring `comments.json`, extract raw paragraph text directly from the document XML** to find exact verbatim strings. Unzip the .docx and read `word/document.xml` — do not rely on what a rendered viewer shows. This is the only way to capture curly/smart quotes (`""`), curly apostrophes (`'`), em dashes, and other typographic characters exactly as they appear in the file.

   > ⚠️ **`doc.paragraphs` does not include table cells.** python-docx's `doc.paragraphs` only iterates paragraphs directly in the main document body (`<w:body>`); paragraphs nested inside table cells (`<w:tbl>` → `<w:tr>` → `<w:tc>` → `<w:p>`) are silently excluded, with no error. If the document contains tables, you must **also** iterate `doc.tables` → each `row.cells` → each `cell.paragraphs` to reach text (and tracked changes like `w:ins` / `w:del`) inside table cells — or bypass python-docx entirely and use lxml's `body.iter(w("p"))` on the raw XML, which finds **all** `<w:p>` elements regardless of nesting depth (this is what the inject script already does). Relying solely on `doc.paragraphs` will silently miss any content inside table cells.
5. Author a `comments.json` file for `scripts/inject-comments-docx.py`. It is a JSON array of objects, each with the keys `id`, `search_phrase`, and `paragraphs`:
   - `id` — a unique integer starting at 0
   - `search_phrase` — **must appear exactly once in the document, and must contain no quotes or apostrophes.** Two hard rules:
     - **Uniqueness:** before using a phrase, verify it occurs exactly once in the document. If a document has repeated stories, boilerplate, or duplicate paragraphs, a generic phrase will silently match the *first* occurrence — anchoring the comment to the wrong paragraph (e.g. one with no tracked change), so it never appears where intended. When commenting on a tracked change, prefer text from the change itself (inserted `w:ins` text is still captured by `iter(w("t"))`) or a phrase from the immediately surrounding *unique* context.
     - **No quotes/apostrophes:** curly/smart quotes (`""`), curly apostrophes (`'`), and their straight equivalents (`"`, `'`) will silently fail to match if there is any character mismatch in the raw XML. The safest and confirmed fix is to simply avoid them — pick plain words from the same paragraph instead.
   - `paragraphs` — a list of strings; each string becomes a separate paragraph inside the Word comment. Start each comment with the appropriate emoji:
     - 💡 when adding context, a definition, a citation, a relevant update, or a suggested improvement
     - 🧹 when flagging an inaccuracy, ambiguity, contradiction, missing information, or something that needs cleanup

   Example `comments.json`:
   ```json
   [
     {
       "id": 0,
       "search_phrase": "revenue grew by 40 percent in the last quarter",
       "paragraphs": [
         "🧹 This figure has no citation. The Q3 finance report shows 32 percent growth — please verify the source.",
         "See: internal Finance/Q3-summary."
       ]
     },
     {
       "id": 1,
       "search_phrase": "our platform is fully compliant with all regulations",
       "paragraphs": ["💡 Consider naming the specific frameworks (SOC 2, GDPR) to make this claim concrete."]
     }
   ]
   ```
6. Run `scripts/inject-comments-docx.py` **once**, passing the **original uploaded .docx** as the input, a new path as the output, and your `comments.json`. Inject all comments in a single pass:
   ```bash
   python scripts/inject-comments-docx.py <input.docx> <output.docx> <comments.json>
   ```
   **Never run the script a second time on the output file** — doing so creates duplicate and empty comment bubbles in Word.
7. If a re-run is needed for any reason, **delete the previous output file first**, then re-run the script against the original input.
8. Do NOT rewrite, delete, or silently modify any of the document's original text. The script only adds comments — it never edits the document body.

## How inject-comments-docx.py works

The script (`scripts/inject-comments-docx.py`) is the injection engine. It:
- Unzips the .docx, parses `word/document.xml` using `lxml`
- Searches each paragraph for the `search_phrase` and anchors the comment there
- Builds `word/comments.xml` with proper Open XML structure, setting `w:author` to `Copilot Studio AI`
- Patches `[Content_Types].xml` and `word/_rels/document.xml.rels` so Word recognises the comments
- Writes the final .docx to the output path

**Inputs are all passed on the command line** — the script has no hardcoded filenames or comment text:
- `<input.docx>` — the original uploaded document
- `<output.docx>` — the new path to write the commented document to
- `<comments.json>` — the comments you authored (see the schema in step 5)

**Dependency:** requires `lxml` — preinstalled in the Copilot Studio sandbox, so no `pip install` is needed.

## Guidelines

- **Never alter the author's original wording — flag issues in a comment instead.** The script only adds comments; it must never edit, delete, or rewrite the document body.
- Use the Copilot Studio Analyze skill first before researching so you understand the full document before authoring `comments.json`.
- Only add comments where they genuinely help — do not comment on every sentence.
- Comments should be factual, concise, and sourced when possible.
- If the document topic is outside available knowledge sources, note that in the summary and recommend the author seek a subject matter expert.

> The hard rules for extraction and `search_phrase` (raw-XML text, uniqueness, no quotes/apostrophes) and the run-once rule are defined in Steps 4–8 above — they are not repeated here.

## Examples

**Business report with unsupported statistics**
- Analyze the .docx, identify statistics without citations, research current benchmarks, author `comments.json` with sourced notes, run scripts/inject-comments-docx.py, return the commented .docx.

**Technical article with outdated information**
- Use the Analyze skill to extract claims, research the latest updates, author `comments.json` flagging outdated statements with current context, run scripts/inject-comments-docx.py, return the updated .docx.

## Sandbox Execution Tips

These tips apply when generating the output `.docx` via Python inside the sandbox:

- **The confirmed working pattern is:**
  1. Remove the pre-existing read-only output file at `/app/created/filename_commented.docx` before doing anything else.
  2. Write your injection script to `/app/workspace/` (or another writable scratch path).
  3. Run it using `exec(open('/app/workspace/script.py').read())` inside a `python3 -c "..."` call within the double-nested `sandbox-exec → bash → sandbox-exec → python3 -c` pattern.

- **Always remove the pre-existing output file first.** The sandbox pre-places a read-only file at the output path. Every write attempt will fail with `PermissionError` until it is removed.
- **Use `exec(open(...).read())` to run longer scripts.** Write the full script to `/app/workspace/`, then load and execute it inline via `python3 -c "exec(open('/app/workspace/script.py').read())"`. This avoids heredoc quoting failures while keeping the correct nesting level.
- **The correct nesting is double — not triple.** The pattern is `sandbox-exec → bash → sandbox-exec → python3 -c "..."`. A third nested layer loses write permissions.
- **Only write the final output to `/app/created`.** Use `/app/workspace/` for intermediate/script files. `/tmp/` is unwritable from Python in the sandbox.

