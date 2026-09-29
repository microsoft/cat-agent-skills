"""Build the fixture documents in assets/fixtures/ from hand-written OOXML.

Usage:
    python scripts/build_fixtures.py            # (re)write assets/fixtures/*.docx
    python scripts/build_fixtures.py --check    # exit 1 if any committed fixture differs

Standard library only. Every part is literal XML in this file, so the fixtures are reviewable as
text. Every host-dependent zip header field is pinned (timestamp, permissions, creating system), so
a build on Windows, macOS or Linux produces the same archive given the same deflate implementation.
`--check` compares the committed files with an in-memory build *logically* - entry names and order,
per-entry metadata, and the uncompressed bytes of every part - so a different zlib can never cause
a false drift, while any change to the content the filler must preserve is still caught.

The expected results live in assets/expected/<fixture>.json (see assets/expected/README.md).

Fixture inventory:
    six-position           double-brace placeholders in body, header, footer, table, list, hyperlink; run splits
    mixed-conventions      brackets, angle brackets, blanks, a bracketed guidance note, a conditional heading, a
                           hidden note, a content control with placeholder text, a repeatable row, a footnote,
                           a header field, a bookmark, two tables (one inside a deletable section)
    deletion-safety        a section-break paragraph, an unbalanced bookmark pair, a sole paragraph in a cell
    mixed-format-split     placeholder split across runs with different formatting -> review item
    tab-in-placeholder     structural tab inside the braces -> ineligible candidate
    comments-only          comments part and markers -> report finding
    revisions-only         tracked changes, incl. a tracked paragraph mark -> report finding, ineligible candidate
    block-sdt-wrapping     placeholder inside a block-level content control (fillable in v3)
    complex-field-result   placeholder in a complex field's result run -> ineligible
    signature-marker       synthetic signature-origin part -> blocked
    mc-ignorable-root      real-world root element (mc:Ignorable, unused xmlns:wpc, w14/rsid attributes)
"""
from __future__ import annotations

import io
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.normpath(os.path.join(HERE, "..", "assets", "fixtures"))
FIXED_TIME = (2026, 9, 7, 0, 0, 0)

XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
NS = f"{W} {R}"

REL_OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_WML = "application/vnd.openxmlformats-officedocument.wordprocessingml"


