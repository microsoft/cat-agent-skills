#!/usr/bin/env python3
"""make_qr.py - portable QR code generator (Cowork + Copilot Studio).

Required: Pillow. QR encoder: ReportLab (preferred) -> qrcode -> segno, whichever is installed.
PDF: ReportLab vector PDF, or a Pillow raster PDF when ReportLab is missing. SVG needs nothing extra.
Optional: OpenCV / zxing-cpp / pyzbar - if present, the output is decoded to verify it really scans.
Run `python make_qr.py --check` first to see what this environment supports.

Output safety: every run writes ONLY into --scratch, which must be a new or empty folder inside the current
working directory (no "..", no links out). --file-name is reduced to safe characters, and every file is checked
to stay inside --scratch before it is written. Nothing outside --scratch is ever created, overwritten or deleted.

Examples:
  python make_qr.py --type url --url contoso.com --format png --scratch qr/contoso-run1 --file-name contoso.com-qr
  python make_qr.py --type wifi --ssid MyNet --password s3cret --auth WPA --format pdf --scratch qr/wifi-run1 --file-name wifi-qr
  python make_qr.py --url contoso.com --logo logo.png --style rounded --fg "#0B3D91" --format png,svg,pdf --scratch qr/brand-run1 --file-name brand-qr
  python make_qr.py --batch people.csv --data-column url --name-column name --format png --scratch qr/batch-run1
"""
import argparse, re, base64, csv, io, json, math, os, sys, tempfile
import gzip
from urllib.parse import unquote_to_bytes
from datetime import datetime
from urllib.parse import quote
from urllib.parse import urlsplit

class QRError(Exception):
    """A user-fixable problem. Printed as JSON {"error": code, "message": ...} on stdout, exit code 2."""
    def __init__(self, code, message):
        super().__init__(message); self.code = code; self.message = message

try:
    from PIL import Image, ImageDraw, ImageColor, ImageFont
except ImportError:  # Pillow is the one hard requirement
    print(json.dumps({"error": "missing_pillow", "message": "Pillow (PIL) is not installed in this environment, so QR images cannot be drawn."}))
    sys.exit(2)

ENCODER = None
try:
    from reportlab.graphics.barcode import qrencoder
    ENCODER = "reportlab"
except ImportError:
    try:
        import qrcode as _qrcode
        ENCODER = "qrcode"
    except ImportError:
        try:
            import segno as _segno
            ENCODER = "segno"
        except ImportError:
            ENCODER = None
try:
    import reportlab  # noqa: F401  (vector PDF)
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

EC_LEVELS = ["L", "M", "Q", "H"]
RASTER = {"png", "jpg", "jpeg", "webp"}
VECTOR = {"svg", "pdf"}

# ---------- payload builders ----------
def _esc(s):  # escaping for WIFI: payload fields (\ ; , : ")
    return "".join("\\" + c if c in '\\;,:"' else c for c in (s or ""))

