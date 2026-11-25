# Pack outputs: what each file holds and how it is built

Every output has a bundled fallback that needs only Python and the libraries listed in the skill's
compatibility notes. Other skills are optional enhancements. Use one only when it is available in the
session; if a call to it fails, use the fallback and say so in the report.

| Output | File | Bundled fallback | Optional enhancement |
|---|---|---|---|
| Agenda | `agenda.docx` | `build_docs.py --only agenda` | docx skill |
| Agenda one-page view | `agenda-one-page.docx` (landscape) | `build_docs.py --only agenda` | docx skill; render-ui card in chat |
| Slide deck | `deck.pptx` | `build_deck.py` (python-pptx), with `--template` for a brand file | pptx skill |
| Facilitator guide | `facilitator-guide.docx` | `build_docs.py --only guide` | docx skill |
| Participant workbook | `participant-workbook.docx` | `build_docs.py --only workbook` | docx skill |
| Pre-read (optional) | `pre-read.docx` | `build_docs.py --only preread` | docx skill |
| Feedback survey (optional) | `feedback-survey.docx` | `build_docs.py --only survey` | A forms tool, if the user asks and one is available |
| Follow-up email (optional) | `follow-up-email-draft.md` | `build_docs.py --only email` | A mail tool may save it as a draft only when the user asks; never send |
| HTML page (optional) | `workshop.html` | `build_docs.py --html` | A SharePoint page skill (for example `sharepoint-site-kit`): offer to hand the page over |

## Deck slide plan

Same plan whether the pptx skill or `build_deck.py` builds it:

1. Title: title, subtitle, format, length.
2. Executive summary.
3. Agenda with clock times and duration labels.
4. "By the end of this session you will be able to" with the objectives.
5. Per module: a section divider with the duration label; key point slides (at most four points per
   slide, source refs in the footer); one slide per activity with numbered steps, the timebox, the goal,
   the expected output and the materials.
6. Break slides with the return time.
7. Next steps.
8. Sources.

Every slide has speaker notes. Module and activity slides end with "Timing: N minutes." Activity notes
hold the debrief questions and the fallback.

## Using a brand template

- The user supplies a `.pptx` or `.potx`. Never require one.
- Fallback path: `python scripts/build_deck.py workshop.json --out deck.pptx --template brand.potx`. It
  uses the template's masters and layouts, matched by name (Title Slide, Section Header, Title and
  Content, Title Only), removes the template's own slides from the copy and never edits the original.
- Brand colors and fonts for documents and the HTML page:
  `python scripts/extract_brand.py brand.potx --json-out brand.json`, then pass `--brand brand.json` to
  `build_docs.py` (and to `build_deck.py` when there is no template).
- With the pptx skill: hand it the same slide plan and the template path, and follow that skill's
  template workflow.
- If the template has no layout with a body placeholder, the fallback adds text boxes; check the result
  in the visual check.

## Handing off the HTML page

When a SharePoint page skill is installed (for example `sharepoint-site-kit`), offer: "I can hand this
page to <skill> to publish it to a SharePoint site." Do it only if the user agrees. Otherwise deliver
`workshop.html` as a file. The page is self-contained: inline CSS, no scripts, no external resources.

## Delivery

Run `check_pack.py --pack-dir` on the completed folder: it requires all five core files and the
pre-read, survey and email draft when their data is present in the spec. Add `--html` to the check when
the HTML page was requested. Each workbook exercise includes its own source-unit citations.

Write every file into a working folder, then publish to the user's output folder with the session's
file-publish tool (in Cowork: `CopyArtifact(surface="output", ...)`), and check each result. Suggested
names: `<Short title> - Agenda.docx`, `<Short title> - Deck.pptx`, `<Short title> - Facilitator guide.docx`,
`<Short title> - Participant workbook.docx`.
