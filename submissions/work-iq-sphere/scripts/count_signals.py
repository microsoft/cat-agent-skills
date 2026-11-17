#!/usr/bin/env python3
"""Turn ONE person's ExecuteSql result files (messages + calendarView) into the Work IQ "signals" block.

Usage:
  python count_signals.py --messages <messages.jsonl> [--messages <more.jsonl>] --calendar <calendarView.jsonl>
      --start 2026-07-20 --weeks 14 --keywords working/keywords.json --self "user@contoso.com" --self "Display Name"
      [--folders <mailFolders.jsonl>] [--chats-file working/chats.json] [--own-domains "contoso.com"]
      [--exclude-domains "parish|school"] [--files working/files.json] [--now 2026-10-21T11:40:00Z] --out working/signals.json

messages jsonl columns: subject, receivedDateTime, sender, and ideally internetMessageId + parentFolderId (line 1 = header).
  With internetMessageId, copies of one email in several folders count once. With parentFolderId plus --folders
  (SELECT id, displayName FROM mailFolders), mail in Junk Email, Drafts and Outbox is excluded and "sent" means Sent Items.
calendar jsonl columns: subject, startDateTime, isCancelled (line 1 = header). Every non-cancelled entry counts as a calendar event.
keywords.json: {"t_<theme>": "regex", "c_<customer>": "regex", ...} written for THIS person from their discovery.json.
  The bundled example keywords, or keywords copied from an earlier version's sample, are refused.
--chats-file: the chats listed by the tool script (the same file discover.py read); the chat count (group and 1:1 chats
  with activity in the window, meeting chats not counted) is computed from it. --chats N only when no chats file exists.
Outputs {"grid", "vol": {mail_in, mail_out, meet}, "senders", "orgs", "pub_orgs", "chats", "weeks", "meta"} and prints a summary.
--files (version 1.6): files.json from collect_files_recipe.py, stamped with its owner (meta.owner must be the first
  --self address). Adds vol.files (files worked on per week, each file once, in the week of my last edit or creation,
  else my last open) and "files": {worked_on, edited, created, opened, sites, byContainer}; keyword series also count
  the names of files the person edited or created (never files they only opened); the fingerprint and the digest cover
  the files, so run discover.py with the same --files. Without --files the output is the same as without the files source.
--now: the current UTC time, used as the generatedAt stamp (so the same command gives the same file).
Window (version 1.7): the same window options as discover.py (--start with --weeks as in 1.6; --window week|month|quarter
  with --today; or --start with --unit day|week and --columns). A day-by-day window counts one column per day and labels
  them like "Thu 15 Oct"; meta then records "unit": "day" and "columns" (weekly windows keep the 1.6 fields).
Focus (version 1.7): --focus-type customer|programme|theme with --focus-regex "<its name or words>" (and, for a customer,
  --focus-domains "<its mail domains>"), as scripts/focus.py prints them, adds "focus": {"vol": {mail_in, mail_out, meet,
  chats[, files]}, "grid": {...}}: per column, the emails, calendar events, chats and files about the focus (a customer:
  sent from or attended by its domains, or its name in a subject, chat title, file name or site name; a programme or
  topic: its words there), and every keyword series counted inside that subset. meta.focus records the type, the
  pattern and the domains, and the digest covers both. Matching is by name, domain and keywords: direction, not a census.
  Without the focus options every output is exactly as before.
"meta" records whose data this is (the --self values), the window and a fingerprint of exactly which items were read;
build_workiq.py checks it against the config owner and discovery.json.
Version 1.7.1: personal webmail domains (wiq_data.CONSUMER, subdomains included) never count as external
  organisations, and Sent Items rows with a legacy Exchange X500 sender count as sent by the first --self address,
  exactly as in discover.py, so both scripts give identical totals and fingerprints.
Views (version 1.8): meta.source fingerprints everything read, whatever the window (as discover.py does).
  --view-of <the three-month signals.json>: the week or month view of the same data. It refuses other result files,
  another person, other keywords or another focus than the three-month run, skips the catch-all keyword check (the
  three-month run already made it on more subjects) and records the three-month digest in meta.viewOf.
"""
import argparse, json, re, os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wiq_data as W
HERE = os.path.dirname(os.path.abspath(__file__))

