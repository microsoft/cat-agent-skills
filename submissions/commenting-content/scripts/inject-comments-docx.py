"""
Inject native Word comments into a .docx file.
Author tag: Copilot Studio AI

Usage:
    python inject-comments-docx.py <input.docx> <output.docx> <comments.json>

comments.json format:
    [
        {
            "id": 0,
            "search_phrase": "unique phrase in the target paragraph",
            "paragraphs": ["Comment line 1", "Comment line 2"]
        },
        ...
    ]
"""
import sys, json, zipfile, io, re
from datetime import datetime, timezone
from lxml import etree

if len(sys.argv) != 4:
    print("Usage: python inject-comments-docx.py <input.docx> <output.docx> <comments.json>")
    sys.exit(1)

INPUT  = sys.argv[1]
OUTPUT = sys.argv[2]

with open(sys.argv[3], "r", encoding="utf-8") as f:
    raw = json.load(f)

COMMENTS = [(c["id"], c["search_phrase"], c["paragraphs"]) for c in raw]

# ── namespace helpers ────────────────────────────────────────────────────────
W   = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT  = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

def w(tag):  return f"{{{W}}}{tag}"
def r(tag):  return f"{{{REL}}}{tag}"

AUTHOR   = "Copilot Studio AI"
INITIALS = "CS"
DATE     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── helpers ──────────────────────────────────────────────────────────────────

def para_text(p_elem):
    """Concatenate all w:t text in a paragraph element."""
    return "".join((t.text or "") for t in p_elem.iter(w("t")))


def next_rel_id(rels_xml):
    """Return an rId not already used in the given .rels XML string."""
    used = {int(n) for n in re.findall(r'Id="rId(\d+)"', rels_xml)}
    i = 1
    while i in used:
        i += 1
    return f"rId{i}"


# Namespace declarations mirrored from document.xml so a freshly created
# comments.xml validates the same way Word writes it.
COMMENTS_NS = {
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "cx":  "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "mc":  "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "o":   "urn:schemas-microsoft-com:office:office",
    "r":   REL,
    "m":   "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "v":   "urn:schemas-microsoft-com:vml",
    "wp":  "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "w10": "urn:schemas-microsoft-com:office:word",
    "w":   W,
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
}


def new_comments_root():
    """Create an empty word/comments.xml root — used only when the document has
    no comments yet. Existing comments are always preserved and appended to."""
    root = etree.Element(w("comments"), nsmap=COMMENTS_NS)
    root.set(f"{{{COMMENTS_NS['mc']}}}Ignorable", "w14 w15")
    return root


def append_comment(root, cid, paras):
    """Append a single <w:comment> to a comments root, leaving every comment
    already present in that root untouched."""
    cmt = etree.SubElement(root, w("comment"))
    cmt.set(w("id"),       str(cid))
    cmt.set(w("author"),   AUTHOR)
    cmt.set(w("date"),     DATE)
    cmt.set(w("initials"), INITIALS)

    for idx, line in enumerate(paras):
        p = etree.SubElement(cmt, w("p"))
        pPr = etree.SubElement(p, w("pPr"))
        pStyle = etree.SubElement(pPr, w("pStyle"))
        pStyle.set(w("val"), "CommentText")

        # First paragraph gets the annotationRef run
        if idx == 0:
            r_ref = etree.SubElement(p, w("r"))
            rPr_ref = etree.SubElement(r_ref, w("rPr"))
            rStyle_ref = etree.SubElement(rPr_ref, w("rStyle"))
            rStyle_ref.set(w("val"), "CommentReference")
            etree.SubElement(r_ref, w("annotationRef"))

        # Text run
        r_txt = etree.SubElement(p, w("r"))
        t = etree.SubElement(r_txt, w("t"))
        t.text = line
        if line != line.strip():
            t.set(XML_SPACE, "preserve")


