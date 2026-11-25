# Output, preservation, and delivery

## Format

The brief is always an editable PowerPoint deck (`.pptx`) with a source
appendix. This version makes no Word, PDF, or Markdown files; if one is asked
for, say so and offer the deck instead.

## Check support every turn

Look at the tools and environment actually present now. Capabilities, search
toggles, and workspaces change between turns and sessions; never infer them
from the host's or model's name, and never carry a path from an earlier turn.

A deck can be made only when the host can both **create** it and **deliver**
it somewhere the user can open:

| Environment | How the deck is delivered |
| --- | --- |
| PowerPoint agent container (`$OUTPUT_DIR` is set) | Final deck written to the mode's filename is pushed to the open presentation |
| Host with native presentation creation and save | Native create and save |
| Agent with a user-visible file system | New file in the folder the user named, or the working folder |

A library, converter, or writable folder alone is not delivery. In the
PowerPoint container, anything left in `$OUTPUT_DIR` other than the final deck
is deleted at task end.

## PowerPoint agent container

**Classify the open deck first.** `$WORKSPACE_DIR/input.pptx` is the user's open
presentation, freshly fetched this turn; it may not exist. Writing the final
deck updates that presentation. It does not create a copy.

| Open deck | What to do |
| --- | --- |
| None, or blank (no slides, or only empty placeholders) | Build the brief as this deck. |
| A template the user supplied for this brief | Keep its theme, masters, and layouts; replace only sample or placeholder content. |
| Has content, and the user asked to add the brief to it | Append the brief slides; leave every existing slide unchanged. |
| Has content, and no such request | Stop before writing. Ask the user to open a new blank presentation (or a copy) and ask again, or to confirm adding the brief to this deck. |

**Build with the active capability.** With no usable input deck, use the active
presentation capability's own creation workflow. Edit an existing deck in place
with python-pptx. Never unpack, repack, or zip a deck; never hand-write OOXML
parts; never reference another skill's folder, hard-code an `/agent` path,
install packages, or branch on the model.

**Deliver the deck.** Write the final deck to `$OUTPUT_DIR/output.pptx`, or to
the filename the host's current mode requires instead (some edit modes forbid
`output.pptx` and require a topic name). Write it last, after checks; any later
change means recheck and rewrite. Confirm the file exists, is nonempty, reopens
with the expected slides, and was written after the last edit. The host pushes
it; report that it was handed to PowerPoint, not that the user has reviewed it.

## Other hosts

- **Native presentation host:** create a new presentation, or Save a
  Copy of a supplied original before editing. Report the name and location the
  host shows after the save.
- **File-system agent:** write a new file to the folder the user named, or the
  working folder. Never overwrite; add a date or version suffix if the name is
  taken. Report the actual path. A local write is not a cloud upload or a link.

In every host, never open an application, send the file, or share it.

## Verify what the user gets

- Correct account, as-of date, and source scope on the title slide.
- Every factual claim traceable through a visible citation marker to the
  source list; hypotheses and unknowns labeled wherever they appear.
- Sources and caveats on visible slides, not only in speaker notes.
- Text and tables are native and editable, not pictures of text.
- The deck follows [slide design](slide-design.md): the template's layouts
  when usable, at least 4 different layouts and none on more than 2
  consecutive slides, tables on at most a third of main slides and never
  adjacent, a native chart when 3 comparable sourced figures exist, body text
  at least 12 pt, and no empty placeholders.
- Rendered slides checked when rendering is available. Renders show what is
  there, not exact text fit, because server fonts differ. If no rendering was
  possible, say so.
- The user's original and any unrelated slides are unchanged.

## Handoff

State the deck's location or link as returned, the as-of date,
the source scope, the most important open questions, and any check that did
not run. If nothing was delivered, say so plainly; offer the verified content
as a draft only when that helps, never as a delivered file. Recommended actions
are proposals; never say contacts were made or actions completed.
