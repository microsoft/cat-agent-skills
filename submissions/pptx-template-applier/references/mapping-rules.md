# Mapping rules

How `plan_mapping.py` picks a template layout for each source slide, and how the user changes it.

## 1. Layout kinds

Every layout (template) and every source slide gets one kind. The placeholder signature decides; the
layout `type` attribute and the layout name are tie-breakers, because brand templates often rename
layouts or drop the type.

| Kind | Signature |
|---|---|
| title | title plus subtitle, no content or picture placeholder |
| section | title plus one short text placeholder, or layout type `secHead`, or a name with "section" or "divider" |
| content | title plus one body or content placeholder |
| two_content | title plus two body or content placeholders side by side |
| comparison | title plus four body or content placeholders (two headers, two bodies) |
| picture | title plus a picture placeholder |
| caption_content | title plus a content placeholder and a caption text placeholder |
| title_only | title placeholder only |
| blank | no placeholders besides date, footer and slide number |

Date, footer, slide number and header placeholders never count.

## 2. What a source slide holds can change its kind

- A blank slide with a large text box (24 pt or more) near the top: the text box becomes the title and
  the slide is treated as title_only with free content.
- A title-only or content slide whose only item is one table, chart or picture: treated as content, so
  the item fills the template's content placeholder area.
- A content slide with extra items (shapes, pictures) beside the bullets: content, and the extra items
  are placed as free content.

## 3. Fallback chain (first available wins)

| Source kind | Tries, in order |
|---|---|
| title | title, section, title_only |
| section | section, title, title_only |
| content | content, caption_content, title_only |
| two_content | two_content, comparison, title_only |
| comparison | comparison, two_content (headers merged into each column, in bold), title_only |
| picture | picture, caption_content, content, title_only |
| caption_content | caption_content, content, title_only |
| title_only | title_only, content, blank |
| blank | blank, title_only |

When several layouts share a kind, the one whose layout type matches the kind wins, then the shortest
name (the base layout rather than a variant such as "Content, dark").

"Title only plus free content" is the last resort: text that has no placeholder goes into text boxes and
other items keep their relative positions, scaled into the area under the title.

## 4. Showing the plan

Show the Markdown table that `plan_mapping.py` prints, as is, then one question:

> Here is how each slide maps to the template. Want to change any of these?

Keep it to the table and the question. Do not explain the rules unless asked.

## 5. Overrides

- By index: `--override 5=3` puts source slide 5 on template layout 3 (indexes are in the inspect
  summary).
- By name: `--override "10=Contoso Clean"`. The name must match exactly.
- Several: repeat `--override`.
- The JSON can also be edited by hand: change `target_layout_index` and `target_layout` for a slide.

An override is recorded with the reason `user override`. Re-run the plan with all overrides at once,
show the changed rows and build.

## 6. Mode

`mode` in mapping.json is `rebuild` when at least one layout has a title and a body or content
placeholder. Otherwise it is `restyle`, and `apply_template.py` refuses to run: use the fallback in
`fallback-restyle.md`.