def norm_rx(v):
    return re.sub(r'\s+', '', (v or '').lower())

# Microsoft product words: anyone's product keywords look alike, so they never count as copied.
PRODUCT_WORDS = set('''copilot microsoft 365 m365 studio chat purview teams sharepoint onedrive outlook word excel powerpoint loop
dynamics power bi platform apps automate pages fabric azure entra intune defender viva windows github dragon agent agents'''.split())

def _split_top(rx):
    parts, depth, cur, esc = [], 0, '', False
    for ch in rx:
        if esc:
            cur += ch; esc = False; continue
        if ch == '\\':
            cur += ch; esc = True; continue
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == '|' and depth == 0:
            parts.append(cur); cur = ''
        else:
            cur += ch
    return parts + [cur]

def alternatives(rx):
    """The top-level alternatives of a keyword regex, normalised (lower case, no word boundaries, empty or wrapping
    groups removed), so reordering or padding a copied keyword does not make it look new."""
    out = set()
    for p in _split_top(rx or ''):
        q = re.sub(r'\(\?:\)|\\b', '', p.lower()).strip()
        m = re.fullmatch(r'\((?:\?:)?(.*)\)', q)
        if m and m.group(1).count('(') == m.group(1).count(')'):
            out |= alternatives(m.group(1)); continue
        q = re.sub(r'\\s[*+?]?|\s+', ' ', q).strip()
        if q:
            out.add(q)
    return out

def _product_only(alt):
    return set(re.findall(r'[a-z0-9]+', alt)) <= PRODUCT_WORDS

def guard_keywords(kw, selves, subjects):
    """Refuse catch-all keywords, and keywords copied from a bundled sample that the person's own subjects barely match.
    A copied-looking keyword that does match the person's own work (a teammate's shared customer) is kept, with a note."""
    errs, n = [], len(subjects)
    for k, v in kw.items():
        try:
            r = re.compile(v, re.I)
        except re.error as e:
            errs.append('%s is not a valid pattern (%s)' % (k, e)); continue
        if r.search('') is not None:
            errs.append('%s matches empty text' % k); continue
        for alt in alternatives(v):
            letters = re.sub(r'\\.|[^a-z0-9]', '', alt)
            if len(letters) < 2 or (len(letters) < 3 and '\\b' not in v.lower()):
                errs.append('%s has an alternative too short to mean anything ("%s")' % (k, alt)); break
        if not k.startswith('p_') and n >= 50:
            hits = sum(1 for x in subjects if r.search(x))
            if hits > 0.4 * n:
                errs.append('%s matches %d of your %d subjects, so it says nothing about one customer or theme' % (k, hits, n))
    copied = []
    mine_up = [s.strip().lower() for s in selves if '@' in (s or '')]
    sample = W.guard_data().get('sample') or {}
    if sample.get('keywords') and str(sample.get('keywordsOwner', '')).strip().lower() not in mine_up:
        # the bundled sample's keywords, as one-way hashes of their alternatives (version 1.8.2: not shipped in plain text)
        ex_sets = [set(es) for es in sample['keywords']]
        for k, v in kw.items():
            mine = {W.short_hash(a) for a in alternatives(v) if not _product_only(a)}
            if k.startswith('p_') or not mine:
                continue
            if any(es and len(mine & es) / len(mine | es) >= 0.5 for es in ex_sets):
                copied.append(k)
    leg = set(W.guard_data().get('legacyKeywords', []))
    copied += [k for k, v in kw.items() if not k.startswith('p_') and W.text_hash(norm_rx(v)) in leg and k not in copied]
    dead = []
    for k in copied:
        alts = sorted(alternatives(kw[k])); live = 0
        for alt in alts:
            try:
                ra = re.compile(alt, re.I)
            except re.error:
                continue
            live += any(ra.search(x) for x in subjects)
        if live * 2 < len(alts) or not live:
            dead.append(k)
    if dead:
        errs.append('keywords %s are copied from a bundled sample and your own mail and calendar hardly match them, so they are '
                    'not yours. Write keywords.json from the terms, meetings and organisations in YOUR discovery.json' % ', '.join(dead))
    if errs:
        print('ERROR: ' + '; '.join(errs) + '.'); sys.exit(2)
    if copied:
        print('NOTE: keywords %s look like the bundled sample\'s, but your own subjects match them, so they are kept.' % ', '.join(copied))

