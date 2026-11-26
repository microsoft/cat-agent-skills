#!/usr/bin/env python3
"""Fill the Work IQ slide from ONE person's workiq_config.json, deterministically.

Every text on slide 1 is either computed from the config or one of a small fixed set of static labels.
A residue guard refuses to write the deck if anything else is left on slide 1 or 2, in the speaker
notes or anywhere else in the file (for example text from whoever filled the template before).

Usage:
  python fill_slide.py --config workiq_config.json --discovery discovery.json --out "Work IQ Sphere Slide.pptx"
      [--template "../references/Work IQ Sphere Slide Reference.pptx"] [--target "<relative link>"] [--internal-names]

  --template        the shipped reference, or ANY deck this script wrote (every output works as a template)
  --target          relative link written into every hyperlink that points at an .html file. Default:
                    "Work%20IQ%20Sphere%20(customer-safe).html", or "Work%20IQ%20Sphere.html" with --internal-names
  --internal-names  real names instead of safe aliases (presenting internally only; never send it out)

Idempotent: slots a config does not need (portal pills, the label and dots of an empty class, surplus dots, the
outputs block, the files row) are hidden and emptied, never deleted, and font sizes and the Business data card
layout go back to the reference on every fill, so any deck this script writes can be the template of the next fill
without drifting. A template with fewer slots is repaired first: pills are cloned downward by the pill pitch, and a
missing class label, dot class, outputs block or files row is rebuilt at its reference position.

Files (version 1.6): when signals.files exists (from count_signals.py --files), the Business data card shows a fourth
row, "files I worked on" (OneDrive and SharePoint), and the total includes signals.files.worked_on. Without it the
row is hidden and the card, total, source line and notes are exactly as before.

Text never goes below 9pt: it shrinks one step at most, then names are shortened with "..." at a word boundary,
sentences are cut at a sentence or clause boundary and the title and subtitle at a clause boundary, never mid-word.
The Memory line is text.slideMemory, or the first memory callout that fits whole.

Window and focus (version 1.7): a day-by-day window (the last 7 days) says "days" wherever the slide talks about time,
including the Memory pillar ("Recalls what matters across days."). A focus (meta.choices.focus) is named by the title
(its {token} in the headline), the subtitle ("<window>, focused on <name>: <n> of my <total> signals"), first in its
class label with "(focus)", in the source line (matched by name, domain and keywords, so direction rather than a census)
and in the speaker notes with its counts. Customer-safe slides show its safe alias, like every name.

Views (version 1.8): the sphere switches between the last 7 days, the last month and the last three months; the slide
stays one slide and shows the three-month numbers, and its subtitle names that window ("The last 3 months (20 Jul to
21 Oct 2026), built automatically ..."). Count placeholders in the config text ({#...}) are filled for the three months
from the discovery.json, exactly as build_workiq.py fills them.

Customer-safe by default: safe aliases ({entity_id} tokens resolve to them in every text), internal
entities/questions/outputs skipped, and the build stops if a real customer, person or escalation name would
appear in the slide text.
Exit codes: 0 = written, one JSON status line printed; 2 = "ERROR: ..." printed, nothing written.

Optional tools for another deck (version 1.8.2: these were add_sphere_link.py and add_official_slide.py):
  python fill_slide.py --add-sphere-link --in deck.pptx --out deck_linked.pptx [--slide 1]
      [--target "Work%20IQ%20Sphere.html"] [--box x,y,w,h EMU] [--html-name "Work IQ Sphere.html"]
      Adds a transparent click area over the sphere (the largest oval unless --box is given), an "Explore in 3D"
      button, hyperlinks with a screen tip and a speaker-notes line. For a customer deck pass
      --target "Work%20IQ%20Sphere%20(customer-safe).html" (the default links to the presenting file).
  python fill_slide.py --add-official-slide --in deck.pptx --out deck_out.pptx
      [--image ../templates/official_workiq_slide.jpg] [--button-box x,y,w,h inches] [--hide-internal]
      Adds Microsoft's official Work IQ slide as a hidden pop-up slide 2 with a "Microsoft's Work IQ slide" button on
      slide 1 and a "Back to my Work IQ" button; --hide-internal also hides any slide carrying
      "INTERNAL: do not show customers".
"""
import argparse, copy, html, json, math, os, random, re, sys, time, unicodedata, zipfile
from urllib.parse import quote, unquote

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.normpath(os.path.join(HERE, '..', 'references', 'Work IQ Sphere Slide Reference.pptx'))
SAFE_TARGET = 'Work%20IQ%20Sphere%20(customer-safe).html'
INTERNAL_TARGET = 'Work%20IQ%20Sphere.html'
EMU_IN = 914400
SEED = 20261021
MAX_PORTALS = 4
PILL_PITCH = 330000  # EMU between pill tops in the reference layout

CLASSES = ['customer', 'product', 'programme', 'theme', 'uat', 'asset', 'person']
CLASS_LABEL = {'customer': 'Customers', 'product': 'Products', 'programme': 'Programmes', 'theme': 'Themes and concerns',
               'uat': 'Escalations', 'asset': 'Assets and agents', 'person': 'People'}
N_EXAMPLES = {'customer': 3, 'uat': 1}
DOT_STYLE = {'customer': ('0078D4', 'ellipse'), 'product': ('00BCF2', 'ellipse'), 'programme': ('008575', 'ellipse'),
             'theme': ('8661C5', 'ellipse'), 'uat': ('D13438', 'diamond'), 'asset': ('C19C00', 'roundRect'),
             'person': ('5C2D91', 'ellipse')}
DOT_CLASS = {v: k for k, v in DOT_STYLE.items()}
sys.path.insert(0, HERE)
from wiq_data import DEFAULT_PORTALS
SPHERE_FALLBACK = (4.79, 1.60, 3.11, 3.11)
HUB_FALLBACK = (5.74, 2.55, 1.20, 1.20)

# Reference layout (EMU) for slots an older deck may have lost.
# class label: box, alignment, heading colour, examples bold, examples colour
REF_LABEL = {'customer': ((2880000, 1240000, 1720000, 660000), 'r', '0078D4', True, '424242'),
             'person': ((2880000, 3250000, 1520000, 540000), 'r', '5C2D91', False, '605E5C'),
             'asset': ((2880000, 3900000, 1800000, 540000), 'r', '8A6D00', False, '605E5C'),
             'product': ((6900000, 1240000, 2400000, 540000), 'l', '0078A8', False, '605E5C'),
             'programme': ((7330000, 1950000, 1980000, 540000), 'l', '008575', False, '605E5C'),
             'theme': ((7330000, 3250000, 1980000, 540000), 'l', '8661C5', False, '605E5C'),
             'uat': ((7000000, 3880000, 2000000, 400000), 'l', 'C50F1F', False, '605E5C')}
REF_CLUSTER = {'customer': (4589536, 1737203, 5648026, 2801698), 'product': (6004924, 1876027, 6617810, 2350022),
               'programme': (6425310, 2383301, 6994140, 2828846), 'theme': (6405225, 2970799, 6915238, 3610810),
               'uat': (5791478, 3196848, 6704806, 4161674), 'asset': (5016204, 3360140, 5546072, 3915056),
               'person': (4630486, 2862147, 5205934, 3491533)}
REF_DOT = 131673
REF_SMALL_DOT = 117043  # dots added for extra (tail) entities are no bigger than this
REF_SPHERE = (4380000, 1460000, 2840000, 2840000)
# (slot, donor shape it is rebuilt from, box)
REF_OUTPUTS = [('WIQ outputs divider', 'WIQ agents divider', (9521440, 3150000, 2041920, 9525)),
               ('WIQ static outputs heading', 'WIQ static agents heading', (9430000, 3200000, 2224800, 300000)),
               ('WIQ outputs', 'WIQ portal 1 text', (9430000, 3500000, 2224800, 965992))]
OUTPUTS_HEADING = 'What it produced for me'
FILES_LABEL, FILES_WHERE = 'files I worked on', 'OneDrive and SharePoint'
# Font size every fill starts from, whatever an earlier fill shrank it to.
BASE_SIZE = {'WIQ title': 28, 'WIQ subtitle': 14, 'WIQ emails': 26, 'WIQ events': 26, 'WIQ chats': 26, 'WIQ files': 26,
             'WIQ total': 16, 'WIQ outputs': 11, 'WIQ context proof': 11, 'WIQ memory proof': 11, 'WIQ skills proof': 11,
             'WIQ source': 9}
NUMBERS = ['WIQ emails', 'WIQ events', 'WIQ chats', 'WIQ files']
FOUR_ROW_NUMBER_SIZE = 24  # the big numbers when the files row is shown, so four rows fit the card

# Business data card layout, (x, y, w, h) in EMU from the card's top-left corner, set on every fill.
# Three rows (no files): the v1.5 positions, except that the chats label sits on one line like the other labels and
# the total and the uploads chip moved up so the chip ends inside the card. Four rows (files): 24pt numbers.
# Both keep at least 0.03 in between the glyphs of neighbouring lines in PowerPoint (Segoe UI) and LibreOffice.
CARD_ORIGIN = (457200, 1230000)
LABEL_W = 2230856  # labels run to the card's right edge (right inset 0) so "Teams chats (group and 1:1)" fits on one line
CARD_LAYOUT = {
    False: {'WIQ static business data': (110000, 70000, 2130000, 380000),
            'WIQ business divider 1': (201440, 480000, 1947120, 9525),
            'WIQ emails': (110000, 530000, 2130000, 579090),
            'WIQ static emails label': (110000, 920000, 2130000, 260000),
            'WIQ events': (110000, 1180000, 2130000, 547270),
            'WIQ static events label': (110000, 1570000, 2130000, 260000),
            'WIQ chats': (110000, 1830000, 2130000, 515450),
            'WIQ static chats label': (110000, 2197725, LABEL_W, 260000),
            'WIQ files': (110000, 1886824, 2130000, 420624),
            'WIQ static files label': (110000, 2194794, LABEL_W, 237744),
            'WIQ static files where': (110000, 2352253, LABEL_W, 201168),
            'WIQ business divider 2': (201440, 2506000, 1947120, 9525),
            'WIQ total': (110000, 2529096, 2130000, 292608),
            'WIQ static uploads chip': (201440, 2848224, 2046835, 347472)},
    True: {'WIQ static business data': (110000, 70000, 2130000, 380000),
           'WIQ business divider 1': (201440, 480000, 1947120, 9525),
           'WIQ emails': (110000, 468681, 2130000, 420624),
           'WIQ static emails label': (110000, 776651, 2130000, 237744),
           'WIQ events': (110000, 938225, 2130000, 420624),
           'WIQ static events label': (110000, 1246195, 2130000, 237744),
           'WIQ chats': (110000, 1407770, 2130000, 420624),
           'WIQ static chats label': (110000, 1710893, LABEL_W, 237744),
           'WIQ files': (110000, 1886824, 2130000, 420624),
           'WIQ static files label': (110000, 2194794, LABEL_W, 237744),
           'WIQ static files where': (110000, 2352253, LABEL_W, 201168),
           'WIQ business divider 2': (201440, 2573904, 1947120, 9525),
           'WIQ total': (110000, 2583048, 2130000, 292608),
           'WIQ static uploads chip': (201440, 2884800, 2046835, 310896)},
}
NO_RIGHT_INSET = ('WIQ static chats label', 'WIQ static files label', 'WIQ static files where')
# Pillar definitions and proof lines start at the top of their boxes, so the three pillars line up.
TOP_ANCHORED = ['WIQ static %s def' % p for p in ('context', 'memory', 'skills')] + ['WIQ %s proof' % p for p in ('context', 'memory', 'skills')]

