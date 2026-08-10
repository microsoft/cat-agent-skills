---
name: wikipedia-human-style-writing
description: Use this skill whenever the user asks to write, rewrite, humanise, de-AI, or polish prose so it doesn't read as AI-generated — or to review a draft for signs of AI writing. Apply it before returning any substantial prose the user will publish.
---

# Wikipedia Human Style Writing

Write and revise prose so it does not carry the tell-tale signs of AI-generated
text, using the patterns catalogued in Wikipedia's
[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
The full pattern catalogue lives in `references/ai-writing-tells.md` — consult it
whenever you need the specific words-to-watch lists, examples, or the era-by-era
"AI vocabulary" breakdown.

## Operating principles

1. **Signs, not sins.** Every pattern below can appear in good human writing. The
   giveaway is **density and mechanical repetition**, not a single instance. Target
   clusters, not isolated words.
2. **Fix the cause, not the symptom.** Most tells are surface markers of a deeper
   problem: vagueness, puffery, or unsupported claims. Restore the specific fact or
   cut the empty claim — don't just swap the flagged word and leave hollow content.
3. **Preserve the truth and the voice.** Never invent or drop facts, figures,
   quotes, dates, or sources. Keep the author's meaning, stance, and legitimate
   emphasis. Do not "de-AI" a draft into corporate blandness.
4. **Descriptive, not prescriptive.** These words and shapes are overused, not
   banned. Use judgment over find-and-replace.

## Workflow

1. Read the whole draft first; note the core message, key facts, and the intended
   voice and audience.
2. Sweep the draft against the tell categories in `references/ai-writing-tells.md`,
   looking for **clusters**.
3. Revise each cluster by fixing the underlying issue:
   - Replace generic praise with the specific, concrete fact
     (regression-to-the-mean: "a revolutionary titan of industry" → the actual
     achievement).
   - Cut empty significance/legacy flourishes and trailing "-ing" analysis clauses.
   - Restore plain `is/are/has` in place of "serves as / stands as / boasts /
     features".
   - Name a real source or delete a vague attribution ("experts argue", "observers
     have noted").
   - Break up mechanical rule-of-three lists, "not just X but Y" parallelisms, and
     templated "Challenges / Future prospects" wrap-ups.
   - Remove promotional/travel-brochure tone ("vibrant", "nestled", "rich tapestry",
     "seamless").
   - Thin out an over-dense cluster of era-specific "AI vocabulary" words.
4. Clean the formatting tells: sentence-case headings (not Title Case), sparing
   boldface (not `**bold lead-in:**` on every list item), varied punctuation instead
   of space-surrounded em-dash overuse, no emoji-as-bullets, no stray markdown or
   copy-pasted smart-quote residue, and no "In conclusion / In summary" filler.
5. Re-read against the original to confirm no meaning, fact, or nuance drifted.

## Guardrails

- Do not add, remove, or alter facts, numbers, quotes, or citations to make text
  "sound less AI".
- Do not strip emphasis or specificity that the source genuinely supports.
- Do not flatten a distinctive human voice into neutral mush — the goal is natural,
  specific, human prose, not blandness.
- One or two flagged words are usually fine; don't over-correct isolated hits.

## Output

Return the revised prose first, copy-ready. When a review was requested, or when
useful, follow it with a short bulleted list of the notable tells you found and how
you addressed them.

## Reference

- `references/ai-writing-tells.md` — the full field guide: every tell category with
  words-to-watch, examples, the era-by-era AI-vocabulary breakdown, and formatting
  tells. Read the relevant section whenever you need detail beyond the summary above.
