# Reference: Commenting a PowerPoint Presentation (.pptx)

When the attached file is a `.pptx`, follow these steps:

1. Open and analyze the .pptx file using the built-in Copilot Studio Analyze skill. Extract the main topic, key claims per slide, structure, and overall narrative flow.
2. Identify slides or specific content areas that would benefit from a native PowerPoint comment — including unsupported statistics, unclear messaging, missing context, outdated information, contradictions, or places where a citation would strengthen a claim.
3. Research the presentation's topic using any available sources — including internal documents, emails, Microsoft Teams messages, approved knowledge sources, and web research tools — to gather relevant facts, definitions, recent updates, and citations.
4. Author a `comments.json` file for `scripts/inject-comments-pptx.py`, choosing the slide each comment belongs on. Each comment should do one or more of the following:
   - Flag a claim that needs verification or a citation
   - Provide relevant context, a definition, or a recent update
   - Note a potential inaccuracy, ambiguity, or contradiction
   - Suggest a concise improvement without altering the original slide content
   - Include a source link or citation when available
5. Run `scripts/inject-comments-pptx.py` **once**, passing the **original uploaded .pptx** as the input, a new path as the output, and your `comments.json`:
   ```bash
   python scripts/inject-comments-pptx.py <input.pptx> <output.pptx> <comments.json>
   ```
   **Never run the script a second time on the output file.**
6. Do NOT rewrite, delete, or silently modify any slide text, notes, or visuals. Preserve all formatting and structure. Add native PowerPoint comments only — never edit slide content.
7. Return the updated .pptx file with comments embedded.

## comments.json schema

A JSON array of objects, each with these keys:

- `slide` — the 1-based slide number the comment anchors to (slide 1 = first slide)
- `idx` — an integer that must be **unique per slide** (the comment's index within that slide)
- `text` — the comment body (start with 💡 for context/citations/improvements, 🧹 for inaccuracies/ambiguities/missing info)
- `x` / `y` — optional EMU position of the comment marker on the slide; `1270` (top-left) is a safe default

Example `comments.json`:

```json
[
  {
    "slide": 2,
    "idx": 1,
    "text": "🧹 This market-share figure has no source. The latest analyst report shows 24%, not 30% — please verify.",
    "x": 1270,
    "y": 1270
  },
  {
    "slide": 4,
    "idx": 1,
    "text": "💡 Consider adding the data cutoff date so the growth projection is reproducible."
  }
]
```

Multiple comments on the same slide are grouped into that slide's comment file automatically; just give each a unique `idx`.

## How inject-comments-pptx.py works

The script (`scripts/inject-comments-pptx.py`) is the injection engine. It:

- Unzips the .pptx and groups the comments by `slide`
- Writes `ppt/comments/comment<N>.xml` for each commented slide and adds the slide's comments relationship
- Writes `ppt/commentAuthors.xml`, setting the author to `Copilot Studio AI`
- Patches `[Content_Types].xml` and `ppt/_rels/presentation.xml.rels` so PowerPoint recognises the comments

**Inputs are all passed on the command line** — the script has no hardcoded filenames or comment text:

- `<input.pptx>` — the original uploaded presentation
- `<output.pptx>` — the new path to write the commented presentation to
- `<comments.json>` — the comments you authored (see the schema above)

**Dependency:** the standard library only (`zipfile`, `json`) — no `pip install` required.

## Guidelines

- Use the Copilot Studio Analyze skill first before researching so you understand the full presentation before placing comments.
- Anchor comments to the most relevant slide — if a claim spans multiple slides, comment on the slide where it first appears.
- Only add comments where they genuinely help — do not comment on every bullet point.
- Comments should be factual, concise, and sourced when possible.
- Never alter the presenter's original wording — flag issues in a native PowerPoint comment instead.
- The comment author is set to `Copilot Studio AI` automatically by `scripts/inject-comments-pptx.py` (via `ppt/commentAuthors.xml`) — you don't need to set it yourself.
- **When extracting slide text to identify which slide to comment on, read the raw XML from `ppt/slides/slide{N}.xml`** — do not rely on rendered output. Slide text may contain curly/smart quotes (`""`), curly apostrophes (`'`), or em dashes that won't match straight-quote assumptions. If you need to match text, prefer a portion with no quotes at all.
- If the presentation topic is outside available knowledge sources, note that in the summary and recommend the author seek a subject matter expert.

## Examples

**Sales deck with unverified market data**
- Analyze the .pptx, identify slides with market share or growth figures lacking citations, research current data, author `comments.json` with sourced notes on those slides, run scripts/inject-comments-pptx.py, return the commented .pptx.

**Executive briefing with potentially outdated competitive landscape**
- Use the Analyze skill to extract competitive claims, research the latest developments, author `comments.json` flagging outdated statements with current context, run scripts/inject-comments-pptx.py, return the updated .pptx.

## Sandbox Execution Tips

These tips apply when generating the output `.pptx` via Python inside the sandbox:

- **The confirmed working pattern is:**
  1. Remove the pre-existing read-only output file at `/app/created/filename_commented.pptx` before doing anything else.
  2. Write your injection script to `/app/workspace/` (or another writable scratch path).
  3. Run it using `exec(open('/app/workspace/script.py').read())` inside a `python3 -c "..."` call within the double-nested `sandbox-exec → bash → sandbox-exec → python3 -c` pattern.

- **Always remove the pre-existing output file first.** The sandbox pre-places a read-only file at the output path. Every write attempt will fail with `PermissionError` until it is removed.
- **Use `exec(open(...).read())` to run longer scripts.** Write the full script to `/app/workspace/`, then load and execute it inline via `python3 -c "exec(open('/app/workspace/script.py').read())"`. This avoids heredoc quoting failures while keeping the correct nesting level.
- **The correct nesting is double — not triple.** The pattern is `sandbox-exec → bash → sandbox-exec → python3 -c "..."`. A third nested layer loses write permissions.
- **Only write the final output to `/app/created`.** Use `/app/workspace/` for intermediate/script files. `/tmp/` is unwritable from Python in the sandbox.