def content_types(extra_overrides: list[tuple[str, str]] = (), extra_defaults: list[tuple[str, str]] = ()) -> str:
    defaults = [("rels", "application/vnd.openxmlformats-package.relationships+xml"), ("xml", "application/xml")] + list(extra_defaults)
    overrides = [
        ("/word/document.xml", f"{CT_WML}.document.main+xml"),
        ("/word/styles.xml", f"{CT_WML}.styles+xml"),
        ("/word/settings.xml", f"{CT_WML}.settings+xml"),
        ("/word/header1.xml", f"{CT_WML}.header+xml"),
        ("/word/footer1.xml", f"{CT_WML}.footer+xml"),
        ("/word/numbering.xml", f"{CT_WML}.numbering+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
    ] + list(extra_overrides)
    body = "".join(f'<Default Extension="{e}" ContentType="{c}"/>' for e, c in defaults)
    body += "".join(f'<Override PartName="{p}" ContentType="{c}"/>' for p, c in overrides)
    return XML + f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{body}</Types>'


def root_rels(extra: str = "") -> str:
    return XML + (
        f'<Relationships xmlns="{REL_PKG}">'
        f'<Relationship Id="rId1" Type="{REL_OFFICE}/officeDocument" Target="word/document.xml"/>'
        f'<Relationship Id="rId2" Type="{REL_PKG}/metadata/core-properties" Target="docProps/core.xml"/>'
        f'<Relationship Id="rId3" Type="{REL_OFFICE}/extended-properties" Target="docProps/app.xml"/>'
        f"{extra}</Relationships>"
    )


def document_rels(extra: str = "") -> str:
    return XML + (
        f'<Relationships xmlns="{REL_PKG}">'
        f'<Relationship Id="rId1" Type="{REL_OFFICE}/styles" Target="styles.xml"/>'
        f'<Relationship Id="rId2" Type="{REL_OFFICE}/settings" Target="settings.xml"/>'
        f'<Relationship Id="rId3" Type="{REL_OFFICE}/header" Target="header1.xml"/>'
        f'<Relationship Id="rId4" Type="{REL_OFFICE}/footer" Target="footer1.xml"/>'
        f'<Relationship Id="rId5" Type="{REL_OFFICE}/numbering" Target="numbering.xml"/>'
        f"{extra}</Relationships>"
    )


HYPERLINK_REL = f'<Relationship Id="rId6" Type="{REL_OFFICE}/hyperlink" Target="https://example.test/client" TargetMode="External"/>'
COMMENTS_REL = f'<Relationship Id="rId7" Type="{REL_OFFICE}/comments" Target="comments.xml"/>'
FOOTNOTES_REL = f'<Relationship Id="rId8" Type="{REL_OFFICE}/footnotes" Target="footnotes.xml"/>'

STYLES = XML + (
    f"<w:styles {W}>"
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="40"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720"/></w:pPr></w:style>'
    '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
    '<w:style w:type="character" w:styleId="PlaceholderText"><w:name w:val="Placeholder Text"/><w:rPr><w:color w:val="808080"/></w:rPr></w:style>'
    '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
    '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblCellMar><w:left w:w="108" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
    "</w:styles>"
)

SETTINGS = XML + f'<w:settings {W}><w:defaultTabStop w:val="720"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>'

NUMBERING = XML + (
    f"<w:numbering {W}>"
    '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>'
    "</w:abstractNum>"
    '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
    "</w:numbering>"
)

CORE = XML + (
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    "<dc:title>fill-word-template fixture</dc:title><dc:creator>fill-word-template</dc:creator>"
    '<dcterms:created xsi:type="dcterms:W3CDTF">2026-09-07T00:00:00Z</dcterms:created>'
    '<dcterms:modified xsi:type="dcterms:W3CDTF">2026-09-07T00:00:00Z</dcterms:modified>'
    "</cp:coreProperties>"
)

APP = XML + (
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    "<Application>fill-word-template fixtures</Application></Properties>"
)

SECT = (
    '<w:sectPr><w:headerReference w:type="default" r:id="rId3"/><w:footerReference w:type="default" r:id="rId4"/>'
    '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
)


def header(text_runs: str) -> str:
    return XML + f"<w:hdr {NS}><w:p>{text_runs}</w:p></w:hdr>"


def footer(text_runs: str) -> str:
    return XML + f"<w:ftr {NS}><w:p>{text_runs}</w:p></w:ftr>"


def document(body: str) -> str:
    return XML + f"<w:document {NS}><w:body>{body}{SECT}</w:body></w:document>"


def t(text: str) -> str:
    """A w:t; preserve whitespace when it matters. `text` must already be XML-escaped."""
    attr = ' xml:space="preserve"' if text != text.strip() or "  " in text else ""
    return f"<w:t{attr}>{text}</w:t>"


def p(inner: str, ppr: str = "") -> str:
    return f"<w:p>{ppr}{inner}</w:p>"


def r(inner: str, rpr: str = "") -> str:
    return f"<w:r>{rpr}{inner}</w:r>"


def cell(inner: str, width: int = 4500) -> str:
    return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>{inner}</w:tc>'


def table(*rows: str) -> str:
    return ('<w:tbl><w:tblPr><w:tblStyle w:val="TableNormal"/><w:tblW w:w="0" w:type="auto"/></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="4500"/><w:gridCol w:w="4500"/></w:tblGrid>' + "".join(f"<w:tr>{row}</w:tr>" for row in rows) + "</w:tbl>")


BASE_PARTS = {
    "word/styles.xml": STYLES,
    "word/settings.xml": SETTINGS,
    "word/numbering.xml": NUMBERING,
    "docProps/core.xml": CORE,
    "docProps/app.xml": APP,
}

# Entry order mirrors what Word writes; the filler must preserve it.
ORDER = [
    "[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/_rels/document.xml.rels",
    "word/header1.xml", "word/footer1.xml", "word/footnotes.xml", "word/styles.xml", "word/settings.xml", "word/numbering.xml",
    "word/comments.xml", "_xmlsignatures/origin.sigs", "docProps/core.xml", "docProps/app.xml",
]


def package(parts: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name in ORDER:
            if name not in parts:
                continue
            data = parts[name]
            if isinstance(data, str):
                data = data.encode("utf-8")
            zi = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            zi.create_system = 3  # ZipInfo defaults this from the host OS (0 on Windows); pin to Unix
            z.writestr(zi, data)
        unknown = set(parts) - set(ORDER)
        if unknown:
            raise ValueError(f"parts not in ORDER: {sorted(unknown)}")
    return buf.getvalue()


# --------------------------------------------------------------------------------------
# Fixture bodies. Paragraph indices and expected texts live in assets/expected/*.json; keep
# this XML in step with those files.
# --------------------------------------------------------------------------------------

def six_position() -> dict[str, str | bytes]:
    body = (
        p(r(t("Client agreement")), '<w:pPr><w:pStyle w:val="Title"/></w:pPr>')                        # p0
        + p(r(t("Dear {{ first }} {{ last }},")))                                                       # p1 shared node
        + p(r(t("Reference: {{ cli")) + r(t("ent_name }} (copy 1)")))                                    # p2 split, same format
        + p(r(t("Amount:") + "<w:tab/>" + t("{{ amount }}")))                                            # p3 existing tab before
        + p(r(t("Issued on") + "<w:br/>" + t("{{ issued }}")))                                           # p4 existing break before
        + p(r(t("Code: {{ code_a }}{{ code_b }}")))                                                     # p5 adjacent
        + p(r(t("See ")) + '<w:hyperlink r:id="rId6">' + r(t("{{ client_name }}"), '<w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>') + "</w:hyperlink>")  # p6 hyperlink
        + p(r(t("Use {braces} carefully; the value {{ remarks }} follows.")))                          # p7 literal single braces
        + p(r(t("Active: {{ active }}")), '<w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>')  # p8 numbered
        + table(cell(p(r(t("Count")))) + cell(p(r(t("{{ count }}")))))                                   # p9, p10
        + p(r(t("Signed for {{ client_name }}")))                                                       # p11 repeated identifier
    )
    return {
        "[Content_Types].xml": content_types(),
        "_rels/.rels": root_rels(),
        "word/document.xml": document(body),
        "word/_rels/document.xml.rels": document_rels(HYPERLINK_REL),
        "word/header1.xml": header(r(t("{{ client_name }} - Confidential"))),
        "word/footer1.xml": footer(r(t("Ref {{ code_a }}"))),
        **BASE_PARTS,
    }


def simple(body_paragraphs: str, *, doc_rels_extra: str = "", ct_overrides=(), ct_defaults=(), root_extra: str = "", extra_parts: dict | None = None) -> dict[str, str | bytes]:
    body = p(r(t("Client agreement")), '<w:pPr><w:pStyle w:val="Title"/></w:pPr>') + body_paragraphs
    parts: dict[str, str | bytes] = {
        "[Content_Types].xml": content_types(list(ct_overrides), list(ct_defaults)),
        "_rels/.rels": root_rels(root_extra),
        "word/document.xml": document(body),
        "word/_rels/document.xml.rels": document_rels(doc_rels_extra),
        "word/header1.xml": header(r(t("Confidential"))),
        "word/footer1.xml": footer(r(t("Page footer"))),
        **BASE_PARTS,
    }
    parts.update(extra_parts or {})
    return parts


FOOTNOTES = XML + (
    f"<w:footnotes {NS}>"
    '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'          # p0
    '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'  # p1
    '<w:footnote w:id="1">' + p(r(t("See [Reference] for details."))) + "</w:footnote>"                  # p2
    "</w:footnotes>"
)

PLACEHOLDER_RUN = r(t("Click here to enter text."), '<w:rPr><w:rStyle w:val="PlaceholderText"/></w:rPr>')


def mixed_conventions() -> dict[str, str | bytes]:
    body = (
        p(r(t("STATEMENT OF WORK")), '<w:pPr><w:pStyle w:val="Title"/></w:pPr>')                                                   # p0
        + p(r(t("Prepared for [Client Name] on &lt;insert date&gt;")))                                                             # p1
        + p(r(t("[Guidance: delete this paragraph before sending]")))                                                              # p2
        + p(r(t("Section 3 - Optional services (include only if applicable)")), '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>')  # p3
        + p('<w:bookmarkStart w:id="7" w:name="optional"/>' + r(t("Optional services are provided at the rates in Schedule B.")) + '<w:bookmarkEnd w:id="7"/>')  # p4
        + table(cell(p(r(t("Service")))) + cell(p(r(t("Rate")))),                                                                 # p5, p6
                cell(p(r(t("Advisory")))) + cell(p(r(t("[rate]")))))                                                              # p7, p8
        + p(r(t("End of optional services.")))                                                                                    # p9
        + p(r(t("Customer contact: ____________________")))                                                                       # p10
        + p(r(t("Total: {{ total_amount }}")))                                                                                    # p11
        + table(cell(p(r(t("Item")))) + cell(p(r(t("Qty")))),                                                                    # p12, p13
                cell(p(r(t("&lt;item name&gt;")))) + cell(p("")))                                                                 # p14, p15 (empty cell)
        + p(r(t("Signatory: "))                                                                                                    # p16 inline control
            + '<w:sdt><w:sdtPr><w:alias w:val="Signatory name"/><w:tag w:val="signatory"/><w:id w:val="2001"/><w:showingPlcHdr/><w:text/></w:sdtPr>'
            + "<w:sdtContent>" + PLACEHOLDER_RUN + "</w:sdtContent></w:sdt>")
        + p(r(t("Internal note: remove before issue"), "<w:rPr><w:vanish/></w:rPr>"))                                             # p17 hidden
        + p(r(t("Remarks: {{ remarks }}")) + r('<w:footnoteReference w:id="1"/>', '<w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr>'))  # p18
    )
    return {
        "[Content_Types].xml": content_types([("/word/footnotes.xml", f"{CT_WML}.footnotes+xml")]),
        "_rels/.rels": root_rels(),
        "word/document.xml": document(body),
        "word/_rels/document.xml.rels": document_rels(FOOTNOTES_REL),
        "word/header1.xml": header(r(t("Confidential - [Client Name]"))),
        "word/footer1.xml": footer(r(t("Page footer"))),
        "word/footnotes.xml": FOOTNOTES,
        **BASE_PARTS,
    }


def deletion_safety() -> dict[str, str | bytes]:
    body = (
        p(r(t("First section text.")), '<w:pPr><w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:pPr>')   # p1 section break
        + p('<w:bookmarkStart w:id="3" w:name="span"/>' + r(t("Bookmark starts here")))                          # p2
        + p(r(t("and ends here.")) + '<w:bookmarkEnd w:id="3"/>')                                                 # p3
        + table(cell(p(r(t("Only paragraph in cell [x]")), '<w:pPr><w:jc w:val="center"/></w:pPr>'), 9000))       # p4 sole paragraph in its cell
        + p(r(t("Tail paragraph {{ tail }}")))                                                                    # p5
    )
    return simple(body)


def mixed_format_split() -> dict[str, str | bytes]:
    # p1: the second fragment is bold; the first owning run's formatting will win -> review item.
    return simple(p(r(t("Name: {{ cli")) + r(t("ent_name }}"), "<w:rPr><w:b/></w:rPr>")))


def tab_in_placeholder() -> dict[str, str | bytes]:
    # p1 paragraph text is "{{\tx }}": a candidate that covers a structural tab is ineligible.
    return simple(p(r(t("{{") + "<w:tab/>" + t("x }}"))))


def comments_only() -> dict[str, str | bytes]:
    comments = XML + (
        f'<w:comments {NS}><w:comment w:id="0" w:author="Reviewer" w:date="2026-09-07T00:00:00Z" w:initials="RV">'
        + p(r(t("Please confirm the wording.")), '<w:pPr><w:pStyle w:val="Normal"/></w:pPr>')
        + "</w:comment></w:comments>"
    )
    body = (
        p('<w:commentRangeStart w:id="0"/>' + r(t("This clause is under discussion.")) + '<w:commentRangeEnd w:id="0"/>' + r('<w:commentReference w:id="0"/>'))  # p1
        + p(r(t("Client: {{ client_name }}")))                                                         # p2 eligible
    )
    return simple(
        body,
        doc_rels_extra=COMMENTS_REL,
        ct_overrides=[("/word/comments.xml", f"{CT_WML}.comments+xml")],
        extra_parts={"word/comments.xml": comments},
    )


def revisions_only() -> dict[str, str | bytes]:
    body = (
        p(r(t("The fee is ")) + '<w:ins w:id="1" w:author="Reviewer" w:date="2026-09-07T00:00:00Z">' + r(t("now ")) + "</w:ins>"
          + '<w:del w:id="2" w:author="Reviewer" w:date="2026-09-07T00:00:00Z">' + r("<w:delText>previously </w:delText>") + "</w:del>" + r(t("payable monthly.")))  # p1
        + p(r(t("Client: {{ client_name }}")))                                                          # p2 eligible
        + p(r(t("Added clause for {{ client_name }}")), '<w:pPr><w:rPr><w:ins w:id="3" w:author="Reviewer" w:date="2026-09-07T00:00:00Z"/></w:rPr></w:pPr>')  # p3 tracked paragraph mark
    )
    return simple(body)


def block_sdt_wrapping() -> dict[str, str | bytes]:
    body = (
        '<w:sdt><w:sdtPr><w:alias w:val="Client section"/><w:tag w:val="client_section"/><w:id w:val="1001"/></w:sdtPr><w:sdtContent>'
        + p(r(t("Client: {{ client_name }}")))                                                          # p1 inside a block-level control
        + "</w:sdtContent></w:sdt>"
        + p(r(t("Amount: {{ amount }}")))                                                               # p2
    )
    return simple(body)


def complex_field_result() -> dict[str, str | bytes]:
    body = p(
        r('<w:fldChar w:fldCharType="begin"/>')
        + r('<w:instrText xml:space="preserve"> DOCPROPERTY Title </w:instrText>')
        + r('<w:fldChar w:fldCharType="separate"/>')
        + r(t("{{ client_name }}"))                                                                     # result run, no field marker of its own
        + r('<w:fldChar w:fldCharType="end"/>')
    ) + p(r(t("Amount: {{ amount }}")))                                                                 # p2
    return simple(body)


def signature_marker() -> dict[str, str | bytes]:
    # Presence detection only: an empty signature-origin part with its relationship and content type.
    return simple(
        p(r(t("Client: {{ client_name }}"))),
        ct_defaults=[("sigs", "application/vnd.openxmlformats-package.digital-signature-origin")],
        root_extra=f'<Relationship Id="rId4" Type="{REL_PKG}/digital-signature/origin" Target="_xmlsignatures/origin.sigs"/>',
        extra_parts={"_xmlsignatures/origin.sigs": b""},
    )


# A root element as Word 2016+ writes it: many namespaces, several unused in the body, and an
# mc:Ignorable list naming prefixes. ElementTree re-serialisation would drop the unused xmlns
# declarations and keep mc:Ignorable="w14 w15 wp14" verbatim, so Word reports the file as corrupt.
REALISTIC_ROOT_ATTRS = (
    ' xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"'
    ' xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
    ' xmlns:o="urn:schemas-microsoft-com:office:office"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    ' xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
    ' xmlns:v="urn:schemas-microsoft-com:vml"'
    ' xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"'
    ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
    ' xmlns:w10="urn:schemas-microsoft-com:office:word"'
    ' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    ' xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
    ' xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"'
    ' xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"'
    ' xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"'
    ' xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"'
    ' xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"'
    ' mc:Ignorable="w14 w15 wp14"'
)


def mc_ignorable_root() -> dict[str, str | bytes]:
    body = (
        '<w:p w14:paraId="12345678" w14:textId="77777777" w:rsidR="00AB12CD" w:rsidRDefault="00AB12CD">'
        '<w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r w:rsidRPr="00AB12CD">' + t("Client agreement") + "</w:r></w:p>"        # p0
        + '<w:p w14:paraId="23456789" w14:textId="77777778" w:rsidR="00AB12CD">'
        + '<w:r w:rsidR="00AB12CD">' + t("Client: {{ cli") + "</w:r>"
        + '<w:r w:rsidR="00EF3456">' + t("ent_name }}") + "</w:r></w:p>"                                                   # p1 split, both runs without rPr
        + '<w:p w14:paraId="3456789A" w14:textId="77777779" w:rsidR="00AB12CD"><w:r>' + t("Amount: {{ amount }}") + "</w:r></w:p>"  # p2
    )
    document = XML + f"<w:document{REALISTIC_ROOT_ATTRS}><w:body>{body}{SECT}</w:body></w:document>"
    return {
        "[Content_Types].xml": content_types(),
        "_rels/.rels": root_rels(),
        "word/document.xml": document,
        "word/_rels/document.xml.rels": document_rels(),
        "word/header1.xml": header(r(t("Confidential"))),
        "word/footer1.xml": footer(r(t("Page footer"))),
        **BASE_PARTS,
    }


FIXTURE_BUILDERS = {
    "six-position": six_position,
    "mixed-conventions": mixed_conventions,
    "deletion-safety": deletion_safety,
    "mixed-format-split": mixed_format_split,
    "tab-in-placeholder": tab_in_placeholder,
    "comments-only": comments_only,
    "revisions-only": revisions_only,
    "block-sdt-wrapping": block_sdt_wrapping,
    "complex-field-result": complex_field_result,
    "signature-marker": signature_marker,
    "mc-ignorable-root": mc_ignorable_root,
}


def logical_view(data: bytes) -> list[tuple]:
    """What a fixture *is*, independent of the deflate implementation that wrote it."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return [
            (i.filename, i.date_time, i.external_attr, i.create_system, i.compress_type, z.read(i.filename))
            for i in z.infolist()
        ]


LABEL_PARTS = ("docMetadata/LabelInfo.xml", "docProps/custom.xml")


def diagnose(name: str, committed: bytes, fresh: bytes) -> str | None:
    """None if the committed fixture is logically identical to a fresh build, else a reason."""
    try:
        have = logical_view(committed)
    except zipfile.BadZipFile:
        return f"{name}: committed file is not a zip"
    want = logical_view(fresh)
    if have == want:
        return None
    have_names = [h[0] for h in have]
    if any(part in have_names for part in LABEL_PARTS):
        return (f"{name}: rewritten by a sensitivity-labelling service (found {', '.join(x for x in LABEL_PARTS if x in have_names)}); "
                f"rebuild it outside synced folders")
    want_names = [w[0] for w in want]
    if have_names != want_names:
        return f"{name}: entry list differs (committed {len(have_names)} entries, fresh {len(want_names)})"
    fields = ("date_time", "external_attr", "create_system", "compress_type")
    for h, w in zip(have, want):
        drifted = [f for f, hv, wv in zip(fields, h[1:5], w[1:5]) if hv != wv]
        if drifted:
            return f"{name}: zip header field(s) {', '.join(drifted)} differ for {h[0]}"
        if h[5] != w[5]:
            return f"{name}: content of {h[0]} differs"
    return f"{name}: differs"


def main(argv: list[str]) -> int:
    check = "--check" in argv
    os.makedirs(FIXTURES, exist_ok=True)
    drift = []
    for name, build in FIXTURE_BUILDERS.items():
        data = package(build())
        path = os.path.join(FIXTURES, f"{name}.docx")
        if check:
            try:
                with open(path, "rb") as fh:
                    committed = fh.read()
            except FileNotFoundError:
                drift.append(f"{name}: missing")
                continue
            reason = diagnose(name, committed, data)
            if reason:
                drift.append(reason)
        else:
            with open(path, "wb") as fh:
                fh.write(data)
            print(f"wrote assets/fixtures/{name}.docx ({len(data)} bytes)")
    if check:
        for d in drift:
            print("DRIFT", d)
        print("fixtures match build_fixtures.py" if not drift else "fixtures drifted")
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