def focus_errors(a, subjects):
    """Why the focus options cannot be counted (plain English), or []: a customer needs its domains, a programme or topic
    none, and the pattern must name one thing (not empty, not a catch-all)."""
    errs = []
    if not a.focus_type:
        if a.focus_regex or a.focus_domains:
            errs.append('--focus-regex and --focus-domains need --focus-type customer, programme or theme')
        return errs
    if not a.focus_regex:
        return ['--focus-type needs --focus-regex (the focus flags scripts/focus.py prints)']
    try:
        r = re.compile(a.focus_regex, re.I)
    except re.error as e:
        return ['the focus pattern is not valid (%s)' % e]
    if r.search('') is not None:
        errs.append('the focus pattern matches empty text')
    for alt in alternatives(a.focus_regex):
        if len(re.sub(r'\\.|[^a-z0-9]', '', alt)) < 3:
            errs.append('the focus pattern has an alternative too short to mean anything ("%s")' % alt); break
    n = len(subjects)
    if n >= 50 and sum(1 for x in subjects if r.search(x)) > 0.4 * n:
        errs.append('the focus pattern matches most of your subjects, so it is not one customer, programme or topic')
    doms = [d for d in (a.focus_domains or '').split('|') if d.strip()]
    if a.focus_type == 'customer' and not doms:
        errs.append('a customer focus needs --focus-domains (its mail domains, as focus.py prints them)')
    if a.focus_type != 'customer' and doms:
        errs.append('only a customer focus has domains')
    if any('.' not in d or '@' in d or ' ' in d.strip() for d in doms):
        errs.append('--focus-domains takes mail domains such as contoso.com, separated by |')
    return errs

