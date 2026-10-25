# Email, PDF, OpenDocument, and unsupported formats

This reference describes conditional workflows and limits, not a claim that
all these formats have been rendered or tested in every agent host.

## Outlook and email

Identify whether the user has an editable draft, an HTML body, a plain-text
body, a MIME `.eml`, or an Outlook `.msg` file.

- In an editable draft, set native paragraph direction and preserve the
  message's links, signatures, attachments, recipients, and existing layout.
  Do not send a message unless the user separately authorizes sending.
- For HTML email, use explicit `dir` on paragraphs/blocks. Isolate inline
  opposite-direction phrases where the target mail client supports it.
  Do not assume `bdi` or CSS support is identical to a browser.
  Test in the specified Outlook desktop/web/mobile client.
- For plain text, explain the absence of persistent paragraph formatting.
  Prefer client-level direction; obtain approval before inserting isolates.
- For `.eml`, use a MIME-aware parser and preserve headers, MIME boundaries,
  charset, transfer encoding, attachments, and alternative bodies. Update
  approved text parts, not raw bytes with global replacement.
- Editing signed/encrypted email can invalidate trust. Stop and explain.
  Do not claim to preserve DKIM or S/MIME validity after content changes.
- `.msg` needs a compatible Outlook or message-format tool. If unavailable,
  request a draft/HTML export rather than pretending it is a text file.

## PDF

Distinguish a born-digital PDF, a tagged PDF, and a scan. A PDF's displayed
glyph positions, text extraction order, and accessibility reading order are
separate concerns.

1. Prefer fixing the editable source (DOCX, PPTX, HTML, or ODF), then re-export
   to a new PDF. Validate both the source and the exported result.
2. If the PDF looks correct but extraction is wrong, do not reverse the
   displayed text. A tagging/reading-order repair requires appropriate PDF
   tooling and a separate accessibility check.
3. Direct PDF editing is tool-dependent; ordinary paragraph RTL properties
   cannot simply be applied to positioned glyph streams.
4. For scans or rasterized text, use OCR only with approval and suitable tools.
   Explain that OCR reconstructs text and may change layout or introduce
   recognition errors. Do not promise a lossless editable repair.
5. Preserve links, forms, annotations, tags, and embedded fonts where the
   chosen tooling permits. Stop before invalidating a signature.
6. Inspect rendered pages, text extraction, token copy/paste, and accessibility
   order when applicable. A correct image alone does not validate all three.

If no source or suitable PDF editor is available, report the blocker and
request the editable source. Do not return an unchanged PDF as "fixed."

## OpenDocument (.odt, .odp, .ods)

Use a compatible ODF-aware editor, preferably the target application. Apply
paragraph writing direction and alignment separately. ODF commonly expresses
paragraph writing mode through `style:writing-mode`, with `rl-tb` for horizontal
RTL text and `lr-tb` for LTR text. Verify the property's applicability for the
specific document type and version; do not paste Open XML properties into ODF.

Preserve style inheritance, text spans, lists, tables, formulas, media, and
package relationships. Presentation and spreadsheet behavior is
application-dependent. Reopen and render in the requested LibreOffice or
other ODF application.

Conversion to DOCX/PPTX/XLSX is an alternative only with approval and a warning
about layout/feature changes; preserve the original and inspect the round trip.

## Legacy Office, RTF, images, and unknown types

- `.doc`, `.ppt`, and `.xls` are not ZIP/Open XML packages. Use native tools or
  obtain approval to convert a copy to a modern editable format.
- RTF has its own paragraph/character direction controls. Use an RTF parser
  or native application, not a plain-text or Open XML replacement.
- Macro-enabled Office files require tooling that preserves macros and
  relationships without executing code. Never silently save them as
  macro-free files.
- Images have no editable text direction. Request the source, or propose
  approved OCR/reconstruction with its limits.
- For any unlisted type, first establish whether it can represent direction
  and whether the installed tools can preserve its semantics. If not, request
  an editable export. "All file types" is not a technically valid guarantee.

## Authoritative references

- [OASIS OpenDocument specifications](https://www.oasis-open.org/standard/opendocument/)
- [W3C PDF reading-order technique](https://www.w3.org/TR/WCAG20-TECHS/PDF3.html)
- [MIME format, RFC 2045](https://www.rfc-editor.org/rfc/rfc2045)
