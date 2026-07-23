# Archetype: Process Rail (linear flow) — native PowerPoint (.pptx)

Use when the sketch is an ordered sequence: step 1 → step 2 → … → step N.

Build it as a **single editable slide** with `python-pptx`, drawn natively as
shapes. The layout is **deterministic** — compute every position from the step
count and the canvas, so the slide is correct by construction and doesn't depend
on a visual self-critique pass.

## Layout (banded)

A fixed 1600×1000 grid split into horizontal bands. The classic split is
**50% flow / 25% callouts / 25% bottom band**, but relax it when faithful
capture demands more room (e.g. a "detailed" version with dense notes can let
the callouts band grow — disclose the deviation to the user).

```
┌──────────────────────────────────────────────────────────┐
│ HEADER: title · subtitle · accent rule · (scope at right) │
├──────────────────────────────────────────────────────────┤
│ THE PROCESS                                                │
│  (1)─›(2)─›(3)─›(4)─›(5)   numbered rail, chevrons between │
│   │    │    │    ...  accent drop-lines down to cards      │
├──────────────────────────────────────────────────────────┤
│ KEY ACTIVITIES                                             │
│  [card] [card] [card] [card] [card]   one per step         │
├──────────────────────────────────────────────────────────┤
│ BOTTOM BAND: principles OR requirements (or omit)          │
└──────────────────────────────────────────────────────────┘
```

**Signature device**: numbered accent badges on a chevron-connected rail, with a
thin accent drop-line from each step down into its callout card, so each column
reads top-to-bottom. Numbered markers are justified here *because the content is
genuinely a sequence*.

## Color placeholders

Substitute the confirmed client palette for these tokens (hex, no `#`):
`INK` (structure/dark text), `SECONDARY` (sub-heads/connectors),
`ACCENT` (badges/bullets/flags), `CARD` (card fill),
`ATINT` (wash behind flagged items), `INK_SOFT` (muted caption text).

## python-pptx skeleton (validated; adapt freely)