def view_base(a, raw, source):
    """Version 1.8: the three-month signals.json this run is a view of, after checking it counted the same data the same way."""
    try:
        base = json.load(open(a.view_of, encoding='utf-8'))
        bm = base['meta']
    except (OSError, ValueError, KeyError, TypeError):
        print('ERROR: --view-of %s is not a signals.json written by count_signals.py' % a.view_of); sys.exit(2)
    why = []
    if [x.strip().lower() for x in bm.get('self') or []] != [x.strip().lower() for x in a.self]:
        why.append('it was counted with --self %s' % ', '.join(bm.get('self') or ['nobody']))
    if not bm.get('source') or bm.get('source') != source:
        why.append('it read other result files (or other chats or files) than this run')
    if (bm.get('keywords') or {}) != raw:
        why.append('it used other keywords')
    want = None
    if a.focus_type:
        want = {'type': a.focus_type, 'regex': a.focus_regex,
                'domains': sorted({W.org_root(d.strip().lower()) for d in (a.focus_domains or '').split('|') if d.strip()})}
    if (bm.get('focus') or None) != want:
        why.append('it was counted for another focus')
    if bm.get('digest') != W.signals_digest(base):
        why.append('it is not what count_signals.py wrote')
    if why:
        print('ERROR: --view-of %s is not the three-month count of this same data (%s). Run count_signals.py for the week and the '
              'month with exactly the same --messages, --calendar, --folders, --chats-file, --files, --keywords, focus flags '
              'and --self as the three-month run, and pass its signals.json.' % (a.view_of, '; '.join(why))); sys.exit(2)
    return base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--messages', action='append', default=[]); ap.add_argument('--calendar', action='append', default=[])
    W.add_window_args(ap, weeks_default=13)
    ap.add_argument('--today', help='today (for --window); default: the date of --now, else the clock')
    ap.add_argument('--keywords', required=True); ap.add_argument('--self', action='append', default=[], required=True)
    ap.add_argument('--folders'); ap.add_argument('--own-domains', default=''); ap.add_argument('--exclude-domains', default='')
    ap.add_argument('--chats', type=int, default=None, help='only when no chats file exists; otherwise use --chats-file')
    ap.add_argument('--chats-file', help='working/chats.json (the same file discover.py read); the chat count is computed from it')
    ap.add_argument('--files', help='files.json from collect_files_recipe.py (your own OneDrive and SharePoint file activity)')
    ap.add_argument('--now', help='the current UTC time (e.g. 2026-10-21T11:40:00Z), written as generatedAt')
    ap.add_argument('--focus-type', choices=('customer', 'programme', 'theme'), help='count what is about one customer, programme or topic')
    ap.add_argument('--focus-regex', help='the focus name or words (case-insensitive) for subjects, chat titles and file or site names')
    ap.add_argument('--focus-domains', default='', help='a customer focus: its mail domains, separated by |')
    ap.add_argument('--view-of', help='the three-month signals.json (version 1.8): this run is its week or month view')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if not any('@' in s for s in a.self):
        print('ERROR: pass your own UPN with --self (for example --self you@contoso.com) so the numbers are stamped as yours'); sys.exit(2)
    today = dt.date.fromisoformat(a.today) if a.today else (dt.date.fromisoformat(W.stamp(a.now)[:10]) if a.now else dt.date.today())
    win, why = W.window_from_args(a, today, weeks_default=13)
    if win is None:
        print('ERROR: ' + why); sys.exit(2)
    start, weeks = win['start'], win['columns']
    if win['unit'] == 'week' and start.weekday() != 0: print('WARNING: --start is not a Monday')
    raw = {k: v for k, v in json.load(open(a.keywords, encoding='utf-8')).items() if not k.startswith('_')}
    for k, v in raw.items():
        try:
            re.compile(v, re.I)
        except re.error as e:
            print('ERROR: keyword %s is not a valid pattern (%s)' % (k, e)); sys.exit(2)
    kw = {k: re.compile(v, re.I) for k, v in raw.items()}
    grid = {k: [0] * weeks for k in kw}; vol = {'mail_in': [0] * weeks, 'mail_out': [0] * weeks, 'meet': [0] * weeks}
    wk = W.column_index(win)
    is_self = W.self_matcher(a.self)
    own = W.own_domains(a.self, a.own_domains)
    excl = re.compile(a.exclude_domains, re.I) if a.exclude_domains else None
    mail = W.load_mail(a.messages, a.folders, a.self)
    cal = W.load_calendar(a.calendar)
    fstats = {}
    files = W.load_files(a.files, a.self, fstats) if a.files else None
    frows = W.files_in_window(files, wk) if files is not None else []
    mine = [x for x in frows if x[2]]               # files the person edited or created; opened-only files are only counted
    if files is not None:
        errs = W.files_owner_errors(a.files, a.self, files)
        if errs:
            print('ERROR: ' + '; '.join(errs) + '. Collect your own files with scripts/collect_files_recipe.py, or leave --files out.'); sys.exit(2)
    errs = W.mailbox_errors(a.messages, [m for m in mail if wk(m['t']) is not None], a.self,
                            W.fingerprint(mail, cal, start, weeks, files, wk=wk), win, cal, files)
    if errs:
        print('ERROR: ' + '; '.join(errs) + '. Run the ExecuteSql queries for the signed-in user and pass only those result files.'); sys.exit(2)
    if a.chats_file:
        n_chats = W.chats_in_window(a.chats_file, wk)
        if a.chats is not None and a.chats != n_chats:
            print('ERROR: --chats %d does not match the %d group and 1:1 chats active in the window in %s; leave --chats out' % (a.chats, n_chats, a.chats_file)); sys.exit(2)
        a.chats = n_chats
    elif a.chats is None:
        a.chats = 0
    subjects = ([m['s'] or '' for m in mail if wk(m['t']) is not None] + [r.get('subject') or '' for r in cal if wk(r.get('startDateTime')) is not None] +
                [W.file_text(f['name']) for f, _, _, _ in mine])
    source = W.source_fingerprint(mail, cal, files, W.rows(a.chats_file) if a.chats_file else None)
    base = view_base(a, raw, source) if a.view_of else None
    if base is None:
        guard_keywords(raw, a.self, subjects)
    errs = focus_errors(a, subjects) if base is None else []     # a view repeats the three-month focus, checked there
    if errs:
        print('ERROR: ' + '; '.join(errs) + '.'); sys.exit(2)
    people, pub, orgs = set(), set(), set()
    for m in mail:
        w = wk(m['t'])
        if w is None: continue
        vol['mail_out' if m['sent'] else 'mail_in'][w] += 1
        for k, r in kw.items():
            if r.search(m['s'] or ''): grid[k][w] += 1
        snd = (m['from'] or '').lower()
        if '@' in snd and not is_self(snd):
            people.add(snd)
            dom = snd.split('@')[1]
            o = W.uk_public_org(dom)
            if o and not (excl and excl.search(dom)): pub.add(o)
            d = W.external_domain(snd, own, excl)
            if d: orgs.add(W.org_root(d))
    for r in cal:
        w = wk(r.get('startDateTime'))
        if w is None: continue
        vol['meet'][w] += 1
        for k, rr in kw.items():
            if rr.search(r.get('subject') or ''): grid[k][w] += 1
    if files is not None:
        vol['files'] = [0] * weeks
        for f, w, e, when in frows:
            vol['files'][w] += 1
        for f, w, e, when in mine:
            text = W.file_text(f['name'])
            for k, rr in kw.items():
                if rr.search(text): grid[k][w] += 1
    labels = W.column_labels(win)
    meta = {'tool': 'work-iq-sphere count_signals', 'version': W.VERSION, 'self': a.self, 'owner': W.addresses(a.self)[0]}
    meta.update(W.window_meta(win))
    meta.update({'end': win['end'].isoformat(), 'fingerprint': W.fingerprint(mail, cal, start, weeks, files, wk=wk),
                 'generatedAt': W.stamp(a.now)})
    meta['keywords'] = raw
    out = {'grid': grid, 'vol': vol, 'senders': len(people), 'orgs': len(orgs), 'pub_orgs': len(pub), 'chats': a.chats,
           'weeks': labels, 'meta': meta}
    if files is not None:
        out['files'] = W.file_summary(frows, wk)
        meta['files'] = {'read': len(files), 'inWindow': len(frows), 'skipped': fstats.get('skipped', 0)}
    if a.focus_type:
        out['focus'] = count_focus(a, mail, cal, frows, kw, wk, weeks, files is not None)
        meta['focus'] = {'type': a.focus_type, 'regex': a.focus_regex,
                         'domains': sorted({W.org_root(d.strip().lower()) for d in a.focus_domains.split('|') if d.strip()})}
    meta['source'] = source
    if base is not None:
        meta['viewOf'] = {'digest': base['meta'].get('digest'), 'fingerprint': base['meta'].get('fingerprint')}
    meta['digest'] = W.signals_digest(out)
    json.dump(out, open(a.out, 'w', encoding='utf-8'))
    tot = sum(vol['mail_in']) + sum(vol['mail_out']) + sum(vol['meet']) + a.chats
    summary = {'status': 'ok', 'total_signals': tot, 'emails': sum(vol['mail_in']) + sum(vol['mail_out']),
               'mail_in': sum(vol['mail_in']), 'mail_out': sum(vol['mail_out']), 'calendar_events': sum(vol['meet']),
               'chats': a.chats, 'senders': len(people), 'external_orgs': len(orgs), 'uk_public_orgs': len(pub),
               'fingerprint': meta['fingerprint'], 'theme_totals': {k: sum(v) for k, v in grid.items()}}
    if files is not None:
        fs = out['files']
        summary['total_signals'] = tot + fs['worked_on']
        summary['files_worked_on'], summary['files_edited'], summary['files_opened'] = fs['worked_on'], fs['edited'], fs['opened']
        summary['files_created'], summary['file_sites'], summary['files_by_container'] = fs['created'], fs['sites'], fs['byContainer']
        summary['files_per_%s' % win['unit']] = vol['files']
    if a.focus_type:
        fv = out['focus']['vol']
        fs = {'type': a.focus_type, 'emails': sum(fv['mail_in']) + sum(fv['mail_out']), 'calendar_events': sum(fv['meet']), 'chats': sum(fv['chats'])}
        if 'files' in fv:
            fs['files_worked_on'] = sum(fv['files'])
        fs['total_signals'] = sum(v for k, v in fs.items() if k != 'type')
        fs['theme_totals'] = {k: sum(v) for k, v in out['focus']['grid'].items()}
        summary['focus'] = fs
    print(json.dumps(summary))

