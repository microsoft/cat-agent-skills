#!/usr/bin/env python3
"""Discover what THIS person's work is about, from their own ExecuteSql results.

Writes discovery.json: candidate entities with evidence counts taken only from the person's own mail,
calendar, chats and (with --files) files (recurring meetings, busy threads, external organisations, people, things
they send repeatedly, escalation IDs, upcoming meetings, frequent subject terms, files they edited and the sites
holding them). Every node in workiq_config.json
must cite at least one of these item ids in its "from" list, and build_workiq.py checks it, so nothing on
the sphere can come from the bundled example or from anybody else's work.

Usage:
  python discover.py --messages mail1.jsonl [--messages mail2.jsonl] --calendar cal.jsonl --folders folders.jsonl
      --start 2026-07-20 --weeks 14 --self user@contoso.com --self "Display Name"
      [--chats-file chats.json] [--own-domains "contoso.com|contoso.onmicrosoft.com"]
      [--exclude-domains "parish|school"] [--today 2026-10-21] [--now 2026-10-21T11:40:00Z] [--files working/files.json]
      --out working/discovery.json
Window (version 1.7), one of:
  --start <Monday> --weeks N                 N weekly columns (as in 1.6; the quarter is --weeks 14)
  --window week|month|quarter --today <day>  week = the last 7 days including today, day by day (7 columns);
                                             month = the 4 full weeks before this week plus this week (5 columns);
                                             quarter = the 13 full weeks before this week plus this week (14 columns)
  --start <day> --unit day|week --columns N  any number of day or week columns
  scripts/window.py prints the exact flags for a choice. meta records the window: weekly windows keep the 1.6 fields
  (start and weeks, no unit), day-by-day windows add "unit": "day" and "columns". A day-by-day window also lists the
  meetings from its end to the end of this week as upcoming (meta.lookAhead); they are never counted, never feed
  people, organisations or terms, and are not part of the fingerprint.
chats.json (optional): the chats listed by the tool script, as a JSON array of {topic, chatType, lastUpdatedDateTime}.
files.json (optional, version 1.6): the person's own OneDrive and SharePoint file activity written by
  collect_files_recipe.py, stamped with its owner (meta.owner must be the first --self address). Adds "file:" items for
  the files they edited or created in the window and "site:" items for the SharePoint and Teams sites holding them, and
  the names of those files count towards the subject terms. Files they only opened are counted in meta.files but are
  never items, terms or evidence. The skill's own files and outputs (whoever made them) are skipped. Without --files
  the output is the same as without the files source.
Personal webmail (outlook.com, gmail.com, hotmail.com and the rest of wiq_data.CONSUMER, subdomains included) is never
  an "org:" item: those are personal contacts, not organisations (version 1.7.1; count_signals.py leaves them out of
  external_orgs the same way). --exclude-domains is for other personal domains (schools, clubs, family).
Sent Items rows whose sender is a legacy Exchange X500 address ("/O=EXCHANGELABS/...") count as sent by the first
  --self address (version 1.7.1), exactly as in count_signals.py.
--now: the current UTC time; meetings before it are not listed as upcoming, and it is the generatedAt stamp (so the
  same command gives the same file).
Views (version 1.8): one data collection feeds three views of the sphere (the last 7 days, the last month, the last three
  months). Every item now records "cols" (its count per column of the window) and its "first" and "last" dates, and
  meta.source fingerprints everything read, whatever the window, so the three runs can be tied to the same data.
  --view-of <the three-month discovery.json>: run on exactly the same result files for the week or the month window; it
  refuses other data, another person or another day, and writes "tracked": every item of the three-month discovery that
  has activity in this window, counted the same way but without the thresholds that make an item (a weekly meeting
  that met once this week still counts), so the build can size, show or hide each node in that view.
"""
import argparse, json, re, sys, os, datetime as dt
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wiq_data as W

AUTOMATED = re.compile(r'(no-?reply|do-?not-?reply|notification|notify|postmaster|mailer-daemon|newsletter|news|digest|updates?|'
                       r'alerts?|marketing|info|hello|support|service|team|admin|bounce|azuredevops|calendar|events?|mailer|reply)[^@]*@|'
                       r'^[^@]*(update|noreply|no-reply)[-.0-9a-f]*@', re.I)