def _vtext(s):
    """vCard 3.0 / iCalendar TEXT escaping: backslash, semicolon, comma, and newlines -> \\n."""
    s = (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return s.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")

def _oneline(s):
    """Non-TEXT single-line values (phone, email, URL). Line breaks are rejected in validate_fields(),
    so they can never start a new vCard field; this only trims surrounding spaces."""
    return (s or "").strip()

TYPE_LABELS = {"text": "plain-text", "wifi": "Wi-Fi", "vcard": "contact card", "email": "email",
               "phone": "phone-call", "sms": "text-message", "geo": "map-location", "event": "calendar-event"}

FIELD_LABELS = {"text": "the text", "ssid": "the Wi-Fi network name", "password": "the Wi-Fi password",  # nosec B105 - a field label, not a password
                "name": "the contact's name", "email": "the email address", "phone": "the phone number",
                "lat": "the latitude", "lon": "the longitude", "summary": "the event title",
                "start": "the event start time", "end": "the event end time"}

REQUIRED_FIELDS = {"text": ["text"], "wifi": ["ssid"], "vcard": ["name"], "email": ["email"],
                   "phone": ["phone"], "sms": ["phone"], "geo": ["lat", "lon"],
                   "event": ["summary", "start", "end"]}

def parse_event_time(raw, label):
    """Return (datetime, kind, utc) for an iCalendar DATE (20261015) or DATE-TIME (20261015T190000[Z]).
    Dashes/colons are allowed (2026-10-15T19:00:00). Impossible dates/times raise invalid_field."""
    v = (raw or "").strip().replace("-", "").replace(":", "")
    utc = v.upper().endswith("Z")
    core = v[:-1] if utc else v
    m = re.fullmatch(r"(\d{8})(?:T(\d{6}))?", core)
    if not m or (utc and not m.group(2)):
        raise QRError("invalid_field", f"The event {label} \"{raw}\" should look like 20261015T190000 (date and time) or 20261015 (all-day).")
    try:
        if m.group(2):
            return datetime.strptime(core, "%Y%m%dT%H%M%S"), "datetime", utc
        return datetime.strptime(core, "%Y%m%d"), "date", False
    except ValueError:
        raise QRError("invalid_field", f"The event {label} \"{raw}\" isn't a real date/time (check the month, day and hour - e.g. 20261015T190000 is 15 Oct 2026, 7:00 pm).")

# Phones understand exactly three WIFI: security types: WPA (covers WPA/WPA2/WPA3-Personal), WEP and nopass.
WIFI_AUTH_ALIASES = {
    "WPA": "WPA", "WPA2": "WPA", "WPA3": "WPA", "WPA/WPA2": "WPA", "WPA2/WPA3": "WPA", "WPA-PSK": "WPA",
    "WPA2-PSK": "WPA", "WPA3-PSK": "WPA", "WPA-PERSONAL": "WPA", "WPA2-PERSONAL": "WPA", "WPA3-PERSONAL": "WPA",
    "SAE": "WPA", "WEP": "WEP", "NOPASS": "nopass", "NONE": "nopass", "OPEN": "nopass",
}
ENTERPRISE_AUTH = ("EAP", "ENTERPRISE", "802.1X", "8021X", "RADIUS", "PEAP", "TTLS", "LEAP")

def _wifi_auth(a):
    raw = (a.auth or "WPA").strip()
    key = re.sub(r"\s+", "", raw).upper()
    if key in WIFI_AUTH_ALIASES:
        return WIFI_AUTH_ALIASES[key]
    if any(tag in key for tag in ENTERPRISE_AUTH):
        raise QRError("invalid_field", f"\"{raw}\" is an enterprise (work/school login) Wi-Fi type. Wi-Fi QR codes only support personal networks: WPA (WPA/WPA2/WPA3), WEP or open (no password).")
    raise QRError("invalid_field", f"\"{raw}\" isn't a Wi-Fi security type QR codes support. Use WPA (for WPA, WPA2 or WPA3), WEP, or nopass for an open network.")

def validate_fields(a):
    """Raise QRError before building a payload if a required field for this code type is missing or malformed."""
    t = a.type
    need = list(REQUIRED_FIELDS.get(t, []))
    if t == "wifi" and _wifi_auth(a) != "nopass":
        need.append("password")
    missing = [f for f in need if not str(getattr(a, f, None) or "").strip()]
    if missing:
        names = " and ".join(FIELD_LABELS.get(f, f) for f in missing)
        flags = ", ".join("--" + f for f in missing)
        raise QRError("missing_field", f"For this {TYPE_LABELS.get(t, t)} QR code I need {names} ({flags}).")
    for f in ("phone", "email", "url"):
        v = getattr(a, f, None) or ""
        if t in ("vcard", "email", "phone", "sms") and re.search(r"[\r\n]", v):
            raise QRError("invalid_field", f"The {f} can't contain line breaks.")
    if t == "vcard" and a.email and (re.search(r"\s", a.email.strip()) or "@" not in a.email):
        raise QRError("invalid_field", f"\"{a.email.strip()}\" doesn't look like an email address.")
    if t == "email" and (re.search(r"\s", a.email.strip()) or "@" not in a.email):
        raise QRError("invalid_field", f"\"{a.email}\" doesn't look like an email address.")
    if t == "geo":
        try:
            lat, lon = float(a.lat), float(a.lon)
        except ValueError:
            raise QRError("invalid_field", "Latitude and longitude must be numbers, e.g. 38.9072 and -77.0369.")
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise QRError("invalid_field", "Latitude must be between -90 and 90, and longitude between -180 and 180.")
    if t == "event":
        start, end = parse_event_time(a.start, "start"), parse_event_time(a.end, "end")
        if start[1] != end[1]:
            raise QRError("invalid_field", "The event start and end must both be all-day dates (20261015) or both be date-and-times (20261015T190000).")
        if start[2] != end[2]:
            raise QRError("invalid_field", "The event start and end must both use UTC (ending in Z) or both use local time - not one of each.")
        if end[0] <= start[0]:
            if start[1] == "date":
                raise QRError("invalid_field", f"The event must end after it starts. For an all-day event the end is the day AFTER the last day (e.g. start {a.start.strip()} -> end the next day).")
            raise QRError("invalid_field", f"The event must end after it starts (start {a.start.strip()}, end {a.end.strip()}).")

def build_payload(a):
    t = a.type
    a._payload_notes = []
    validate_fields(a)
    if t == "url":
        return normalize_url(a.url)
    if t == "text":
        return a.text
    if t == "wifi":
        auth = _wifi_auth(a)
        if auth == "nopass" and (a.password or "").strip():
            a._payload_notes.append("This is an open network, so the password you gave was left out of the code.")
        elif auth == "WPA" and not (8 <= len(a.password) <= 63 or re.fullmatch(r"[0-9A-Fa-f]{64}", a.password)):
            a._payload_notes.append("WPA passwords are normally 8-63 characters - double-check it, or phones won't connect.")
        elif auth == "WEP" and not (len(a.password) in (5, 13) or re.fullmatch(r"[0-9A-Fa-f]{10}|[0-9A-Fa-f]{26}", a.password)):
            a._payload_notes.append("WEP passwords are normally 5 or 13 characters (or 10/26 hex digits) - double-check it, or phones won't connect.")
        if auth == "nopass":
            return f"WIFI:T:nopass;S:{_esc(a.ssid)};{'H:true;' if a.hidden else ''};"
        return f"WIFI:T:{auth};S:{_esc(a.ssid)};P:{_esc(a.password)};{'H:true;' if a.hidden else ''};"
    if t == "vcard":
        full = a.name.strip()
        parts = full.split(" ", 1)
        first, last = parts[0], (parts[1] if len(parts) > 1 else "")
        lines = ["BEGIN:VCARD", "VERSION:3.0", f"N:{_vtext(last)};{_vtext(first)};;;", f"FN:{_vtext(full)}"]
        if a.org: lines.append(f"ORG:{_vtext(a.org)}")
        if a.title: lines.append(f"TITLE:{_vtext(a.title)}")
        if a.phone: lines.append(f"TEL;TYPE=CELL:{_oneline(a.phone)}")
        if a.email: lines.append(f"EMAIL:{_oneline(a.email)}")
        if a.url: lines.append(f"URL:{_oneline(a.url)}")
        if a.address: lines.append(f"ADR:;;{_vtext(a.address)};;;;")
        lines.append("END:VCARD")
        return "\n".join(lines)
    if t == "email":
        q = []
        if a.subject: q.append("subject=" + quote(a.subject))
        if a.body: q.append("body=" + quote(a.body))
        return f"mailto:{a.email.strip()}" + ("?" + "&".join(q) if q else "")
    if t == "phone":
        return f"tel:{_oneline(a.phone)}"
    if t == "sms":
        return f"SMSTO:{_oneline(a.phone)}:{a.body or ''}"
    if t == "geo":
        return f"geo:{float(a.lat)},{float(a.lon)}"
    if t == "event":
        def dt(name, s):
            v = s.strip().replace("-", "").replace(":", "").upper()
            return f"{name};VALUE=DATE:{v}" if "T" not in v else f"{name}:{v}"  # RFC 5545: all-day needs VALUE=DATE
        lines = ["BEGIN:VEVENT", f"SUMMARY:{_vtext(a.summary.strip())}", dt("DTSTART", a.start), dt("DTEND", a.end)]
        if a.location: lines.append(f"LOCATION:{_vtext(a.location)}")
        lines.append("END:VEVENT")
        return "\n".join(lines)
    raise SystemExit(f"Unknown type {t}")

# ---------- encoding (ReportLab) ----------
def encode(data, ec="M"):
    too_long = QRError("too_long", f"Content is too long for one QR code at error-correction {ec} "
                       f"({len(data.encode('utf-8'))} bytes). Shorten it (e.g. use a short link) or remove the logo.")
    if ENCODER is None:
        raise QRError("missing_encoder", "No QR encoder is installed (need ReportLab, qrcode or segno).")
    if ENCODER == "reportlab":
        lv = {"L": qrencoder.QRErrorCorrectLevel.L, "M": qrencoder.QRErrorCorrectLevel.M,
              "Q": qrencoder.QRErrorCorrectLevel.Q, "H": qrencoder.QRErrorCorrectLevel.H}[ec]
        q = qrencoder.QRCode(None, lv); q.addData(data)
        try:
            q.make()
        except Exception:
            raise too_long
        n = q.getModuleCount()
        return [[bool(q.isDark(r, c)) for c in range(n)] for r in range(n)], q.version
    if ENCODER == "qrcode":
        lv = {"L": _qrcode.constants.ERROR_CORRECT_L, "M": _qrcode.constants.ERROR_CORRECT_M,
              "Q": _qrcode.constants.ERROR_CORRECT_Q, "H": _qrcode.constants.ERROR_CORRECT_H}[ec]
        q = _qrcode.QRCode(version=None, error_correction=lv, border=0); q.add_data(data)
        try:
            q.make(fit=True)
        except Exception:
            raise too_long
        return [[bool(v) for v in row] for row in q.get_matrix()], q.version
    try:
        q = _segno.make(data, error=ec.lower(), boost_error=False, micro=False)
    except Exception:
        raise too_long
    return [[bool(v) for v in row] for row in q.matrix], q.version

def is_finder(r, c, n):
    return (r < 7 and c < 7) or (r < 7 and c >= n - 7) or (r >= n - 7 and c < 7)

# ---------- raster (Pillow) ----------
def _rgba(color):
    if color in (None, "transparent", "none"):
        return (255, 255, 255, 0)
    return ImageColor.getcolor(color, "RGBA")

# ---------- raster styling (Pillow) ----------
BODY_SHAPES = ["square", "rounded", "dots", "diamond", "fluid", "vertical-bars", "horizontal-bars", "small-squares"]
EYE_FRAMES = ["square", "rounded", "extra-rounded", "circle", "leaf"]
EYE_CENTERS = ["square", "rounded", "circle", "diamond", "leaf"]
FRAMES = ["none", "box", "rounded-box", "banner"]
SS = 4  # supersampling factor for smooth curves
MAX_CANVAS = 6000  # max supersampled canvas edge in px (a 1000 px code keeps the full 4x)

def _finder_origins(n):
    return [(0, 0), (0, n - 7), (n - 7, 0)]

def _leaf_corners(idx):
    # (top_left, top_right, bottom_right, bottom_left); leaf points away from the code centre
    return [(True, False, True, False), (False, True, False, True), (False, True, False, True)][idx]

def _shape(d, box, kind, fill, idx=0):
    x0, y0, x1, y1 = box
    w = x1 - x0
    if kind == "square":
        d.rectangle(box, fill=fill)
    elif kind == "rounded":
        d.rounded_rectangle(box, radius=w * 0.25, fill=fill)
    elif kind == "extra-rounded":
        d.rounded_rectangle(box, radius=w * 0.42, fill=fill)
    elif kind == "circle":
        d.ellipse(box, fill=fill)
    elif kind == "leaf":
        try:
            d.rounded_rectangle(box, radius=w * 0.45, fill=fill, corners=_leaf_corners(idx))
        except TypeError:  # older Pillow without per-corner rounding
            d.rounded_rectangle(box, radius=w * 0.3, fill=fill)
    elif kind == "diamond":
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        d.polygon([(cx, y0), (x1, cy), (cx, y1), (x0, cy)], fill=fill)
    else:
        raise SystemExit(f"Unknown shape {kind}")

def render_code(m, size, border, fg, bg, body, eye_frame, eye_center, eye_color, logo, logo_scale):
    n = len(m); total = n + 2 * border
    box = max(1, size // total)
    ss = max(1, min(SS, MAX_CANVAS // max(1, box * total)))  # keep the supersampled canvas memory-bounded
    b = box * ss; px = b * total
    bgc = _rgba(bg); fgc = _rgba(fg); eyec = _rgba(eye_color or fg)
    img = Image.new("RGBA", (px, px), bgc)
    d = ImageDraw.Draw(img)
    def in_f(r, c): return is_finder(r, c, n)
    def dark(r, c): return 0 <= r < n and 0 <= c < n and m[r][c] and not in_f(r, c)
    for r in range(n):
        for c in range(n):
            if not dark(r, c):
                continue
            x0, y0 = (c + border) * b, (r + border) * b
            x1, y1 = x0 + b - 1, y0 + b - 1
            if body == "square":
                d.rectangle([x0, y0, x1, y1], fill=fgc)
            elif body == "rounded":
                i = b * 0.04; d.rounded_rectangle([x0 + i, y0 + i, x1 - i, y1 - i], radius=b * 0.3, fill=fgc)
            elif body == "dots":
                i = b * 0.06; d.ellipse([x0 + i, y0 + i, x1 - i, y1 - i], fill=fgc)
            elif body == "diamond":
                cx, cy = x0 + b / 2, y0 + b / 2; h = b * 0.56
                d.polygon([(cx, cy - h), (cx + h, cy), (cx, cy + h), (cx - h, cy)], fill=fgc)
            elif body == "small-squares":
                i = b * 0.12; d.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], fill=fgc)
            elif body == "fluid":
                d.ellipse([x0, y0, x1, y1], fill=fgc)
                if dark(r, c + 1): d.rectangle([x0 + b / 2, y0, x1 + b / 2, y1], fill=fgc)
                if dark(r + 1, c): d.rectangle([x0, y0 + b / 2, x1, y1 + b / 2], fill=fgc)
            elif body == "vertical-bars":
                i = b * 0.1; d.ellipse([x0 + i, y0 + i, x1 - i, y1 - i], fill=fgc)
                if dark(r + 1, c): d.rectangle([x0 + i, y0 + b / 2, x1 - i, y1 + b / 2], fill=fgc)
            elif body == "horizontal-bars":
                i = b * 0.1; d.ellipse([x0 + i, y0 + i, x1 - i, y1 - i], fill=fgc)
                if dark(r, c + 1): d.rectangle([x0 + b / 2, y0 + i, x1 + b / 2, y1 - i], fill=fgc)
            else:
                raise SystemExit(f"Unknown body shape {body}")
    hole = bgc if bgc[3] else (0, 0, 0, 0)
    for idx, (fr, fc) in enumerate(_finder_origins(n)):
        x0, y0 = (fc + border) * b, (fr + border) * b
        _shape(d, [x0, y0, x0 + 7 * b - 1, y0 + 7 * b - 1], eye_frame, eyec, idx)
        _shape(d, [x0 + b, y0 + b, x0 + 6 * b - 1, y0 + 6 * b - 1], eye_frame, hole, idx)
        _shape(d, [x0 + 2 * b, y0 + 2 * b, x0 + 5 * b - 1, y0 + 5 * b - 1], eye_center, eyec, idx)
    if logo:
        lg = Image.open(logo).convert("RGBA")
        target = int(n * b * logo_scale)
        k = target / max(lg.width, lg.height)  # scale up OR down to the requested size
        lg = lg.resize((max(1, int(lg.width * k)), max(1, int(lg.height * k))), Image.LANCZOS)
        pad = max(4 * ss, b)
        cx = cy = px // 2
        plate = [cx - lg.width // 2 - pad, cy - lg.height // 2 - pad, cx + lg.width // 2 + pad, cy + lg.height // 2 + pad]
        d.rounded_rectangle(plate, radius=pad, fill=bgc if bgc[3] else (255, 255, 255, 255))
        img.alpha_composite(lg, (cx - lg.width // 2, cy - lg.height // 2))
    return img.resize((box * total, box * total), Image.LANCZOS)

FONT_CANDIDATES = ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                   "Arial Bold.ttf", "arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf")

def _font(sz):
    for f in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=sz)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()

def _wrap(text, fits):
    """Greedy word wrap; words longer than a whole line are broken by characters."""
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if fits(cand):
            cur = cand; continue
        if cur:
            lines.append(cur); cur = ""
        while not fits(word) and len(word) > 1:
            k = len(word)
            while k > 1 and not fits(word[:k]): k -= 1
            lines.append(word[:k]); word = word[k:]
        cur = word
    if cur: lines.append(cur)
    return lines or [text]

def decorate(code, fg, bg, frame, frame_text, caption, frame_color=None, notes=None):
    """Optional outer frame around the code, plus optional caption (shrunk, then wrapped, to fit - never clipped).
    `notes` (a list) collects user-facing warnings."""
    notes = notes if notes is not None else []
    W = code.width; fgc = _rgba(fg); bgc = _rgba(bg); fc = _rgba(frame_color or fg)
    solid_bg = bgc if bgc[3] else (255, 255, 255, 255)
    img = code
    if frame != "none":
        t = max(6, W // 45); pad = t * 2
        banner_h = int(W * 0.16) if frame == "banner" else 0
        out = Image.new("RGBA", (W + 2 * (pad + t), W + 2 * (pad + t) + banner_h), bgc)
        d = ImageDraw.Draw(out)
        rect = [0, 0, out.width - 1, out.height - 1]
        r = 0 if frame == "box" else W // 12
        d.rounded_rectangle(rect, radius=r, fill=fc)
        inner_bottom = (W + 2 * pad + t - 1) if banner_h else (out.height - 1 - t)
        d.rounded_rectangle([t, t, out.width - 1 - t, inner_bottom], radius=max(0, r - t), fill=solid_bg)
        out.alpha_composite(code, (t + pad, t + pad))
        if banner_h:
            txt = (frame_text or "SCAN ME").upper(); fs = int(banner_h * 0.5); f = _font(fs)
            while d.textlength(txt, font=f) > out.width * 0.85 and fs > 10:
                fs -= 2; f = _font(fs)
            tw = d.textlength(txt, font=f)
            if tw > out.width * 0.95:
                notes.append("The banner text is too long to fit the banner and is cut off at the edges - shorten it (e.g. \"SCAN ME\").")
            d.text(((out.width - tw) / 2, W + 2 * pad + t + (banner_h - fs) / 2 - fs * 0.1), txt, fill=solid_bg, font=f)
        img = out
    if caption:
        probe = ImageDraw.Draw(img); max_w = img.width * 0.92
        cap_size = max(12, W // 18); min_size = max(12, W // 36); f = _font(cap_size)
        while probe.textlength(caption, font=f) > max_w and cap_size > min_size:
            cap_size = max(min_size, cap_size - 2); f = _font(cap_size)
        lines = [caption]
        if probe.textlength(caption, font=f) > max_w:
            lines = _wrap(caption, lambda t: probe.textlength(t, font=f) <= max_w)
        if len(lines) > 1:
            notes.append(f"The caption is too long for one line, so it's shown smaller on {len(lines)} lines - consider shortening it.")
        line_h = int(cap_size * 1.25)
        cap_h = int(cap_size * 1.8) + line_h * (len(lines) - 1)
        canvas = Image.new("RGBA", (img.width, img.height + cap_h), bgc)
        canvas.alpha_composite(img, (0, 0))
        dd = ImageDraw.Draw(canvas)
        for k, line in enumerate(lines):
            w = dd.textlength(line, font=f)
            dd.text(((img.width - w) / 2, img.height + cap_h * 0.15 if len(lines) == 1 else img.height + cap_size * 0.27 + k * line_h), line, fill=fgc, font=f)
        img = canvas
    return img

LOGO_SIZES = {"small": 0.15, "medium": 0.22, "large": 0.28}

def color_from_logo(path):
    """Pick the most common DARK colour in the logo (ignoring transparent/near-white/near-grey pixels)
    so the code matches the brand but keeps strong contrast on white."""
    im = Image.open(path).convert("RGBA"); im.thumbnail((200, 200))
    q = im.convert("RGB").quantize(colors=12, method=getattr(getattr(Image, "Quantize", None), "MEDIANCUT", 0))
    pal = q.getpalette(); alpha = im.split()[3].load(); qp = q.load(); counts = {}
    for y in range(im.height):
        for x in range(im.width):
            if alpha[x, y] < 128: continue
            i = qp[x, y]; counts[i] = counts.get(i, 0) + 1
    if not counts:
        raise QRError("logo_unreadable", f"The logo \"{os.path.basename(path)}\" has no visible pixels (it's fully transparent), so its color can't be matched. Pick a color instead, or use a different logo.")
    best = None
    for i, _count in sorted(counts.items(), key=lambda kv: -kv[1]):
        r, g, b = pal[3 * i:3 * i + 3]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum < 110:  # dark enough to scan on white
            best = (r, g, b); break
    if best is None:  # logo has no dark colour: darken its main colour
        i = max(counts, key=counts.get); r, g, b = pal[3 * i:3 * i + 3]
        f = 90 / max(1, 0.2126 * r + 0.7152 * g + 0.0722 * b); best = tuple(int(v * f) for v in (r, g, b))
    return "#%02X%02X%02X" % best

EC_CAPACITY = {"L": 7, "M": 15, "Q": 25, "H": 30}

def readback_check(code, m, size, border, ec):
    """Sample the rendered code at every data-module centre (finder eyes excluded - their shape is
    styled on purpose) and compare with the intended matrix. An ESTIMATE, not a real scanner."""
    n = len(m); total = n + 2 * border; box = max(1, size // total)
    g = Image.new("RGB", code.size, (255, 255, 255)); g.paste(code, mask=code.split()[3]); g = g.convert("L")
    px = g.load(); bad = 0; cnt = 0
    for r in range(n):
        for c in range(n):
            if is_finder(r, c, n): continue
            cnt += 1
            x = (c + border) * box + box // 2; y = (r + border) * box + box // 2
            if (px[x, y] < 128) != m[r][c]: bad += 1
    pct = 100.0 * bad / cnt; cap = EC_CAPACITY[ec]
    verdict = "good" if pct <= cap * 0.5 else ("risky" if pct <= cap * 0.8 else "likely to fail")
    return {"modules_obscured_pct": round(pct, 1), "error_correction_budget_pct": cap, "verdict": verdict}

def save_raster(img, path, fmt, bg):
    if fmt in ("jpg", "jpeg"):
        base = Image.new("RGB", img.size, _rgba(bg)[:3] if _rgba(bg)[3] else (255, 255, 255))
        base.paste(img, mask=img.split()[3])
        base.save(path, "JPEG", quality=95)
    elif fmt == "webp":
        img.save(path, "WEBP", lossless=True)
    else:
        img.save(path, "PNG")

# ---------- vector (ReportLab PDF, hand-built SVG) ----------
def _hex(color):
    """Normalize any Pillow-accepted color (name, #abc, rgb(), hsl()) to #RRGGBB, so the colors that pass
    check_color() are exactly the colors ReportLab and SVG render (ReportLab lacks some CSS names and
    reads 3-digit hex differently)."""
    r, g, b = ImageColor.getrgb(color)[:3]
    return "#%02X%02X%02X" % (r, g, b)

def _transparent(color):
    return color in (None, "transparent", "none")

def render_svg(m, border, fg, bg, logo, logo_scale, path, size):
    n = len(m); total = n + 2 * border
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total} {total}" width="{size}" height="{size}" shape-rendering="crispEdges">']
    if not _transparent(bg):
        out.append(f'<rect width="{total}" height="{total}" fill="{_hex(bg)}"/>')
    d = "".join(f"M{c+border},{r+border}h1v1h-1z" for r in range(n) for c in range(n) if m[r][c])
    out.append(f'<path d="{d}" fill="{_hex(fg)}"/>')
    if logo:
        buf = io.BytesIO(); lg = Image.open(logo).convert("RGBA"); lg.save(buf, "PNG")
        k = (n * logo_scale) / max(lg.width, lg.height)  # longest side = logo_scale of the code (matches raster)
        w, h = lg.width * k, lg.height * k; x, y = total / 2 - w / 2, total / 2 - h / 2
        plate = "#FFFFFF" if _transparent(bg) else _hex(bg)
        out.append(f'<rect x="{x-0.6:.3f}" y="{y-0.6:.3f}" width="{w+1.2:.3f}" height="{h+1.2:.3f}" rx="0.6" fill="{plate}"/>')
        out.append(f'<image x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" href="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')
    out.append("</svg>")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(out))

def render_pdf(m, border, fg, bg, logo, logo_scale, path, size_pts, caption, notes=None):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth
    n = len(m); total = n + 2 * border; u = size_pts / total
    cap_lines, cap_fs = [], 14.0
    if caption:
        max_w = size_pts * 0.92
        while stringWidth(caption, "Helvetica-Bold", cap_fs) > max_w and cap_fs > 8:
            cap_fs -= 0.5
        cap_lines = [caption] if stringWidth(caption, "Helvetica-Bold", cap_fs) <= max_w else \
            _wrap(caption, lambda t: stringWidth(t, "Helvetica-Bold", cap_fs) <= max_w)
    cap_h = 0 if not caption else (28 if len(cap_lines) == 1 and cap_fs == 14.0 else cap_fs * 1.25 * len(cap_lines) + 12)
    c = canvas.Canvas(path, pagesize=(size_pts, size_pts + cap_h))
    if not _transparent(bg):
        c.setFillColor(HexColor(_hex(bg))); c.rect(0, 0, size_pts, size_pts + cap_h, stroke=0, fill=1)
    c.setFillColor(HexColor(_hex(fg)))
    for r in range(n):
        for col in range(n):
            if m[r][col]:
                c.rect((col + border) * u, cap_h + (total - border - r - 1) * u, u, u, stroke=0, fill=1)
    if logo:
        lg = Image.open(logo).convert("RGBA")
        k = (n * u * logo_scale) / max(lg.width, lg.height)  # longest side = logo_scale of the code (matches raster)
        w, h = lg.width * k, lg.height * k
        x, y = size_pts / 2 - w / 2, cap_h + size_pts / 2 - h / 2
        c.setFillColor(white if _transparent(bg) else HexColor(_hex(bg)))
        c.roundRect(x - u, y - u, w + 2 * u, h + 2 * u, u, stroke=0, fill=1)
        c.drawImage(ImageReader(lg), x, y, w, h, mask="auto")
    if caption:
        c.setFillColor(HexColor(_hex(fg))); c.setFont("Helvetica-Bold", cap_fs)
        for k, line in enumerate(cap_lines):  # first line on top
            c.drawCentredString(size_pts / 2, 10 + (len(cap_lines) - 1 - k) * cap_fs * 1.25, line)
    c.save()

def render_pdf_pillow(m, border, fg, bg, logo, logo_scale, path, size_pts, caption, notes=None):
    """PDF without ReportLab: a 300-dpi raster of the plain square code placed on a PDF page."""
    px = int(size_pts / 72 * 300)
    code = render_code(m, px, border, fg, bg if bg not in ("transparent", "none") else "#FFFFFF",
                       "square", "square", "square", None, logo, logo_scale)
    img = decorate(code, fg, bg if bg not in ("transparent", "none") else "#FFFFFF", "none", None, caption, None, notes)
    img.convert("RGB").save(path, "PDF", resolution=300.0)

# ---------- verification (optional real decode) ----------
def decode_check(path, expected):
    """Decode the rendered image with any QR reader that happens to be installed. None if no reader."""
    try:
        import zxingcpp
        res = zxingcpp.read_barcodes(Image.open(path).convert("RGB"))
        got = res[0].text if res else None
        return {"engine": "zxing-cpp", "decoded": got is not None, "matches_content": got == expected}
    except ImportError:
        pass
    except Exception as e:
        return {"engine": "zxing-cpp", "decoded": False, "matches_content": False, "note": str(e)[:120]}
    try:
        import cv2, numpy as np
        img = np.array(Image.open(path).convert("RGB"))[:, :, ::-1]
        got, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        return {"engine": "opencv", "decoded": bool(got), "matches_content": got == expected}
    except ImportError:
        pass
    except Exception as e:
        return {"engine": "opencv", "decoded": False, "matches_content": False, "note": str(e)[:120]}
    try:
        from pyzbar.pyzbar import decode as zbar
        res = zbar(Image.open(path)); got = res[0].data.decode("utf-8") if res else None
        return {"engine": "pyzbar", "decoded": got is not None, "matches_content": got == expected}
    except ImportError:
        return None
    except Exception as e:
        return {"engine": "pyzbar", "decoded": False, "matches_content": False, "note": str(e)[:120]}

def environment_report():
    def has(mod):
        try:
            __import__(mod); return True
        except Exception:
            return False
    import PIL
    readers = [n for n, mod in (("zxing-cpp", "zxingcpp"), ("opencv", "cv2"), ("pyzbar", "pyzbar")) if has(mod)]
    font_ok = any(_try_font(f) for f in FONT_CANDIDATES)
    return {"ok": ENCODER is not None, "encoder": ENCODER, "pillow": PIL.__version__,
            "vector_pdf": HAS_REPORTLAB, "pdf": "vector" if HAS_REPORTLAB else "raster (Pillow)",
            "scan_verifier": readers[0] if readers else None, "truetype_font": font_ok,
            "styles": {"body": BODY_SHAPES, "eye_frame": EYE_FRAMES, "eye_center": EYE_CENTERS, "frame": FRAMES}}

def _try_font(f):
    try:
        ImageFont.truetype(f, 12); return True
    except OSError:
        return False

# ---------- input validation ----------
def normalize_url(raw):
    u = (raw or "").strip()
    if not u:
        raise QRError("missing_url", "A web address is required.")
    if any(ch.isspace() for ch in u):
        raise QRError("invalid_url", f"The web address \"{u}\" contains a space, so the code would open a broken link. Check the address and try again.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in u):
        raise QRError("invalid_url", "The web address contains hidden control characters. Please retype or re-paste it.")
    if not u.lower().startswith(("http://", "https://")):
        u = "https://" + u
    try:
        parts = urlsplit(u)
        host, port = parts.hostname or "", parts.port  # .port raises ValueError for out-of-range / non-numeric ports
    except ValueError:
        raise QRError("invalid_url", f"\"{raw}\" isn't a valid web address (the part after https:// is malformed). Check it and try again.")
    if port == 0:
        raise QRError("invalid_url", f"\"{raw}\" has an invalid port number (:0).")
    if "." not in host and host != "localhost":
        raise QRError("invalid_url", f"\"{raw}\" doesn't look like a web address (expected something like contoso.com).")
    return u

def check_color(name, value):
    if value in (None, "transparent", "none") or str(value).lower() == "logo":
        return
    try:
        ImageColor.getcolor(value, "RGBA")
    except ValueError:
        raise QRError("bad_color", f"\"{value}\" isn't a color I recognize for {name}. Use a hex code like #5C3A21 or a basic name like navy.")

def _fully_load(path):
    """verify() only checks headers; a full decode also catches truncated or corrupt image data."""
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        im.load()

MAX_SVG_BYTES = 2 * 1024 * 1024
_SVG_REF = re.compile(r"""(?:\b(?:xlink:)?href|\bsrc)\s*=\s*(["'])(.*?)\1|url\(\s*(["']?)(.*?)\3\s*\)|@import\s+(["'])(.*?)\5""", re.I | re.S)

_INLINE_RASTER = re.compile(r"data:image/(png|jpe?g|gif|webp)[;,]", re.I)  # inline bitmaps only - no nested SVG

def _svg_ref_allowed(ref):
    ref = ref.strip()
    return ref == "" or ref.startswith("#") or bool(_INLINE_RASTER.match(ref))

def read_safe_svg(path, name):
    """Read an SVG logo and refuse anything that could make the renderer reach outside the file:
    DOCTYPE/ENTITY declarations (XXE, entity bombs) and any href/src/url()/@import that isn't an internal
    #fragment or an inline data: URI (http(s), file:, //host, relative paths...)."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_SVG_BYTES + 1)
        if raw[:2] == b"\x1f\x8b":  # .svgz (gzip)
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
                raw = gz.read(MAX_SVG_BYTES + 1)
    except (OSError, EOFError):
        raise QRError("logo_unreadable", f"The SVG logo \"{name}\" couldn't be read. Please attach the logo as a PNG or JPG instead.")
    if len(raw) > MAX_SVG_BYTES:
        raise QRError("logo_unreadable", f"The SVG logo \"{name}\" is too large (over 2 MB). Please attach the logo as a PNG or JPG instead.")
    text = raw.decode("utf-8", errors="replace")
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", text, re.I):
        raise QRError("logo_unreadable", f"The SVG logo \"{name}\" contains document-type declarations that aren't allowed. Please attach the logo as a PNG or JPG instead.")
    for m_ in _SVG_REF.finditer(text):
        ref = next(g for g in (m_.group(2), m_.group(4), m_.group(6)) if g is not None)
        if not _svg_ref_allowed(ref):
            raise QRError("logo_unreadable", f"The SVG logo \"{name}\" links to outside files or web addresses, which isn't allowed. Please attach the logo as a PNG or JPG instead.")
    return raw

def _svg_fetch_inline_only(url, *args, **kwargs):
    """cairosvg url_fetcher: decode inline bitmap data: URIs locally; refuse everything else (network, files, nested SVG).
    Returns raw BYTES - CairoSVG's own fetchers (cairosvg.url.fetch / safe_fetch) return bytes and its image
    loader sniffs those bytes (PNG/JPEG/GIF/WEBP signature). The dict form (string/file_obj/mime_type) is
    WeasyPrint's url_fetcher API, not CairoSVG's."""
    url = str(url).strip()
    if not _INLINE_RASTER.match(url) or "," not in url:
        raise ValueError("external resource blocked")
    meta, payload = url.split(",", 1)  # decode the data: URI locally - no URL opener, no network, no files
    if meta.lower().endswith(";base64"):
        return base64.b64decode(unquote_to_bytes(payload), validate=False)
    return unquote_to_bytes(payload)

def check_logo(path):
    if not os.path.isfile(path):
        raise QRError("logo_not_found", f"I couldn't find the logo file \"{path}\".")
    name = os.path.basename(path)
    if path.lower().endswith((".svg", ".svgz")):
        svg_bytes = read_safe_svg(path, name)  # refuses external references, DOCTYPE/entities and oversize files
        try:
            import cairosvg
        except (ImportError, OSError):  # OSError: cairosvg installed but the Cairo system library is missing
            raise QRError("logo_svg", "SVG logos can't be read here. Please attach the logo as a PNG (preferably with a transparent background) or JPG.")
        # Convert into a private temp folder - never next to the upload, which may be read-only or hold a same-named file.
        try:
            png = os.path.join(tempfile.mkdtemp(prefix="qr_logo_"), os.path.splitext(name)[0] + ".png")
            # bytestring (no base URL) + unsafe=False + a fetcher that only decodes inline data: URIs, so nothing is
            # ever loaded from the network or the local disk while rendering.
            cairosvg.svg2png(bytestring=svg_bytes, write_to=png, output_width=800, unsafe=False, url_fetcher=_svg_fetch_inline_only)
            _fully_load(png)
        except TypeError:  # an old cairosvg without url_fetcher: can't guarantee no external loading -> refuse
            raise QRError("logo_svg", "SVG logos can't be converted safely here. Please attach the logo as a PNG (preferably with a transparent background) or JPG.")
        except Exception:  # malformed/unsupported SVG, blocked resource, unwritable temp, or an unreadable result
            raise QRError("logo_unreadable", f"The SVG logo \"{name}\" couldn't be converted to an image. Please attach the logo as a PNG or JPG instead.")
        return png
    try:
        _fully_load(path)
    except Exception:
        raise QRError("logo_unreadable", f"The logo \"{name}\" couldn't be opened as an image (it may be damaged or not an image). Please attach a PNG or JPG.")
    return path

UNSUPPORTED_GLYPH_START = 0x2E80  # CJK and later blocks are missing from the bundled fonts

def glyph_warning(label, text):
    if text and any(ord(ch) >= UNSUPPORTED_GLYPH_START for ch in text):
        return [f"The {label} contains characters (e.g. Chinese/Japanese/Korean or emoji) that may show as empty boxes - consider Latin text."]
    return []

def pad_to_size(img, size, bg):
    """Squares must be whole pixels, so the drawn code can be a few px under the requested size.
    Add the difference as extra quiet-zone margin (never stretch - that would blur the squares)."""
    if img.width >= size:
        return img
    out = Image.new("RGBA", (size, size), _rgba(bg))
    off = (size - img.width) // 2
    out.alpha_composite(img, (off, off))
    return out

def mask_secrets(payload):
    """Hide a Wi-Fi password in the JSON report (the QR code itself keeps the real password)."""
    if payload.upper().startswith("WIFI:"):
        return re.sub(r"(P:)((?:\\.|[^;])*)", lambda m_: m_.group(1) + ("********" if m_.group(2) else ""), payload)
    return payload

# ---------- output-path safety ----------
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}

def safe_file_name(raw, default="qr"):
    """Reduce a requested file name to a safe base name: letters, digits, '.', '-', '_' only. Slashes, '..',
    drive letters and other path syntax can't survive, so the name can never point outside --scratch."""
    s = "".join(ch if (ch.isalnum() and ord(ch) < 0x2E80) or ch in ".-_" else "_" for ch in (raw or ""))
    s = re.sub(r"\.{2,}", ".", s)
    s = re.sub(r"_{2,}", "_", s).strip("._- ")
    while True:  # drop a format extension the caller may have added (x.png -> x)
        stem, ext = os.path.splitext(s)
        if ext.lower().lstrip(".") in RASTER | VECTOR | {"jpeg"} and stem:
            s = stem.rstrip("._- ")
        else:
            break
    s = s[:80].rstrip("._- ")
    if not s:
        s = default
    if s.split(".")[0].upper() in RESERVED_NAMES:
        s = "qr_" + s
    return s

def safe_file_name_ext_only(raw):
    """The requested name with only a trailing format extension removed (used to decide whether to warn)."""
    s = (raw or "").strip()
    while True:
        stem, ext = os.path.splitext(s)
        if ext.lower().lstrip(".") in RASTER | VECTOR | {"jpeg"} and stem:
            s = stem
        else:
            return s

def _inside(child, parent):
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:  # different drives (Windows)
        return False

def prepare_scratch(raw):
    """Validate --scratch and return its resolved path. It must be a new or EMPTY folder inside the current
    working directory, reached without '..' segments or links that lead elsewhere."""
    if not raw or not str(raw).strip():
        raise QRError("bad_scratch", "No scratch folder was given (--scratch).")
    raw = str(raw).strip()
    if any(seg == ".." for seg in re.split(r"[\\/]+", raw)):
        raise QRError("bad_scratch", f"The scratch folder \"{raw}\" contains \"..\". Use a plain new folder such as qr/contoso-run1.")
    base = os.path.realpath(os.getcwd())
    real = os.path.realpath(raw)
    if real == base or not _inside(real, base):
        raise QRError("bad_scratch", f"The scratch folder \"{raw}\" must be a sub-folder of the working folder (e.g. qr/contoso-run1).")
    if os.path.lexists(raw):
        if os.path.islink(raw) or not os.path.isdir(raw):
            raise QRError("bad_scratch", f"\"{raw}\" isn't a plain folder. Use a new folder name.")
        if os.listdir(raw):
            raise QRError("scratch_not_empty", f"The scratch folder \"{raw}\" already has files in it. Use a NEW folder for every run (e.g. ...-run2) so old QR files can't be delivered by mistake.")
    else:
        try:
            os.makedirs(raw)
        except OSError as e:
            raise QRError("cannot_write", f"I couldn't create the scratch folder \"{raw}\" ({e.strerror or e}).")
        if os.path.realpath(raw) != real or not _inside(os.path.realpath(raw), base):
            raise QRError("bad_scratch", f"The scratch folder \"{raw}\" resolves outside the working folder.")
    return real

def safe_target(scratch_real, file_name):
    """Absolute path for file_name inside scratch_real; refuse anything that would land elsewhere or overwrite."""
    if os.path.basename(file_name) != file_name or file_name in ("", ".", ".."):
        raise QRError("bad_scratch", f"Refusing unsafe file name \"{file_name}\".")
    path = os.path.join(scratch_real, file_name)
    if os.path.realpath(os.path.dirname(path)) != scratch_real or not _inside(os.path.realpath(path), scratch_real):
        raise QRError("bad_scratch", f"Refusing to write \"{file_name}\" outside the scratch folder.")
    if os.path.lexists(path):
        raise QRError("scratch_not_empty", f"\"{file_name}\" already exists in the scratch folder - use a new folder for this run.")
    return path

def vector_unsupported(a, fmt):
    """Requested styling options that this vector format does not render (PNG/JPG/WEBP render all of them)."""
    dropped = []
    if a.style != "square": dropped.append(f"body shape ({a.style})")
    if a.eye_frame != "square": dropped.append(f"corner-eye frame ({a.eye_frame})")
    if a.eye_center != "square": dropped.append(f"corner-eye center ({a.eye_center})")
    if a.eye_color: dropped.append("corner-eye color")
    if a.frame != "none": dropped.append(f"outer frame ({a.frame})")
    if fmt == "svg" and a.caption: dropped.append("caption")
    return dropped

# ---------- driver ----------
def contrast_warning(fg, bg, label="code"):
    def lum(col):
        r, g, b, a = _rgba(col)
        if a == 0: return 1.0
        f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
    lf, lb = lum(fg), lum(bg)
    warn = []
    if lf > lb: warn.append(f"The {label} color is lighter than the background (inverted) - many scanners fail on inverted codes.")
    ratio = (max(lf, lb) + 0.05) / (min(lf, lb) + 0.05)
    if ratio < 4: warn.append(f"Low contrast for the {label} ({ratio:.1f}:1) - aim for 4:1 or higher.")
    return warn

MIN_MODULE_PX = 4     # smallest square (px) phones scan reliably on screen; also guarantees the image fits --size
MIN_MODULE_PT = 1.0   # smallest printed square in a PDF (1 pt = 0.35 mm)

LIMITS = {"size": (100, 5000, "px"), "pdf_size": (36, 2000, "pt"), "border": (0, 20, "squares"),
          "logo_scale": (0.05, 0.30, "of the code width")}

def check_options(a):
    for key, (lo, hi, unit) in LIMITS.items():
        v = getattr(a, key)
        if key == "logo_scale" and (a.logo_size or not a.logo):
            continue  # --logo-size overrides it; ignored without a logo
        if key == "logo_scale" and v > hi:
            continue  # capped to 0.30 later with a warning (existing behavior)
        if not (lo <= v <= hi):
            raise QRError("bad_option", f"--{key.replace('_', '-')} {v:g} is out of range - use {lo:g} to {hi:g} {unit}.")

def make_one(data, a, scratch_real, file_name):
    ec = a.ec
    warnings = []
    for nm, val in (("the code", a.fg), ("the background", a.bg), ("the corner squares", a.eye_color), ("the frame", a.frame_color)):
        check_color(nm, val)
    if a.logo:
        a.logo = check_logo(a.logo)
    if a.logo_size:
        a.logo_scale = LOGO_SIZES[a.logo_size]
    for attr in ("fg", "eye_color", "frame_color"):
        if (getattr(a, attr) or "").lower() == "logo":
            if not a.logo: raise QRError("no_logo", f"--{attr.replace('_','-')} logo needs --logo (a logo file to take the color from).")
            setattr(a, attr, color_from_logo(a.logo)); warnings.append(f"{attr} taken from logo: {getattr(a, attr)}")
    if a.logo:
        if ec != "H": warnings.append(f"Logo present: error correction raised from {ec} to H.")
        ec = "H"
        if a.logo_scale > 0.30:
            warnings.append("Logo scale capped at 0.30 of the code width to keep it scannable."); a.logo_scale = 0.30
    m, version = encode(data, ec)
    warnings += contrast_warning(a.fg, a.bg)
    if a.eye_color: warnings += contrast_warning(a.eye_color, a.bg, "corner squares")
    if a.frame != "none" and a.frame_color: warnings += contrast_warning(a.frame_color, a.bg, "frame")
    if a.border < 2:
        warnings.append(f"The white margin is only {a.border} square(s) wide - scanners need about 4. Use --border 4 unless the code will sit on a large plain white area.")
    elif a.border < 4:
        warnings.append(f"The white margin is {a.border} squares wide; 4 is the standard. Keep plenty of white space around the code when you place it.")
    warnings += glyph_warning("caption", a.caption) + (glyph_warning("banner text", a.frame_text) if a.frame == "banner" else [])
    fmts = [f.strip().lower() for f in a.format.split(",") if f.strip()]
    bad = [f for f in fmts if f not in RASTER | VECTOR]
    if bad or not fmts:
        raise QRError("bad_format", f"Unsupported format(s): {', '.join(bad) or '(none)'}. Choose from png, jpg, webp, svg, pdf.")
    total = len(m) + 2 * a.border
    if any(f in RASTER or f == "svg" for f in fmts) and a.size // total < MIN_MODULE_PX:
        need = MIN_MODULE_PX * total
        raise QRError("size_too_small", f"--size {a.size} is too small for this much content: each square would be under {MIN_MODULE_PX} px and phones couldn't scan it. Use --size {need} or more (or shorten the content).")
    if "pdf" in fmts and a.pdf_size / total < MIN_MODULE_PT:
        need = math.ceil(MIN_MODULE_PT * total)
        raise QRError("size_too_small", f"--pdf-size {a.pdf_size:g} pt is too small for this much content: each square would be under {MIN_MODULE_PT:g} pt (about 0.35 mm). Use --pdf-size {need} or more (or shorten the content).")
    files = []
    raster_img = None
    readback = None
    try:
        for f in fmts:
            path = safe_target(scratch_real, f"{file_name}.{f}")
            files.append(path)  # recorded before writing so a partial file is cleaned up on failure
            if f in RASTER:
                if raster_img is None:
                    code_img = render_code(m, a.size, a.border, a.fg, a.bg, a.style, a.eye_frame, a.eye_center, a.eye_color, a.logo, a.logo_scale)
                    readback = readback_check(code_img, m, a.size, a.border, ec)
                    code_img = pad_to_size(code_img, a.size, a.bg)
                    raster_img = decorate(code_img, a.fg, a.bg, a.frame, a.frame_text, a.caption, a.frame_color, warnings)
                if f in ("jpg", "jpeg") and a.bg in ("transparent", "none"):
                    warnings.append("JPG cannot be transparent - used white background.")
                save_raster(raster_img, path, f, a.bg)
            elif f == "svg":
                dropped = vector_unsupported(a, "svg")
                if dropped: warnings.append(f"The SVG leaves out: {', '.join(dropped)} - SVG is a plain square code; these apply to PNG/JPG/WEBP.")
                render_svg(m, a.border, a.fg, a.bg, a.logo, a.logo_scale, path, a.size)
            elif f == "pdf":
                dropped = vector_unsupported(a, "pdf")
                if dropped: warnings.append(f"The PDF leaves out: {', '.join(dropped)} - PDF is a plain square code (caption included); these apply to PNG/JPG/WEBP.")
                if HAS_REPORTLAB:
                    render_pdf(m, a.border, a.fg, a.bg, a.logo, a.logo_scale, path, a.pdf_size, a.caption, warnings)
                else:
                    render_pdf_pillow(m, a.border, a.fg, a.bg, a.logo, a.logo_scale, path, a.pdf_size, a.caption, warnings)
                    warnings.append("ReportLab isn't installed here, so the PDF holds a high-resolution (300 dpi) image of the code rather than vector shapes - still fine for printing.")
    except BaseException as e:
        for p in files:  # remove only files THIS run created inside scratch, so no half-finished set is left behind
            try:
                if os.path.lexists(p) and _inside(os.path.realpath(p), scratch_real):
                    os.remove(p)
            except OSError:
                pass
        if isinstance(e, OSError):
            raise QRError("cannot_write", f"I couldn't save the QR code file ({e.strerror or e}). Check that the scratch folder is writable.")
        raise
    rb = readback
    dc = None
    first_raster = next((p for p in files if p.rsplit(".", 1)[-1] in RASTER), None)
    if first_raster:
        dc = decode_check(first_raster, data)
        if dc and not dc.get("matches_content"):
            warnings.append(f"A real scan test with {dc['engine']} could NOT read this code back correctly - simplify the styling, shrink the logo or increase contrast.")
    if rb and rb["verdict"] != "good":
        warnings.append(f"Readback check {rb['verdict']}: {rb['modules_obscured_pct']}% of modules obscured vs {rb['error_correction_budget_pct']}% budget - shrink the logo or simplify styling.")
    return {"payload": mask_secrets(data), "version": version, "readback_check": rb, "scan_verified": dc,
            "modules": len(m), "error_correction": ec, "encoder": ENCODER,
            "files": files, "file_names": [os.path.basename(p) for p in files], "warnings": list(dict.fromkeys(warnings))}

def folder_report(scratch_real, produced):
    """Confirm the scratch folder holds exactly the files this run produced (nothing stale, nothing extra)."""
    on_disk = sorted(os.listdir(scratch_real))
    expected = sorted(os.path.basename(p) for p in produced)
    extra = [f for f in on_disk if f not in expected]
    return {"scratch": scratch_real, "folder_clean": not extra and on_disk == expected, "unexpected_files": extra}

class _JsonArgParser(argparse.ArgumentParser):
    def error(self, message):  # bad/unknown option -> the documented JSON error, not usage text on stderr
        print(json.dumps({"error": "bad_option", "message": f"Invalid option: {message}."}, indent=2))
        sys.exit(2)

def main():
    p = _JsonArgParser()
    p.add_argument("--check", action="store_true", help="report what this environment supports, then exit")
    p.add_argument("--type", default="url", choices=["url", "text", "wifi", "vcard", "email", "phone", "sms", "geo", "event"])
    for k in ["url", "text", "ssid", "password", "auth", "name", "org", "title", "phone", "email", "address",
              "subject", "body", "lat", "lon", "summary", "start", "end", "location"]:
        p.add_argument(f"--{k}")
    p.add_argument("--hidden", action="store_true")
    p.add_argument("--format", default="png", help="comma list: png,jpg,webp,svg,pdf")
    p.add_argument("--scratch", help="NEW or empty folder (inside the working folder) to write into; one per run")
    p.add_argument("--file-name", default="qr", help="base file name; reduced to safe characters, no paths")
    p.add_argument("--size", type=int, default=1000, help="raster pixel width / svg width")
    p.add_argument("--pdf-size", type=float, default=216, help="PDF code width in points (72 = 1 inch)")
    p.add_argument("--border", type=int, default=4)
    p.add_argument("--ec", default="M", choices=EC_LEVELS)
    p.add_argument("--fg", default="#000000", help='hex colour, or "logo" to match the logo\'s main dark colour'); p.add_argument("--bg", default="#FFFFFF")
    p.add_argument("--style", default="square", choices=BODY_SHAPES, help="data-module (body) shape")
    p.add_argument("--eye-frame", default="square", choices=EYE_FRAMES, help="outer ring of the 3 corner eyes")
    p.add_argument("--eye-center", default="square", choices=EYE_CENTERS, help="inner dot of the 3 corner eyes")
    p.add_argument("--eye-color", help="optional separate color for the corner eyes")
    p.add_argument("--frame", default="none", choices=FRAMES, help="optional outer frame around the code")
    p.add_argument("--frame-text", default="SCAN ME", help="text in the banner frame")
    p.add_argument("--frame-color", help="frame color (defaults to --fg)")
    p.add_argument("--logo"); p.add_argument("--logo-scale", type=float, default=0.22)
    p.add_argument("--logo-size", choices=list(LOGO_SIZES), help="small=0.15 (subtle), medium=0.22, large=0.28; overrides --logo-scale")
    p.add_argument("--caption")
    p.add_argument("--batch"); p.add_argument("--data-column", default="data"); p.add_argument("--name-column")
    a = p.parse_args()
    if a.check:
        print(json.dumps(environment_report(), indent=2)); return
    try:
        check_options(a)
        run(a)
    except QRError as e:
        print(json.dumps({"error": e.code, "message": e.message}, indent=2)); sys.exit(2)
    except MemoryError:
        print(json.dumps({"error": "too_large", "message": "Not enough memory to draw a code this large - use a smaller --size."}, indent=2)); sys.exit(2)
    except Exception as e:  # last-resort guard: the caller always gets JSON, never a traceback
        print(json.dumps({"error": "internal_error", "message": "Something unexpected went wrong while making the QR code. Try again with simpler options.",
                          "detail": f"{type(e).__name__}: {str(e)[:200]}"}, indent=2)); sys.exit(2)

# In a web-link batch, cells that already start with one of these are other code types and are encoded as given.
BATCH_RAW_SCHEMES = ("mailto:", "tel:", "wifi:", "smsto:", "geo:", "begin:")

def read_csv_text(path):
    """Decode a CSV the way spreadsheets actually save it: UTF-8 (with or without BOM), else Windows-1252
    (Excel's classic "CSV (Comma delimited)"). Binary / non-text files raise bad_csv."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        raise QRError("batch_not_found", f"I couldn't open the spreadsheet file \"{path}\" ({e.strerror or e}).")
    if b"\x00" in raw:
        raise QRError("bad_csv", "That file isn't a text CSV (it looks like a binary or Excel file). Save the sheet as \"CSV UTF-8 (Comma delimited)\" and upload it again.")
    try:
        return raw.decode("utf-8-sig"), None
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1252"), "The CSV wasn't saved as UTF-8, so it was read as Windows (Excel) text - check that accented names look right."
    except UnicodeDecodeError:
        raise QRError("bad_csv", "The CSV's text encoding couldn't be read. Save the sheet as \"CSV UTF-8 (Comma delimited)\" and upload it again.")

def run(a):
    if a.batch:
        results = []
        if not os.path.isfile(a.batch):
            raise QRError("batch_not_found", f"I couldn't find the spreadsheet file \"{a.batch}\".")
        if a.batch.lower().endswith((".xlsx", ".xlsm", ".xls", ".ods", ".numbers")):
            raise QRError("not_csv", "The QR engine reads CSV files only. Convert the spreadsheet to CSV first, or save it as \"CSV UTF-8 (Comma delimited)\" and upload that.")
        text, enc_note = read_csv_text(a.batch)
        try:
            rows = list(csv.DictReader(io.StringIO(text, newline="")))
            cols = list(csv.DictReader(io.StringIO(text, newline="")).fieldnames or [])
        except csv.Error as e:
            raise QRError("bad_csv", f"The file couldn't be read as a CSV spreadsheet ({e}). Save it as \"CSV UTF-8 (Comma delimited)\" and upload it again.")
        for col in [a.data_column] + ([a.name_column] if a.name_column else []):
            if col not in cols:
                raise QRError("bad_column", f"The spreadsheet has no column named \"{col}\". Its columns are: {', '.join(cols) or '(none)'}.")
        scratch_real = prepare_scratch(a.scratch)
        for i, row in enumerate(rows, 1):
            data = (row.get(a.data_column) or "").strip()
            name = ((row.get(a.name_column) or "") if a.name_column else "").strip()
            if not data:
                results.append({"row": i, "name": name, "error": "missing_data",
                                "message": f"Row {i} has nothing in the \"{a.data_column}\" column, so no QR code was made for it."})
                continue
            # Row number keeps every file name unique (a/b and a?b no longer collide);
            # names that sanitize to nothing fall back to qr_<row>.
            safe = re.sub(r"_+", "_", "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)).strip("_-")[:60]
            safe = f"{safe}_{i:03d}" if safe else f"qr_{i:03d}"
            try:
                if a.type == "url" and not data.lower().startswith(BATCH_RAW_SCHEMES):
                    data = normalize_url(data)  # bare domains AND http(s) links: same checks as a single link
                res = make_one(data, a, scratch_real, safe)
                results.append({"row": i, "name": name, **res})
            except QRError as e:
                results.append({"row": i, "name": name, "error": e.code, "message": e.message})
        ok = sum(1 for r in results if "error" not in r)
        out = {"rows": len(results), "count": ok, "failed": len(results) - ok, "results": results}
        out.update(folder_report(scratch_real, [p for r in results for p in r.get("files", [])]))
        notes = [enc_note] if enc_note else []
        if not out["folder_clean"]:
            notes.append("The scratch folder holds files this run didn't make - deliver only the listed files.")
        if notes: out["warnings"] = notes
        print(json.dumps(out, indent=2))
    else:
        payload = build_payload(a)  # validate inputs before touching the file system
        file_name = safe_file_name(a.file_name)
        scratch_real = prepare_scratch(a.scratch)
        out = make_one(payload, a, scratch_real, file_name)
        out["warnings"] = list(dict.fromkeys(a._payload_notes + out["warnings"]))
        out["file_name"] = file_name
        if file_name != safe_file_name_ext_only(a.file_name):
            out["warnings"].append(f"The file name was changed to \"{file_name}\" (only letters, numbers, '.', '-' and '_' are allowed; no folders).")
        out.update(folder_report(scratch_real, out["files"]))
        if not out["folder_clean"]:
            out["warnings"].append("The scratch folder holds files this run didn't make - deliver only the listed files.")
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
