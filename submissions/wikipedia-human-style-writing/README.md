# Wikipedia Human Style Writing

A skill that helps an agent write and revise prose so it doesn't read as
AI-generated.

## Genesis

Wikipedia editors, flooded with undisclosed AI-generated edits, wrote a community
field guide —
[**Signs of AI writing**](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) —
cataloguing the tell-tale patterns of LLM prose: empty significance flourishes,
promotional puffery, weasel-worded attributions, era-specific "AI vocabulary"
(*delve*, *tapestry*, *underscore*), rule-of-three lists, em-dash overuse, and more.

That guide is written to *detect* AI text. This skill flips it around to *avoid*
writing that way in the first place — and to review drafts for the same tells. The
patterns are distilled into `references/ai-writing-tells.md`, which the skill
consults while editing.

## What it does

- Sweeps a draft for **clusters** of AI tells (density matters more than any single
  word).
- Fixes the underlying cause — restores specific facts, cuts hollow significance,
  names real sources — rather than just swapping surface words.
- Preserves the author's meaning, facts, and voice; it humanises without flattening.

Treats the guide as **descriptive, not prescriptive**: these words and shapes are
overused, not banned, so judgment beats find-and-replace.