ESC = re.compile(r'\b(?:Action|UAT)\s*#?\s*:?\s*(\d{6})\b', re.I)
STOP = set('''a an and are as at be by for from in into is it of on or our re the to this that with your you we i me my
fw fwd aw wg meeting meetings call sync catch up catchup invite invitation update updates follow following question
questions request re: hi hello thanks thank please new next week weekly daily monthly today tomorrow am pm via
microsoft call: join session sessions accepted declined tentative canceled cancelled copy reminder notification shared
monday tuesday wednesday thursday friday saturday sunday jan feb mar apr may jun jul aug sep sept oct nov dec january
february march april june july august september october november december 2025 2026 2027 q1 q2 q3 q4 fy26 fy27 fy28
about all also any can how what when where who will not out up just more one two'''.split())

def _act(agg, **extra):
    out = {'cols': list(agg['c']), 'first': agg['f'], 'last': agg['l']}
    out.update(extra)
    return out

def track(base_items, items, series, threads, sent, sent_act, org, people, esc, chat_act, terms, term_cols, mine, sites, selves, n):
    """Version 1.8: every item of the three-month discovery that has activity in this window, counted exactly as the
    items are, without the thresholds (a weekly meeting that met once this week, a thread with one email, a person who
    wrote twice, a term outside the busiest 120 still count). Keys are the three-month item ids."""
    by = {}
    def merge(iid, rec):
        old = by.get(iid)
        if old is None:
            by[iid] = rec; return
        for k, v in rec.items():                # two subjects that make the same id add up
            if k == 'cols':
                old[k] = [x + y for x, y in zip(old[k], v)]
            elif k == 'first':
                old[k] = min(x for x in (old.get(k), v) if x) if (old.get(k) or v) else ''
            elif k == 'last':
                old[k] = max(old.get(k) or '', v or '')
            elif isinstance(v, int) and not isinstance(v, bool):
                old[k] = old.get(k, 0) + v
    # a meeting series, a thread, a thing sent and a term are the ONE subject (or word) the three-month item names, counted
    # in this window as a fresh run of it counts that subject; other subjects that make the same id are not added to it
    for iid, it in base_items.items():
        kind, lab = it.get('kind'), it.get('label')
        if kind == 'meeting' and lab in series and series[lab]['n']:
            by[iid] = _act(series[lab], count=series[lab]['n'], weeks=len(series[lab]['weeks']))
        elif kind == 'thread' and lab in threads and threads[lab]['in'] + threads[lab]['out']:
            t = threads[lab]
            by[iid] = _act(t, count=t['in'] + t['out'], **{'in': t['in'], 'out': t['out']})
        elif kind == 'sent' and sent.get(lab):
            by[iid] = _act(sent_act[lab], count=sent[lab])
        elif kind == 'term' and terms.get(lab):
            by[iid] = {'count': terms[lab], 'cols': list(term_cols[lab])}
    for root, o in org.items():
        if o['mails'] + o['meetings']:
            merge('org:' + root, _act(o, count=o['mails'] + o['meetings'], mails=o['mails'], meetings=o['meetings'], people=len(o['people'])))
    for addr, p in people.items():
        if p['meetings'] + p['mails']:
            merge('person:' + addr, _act(p, count=p['meetings'] + p['mails'], meetings=p['meetings'], mails=p['mails']))
    for num, e in esc.items():
        if e['count']:
            merge('esc:' + num, _act(e, count=e['count']))
    for cid, c in chat_act.items():
        if sum(c['c']):
            merge(cid, _act(c, count=sum(c['c'])))
    out = {}
    files_by = defaultdict(list)
    for f, w, e, when in mine:
        files_by[(W.file_label(f['name']), f['container'])].append((w, when))
    sites_by = defaultdict(list)
    for st in sites.values():
        sites_by[st['label']].append(st)
    for iid, it in base_items.items():
        kind = it.get('kind')
        if kind == 'file':
            acts = files_by.get((it.get('label'), it.get('container'))) or []
            if acts:
                cols = [0] * n
                for w, _ in acts:
                    cols[w] += 1
                last = max(when for _, when in acts)
                out[iid] = {'count': len(acts), 'edited': len(acts), 'cols': cols, 'first': min(when for _, when in acts)[:10],
                            'last': last[:10]}
        elif kind == 'site':
            sts = [st for st in sites_by.get(it.get('label')) or [] if st['edited']]
            if sts:
                out[iid] = {'count': sum(st['n'] for st in sts), 'edited': sum(st['edited'] for st in sts),
                            'cols': [sum(x) for x in zip(*[st['c'] for st in sts])], 'last': max(st['last'] for st in sts)}
        elif kind == 'upcoming':
            if iid in items:
                out[iid] = {'count': 1, 'when': items[iid].get('when')}
        elif iid in by and by[iid].get('count'):
            out[iid] = by[iid]
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--messages', action='append', default=[]); ap.add_argument('--calendar', action='append', default=[])
    ap.add_argument('--folders'); ap.add_argument('--chats-file')
    ap.add_argument('--files', help='files.json from collect_files_recipe.py (your own OneDrive and SharePoint file activity)')
    W.add_window_args(ap)
    ap.add_argument('--self', action='append', default=[], required=True)
    ap.add_argument('--own-domains', default=''); ap.add_argument('--exclude-domains', default='')
    ap.add_argument('--today'); ap.add_argument('--now', help='optional UTC time (e.g. 2026-10-21T11:40:00Z) so meetings earlier today are not listed as upcoming')
    ap.add_argument('--view-of', help='the three-month discovery.json (version 1.8): count its items in this window too')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    win, why = W.window_from_args(a, today)
    if win is None:
        print('ERROR: ' + why); sys.exit(2)
    start, weeks, end = win['start'], win['columns'], win['end']
    wk = W.column_index(win)
    is_self = W.self_matcher(a.self)
    own = W.own_domains(a.self, a.own_domains)
    excl = re.compile(a.exclude_domains, re.I) if a.exclude_domains else None
    all_mail = W.load_mail(a.messages, a.folders, a.self)
    mail = [m for m in all_mail if wk(m['t']) is not None]
    all_cal = W.load_calendar(a.calendar)
    cal = [r for r in all_cal if wk(r.get('startDateTime')) is not None]
    a_end = W.ahead_end(win, today)            # day-by-day windows: the rest of this week, listed but never counted
    ahead = [r for r in all_cal if a_end > end and end.isoformat() <= (r.get('startDateTime') or '')[:10] < a_end.isoformat()]
    if not mail and not cal:
        print('ERROR: no mail or calendar rows fall inside the window %s to %s' % (start, end)); sys.exit(2)
    if not W.addresses(a.self):
        print('ERROR: pass your own UPN with --self (first), then your mail address if it differs, then your display name'); sys.exit(2)
    fstats = {}
    files = W.load_files(a.files, a.self, fstats) if a.files else None
    frows = W.files_in_window(files, wk) if files is not None else []
    if files is not None:
        errs = W.files_owner_errors(a.files, a.self, files)
        if errs:
            print('ERROR: ' + '; '.join(errs) + '. Collect your own files with scripts/collect_files_recipe.py, or leave --files out.'); sys.exit(2)
    errs = W.mailbox_errors(a.messages, mail, a.self, W.fingerprint(mail, cal, start, weeks, files, wk=wk), win, cal, files)
    if errs:
        print('ERROR: ' + '; '.join(errs) + '. Run the ExecuteSql queries for the signed-in user and pass only those result files.'); sys.exit(2)
    chat_rows = W.rows(a.chats_file) if a.chats_file else None
    source = W.source_fingerprint(all_mail, all_cal, files, chat_rows)
    base = None
    if a.view_of:
        try:
            base = json.load(open(a.view_of, encoding='utf-8'))
            bm = base['meta']
        except (OSError, ValueError, KeyError, TypeError):
            print('ERROR: --view-of %s is not a discovery.json written by discover.py' % a.view_of); sys.exit(2)
        why = []
        if [x.strip().lower() for x in bm.get('self') or []] != [x.strip().lower() for x in a.self]:
            why.append('it was made with --self %s' % ', '.join(bm.get('self') or ['nobody']))
        if bm.get('today') != today.isoformat():
            why.append('it was made on %s, not %s' % (bm.get('today'), today.isoformat()))
        if not bm.get('source') or bm.get('source') != source:
            why.append('it read other result files (or other chats or files) than this run')
        bwin = W.window_from_meta(bm)
        if bwin is None or start < bwin['start'] or end > bwin['end']:
            why.append('its window does not hold this one')
        if why:
            print('ERROR: --view-of %s is not the three-month run of this same data (%s). Run discover.py for the week and the '
                  'month with exactly the same --messages, --calendar, --folders, --chats-file, --files, --self and --today as '
                  'the three-month run, and pass its discovery.json.' % (a.view_of, '; '.join(why))); sys.exit(2)
    unk, tot = W.unknown_folder_rows(a.messages, a.folders)
    if not a.folders:
        print('WARNING: no --folders file, so Sent Items, Junk Email and Drafts are not recognised')
    elif tot and unk > 0.1 * tot:
        print('WARNING: %d of %d mail rows sit in folders missing from --folders (subfolders, or mail from another mailbox mixed in)' % (unk, tot))
    items = {}

    # recurring meetings and external one-offs
    def act():
        return {'c': [0] * weeks, 'f': '', 'l': ''}
    def touch(agg, col, when):
        """Version 1.8: count one piece of activity in its column and keep the first and last dates."""
        if col is None:
            return
        agg['c'][col] += 1
        d = (when or '')[:10]
        if d:
            if not agg['f'] or d < agg['f']:
                agg['f'] = d
            if d > agg['l']:
                agg['l'] = d
    series = defaultdict(lambda: dict(act(), n=0, weeks=set(), orgs=Counter(), people=Counter(), last=''))
    people = defaultdict(lambda: dict(act(), name='', meetings=0, mails=0))
    org = defaultdict(lambda: dict(act(), mails=0, meetings=0, people=set(), subjects=Counter()))
    upcoming = []
    for r in cal:
        subj = W.series_key(W.norm_subject(r.get('subject')))
        if not subj:
            continue
        col = wk(r.get('startDateTime'))
        s = series[subj]; s['n'] += 1; s['weeks'].add(col); s['last'] = max(s['last'], r.get('startDateTime') or '')
        touch(s, col, r.get('startDateTime'))
        others, seen_people, orgs_here = [], set(), set()
        for name, addr in W.parse_attendees(r.get('attendees')):
            a_ = addr.lower()
            if is_self(addr) or is_self(name) or a_ in seen_people:
                continue
            seen_people.add(a_)
            others.append((name, a_))
            p = people[a_]; p['meetings'] += 1; p['name'] = p['name'] or name
            touch(p, col, r.get('startDateTime'))
            s['people'][a_] += 1
            d = W.external_domain(addr, own, excl)
            if d:
                root = W.org_root(d)
                org[root]['people'].add(a_)
                orgs_here.add(root)
        for root in sorted(orgs_here):              # one calendar event counts once per organisation, however many attend
            o = org[root]; o['meetings'] += 1; o['subjects'][subj] += 1
            touch(o, col, r.get('startDateTime'))
            s['orgs'][root] += 1
        try:
            when = dt.date.fromisoformat((r.get('startDateTime') or '')[:10])
        except ValueError:
            when = None
        later = (r.get('startDateTime') or '')[:19] >= a.now[:19] if a.now else True
        if when and when >= today and later:
            upcoming.append((r.get('startDateTime'), subj, r.get('responseStatus') or '', others))
    for r in ahead:       # the look-ahead: listed for "prep me for" questions only, so no people, organisations or series
        subj = W.series_key(W.norm_subject(r.get('subject')))
        if not subj:
            continue
        others, seen_people = [], set()
        for name, addr in W.parse_attendees(r.get('attendees')):
            a_ = addr.lower()
            if is_self(addr) or is_self(name) or a_ in seen_people:
                continue
            seen_people.add(a_)
            others.append((name, a_))
        later = (r.get('startDateTime') or '')[:19] >= a.now[:19] if a.now else True
        if (r.get('startDateTime') or '')[:10] >= today.isoformat() and later:
            upcoming.append((r.get('startDateTime'), subj, r.get('responseStatus') or '', others))
    meeting_people = {}
    for subj, s in series.items():
        if s['n'] >= 2 or s['orgs']:
            mid = 'meeting:' + W.slug(subj)
            items[mid] = {'kind': 'meeting', 'label': subj, 'count': s['n'], 'weeks': len(s['weeks']),
                          'orgs': [o for o, _ in s['orgs'].most_common(3)], 'last': s['last'][:10], 'first': s['f'], 'cols': s['c']}
            meeting_people[mid] = [a for a, _ in s['people'].most_common(8)]

    # mail threads, organisations, people, things the person sends repeatedly
    threads = defaultdict(lambda: dict(act(), orgs=Counter(), **{'in': 0, 'out': 0}))
    sent = Counter()
    sent_act = defaultdict(act)
    for m in mail:
        subj = W.series_key(W.norm_subject(m['s']))
        t = threads[subj] if subj else None
        col = wk(m['t'])
        if t is not None: touch(t, col, m['t'])
        if m['sent']:
            if t is not None: t['out'] += 1
            if subj: sent[subj] += 1; touch(sent_act[subj], col, m['t'])
            continue
        if t is not None: t['in'] += 1
        snd = (m['from'] or '').strip()
        if '@' in snd and not is_self(snd):
            people[snd.lower()]['mails'] += 1
            touch(people[snd.lower()], col, m['t'])
            d = W.external_domain(snd, own, excl)
            if d:
                o = org[W.org_root(d)]; o['mails'] += 1; o['people'].add(snd.lower())
                touch(o, col, m['t'])
                if subj: o['subjects'][subj] += 1
                if t is not None: t['orgs'][W.org_root(d)] += 1
    for subj, t in threads.items():
        if t['in'] + t['out'] >= 3:
            items['thread:' + W.slug(subj)] = {'kind': 'thread', 'label': subj, 'count': t['in'] + t['out'], 'in': t['in'],
                                               'out': t['out'], 'orgs': [o for o, _ in t['orgs'].most_common(3)],
                                               'first': t['f'], 'last': t['l'], 'cols': t['c']}
    for subj, n in sent.items():
        if n >= 2:
            items['sent:' + W.slug(subj)] = {'kind': 'sent', 'label': subj, 'count': n, 'first': sent_act[subj]['f'],
                                             'last': sent_act[subj]['l'], 'cols': sent_act[subj]['c']}
    for root, o in org.items():
        humans = {p for p in o['people'] if not AUTOMATED.search(p)}
        items['org:' + root] = {'kind': 'org', 'label': root, 'count': o['mails'] + o['meetings'], 'mails': o['mails'],
                                'meetings': o['meetings'], 'people': len(o['people']),
                                'automated': o['meetings'] == 0 and len(humans) == 0,
                                'topSubjects': [s for s, _ in o['subjects'].most_common(3)],
                                'first': o['f'], 'last': o['l'], 'cols': o['c']}
    cand = []
    for addr, p in people.items():
        if AUTOMATED.search(addr):
            continue
        if p['meetings'] >= 1 or p['mails'] >= 3:
            cand.append((p['meetings'] * 3 + p['mails'], addr, p))
    for score, addr, p in sorted(cand, key=lambda x: (-x[0], x[1]))[:300]:
        d = W.external_domain(addr, own, excl)
        items['person:' + addr] = {'kind': 'person', 'label': p['name'] or addr.split('@')[0], 'email': addr,
                                   'count': p['meetings'] + p['mails'], 'meetings': p['meetings'], 'mails': p['mails'],
                                   'score': score, 'external': bool(d), 'org': W.org_root(d) if d else None,
                                   'first': p['f'], 'last': p['l'], 'cols': p['c']}

    for mid, addrs in meeting_people.items():
        items[mid]['people'] = ['person:' + a for a in addrs if ('person:' + a) in items][:6]

    # escalation IDs from subjects and chat topics; chats in the window
    esc = defaultdict(lambda: dict(act(), count=0, first='', subjects=Counter()))
    def take_esc(text, when, col=None):
        for num in ESC.findall(text or ''):
            e = esc[num]; e['count'] += 1; e['first'] = min(e['first'] or when or '', when or '') or e['first']
            e['subjects'][W.norm_subject(text)] += 1
            touch(e, col, when)
    for m in mail: take_esc(m['s'], (m['t'] or '')[:10], wk(m['t']))
    for r in cal: take_esc(r.get('subject'), (r.get('startDateTime') or '')[:10], wk(r.get('startDateTime')))
    chats = {'group': 0, 'oneOnOne': 0, 'meeting': 0, 'listed': 0}
    chat_act = defaultdict(act)
    if a.chats_file:
        for c in chat_rows:
            chats['listed'] += 1
            t = c.get('chatType') or ''
            col = wk(c.get('lastUpdatedDateTime'))
            if col is None:
                continue
            if t in chats: chats[t] += 1
            topic = (c.get('topic') or '').strip()
            if topic:
                take_esc(topic, (c.get('lastUpdatedDateTime') or '')[:10], col)
                if t == 'group':
                    cid = 'chat:' + W.slug(topic)
                    touch(chat_act[cid], col, c.get('lastUpdatedDateTime'))
                    it = items.setdefault(cid, {'kind': 'chat', 'label': topic, 'count': 0})
                    it['count'] += 1
                    it['last'], it['cols'] = chat_act[cid]['l'], chat_act[cid]['c']
    for num, e in esc.items():
        items['esc:' + num] = {'kind': 'escalation', 'label': num, 'count': e['count'], 'first': e['first'],
                               'subjects': [s for s, _ in e['subjects'].most_common(2)], 'last': e['l'], 'cols': e['c']}

    # files the person edited or created in the window, and the SharePoint and Teams sites that hold them; files they
    # only opened are counted in meta.files but never become items, terms or evidence
    mine = [x for x in frows if x[2]]
    sites = {}
    if files is not None:
        order = sorted(mine, key=lambda x: x[0]['id'])
        order.sort(key=lambda x: x[3], reverse=True)
        site_ids = {}
        for f, w, e, when in order:
            label = W.file_label(f['name'])
            fid = 'file:' + W.slug(label)
            if fid in items:
                fid = 'file:' + W.slug(label + ' ' + f['container'])
            n = 2
            while fid in items:
                fid = 'file:%s-%d' % (W.slug(label), n); n += 1
            items[fid] = {'kind': 'file', 'label': label, 'count': 1, 'edited': e,
                          'created': f['createdByMe'] and wk(f['createdDateTime']) is not None, 'type': f['type'],
                          'container': f['container'], 'containerType': f['containerType'], 'last': when[:10], 'week': w,
                          'source': f['source']}
            site_ids[f['id']] = fid
        for f, w, e, when in sorted(frows, key=lambda x: (x[3], x[0]['id']), reverse=True):
            key = W.file_site_key(f)
            if key:
                st = sites.setdefault(key, {'label': f['container'], 'files': [], 'n': 0, 'edited': 0, 'types': Counter(), 'last': '',
                                            'c': [0] * weeks})
                st['n'] += 1; st['edited'] += e; st['types'][f['containerType']] += 1
                if e: st['c'][w] += 1
                st['last'] = max(st['last'], when[:10])
                if e:
                    st['files'].append(site_ids[f['id']])
        for key in sorted(sites, key=lambda k: (-sites[k]['n'], k)):
            st = sites[key]
            if not st['edited']:
                continue                            # a site where the person only opened files is not their work
            sid = 'site:' + W.slug(st['label']); n = 2
            while sid in items:
                sid = 'site:%s-%d' % (W.slug(st['label']), n); n += 1
            items[sid] = {'kind': 'site', 'label': st['label'], 'count': st['n'], 'edited': st['edited'],
                          'containerType': st['types'].most_common(1)[0][0], 'last': st['last'], 'files': st['files'][:8],
                          'cols': st['c']}
            for fid in st['files']:
                items[fid]['site'] = sid

    # frequent subject terms (for themes and products)
    terms = Counter()
    term_cols = defaultdict(lambda: [0] * weeks)
    for subj, col in ([(W.norm_subject(m['s']), wk(m['t'])) for m in mail] + [(W.norm_subject(r.get('subject')), wk(r.get('startDateTime'))) for r in cal]
                      + [(W.file_text(f['name']), w) for f, w, _, _ in mine]):
        words = re.findall(r"[^\W_][\w+#&'-]*[^\W_]|[^\W_]", subj.lower())
        seen = set()
        for i, w in enumerate(words):
            if w not in STOP and len(w) > 2 and not w.isdigit(): seen.add(w)
            if i + 1 < len(words) and w not in STOP and words[i + 1] not in STOP and len(w) > 1 and len(words[i + 1]) > 1:
                seen.add(w + ' ' + words[i + 1])
        terms.update(sorted(seen))
        for t_ in seen:
            term_cols[t_][col] += 1
    for name in a.self:
        for w in re.findall(r'[a-z]+', name.lower()): terms.pop(w, None)
    for term, n in sorted(terms.items(), key=lambda kv: (-kv[1], kv[0]))[:120]:
        if n >= 3:
            items['term:' + W.slug(term)] = {'kind': 'term', 'label': term, 'count': n, 'cols': term_cols[term]}

    upcoming.sort(key=lambda u: u[0] or '')
    for when, subj, resp, others in upcoming[:20]:
        items.setdefault('upcoming:' + W.slug(subj), {'kind': 'upcoming', 'label': subj, 'when': when, 'response': resp, 'count': 1,
                                                      'attendees': [('person:' + a) if ('person:' + a) in items else (n or a) for n, a in others][:10]})

    fp = W.fingerprint(mail, cal, start, weeks, files, wk=wk)
    top = {}
    for kind in ('meeting', 'thread', 'org', 'person', 'sent', 'escalation', 'chat', 'term', 'upcoming') + (('file', 'site') if files is not None else ()):
        ids = [k for k, v in items.items() if v['kind'] == kind]
        if kind == 'upcoming':
            ids.sort(key=lambda k: items[k]['when'])
        elif kind == 'file':
            ids.sort(); ids.sort(key=lambda k: items[k]['last'], reverse=True)
        elif kind == 'person':
            ids.sort(key=lambda k: (-items[k]['score'], k))
        elif kind == 'org':
            ids.sort(key=lambda k: (items[k]['automated'], -items[k]['count'], k))
        else:
            ids.sort(key=lambda k: (-items[k]['count'], k))
        top[kind] = ids
    meta = {'tool': 'work-iq-sphere discover', 'version': W.VERSION, 'self': a.self, 'owner': W.addresses(a.self)[0]}
    meta.update(W.window_meta(win))
    meta.update({'end': end.isoformat(), 'today': today.isoformat(), 'fingerprint': fp, 'emails': len(mail),
                 'calendarEvents': len(cal), 'chats': chats, 'generatedAt': W.stamp(a.now)})
    if a_end > end:
        meta['lookAhead'] = {'end': a_end.isoformat(), 'calendarRows': len(ahead)}
    meta['source'] = source
    out = {'meta': meta, 'items': items, 'top': top}
    if base is not None:                       # version 1.8: the three-month items, counted in this window
        meta['viewOf'] = {'fingerprint': base['meta'].get('fingerprint'), 'source': base['meta'].get('source'),
                          'start': base['meta'].get('start'), 'weeks': base['meta'].get('weeks'), 'columns': base['meta'].get('columns'),
                          'unit': base['meta'].get('unit')}
        out['tracked'] = track(base.get('items') or {}, items, series, threads, sent, sent_act, org, people, esc, chat_act,
                               terms, term_cols, mine, sites, a.self, weeks)
    if files is not None:
        out['meta']['files'] = dict(W.file_summary(frows, wk), read=len(files), skipped=fstats.get('skipped', 0),
                                    fingerprintWithoutFiles=W.fingerprint(mail, cal, start, weeks, wk=wk))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    status = {'status': 'ok', 'out': a.out, 'fingerprint': fp, 'emails': len(mail), 'calendar_events': len(cal),
              'chats_in_window': {k: v for k, v in chats.items() if k != 'listed'}, 'items': len(items),
              'by_kind': {k: len(v) for k, v in top.items()}}
    if files is not None:
        status['files'] = {k: v for k, v in out['meta']['files'].items() if k != 'fingerprintWithoutFiles'}
    print(json.dumps(status))
    for kind, n in (('meeting', 15), ('thread', 15), ('org', 15), ('person', 12), ('sent', 8), ('escalation', 30), ('term', 25), ('upcoming', 6)):
        rows_ = ['%s (%s)' % (items[k]['label'][:60], items[k]['when'][:16] if kind == 'upcoming' else
                               ('%d, looks automated' % items[k]['count'] if items[k].get('automated') else items[k]['count'])) for k in top[kind][:n]]
        if rows_:
            print('%s: %s' % (kind.upper(), ' | '.join(rows_)))
    if files is not None:
        for kind, n in (('file', 15), ('site', 10)):
            rows_ = ['%s (%s)' % (items[k]['label'][:60], ('%s, %s' % ('created' if items[k]['created'] else 'edited', items[k]['container'][:30]))
                                   if kind == 'file' else '%d files, %d edited' % (items[k]['count'], items[k]['edited'])) for k in top[kind][:n]]
            if rows_:
                print('%s: %s' % (kind.upper(), ' | '.join(rows_)))
    print('Every entity you put on the sphere must list one or more of these item ids in "from" (for example "%s").'
          % (top['meeting'][0] if top['meeting'] else next(iter(items))))

if __name__ == '__main__':
    main()
