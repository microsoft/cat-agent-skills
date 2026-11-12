"""Shared helpers for the Work IQ sphere scripts.

Reads ExecuteSql result files and the person's own file activity (files.json), removes duplicate and junk mail,
normalises subjects and fingerprints the source data, so every number and every node on the sphere can be traced back
to ONE person's own data.
"""
import json, os, re, hashlib, unicodedata, urllib.parse, datetime as dt
from collections import Counter

VERSION = '1.8.0'
HERE = os.path.dirname(os.path.abspath(__file__))
GUARD_DATA = os.path.join(HERE, 'guard_data.json')
# the default Copilot experiences on the slide and the sphere (shared by build_workiq.py and fill_slide.py)
DEFAULT_PORTALS = ['Microsoft 365 Copilot', 'Copilot Studio', 'Custom agents and apps']

# ---- windows (version 1.7): a run covers `columns` columns of one unit, a day or a week, from `start` ----
UNITS = ('week', 'day')
PRESETS = ('week', 'month', 'quarter')
DAY_NAMES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
MONTH_NAMES = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
# ---- views (version 1.8): one data collection, three views of it in one sphere
VIEWS = ('week', 'month', 'quarter')            # the toggle's order; the quarter is the base the config is written from
VIEW_NAME = {'week': 'Week', 'month': 'Month', 'quarter': '3 months'}
VIEW_PERIOD = {'week': 'the last 7 days', 'month': 'the last month', 'quarter': 'the last three months'}
CHOICE_RX = re.compile(r'^(?:(week|month|quarter)|last-(\d{1,2})-weeks|since-(\d{4}-\d{2}-\d{2}))$')

def monday(d):
    return d - dt.timedelta(days=d.weekday())

def make_window(unit, start, columns):
    """{'unit', 'start', 'columns', 'end'} (dates; end is exclusive) for `columns` days or weeks from `start`."""
    if unit not in UNITS:
        raise ValueError('the unit must be day or week, not %r' % (unit,))
    start = start if isinstance(start, dt.date) else dt.date.fromisoformat(str(start)[:10])
    columns = int(columns)
    if columns < 1:
        raise ValueError('a window needs at least one column')
    return {'unit': unit, 'start': start, 'columns': columns,
            'end': start + dt.timedelta(days=(1 if unit == 'day' else 7) * columns)}

def preset_window(name, today):
    """week: the last 7 days including today, day by day; month: the 4 full weeks before this week plus this partial
    week; quarter: the 13 full weeks before this week plus this partial week (the 1.6 default)."""
    mon = monday(today)
    if name == 'week':
        return make_window('day', today - dt.timedelta(days=6), 7)
    if name == 'month':
        return make_window('week', mon - dt.timedelta(days=28), 5)
    if name == 'quarter':
        return make_window('week', mon - dt.timedelta(days=91), 14)
    raise ValueError('the window must be week, month or quarter, not %r' % (name,))

