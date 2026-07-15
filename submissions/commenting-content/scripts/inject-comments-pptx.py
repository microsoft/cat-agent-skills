"""
Inject native PowerPoint comments into a .pptx file.
Author tag: Copilot Studio AI

Usage:
    python inject-comments-pptx.py <input.pptx> <output.pptx> <comments.json>

comments.json format:
    [
        {
            "slide": 1,
            "idx": 1,
            "text": "Comment text here",
            "x": 1270,
            "y": 1270
        },
        ...
    ]

Notes:
  - "slide" is 1-based (slide 1 = first slide).
  - "idx" must be unique per slide (used as the comment index within that slide).
  - "x" / "y" are EMU positions on the slide (1270 = top-left corner is a safe default).
  - Multiple comments on the same slide are all written into a single comment file
    for that slide (ppt/comments/comment<slide>.xml).
"""
import sys, json, io, zipfile, re
from collections import defaultdict
from datetime import datetime, timezone

if len(sys.argv) != 4:
    print("Usage: python inject-comments-pptx.py <input.pptx> <output.pptx> <comments.json>")
    sys.exit(1)

INPUT  = sys.argv[1]
OUTPUT = sys.argv[2]

with open(sys.argv[3], "r", encoding="utf-8") as f:
    raw = json.load(f)

# Group comments by slide number
by_slide = defaultdict(list)
for c in raw:
    by_slide[c["slide"]].append(c)

CM_CT    = "application/vnd.openxmlformats-officedocument.presentationml.comments+xml"
CM_REL   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
AUTH_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/commentAuthors"
AUTH_CT  = "application/vnd.openxmlformats-officedocument.presentationml.commentAuthors+xml"

AUTHOR   = "Copilot Studio AI"
INITIALS = "CS"
DT       = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── helpers ──────────────────────────────────────────────────────────────────

def make_comments_xml(slide_comments):
    """Build ppt/comments/comment<N>.xml for a list of comment dicts."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<p:cmLst xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"',
        '         xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"',
        '         xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
    ]
    for c in slide_comments:
        x   = c.get("x", 1270)
        y   = c.get("y", 1270)
        idx = c["idx"]
        txt = c["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f'  <p:cm authorId="0" dt="{DT}" idx="{idx}">')
        lines.append(f'    <p:pos x="{x}" y="{y}"/>')
        lines.append(f'    <p:text>{txt}</p:text>')
        lines.append( '  </p:cm>')
    lines.append('</p:cmLst>')
    return "\n".join(lines)


def make_authors_xml(last_idx):
    """Build ppt/commentAuthors.xml."""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<p:cmAuthorLst xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">\n'
        f'  <p:cmAuthor id="0" name="{AUTHOR}" initials="{INITIALS}" lastIdx="{last_idx}" clrIdx="0"/>\n'
        '</p:cmAuthorLst>'
    )


def next_rel_id(rels_xml):
    """Return an rId not already used in the given .rels XML string."""
    used = {int(n) for n in re.findall(r'Id="rId(\d+)"', rels_xml)}
    i = 1
    while i in used:
        i += 1
    return f"rId{i}"


def ensure_slide_rels(files, slide_num, cm_rel_target):
    """Add a comments relationship to the slide's .rels file, creating it if needed."""
    rels_path = f"ppt/slides/_rels/slide{slide_num}.xml.rels"
    if rels_path in files:
        rels = files[rels_path].decode("utf-8")
        if CM_REL not in rels:
            rel_id = next_rel_id(rels)
            rels = rels.replace(
                "</Relationships>",
                f'  <Relationship Id="{rel_id}" Type="{CM_REL}" Target="{cm_rel_target}"/>\n</Relationships>'
            )
    else:
        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            f'  <Relationship Id="rId1" Type="{CM_REL}" Target="{cm_rel_target}"/>\n'
            '</Relationships>'
        )
    files[rels_path] = rels.encode("utf-8")


# ── main ─────────────────────────────────────────────────────────────────────

with zipfile.ZipFile(INPUT, "r") as zin:
    names = zin.namelist()
    files = {n: zin.read(n) for n in names}

auth_path = "ppt/commentAuthors.xml"
max_idx   = 0

for slide_num, comments in by_slide.items():
    cm_path       = f"ppt/comments/comment{slide_num}.xml"
    cm_rel_target = f"../comments/comment{slide_num}.xml"

    files[cm_path] = make_comments_xml(comments).encode("utf-8")
    ensure_slide_rels(files, slide_num, cm_rel_target)

    max_idx = max(max_idx, max(c["idx"] for c in comments))

    # Update [Content_Types].xml
    ct = files["[Content_Types].xml"].decode("utf-8")
    if cm_path not in ct:
        ct = ct.replace(
            "</Types>",
            f'  <Override PartName="/{cm_path}" ContentType="{CM_CT}"/>\n</Types>'
        )
        files["[Content_Types].xml"] = ct.encode("utf-8")

    print(f"  ✓ Slide {slide_num}: {len(comments)} comment(s) written to {cm_path}")

# commentAuthors.xml
files[auth_path] = make_authors_xml(max_idx).encode("utf-8")

# Ensure commentAuthors in [Content_Types].xml
ct = files["[Content_Types].xml"].decode("utf-8")
if "commentAuthors.xml" not in ct:
    ct = ct.replace(
        "</Types>",
        f'  <Override PartName="/ppt/commentAuthors.xml" ContentType="{AUTH_CT}"/>\n</Types>'
    )
    files["[Content_Types].xml"] = ct.encode("utf-8")

# Ensure commentAuthors relationship in presentation rels
prs_rels_path = "ppt/_rels/presentation.xml.rels"
if prs_rels_path in files:
    pr = files[prs_rels_path].decode("utf-8")
    if AUTH_REL not in pr:
        rel_id = next_rel_id(pr)
        pr = pr.replace(
            "</Relationships>",
            f'  <Relationship Id="{rel_id}" Type="{AUTH_REL}" Target="commentAuthors.xml"/>\n</Relationships>'
        )
        files[prs_rels_path] = pr.encode("utf-8")

# Write output
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
    for name, data in files.items():
        zout.writestr(name, data)

with open(OUTPUT, "wb") as f:
    f.write(buf.getvalue())

total = sum(len(v) for v in by_slide.values())
print(f"\nDone — {total} comment(s) across {len(by_slide)} slide(s) written to:\n  {OUTPUT}")