```python
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# --- palette: substitute confirmed client hex values ---
INK="1B2A4A"; SECONDARY="3E6690"; ACCENT="C8322D"; CARD="EDF1F6"
ATINT="F6E3E2"; INK_SOFT="5A6B7C"
def C(h): return RGBColor.from_string(h)

# --- canvas: 1600x1000 design grid -> 13.333in slide (keeps the 1.6 grid) ---
prs = Presentation()
prs.slide_width  = Emu(12192000)
prs.slide_height = Emu(int(12192000/1.6))
EMU_PER_PX = prs.slide_width / 1600
def PX(v): return Emu(int(v*EMU_PER_PX))
slide = prs.slides.add_slide(prs.slide_layouts[6])          # 6 = blank

def box(x,y,w,h,fill=None,line=None,lw=1.0,shape=MSO_SHAPE.RECTANGLE):
    s=slide.shapes.add_shape(shape,PX(x),PX(y),PX(w),PX(h)); s.shadow.inherit=False
    if fill is None: s.fill.background()
    else: s.fill.solid(); s.fill.fore_color.rgb=C(fill)
    if line is None: s.line.fill.background()
    else: s.line.color.rgb=C(line); s.line.width=Pt(lw)
    return s

def label(x,y,w,h,txt,size,bold=True,color=INK,font="Arial Narrow",
          align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE):
    tb=slide.shapes.add_textbox(PX(x),PX(y),PX(w),PX(h)); tf=tb.text_frame
    tf.word_wrap=True; tf.vertical_anchor=anchor
    tf.margin_left=0; tf.margin_right=0; tf.margin_top=0; tf.margin_bottom=0
    p=tf.paragraphs[0]; p.alignment=align
    r=p.add_run(); r.text=txt
    r.font.size=Pt(size); r.font.bold=bold; r.font.name=font; r.font.color.rgb=C(color)
    return tb

def bullets(x,y,w,h,items,size=13,color=INK,marker=ACCENT):
    tb=slide.shapes.add_textbox(PX(x),PX(y),PX(w),PX(h)); tf=tb.text_frame; tf.word_wrap=True
    for i,it in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        m=p.add_run(); m.text="\u25aa "; m.font.size=Pt(size); m.font.color.rgb=C(marker); m.font.name="Arial"
        t=p.add_run(); t.text=it; t.font.size=Pt(size); t.font.color.rgb=C(color); t.font.name="Arial"
    return tb

def gap_pill(x,y,w,text):        # fit/gap flag: solid accent tag on a washed strip
    box(x,y,w,44,fill=ATINT); box(x,y,4,44,fill=ACCENT)
    box(x+9,y+7,40,15,fill=ACCENT); label(x+9,y+7,40,15,"GAP",9,color="FFFFFF")
    label(x+9,y+23,w-16,16,text,10,bold=False,color=INK,font="Arial",align=PP_ALIGN.LEFT)

def nd_tag(x,y,text):            # open-item flag: hollow "need details" tag + note
    box(x,y,86,20,fill=INK,line=SECONDARY,lw=1); label(x,y,86,20,"need details",9,color="9FC0E6")
    label(x+92,y,150,20,text,10,bold=False,color=INK_SOFT,font="Arial",align=PP_ALIGN.LEFT)
# Use ONLY where the user confirms them: gap_pill(...) inside the relevant card
# (below its bullets), nd_tag(...) for an undecided item. Add a one-line legend.

# ---- HEADER ----
label(40,20,1200,54,"‹TITLE›",44,color=INK,align=PP_ALIGN.LEFT)
label(40,74,1200,20,"‹SUBTITLE›",13,bold=False,color=INK_SOFT,font="Arial",align=PP_ALIGN.LEFT)
box(40,96,1520,4,fill=ACCENT)                               # accent rule
label(40,116,1520,16,"THE PROCESS",12,color=SECONDARY,align=PP_ALIGN.LEFT)

# ---- RAIL (deterministic columns) ----
steps=[("‹STEP 1›",["‹activity›","‹activity›"]), ("‹STEP 2›",["…"])]   # one tuple per step
N=len(steps); PADL=40; GUT=16; INNER=1600-2*PADL
col=(INNER-(N-1)*GUT)/N                                      # even column width
rail_y=150; badge=54; title_y=rail_y+64; title_h=64; card_y=520; card_h=250
for i,(ttl,items) in enumerate(steps):
    x=PADL+i*(col+GUT); cx=x+col/2
    box(cx-badge/2,rail_y,badge,badge,fill=ACCENT,shape=MSO_SHAPE.OVAL)          # numbered badge
    label(cx-badge/2,rail_y,badge,badge,str(i+1),28,color="FFFFFF")
    box(x,title_y,col,title_h,fill=INK)                                         # dark title box
    label(x,title_y,col,title_h,ttl,18,color="FFFFFF")
    box(cx-1,title_y+title_h,2,card_y-(title_y+title_h),fill=ACCENT)            # drop-line
    if i<N-1:
        box(x+col+2,rail_y+14,GUT-4,26,fill=SECONDARY,shape=MSO_SHAPE.CHEVRON)  # chevron connector
    box(x,card_y,col,card_h,fill=CARD)                                          # callout card
    box(x,card_y,col,4,fill=SECONDARY)                                          # card top accent
    bullets(x+14,card_y+14,col-28,card_h-28,items)

# ---- BOTTOM BAND (principles or requirements; omit if nothing) ----
by=card_y+card_h+20
box(0,by,1600,1000-by,fill=INK)
label(PADL,by+20,600,16,"‹BAND LABEL›",12,color="8FB0D6",align=PP_ALIGN.LEFT)

prs.save("infographic-v1.pptx")   # v2, v3, ... on each revision — never reuse a name
```

## Build tips
- **Compute, don't place by hand.** Column width = `(1520 − (N−1)×16) / N`; keep
  one badge, one title box, and one card per step so drop-lines land dead-center
  on their cards. Verify no two shapes overlap before saving.
- Text sits in overlay textboxes here for simple centering; for a tighter
  editable slide you can instead write into each shape's own `text_frame`.
- A **cross-cutting note** (something true of every step, e.g. a security model)
  reads well as a thin full-width band between the rail and the cards, or as a
  right-aligned header note.
- **Executive vs. detailed**: exec = 2–3 short callouts per step; detailed =
  every margin note, with sub-heads and nested bullets. Keep the rail identical
  between the two so they're visibly a pair.
- Use the accent **GAP** pill and hollow **need-details** tag only where the user
  confirms them; add the one-line legend.