def inject_comment_in_para(para, cid):
    """
    Wrap the paragraph's runs with commentRangeStart / commentRangeEnd
    and append a commentReference run.
    """
    # commentRangeStart goes before the first w:r (or as first child after w:pPr)
    cs = etree.Element(w("commentRangeStart"))
    cs.set(w("id"), str(cid))

    ce = etree.Element(w("commentRangeEnd"))
    ce.set(w("id"), str(cid))

    # Reference run
    r_ref = etree.Element(w("r"))
    rPr = etree.SubElement(r_ref, w("rPr"))
    rStyle = etree.SubElement(rPr, w("rStyle"))
    rStyle.set(w("val"), "CommentReference")
    ref = etree.SubElement(r_ref, w("commentReference"))
    ref.set(w("id"), str(cid))

    children = list(para)
    # Find index after w:pPr (skip it); default to 0 if not present
    insert_pos = 0
    for i, child in enumerate(children):
        if child.tag == w("pPr"):
            insert_pos = i + 1
            break

    para.insert(insert_pos, cs)
    # After insert, last position shifted by 1
    para.append(ce)
    para.append(r_ref)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    # Read all files from the original zip
    with zipfile.ZipFile(INPUT, "r") as zin:
        names   = zin.namelist()
        file_map = {name: zin.read(name) for name in names}

    # Parse document.xml
    doc_xml  = file_map["word/document.xml"]
    tree     = etree.fromstring(doc_xml)
    body     = tree.find(f"{{{W}}}body")

    # Merge into any existing comments instead of overwriting them: load the
    # document's current comments.xml (if present) and continue numbering after
    # the highest id already in use, so pre-existing comments are never wiped
    # and newly injected ids can't collide with them.
    if "word/comments.xml" in file_map:
        comments_root = etree.fromstring(file_map["word/comments.xml"])
        existing_ids  = [
            int(c.get(w("id")))
            for c in comments_root.findall(w("comment"))
            if (c.get(w("id")) or "").lstrip("-").isdigit()
        ]
    else:
        comments_root = new_comments_root()
        existing_ids  = []

    next_id = max(existing_ids) + 1 if existing_ids else 0

    # We may need to search the same paragraph for multiple comments,
    # so collect paragraphs first
    para_list = list(body.iter(w("p")))

    placed = 0
    for _json_id, search, paras in COMMENTS:
        cid = next_id  # consumed only if this comment is actually placed
        for para in para_list:
            txt = para_text(para)
            if search in txt:
                inject_comment_in_para(para, cid)
                append_comment(comments_root, cid, paras)
                next_id += 1
                placed  += 1
                print(f"  ✓ Comment {cid} placed on paragraph: '{txt[:80].strip()}…'")
                break
        else:
            print(f"  ✗ Comment not placed — search text not found: '{search}'")

    # Serialise modified document.xml + the merged comments.xml
    file_map["word/document.xml"] = etree.tostring(
        tree, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    file_map["word/comments.xml"] = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    # Update [Content_Types].xml — add comments override if missing
    ct_xml = file_map["[Content_Types].xml"].decode("utf-8")
    if "comments" not in ct_xml:
        ct_xml = ct_xml.replace(
            "</Types>",
            '<Override PartName="/word/comments.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.comments+xml"/></Types>'
        )
        file_map["[Content_Types].xml"] = ct_xml.encode("utf-8")

    # Update word/_rels/document.xml.rels — add comments relationship if missing
    rels_xml = file_map["word/_rels/document.xml.rels"].decode("utf-8")
    if "comments" not in rels_xml:
        rel_id = next_rel_id(rels_xml)
        rels_xml = rels_xml.replace(
            "</Relationships>",
            f'<Relationship Id="{rel_id}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" '
            'Target="comments.xml"/></Relationships>'
        )
        file_map["word/_rels/document.xml.rels"] = rels_xml.encode("utf-8")

    # Write output zip
    buf = io.BytesIO()
    with zipfile.ZipFile(INPUT, "r") as zin:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                zout.writestr(
                    zin.getinfo(name),
                    file_map.get(name, zin.read(name))
                )
            # Add comments.xml if it wasn't already in the archive
            if "word/comments.xml" not in names:
                zout.writestr("word/comments.xml", file_map["word/comments.xml"])

    with open(OUTPUT, "wb") as f:
        f.write(buf.getvalue())

    print(f"\nDone — {placed} comments written to:\n  {OUTPUT}")


if __name__ == "__main__":
    main()