# The only texts allowed on slides 1 and 2 that do not come from the config.
STATIC_TEXT = [
    'Business data', 'emails', 'calendar events', 'Teams chats (group and 1:1)', '0 things tagged or uploaded',
    FILES_LABEL, FILES_WHERE,
    'My', 'Work IQ', 'Copilot and agents', 'What it produced for me', 'Context', 'Memory', 'Skills',
    'Connects information, people and business context.', 'Recalls what matters across weeks.',
    'Recalls what matters across days.',
    'Turns understanding into outcomes.', "Why it's different:", 'Built from work I already do',
    'Respects my permissions and sensitivity labels', 'One foundation for Copilot and agents',
    '\u25B6  Explore in 3D', "\u25B6  Microsoft's Work IQ slide", '\u25C0  Back to my Work IQ',
    'Explore in 3D', "Microsoft's Work IQ slide", 'Back to my Work IQ',
]
STATIC_ALT = ["Microsoft's official Work IQ slide", 'official_workiq_slide.jpg']
# The Memory pillar's definition follows the window's columns (version 1.7: the last 7 days are shown day by day).
MEMORY_DEF = {'week': 'Recalls what matters across weeks.', 'day': 'Recalls what matters across days.'}
TIP_SPHERE, TIP_OFFICIAL, TIP_BACK = 'Opens the interactive Work IQ sphere', "Show Microsoft's official Work IQ slide", 'Back to my Work IQ'
STATIC_TIPS = [TIP_SPHERE, TIP_OFFICIAL, TIP_BACK]

TEXT_SHAPES = (['WIQ title', 'WIQ subtitle'] + NUMBERS + ['WIQ total']
               + ['WIQ cls ' + c for c in CLASSES] + ['WIQ portal %d text' % i for i in range(1, MAX_PORTALS + 1)]
               + ['WIQ outputs', 'WIQ context proof', 'WIQ memory proof', 'WIQ skills proof', 'WIQ source'])
SINGLE_SHAPES = (TEXT_SHAPES + ['WIQ portal %d %s' % (i, part) for i in range(1, MAX_PORTALS + 1) for part in ('bg', 'dot')]
                 + ['WIQ static outputs heading', 'WIQ outputs divider', 'WIQ static files label', 'WIQ static files where'])
PILL_RE = re.compile(r'WIQ portal (\d+) (bg|dot|text)')
BUTTONS = ("Microsoft's Work IQ slide button", 'Explore in 3D button')
SHRINK_TOGETHER = [['WIQ portal %d text' % i for i in range(1, MAX_PORTALS + 1)], NUMBERS]
PROPER_FIRST_WORDS = {'I', 'Microsoft', 'Copilot', 'Work', 'Teams', 'Outlook', 'SharePoint', 'OneDrive', 'Azure', 'Dynamics',
                      'Power', 'Viva', 'Windows', 'Excel', 'Word', 'PowerPoint', 'Loop', 'Fabric', 'Entra', 'Purview',
                      'GitHub', 'LinkedIn', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                      'September', 'October', 'November', 'December', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                      'Friday', 'Saturday', 'Sunday'}

# --- text measurement: DejaVu Sans advance widths (the font LibreOffice substitutes for Segoe UI, and wider than
# Segoe UI), so text that fits here fits in PowerPoint and in a LibreOffice preview. Line height uses Segoe UI's
# taller 1.33 em. Both choices err towards shrinking or truncating rather than overflowing.
UPM = 2048
_W_REG = [int(v) for v in (
    '651,821,942,1716,1303,1946,1597,563,799,799,1024,1716,651,739,651,690,1303,1303,1303,1303,1303,1303,1303,1303,'
    '1303,1303,690,690,1716,1716,1716,1087,2048,1401,1405,1430,1577,1294,1178,1587,1540,604,604,1343,1141,1767,1532,'
    '1612,1235,1612,1423,1300,1251,1499,1401,2025,1403,1251,1403,799,690,799,1716,1024,1024,1255,1300,1126,1300,1260,'
    '721,1300,1298,569,569,1186,569,1995,1298,1253,1300,1300,842,1067,803,1298,1212,1675,1212,1212,1075,1303,690,'
    '1303,1716').split(',')]
_W_BOLD = [int(v) for v in (
    '713,934,1067,1716,1425,2052,1786,627,936,936,1071,1716,778,850,778,748,1425,1425,1425,1425,1425,1425,1425,1425,'
    '1425,1425,819,819,1716,1716,1716,1188,2048,1585,1561,1503,1700,1399,1399,1681,1714,762,762,1587,1305,2038,1714,'
    '1741,1501,1741,1577,1475,1397,1663,1585,2259,1579,1483,1485,936,748,936,1716,1024,1024,1382,1466,1214,1466,1389,'
    '891,1466,1458,702,702,1362,702,2134,1458,1407,1466,1466,1010,1219,979,1458,1335,1892,1321,1335,1192,1458,748,'
    '1458,1716').split(',')]
_W_EXTRA = {'\u2019': (651, 778), '\u2018': (651, 778), '\u201c': (1061, 1346), '\u201d': (1061, 1346),
            '\u2022': (1208, 1309), '\u25b6': (1575, 1575), '\u25c0': (1575, 1575), '\u2026': (2048, 2048),
            '\u00b7': (651, 778), '\u00a3': (1303, 1425), '\u20ac': (1303, 1425), '\u00d7': (1716, 1716)}
SAFETY = 1.02
LINE = 1.33
SIZES = [8, 9, 10, 10.5, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 44, 48, 54, 60, 66, 72]
MIN_SIZE = 9  # style guide minimum
ELLIPSIS = '...'
END_STRIP = ' ,;:.([{/&+-'


class FillError(Exception):
    pass


def fail(msg):
    raise FillError(msg)


# ----------------------------------------------------------------------------------------------- text helpers
def norm(s):
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(s))
    return re.sub(r'\s+', ' ', s.replace('\u00a0', ' ')).strip()


def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]*>', '', str(s)))


def fmt(n):
    return '{:,}'.format(n)


