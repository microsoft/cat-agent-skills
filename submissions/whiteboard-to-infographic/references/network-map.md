# Archetype: Network Map (topology) — native PowerPoint (.pptx)

Use when the sketch is locations / systems / actors connected by flows, with no
single linear order. Build it as a **single editable slide** with `python-pptx`,
drawn natively as shapes (rounded-rect nodes, straight/elbow connectors with
arrowheads, dashed region clusters, white label chips).

This is the higher-effort archetype: **edge routing is up to you.** Place nodes
first, leave generous gutters, and route edges through the gaps — approach a node
straight-on (horizontal or vertical into an edge), never at a shallow diagonal,
and don't run an edge through a node. Compute coordinates deterministically and
check for overlaps; you can't rely on eyeballing the result inside the sandbox.

## Layout

```
┌──────────────────────────────────────────────────────────┐
│ HEADER: title · subtitle · accent rule · (scope at right) │
├──────────────────────────────────────────────────────────┤
│ SUPPLY NETWORK (eyebrow)                                   │
│   [node]──PO─►[node]      ┌─ dashed region cluster ─┐      │
│      │                    │  [node]   [node]        │      │
│   [flow legend]           └─────────────────────────┘      │
│                    [standalone / recurring node]           │
├──────────────────────────────────────────────────────────┤
│ BOTTOM BAND: requirements & open items (flags inline)      │
└──────────────────────────────────────────────────────────┘
```

**Signature device**: a dashed **region cluster** grouping co-located nodes, plus
clean labeled edges. An output/endpoint (e.g. customer delivery) stays *outside*
the cluster even if drawn nearby on the board.

## Color placeholders

Same tokens as the rail: `INK`, `SECONDARY`, `ACCENT`, `CARD`, `ATINT`,
`INK_SOFT`, plus `HAIR` (hairline chip border). Substitute the client palette.

## python-pptx skeleton (validated; adapt freely)

Arrowheads and dashes aren't in python-pptx's high-level API — set them by
appending to the line's `<a:ln>` element, as below (this renders correctly).

```python
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

INK="1B2A4A"; SECONDARY="3E6690"; ACCENT="C8322D"; CARD="EDF1F6"; ATINT="F6E3E2"; INK_SOFT="5A6B7C"; HAIR="C9D6E2"

def C(h): return RGBColor.from_string(h)

prs=Presentation(); prs.slide_width=Emu(12192000); prs.slide_height=Emu(int(12192000/1.6))
EMU_PER_PX=prs.slide_width/1600
def PX(v): return Emu(int(v*EMU_PER_PX))
slide=prs.slides.add_slide(prs.slide_layouts[6])
def _flat(s): s.shadow.inherit=False; return s

def node(x,y,w,h,title,sub=None,fill="FFFFFF",border=INK):
    s=_flat(slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,PX(x),PX(y),PX(w),PX(h)))
    s.fill.solid(); s.fill.fore_color.rgb=C(fill); s.line.color.rgb=C(border); s.line.width=Pt(2)
    tf=s.text_frame; tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER
    r=p.add_run(); r.text=title; r.font.size=Pt(15); r.font.bold=True; r.font.name="Arial Narrow"; r.font.color.rgb=C(INK)
    if sub:
        p2=tf.add_paragraph(); p2.alignment=PP_ALIGN.CENTER
        r2=p2.add_run(); r2.text=sub; r2.font.size=Pt(9); r2.font.name="Arial"; r2.font.color.rgb=C(INK_SOFT)
    return s

def cluster(x,y,w,h,name):
    s=_flat(slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,PX(x),PX(y),PX(w),PX(h)))
    s.fill.background(); s.line.color.rgb=C(SECONDARY); s.line.width=Pt(1.8)
    ln=s.line._get_or_add_ln(); ln.append(ln.makeelement(qn('a:prstDash'),{'val':'dash'}))
    lb=slide.shapes.add_textbox(PX(x+14),PX(y+6),PX(w-28),PX(20))
    r=lb.text_frame.paragraphs[0].add_run(); r.text=name
    r.font.size=Pt(12); r.font.bold=True; r.font.name="Arial Narrow"; r.font.color.rgb=C(SECONDARY)
    return s

def edge(x1,y1,x2,y2,dashed=False,both=False,color=INK):
    cn=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,PX(x1),PX(y1),PX(x2),PX(y2))
    cn.line.color.rgb=C(color); cn.line.width=Pt(2.2)
    ln=cn.line._get_or_add_ln()
    ln.append(ln.makeelement(qn('a:tailEnd'),{'type':'triangle','w':'med','len':'med'}))
    if both: ln.append(ln.makeelement(qn('a:headEnd'),{'type':'triangle','w':'med','len':'med'}))
    if dashed: ln.append(ln.makeelement(qn('a:prstDash'),{'val':'dash'}))
    return cn

def chip(cx,cy,text):                       # white label chip on an edge midpoint
    w=len(text)*8+16
    s=_flat(slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,PX(cx-w/2),PX(cy-12),PX(w),PX(24)))
    s.fill.solid(); s.fill.fore_color.rgb=C("FFFFFF"); s.line.color.rgb=C(HAIR); s.line.width=Pt(1)
    tf=s.text_frame; tf.word_wrap=False; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER
    r=p.add_run(); r.text=text; r.font.size=Pt(11); r.font.bold=True; r.font.name="Arial Narrow"; r.font.color.rgb=C(INK)
    return s

# HEADER
hb=slide.shapes.add_textbox(PX(40),PX(24),PX(1200),PX(50))
r=hb.text_frame.paragraphs[0].add_run(); r.text="‹TITLE›"
r.font.size=Pt(44); r.font.bold=True; r.font.name="Arial Narrow"; r.font.color.rgb=C(INK)
rule=_flat(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,PX(40),PX(96),PX(1520),PX(4)))
rule.fill.solid(); rule.fill.fore_color.rgb=C(ACCENT); rule.line.fill.background()

# EDGES FIRST, then nodes on top (node fills cover the line ends)
edge(300,260,470,260); chip(385,260,"‹PO›")
# ... more edges ...
node(150,220,150,80,"‹NODE›","‹sub›")
cluster(800,180,340,340,"‹REGION›")
node(830,220,120,70,"‹NODE›")
# ... more nodes ...

# BOTTOM BAND (requirements & open items)
band=_flat(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,PX(0),PX(680),PX(1600),PX(320)))
band.fill.solid(); band.fill.fore_color.rgb=C(INK); band.line.fill.background()

prs.save("infographic-v1.pptx")   # v2, v3, ... on each revision — never reuse a name
```

## Build tips
- **Draw edges before nodes** so node fills sit on top of the line ends.
- Pick node positions first (on paper or a coord sketch); leave generous gutters
  for edge routing. Bidirectional relationships use `both=True`.
- Keep an output/endpoint node **outside** any dashed cluster even if drawn near
  it on the board.
- A **standalone/recurring** concept (e.g. cycle counts that apply everywhere) is
  a plain node with a one-line "recurring · applies to all nodes" caption — don't
  add decorative loop arrows unless asked.
- Add a small **flow-legend** box (light `CARD` fill, `HAIR` border) decoding
  edge labels (PO/SO/TO/IC, etc.) in an empty region of the canvas.
- Verify each edge in code: endpoints land on node borders, no edge crosses a
  node, no chip overlaps a node. This is the archetype most likely to need a
  second pass — budget for it.
- **Flags** (GAP / need details) render inline in the requirements band, not on
  the map. Reuse the `gap_pill` / `nd_tag` helpers from `process-rail.md` (widen
  them for the full-width band), and add the one-line legend.