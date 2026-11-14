# Markdown, HTML, and plain text

## HTML

Set base direction on the smallest appropriate block with `dir="rtl"` or
`dir="ltr"`. Use `lang="he"` / `lang="en"` for language, not direction.
Use an explicit direction for known content and `dir="auto"` for genuinely
unknown user-supplied content.

Isolate inline opposite-direction phrases with `bdi` and an appropriate
direction. Include punctuation belonging to the phrase inside its boundary.
Keep surrounding sentence punctuation outside.

```html
<p dir="rtl" lang="he">
  פתחו את <bdi dir="ltr" lang="en">Microsoft Teams</bdi>
  בשעה <bdi dir="ltr">10:30</bdi>.
</p>
<p dir="rtl" lang="he">
  קישור:
  <a href="https://example.com/docs?v=1&amp;lang=he"><bdi dir="ltr">https://example.com/docs?v=1&amp;lang=he</bdi></a>
</p>
<p dir="ltr" lang="en">
  Status: <bdi dir="rtl" lang="he">הבדיקה הושלמה</bdi>.
</p>
```

Preserve link destinations, DOM semantics, escaping, and accessibility.
Escape interpolated text and attributes; never concatenate untrusted HTML.
Do not use `bdo`, `unicode-bidi: bidi-override`, reversed flex order, or
`text-align: right` alone as a text-order repair.
For CSS-only components, use `direction` and `unicode-bidi: isolate` deliberately,
and verify the computed styles and inherited direction in the actual component.
Prefer semantic `dir` attributes for document content.

Validate in the target browser and check selection, wrapping, copy/paste,
links, inline code, and keyboard/screen-reader reading order.

## Markdown (.md)

Markdown has no portable standard syntax for paragraph direction.
Ask which viewer matters: GitHub, VS Code preview, a wiki, a static-site
generator, or a conversion pipeline. Do not promise identical rendering.

1. Preserve Markdown source and logical text order.
2. If the viewer allows HTML and retains direction attributes, use minimal
   HTML such as `<p dir="rtl">...</p>` or `<bdi dir="ltr">...</bdi>`.
   Some sanitizers strip elements, attributes, or styles.
3. Raw HTML blocks may disable Markdown parsing inside them. Do not wrap an
   entire file in a `div` and assume headings, lists, and links still parse.
   Prefer separate HTML paragraphs with explicit HTML markup where needed,
   or a renderer-supported template that supplies direction outside Markdown.
4. Preserve code fences, inline code, link destinations, frontmatter, headings,
   table structure, and commands. Never insert invisible direction controls
   into technical examples or executable content.
5. If HTML is stripped, explain the constraint. Offer a viewer-level RTL setting
   or a separate HTML/DOCX rendering while keeping the Markdown source intact.
   Use approved Unicode isolates only in prose and only after viewer testing.
6. Preview in the requested renderer. Browser testing of an HTML example is
   not evidence that GitHub or a particular wiki preserves that markup.

## Plain text (.txt)

Plain text stores characters, not paragraph formatting. It cannot persist
"right alignment" or guarantee a viewer's base direction.
Preserve the encoding and line endings when known; do not guess a legacy
encoding if decoding fails. For a new file, prefer UTF-8.

Prefer viewer-level direction controls without changing the source. If text
controls are necessary and the user accepts them:

- LRI `U+2066` starts a known LTR isolate.
- RLI `U+2067` starts a known RTL isolate.
- FSI `U+2068` infers the direction of an unknown isolated phrase from its
  first strong character; it is not a paragraph-language detector.
- PDI `U+2069` closes the isolate. Keep isolates balanced and local.

For example, the notation `Hebrew prose [LRI]Microsoft Teams[PDI]` describes
the boundaries; literal `[LRI]` and `[PDI]` labels do not affect rendering.
In an implementation, `"\u2066Microsoft Teams\u2069"` represents the actual
controls. Document their code points and locations in the change summary.
Do not add controls by blindly wrapping every Latin word.

LRM `U+200E` and RLM `U+200F` may resolve specific boundary cases in older
viewers, but they are not interchangeable with isolates. Use them only for a
demonstrated viewer-specific problem. Do not introduce embeddings or overrides
as a default fallback.

Check visual display and copied text in the target application. If the viewer
does not implement the required bidi behavior, explain that text alone cannot
guarantee the requested result.

## Authoritative references

- [W3C inline bidi markup](https://www.w3.org/International/articles/inline-bidi-markup/)
- [W3C structural direction markup](https://www.w3.org/International/questions/qa-html-dir)
- [Unicode Bidirectional Algorithm, UAX #9](https://www.unicode.org/reports/tr9/)
- [CommonMark raw HTML behavior](https://spec.commonmark.org/0.31.2/#html-blocks)
