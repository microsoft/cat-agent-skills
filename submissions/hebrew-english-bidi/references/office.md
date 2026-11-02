# Word and PowerPoint

Use native application controls, a supported document SDK, or a
namespace-aware Open XML editor. Do not assume a library's alignment API also
sets direction. If a library cannot preserve an unsupported feature, use a
more capable tool or report the limitation rather than rebuilding the file.

## Word (.docx)

Inspect paragraphs in the main document, tables (including nested tables),
headers, footers, footnotes, endnotes, and text boxes. Report inaccessible
parts. Preserve comments, tracked changes, content controls, bookmarks, fields,
and relationships; do not accept revisions as a side effect.

For a confirmed Hebrew-base paragraph:

- Set paragraph bidi behavior independently from its alignment.
- In WordprocessingML, `w:pPr/w:bidi` controls RTL paragraph layout.
  `w:jc w:val="right"` sets right alignment when appropriate. Paragraph bidi
  alone is not a complete solution for mixed-run text ordering.
- Inspect `w:rPr/w:rtl` and inherited styles. Hebrew runs may require RTL
  properties. English runs must not inherit an RTL run override; use an explicit
  `w:rtl w:val="0"` where necessary to cancel inherited RTL.
- Keep multiword English phrases and technical tokens logically contiguous,
  while preserving internal bold, italic, links, and other run formatting.
  Do not merge styled runs blindly or assign one direction to a mixed run.
- Use language metadata such as `he-IL` and the document's English locale only
  where it matches the text. Language tags are not a substitute for direction.
- Preserve numbering definitions, hanging indents, tabs, page geometry, and
  intentionally centered or justified content.

Illustrative paragraph fragment (not a complete DOCX package):

```xml
<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:pPr>
    <w:bidi/>
    <w:jc w:val="right"/>
  </w:pPr>
  <w:r>
    <w:rPr><w:rtl/></w:rPr>
    <w:t xml:space="preserve">פתחו את </w:t>
  </w:r>
  <w:r>
    <w:rPr><w:rtl w:val="0"/></w:rPr>
    <w:t>Microsoft Teams</w:t>
  </w:r>
</w:p>
```

Use an SDK or respect schema child ordering when editing existing `w:pPr`
and `w:rPr`. A table's RTL visual ordering is a separate choice: do not mirror
columns merely to fix text inside cells.

## PowerPoint (.pptx)

Inspect slide text, placeholders, grouped text-bearing shapes, table cells,
and speaker notes. Inspect inherited master/layout properties and chart or
SmartArt text where the available tool supports it. Shared master/layout edits
can affect unrelated slides: prefer local overrides for a scoped repair.
Do not flatten text into images or redesign the deck.

For a confirmed Hebrew-base paragraph:

- Set DrawingML paragraph direction with `a:pPr rtl="1"`.
  Use `algn="r"` for right alignment when appropriate.
- Inspect inherited default run properties as well as individual runs.
  The run property is the **child element** `a:rtl` within `a:rPr`,
  not an invented `rtl` attribute on `a:rPr`.
- Apply `a:rtl` to suitable Hebrew runs. Use `a:rtl val="0"` on English
  runs only when necessary to cancel inherited RTL. Never apply an RTL run
  override to strong LTR English text.
- Preserve existing `a:latin` and `a:cs` fonts if they cover the required
  characters. An RTL run can select the complex-script font, so inspect
  whether a font change is the real cause of unexpected appearance.
- Keep paragraph-level bullets, levels, spacing, margins, and tab stops.
  Recheck text-box wrapping, line breaks, and overflow after direction changes.

Illustrative DrawingML fragment:

```xml
<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <a:pPr rtl="1" algn="r"/>
  <a:r>
    <a:rPr lang="he-IL"><a:rtl val="1"/></a:rPr>
    <a:t xml:space="preserve">פתחו את </a:t>
  </a:r>
  <a:r>
    <a:rPr lang="en-US"><a:rtl val="0"/></a:rPr>
    <a:t>Microsoft Teams</a:t>
  </a:r>
</a:p>
```

When adding `a:rtl`, respect DrawingML child ordering: it follows existing
font/hyperlink children and precedes `a:extLst`. Preserve run styling and
hyperlink relationships.

## Package integrity and verification

- Do not use global text replacements over ZIP/XML content. Preserve namespace
  bindings, content types, relationships, media, and all untouched package parts.
- Preserve logical text and spaces when splitting mixed runs, including
  `xml:space="preserve"` where required. Do not reorder XML text nodes.
- Validate the package with native tooling or an Open XML validator when
  available. Reopen in Word or PowerPoint and check for repair warnings.
- Render changed pages/slides, inspect punctuation and clipping, and copy/paste
  tokens back into plain text. Inspect notes separately from slide images.
- If only package checks were possible, report "structurally checked;
  rendering not verified" rather than claiming complete success.

## Authoritative references

- [Word paragraph BiDi](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.bidi)
- [Word run RightToLeftText](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.righttolefttext)
- [DrawingML paragraph properties](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.paragraphproperties)
- [DrawingML RightToLeft run element](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.righttoleft)
