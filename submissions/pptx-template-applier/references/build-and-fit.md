# Build and text fit

What `apply_template.py` does with each kind of content, the text-fit rules, and the known limits.

## 1. The new deck

1. The template is opened from memory (a .potx is read as a presentation; macros are dropped). The file
   on disk is never written.
2. The template's own sample slides are removed. Masters, layouts and the theme stay.
3. One new slide per source slide, in the same order, on the mapped layout. Continuation slides (after
   an agreed split) follow the slide they came from.
4. The result is saved to `--out`, which must differ from both inputs.

## 2. Content handling

| Content | How it moves |
|---|---|
| Title | Into the title placeholder. Without one, a text box in the theme heading font, with a warning. |
| Subtitle | Into the subtitle placeholder, else the first free body placeholder. |
| Body text | Into body or content placeholders in reading order (left column first, then top to bottom). Bullet levels, bold, italic, underline and links are kept. Hard-coded fonts, sizes and colors are dropped so the template's styles apply. |
| Comparison onto two columns | Each header is merged, in bold, at the top of its column. |
| Table | Rebuilt with the same rows, columns, relative column widths, merged cells and text, using the themed table style (header and banding in the template's accent 1). Hard-coded cell fills are dropped. Font size is the largest from 18 pt down to the table floor that fits. |
| Chart | Rebuilt from its data for category charts (column, bar, line, area, pie, doughnut, radar): categories, series names and values, legend and its position, chart title and data labels. Series use theme accents 1 to 6 in order. Scatter, bubble and combo charts are not rebuilt: they are listed as warnings. |
| Picture | Same image, same crop, fitted inside the target area without stretching or extra cropping. Goes into a free picture placeholder first. |
| Shapes, text boxes, groups, connectors | Copied with their pictures and links, scaled into the content area as a group so their layout holds. Hard-coded colors map to theme slots, hard-coded font faces are dropped, font sizes scale with the group (not below 10 pt). |
| Embedded objects, SmartArt, video | Not carried over (the parts cannot move safely between files). Listed as warnings. |
| Speaker notes | Copied as text. |
| Links to other slides | Removed, because slide numbers change. Web links are kept. |

Unused empty placeholders are removed so no "Click to add" prompt is left.
Soft line breaks stay in order with ordinary runs. Fields are rebuilt as their current displayed
text, not live fields. Chart labels retain visibility flags, number formats and custom text at both
plot and series level. Workbook-linked labels use cached display text when available and are
reported; missing caches or extended label settings require a manual check. Copied group descendants
receive fresh shape IDs and connector endpoints are translated after all copied shapes are placed.
Endpoints whose targets were not carried over are detached and reported rather than attached to an
unrelated shape.

## 3. Color mapping

Hard-coded colors in copied shapes and text are mapped once for the whole deck:

1. A color close to one of the source theme colors keeps that slot (accent 2 stays accent 2), so an
   author's theme choices carry over.
2. Other saturated colors take the next unused accent, in order of first use.
3. Grays, near-black and near-white map to the dark, light and background slots by lightness.

The map is in `build.json` under `color_map` and in the summary.

## 4. Text fit

- The starting size comes from the template: the layout placeholder's list style, then the master
  placeholder, then the master text styles.
- The script estimates the lines each paragraph needs from the box width, font size and indent level.
  The estimate assumes wider letters for fonts such as Verdana or Segoe.
- If the text does not fit, every level shrinks in 2 pt steps (level ratios kept) down to the floor.
- Floors: title 24 pt, body 14 pt, table 10 pt. Change them with `--title-floor`, `--body-floor`,
  `--table-floor` when the user asks; going below 12 pt hurts readability in a room.
- Still too long at the floor: the slide is listed under `overflow`. Ask the user, then use
  `--split-overflow N`. The split happens at top-level bullets (a bullet stays with its sub-bullets).
  Continuation slides use the same layout, the title plus "(continued)", and a short note.
- Only a slide with one body placeholder and no other items can be split. Otherwise the slide is
  reported for a manual edit.
- Every continuation chunk must fit, including a top-level bullet with all its sub-bullets. If a
  group is too large to split safely, the original slide and its overflow warning are retained.
- Table row heights account for wrapped text, explicit line breaks and merged cells at the selected
  font size. A table that is still too tall at the floor retains its required height and is reported
  for a manual edit; rows are not silently compressed.

## 5. Slide size

When the source and template sizes differ (for example 4:3 onto 16:9), placeholder content takes the
template's positions and free content is scaled uniformly into the template's content area, so nothing
is stretched.

## 6. Known limits

- The line estimate is conservative: text may end a size or two smaller than strictly needed. The
  rendered check shows the real result.
- Fonts render with substitutes when the brand fonts are not installed on the machine that renders.
  Line breaks may differ slightly in PowerPoint.
- Animations and transitions on the source slides are not copied; the template's are used.
- Pictures held in a picture placeholder are fitted, not cropped to fill. A template whose photo layout
  expects full-bleed images may show white space around a picture of a different shape.
