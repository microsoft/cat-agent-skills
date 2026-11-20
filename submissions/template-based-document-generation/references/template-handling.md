# Template handling: how Word stores a document and what that means for filling

Background for anyone reviewing the scripts. The normative rules are in `contract.md`.

## A `.docx` is a zip of XML parts

The body is `word/document.xml`; headers, footers, footnotes and endnotes are their own parts;
relationships live in `_rels/*.rels`; styles, numbering, settings, theme and media are separate parts.
Filling touches only the parts that have operations and rebuilds the archive with the same entry order,
compression and timestamps, so every untouched part is compared byte for byte. Package structure (main
relationship, content types, internal targets) is validated on input and on output; this is not full
OOXML schema validation and does not prove Word will lay the document out as intended.

## Text is split across runs

Word stores text in runs (`w:r`), each with its own properties (`w:rPr`). A run boundary appears
whenever formatting, spell-check state, language or an edit boundary changes, which is exactly what
happens when someone types `[Client Name]` and later fixes a typo. The visible field is then spread over
several `w:t` nodes:

```xml
<w:r><w:t>[Cli</w:t></w:r>
<w:r><w:rPr><w:b/></w:rPr><w:t>ent Name]</w:t></w:r>
```

A naive text search never sees it. The inspector works on the *paragraph text* (all `w:t` text plus
`\t` for tabs and `\n` for breaks, in order, nested text-box paragraphs excluded) and maps every
character back to its `w:t`. The filler consolidates a span into its first owning run before replacing;
the verifier uses the same text model. The first run's formatting wins across the value, which the
`mixed_formatting` review item points out.

## Paragraph structure

Paragraphs live in *containers*: the body, table cells, text boxes, footnotes, endnotes, headers,
footers. Content controls, custom XML and tracked-change wrappers also enclose paragraphs but are
transparent for range operations: a section that spans a block-level control is still one range of the
body. A container's block-level children are paragraphs and tables, so a range from one body paragraph
to another removes every paragraph and table between them. Word requires at least one paragraph in every
cell and at least one block in every container, which is why the sole paragraph of a cell is emptied
rather than removed and why a deletion may never empty a container.

## Content controls

A content control (`w:sdt`) shows placeholder text (`w:showingPlcHdr`, grey `PlaceholderText` style)
until someone types into it. Filling it means replacing the text inside `w:sdtContent`, dropping
`showingPlcHdr` and the placeholder style, and leaving `w:sdtPr` otherwise intact. Plain-text and
rich-text controls are filled this way. Date pickers, drop-downs, check boxes and pictures hold typed
values, not free text, and are left alone. A control with `w:dataBinding` mirrors a node in a custom XML
part and would be overwritten by Word on open, so it is ineligible.

## Fields, revisions, comments

Complex fields (`w:fldChar begin … separate … end`) keep their result text in ordinary runs that carry
no marker of their own; the inspector tracks field depth across runs so a candidate in a result run is
recognised as ineligible. Tracked changes (`w:ins`, `w:del`, `w:moveFrom`, `w:moveTo`) make the real
text ambiguous, so candidates inside them are ineligible and the template is reported for review; the
same applies to a tracked paragraph mark. Comments are reviewer notes that would ship with the document,
so their presence is reported. Bookmark and comment ranges are pairs of markers that may sit in
different paragraphs; a deletion must remove both or neither.

## XML escaping, whitespace, namespaces

Text is escaped exactly once at serialisation; an unescaped `&` produces a package Word calls corrupt
even though it is still a valid zip. A `\n` inside `w:t` is whitespace to Word: line breaks are
`w:br`, tabs are `w:tab`, and leading, trailing or doubled spaces need `xml:space="preserve"`. Word's
root element declares many namespaces and lists some in `mc:Ignorable`; an XML library that
re-serialises the part drops the unused declarations and Word then reports the file as corrupt. That
is why the filler edits bytes in place and the verifier compares namespace declarations and their
scopes independently.

## Constructs and the policy

| Construct | Policy | Why |
|---|---|---|
| Digital signatures | block | Any modification invalidates them |
| Macros (`vbaProject.bin`) | block | Executable content |
| Embedded objects | report | Preserved byte-for-byte; a reviewer should know they are there |
| Comments | report | Reviewer notes would be delivered |
| Tracked changes | report | The real text is ambiguous; candidates inside are ineligible |
| Field codes | report | Recalculated by Word; results are not fillable |
| External relationships other than hyperlinks | report | Resources Word may resolve on open, including an attached template |
| Hidden text | allow | Treated as an instruction candidate, since template guidance is often hidden |
| Content controls | allow | Fillable candidates |
| Sensitivity label metadata, custom properties | allow | Preserved byte-for-byte |