def choice_window(choice, today):
    """The window a meta.choices.window value means on `today`: "week", "month", "quarter", "last-<N>-weeks" or
    "since-<YYYY-MM-DD>" (weekly, from the Monday on or before that date). None when it is none of these."""
    m = CHOICE_RX.match(str(choice or '').strip())
    if not m:
        return None
    if m.group(1):
        return preset_window(m.group(1), today)
    mon = monday(today)
    if m.group(2):
        n = int(m.group(2))
        return make_window('week', mon - dt.timedelta(days=7 * n), n + 1) if 1 <= n <= 52 else None
    try:
        start = monday(dt.date.fromisoformat(m.group(3)))
    except ValueError:
        return None
    return make_window('week', start, (mon - start).days // 7 + 1) if start <= mon else None

def column_index(win):
    """Column of an ISO date or time inside the window (None outside it): the day, or the whole week, from start."""
    start, n, day = win['start'], win['columns'], win['unit'] == 'day'
    def col(s):
        try:
            d = dt.date.fromisoformat((s or '')[:10])
        except ValueError:
            return None
        c = (d - start).days if day else (d - start).days // 7
        return c if 0 <= c < n else None
    return col

def column_labels(win):
    """"Thu 15 Oct" for each day of a day-by-day window; "20 Jul" (the Monday) for each week, as 1.6 wrote them."""
    s = win['start']
    if win['unit'] == 'day':
        return ['%s %d %s' % (DAY_NAMES[d.weekday()], d.day, MONTH_NAMES[d.month - 1])
                for d in (s + dt.timedelta(days=i) for i in range(win['columns']))]
    return ['%d %s' % ((s + dt.timedelta(days=7 * i)).day, (s + dt.timedelta(days=7 * i)).strftime('%b')) for i in range(win['columns'])]

def meta_window(meta):
    """(unit, start, columns) recorded in a discovery or signals meta. Day-by-day windows write unit "day" and columns;
    weekly windows keep the 1.6 fields (start and weeks), so a meta without a unit is weekly."""
    m = meta or {}
    return (m.get('unit') or 'week'), m.get('start'), (m.get('columns') if m.get('columns') is not None else m.get('weeks'))

def window_from_meta(meta):
    unit, start, cols = meta_window(meta)
    try:
        return make_window(unit, start, cols)
    except (TypeError, ValueError):
        return None

def window_meta(win):
    """The meta fields that record a window (weekly ones exactly as 1.6 wrote them)."""
    out = {'start': win['start'].isoformat()}
    if win['unit'] == 'week':
        out['weeks'] = win['columns']
    else:
        out['unit'], out['columns'] = win['unit'], win['columns']
    return out

def ahead_end(win, today):
    """End (exclusive) of the look-ahead: a day-by-day window also lists (never counts) the meetings from its end to
    the end of this week; weekly windows already run to the end of this week."""
    if win['unit'] != 'day':
        return win['end']
    return max(win['end'], monday(today) + dt.timedelta(days=7))

def window_label(win, today):
    """"20 Jul to 21 Oct 2026": the first day to today (or the window's last day, if earlier)."""
    s0, e0 = win['start'], min(today, win['end'] - dt.timedelta(days=1))
    return '%d %s to %d %s %d' % (s0.day, MONTH_NAMES[s0.month - 1], e0.day, MONTH_NAMES[e0.month - 1], e0.year)

def unit_words(unit):
    """(singular, plural) for column wording: ('day', 'days') or ('week', 'weeks')."""
    return ('day', 'days') if unit == 'day' else ('week', 'weeks')

def add_window_args(ap, weeks_default=None):
    """The window options of discover.py and count_signals.py."""
    ap.add_argument('--window', choices=PRESETS, help='week (the last 7 days, day by day), month (5 weekly columns) or quarter '
                    '(14 weekly columns, the 1.6 default); computed from --today')
    ap.add_argument('--start', help='first day of the window (a Monday for weekly columns)')
    ap.add_argument('--weeks', type=int, default=weeks_default, help='weekly columns from --start (as in 1.6)')
    ap.add_argument('--unit', choices=UNITS, help='day or week columns, with --start and --columns')
    ap.add_argument('--columns', type=int, help='how many day or week columns, with --start and --unit')

def window_from_args(a, today, weeks_default=None):
    """(window, None) for what the command line asks for, or (None, a plain-English error)."""
    weeks_given = a.weeks is not None and a.weeks != weeks_default
    explicit = a.unit is not None or a.columns is not None
    try:
        if a.window:
            if a.start or explicit or weeks_given:
                return None, 'pass either --window or --start with --weeks (or with --unit and --columns), not both'
            return preset_window(a.window, today), None
        if not a.start:
            return None, 'pass --window week|month|quarter, or --start with --weeks (or with --unit and --columns)'
        if explicit:
            if a.unit is None or a.columns is None or weeks_given:
                return None, 'pass --unit and --columns together, without --weeks'
            return make_window(a.unit, a.start, a.columns), None
        if a.weeks is None:
            return None, 'pass --weeks (or --unit and --columns) with --start'
        return make_window('week', a.start, a.weeks), None
    except ValueError as e:
        return None, 'the window is not valid (%s)' % e

def rows(path):
    """Rows from an ExecuteSql result (JSONL with a header line), a JSON array, or {"value": [...]}."""
    with open(path, encoding='utf-8') as f:
        s = f.read().strip()
    if not s:
        return []
    try:
        whole = json.loads(s)
        if isinstance(whole, list) and (not whole or isinstance(whole[0], dict)):
            return whole
        if isinstance(whole, dict):
            for k in ('value', 'rows', 'items', 'chats'):
                if isinstance(whole.get(k), list):
                    return whole[k]
            return [whole]
    except ValueError:
        pass
    lines = [l for l in s.splitlines() if l.strip()]
    first = json.loads(lines[0])
    out = []
    if isinstance(first, list):
        for l in lines[1:]:
            r = json.loads(l)
            out.append(dict(zip(first, r)) if isinstance(r, list) else r)
    else:
        out.append(first)
        out += [json.loads(l) for l in lines[1:]]
    return out

def addresses(selves):
    """The --self values that are mail addresses, in the order given (the first one is the UPN)."""
    return [s.strip().lower() for s in selves if s and '@' in s]

_GD = None

def guard_data():
    """scripts/guard_data.json (one-way fingerprints only), read once; {} when it cannot be read."""
    global _GD
    if _GD is None:
        try:
            with open(GUARD_DATA, encoding='utf-8') as f:
                _GD = json.load(f)
        except (OSError, ValueError):
            _GD = {}
        if not isinstance(_GD, dict):
            _GD = {}
    return _GD

def _sample():
    s = guard_data().get('sample')
    return s if isinstance(s, dict) else {}

def short_hash(s, n=12):
    return hashlib.sha256(str(s).encode('utf-8', 'ignore')).hexdigest()[:n]

def sample_identity():
    """(fingerprint, owner UPN) of the bundled fictional sample run, from guard_data.json (version 1.8.2: the raw
    sample no longer ships in the skill), or (None, None) without it."""
    s = _sample()
    fps = s.get('fingerprints') or []
    return (fps[0] if fps else None), (str(s.get('owner') or '').strip().lower() or None)

def sample_fingerprints(win=None):
    """The fingerprints of the bundled sample run (with and without its files) and, with a window, the sample's
    fingerprints for that window when it is one window.py --views gives on a day of the sample's dates (stored in
    guard_data.json). discover.py and count_signals.py, which hold the data, also compare it with the sample row by
    row for any window (is_sample_data)."""
    s = _sample()
    out = set(s.get('fingerprints') or [])
    if win and out:
        out |= set((s.get('windows') or {}).get('%s|%s|%d' % (win['unit'], win['start'].isoformat(), win['columns'])) or [])
    return out

def _sample_in_window(by_date, wk):
    c = Counter()
    for day, hs in (by_date or {}).items():
        if wk(day) is not None:
            c.update(hs)
    return c

def sample_data_match(mail, cal, files, win):
    """True when the emails, calendar events and (if any fall in the window) files in this window are exactly the
    bundled sample's, compared by one-way hashes: the same test as an equal fingerprint, for any window."""
    s = _sample()
    if not win or not s.get('mail'):
        return False
    wk = column_index(win)
    if Counter(short_hash(m['key']) for m in mail if wk(m['t']) is not None) != _sample_in_window(s.get('mail'), wk):
        return False
    mine_cal = Counter(short_hash('%s|%s' % (r.get('subject') or '', r.get('startDateTime') or ''))
                       for r in cal or [] if wk(r.get('startDateTime')) is not None)
    if mine_cal != _sample_in_window(s.get('calendar'), wk):
        return False
    mine_f = Counter((short_hash(f['id']), w, e) for f, w, e, _ in files_in_window(files or [], wk))
    if not mine_f:
        return True
    stub = [{'id': i, 'lastModifiedByMe': bool(lm), 'lastModifiedDateTime': lm or None, 'createdByMe': bool(c),
             'createdDateTime': c or None, 'lastAccessedDateTime': la or None} for i, lm, c, la in s.get('files') or []]
    return mine_f == Counter((f['id'], w, e) for f, w, e, _ in files_in_window(stub, wk))

def is_sample_data(fp, win, mail, cal=None, files=None):
    """Whether the data read is the bundled fictional sample (its fingerprint, or the same rows in this window)."""
    return fp in sample_fingerprints(win) or (cal is not None and sample_data_match(mail, cal, files, win))

def sample_message_ids():
    """Hashes of every internetMessageId in the bundled sample's mail."""
    s = _sample()
    keys = {h for hs in (s.get('mail') or {}).values() for h in hs} - set(s.get('mailNotIds') or [])
    return keys | set(s.get('idsNotMail') or [])

def sample_file_ids():
    """Hashes of every file id in the bundled sample's files.json."""
    s = _sample()
    return {r[0] for r in s.get('files') or []} | set(s.get('fileIdsExtra') or [])

def stamp(now=None):
    """UTC time as 2026-10-21T11:40:00Z: the --now value when one is given (so a run can be repeated exactly), else the clock."""
    if now:
        t = dt.datetime.fromisoformat(now.strip().replace('Z', '+00:00'))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return t.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def mailbox_errors(paths, mail, selves, fp, win=None, cal=None, files=None):
    """Why these result files are not (only) the --self person's own mailbox; an empty list when they are.

    mail: load_mail() records inside the window (cal and files: what the fingerprint was made from). Sent Items must
    be sent from the --self addresses, every extra address must be one the person sends from, and nothing may come
    from the bundled fictional sample."""
    errs = []
    addrs = addresses(selves)
    s_owner = sample_identity()[1]
    is_sample = bool(s_owner) and is_sample_data(fp, win, mail, cal, files)
    sample_owner = bool(s_owner) and s_owner in addrs
    if sample_owner and not is_sample:
        errs.append('--self %s is the fictional sample person; it is only for rebuilding the shipped example from its own sample data' % s_owner)
    if is_sample and not sample_owner:
        errs.append('these result files come from the bundled fictional sample, not your mailbox')
    elif not sample_owner and s_owner:
        sample_ids = sample_message_ids()
        mine = {short_hash(r.get('internetMessageId')) for p in paths for r in rows(p) if r.get('internetMessageId')}
        shared = len(mine & sample_ids)
        if shared >= max(5, 0.01 * len(mine)):
            errs.append('%d of the mail rows come from the bundled fictional sample' % shared)
    sent = [m for m in mail if m['sent']]
    senders = Counter((m['from'] or '').strip().lower() for m in sent)
    def own(a):
        return any(x == a or x in a for x in addrs)
    by_self = sum(n for a, n in senders.items() if own(a))
    if len(sent) >= 10 and by_self < 0.5 * len(sent):
        errs.append('only %d of the %d mails in Sent Items were sent from %s, so these are not (only) your own result files'
                    % (by_self, len(sent), ', '.join(addrs)))
    if len(sent) >= 10:
        idle = [x for x in addrs[1:] if not any(x == a or x in a for a in senders)]
        if idle:
            errs.append('--self %s sent none of the mail in your Sent Items; pass only your own UPN and your own mail address' % ', '.join(idle))
    if not sent and len(mail) >= 100:
        errs.append('none of the %d mails in the window were sent by %s; check --self and pass --folders so Sent Items are recognised'
                    % (len(mail), ', '.join(addrs)))
    return errs

def unknown_folder_rows(paths, folders_path):
    """(rows whose parentFolderId is not in the folders file, all rows): a high share means another mailbox is mixed in."""
    if not folders_path:
        return 0, 0
    known = {r.get('id') for r in rows(folders_path)}
    allr = [r for p in paths for r in rows(p)]
    return sum(1 for r in allr if r.get('parentFolderId') and r.get('parentFolderId') not in known), len(allr)

def self_matcher(selves):
    low = [s.lower() for s in selves if s]
    def is_self(x):
        x = (x or '').lower()
        return any(s in x for s in low)
    return is_self

def x500(sender):
    """True for a legacy Exchange X500 address (legacyExchangeDN, "/O=EXCHANGELABS/OU=.../CN=...") instead of SMTP."""
    return isinstance(sender, str) and sender.strip().upper().startswith('/O=')

def load_mail(paths, folders_path=None, selves=()):
    """One record per distinct email: junk, drafts and outbox dropped; copies filed in several folders counted once.
    Version 1.7.1: a Sent Items row whose sender is a legacy X500 address (Exchange sometimes returns one for the
    mailbox owner) counts as sent by the owner (the first --self address); X500 senders in other folders are untouched."""
    folders = {r.get('id'): r.get('displayName') for r in rows(folders_path)} if folders_path else {}
    skip = {i for i, n in folders.items() if n in ('Junk Email', 'Drafts', 'Outbox')}
    sent_ids = {i for i, n in folders.items() if n == 'Sent Items'}
    is_self = self_matcher(selves)
    owner = (addresses(selves) or [None])[0]
    mail = {}
    for p in paths:
        for r in rows(p):
            if r.get('parentFolderId') in skip:
                continue
            in_sent = r.get('parentFolderId') in sent_ids
            sender = r.get('sender')
            if in_sent and owner and x500(sender):
                sender = owner                  # Exchange gave the owner's legacy X500 address for their own sent mail
            key = r.get('internetMessageId') or (r.get('subject'), r.get('receivedDateTime'), sender)
            m = mail.setdefault(key, {'t': r.get('receivedDateTime'), 's': r.get('subject'), 'from': sender,
                                      'sent': False, 'key': json.dumps(key) if not isinstance(key, str) else key})
            if not m['s'] and r.get('subject'):
                m['s'] = r.get('subject')
            if in_sent and owner and x500(m['from']):
                m['from'] = owner               # the same mail seen first in another folder with the X500 sender
            if in_sent or (not sent_ids and is_self(r.get('sender'))):
                m['sent'] = True
    return list(mail.values())

def load_calendar(paths):
    out = []
    for p in paths:
        for r in rows(p):
            if r.get('isCancelled') in (True, 'true', 'True', 1):
                continue
            out.append(r)
    return out

def week_index(start, weeks):
    def wk(s):
        try:
            d = dt.date.fromisoformat((s or '')[:10])
        except ValueError:
            return None
        w = (d - start).days // 7
        return w if 0 <= w < weeks else None
    return wk

def fingerprint(mail, cal, start, weeks, files=None, wk=None):
    """Short hash of exactly which emails, calendar events and (with --files) files were read; ties signals and discovery together.
    wk (version 1.7): the column function of the window (column_index); without it, weekly columns from start."""
    wk = wk or week_index(start, weeks)
    h = hashlib.sha256()
    for k in sorted(m['key'] for m in mail if wk(m['t']) is not None):
        h.update(k.encode('utf-8', 'ignore') + b'\n')
    for k in sorted('%s|%s' % (r.get('subject') or '', r.get('startDateTime') or '') for r in cal if wk(r.get('startDateTime')) is not None):
        h.update(k.encode('utf-8', 'ignore') + b'\n')
    for k in sorted('file|%s|%d|%d' % (f['id'], w, e) for f, w, e, _ in files_in_window(files or [], wk)):
        h.update(k.encode('utf-8', 'ignore') + b'\n')
    return h.hexdigest()[:16]

def source_fingerprint(mail, cal, files=None, chats=None):
    """Short hash of EVERYTHING that was read, whatever the window (version 1.8): every distinct email, calendar event,
    file record and chat row. The week, month and three-month runs of one data collection share it, so the build can
    tell that all three views come from exactly the same collected data."""
    h = hashlib.sha256()
    for k in sorted(m['key'] for m in mail):
        h.update(b'm|' + k.encode('utf-8', 'ignore') + b'\n')
    for k in sorted('%s|%s' % (r.get('subject') or '', r.get('startDateTime') or '') for r in cal):
        h.update(b'c|' + k.encode('utf-8', 'ignore') + b'\n')
    for k in sorted('%s|%s|%s|%s|%s|%s' % (f['id'], f.get('lastModifiedDateTime'), f.get('lastModifiedByMe'), f.get('createdDateTime'),
                                           f.get('createdByMe'), f.get('lastAccessedDateTime')) for f in files or []):
        h.update(b'f|' + k.encode('utf-8', 'ignore') + b'\n')
    for k in sorted('%s|%s|%s' % (c.get('topic') or '', c.get('chatType') or '', c.get('lastUpdatedDateTime') or '')
                    for c in chats or [] if isinstance(c, dict)):
        h.update(b't|' + k.encode('utf-8', 'ignore') + b'\n')
    h.update(b'files:%d chats:%d' % (files is not None, chats is not None))
    return h.hexdigest()[:16]

# ---- files (OneDrive, SharePoint and Teams libraries), version 1.6 ----
FILE_TYPES = ('Word', 'Excel', 'PowerPoint', 'PDF', 'OneNote', 'Loop', 'Other')
CONTAINER_TYPES = ('OneDrive', 'SharePoint', 'Teams')
EXT_TYPE = {e: t for t, exts in (
    ('Word', 'doc docx docm dot dotx dotm rtf odt'), ('Excel', 'xls xlsx xlsm xlsb xlt xltx xltm csv ods'),
    ('PowerPoint', 'ppt pptx pptm pot potx potm pps ppsx odp'), ('PDF', 'pdf'), ('OneNote', 'one onetoc2 onepkg'),
    ('Loop', 'loop fluid')) for e in exts.split()}

def _flag(v):
    if isinstance(v, str):
        return v.strip().lower() in ('true', '1', 'yes')
    return bool(v)

def file_label(name):
    """File name without its extension (the label discovery shows)."""
    n = (name or '').strip()
    base, dot, ext = n.rpartition('.')
    return base if dot and base and 1 <= len(ext) <= 5 and ext.isalnum() and not ext.isdigit() else n

def file_text(name):
    """File label as words, for term counts and keyword series (underscores, and hyphens in names without spaces, split words)."""
    t = file_label(name).strip()
    t = t.replace('_', ' ') if ' ' in t else re.sub(r'[-_.]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def _graph_file(r, is_self):
    """A raw Graph driveItem (for example from /me/drive/recent) in the files.json shape."""
    ri = r.get('remoteItem') or r
    def mine(x):
        u = (x or {}).get('user') or {}
        return bool(u) and (is_self(u.get('email')) or is_self(u.get('id')) or (not u.get('email') and not u.get('id') and is_self(u.get('displayName'))))
    pr = ri.get('parentReference') or {}
    spi = ri.get('sharepointIds') or {}
    ctype = 'OneDrive' if pr.get('driveType') in ('business', 'personal') else 'SharePoint'
    site = re.match(r'https?://[^/]+/(?:sites|teams)/([^/?#]+)', spi.get('siteUrl') or '', re.I)
    return {'id': (spi.get('listItemUniqueId') or '').strip('{}').lower() or '%s!%s' % (pr.get('driveId') or '', ri.get('id') or r.get('id') or ''),
            'name': ri.get('name') or r.get('name'), 'containerType': ctype,
            'container': 'OneDrive' if ctype == 'OneDrive' else (re.sub(r'[-_]+', ' ', site.group(1)) if site else None),
            'containerId': None if ctype == 'OneDrive' else ((spi.get('siteId') or '').lower() or None),
            'lastModifiedDateTime': ri.get('lastModifiedDateTime'), 'lastModifiedByMe': mine(ri.get('lastModifiedBy')),
            'createdDateTime': ri.get('createdDateTime'), 'createdByMe': mine(ri.get('createdBy')),
            'lastAccessedDateTime': (r.get('fileSystemInfo') or {}).get('lastAccessedDateTime') or (ri.get('fileSystemInfo') or {}).get('lastAccessedDateTime'),
            'sharedByMe': None, 'source': r.get('source') or 'graph', '_folder': 'folder' in ri,
            '_package': (ri.get('package') or {}).get('type')}

# The skill's own files and outputs, whoever made them (a colleague's sphere or slide, a saved setup, working files), and
# anything in a skills folder (OneDrive path Cowork/skills): never evidence, terms, templates or wording, and not counted.
SKILL_FILE = re.compile(
    r'work[\s_-]*iq[\s_-]*(?:sphere|slide|story|ontology)'
    r'|^workiq[\s_-]*(?:config|keywords|sphere)'
    r'|^(?:discovery|signals|keywords|chats|chats_partial|files|files_report|folders)\b[^/\\]*\.jsonl?$'
    r'|^(?:skill|slide_style|workflow_details|error_table)\.md$|^(?:example_config|example_keywords|guard_data)\.json$', re.I)
SKILLS_FOLDER = re.compile(r'/cowork/skills(?:/|$)', re.I)

def skill_file(r):
    """True for a record of the skill's own files or outputs, or of anything in a skills folder."""
    if SKILL_FILE.search((r.get('name') or '').strip()):
        return True
    paths = [r.get(k) for k in ('path', 'webUrl', 'webDavUrl', 'folder')]
    for x in (r, r.get('remoteItem') or {}):
        paths += [x.get('webUrl'), x.get('webDavUrl'), (x.get('parentReference') or {}).get('path')]
    for v in paths:
        if isinstance(v, str) and v and SKILLS_FOLDER.search(urllib.parse.unquote(v).replace('\\', '/')):
            return True
    return False

def read_files_doc(path):
    """(meta, records) of one files.json. collect_files_recipe.py writes {"meta": {"owner", "self", ...}, "files": [...]};
    a bare list or {"value": [...]} has no meta, so it cannot show whose files it lists."""
    with open(path, encoding='utf-8') as f:
        s = f.read().strip()
    if not s:
        return None, []
    try:
        doc = json.loads(s)
    except ValueError:
        return None, rows(path)
    if isinstance(doc, dict) and isinstance(doc.get('files'), list):
        return (doc['meta'] if isinstance(doc.get('meta'), dict) else None), doc['files']
    return None, rows(path)

def load_files(paths, selves=(), stats=None):
    """One record per file from files.json (written by collect_files_recipe.py), de-duplicated by id.

    Tolerant of missing fields: type comes from the extension, containerType from the container, flags default to false,
    dates to None. Raw Graph driveItems are accepted too; their "by me" flags are worked out from selves (UPN, mail, id).
    Folders and records without a name are skipped, and so are the skill's own files (skill_file); stats, when given,
    counts them under "skipped"."""
    is_self = self_matcher(selves)
    out, by_id = [], {}
    for p in ([paths] if isinstance(paths, str) else paths or []):
        for r in read_files_doc(p)[1]:
            if not isinstance(r, dict):
                continue
            if skill_file(r):
                if stats is not None:
                    stats['skipped'] = stats.get('skipped', 0) + 1
                continue
            if 'remoteItem' in r or isinstance(r.get('lastModifiedBy'), dict) or isinstance(r.get('createdBy'), dict):
                r = _graph_file(r, is_self)
                if r.pop('_folder') or not r.get('name'):
                    continue
                if (r.pop('_package') or '').lower() == 'onenote':
                    r['type'] = 'OneNote'
            name = (r.get('name') or '').strip()
            if not name or r.get('folder') is not None:
                continue
            ctype = r.get('containerType') if r.get('containerType') in CONTAINER_TYPES else None
            cont = (r.get('container') or '').strip()
            if not ctype:
                ctype = 'OneDrive' if cont in ('', 'OneDrive') else 'SharePoint'
            ftype = r.get('type') if r.get('type') in FILE_TYPES else EXT_TYPE.get(name.rsplit('.', 1)[-1].lower() if '.' in name else '', 'Other')
            shared = r.get('sharedByMe')
            f = {'id': str(r.get('id') or '') or 'name:' + hashlib.sha256(('%s|%s|%s' % (name, cont, r.get('lastModifiedDateTime') or '')).encode('utf-8')).hexdigest()[:16],
                 'name': name, 'type': ftype, 'container': cont or ('OneDrive' if ctype == 'OneDrive' else 'SharePoint site'),
                 'containerType': ctype, 'containerId': r.get('containerId') or None,
                 'lastModifiedDateTime': r.get('lastModifiedDateTime') or None, 'lastModifiedByMe': _flag(r.get('lastModifiedByMe')),
                 'createdDateTime': r.get('createdDateTime') or None, 'createdByMe': _flag(r.get('createdByMe')),
                 'lastAccessedDateTime': r.get('lastAccessedDateTime') or None,
                 'sharedByMe': None if shared is None else _flag(shared), 'source': r.get('source') or 'unknown'}
            old = by_id.get(f['id'])
            if old is None:
                by_id[f['id']] = f
                out.append(f)
                continue
            for k in ('lastModifiedByMe', 'createdByMe'):
                old[k] = old[k] or f[k]
            for k in ('lastModifiedDateTime', 'createdDateTime', 'lastAccessedDateTime'):
                if f[k] and (not old[k] or f[k] > old[k]):
                    old[k] = f[k]
            if old['sharedByMe'] is None:
                old['sharedByMe'] = f['sharedByMe']
    return out

def file_activity(f, wk):
    """(week, edited, when) of a file in the window: my last edit, else my creation, when that fell in the window
    (edited = True); otherwise my last open (edited = False). week is None when nothing fell in the window."""
    if f['lastModifiedByMe'] and wk(f['lastModifiedDateTime']) is not None:
        return wk(f['lastModifiedDateTime']), True, f['lastModifiedDateTime']
    if f['createdByMe'] and wk(f['createdDateTime']) is not None:
        return wk(f['createdDateTime']), True, f['createdDateTime']
    return wk(f['lastAccessedDateTime']), False, f['lastAccessedDateTime']

def files_in_window(files, wk):
    """[(file, week, edited, when)] for files the person edited, created or opened in the window."""
    out = []
    for f in files:
        w, e, when = file_activity(f, wk)
        if w is not None:
            out.append((f, w, e, when or ''))
    return out

def file_site_key(f):
    """Which SharePoint or Teams site a file sits in (None for OneDrive)."""
    if f['containerType'] == 'OneDrive':
        return None
    return (f.get('containerId') or '').lower() or 'name:' + f['container'].strip().lower()

def files_owner_errors(paths, selves, files):
    """Why these files.json files are not (only) the --self person's own file activity; an empty list when they are.
    Each must name its owner (the first --self address) and list no other address, and none may share files with the
    bundled fictional sample unless the sample person is rebuilding the sample."""
    errs, addrs = [], addresses(selves)
    for p in ([paths] if isinstance(paths, str) else paths or []):
        meta = read_files_doc(p)[0] or {}
        owner = str(meta.get('owner') or '').strip().lower()
        if not owner:
            errs.append('%s does not say whose files it lists (no meta.owner); collect it again with scripts/collect_files_recipe.py' % p)
        elif not addrs or owner != addrs[0]:
            errs.append('%s lists the files of %s, not yours (%s)' % (p, owner, addrs[0] if addrs else 'no --self address'))
        else:
            extra = [x for x in addresses(meta.get('self') or []) if x not in addrs]
            if extra:
                errs.append('%s was collected for %s as well; collect it again for the signed-in user only' % (p, ', '.join(extra)))
    s_owner = sample_identity()[1]
    if s_owner and s_owner not in addrs and files:
        sample_ids = sample_file_ids()
        shared = sum(1 for f in files if short_hash(f['id']) in sample_ids)
        if shared >= max(3, 0.05 * len(files)):
            errs.append('%d of the files come from the bundled fictional sample' % shared)
    return errs

def file_summary(rows_, wk):
    """signals.files: counts over files_in_window() rows (edited includes files the person created in the window)."""
    by = {t: 0 for t in CONTAINER_TYPES}
    for f, _, _, _ in rows_:
        by[f['containerType']] += 1
    edited = sum(1 for _, _, e, _ in rows_ if e)
    return {'worked_on': len(rows_), 'edited': edited,
            'created': sum(1 for f, _, _, _ in rows_ if f['createdByMe'] and wk(f['createdDateTime']) is not None),
            'opened': len(rows_) - edited, 'sites': len({file_site_key(f) for f, _, _, _ in rows_} - {None}), 'byContainer': by}

PREFIX = re.compile(r'^\s*((re|fw|fwd|aw|wg|sv|vs|tr|antw|rif|accepted|declined|tentative|tentatively accepted|updated|'
                    r'canceled|cancelled|following|automatic reply|out of office|new time proposed|reminder|invitation|'
                    r'updated invitation|abgesagt|angenommen|mit vorbehalt angenommen)\s*(\[\d+\])?\s*:\s*)+', re.I)

def norm_subject(s):
    s = (s or '').strip()
    prev = None
    while prev != s:
        prev = s
        s = PREFIX.sub('', s).strip()
    return re.sub(r'\s+', ' ', s)

def slug(s):
    """Stable ASCII id part: accents transliterated (a umlaut becomes a), long labels get a short hash so ids never collide."""
    t = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii')
    t = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    if len(t) > 60:
        t = t[:52].rstrip('-') + '-' + hashlib.sha1((s or '').encode('utf-8'), usedforsecurity=False).hexdigest()[:7]
    return t or 'untitled'

SERIES_NOISE = re.compile(
    r'\b(?:kw|cw|wk|week|woche|w/c|wc)\s*\.?\s*\d{1,2}\b'
    r'|\b\d{4}-\d{2}-\d{2}\b'
    r'|\b\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?\b'
    r'|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?(?:\s+\d{4})?\b'
    r'|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?\b(?:,?\s+\d{4})?', re.I)

def series_key(subj):
    """A subject without its week number or date, so 'Open points KW 42' and 'Open points KW 43' group as one series."""
    s = SERIES_NOISE.sub(' ', subj or '')
    s = re.sub(r'\(\s*\)', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip(' -:,/')
    return s or (subj or '')

MULTI = ('gov.uk', 'ac.uk', 'nhs.uk', 'mod.uk', 'police.uk', 'org.uk', 'co.uk', 'ltd.uk', 'plc.uk', 'sch.uk', 'gov.wales',
         'gov.scot', 'com.au', 'gov.au', 'co.nz', 'govt.nz', 'co.jp', 'go.jp', 'co.in', 'gov.in', 'com.br', 'gov.br', 'gv.at',
         'co.at', 'or.at', 'ac.at', 'gouv.fr', 'com.cn', 'gov.cn', 'co.za', 'gov.za', 'com.sg', 'gov.sg', 'gov.ie', 'admin.ch')
UK_PUBLIC = ('gov.uk', 'ac.uk', 'nhs.uk', 'mod.uk', 'police.uk', 'gov.wales', 'gov.scot')
CONSUMER = {'gmail.com', 'googlemail.com', 'outlook.com', 'hotmail.com', 'hotmail.co.uk', 'live.com', 'live.co.uk', 'msn.com',
            'yahoo.com', 'yahoo.co.uk', 'icloud.com', 'me.com', 'aol.com', 'btinternet.com', 'sky.com', 'gmx.de', 'gmx.net',
            'web.de', 't-online.de', 'proton.me', 'protonmail.com', 'mail.com',
            'outlook.de', 'outlook.fr', 'outlook.co.uk', 'hotmail.de', 'hotmail.fr', 'live.de', 'live.fr', 'yahoo.de',
            'yahoo.fr', 'ymail.com', 'mac.com', 'aol.co.uk', 'gmx.com', 'gmx.at', 'gmx.ch', 'pm.me'}

def consumer_domain(domain):
    """True for personal webmail (outlook.com, gmail.com, ...), including any subdomain of one: personal contacts,
    never an organisation (version 1.7.1)."""
    d = (domain or '').strip().lower().strip('.').rsplit('@', 1)[-1].strip('>').strip()
    return bool(d) and (d in CONSUMER or org_root(d) in CONSUMER or any(d.endswith('.' + c) for c in CONSUMER))
NOISE = re.compile(r'(^|\.)(microsoft\.com|office\.com|office365\.com|sharepoint\.com|sharepointonline\.com|onmicrosoft\.com|'
                   r'microsoftonline\.com|linkedin\.com|yammer\.com|microsoft365\.com|dynamics\.com|azure\.com|'
                   r'mail\.microsoft|cloud\.microsoft)$', re.I)

def org_root(domain):
    d = (domain or '').lower().strip('.')
    if d == 'nhs.net':
        return 'nhs.net'
    parts = d.split('.')
    for suf in MULTI:
        if d.endswith('.' + suf):
            return '.'.join(parts[-(len(suf.split('.')) + 1):])
    return '.'.join(parts[-2:])

def uk_public_org(domain):
    d = (domain or '').lower()
    if d == 'nhs.net':
        return 'nhs.net'
    for suf in UK_PUBLIC:
        if d.endswith('.' + suf):
            return d.split('.')[-(len(suf.split('.')) + 1)]
    return None

def own_domains(selves, extra=''):
    doms = {s.split('@', 1)[1].lower() for s in selves if s and '@' in s}
    doms |= {d.strip().lower() for d in (extra or '').split('|') if d.strip()}
    return doms

def external_domain(addr, own, excl=None):
    """Domain of an external organisation's address, or None for the user's own organisation, consumer mail and service noise."""
    a = (addr or '').strip().lower()
    if '@' not in a:
        return None
    d = a.rsplit('@', 1)[1].strip('>').strip()
    if not d or consumer_domain(d) or NOISE.search(d):
        return None
    if any(d == o or d.endswith('.' + o) for o in own):
        return None
    if excl and excl.search(d):
        return None
    return d

ATTENDEE = re.compile(r'\s*(?:"?([^"<;]*?)"?\s*)?<([^>]+@[^>]+)>\s*')

def parse_attendees(v):
    """Attendees as [(name, email)] from ExecuteSql's "Name <email>; ..." text or a list of Graph attendee objects."""
    out = []
    if isinstance(v, list):
        for x in v:
            ea = (x or {}).get('emailAddress', x) if isinstance(x, dict) else {}
            if isinstance(ea, dict) and ea.get('address'):
                out.append(((ea.get('name') or '').strip(), ea['address'].strip()))
            elif isinstance(x, str) and '@' in x:
                out.append(('', x.strip()))
        return out
    for part in re.split(r';\s*', v or ''):
        m = ATTENDEE.fullmatch(part.strip()) if part.strip() else None
        if m:
            out.append(((m.group(1) or '').strip(), m.group(2).strip()))
        elif '@' in part:
            out.append(('', part.strip().strip('<>')))
    return out

def signals_digest(sig):
    """Hash of everything count_signals.py wrote, so a signals block that was edited, extended or pasted is refused."""
    body = {k: sig.get(k) for k in ('grid', 'vol', 'senders', 'orgs', 'pub_orgs', 'chats', 'weeks')}
    if 'files' in sig:                     # count_signals.py --files; without it the digest is what 1.5 wrote
        body['files'] = sig['files']
    if 'focus' in sig:                     # count_signals.py --focus-... (1.7); without it the digest is what 1.6 wrote
        body['focus'] = sig['focus']
    meta = {k: v for k, v in (sig.get('meta') or {}).items() if k != 'digest'}
    blob = json.dumps({'body': body, 'meta': meta}, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()[:24]

def chats_in_window(path, wk):
    """Group and 1:1 Teams chats with activity in the window (meeting chats excluded), counted as discover.py does."""
    n = 0
    for c in rows(path):
        if c.get('chatType') in ('group', 'oneOnOne') and wk(c.get('lastUpdatedDateTime')) is not None:
            n += 1
    return n

# Words that say nothing about WHICH programme, theme or asset something is (they match almost any subject).
GENERIC_WORDS = set('''copilot copilots microsoft m365 365 office agent agents pilot pilots programme programmes program programs
project projects weekly monthly daily quarterly review reviews update updates sync syncs meeting meetings team teams customer
customers work plan plans planning status call calls session sessions the and for with from into about our your my of in on to
at by an new next kick off kickoff internal external follow followup general'''.split())
ORG_STOP = {'of', 'for', 'and', 'the', 'und', 'der', 'die', 'das', 'de', 'la', 'le', 'du', 'et'}
DOMAIN_WORDS = {'gov', 'com', 'org', 'net', 'co', 'ac', 'uk', 'example', 'www', 'int', 'edu', 'mail', 'de', 'fr', 'eu', 'io', 'info', 'biz'}

def fold(s):
    """Lower case, accents removed and German umlaut spellings merged, so Mueller, Muller and M\u00fcller compare equal."""
    t = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').lower()
    return t.replace('ae', 'a').replace('oe', 'o').replace('ue', 'u')

def words(s):
    return re.findall(r'[a-z0-9]+', fold(s))

def item_labels(it):
    """Every text a discovery item carries that an entity name can be checked against."""
    out = [it.get('label') or '']
    for k in ('topSubjects', 'subjects', 'orgs'):
        out += [x for x in (it.get(k) or []) if isinstance(x, str)]
    if it.get('email'):
        out.append(it['email'].split('@')[0])
    return out

def org_display_name(item, items=None):
    """The name an organisation's own subjects give it ("Northwind Traders" for northwindtraders.example): the run of
    1 to 4 words in its top subjects (then in any meeting or thread label) whose letters spell its domain's first part.
    None when nothing in the person's own data spells it (newsletters and services usually)."""
    stem = re.sub(r'[^a-z0-9]', '', fold((item.get('label') or '').split('.')[0]))
    if len(stem) < 3:
        return None
    texts = [s for s in (item.get('topSubjects') or []) if isinstance(s, str)]
    texts += [it.get('label') or '' for it in (items or {}).values() if it.get('kind') in ('meeting', 'thread', 'upcoming', 'chat')]
    for t in texts:
        toks = re.findall(r"[^\s:;,.!?()\[\]\"]+", t)
        for i in range(len(toks)):
            for j in range(i + 1, min(len(toks), i + 4) + 1):
                if re.sub(r'[^a-z0-9]', '', fold(''.join(toks[i:j]))) == stem:
                    return ' '.join(toks[i:j])
    return None

def initials(name):
    """Initials with and without small words; an all-capitals word gives all its letters (QX Retail and Logistics: qxrl)."""
    toks = re.findall(r'[A-Za-z0-9]+', unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii'))
    def part(t):
        return t.lower() if t.isupper() and len(t) <= 5 else t[0].lower()
    return {''.join(part(t) for t in toks), ''.join(part(t) for t in toks if t.lower() not in ORG_STOP)}

def norm_text(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = re.sub(r'\{\w+\}', ' ', s)
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def text_hash(s):
    return hashlib.sha256(norm_text(s).encode('utf-8')).hexdigest()[:16]

def shingles(s, n=3):
    w = norm_text(s).split()
    return {' '.join(w[i:i + n]) for i in range(len(w) - n + 1)}

def shingle_hashes(s, n=3):
    return {hashlib.sha256(x.encode('utf-8')).hexdigest()[:12] for x in shingles(s, n)}

def upn_hash(upn):
    return hashlib.sha256((upn or '').strip().lower().encode('utf-8')).hexdigest()[:16]
