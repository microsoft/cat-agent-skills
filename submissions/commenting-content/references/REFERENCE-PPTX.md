# Reference: Commenting a PowerPoint Presentation (.pptx)

When the attached file is a `.pptx`, follow these steps:

1. Open and analyze the .pptx file using the built-in Copilot Studio Analyze skill. Extract the main topic, key claims per slide, structure, and overall narrative flow.
2. Identify slides or specific content areas that would benefit from a native PowerPoint comment — including unsupported statistics, unclear messaging, missing context, outdated information, contradictions, or places where a citation would strengthen a claim.
3. Research the presentation's topic using any available sources — including internal documents, emails, Microsoft Teams messages, approved knowledge sources, and web research tools — to gather relevant facts, definitions, recent updates, and citations.
4. Add native PowerPoint comments (the built-in .pptx comment functionality) to the relevant slides. Each comment should do one or more of the following:
   - Flag a claim that needs verification or a citation
   - Provide relevant context, a definition, or a recent update
   - Note a potential inaccuracy, ambiguity, or contradiction
   - Suggest a concise improvement without altering the original slide content
   - Include a source link or citation when available
5. Do NOT rewrite, delete, or silently modify any slide text, notes, or visuals. Preserve all formatting and structure. Add native PowerPoint comments only — never edit slide content.
6. Return the updated .pptx file with comments embedded.

## Guidelines

- Use the Copilot Studio Analyze skill first before researching so you understand the full presentation before placing comments.
- Anchor comments to the most relevant slide — if a claim spans multiple slides, comment on the slide where it first appears.
- Only add comments where they genuinely help — do not comment on every bullet point.
- Comments should be factual, concise, and sourced when possible.
- Never alter the presenter's original wording — flag issues in a native PowerPoint comment instead.
- Set the comment author to `Copilot Studio AI` using the `p:author` field in the .pptx comment XML.
- **When extracting slide text to identify which slide to comment on, read the raw XML from `ppt/slides/slide{N}.xml`** — do not rely on rendered output. Slide text may contain curly/smart quotes (`""`), curly apostrophes (`'`), or em dashes that won't match straight-quote assumptions. If you need to match text, prefer a portion with no quotes at all.
- If the presentation topic is outside available knowledge sources, note that in the summary and recommend the author seek a subject matter expert.

## Examples

**Sales deck with unverified market data**
- Analyze the .pptx, identify slides with market share or growth figures lacking citations, research current data, insert native PowerPoint comments on those slides, return the commented .pptx.

**Executive briefing with potentially outdated competitive landscape**
- Use the Analyze skill to extract competitive claims, research the latest developments, insert native PowerPoint comments flagging outdated statements with current context, return the updated .pptx.

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
