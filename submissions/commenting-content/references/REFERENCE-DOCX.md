# Reference: Commenting a Word Document (.docx)

When the attached file is a `.docx`, follow these steps:

1. Open and analyze the .docx file using the built-in Copilot Studio Analyze skill. Extract the main topic, key claims, structure, and tone.
2. Identify locations throughout the document that would benefit from a native Word comment — including unsupported assertions, unclear statements, missing context, outdated information, contradictions, or places where a citation would strengthen the content.
3. Research the document's topic using any available sources — including internal documents, emails, Microsoft Teams messages, approved knowledge sources, and web research tools — to gather relevant facts, definitions, recent updates, and citations.
4. **Before building the COMMENTS list, extract raw paragraph text directly from the document XML** to find exact verbatim strings. Unzip the .docx and read `word/document.xml` — do not rely on what a rendered viewer shows. This is the only way to capture curly/smart quotes (`""`), curly apostrophes (`'`), em dashes, and other typographic characters exactly as they appear in the file.
5. Build the `COMMENTS` list for `scripts/inject-comments-docx.py`. Each entry is a tuple of `(id, search_phrase, comment_paragraphs_list)`:
   - `id` — a unique integer starting at 0
   - `search_phrase` — **always choose a portion of the target paragraph that contains no quotes or apostrophes.** This is a hard rule: curly/smart quotes (`""`), curly apostrophes (`'`), and their straight equivalents (`"`, `'`) will silently fail to match if there is any character mismatch in the raw XML. The safest and confirmed fix is to simply avoid them — pick plain words from the same paragraph instead.
   - `comment_paragraphs_list` — a list of strings; each string becomes a separate paragraph inside the Word comment. Start each comment with the appropriate emoji:
     - 🐛 when adding context, a definition, a citation, a relevant update, or a suggested improvement
     - 🧹 when flagging an inaccuracy, ambiguity, contradiction, missing information, or something that needs cleanup
6. Run `scripts/inject-comments-docx.py` **once**, with `INPUT` set to the **original uploaded .docx** and `OUTPUT` set to a new output path. Inject all comments in a single pass. **Never run the script a second time on the output file** — doing so creates duplicate and empty comment bubbles in Word.
7. If a re-run is needed for any reason, **delete the previous output file first**, then re-run the script against the original input.
8. Do NOT rewrite, delete, or silently modify any of the document's original text. The script only adds comments — it never edits the document body.

## How inject-comments-docx.py works

The script (`scripts/inject-comments-docx.py`) is the injection engine. It:
- Unzips the .docx, parses `word/document.xml` using `lxml`
- Searches each paragraph for the `search_phrase` and anchors the comment there
- Builds `word/comments.xml` with proper Open XML structure, setting `w:author` to `Copilot Studio AI`
- Patches `[Content_Types].xml` and `word/_rels/document.xml.rels` so Word recognises the comments
- Writes the final .docx to the `OUTPUT` path

**Only two things change per run:**
- `INPUT` / `OUTPUT` — set to the actual file paths
- `COMMENTS` — populated by you based on the document analysis and research

**Dependency:** requires `lxml` (`pip install lxml`)

## Guidelines

- Use the Copilot Studio Analyze skill first before researching so you understand the full document before building the COMMENTS list.
- Only add comments where they genuinely help — do not comment on every sentence.
- **Always extract raw paragraph text from `word/document.xml`** before writing search phrases — never guess based on rendered output.
- Make `search_phrase` values short and unique within the document so the script anchors comments to the correct paragraph.
- **Never include quotes or apostrophes in a search phrase — this is a hard rule.** A confirmed real failure: smart/curly quotes in the document (`""`, `'`) silently fail to match when straight quotes (`"`, `'`) are used, and vice versa. The fix is to always pick a nearby plain-word portion of the same paragraph that contains no quotes or apostrophes at all.
- **Run the injection script exactly once**, from the original input file, with all comments in a single pass. Never re-run against a previously produced output file.
- Comments should be factual, concise, and sourced when possible.
- Never alter the author's original wording — flag issues in a comment instead.
- If the document topic is outside available knowledge sources, note that in the summary and recommend the author seek a subject matter expert.

## Examples

**Business report with unsupported statistics**
- Analyze the .docx, identify statistics without citations, research current benchmarks, build the COMMENTS list with sourced notes, run scripts/inject-comments-docx.py, return the commented .docx.

**Technical article with outdated information**
- Use the Analyze skill to extract claims, research the latest updates, build the COMMENTS list flagging outdated statements with current context, run scripts/inject-comments-docx.py, return the updated .docx.