def is_whole(x):
    """A count: a non-negative whole number (JSON may also hold true, NaN or Infinity, which are not)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0 and x == int(x)


def plural(n, one, many):
    return '%s %s' % (fmt(n), one if n == 1 else many)


def char_units(ch, bold):
    o = ord(ch)
    if 32 <= o < 127:
        return (_W_BOLD if bold else _W_REG)[o - 32]
    if o == 0xA0:
        return char_units(' ', bold)
    if ch in _W_EXTRA:
        return _W_EXTRA[ch][1 if bold else 0]
    if unicodedata.category(ch).startswith('M'):
        return 0
    base = unicodedata.normalize('NFKD', ch)[:1]
    if base and base != ch and 32 <= ord(base) < 127:
        return char_units(base, bold)
    if unicodedata.east_asian_width(ch) in ('W', 'F'):
        return UPM
    return int(UPM * 0.7)


def text_width(s, size, bold):
    return sum(char_units(c, bold) for c in s) / UPM * size / 72.0 * SAFETY


def wrap(s, size, bold, width):
    """Greedy word wrap as PowerPoint and LibreOffice do it; a word wider than the line is split."""
    lines, cur = [], ''
    for word in s.split(' '):
        cand = word if not cur else cur + ' ' + word
        if text_width(cand, size, bold) <= width:
            cur = cand
            continue
        if cur:
            lines.append(cur)
        cur = word
        while len(cur) > 1 and text_width(cur, size, bold) > width:
            k = len(cur) - 1
            while k > 1 and text_width(cur[:k], size, bold) > width:
                k -= 1
            lines.append(cur[:k])
            cur = cur[k:]
    lines.append(cur)
    return lines


def _balanced(t):
    while t.count('(') > t.count(')'):
        t = t[:t.rfind('(')].rstrip(END_STRIP)
    return t


FOCUS_MARK = ' (focus)'


def truncate(s, ok):
    """Longest word-boundary prefix + '...' that passes ok(); mid-word only when the first word alone is too wide.
    The focus keeps its " (focus)" mark: only its name is shortened."""
    if ok(s):
        return s
    if s.endswith(FOCUS_MARK) and len(s) > len(FOCUS_MARK):
        return truncate(s[:-len(FOCUS_MARK)], lambda t: ok(t + FOCUS_MARK)) + FOCUS_MARK
    words = s.split(' ')
    for k in range(len(words) - 1, 0, -1):
        cand = _balanced(' '.join(words[:k]).rstrip(END_STRIP))
        if cand and ok(cand + ELLIPSIS):
            return cand + ELLIPSIS
    for k in range(len(words[0]) - 1, 0, -1):
        if ok(words[0][:k] + ELLIPSIS):
            return words[0][:k] + ELLIPSIS
    return ELLIPSIS


def cut_at_boundary(s, ok):
    """Longest prefix ending at a sentence or clause boundary (outside brackets) that passes ok(), ended with a full
    stop; falls back to a word-boundary cut with '...'. Never cuts a word."""
    if ok(s):
        return s
    cuts, depth = set(), 0
    for i, ch in enumerate(s):
        nxt = s[i + 1] if i + 1 < len(s) else ' '
        if ch == '(':
            if depth == 0 and i > 0 and s[i - 1] == ' ':
                cuts.add(i)
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        elif depth == 0 and ch in '.!?;:,' and nxt == ' ':
            cuts.add(i + 1 if ch in '.!?' else i)
    for pos in sorted(cuts, reverse=True):
        cand = s[:pos].rstrip(' ,;:-')
        if not cand:
            continue
        if cand[-1] not in '.!?':
            cand += '.'
        if ok(cand):
            return cand
    return truncate(s, ok)


def cut_heading(s, ok, min_share=0.0):
    """A title or subtitle that does not fit: the longest prefix ending at a clause boundary (outside brackets) that
    passes ok(), with no end punctuation and keeping at least min_share of the characters and more than the
    "My Work IQ" lead-in; else a word-boundary cut with '...'. Never cuts a word."""
    if ok(s):
        return s
    cuts, depth = set(), 0
    for i, ch in enumerate(s):
        nxt = s[i + 1] if i + 1 < len(s) else ' '
        if ch == '(':
            if depth == 0 and i > 0 and s[i - 1] == ' ':
                cuts.add(i)
            depth += 1
        elif ch == ')':
            depth = max(0, depth - 1)
        elif depth == 0 and ch in '.!?;:,' and nxt == ' ':
            cuts.add(i)
    lead = len('My Work IQ:') if s.startswith('My Work IQ:') else 0
    for pos in sorted(cuts, reverse=True):
        cand = _balanced(s[:pos].rstrip(END_STRIP))
        if len(cand) > lead and len(cand) >= min_share * len(s) and len(cand.split()) >= 3 and ok(cand):
            return cand
    return truncate(s, ok)


def smaller(size, steps=1):
    for _ in range(steps):
        lower = [s for s in SIZES if s < size - 0.01 and s >= MIN_SIZE]
        if not lower:
            break
        size = lower[-1]
    return size


# ---------------------------------------------------------------------------------------------- XML helpers
def para_text(p):
    return ''.join(t.text or '' for t in p.iter(qn('a:t')))


def is_spacer(p):
    """The tiny non-breaking-space paragraphs some shapes end with (not text, not a slot)."""
    txt = para_text(p)
    if norm(txt):
        return False
    sizes = [int(r.get('sz')) for r in p.iter(qn('a:rPr')) if (r.get('sz') or '').isdigit()]
    return txt != '' or bool(sizes and max(sizes) <= 200)


def slot_paras(txBody):
    """Paragraphs that hold (or held, before a slot was emptied) text, so their formatting survives emptying."""
    return [p for p in txBody.findall(qn('a:p'))
            if (p.find(qn('a:r')) is not None or p.find(qn('a:fld')) is not None) and not is_spacer(p)]


def run_style(p):
    r = p.find(qn('a:r'))
    if r is None:
        r = p.find(qn('a:fld'))
    rPr = r.find(qn('a:rPr')) if r is not None else None
    if rPr is None:
        rPr = p.find(qn('a:endParaRPr'))
    size, bold = 18.0, False
    if rPr is not None:
        if rPr.get('sz'):
            size = int(rPr.get('sz')) / 100.0
        latin = rPr.find(qn('a:latin'))
        bold = rPr.get('b') in ('1', 'true') or (latin is not None and 'Bold' in (latin.get('typeface') or ''))
    return size, bold


def set_para_text(p, text):
    for el in p.findall(qn('a:br')):
        p.remove(el)
    for fld in p.findall(qn('a:fld')):  # a field becomes a plain run with the same formatting
        r = etree.Element(qn('a:r'))
        if fld.find(qn('a:rPr')) is not None:
            r.append(copy.deepcopy(fld.find(qn('a:rPr'))))
        etree.SubElement(r, qn('a:t'))
        fld.addprevious(r)
        p.remove(fld)
    runs = p.findall(qn('a:r'))
    if not runs:
        r = etree.SubElement(p, qn('a:r'))
        end = p.find(qn('a:endParaRPr'))
        rPr = copy.deepcopy(end) if end is not None else etree.Element(qn('a:rPr'))
        rPr.tag = qn('a:rPr')
        r.append(rPr)
        etree.SubElement(r, qn('a:t'))
        if end is not None:
            end.addprevious(r)
        runs = [r]
    for extra in runs[1:]:
        p.remove(extra)
    t = runs[0].find(qn('a:t'))
    if t is None:
        t = etree.SubElement(runs[0], qn('a:t'))
    t.text = text or None  # an empty run always serialises as <a:t/>, so outputs do not depend on their history


def set_paragraphs(sp_el, texts):
    """Write texts run by run: the first run of each paragraph keeps its font, colour and bold; extra runs go;
    paragraphs are cloned from the last one (or deleted) to match. Spacer paragraphs are kept."""
    txBody = sp_el.find(qn('p:txBody'))
    paras = slot_paras(txBody)
    if not paras:
        first = txBody.find(qn('a:p'))
        if first is None:
            first = etree.SubElement(txBody, qn('a:p'))
        paras = [first]
    out = []
    for i, text in enumerate(texts):
        if i < len(paras):
            p = paras[i]
        else:
            p = copy.deepcopy(out[-1])
            out[-1].addnext(p)
        set_para_text(p, text)
        out.append(p)
    for p in paras[len(texts):]:
        txBody.remove(p)
    return out


def first_rPr(p):
    r = p.find(qn('a:r'))
    rPr = r.find(qn('a:rPr'))
    if rPr is None:
        rPr = etree.Element(qn('a:rPr'))
        r.insert(0, rPr)
    return rPr


def set_run_attr(p, attr, value):
    rPr = first_rPr(p)
    if value is None:
        rPr.attrib.pop(attr, None)
    else:
        rPr.set(attr, value)


def set_fill(parent, hex_colour):
    """Solid fill of a run (rPr) or shape (spPr), keeping the element order the schema expects."""
    sf = parent.find(qn('a:solidFill'))
    if sf is None:
        sf = etree.Element(qn('a:solidFill'))
        anchor = parent.find(qn('a:ln')) if parent.tag == qn('a:rPr') else parent.find(qn('a:prstGeom'))
        if anchor is not None:
            anchor.addnext(sf)
        else:
            parent.insert(0, sf)
    for child in list(sf):
        sf.remove(child)
    etree.SubElement(sf, qn('a:srgbClr')).set('val', hex_colour)


def box_in(sh):
    return ((sh.left or 0) / EMU_IN, (sh.top or 0) / EMU_IN, (sh.width or 0) / EMU_IN, (sh.height or 0) / EMU_IN)


def insets(sp_el):
    bp = sp_el.find(qn('p:txBody')).find(qn('a:bodyPr'))
    g = lambda k, d: int(bp.get(k)) / EMU_IN if bp is not None and bp.get(k) is not None else d
    return g('lIns', 0.1), g('tIns', 0.05), g('rIns', 0.1), g('bIns', 0.05), (bp.get('anchor') if bp is not None else None) or 't'


def geom_fill(el):
    spPr = el.find(qn('p:spPr'))
    if spPr is None:
        return None, None
    g = spPr.find(qn('a:prstGeom'))
    f = spPr.find(qn('a:solidFill'))
    c = f.find(qn('a:srgbClr')) if f is not None else None
    return (g.get('prst') if g is not None else None), (c.get('val').upper() if c is not None else None)


def cnv_of(el):
    return el.find('.//' + qn('p:cNvPr'))


def is_hidden(el):
    return (cnv_of(el).get('hidden') or '').lower() in ('1', 'true')


def set_hidden(el, hidden):
    cnv = cnv_of(el)
    if hidden:
        cnv.set('hidden', '1')
    else:
        cnv.attrib.pop('hidden', None)


def hide_slot(el):
    """Hidden and emptied, but kept (with its paragraphs and formatting) for the next fill."""
    set_hidden(el, True)
    for t in el.iter(qn('a:t')):
        if norm(t.text or ''):
            t.text = None


def zpos(el):
    return el.getparent().index(el)


def all_ids(slide):
    return [int(e.get('id')) for e in slide._element.iter(qn('p:cNvPr')) if (e.get('id') or '').isdigit()]


class Ids:
    def __init__(self, slide):
        self.n = max(all_ids(slide)) + 1

    def next(self):
        self.n += 1
        return self.n - 1


def clone_shape(src_el, name, new_id, after=None, box=None, dy=0):
    el = copy.deepcopy(src_el)
    cnv = cnv_of(el)
    cnv.set('id', str(new_id))
    cnv.set('name', name)
    for ext in cnv.findall(qn('a:extLst')):
        cnv.remove(ext)
    xfrm = el.find(qn('p:spPr')).find(qn('a:xfrm'))
    off, ext = xfrm.find(qn('a:off')), xfrm.find(qn('a:ext'))
    if box is not None:
        off.set('x', str(int(box[0])))
        off.set('y', str(int(box[1])))
        ext.set('cx', str(int(box[2])))
        ext.set('cy', str(int(box[3])))
    if dy:
        off.set('y', str(int(off.get('y')) + int(dy)))
    (after if after is not None else src_el).addnext(el)
    return el


def shapes_named(slide):
    d = {}
    for sh in slide.shapes:
        d.setdefault(sh.name, []).append(sh)
    return d


# ----------------------------------------------------------------------------------------------- content
class Content:
    """Everything the slide says, computed from the config only."""

    def __init__(self, cfg, internal_names, target):
        self.cfg, self.internal_names, self.warnings = cfg, internal_names, []
        sig = cfg.get('signals') if isinstance(cfg.get('signals'), dict) else {}
        smeta = sig.get('meta') if isinstance(sig.get('meta'), dict) else {}
        self.unit = 'day' if smeta.get('unit') == 'day' else 'week'   # version 1.7: the week is counted day by day
        self.one, self.many = ('day', 'days') if self.unit == 'day' else ('week', 'weeks')
        self.validate()
        text = cfg.get('text') or {}
        self.ents = {e['id']: e for e in cfg['entities'] if isinstance(e, dict) and 'id' in e}
        vis = [e for e in cfg['entities'] if e['cls'] != 'hub' and not e.get('internal')]
        self.visible = vis

        vol = cfg['signals']['vol']
        self.emails = sum(vol['mail_in']) + sum(vol['mail_out'])
        self.events = sum(vol['meet'])
        self.chats = cfg['signals'].get('chats')
        if self.chats is None:
            self.chats = 0
            self.warnings.append('signals.chats missing: Teams chats show 0')
        files = cfg['signals'].get('files')  # validated: None, or a dict with a whole worked_on
        self.files = files['worked_on'] if files is not None else None
        self.files_edited = files.get('edited') if files is not None else None
        self.total = self.emails + self.events + self.chats + (self.files or 0)
        self.focus, self.fcounts, self.focus_type = None, None, None
        f = ((cfg.get('meta') or {}).get('choices') or {}).get('focus') if isinstance((cfg.get('meta') or {}).get('choices'), dict) else None
        fe = self.ents.get(f.get('id')) if isinstance(f, dict) and f.get('type') in ('customer', 'programme', 'theme') else None
        sf = cfg['signals'].get('focus') if isinstance(cfg['signals'].get('focus'), dict) else None
        if fe is not None and fe['cls'] != 'hub' and not fe.get('internal'):
            self.focus, self.focus_type = fe, f['type']
            if sf and isinstance(sf.get('vol'), dict):
                fv = sf['vol']
                tot = lambda k: sum(int(x) for x in fv.get(k) or [] if is_whole(x))
                self.fcounts = {'emails': tot('mail_in') + tot('mail_out'), 'events': tot('meet'), 'chats': tot('chats'),
                                'files': tot('files') if self.files is not None else 0}
                self.fcounts['total'] = sum(self.fcounts.values())

        window = self.r(text.get('windowLabel') or text.get('sparkRange') or '', 'text.windowLabel')
        n_weeks = len(cfg['weeks'])
        choice = (((cfg.get('meta') or {}).get('choices') or {}) if isinstance((cfg.get('meta') or {}).get('choices'), dict) else {}).get('window')
        sub_window = ('The last 3 months (%s)' % window) if choice == 'quarter' and window else window   # version 1.8: names the view
        self.title = self.r(text['slideTitle'], 'text.slideTitle') if text.get('slideTitle') else self.make_title(text)
        if text.get('slideSubtitle'):
            self.subtitle = self.r(text['slideSubtitle'], 'text.slideSubtitle')
        elif self.focus is not None and self.fcounts is not None:
            self.subtitle = '%s, focused on %s: %s of my %s' % (sub_window or 'The last %d %s' % (n_weeks, self.many), self.name(self.focus),
                                                               fmt(self.fcounts['total']), plural(self.total, 'signal', 'signals'))
        else:
            if not window:
                self.warnings.append('text.windowLabel and text.sparkRange missing: subtitle says "The last %d %s"' % (n_weeks, self.many))
            self.subtitle = (sub_window or 'The last %d %s' % (n_weeks, self.many)) + ', built automatically from the work I already do'

        grid = cfg['signals'].get('grid') or {}

        def size(e):  # the size the sphere gives the node (build_workiq template): signal volume, else weight
            sig = e.get('signal')
            try:
                if sig and sig in grid:
                    return 3 + math.sqrt(max(0, sum(grid[sig]))) * 0.5
            except TypeError:
                self.warnings.append('signals.grid.%s is not a list of numbers; %s is ranked by weight' % (sig, e['id']))
            try:
                return 3 + float(e.get('weight') or 0) * 0.8
            except (TypeError, ValueError):
                return 3.0

        self.counts, self.examples = {}, {}
        for c in CLASSES:
            members = [e for e in vis if e['cls'] == c]
            self.counts[c] = len(members)
            ranked = sorted(members, key=lambda e: (e is not self.focus, -size(e)))  # the focus first; config order breaks ties
            self.examples[c] = [self.name(e) + (FOCUS_MARK if e is self.focus else '') for e in ranked[:N_EXAMPLES.get(c, 2)]]

        raw = cfg.get('portals')
        if raw is None:
            names = list(DEFAULT_PORTALS)
        else:
            if not isinstance(raw, list):
                fail('portals must be a list of {"name": ...}')
            names = [self.r(p.get('name', '') if isinstance(p, dict) else p, 'portals') for p in raw]
            names = [n for n in names if n]
        if not names:
            fail('portals must name 1 to 4 things Work IQ powers (or leave "portals" out for the default three)')
        if len(names) > MAX_PORTALS:
            self.warnings.append('%d portals given; the slide shows the first %d' % (len(names), MAX_PORTALS))
        self.portals = names[:MAX_PORTALS]

        outs = [o for o in (cfg.get('outputs') or []) if not o.get('internal')]
        titles = [self.r(strip_tags(o.get('title', '')), 'outputs.title') for o in outs]
        titles = [t for t in titles if t]
        if len(titles) > 1:
            titles = [t for t in titles if t.lower() != 'this visual'] or titles
        self.outputs = titles[:3]
        if not self.outputs:
            self.warnings.append('no customer-safe outputs: the "What it produced for me" block is hidden')

        ids = {e['id'] for e in vis} | {e['id'] for e in cfg['entities'] if e['cls'] == 'hub'}
        rels = [r for r in (cfg.get('relations') or []) if r[0] in ids and r[1] in ids]
        self.n_entities, self.n_types, self.n_relations = len(vis), len({e['cls'] for e in vis}), len(rels)
        self.context = '%s, %s, %s' % (plural(self.n_entities, 'entity', 'entities'), plural(self.n_types, 'type', 'types'),
                                      plural(self.n_relations, 'relationship', 'relationships'))

        self.memory_override = self.r(strip_tags(text['slideMemory']), 'text.slideMemory') if text.get('slideMemory') else None
        self.memory_candidates = [self.r(strip_tags(m.get('text', '')), 'memory[%d].text' % i)
                                  for i, m in enumerate(cfg.get('memory') or []) if not m.get('internal')]
        self.memory_candidates = [m for m in self.memory_candidates if m]
        if not self.memory_override and not self.memory_candidates:
            fail('config needs text.slideMemory or at least one memory item with text (for the Memory proof line)')
        if text.get('slideSkills'):
            self.skills = self.r(strip_tags(text['slideSkills']), 'text.slideSkills')
        else:
            q = next((q for q in (cfg.get('questions') or []) if not q.get('internal') and norm(strip_tags(q.get('grounding', '')))), None)
            if q is None:
                fail('config needs text.slideSkills or a customer-safe question with a grounding line (for the Skills proof line)')
            self.skills = self.r(strip_tags(q['grounding']), 'questions[].grounding')

        owner = self.r(cfg['owner'], 'owner')
        src_window = window or 'the last %d %s' % (n_weeks, self.many)
        if self.files is None:
            sources = 'Outlook mail (junk and duplicate copies removed), calendar and Teams group and 1:1 chats'
        else:
            sources = ('Outlook mail (junk and duplicate copies removed), calendar, Teams group and 1:1 chats, and the files '
                       'I worked on in OneDrive and SharePoint')
        self.fixed_source = sources        # the skill's own fixed wording ("Outlook mail", ...), never a real name
        meta = cfg.get('meta') if isinstance(cfg.get('meta'), dict) else {}
        fictional = False
        if meta.get('sample') == 'fictional':   # version 1.8: the shipped fictional example's slide says so
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import wiq_data
            s_owner = wiq_data.sample_identity()[1]
            fictional = bool(s_owner) and str(meta.get('ownerUpn', '')).strip().lower() == s_owner
        self.source = ("Source: %s's %s, %s. " % (owner, sources, src_window)
                       + ('Fictional sample data. ' if fictional else '')
                       + ('' if internal_names else 'Customer and people names anonymised. ')
                       + (('Focus counts match %s, so they show direction, not a census. '
                           % ('names, mail domains and keywords' if self.focus_type == 'customer' else 'names and keywords'))
                          if self.focus is not None else '')
                       + 'Interactive 3D version available.')

        period = self.r(text['period'], 'text.period') if text.get('period') else '%d %s' % (n_weeks, self.many)
        html_name = os.path.basename(unquote(target).split('#')[0].split('?')[0]) or target
        raw = ('emails, calendar events and chats' if self.files is None else
               'emails, calendar events, chats and the files I worked on in OneDrive and SharePoint')
        self.notes = [
            'Read this left to right. On the left is my own raw work: %s, with nothing tagged or uploaded. Work IQ turns '
            'that into context, memory and skills, shown by the clusters on the sphere and the three pillars along the '
            'bottom. On the right, the same foundation powers Copilot and agents. Every number here is mine, from %s of '
            'real work.' % (raw, period)]
        if self.files is not None:
            if self.files_edited and self.files == 1:
                edited = ' (I edited it)'
            elif self.files_edited and self.files_edited >= self.files:
                edited = ' (I edited all of them)'
            elif self.files_edited:
                edited = ' (I edited %s of them)' % fmt(self.files_edited)
            else:
                edited = ''
            self.notes.append('Files: %s I worked on in OneDrive and SharePoint%s, counted in the %s.'
                              % (plural(self.files, 'file', 'files'), edited, plural(self.total, 'signal', 'signals')))
        self.notes += [
            'Click the sphere or Explore in 3D to open the interactive version (keep %s in the same folder as this deck).' % html_name,
            "Microsoft's Work IQ slide (top right) jumps to Microsoft's official Work IQ slide, which is hidden in the slide "
            'show; Back to my Work IQ returns here.']
        if self.focus is not None and self.fcounts is not None:
            fc = self.fcounts
            self.notes.append('Focus: %s. Of my %s, %s are about it: %s, %s, %s%s. They match by %s, so read them as direction, '
                              'not a census.' % (self.name(self.focus), plural(self.total, 'signal', 'signals'), fmt(fc['total']),
                                                 plural(fc['emails'], 'email', 'emails'), plural(fc['events'], 'calendar event', 'calendar events'),
                                                 plural(fc['chats'], 'Teams chat', 'Teams chats'),
                                                 (', ' + plural(fc['files'], 'file', 'files')) if self.files is not None else '',
                                                 'name, mail domain and keyword' if self.focus_type == 'customer' else 'name and keyword'))
        if internal_names:
            self.notes.append('This deck shows real customer and people names: present it internally only and never send it '
                              'to customers.')

    # -- validation and names
    def validate(self):
        cfg = self.cfg
        for k in ('owner', 'weeks', 'signals', 'entities'):
            if k not in cfg:
                fail('config is missing "%s"' % k)
        if not isinstance(cfg['weeks'], list) or not cfg['weeks']:
            fail('weeks must be a non-empty list of %s labels' % self.one)
        if not isinstance(cfg['owner'], str) or not norm(cfg['owner']):
            fail('owner must be the display name of the person whose work this is')
        if not isinstance(cfg['signals'], dict):
            fail('signals must be an object with vol, chats (and grid)')
        if not isinstance(cfg['entities'], list):
            fail('entities must be a list')
        if cfg.get('text') is not None and not isinstance(cfg['text'], dict):
            fail('text must be an object')
        vol = cfg['signals'].get('vol')
        if not isinstance(vol, dict):
            fail('config is missing signals.vol')
        for k in ('mail_in', 'mail_out', 'meet'):
            v = vol.get(k)
            if not isinstance(v, list) or not all(is_whole(x) for x in v):
                fail('signals.vol.%s must be a list of whole numbers, one per %s' % (k, self.one))
            vol[k] = [int(x) for x in v]
            if len(v) != len(cfg['weeks']):
                self.warnings.append('signals.vol.%s has %d values for %d %s' % (k, len(v), len(cfg['weeks']), self.many))
        whole = is_whole
        ch = cfg['signals'].get('chats')
        if ch is not None and not whole(ch):
            fail('signals.chats must be a whole number')
        if ch is not None:
            cfg['signals']['chats'] = int(ch)
        files = cfg['signals'].get('files')
        if files is not None:
            if not isinstance(files, dict) or not whole(files.get('worked_on')):
                fail('signals.files must be {"worked_on": N, "edited": E, "opened": O, "sites": K} with whole numbers, '
                     'as count_signals.py --files writes it (or leave it out: the slide then has no files row)')
            for k in ('worked_on', 'edited', 'opened', 'sites'):
                if files.get(k) is not None:
                    if not whole(files[k]):
                        fail('signals.files.%s must be a whole number' % k)
                    files[k] = int(files[k])
            if files.get('edited') is not None and files['edited'] > files['worked_on']:
                self.warnings.append('signals.files.edited (%d) is more than worked_on (%d): the notes leave the edited count out'
                                     % (files['edited'], files['worked_on']))
                files['edited'] = None
            if files['worked_on'] == 0:
                self.warnings.append('signals.files.worked_on is 0: the files row shows 0')
            vf = vol.get('files')
            if vf is not None:
                if not isinstance(vf, list) or not all(whole(x) for x in vf):
                    fail('signals.vol.files must be a list of whole numbers, one per %s' % self.one)
                if len(vf) != len(cfg['weeks']):
                    self.warnings.append('signals.vol.files has %d values for %d %s' % (len(vf), len(cfg['weeks']), self.many))
                if sum(vf) != files['worked_on']:
                    self.warnings.append('signals.vol.files adds up to %d but signals.files.worked_on is %d: the slide shows '
                                         'worked_on' % (sum(vf), files['worked_on']))
        elif vol.get('files') is not None:
            self.warnings.append('signals.vol.files without signals.files: files are left out of the slide and the total')
        seen = set()
        for e in cfg['entities']:
            if not isinstance(e, dict) or 'id' not in e or 'cls' not in e:
                fail('every entity needs an id and a cls')
            if e['id'] in seen:
                fail('entity id %s is used twice' % e['id'])
            seen.add(e['id'])
            if e['cls'] not in CLASSES and e['cls'] != 'hub':
                fail('entity %s has unknown cls "%s"' % (e['id'], e['cls']))
            if not norm(e.get('real') or ''):
                fail('entity %s has no "real" name' % e['id'])
        for r in cfg.get('relations') or []:
            if not isinstance(r, list) or len(r) < 2:
                fail('relation %r must be [from, to, verb]' % (r,))
            for x in r[:2]:
                if x not in seen:
                    fail('relation %s refers to unknown entity %s' % (r, x))
        if sum(1 for e in cfg['entities'] if e['cls'] == 'hub') != 1:
            self.warnings.append('expected exactly one hub entity (the owner)')

    def name(self, e, depth=0):
        base = e['real'] if self.internal_names else (e.get('safe') or e['real'])
        return self.r(base, 'name of %s' % e['id'], depth + 1)

    def r(self, s, field, depth=0):
        """Resolve {entity_id} tokens to safe (or, with --internal-names, real) names."""
        def rep(m):
            e = self.ents.get(m.group(1))
            if e is None:
                fail('%s: token {%s} does not match an entity id' % (field, m.group(1)))
            if e.get('internal'):
                fail('%s: token {%s} points at an internal entity; internal content never goes on the slide' % (field, m.group(1)))
            if depth > 2:
                fail('%s: tokens nest too deeply' % field)
            return self.name(e, depth)
        return norm(re.sub(r'\{(\w+)\}', rep, str(s)))

    def make_title(self, text):
        raw = (text.get('headline') or '').strip()
        h = self.r(raw, 'text.headline').rstrip()
        while h.endswith('.'):
            h = h[:-1].rstrip()
        if not h:
            self.warnings.append('text.headline missing: title is just "My Work IQ"')
            return 'My Work IQ'
        first = re.split(r'[\s,:;]', h, 1)[0]
        keep = (first in PROPER_FIRST_WORDS or first.startswith("I'") or any(c.isupper() or c.isdigit() for c in first[1:])
                or raw.startswith('{'))           # a name from a {token} keeps its capital
        return 'My Work IQ: ' + (h if keep else h[0].lower() + h[1:])

    def leak_terms(self):
        """Real names that must not appear on a customer-safe slide."""
        terms = set()
        for e in self.cfg['entities']:
            if e['cls'] == 'hub':
                continue
            real = norm(e['real'])
            if e.get('internal') or (e.get('safe') and norm(e['safe']) != real):
                terms.add(real)
                if e['cls'] == 'uat' or e.get('internal'):
                    terms.update(re.findall(r'\b\d{6}\b', real))
        shown = ' '.join([self.name(e) for e in self.visible]).lower()
        return sorted(t for t in terms if len(t) >= 2 and not re.search(r'(?<![a-z0-9])' + re.escape(t.lower()) + r'(?![a-z0-9])', shown))

    def fields(self, memory):
        f = {'WIQ title': [self.title], 'WIQ subtitle': [self.subtitle], 'WIQ emails': [fmt(self.emails)],
             'WIQ events': [fmt(self.events)], 'WIQ chats': [fmt(self.chats)],
             'WIQ files': [fmt(self.files)] if self.files is not None else None,
             'WIQ total': ['= %s' % plural(self.total, 'signal', 'signals')],
             'WIQ outputs': self.outputs or None, 'WIQ context proof': [self.context], 'WIQ memory proof': [memory],
             'WIQ skills proof': [self.skills], 'WIQ source': [self.source]}
        for c in CLASSES:
            f['WIQ cls ' + c] = (['%s (%s)' % (CLASS_LABEL[c], fmt(self.counts[c]))] + self.examples[c]) if self.counts[c] else None
        for i in range(1, MAX_PORTALS + 1):
            f['WIQ portal %d text' % i] = [self.portals[i - 1]] if i <= len(self.portals) else None
        return f


# ------------------------------------------------------------------------------------------- slot repair
def repair_pills(slide, ids, restored):
    """Older decks may carry fewer pills: clone the last one downward by the pill pitch up to MAX_PORTALS."""
    groups = {}
    for sh in slide.shapes:
        m = PILL_RE.fullmatch(sh.name)
        if m:
            groups.setdefault(int(m.group(1)), {}).setdefault(m.group(2), []).append(sh._element)
    for i, parts in groups.items():
        if any(len(parts.get(p, [])) != 1 for p in ('bg', 'dot', 'text')):
            fail('portal pill %d in the template must have exactly one bg, dot and text shape' % i)
    k = 0
    while k + 1 in groups:
        k += 1
    if k == 0:
        fail('template has no portal pill ("WIQ portal 1 bg", "dot" and "text") to copy')
    if len(groups) != k:
        fail('portal pills in the template must be numbered 1, 2, 3 ... without gaps')
    top = lambda i: int(groups[i]['bg'][0].find(qn('p:spPr')).find(qn('a:xfrm')).find(qn('a:off')).get('y'))
    pitch = top(k) - top(k - 1) if k >= 2 else PILL_PITCH
    pitch = pitch if pitch > 0 else PILL_PITCH
    anchor = max((groups[k][p][0] for p in ('bg', 'dot', 'text')), key=zpos)
    for j in range(k + 1, MAX_PORTALS + 1):
        for part in ('bg', 'dot', 'text'):
            anchor = clone_shape(groups[k][part][0], 'WIQ portal %d %s' % (j, part), ids.next(), after=anchor, dy=pitch * (j - k))
        restored.append('WIQ portal %d' % j)


def restyle_label(el, c):
    _, algn, head, ex_bold, ex_colour = REF_LABEL[c]
    bp = el.find(qn('p:txBody')).find(qn('a:bodyPr'))
    for k in ('lIns', 'rIns'):
        bp.attrib.pop(k, None)
    bp.set('lIns' if algn == 'r' else 'rIns', '18288')
    for i, p in enumerate(slot_paras(el.find(qn('p:txBody')))):
        pPr = p.find(qn('a:pPr'))
        if pPr is None:
            pPr = etree.Element(qn('a:pPr'))
            p.insert(0, pPr)
        pPr.set('algn', algn)
        if p.find(qn('a:r')) is None:
            set_para_text(p, '')
        rPr = first_rPr(p)
        rPr.set('sz', '1000' if i == 0 else '900')
        if i == 0 or ex_bold:
            rPr.set('b', '1')
        else:
            rPr.attrib.pop('b', None)
        set_fill(rPr, head if i == 0 else ex_colour)


def label_align(sh):
    paras = slot_paras(sh._element.find(qn('p:txBody')))
    pPr = paras[0].find(qn('a:pPr')) if paras else None
    return pPr.get('algn') if pPr is not None else None


def repair_labels(slide, ids, restored):
    """A class label an older deck dropped is rebuilt at its reference position from another label."""
    named = shapes_named(slide)
    donors = [named['WIQ cls ' + c][0] for c in CLASSES if named.get('WIQ cls ' + c)]
    if not donors:
        fail('template has no class label ("WIQ cls ...") to copy')
    for c in CLASSES:
        if named.get('WIQ cls ' + c):
            continue
        box, algn = REF_LABEL[c][0], REF_LABEL[c][1]
        donor = next((d for d in donors if label_align(d) == algn), donors[0])
        el = clone_shape(donor._element, 'WIQ cls ' + c, ids.next(), box=box)
        restyle_label(el, c)
        hide_slot(el)
        restored.append('WIQ cls ' + c)


def repair_outputs(slide, ids, restored):
    """The outputs block an older deck dropped is rebuilt at its reference position."""
    for name, donor_name, box in REF_OUTPUTS:
        named = shapes_named(slide)
        if named.get(name):
            continue
        if not named.get(donor_name):
            fail('template has no "%s" and no "%s" to rebuild it from' % (name, donor_name))
        donor = named[donor_name][0]._element
        el = clone_shape(donor, name, ids.next(), after=donor, box=box)
        if name != 'WIQ outputs divider':
            p = slot_paras(el.find(qn('p:txBody')))[0]
            set_para_text(p, OUTPUTS_HEADING if name == 'WIQ static outputs heading' else '')
            rPr = first_rPr(p)
            rPr.set('sz', '1200' if name == 'WIQ static outputs heading' else '1100')
            set_fill(rPr, '0078D4' if name == 'WIQ static outputs heading' else '424242')
        if name == 'WIQ outputs':
            el.find(qn('p:txBody')).find(qn('a:bodyPr')).set('anchor', 't')
            hide_slot(el)
        else:
            set_hidden(el, True)  # static heading and divider keep their look; shown again when there are outputs
        restored.append(name)


def repair_files(slide, ids, restored):
    """Decks from before version 1.6 have no files row: its number slot and two static labels are cloned from the chats
    row (hidden; the card layout places them)."""
    named = shapes_named(slide)
    donor_label = (named.get('WIQ static chats label') or named.get('WIQ static emails label') or [None])[0]
    after = donor_label._element if donor_label is not None else None
    for name, donor_name, text, size, colour in (
            ('WIQ files', 'WIQ chats', None, None, None),
            ('WIQ static files label', None, FILES_LABEL, '1200', '424242'),
            ('WIQ static files where', None, FILES_WHERE, '1000', '605E5C')):
        if named.get(name):
            after = named[name][0]._element
            continue
        donor = named.get(donor_name, [None])[0] if donor_name else donor_label
        if donor is None:
            fail('template has no "%s" to rebuild "%s" from' % (donor_name or 'WIQ static chats label', name))
        el = clone_shape(donor._element, name, ids.next(), after=after)
        if text is None:  # an empty, hidden number slot
            for t in el.iter(qn('a:t')):
                if norm(t.text or ''):
                    t.text = None
            set_hidden(el, True)
        else:
            p = set_paragraphs(el, [text])[0]
            rPr = first_rPr(p)
            rPr.set('sz', size)
            rPr.attrib.pop('b', None)
            set_fill(rPr, colour)
            set_hidden(el, True)
        after = el
        restored.append(name)


def layout_card(slide, four_rows):
    """Place the Business data card's rows for three rows (no files) or four (files), from the card's corner."""
    named = shapes_named(slide)
    card = named.get('WIQ business card')
    ox, oy = (card[0].left, card[0].top) if card else CARD_ORIGIN
    for name, (x, y, w, h) in CARD_LAYOUT[four_rows].items():
        for sh in named.get(name, [])[:1]:
            sh.left, sh.top, sh.width, sh.height = ox + x, oy + y, w, h
            if name in NO_RIGHT_INSET:
                sh._element.find(qn('p:txBody')).find(qn('a:bodyPr')).set('rIns', '0')
    for name in ('WIQ static files label', 'WIQ static files where'):
        set_hidden(named[name][0]._element, not four_rows)


def anchor_top(slide):
    named = shapes_named(slide)
    for name in TOP_ANCHORED:
        for sh in named.get(name, []):
            sh._element.find(qn('p:txBody')).find(qn('a:bodyPr')).set('anchor', 't')


def find_dots(slide, area):
    """Entity dots (visible and hidden) by class: class colour and shape, small, centred inside the sphere."""
    ax, ay, aw, ah = area
    dots = {c: [] for c in CLASSES}
    for sh in slide.shapes:
        el = sh._element
        if el.tag != qn('p:sp'):
            continue
        cls = DOT_CLASS.get(tuple(reversed(geom_fill(el))))
        if cls is None:
            continue
        x, y, w, h = box_in(sh)
        if max(w, h) < 0.35 and ax <= x + w / 2 <= ax + aw and ay <= y + h / 2 <= ay + ah:
            dots[cls].append(sh)
    return dots


def repair_dots(slide, area, ids, restored):
    """Every class keeps at least one dot to clone from; a class an older deck lost gets one at its reference cluster."""
    dots = find_dots(slide, area)
    donors = [s for c in CLASSES for s in dots[c]]
    if not donors:
        fail('template has no entity dots to copy')
    for c in CLASSES:
        if dots[c]:
            continue
        colour, prst = DOT_STYLE[c]
        donor = next((s for s in donors if geom_fill(s._element)[0] == prst), donors[0])
        x0, y0, x1, y1 = ref_cluster(c, area)
        el = clone_shape(donor._element, 'WIQ dot %s 1' % c, ids.next(),
                         box=(round(((x0 + x1) / 2) * EMU_IN - REF_DOT / 2), round(((y0 + y1) / 2) * EMU_IN - REF_DOT / 2), REF_DOT, REF_DOT))
        spPr = el.find(qn('p:spPr'))
        spPr.find(qn('a:prstGeom')).set('prst', prst)
        set_fill(spPr, colour)
        set_hidden(el, True)
        restored.append('WIQ dot %s' % c)


def ref_cluster(c, area):
    """The class's reference cluster box (inches), mapped onto this template's sphere."""
    sx, sy, sw, sh = [v / EMU_IN for v in REF_SPHERE]
    x0, y0, x1, y1 = [v / EMU_IN for v in REF_CLUSTER[c]]
    kx, ky = area[2] / sw, area[3] / sh
    return (area[0] + (x0 - sx) * kx, area[1] + (y0 - sy) * ky, area[0] + (x1 - sx) * kx, area[1] + (y1 - sy) * ky)


def adjust_dots(slide, counts, area, hub, ids):
    """One visible dot per entity: the largest dots of a class are shown and the rest hidden (never deleted); if a class
    needs more, small dots are cloned with seeded random offsets inside that cluster's box (never under the centre
    circle or outside the sphere). Every class keeps at least one hidden dot for the next fill to clone from."""
    dots = find_dots(slide, area)
    scx, scy, sr = area[0] + area[2] / 2, area[1] + area[3] / 2, min(area[2], area[3]) / 2
    hcx, hcy, hr = hub[0] + hub[2] / 2, hub[1] + hub[3] / 2, min(hub[2], hub[3]) / 2
    for c in CLASSES:
        ordered = sorted(dots[c], key=lambda s: (-(s.width * s.height), zpos(s._element)))
        for i, s in enumerate(ordered):
            set_hidden(s._element, i >= counts[c])
    centre = lambda s: (box_in(s)[0] + box_in(s)[2] / 2, box_in(s)[1] + box_in(s)[3] / 2, max(box_in(s)[2:]) / 2)
    placed = [centre(s) for c in CLASSES for s in dots[c] if not is_hidden(s._element)]
    for ci, c in enumerate(CLASSES):
        have, need = dots[c], counts[c]
        if need < len(have):  # a hidden dot is left over for the next fill to clone from
            continue
        rng = random.Random(SEED * 10 + ci)
        rx0, ry0, rx1, ry1 = ref_cluster(c, area)
        bx0 = min([box_in(s)[0] for s in have] + [rx0])
        by0 = min([box_in(s)[1] for s in have] + [ry0])
        bx1 = max([box_in(s)[0] + box_in(s)[2] for s in have] + [rx1])
        by1 = max([box_in(s)[1] + box_in(s)[3] for s in have] + [ry1])
        sources = sorted(have, key=lambda s: (s.width * s.height, zpos(s._element)))
        small = min([min(s.width, s.height) for s in have] + [REF_SMALL_DOT])
        serial = max([int(m.group(1)) for s in have for m in [re.search(r'(\d+)$', s.name)] if m] or [len(have)])
        for k in range(need + 1 - len(have)):  # the last one is a hidden spare
            src = sources[k % len(sources)]
            ocx, ocy = box_in(src)[0] + box_in(src)[2] / 2, box_in(src)[1] + box_in(src)[3] / 2
            w = h = small / EMU_IN
            r = w / 2
            best, best_clear = None, -1.0
            for attempt in range(600):
                spread = min(0.08 + 0.003 * attempt, 0.6)
                cx = min(max(ocx + rng.uniform(-spread, spread), bx0 + r), bx1 - r)
                cy = min(max(ocy + rng.uniform(-spread, spread), by0 + r), by1 - r)
                if math.hypot(cx - scx, cy - scy) > sr - r - 0.05 or math.hypot(cx - hcx, cy - hcy) < hr + r + 0.02:
                    continue
                clear = min([math.hypot(cx - px, cy - py) / (r + pr) for px, py, pr in placed] or [9.0])
                if clear > best_clear:
                    best, best_clear = (cx, cy), clear
                if clear >= (1.15 if attempt < 200 else 0.85):
                    break
            if best is None:
                best = (ocx, ocy)
            serial += 1
            el = clone_shape(src._element, 'WIQ dot %s %d' % (c, serial), ids.next(),
                             box=(round((best[0] - w / 2) * EMU_IN), round((best[1] - h / 2) * EMU_IN), small, small))
            spare = len(have) + k >= need
            set_hidden(el, spare)
            if not spare:
                placed.append((best[0], best[1], r))
    final = find_dots(slide, area)
    shown = {c: sum(1 for s in final[c] if not is_hidden(s._element)) for c in CLASSES}
    hidden = {c: len(final[c]) - shown[c] for c in CLASSES}
    if shown != counts:
        fail('dot counts %s do not match entity counts %s' % (shown, counts))
    if not all(hidden[c] for c in CLASSES):
        fail('every dot class must keep a hidden dot for the next fill')
    return shown, hidden


# ------------------------------------------------------------------------------------------------- fitting
def fit_spec(name):
    if name in NUMBERS or name == 'WIQ total':
        return {'lines': 1, 'steps': 3, 'truncate': False}
    if name in ('WIQ title', 'WIQ subtitle'):
        return {'lines': 1, 'steps': 1, 'heading': 0.4 if name == 'WIQ title' else 0.0}
    if name.startswith('WIQ cls '):
        return {'lines': 1, 'steps': 1, 'split_head': True}
    if name == 'WIQ outputs':
        return {'lines': 2, 'steps': 1, 'slack': 0.0}
    if name in ('WIQ context proof', 'WIQ memory proof', 'WIQ skills proof'):
        return {'lines': 3, 'steps': 1, 'slack': 0.08, 'sentence': True}
    if name == 'WIQ source':
        return {'lines': 2, 'steps': 1, 'slack': 0.05, 'sentence': True}
    return {'lines': 1, 'steps': 1}


def base_size(name, i, base=None):
    if base and name in base:
        return float(base[name])
    if name.startswith('WIQ cls '):
        return 10.0 if i == 0 else 9.0
    if name.startswith('WIQ portal '):
        return 11.0
    return float(BASE_SIZE[name])


def styles_for(sh, name, n, base=None):
    tmpl = slot_paras(sh._element.find(qn('p:txBody')))
    if not tmpl:
        fail('template shape "%s" has no text paragraph to fill' % name)
    return [(base_size(name, i, base), (name == 'WIQ cls customer' and i > 0) or run_style(tmpl[min(i, len(tmpl) - 1)])[1])
            for i in range(n)]


def avail_width(sh, slide):
    x, y, w, h = box_in(sh)
    l_ins, _, r_ins, _, _ = insets(sh._element)
    left, right = x + l_ins, x + w - r_ins
    for ob in slide.shapes:
        if ob.name in BUTTONS:
            ox, oy, ow, oh = box_in(ob)
            if oy < y + h and oy + oh > y and left < ox < right:
                right = ox - 0.08
    return right - left


def block_limits(sh, name):
    """Height a multi-line block may take (inches) and the height of its spacer paragraphs."""
    spec = fit_spec(name)
    _, t_ins, _, b_ins, anchor = insets(sh._element)
    spacer = sum(LINE * run_style(p)[0] for p in sh._element.find(qn('p:txBody')).findall(qn('a:p')) if is_spacer(p)) / 72.0
    return box_in(sh)[3] - t_ins - b_ins + spec['slack'] * (2 if anchor == 'ctr' else 1), spacer


def _single_line_fits(texts, styles, idx, step, width, lines):
    return all(len(wrap(texts[i], smaller(styles[i][0], step), styles[i][1], width)) <= lines for i in idx)


def steps_needed(sh, name, texts, slide, base=None):
    """Smallest shrink step at which every paragraph of a single-line shape fits (capped at the allowed steps)."""
    spec = fit_spec(name)
    styles = styles_for(sh, name, len(texts), base)
    width = avail_width(sh, slide)
    return next((s for s in range(spec['steps'] + 1)
                 if _single_line_fits(texts, styles, range(len(texts)), s, width, spec['lines'])), spec['steps'])


def fit(sh, name, texts, slide, force_step=None, base=None):
    """Choose a font size per paragraph (never below 9pt; at most one step smaller, three for the big numbers) and
    shorten what still does not fit: names with '...' at a word boundary, sentences at a sentence or clause boundary,
    the title and subtitle at a clause boundary. force_step makes shapes of one group (the pills, the big numbers)
    shrink together; base overrides the starting size (the numbers of the four-row card)."""
    spec = fit_spec(name)
    styles = styles_for(sh, name, len(texts), base)
    width = avail_width(sh, slide)
    sizes = [s for s, _ in styles]
    texts = list(texts)
    note = None
    if 'slack' not in spec:
        groups = [[0], list(range(1, len(texts)))] if spec.get('split_head') and len(texts) > 1 else [list(range(len(texts)))]
        for g in groups:
            ok = False
            for step in ([force_step] if force_step is not None else range(spec['steps'] + 1)):
                trial = [smaller(styles[i][0], step) for i in g]
                if _single_line_fits(texts, styles, g, step, width, spec['lines']):
                    ok = True
                    break
            for j, i in enumerate(g):
                sizes[i] = trial[j]
            if not ok:
                if 'heading' in spec:
                    for i in g:
                        texts[i] = cut_heading(texts[i], lambda t, i=i: len(wrap(t, sizes[i], styles[i][1], width)) <= spec['lines'],
                                               spec['heading'])
                    note = 'shortened' if texts[g[0]].endswith(ELLIPSIS) else 'cut at a clause boundary'
                elif spec.get('truncate', True):
                    for i in g:
                        texts[i] = truncate(texts[i], lambda t, i=i: len(wrap(t, sizes[i], styles[i][1], width)) <= spec['lines'])
                    note = 'shortened'
                else:
                    note = 'too wide even at %gpt' % min(sizes)
            elif step and sizes[g[0]] != styles[g[0]][0]:
                note = note or 'shrunk'
        return texts, sizes, styles, note
    # multi-line block: every line counts against the box height (plus slack where the layout allows)
    max_h, spacer = block_limits(sh, name)

    def height(sz, nlines):
        return sum(n * s * LINE for n, s in zip(nlines, sz)) / 72.0 + spacer

    ok = False
    for step in range(spec['steps'] + 1):
        sizes = [smaller(s, step) for s, _ in styles]
        nlines = [len(wrap(t, sizes[i], styles[i][1], width)) for i, t in enumerate(texts)]
        if max(nlines) <= spec['lines'] and height(sizes, nlines) <= max_h:
            ok = True
            break
    if ok:
        return texts, sizes, styles, ('shrunk' if step and sizes != [s for s, _ in styles] else None)
    budget = [min(n, spec['lines']) for n in nlines]
    while height(sizes, budget) > max_h:
        if max(budget) > 1:
            i = max(range(len(budget)), key=lambda k: (budget[k], k))
            budget[i] -= 1
        elif len(texts) > 1:
            texts, sizes, styles, budget = texts[:-1], sizes[:-1], styles[:-1], budget[:-1]
        else:
            break
    shorten = cut_at_boundary if spec.get('sentence') else truncate
    texts = [shorten(t, lambda x, i=i: len(wrap(x, sizes[i], styles[i][1], width)) <= budget[i]) for i, t in enumerate(texts)]
    return texts, sizes, styles, 'cut at a sentence or clause boundary' if spec.get('sentence') else 'shortened'


def pick_memory(content, sh, slide):
    """text.slideMemory if set; else the first memory callout that fits whole at the shape's font size; else the first
    callout cut at a sentence or clause boundary."""
    if content.memory_override:
        return content.memory_override, None
    size, bold = styles_for(sh, 'WIQ memory proof', 1)[0]
    width = avail_width(sh, slide)
    max_h, spacer = block_limits(sh, 'WIQ memory proof')
    cap = fit_spec('WIQ memory proof')['lines']

    def whole(t):
        n = len(wrap(t, size, bold, width))
        return n <= cap and n * size * LINE / 72.0 + spacer <= max_h

    cands = content.memory_candidates
    for i, t in enumerate(cands):
        if whole(t):
            return t, (None if i == 0 else 'memory callout %d of %d, the first that fits whole' % (i + 1, len(cands)))
    return cut_at_boundary(cands[0], whole), 'memory callout 1 of %d cut at a sentence or clause boundary (none fits whole)' % len(cands)


# -------------------------------------------------------------------------------------------- residue guard
def shape_texts(container_el):
    """(shape id, name, [paragraph texts], [alt texts], hidden) for every shape element, groups included."""
    out = []
    for el in container_el.iter(qn('p:sp'), qn('p:graphicFrame'), qn('p:pic'), qn('p:cxnSp'), qn('p:grpSp')):
        cnv = el.find('.//' + qn('p:cNvPr'))
        if el.tag == qn('p:sp'):
            tx = el.find(qn('p:txBody'))
            paras = tx.findall(qn('a:p')) if tx is not None else []
        elif el.tag == qn('p:graphicFrame'):
            paras = list(el.iter(qn('a:p')))
        else:
            paras = []
        texts = [norm(para_text(p)) for p in paras]
        alts = [norm(cnv.get(a) or '') for a in ('descr', 'title')] if cnv is not None else []
        hidden = cnv is not None and (cnv.get('hidden') or '').lower() in ('1', 'true')
        out.append((int(cnv.get('id')) if cnv is not None and (cnv.get('id') or '').isdigit() else -1,
                    cnv.get('name') if cnv is not None else '', [t for t in texts if t], [a for a in alts if a], hidden))
    return out


def set_tooltips(prs, html_rids):
    """Screen tips are fixed wording owned by this script: sphere links, the jump to the official slide and the way back."""
    first, second = prs.slides[0].part, prs.slides[1].part
    for slide in list(prs.slides)[:2]:
        for h in slide._element.iter(qn('a:hlinkClick')):
            rid = h.get(qn('r:id'))
            if rid in html_rids.get(slide.part, ()):
                h.set('tooltip', TIP_SPHERE)
            elif (h.get('action') or '').startswith('ppaction://hlinksldjump') and rid in slide.part.rels:
                part = slide.part.rels[rid].target_part
                if part is second:
                    h.set('tooltip', TIP_OFFICIAL)
                elif part is first:
                    h.set('tooltip', TIP_BACK)


def notes_body(slide):
    if not slide.has_notes_slide:
        return None
    ph = slide.notes_slide.notes_placeholder
    return ph._element if ph is not None else None


def collect_previous(prs):
    """Every text in the template before filling (the previous person's fill), minus the static labels."""
    prev = set()
    for slide in list(prs.slides)[:2]:
        for _, _, texts, alts, _ in shape_texts(slide._element):
            prev.update(texts)
            prev.update(alts)
        if slide.has_notes_slide:
            for _, _, texts, _, _ in shape_texts(slide.notes_slide._element):
                prev.update(texts)
    return prev - set(norm(t) for t in STATIC_TEXT + STATIC_ALT)


def residue_guard(prs, written, written_notes):
    """Slide 1 shapes we filled must hold exactly what we wrote; every other text on slides 1 and 2 (and in their
    notes) must be a static label. Hidden, empty slots are fine. Anything else is residue."""
    static = set(norm(t) for t in STATIC_TEXT)
    alt_ok = set(norm(t) for t in STATIC_ALT)
    mine = {t for v in written.values() for t in v} | set(written_notes)
    offenders, dashes = [], []
    for si, slide in enumerate(list(prs.slides)[:2], 1):
        for sid, name, texts, alts, hidden in shape_texts(slide._element):
            if si == 1 and sid in written:
                if texts != written[sid]:
                    offenders += [t for t in texts if t not in written[sid]] or ['%s (paragraphs changed)' % name]
            elif si == 1 and (name in TEXT_SHAPES or (PILL_RE.fullmatch(name or '') and name.endswith(' text'))):
                if texts or not hidden:
                    offenders += texts or ['%s (left unfilled)' % name]
            else:
                offenders += [t for t in texts if t not in static]
            offenders += [a for a in alts if a not in alt_ok and a not in mine]
            dashes += [t for t in texts + alts if re.search('[\u2013\u2014]', t)]
        tips = [norm(h.get('tooltip')) for h in slide._element.iter(qn('a:hlinkClick'), qn('a:hlinkHover')) if norm(h.get('tooltip') or '')]
        offenders += [t for t in tips if t not in STATIC_TIPS]
        body = notes_body(slide)
        if slide.has_notes_slide:
            for sid, name, texts, alts, hidden in shape_texts(slide.notes_slide._element):
                if body is not None and sid == int(body.find('.//' + qn('p:cNvPr')).get('id')):
                    expect = written_notes if si == 1 else []
                    if texts != expect:
                        offenders += [t for t in texts if t not in expect] or ['speaker notes (paragraphs changed)']
                else:
                    offenders += [t for t in texts if not re.fullmatch(r'\d*', t)]
                dashes += [t for t in texts if re.search('[\u2013\u2014]', t)]
    if dashes:
        fail('slide text contains an em or en dash: %s' % '; '.join('"%s"' % t for t in dashes[:5]))
    if offenders:
        uniq = list(dict.fromkeys(offenders))
        fail('slide still contains text that did not come from your config: %s%s' % (
            '; '.join('"%s"' % t[:90] for t in uniq[:8]), ' (and %d more)' % (len(uniq) - 8) if len(uniq) > 8 else ''))


_REF_TEXTS = None

def reference_texts():
    """Texts the shipped reference itself carries outside its two slides (placeholder prompts, theme, font and app names)."""
    global _REF_TEXTS
    if _REF_TEXTS is None:
        out, parser = set(), etree.XMLParser(recover=True, huge_tree=True)
        with zipfile.ZipFile(DEFAULT_TEMPLATE) as z:
            for name in z.namelist():
                low = name.lower()
                if not low.endswith('.xml') or low.startswith(('ppt/slides/', 'ppt/notesslides/')):
                    continue
                root = etree.fromstring(z.read(name), parser)
                if root is None:
                    continue
                out.update(norm(para_text(p)) for p in root.iter(qn('a:p')))
                for el in root.iter():
                    if isinstance(el.tag, str):
                        if el.text and el.tag != qn('a:t'):
                            out.add(norm(el.text))
                        out.update(norm(el.get(a)) for a in ('descr', 'title') if el.get(a))
        _REF_TEXTS = out
    return _REF_TEXTS


CORE_PEOPLE = ('creator', 'lastModifiedBy', 'title', 'subject', 'keywords', 'description', 'category', 'contentStatus')
DROP_RELS = ('/comments', '/commentAuthors', '/authors', '/thumbnail')
LABEL_PROPERTY = re.compile(r'^MSIP_Label_', re.I)


def keep_label_properties(pkg, rId, part):
    """Custom document properties can name a person or a project; the Microsoft sensitivity label is stored there too
    (MSIP_Label_* properties). Keep exactly the label properties, unchanged, and drop the rest (the part goes when
    nothing is left)."""
    blob = part.blob if not hasattr(part, '_element') else etree.tostring(part._element, xml_declaration=True, encoding='UTF-8', standalone=True)
    root = etree.fromstring(blob)
    gone = [el for el in root if not LABEL_PROPERTY.match(el.get('name') or '')]
    if len(gone) == len(root):
        pkg.drop_rel(rId)
        return
    for el in gone:
        root.remove(el)
    if hasattr(part, '_element'):
        part._element = root
    else:
        part._blob = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def scrub_package(prs):
    """Remove what the template deck says about whoever made or edited it: document properties, comments and their
    authors, custom properties other than the sensitivity label's, and the preview picture. The deck's Microsoft
    sensitivity label (docMetadata/LabelInfo.xml and MSIP_Label custom properties) is never removed, changed or
    downgraded: every deck this script writes inherits the template's label."""
    cp = prs.core_properties
    for k in ('author', 'last_modified_by', 'title', 'subject', 'keywords', 'comments', 'category', 'content_status',
              'identifier', 'language', 'version'):
        setattr(cp, k, '')
    cp.revision = 1
    pkg = prs.part.package
    for owner in [pkg, prs.part] + [sl.part for sl in prs.slides]:
        rels = owner._rels if owner is pkg else owner.rels
        for rId, rel in list(rels.items()):
            if rel.reltype.endswith(DROP_RELS):
                (pkg.drop_rel if owner is pkg else owner.drop_rel)(rId)
            elif owner is pkg and rel.reltype.endswith('/custom-properties'):
                keep_label_properties(pkg, rId, rel.target_part)
    for part in pkg.iter_parts():
        if str(part.partname) == '/docProps/app.xml':
            root = etree.fromstring(part.blob)
            for el in root:
                if etree.QName(el).localname in ('Company', 'Manager', 'HyperlinkBase'):
                    el.text = ''
            part._blob = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def verify_package(path, previous, mine):
    """Second net over the saved file: no XML part anywhere (notes, document properties, change tracking...) may
    still hold a text from the template's previous fill that the config did not write again."""
    static = set(norm(t) for t in STATIC_TEXT + STATIC_ALT)
    stale = {t for t in previous if t not in mine and len(t) >= 4 and re.search('[A-Za-z]', t)}
    long_stale = [t for t in stale if len(t) >= 24 and not any(t in m for m in mine)]
    hits = []
    parser = etree.XMLParser(recover=True, huge_tree=True)
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            low = name.lower()
            if 'thumbnail' in low:
                hits.append(('(preview picture of a previous fill)', name))
                continue
            if not low.endswith(('.xml', '.rels')):
                continue
            root = etree.fromstring(z.read(name), parser)
            if root is None:
                continue
            texts = [norm(para_text(p)) for p in root.iter(qn('a:p'))]
            for el in root.iter():
                if isinstance(el.tag, str) and el.text and el.tag != qn('a:t'):
                    texts.append(norm(el.text))
                for a in ('descr', 'title'):
                    if el.get(a):
                        texts.append(norm(el.get(a)))
            hits += [(t, name) for t in texts if t in stale]
            flat = norm(' '.join(texts))
            hits += [(t, name) for t in long_stale if t in flat]
            if low.startswith(('ppt/slidelayouts/', 'ppt/slidemasters/', 'ppt/notesmasters/', 'ppt/handoutmasters/',
                               'ppt/comments', 'ppt/commentauthors', 'ppt/authors', 'docprops/app')):
                allowed = reference_texts() | mine | static
                hits += [(t, name) for t in texts if t and t not in allowed and re.search('[A-Za-z]{3}', t)]
            if low == 'docprops/core.xml':
                hits += [(norm(el.text), name) for el in root.iter() if isinstance(el.tag, str) and
                         etree.QName(el).localname in CORE_PEOPLE and norm(el.text or '')]
            if re.match(r'ppt/slides/slide(\d+)\.xml$', low) and low not in ('ppt/slides/slide1.xml', 'ppt/slides/slide2.xml'):
                hits.append(('(an extra slide)', name))
    if hits:
        uniq = list(dict.fromkeys(hits))
        fail('slide still contains text that did not come from your config: %s' % '; '.join(
            '"%s" (in %s)' % (t[:90], n) for t, n in uniq[:8]))


# ---------------------------------------------------------------------------------------------------- main
def build(config_path, out_path, template_path, target=None, internal_names=False, extra_leaks=(), discovery_path=None):
    try:
        with open(config_path, encoding='utf-8') as fh:
            cfg = json.load(fh)
    except (OSError, ValueError) as e:
        fail('cannot read config %s: %s' % (config_path, e))
    if not isinstance(cfg, dict):
        fail('config must be a JSON object')
    if discovery_path:                     # version 1.8: count placeholders filled for the three months
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_workiq as B
        try:
            cfg = B.resolve_config(cfg, json.load(open(discovery_path, encoding='utf-8')))
        except (OSError, ValueError, KeyError) as e:
            fail('cannot fill the counts in the config text (%s)' % e)
    target = quote(unquote(target or (INTERNAL_TARGET if internal_names else SAFE_TARGET)), safe="/:#?&=@+,;~%()")
    content = Content(cfg, internal_names, target)

    if not os.path.exists(template_path):
        fail('template not found: %s' % template_path)
    prs = Presentation(template_path)
    if len(prs.slides) != 2:
        fail('template must have exactly the Work IQ slide and the hidden official slide (it has %d slides); use the shipped '
             'reference or a deck this script wrote' % len(prs.slides))
    s1, s2 = prs.slides[0], prs.slides[1]
    if not any(sh.name.startswith('WIQ ') for sh in s1.shapes):
        fail('template %s has no "WIQ ..." shape names; use the shipped reference or a deck this script wrote' % template_path)
    previous = collect_previous(prs)

    ids, restored = Ids(s1), []
    repair_pills(s1, ids, restored)
    repair_labels(s1, ids, restored)
    repair_outputs(s1, ids, restored)
    repair_files(s1, ids, restored)
    area = next((box_in(sh) for sh in s1.shapes if sh.name == 'Sphere click area'), SPHERE_FALLBACK)
    hub = next((box_in(sh) for sh in s1.shapes if sh.name == 'WIQ hub circle'), HUB_FALLBACK)
    repair_dots(s1, area, ids, restored)
    named = shapes_named(s1)
    for n in SINGLE_SHAPES:
        if len(named.get(n, [])) != 1:
            fail('template must have exactly one shape named "%s" on slide 1 (found %d)' % (n, len(named.get(n, []))))
    shape = {n: named[n][0] for n in SINGLE_SHAPES}
    four_rows = content.files is not None
    layout_card(s1, four_rows)
    anchor_top(s1)
    for sh in named.get('WIQ static memory def', [])[:1]:   # back to weeks, or days for the week, on every fill
        set_paragraphs(sh._element, [MEMORY_DEF[content.unit]])
    base = {n: FOUR_ROW_NUMBER_SIZE for n in NUMBERS} if four_rows else None

    memory, memory_note = pick_memory(content, shape['WIQ memory proof'], s1)
    fields = content.fields(memory)
    all_text = [(k, t) for k, v in fields.items() if v for t in v] + [('notes', t) for t in content.notes]
    for k, t in all_text:
        if re.search('[\u2013\u2014]', t):
            fail('%s would put an em or en dash on the slide: "%s". Use commas, colons, parentheses or "to"' % (k, t))
    if not internal_names:
        def scanned(k, t):                 # version 1.7.1: the source line's fixed wording is the skill's, not a name
            fixed = getattr(content, 'fixed_source', None)
            return t.replace(fixed, ' ') if k == 'WIQ source' and fixed else t
        leaks = [(term, k) for term in sorted(set(content.leak_terms()) | set(extra_leaks)) for k, t in all_text
                 if re.search(r'(?<![A-Za-z0-9])' + re.escape(term) + r'(?![A-Za-z0-9])', scanned(k, t),
                              0 if any(ch.isupper() for ch in term) else re.I)]
        if leaks:
            fail('customer-safe slide would show real names: %s. Refer to customers, people and escalations with '
                 '{entity_id} tokens (they show the safe alias), or pass --internal-names for an internal-only deck'
                 % ', '.join('"%s" in %s' % lk for lk in dict.fromkeys(leaks)))

    forced = {}
    for group in SHRINK_TOGETHER:
        present = [n for n in group if fields[n] is not None]
        step = max([steps_needed(shape[n], n, fields[n], s1, base) for n in present] or [0])
        forced.update({n: step for n in present})

    written, fitted, hidden_slots = {}, [], []
    if memory_note:
        fitted.append({'shape': 'WIQ memory proof', 'fit': memory_note, 'size': base_size('WIQ memory proof', 0)})
    for name in TEXT_SHAPES:
        sh, texts = shape[name], fields[name]
        if texts is None:  # not needed by this config: hidden and emptied, kept for the next fill
            hide_slot(sh._element)
            for i, p in enumerate(slot_paras(sh._element.find(qn('p:txBody')))):
                if p.find(qn('a:r')) is not None:  # back to the reference size, whatever an earlier fill used
                    set_run_attr(p, 'sz', str(int(round(base_size(name, i) * 100))))
            hidden_slots.append(name)
            continue
        set_hidden(sh._element, False)
        texts, sizes, styles, note = fit(sh, name, texts, s1, forced.get(name), base)
        paras = set_paragraphs(sh._element, texts)
        for i, p in enumerate(paras):
            set_run_attr(p, 'sz', str(int(round(sizes[i] * 100))))
            if name == 'WIQ cls customer' and i > 0:
                set_run_attr(p, 'b', '1')
        if note:
            fitted.append({'shape': name, 'fit': note, 'size': min(sizes)})
            if name in ('WIQ title', 'WIQ subtitle') and note != 'shrunk':
                content.warnings.append('%s shortened to fit: "%s" (set text.%s to a shorter one to choose the words)'
                                        % (name[4:], texts[0], 'slideTitle' if name == 'WIQ title' else 'slideSubtitle'))
        written[sh.shape_id] = [norm(t) for t in texts]
    for sh in s1.shapes:
        m = PILL_RE.fullmatch(sh.name)
        if m and int(m.group(1)) > len(content.portals):
            if m.group(2) != 'text' or int(m.group(1)) > MAX_PORTALS:
                hide_slot(sh._element)
        elif m and m.group(2) != 'text':
            set_hidden(sh._element, False)
    for n in ('WIQ static outputs heading', 'WIQ outputs divider'):
        set_hidden(shape[n]._element, not content.outputs)

    dots, dots_hidden = adjust_dots(s1, content.counts, area, hub, ids)

    n_links, html_rids = 0, {}
    for slide in prs.slides:
        rids = html_rids.setdefault(slide.part, set())
        for rel in slide.part.rels.values():
            if rel.reltype == RT.HYPERLINK and rel.is_external:
                base = str(rel._target).split('#')[0].split('?')[0].lower()
                if base.endswith(('.html', '.htm')):
                    rel._target = target
                    rel.__dict__.pop('target_ref', None)  # python-pptx caches it
                    rids.add(rel.rId)
        n_links += sum(1 for h in slide._element.iter(qn('a:hlinkClick')) if h.get(qn('r:id')) in rids)
    set_tooltips(prs, html_rids)

    body = s1.notes_slide.notes_placeholder
    if body is None:
        fail('slide 1 notes have no body placeholder')
    set_paragraphs(body._element, content.notes)
    written_notes = [norm(t) for t in content.notes]
    s2._element.set('show', '0')

    scrub_package(prs)  # also drops the thumbnail, a picture of the template's previous fill; keeps the sensitivity label
    dash_free_bullets(prs)

    residue_guard(prs, written, written_notes)

    out_abs = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    tmp = os.path.join(os.path.dirname(out_abs), '.~fill-%d-%s' % (os.getpid(), os.path.basename(out_abs)))
    mine = {t for v in written.values() for t in v} | set(written_notes)
    for attempt in range(3):  # cloud-synced folders can fail a write or rename now and then (EIO): try again
        try:
            prs.save(tmp)
            verify_package(tmp, previous, mine)
            data = open(tmp, 'rb').read()
            os.replace(tmp, out_abs)
            if os.path.exists(tmp) or open(out_abs, 'rb').read() != data:   # synced folders can undo a rename
                raise OSError('the new slide did not replace the old file')
            break
        except FillError:
            remove_quietly(tmp)
            raise
        except (OSError, zipfile.BadZipFile) as e:
            remove_quietly(tmp)
            if attempt == 2:
                fail('could not write %s: %s' % (out_path, e))
            time.sleep(1.0)
    if internal_names:
        content.warnings.append('real names shown: present internally only, never send this deck to customers')
    return {'status': 'ok', 'out': out_path,
            'numbers': dict({'emails': content.emails, 'events': content.events, 'chats': content.chats},
                            **({'files': content.files} if four_rows else {}), total=content.total,
                            **({'focus': content.fcounts} if content.focus is not None and content.fcounts else {})),
            'classes': content.counts, 'portals': len(content.portals), 'outputs': len(content.outputs),
            'customer_safe': not internal_names, 'dots': dots, 'dots_hidden': dots_hidden,
            'context': {'entities': content.n_entities, 'types': content.n_types, 'relationships': content.n_relations},
            'html_links': n_links, 'target': target, 'fitted': fitted, 'hidden_slots': hidden_slots,
            'restored_slots': restored, 'warnings': content.warnings}


def dash_free_bullets(prs):
    """The stock Office master bullets levels 2 and 4 with an en dash; decks this script writes use a round bullet,
    so a slide a presenter adds to the deck carries no dash either."""
    parts = [prs.notes_master._element]
    for master in prs.slide_masters:
        parts += [master._element] + [layout._element for layout in master.slide_layouts]
    for el in parts:
        for bu in el.iter(qn('a:buChar')):
            if bu.get('char') in ('\u2013', '\u2014'):
                bu.set('char', '\u2022')


def remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


def fresh_analysis_guard(config_path, discovery_path, internal_names=False):
    """Same checks as build_workiq.py: the config must be this person's own fresh, evidence-backed analysis."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_workiq as B
    try:
        cfg = json.load(open(config_path, encoding='utf-8'))
        disc = json.load(open(discovery_path, encoding='utf-8'))
    except (OSError, ValueError) as e:
        print('ERROR: cannot read %s' % e); sys.exit(2)
    B.guard(cfg, disc)
    if not internal_names:
        B.check_safe_aliases(cfg, disc)
    return B.safe_leak_terms(cfg, disc)


# ---- optional tools for another deck (version 1.8.2: formerly add_sphere_link.py and add_official_slide.py) ----
LINK_TIP = 'Opens the interactive Work IQ sphere'
POP_NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}


def _link(sh, target):
    sh.click_action.hyperlink.address = target
    h = sh._element.find('.//' + qn('a:hlinkClick'))
    if h is not None: h.set('tooltip', LINK_TIP)


def add_sphere_link(argv):
    """Make a Work IQ slide open the interactive sphere when clicked (a local .pptx copy)."""
    from pptx.util import Emu, Pt
    from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.dml.color import RGBColor
    ap = argparse.ArgumentParser(prog='fill_slide.py --add-sphere-link')
    ap.add_argument('--in', dest='inp', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--slide', type=int, default=1); ap.add_argument('--target', default='Work%20IQ%20Sphere.html')
    ap.add_argument('--box'); ap.add_argument('--html-name', default='Work IQ Sphere.html')
    a = ap.parse_args(argv)
    p = Presentation(a.inp); s = p.slides[a.slide - 1]
    if a.box:
        x, y, w, h = [int(v) for v in a.box.split(',')]
    else:
        ovals = [sh for sh in s.shapes if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and 'Oval' in sh.name]
        if not ovals: raise SystemExit('No oval found; pass --box x,y,w,h')
        big = max(ovals, key=lambda sh: sh.width * sh.height); x, y, w, h = big.left, big.top, big.width, big.height
    ov = s.shapes.add_shape(MSO_SHAPE.OVAL, Emu(x), Emu(y), Emu(w), Emu(h)); ov.name = 'Sphere click area'
    ov.fill.solid(); ov.fill.fore_color.rgb = RGBColor(255, 255, 255)
    clr = ov._element.spPr.find(qn('a:solidFill')).find(qn('a:srgbClr')); etree.SubElement(clr, qn('a:alpha')).set('val', '0')
    ov.line.fill.background(); ov.shadow.inherit = False; _link(ov, a.target)
    bw, bh = 1500000, 290000
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(x + (w - bw) // 2), Emu(y + h + 40000), Emu(bw), Emu(bh)); b.name = 'Explore in 3D button'
    b.fill.solid(); b.fill.fore_color.rgb = RGBColor(255, 255, 255); b.line.color.rgb = RGBColor(0x00, 0x78, 0xD4); b.line.width = Pt(1); b.shadow.inherit = False
    tf = b.text_frame; tf.margin_top = tf.margin_bottom = Emu(0); tf.word_wrap = False; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para = tf.paragraphs[0]; para.alignment = PP_ALIGN.CENTER; r = para.add_run(); r.text = '\u25B6  Explore in 3D'
    r.font.name = 'Segoe UI Semibold'; r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x00, 0x78, 0xD4); _link(b, a.target)
    s.notes_slide.notes_text_frame.add_paragraph().text = ('Click the sphere or Explore in 3D to open the interactive version '
                                                          '(keep %s in the same folder as this deck).' % a.html_name)
    p.save(a.out); print('linked', a.out, '->', a.target)


def _pop_button(shapes, template, name, box, text, tip, target):
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    if template is not None:
        el = copy.deepcopy(template._element); shapes._spTree.append(el); sh = shapes[-1]
        el.find('.//p:cNvPr', POP_NS).set('id', str(max(s.shape_id for s in shapes) + 1))
        for h in el.findall('.//a:hlinkClick', POP_NS): h.getparent().remove(h)
        tf = sh.text_frame; p = tf.paragraphs[0]
        for extra in p.runs[1:]: extra._r.getparent().remove(extra._r)
        for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)
        p.runs[0].text = text
    else:
        sh = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0, 0, 1, 1)
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sh.line.color.rgb = RGBColor(0x00, 0x78, 0xD4); sh.line.width = Pt(1.25); sh.shadow.inherit = False
        tf = sh.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = text
        r.font.name = 'Segoe UI Semibold'; r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x00, 0x78, 0xD4)
    sh.name = name
    sh.left, sh.top, sh.width, sh.height = [Inches(v) for v in box]
    sh.click_action.target_slide = target
    sh._element.find('.//p:cNvPr/a:hlinkClick', POP_NS).set('tooltip', tip)
    return sh


def _pop_fade(slide):
    e = slide._element
    if e.find('p:transition', POP_NS) is not None: return
    t = etree.SubElement(e, '{%s}transition' % POP_NS['p']); t.set('spd', 'slow'); etree.SubElement(t, '{%s}fade' % POP_NS['p'])
    anchor = e.find('p:clrMapOvr', POP_NS)
    (anchor if anchor is not None else e.find('p:cSld', POP_NS)).addnext(t)


def add_official_slide(argv):
    """Add Microsoft's official Work IQ slide to a Work IQ deck as a hidden pop-up slide."""
    ap = argparse.ArgumentParser(prog='fill_slide.py --add-official-slide')
    ap.add_argument('--in', dest='src', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--image', default=os.path.join(HERE, '..', 'templates', 'official_workiq_slide.jpg'))
    ap.add_argument('--button-box', default='10.23,0.88,2.61,0.34', help='x,y,w,h in inches for the button on slide 1')
    ap.add_argument('--hide-internal', action='store_true')
    a = ap.parse_args(argv)
    prs = Presentation(a.src); main_slide = prs.slides[0]
    if any(sh.name == "Microsoft's Work IQ slide button" for sh in main_slide.shapes):
        raise SystemExit('ERROR: this deck already has the official slide button')
    tpl = next((s for s in main_slide.shapes if s.name == 'Explore in 3D button'), None)
    layout = next((l for l in prs.slide_layouts if l.name == 'Blank'), prs.slide_layouts[-1])
    off = prs.slides.add_slide(layout)
    for ph in list(off.placeholders): ph._element.getparent().remove(ph._element)
    pic = off.shapes.add_picture(a.image, 0, 0, prs.slide_width, prs.slide_height)
    pic.name = 'Microsoft Work IQ slide'; pic.click_action.target_slide = main_slide
    w_in = prs.slide_width / 914400; h_in = prs.slide_height / 914400
    _pop_button(off.shapes, tpl, 'Back to my Work IQ button', (w_in - 2.88, h_in - 0.88, 2.4, 0.38), '\u25C0  Back to my Work IQ', 'Back to my Work IQ', main_slide)
    box = [float(v) for v in a.button_box.split(',')]
    _pop_button(main_slide.shapes, tpl, "Microsoft's Work IQ slide button", box, "\u25B6  Microsoft's Work IQ slide", "Show Microsoft's official Work IQ slide", off)
    lst = prs.slides._sldIdLst; new = list(lst)[-1]; lst.remove(new); lst.insert(1, new)
    off._element.set('show', '0'); _pop_fade(off); _pop_fade(main_slide)
    hidden = 0
    if a.hide_internal:
        for s in prs.slides:
            if any(sh.has_text_frame and 'INTERNAL: do not show customers' in sh.text_frame.text for sh in s.shapes):
                s._element.set('show', '0'); hidden += 1
    prs.save(a.out)
    print('{"status": "ok", "out": "%s", "official_slide": 2, "internal_slides_hidden": %d}' % (a.out, hidden))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == '--add-sphere-link':
        return add_sphere_link(argv[1:])
    if argv and argv[0] == '--add-official-slide':
        return add_official_slide(argv[1:])
    ap = argparse.ArgumentParser(description='Fill the Work IQ slide from one person\'s workiq_config.json.',
                                 epilog='Optional tools for another deck (each has its own --help): --add-sphere-link --in DECK --out DECK '
                                        'adds the click-through to the sphere; --add-official-slide --in DECK --out DECK adds Microsoft\'s '
                                        'official Work IQ slide as a hidden pop-up slide.')
    ap.add_argument('--config', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--template', default=DEFAULT_TEMPLATE)
    ap.add_argument('--target', default=None, help=('relative link for the sphere HTML (default %s, or %s with --internal-names)'
                                                    % (SAFE_TARGET, INTERNAL_TARGET)).replace('%', '%%'))
    ap.add_argument('--internal-names', action='store_true', help='real names instead of safe aliases (internal use only)')
    ap.add_argument('--discovery', required=True, help='the discovery.json made by discover.py from the same data as the config')
    a = ap.parse_args(argv)
    extra = fresh_analysis_guard(a.config, a.discovery, a.internal_names)
    try:
        status = build(a.config, a.out, a.template, a.target, a.internal_names, extra, a.discovery)
    except FillError as e:
        print('ERROR: %s' % e)
        sys.exit(2)
    print(json.dumps(status, ensure_ascii=False))


if __name__ == '__main__':
    main()