def count_focus(a, mail, cal, frows, kw, wk, n, with_files):
    """signals.focus: per column, what is about the focus, and every keyword series inside that subset."""
    rx = re.compile(a.focus_regex, re.I)
    doms = {W.org_root(d.strip().lower()) for d in (a.focus_domains or '').split('|') if d.strip()}
    def from_focus(addr):
        x = (addr or '').strip().lower()
        return bool(doms) and '@' in x and W.org_root(x.rsplit('@', 1)[1].strip('>').strip()) in doms
    vol = {'mail_in': [0] * n, 'mail_out': [0] * n, 'meet': [0] * n, 'chats': [0] * n}
    if with_files:
        vol['files'] = [0] * n
    grid = {k: [0] * n for k in kw}
    for m in mail:
        w = wk(m['t'])
        if w is None or not (rx.search(m['s'] or '') or (not m['sent'] and from_focus(m['from']))):
            continue
        vol['mail_out' if m['sent'] else 'mail_in'][w] += 1
        for k, r in kw.items():
            if r.search(m['s'] or ''): grid[k][w] += 1
    for r in cal:
        w = wk(r.get('startDateTime'))
        if w is None or not (rx.search(r.get('subject') or '') or any(from_focus(addr) for _, addr in W.parse_attendees(r.get('attendees')))):
            continue
        vol['meet'][w] += 1
        for k, rr in kw.items():
            if rr.search(r.get('subject') or ''): grid[k][w] += 1
    if a.chats_file:
        for c in W.rows(a.chats_file):
            w = wk(c.get('lastUpdatedDateTime'))
            if w is not None and c.get('chatType') in ('group', 'oneOnOne') and rx.search(c.get('topic') or ''):
                vol['chats'][w] += 1
    for f, w, e, when in frows:
        text = W.file_text(f['name'])
        if not (rx.search(text) or rx.search(f['name']) or (f['containerType'] != 'OneDrive' and rx.search(f['container'] or ''))):
            continue
        vol['files'][w] += 1
        if e:                                       # only files the person edited or created feed keyword series
            for k, rr in kw.items():
                if rr.search(text): grid[k][w] += 1
    return {'vol': vol, 'grid': grid}

if __name__ == '__main__':
    main()
