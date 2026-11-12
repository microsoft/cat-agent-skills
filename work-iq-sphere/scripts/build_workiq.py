#!/usr/bin/env python3
"""Build a self-contained Work IQ sphere HTML from ONE person's own config.

Usage:
  python build_workiq.py --config working/workiq_config.json --discovery working/discovery.json
      [--view week working/views/discovery_week.json working/views/signals_week.json]
      [--view month working/views/discovery_month.json working/views/signals_month.json]
      --out "working/Work IQ Sphere.html" [--customer-safe] [--template path] [--official-slide path] [--previous saved.json]

Views (version 1.8): one data collection, three views in one sphere (Week, Month, 3 months; the toggle starts on 3 months).
The config, its discovery.json and its signals are the three-month run; each --view adds the week or the month, from
discover.py and count_signals.py run with that view's window flags and --view-of on exactly the same result files. The
guard binds every view to the same person, day, collected data (meta.source), keywords and focus. Text that every view
shows (details, Skills questions and answers, groundings, outputs, the example chain) writes its counts as placeholders
the build fills for each view: {#<item id>.<count|mails|meetings|people|in|out|edited|weeks|first|last>},
{#signal:<key>.<sum|max|last|nonzero|peak>}, {#period} and {#unit}; with views it may hold no typed-in count and no date
outside the last 7 days. For each view the build computes node sizes and which nodes show (an entity with no activity in
that view is hidden), each node's evidence, the Memory callouts of the week and the month, and 3 to 5 "In this view"
findings. Without --view the sphere has one view, as in 1.7 (placeholders are still filled for its window).

Fresh-analysis guard (runs on every build, there is no switch to turn it off):
  * the config is stamped with its owner (meta.ownerUpn, skillVersion 1.6 or later, so older configs are rebuilt fresh);
  * signals and discovery.json were both produced from that same person's data (same --self, same fingerprint, same window,
    same files) and the signals block is exactly what count_signals.py wrote (digest, totals, chats, weeks, files);
  * the window (version 1.7): discovery, signals and the config's "weeks" cover the same columns (days for the week,
    weeks otherwise), and meta.choices.window (week, month, quarter, last-<N>-weeks, since-<date>) is the window they
    were counted for; a config without meta.choices (made by 1.6) is weekly and means all my work;
  * a focus (meta.choices.focus, version 1.7): the focus entity exists with the chosen class and rests on the person's own
    discovery; the signals were counted for that same focus (count_signals.py --focus-..., recorded in signals.meta.focus
    and sealed by the digest), never above the counts for all their work nor below what their discovery shows about it;
    every other entity links to it within 2 relationships that do not pass through the hub, and its own evidence
    co-occurs with the focus (a discovery item that names it or comes from its domains, a person at its meetings, or a
    keyword series with hits about it); outputs too; a customer focus has no other customer and nothing that cites or is
    named after another organisation; every Skills question names or highlights it, and the headline names it with its
    {token};
  * every customer, product, programme, theme, escalation, asset, person and output cites evidence found in that data
    ("from": discovery item ids, or "signal:<key>" with hits; "stated:<what the user said>" is allowed for products,
    programmes, themes, assets and outputs, and "source:<document>" for internal-module items from a file the user named),
    and every node's name matches the evidence it cites;
  * file evidence (discover.py --files): customers and programmes may cite "site:" items (a site where the person edited
    at least 2 files) and "file:" items, assets and outputs "file:" items; only files the person edited or created are
    items at all, so a file they only opened is never evidence;
  * every Skills question names the person's own entities, is a different kind and cites the items that kind needs;
  * nothing is copied from the bundled example or from an earlier version's sample.
Other checks: required keys, entity ids referenced by relations, questions and {tokens}, no em or en dashes, lane keys,
numbers and dates in the text, and in customer-safe mode no real name, address, number, site or file name.
"""
import argparse, json, math, os, re, statistics, sys, html, base64, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wiq_data as W

DEFAULT_TPL = os.path.join(HERE, '..', 'templates', 'workiq_sphere_template.html')
EXAMPLE = os.path.join(HERE, '..', 'examples', 'example_config.json')
GUARD = os.path.join(HERE, 'guard_data.json')
REQ = ['owner', 'title', 'source', 'weeks', 'signals', 'text', 'lanes', 'memory', 'entities', 'relations', 'questions', 'outputs']
CLASSES = {'hub', 'customer', 'product', 'programme', 'theme', 'uat', 'asset', 'person'}
EVIDENCE_CLASSES = CLASSES - {'hub'}
STATED_OK = {'product', 'programme', 'theme', 'asset'}
KIND_RULE = {'person': ('person:',), 'uat': ('esc:', 'signal:')}
FILE_KIND_OK = {'file:': {'customer', 'programme', 'asset', 'output'}, 'site:': {'customer', 'programme'}}
SITE_MIN_EDITED = 2
MIN_VERSION = (1, 6)    # configs from earlier versions lack question kinds, aka and the signals digest: build them fresh

def fail(msg):
    print('ERROR: ' + msg); sys.exit(2)

def vtuple(v):
    try:
        return tuple(int(x) for x in str(v).split('.')[:3])
    except ValueError:
        return (0,)

def free_texts(cfg):
    """(where, text) for every piece of free text a person writes into a config."""
    for e in cfg.get('entities', []):
        for k in ('detail', 'internalDetail'):
            if e.get(k): yield ('detail of %s' % e.get('id'), e[k])
    for i, q in enumerate(cfg.get('questions', [])):
        yield ('Skills question %d' % (i + 1), q.get('q', ''))
        for line in q.get('answer', []) or []:
            yield ('answer to question %d' % (i + 1), line)
        if q.get('grounding'): yield ('grounding of question %d' % (i + 1), q['grounding'])
    for i, o in enumerate(cfg.get('outputs', [])):
        for k in ('title', 'text', 'internalText'):
            if o.get(k): yield ('output %d %s' % (i + 1, k), o[k])
    for i, m in enumerate(cfg.get('memory', [])):
        yield ('memory callout %d' % (i + 1), m.get('text', ''))
    text = cfg.get('text') or {}
    for k in COPY_TEXT:
        if isinstance(text.get(k), str) and text[k]:
            yield ('text.%s' % k, text[k])
    inte = cfg.get('internal') or {}
    for k in ('nav', 'kicker', 'headline', 'intro', 'note', 'legend', 'totalLabel'):
        if isinstance(inte.get(k), str) and inte[k]: yield ('internal %s' % k, inte[k])
    for c in inte.get('cards', []) or []:
        for k in ('title', 'text'):
            if isinstance(c, dict) and c.get(k): yield ('internal card', c[k])
    for x in (inte.get('kpis') or []) + (inte.get('pillars') or []):
        for k in ('label', 'name', 'text', 'note'):
            if isinstance(x, dict) and isinstance(x.get(k), str) and x[k]: yield ('internal kpi or pillar', x[k])
    for x in cfg.get('entities', []) + cfg.get('outputs', []):
        for f in x.get('from') or []:
            if isinstance(f, str) and f.startswith(('stated:', 'source:')):
                yield ('what you said about "%s"' % (x.get('real') or x.get('title') or ''), f.split(':', 1)[1])

COPY_TEXT = ('headline', 'exampleChain', 'slideTitle', 'slideMemory', 'slideSkills')
LABEL_TEXT = ('kicker', 'period', 'windowLabel', 'sparkRange', 'chatLabel', 'orgLabel', 'uatLabel', 'memoryNote', 'slideSubtitle')
# SKILL.md's own example wording; using it is not copying anybody's work
GENERIC_TEXT = {'three months of my work understood', 'this visual'}

def all_texts(cfg):
    """Every text that reaches the sphere or the slide: free text plus names, labels, owner, title, source and portals."""
    yield from free_texts(cfg)
    for k in ('owner', 'title', 'source'):
        if isinstance(cfg.get(k), str): yield (k, cfg[k])
    text = cfg.get('text') or {}
    for k in LABEL_TEXT:
        if isinstance(text.get(k), str) and text[k]: yield ('text.%s' % k, text[k])
    for e in cfg.get('entities', []):
        for k in ('real', 'safe', 'sector'):
            if isinstance(e.get(k), str) and e[k]: yield ('%s of %s' % (k, e.get('id')), e[k])
    for l in cfg.get('lanes', []):
        if isinstance(l.get('name'), str): yield ('lane name', l['name'])
    for p_ in cfg.get('portals') or []:
        if isinstance(p_, dict) and isinstance(p_.get('name'), str): yield ('portal', p_['name'])
    inte = cfg.get('internal') or {}
    if inte.get('total') is not None: yield ('internal total', str(inte['total']))
    for x in inte.get('kpis') or []:
        if isinstance(x, dict):
            for k in ('value', 'n', 'number'):
                if x.get(k) is not None: yield ('internal kpi value', str(x[k]))

def check_owner(cfg, disc):
    meta = cfg.get('meta')
    if not isinstance(meta, dict) or '@' not in str(meta.get('ownerUpn', '')) or vtuple(meta.get('skillVersion')) < MIN_VERSION:
        fail('this config was not made by a fresh analysis (no owner stamp from version 1.6 or later). Do a New build from '
             'your own data: discover.py, your own keywords.json, count_signals.py, then a new config with meta.ownerUpn. '
             'Never reuse a config from an earlier version, from the examples folder or from another person.')
    owner = meta['ownerUpn'].strip().lower()
    sm = cfg['signals'].get('meta') or {}
    dm = disc.get('meta') or {}
    # the owner is the FIRST address given to --self (the UPN); a later address may only be the person's own mail address
    s_self, d_self = W.addresses(sm.get('self', [])), W.addresses(dm.get('self', []))
    if not s_self or s_self[0] != owner:
        fail('the numbers in "signals" were counted for %s, not for the config owner %s. Run count_signals.py on your own '
             'data with --self %s and paste its output into the config.' % (', '.join(s_self) or 'nobody', owner, owner))
    if not d_self or d_self[0] != owner:
        fail('discovery.json was made for %s, not for %s. Run discover.py on your own data.' % (', '.join(d_self) or 'nobody', owner))
    if s_self != d_self:
        fail('discovery.json and the signals were made with different --self addresses (%s and %s).' % (', '.join(d_self), ', '.join(s_self)))
    s_fps, s_owner = W.sample_fingerprints(W.window_from_meta(dm)), W.sample_identity()[1]
    if s_fps and dm.get('fingerprint') in s_fps and owner != s_owner:
        fail('discovery.json was made from the bundled fictional sample, not from your own mailbox. '
             'Run the ExecuteSql queries for the signed-in user and start again from discover.py.')
    if s_owner and owner == s_owner and dm.get('fingerprint') not in s_fps:
        fail('meta.ownerUpn is the fictional sample person. Stamp the config with your own UPN.')
    if not dm.get('fingerprint') or dm.get('fingerprint') != sm.get('fingerprint'):
        fail('discovery.json and the signals come from different data (fingerprints %s and %s). Run discover.py and '
             'count_signals.py on the same result files and window.' % (dm.get('fingerprint'), sm.get('fingerprint')))
    sw, dw = W.meta_window(sm), W.meta_window(dm)
    if sw != dw:
        fail('discovery.json and the signals cover different windows (%s and %s). Run discover.py and count_signals.py '
             'with exactly the same window flags.' % (describe_window(dw), describe_window(sw)))
    if sw[2] != len(cfg['weeks']) or sm.get('start') != dm.get('start'):
        fail('the config has %d columns in "weeks" but your data was counted %s. Copy "weeks" and "signals" from the '
             'same signals.json.' % (len(cfg['weeks']), describe_window(sw)))
    if W.window_from_meta(dm) is None:
        fail('discovery.json does not record a window this version can read (%s); run discover.py again.' % describe_window(dw))
    return owner, dm

def describe_window(mw):
    """Plain words for a (unit, start, columns) window: "day by day for 7 days from 2026-10-15"."""
    unit, start, cols = mw
    one, many = W.unit_words(unit)
    return '%s for %s %s from %s' % ('day by day' if unit == 'day' else 'week by week', cols, one if cols == 1 else many, start)

FOCUS_TYPES = ('customer', 'programme', 'theme')
FOCUS_CLASS = {'customer': 'customer', 'programme': 'programme', 'theme': 'theme'}
FOCUS_ITEM_KINDS = {'customer': ('org',), 'programme': ('meeting', 'thread', 'chat', 'sent', 'file', 'site', 'term', 'upcoming'),
                    'theme': ('term', 'thread', 'meeting', 'chat', 'sent', 'file', 'site')}

def _seq_ok(v, n):
    return isinstance(v, list) and len(v) == n and all(_whole(x) for x in v)

def check_focus(cfg, disc):
    """A focused sphere (meta.choices.focus) shows one customer, or one programme or topic, and what connects to it, all
    from the person's own data. Returns the focus as {"type", "id", "rx", "domains"}, or None for all my work."""
    _, focus = read_choices(cfg)
    sig = cfg['signals']; sm = sig.get('meta') or {}
    sf, mf = sig.get('focus'), sm.get('focus')
    if focus is None:
        if sf is not None or mf is not None:
            fail('your numbers are for one focus (%s), but the config does not choose one. Set meta.choices.focus, or '
                 'run count_signals.py without the focus flags for all your work.' % ((mf or {}).get('type') or 'unknown'))
        return None
    items = disc.get('items', {})
    ents = {e['id']: e for e in cfg['entities']}
    fid, ftype = focus['id'], focus['type']
    fe = ents.get(fid)
    if fe is None:
        fail('meta.choices.focus names "%s", which is not an entity on your sphere. Make the %s you chose an entity with that id '
             '(from your own discovery, step 7), or choose it again.' % (fid, 'customer' if ftype == 'customer' else 'programme or topic'))
    if fe['cls'] != FOCUS_CLASS[ftype]:
        fail('the focus "%s" is a %s on your sphere, but you chose a %s focus. Use the entity for the %s you chose.'
             % (fe.get('real'), fe['cls'], ftype, ftype))
    own = [f for f in fe.get('from') or [] if isinstance(f, str) and f in items and items[f].get('kind') in FOCUS_ITEM_KINDS[ftype]]
    if not own:
        fail('the focus "%s" is not in your own discovery: a focus %s must cite %s from discovery.json. Choose one that your own data '
             'shows (scripts/focus.py lists them).' % (fe.get('real'), ftype, ' or '.join('"%s:" items' % k for k in FOCUS_ITEM_KINDS[ftype][:3])))
    if not isinstance(sf, dict) or not isinstance(mf, dict):
        fail('your numbers cover all your work, not the focus "%s". Run count_signals.py again with the focus flags '
             'scripts/focus.py printed, and paste the whole signals.json.' % fe.get('real'))
    if mf.get('type') != ftype:
        fail('your numbers are for a %s focus, but you chose a %s focus. Run count_signals.py again with the focus flags for '
             'your choice.' % (mf.get('type'), ftype))
    try:
        rx = re.compile(mf.get('regex') or '', re.I)
    except re.error:
        fail('signals.meta.focus has no valid focus pattern; run count_signals.py again with the focus flags scripts/focus.py printed.')
    names = [fe.get('real') or ''] + [a for a in (fe.get('aka') or []) if isinstance(a, str)]
    doms = sorted(set(mf.get('domains') or []))
    want = sorted({items[f]['label'] for f in own if items[f].get('kind') == 'org'})
    if not mf.get('regex') or rx.search('') or not any(rx.search(n) for n in names) or (ftype == 'customer' and doms != want) \
            or (ftype != 'customer' and doms):
        fail('your numbers are for another focus (pattern "%s"%s), not for "%s". Run count_signals.py again with the focus '
             'flags scripts/focus.py printed for it.' % (mf.get('regex'), (', domains ' + ', '.join(doms)) if doms else '', fe.get('real')))
    n, vol, grid = len(cfg['weeks']), sig['vol'], sig['grid']
    fv, fg = sf.get('vol'), sf.get('grid')
    keys = ('mail_in', 'mail_out', 'meet', 'chats') + (('files',) if 'files' in vol else ())
    if not isinstance(fv, dict) or not isinstance(fg, dict) or set(fv) != set(keys) or set(fg) != set(grid) \
            or not all(_seq_ok(fv[k], n) for k in keys) or not all(_seq_ok(fg[k], n) for k in fg):
        fail('signals.focus is not what count_signals.py wrote; paste the whole signals.json unchanged.')
    over = [k for k in ('mail_in', 'mail_out', 'meet') + (('files',) if 'files' in vol else ()) if any(a > b for a, b in zip(fv[k], vol[k]))]
    over += [k for k in fg if any(a > b for a, b in zip(fg[k], grid[k]))]
    if sum(fv['chats']) > (sig.get('chats') or 0):
        over.append('chats')
    if over:
        fail('signals.focus counts more than all your work (%s), so it is not what count_signals.py wrote; paste the whole signals.json '
             'unchanged.' % ', '.join(over[:6]))
    # what the person's own discovery already shows about the focus is a floor for its counts
    if ftype == 'customer':
        orgs_f = [items[f] for f in own if items[f].get('kind') == 'org']
        floor_mail, floor_meet = sum(o.get('mails', 0) for o in orgs_f), sum(o.get('meetings', 0) for o in orgs_f)
    else:
        named = [it for it in items.values() if rx.search(it.get('label') or '')]
        floor_mail = sum(it.get('count', 0) for it in named if it.get('kind') == 'thread')
        floor_meet = sum(it.get('count', 0) for it in named if it.get('kind') == 'meeting')
    have_mail = sum(fv['mail_in']) + (0 if ftype == 'customer' else sum(fv['mail_out']))   # an organisation's mails are what it sent me
    have_meet = sum(fv['meet'])
    if have_mail < floor_mail or have_meet < floor_meet:
        fail('signals.focus counts fewer emails or calendar events about "%s" (%d and %d) than your own discovery shows for it (%d and %d), '
             'so it was not counted for this focus. Run count_signals.py again with the focus flags scripts/focus.py printed, and paste the '
             'whole signals.json unchanged.' % (fe.get('real'), have_mail, have_meet, floor_mail, floor_meet))
    hubs = {e['id'] for e in cfg['entities'] if e['cls'] == 'hub'}
    others = [e['id'] for e in cfg['entities'] if e['cls'] == 'customer' and e['id'] != fid]
    if ftype == 'customer' and others:
        fail('a sphere focused on one customer shows no other customer: remove %s (or choose All my work).' % ', '.join(others[:8]))
    if ftype == 'customer':
        fo = {f for f in own if items[f].get('kind') == 'org'}
        orgs = {k: W.org_display_name(it, items) for k, it in items.items() if it.get('kind') == 'org' and k not in fo and not it.get('automated')}
        onames = {k: v for k, v in orgs.items() if v and len(W.words(v)) and not set(W.words(v)) <= W.GENERIC_WORDS}
        about = []
        for e in cfg['entities']:
            if e['cls'] == 'hub' or e['id'] == fid:
                continue
            cites = [f for f in e.get('from') or [] if isinstance(f, str) and f in orgs]
            nm = ' %s ' % ' '.join(W.words(' '.join([e.get('real') or ''] + [x for x in e.get('aka') or [] if isinstance(x, str)])))
            named = [v for v in onames.values() if ' %s ' % ' '.join(W.words(v)) in nm] if e['cls'] != 'product' else []
            if cites or named:
                about.append('%s "%s" (%s)' % (e['cls'], e.get('real'), 'cites ' + cites[0] if cites else 'named after ' + named[0]))
        if about:
            fail('a sphere focused on one customer leaves other organisations off, but these are about another one: %s. Remove them '
                 '(or choose All my work).' % '; '.join(about[:8]))
    adj = {}
    for r in cfg['relations']:
        a, b = r[0], r[1]
        if a in hubs or b in hubs:
            continue
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    dist, frontier = {fid: 0}, [fid]
    for d in (1, 2):
        nxt = []
        for x in frontier:
            for y in adj.get(x, ()):
                if y not in dist:
                    dist[y] = d; nxt.append(y)
        frontier = nxt
    far = ['%s "%s"' % (e['id'], e.get('real')) for e in cfg['entities'] if e['cls'] not in ('hub',) and e['id'] not in dist]
    if far:
        fail('these items do not connect to the focus "%s" within two relationships (links through you do not count): %s. Link each to '
             'it, or to something linked to it, with a relationship your data supports, or leave it out.' % (fe.get('real'), '; '.join(far[:10])))
    co = focus_cooccurrence(items, rx, set(doms), sf)
    stray = []
    for e in cfg['entities']:
        if e['cls'] == 'hub' or e['id'] == fid:
            continue
        refs = [f for f in e.get('from') or [] if isinstance(f, str)] + (['signal:' + e['signal']] if e.get('signal') else [])
        if not any(co(f) for f in refs):
            stray.append('%s "%s"' % (e['cls'], e.get('real')))
    for i, o in enumerate(cfg.get('outputs') or []):
        refs = [f for f in o.get('from') or [] if isinstance(f, str)]
        if 'builtin:this-visual' not in refs and not any(co(f) for f in refs):
            stray.append('output %d "%s"' % (i + 1, o.get('title', '')))
    if stray:
        fail('nothing in your own data connects these to the focus "%s": %s. In a focused sphere each item must cite evidence about '
             'the focus (a meeting, thread, chat, file or site that names it or comes from its domains, a person at its meetings, or '
             'a keyword series with hits about it); cite such evidence or leave the item out.' % (fe.get('real'), '; '.join(stray[:10])))
    tok = '{%s}' % fid
    miss = [str(i + 1) for i, q in enumerate(cfg['questions']) if tok not in (q.get('q') or '') and fid not in (q.get('highlight') or [])]
    if miss:
        fail('Skills question%s %s do%s not name or highlight the focus "%s": every question in a focused sphere is about it (put %s '
             'in the question or its id in "highlight").' % ('s' if len(miss) > 1 else '', ', '.join(miss), '' if len(miss) > 1 else 'es',
                                                              fe.get('real'), tok))
    t = cfg.get('text') or {}
    if tok not in (t.get('headline') or '') or (t.get('slideTitle') and tok not in t['slideTitle']):
        fail('the headline%s must name the focus with its token %s, so the title names it (customer-safe files then show its alias).'
             % (' and text.slideTitle' if t.get('slideTitle') else '', tok))
    return {'type': ftype, 'id': fid, 'rx': rx, 'domains': set(doms)}

def focus_cooccurrence(items, rx, doms, sf):
    """f(ref) -> True when a piece of evidence co-occurs with the focus in the person's own discovery: an item whose label,
    subjects or (for a file) site names the focus; for a customer focus an item of its domains (its organisation, a meeting
    or thread with its people, a person who works there); a person listed at a meeting or upcoming meeting that co-occurs;
    a keyword series with hits inside the focus subset (signals.focus.grid); words the person said that name it."""
    def direct(it):
        texts = [it.get('label') or ''] + [x for x in (it.get('topSubjects') or []) + (it.get('subjects') or []) if isinstance(x, str)]
        if it.get('kind') == 'file' and it.get('containerType') != 'OneDrive':
            texts.append(it.get('container') or '')
        if any(rx.search(t) for t in texts):
            return True
        if doms and ((it.get('kind') == 'org' and it.get('label') in doms) or any(o in doms for o in it.get('orgs') or [])
                     or (it.get('kind') == 'person' and it.get('org') in doms)):
            return True
        if doms and it.get('kind') == 'upcoming':
            for a in it.get('attendees') or []:
                p = items.get(a) if isinstance(a, str) else None
                if (p and p.get('org') in doms) or (isinstance(a, str) and '@' in a and W.org_root(a.rsplit('@', 1)[1]) in doms):
                    return True
        return False
    met = set()
    for it in items.values():
        if it.get('kind') in ('meeting', 'upcoming') and direct(it):
            met.update(x for x in (it.get('people') or []) + (it.get('attendees') or []) if isinstance(x, str))
    fg = (sf or {}).get('grid') or {}
    def co(f):
        if f.startswith('signal:'):
            return sum(fg.get(f[7:]) or [0]) > 0
        if f.startswith(('stated:', 'source:')):
            return bool(rx.search(f.split(':', 1)[1]))
        it = items.get(f)
        return bool(it) and (direct(it) or (it.get('kind') == 'person' and f in met))
    return co

def read_choices(cfg):
    """meta.choices as (window value or None, focus {"type", "id"} or None). A config without choices (made by 1.6) means
    the last quarter, or the weekly window its signals were counted for, and all my work."""
    ch = (cfg.get('meta') or {}).get('choices')
    if ch is None:
        return None, None
    if not isinstance(ch, dict):
        fail('meta.choices must be an object like {"window": "month", "focus": {"type": "all"}}.')
    win = ch.get('window')
    if win is not None and not isinstance(win, str):
        fail('meta.choices.window must be "week", "month", "quarter", "last-<N>-weeks" or "since-<YYYY-MM-DD>".')
    focus = ch.get('focus')
    if focus is None or (isinstance(focus, dict) and focus.get('type') in (None, 'all')):
        return win, None
    if not isinstance(focus, dict) or focus.get('type') not in FOCUS_TYPES or not isinstance(focus.get('id'), str) or not focus['id']:
        fail('meta.choices.focus must be {"type": "all"} or {"type": "customer", "programme" or "theme", "id": "<entity id>"}.')
    return win, {'type': focus['type'], 'id': focus['id']}

def check_memory(cfg, dm):
    """Every memory callout points at a lane and a column (a day for the week, else a week) that exist."""
    nweeks, lanes = len(cfg['weeks']), cfg.get('lanes') or []
    one, many = W.unit_words(W.meta_window(dm)[0])
    for i, m in enumerate(cfg.get('memory') or []):
        ln, wk = (m.get('lane'), m.get('week')) if isinstance(m, dict) else (None, None)
        if not isinstance(ln, int) or not isinstance(wk, int) or isinstance(ln, bool) or isinstance(wk, bool) \
                or not (0 <= ln < len(lanes)) or not (0 <= wk < nweeks):
            fail('memory callout %d ("%s") points at lane %s and %s %s, but the sphere has %d lanes (0 to %d) and %d %s (0 to %d, '
                 'counting from 0, so the last %s is %d). Set "lane" and "week" to positions in "lanes" and "weeks".'
                 % (i + 1, str((m or {}).get('text', ''))[:60], ln, one, wk, len(lanes), len(lanes) - 1, nweeks, many, nweeks - 1, one, nweeks - 1))

def check_choices(cfg, dm):
    """The window the person chose (meta.choices.window) is the window discovery.json and the signals were counted for."""
    win, _ = read_choices(cfg)
    actual = W.meta_window(dm)
    if win is None:
        if actual[0] != 'week':
            fail('your data was counted %s, but the config does not say which window you chose. Save it as '
                 'meta.choices.window ("week" for the last 7 days).' % describe_window(actual))
        return
    try:
        today = dt.date.fromisoformat(dm.get('today') or '')
    except ValueError:
        fail('discovery.json has no "today", so the chosen window cannot be checked; run discover.py with --today.')
    want = W.choice_window(win, today)
    if want is None:
        fail('meta.choices.window is "%s", which is not a window this skill knows: use "week", "month", "quarter", '
             '"last-<N>-weeks" or "since-<YYYY-MM-DD>".' % win)
    exp = (want['unit'], want['start'].isoformat(), want['columns'])
    if exp != actual:
        fail('you chose the window "%s" (%s), but your data was counted %s. Run discover.py and count_signals.py with '
             'the flags scripts/window.py prints for that choice.' % (win, describe_window(exp), describe_window(actual)))

def check_signals(cfg, dm):
    """The numbers are exactly the ones count_signals.py counted from the same files discover.py read."""
    sig = cfg['signals']; sm = sig.get('meta') or {}
    if not sm.get('digest') or sm['digest'] != W.signals_digest(sig):
        fail('the "signals" block is not exactly what count_signals.py wrote (a number, series, label or count was edited, '
             'added or pasted from elsewhere). Paste the whole signals.json from your own run, unchanged.')
    vol = sig['vol']
    emails, events = sum(vol['mail_in']) + sum(vol['mail_out']), sum(vol['meet'])
    if (emails, events) != (dm.get('emails'), dm.get('calendarEvents')):
        fail('signals count %d emails and %d calendar events, but discover.py found %s and %s in the same window. '
             'Run both scripts on the same result files.' % (emails, events, dm.get('emails'), dm.get('calendarEvents')))
    ch = dm.get('chats') or {}
    expect = ch.get('group', 0) + ch.get('oneOnOne', 0) if ch.get('listed') else 0
    if sig.get('chats', 0) != expect:
        fail('signals.chats is %s, but your chats file has %d group and 1:1 chats active in the window. Run count_signals.py '
             'with --chats-file working/chats.json (the same file discover.py read), or 0 when chats were not listed.' % (sig.get('chats'), expect))
    if list(cfg['weeks']) != list(sig.get('weeks') or []):
        fail('the config weeks (%s ...) are not the weeks your data was counted for (%s ...). Copy "weeks" from signals.json.'
             % (', '.join(cfg['weeks'][:2]), ', '.join((sig.get('weeks') or [])[:2])))
    check_files(sig, dm, len(cfg['weeks']))

def _whole(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0

def check_files(sig, dm, nweeks):
    """Files (discover.py and count_signals.py --files): both or neither, counts that add up, and the same counts
    discover.py found in the same files.json, so a files number typed into the config is refused."""
    fs, vf, dfs = sig.get('files'), (sig.get('vol') or {}).get('files'), dm.get('files')
    if fs is None and vf is None and dfs is None:
        return
    if fs is None or vf is None or dfs is None:
        fail('discovery.json %s files and the signals %s; run discover.py and count_signals.py with the same --files '
             'working/files.json (or both without it) and paste the whole signals.json'
             % ('has' if dfs is not None else 'has no', 'have them' if fs is not None or vf is not None else 'have none'))
    if not isinstance(fs, dict) or not isinstance(vf, list) or len(vf) != nweeks or not all(_whole(x) for x in vf):
        fail('signals.vol.files must have one whole number per %s, and signals.files must be the counts count_signals.py wrote'
             % W.unit_words(W.meta_window(dm)[0])[0])
    for k in ('worked_on', 'edited', 'created', 'opened', 'sites'):
        if not _whole(fs.get(k)):
            fail('signals.files.%s must be a count from count_signals.py' % k)
    if sum(vf) != fs['worked_on'] or fs['edited'] + fs['opened'] != fs['worked_on'] or fs['created'] > fs['edited']:
        fail('signals.files does not add up (worked on %s, edited %s, opened %s, weekly total %s); paste count_signals.py output unchanged'
             % (fs['worked_on'], fs['edited'], fs['opened'], sum(vf)))
    diff = [k for k in ('worked_on', 'edited', 'created', 'opened', 'sites', 'byContainer') if fs.get(k) != dfs.get(k)]
    if diff:
        fail('signals.files (%s) is not what discover.py found in the same files (%s); run both scripts on the same files.json'
             % (', '.join('%s %s' % (k, fs.get(k)) for k in diff), ', '.join('%s %s' % (k, dfs.get(k)) for k in diff)))

def _sig_words(name, cls):
    gen = set() if cls == 'product' else W.GENERIC_WORDS
    raw = re.findall(r'[A-Za-z0-9]+', name or '')
    out = []
    for t in raw:
        w = W.fold(t)
        if w in gen:
            continue
        if len(w) >= 3 or (len(w) == 2 and t.isupper()):
            out.append(w)
    return out

def _stem_hit(w, lw):
    return w in lw or (len(w) >= 5 and any(len(x) >= 5 and x[:5] == w[:5] for x in lw))

def name_agrees(e, refs, items, kw, strict=False):
    """True when the entity's name (or an aka that itself appears in the evidence) matches what it cites: the person's
    name, the escalation number, the customer's domain or subjects, or a significant word of the programme, theme,
    asset or product. A name that resembles the bundled example's needs most of its words in the evidence (strict)."""
    cls, real = e['cls'], e.get('real') or ''
    data = [items[f] for f in refs if f in items]
    labels = [l for it in data for l in W.item_labels(it)]
    lw = set(w for l in labels for w in W.words(l))
    compacts = [''.join(W.words(l)) for l in labels]
    names = [real] + [a for a in (e.get('aka') or []) if isinstance(a, str) and a.strip()
                      and any(''.join(W.words(a)) in c for c in compacts)]
    rxs = [kw[f[7:]] for f in refs if f.startswith('signal:') and f[7:] in kw and (cls == 'product' or not f[7:].startswith('p_'))]
    def rx_ok():
        for r in rxs:
            try:
                if any(re.search(r, n, re.I) for n in names):
                    return True
            except re.error:
                pass
        return False
    if cls == 'uat':
        nums = set(re.findall(r'\d{6}', real))
        return bool(nums) and (any(f[4:] in nums for f in refs if f.startswith('esc:') and f in items) or any(n in r for r in rxs for n in nums))
    if cls == 'person':
        nw = [w for w in W.words(real) if len(w) >= 2]
        hits = [w for w in nw if w in lw]
        return bool(nw) and (len(hits) >= min(2, len(nw)) or (len(nw[-1]) >= 3 and nw[-1] in lw))
    if rx_ok():
        return True
    if cls == 'customer':
        org_words = {w for it in data if it.get('kind') == 'org' for w in W.words(it.get('label')) if w not in W.DOMAIN_WORDS and len(w) >= 2}
        for n in names:
            core = [w for w in W.words(n) if w not in W.ORG_STOP]
            if not core:
                continue
            whole = ''.join(core)
            if len(whole) >= 3 and any(whole in c for c in compacts):
                return True
            if len(core[0]) >= 4 and any(c.startswith(core[0]) for c in compacts):
                return True
            if any(i in org_words for i in W.initials(n) if len(i) >= 2):
                return True
            if any(len(o) >= 3 and any(w.startswith(o) for w in core) for o in org_words):
                return True
        return False
    for n in names:
        sw = _sig_words(n, cls)
        if not sw:
            continue
        hits = sum(1 for w in sw if _stem_hit(w, lw))
        if hits >= ((len(sw) // 2 + 1) if strict else 1):
            return True
    return False

def _resembles(name, others):
    a = {w[:5] for w in _sig_words(name, 'programme')}
    return bool(a) and any(len(a & b) / len(a | b) >= 0.5 for b in others if b)

def check_evidence(cfg, disc, building_example=False):
    items = disc.get('items', {}); grid = cfg['signals']['grid']
    kw = (cfg['signals'].get('meta') or {}).get('keywords') or {}
    ex = json.load(open(EXAMPLE, encoding='utf-8')) if os.path.exists(EXAMPLE) and not building_example else None
    ex_sets = [{w[:5] for w in _sig_words(x['real'], 'programme')} for x in (ex or {}).get('entities', [])
               if x['cls'] in ('programme', 'theme', 'asset', 'customer')]
    unknown, missing, wrong_kind, stated, disagree = [], [], [], [], []
    file_kind, opened_only, thin_site = [], [], []
    def has_hits(k):
        return k in grid and sum(grid[k]) > 0
    def ok(refs, allow_stated, allow_builtin=False, kinds=None, cls=None):
        good = False
        for f in refs:
            if not isinstance(f, str) or not f:
                continue
            if kinds and not f.startswith(kinds) and not (f.startswith(('stated:', 'source:')) and allow_stated):
                wrong_kind.append(f); continue
            if f.startswith(tuple(FILE_KIND_OK)) and f in items:
                fk = f.split(':', 1)[0] + ':'
                if cls not in FILE_KIND_OK[fk]:
                    file_kind.append('%s cited by a %s' % (f, cls)); continue
                if fk == 'file:' and not items[f].get('edited'):
                    opened_only.append(f); continue
                if fk == 'site:' and (items[f].get('edited') or 0) < SITE_MIN_EDITED:
                    thin_site.append(f); continue
            if f.startswith('signal:'):
                if has_hits(f[7:]): good = True
                else: unknown.append(f)
            elif f.startswith(('stated:', 'source:')):
                if allow_stated and len(f) > 9: good = True; stated.append(f.split(':', 1)[1])
                else: unknown.append(f)
            elif f == 'builtin:this-visual':
                if allow_builtin: good = True
                else: unknown.append(f)
            elif f in items:
                good = True
            else:
                unknown.append(f)
        return good
    said_bad = []
    def said_ok(refs, x, cls):
        """stated: is what the person told you about THIS item, in their words; source: is a document behind an internal item."""
        name = x.get('real') or x.get('title') or ''
        keep = []
        for f in refs:
            if not f.startswith(('stated:', 'source:')):
                keep.append(f); continue
            kind, said = f.split(':', 1)
            why = None
            if kind == 'source' and not x.get('internal'):
                why = 'source: is only for internal items from a document the person named'
            elif kind == 'stated' and cls in ('customer', 'person', 'uat'):
                why = 'customers, people and escalations must come from the person\'s own mail, calendar or chats'
            elif len(said.split()) < 3 or len(said.strip()) < 12:
                why = 'write what the person said, in their words'
            elif kind == 'stated' and not any(_stem_hit(w, set(W.words(said))) for w in (_sig_words(name, 'product') or W.words(name))):
                why = 'what the person said does not name it'
            elif _resembles(name, ex_sets):
                why = 'it looks like the bundled example\'s %s' % cls
            if why:
                said_bad.append('"%s" (%s)' % (name[:50], why))
            else:
                keep.append(f)
        return keep
    data_ev = {}
    n_said_only, n_said_outputs = 0, 0
    for e in cfg['entities']:
        if e['cls'] not in EVIDENCE_CLASSES:
            continue
        refs = said_ok([f for f in (e.get('from') or []) if isinstance(f, str)], e, e['cls'])
        if e.get('signal'):
            refs.append('signal:' + e['signal'])
        if refs and all(f.startswith(('stated:', 'source:')) for f in refs):
            n_said_only += 1
        if not ok(refs, e['cls'] in STATED_OK or bool(e.get('internal')), kinds=KIND_RULE.get(e['cls']), cls=e['cls']):
            missing.append('%s (%s "%s")' % (e['id'], e['cls'], e.get('real', '')))
        has_data = any(f in items or (f.startswith('signal:') and has_hits(f[7:])) for f in refs)
        strict = _resembles(e.get('real', ''), ex_sets)
        agrees = has_data and name_agrees(e, [f for f in refs if f in items or (f.startswith('signal:') and has_hits(f[7:]))], items, kw, strict)
        only_said = all(f.startswith(('stated:', 'source:')) for f in refs if f not in items and not f.startswith('signal:')) and \
            any(f.startswith(('stated:', 'source:')) for f in refs)
        if has_data and not agrees and not only_said:
            cited = [f for f in refs if f in items or f.startswith('signal:')][:2]
            disagree.append('%s "%s" (cites %s)' % (e['cls'], e.get('real', ''), ', '.join(cited)))
        data_ev[e['id']] = agrees
    ex_sets_out = ex_sets + [{w[:5] for w in _sig_words(x.get('title', ''), 'programme')} for x in (ex or {}).get('outputs', [])]
    for i, o in enumerate(cfg['outputs']):
        refs = [f for f in (o.get('from') or []) if isinstance(f, str)]
        if any(f.startswith(('stated:', 'source:')) for f in refs):
            if _resembles(o.get('title', ''), ex_sets_out):
                said_bad.append('"%s" (it looks like the bundled example\'s output)' % o.get('title', '')[:50]); refs = []
            else:
                refs = said_ok(refs, o, 'output')
            if refs and all(f.startswith(('stated:', 'source:')) for f in refs):
                n_said_outputs += 1
        if not ok(refs, True, allow_builtin=True, cls='output'):
            missing.append('output %d "%s"' % (i + 1, o.get('title', '')))
    n_ev = sum(1 for e in cfg['entities'] if e['cls'] in EVIDENCE_CLASSES)
    if n_said_only > max(3, n_ev // 10) or n_said_outputs > 2:
        said_bad.append('%d nodes and %d outputs rest only on what was said; most of the sphere must come from the person\'s own data '
                        '(at most %d nodes and 2 outputs)' % (n_said_only, n_said_outputs, max(3, n_ev // 10)))
    msgs = []
    if unknown: msgs.append('these evidence references are not in your discovery.json or have no hits in your signals: %s' % ', '.join(sorted(set(unknown))[:15]))
    if wrong_kind: msgs.append('people need "person:" evidence and escalations need "esc:" evidence: %s' % ', '.join(sorted(set(wrong_kind))[:10]))
    if file_kind: msgs.append('"site:" items are evidence only for customers and programmes, and "file:" items only for customers, '
                              'programmes, assets and outputs: %s' % ', '.join(sorted(set(file_kind))[:10]))
    if opened_only: msgs.append('only files you edited or created are evidence, never files you only opened: %s' % ', '.join(sorted(set(opened_only))[:10]))
    if thin_site: msgs.append('a site is evidence only when you edited at least %d files there: %s' % (SITE_MIN_EDITED, ', '.join(sorted(set(thin_site))[:10])))
    if missing: msgs.append('no evidence from your own data for: %s' % ', '.join(missing[:20]))
    if said_bad: msgs.append('these "stated:" or "source:" items cannot be used: %s' % '; '.join(said_bad[:8]))
    if disagree: msgs.append('these names do not match the evidence they cite (a person must be that person, an escalation '
                             'that number, a customer that organisation, and a programme, theme or asset must share a real word '
                             'with its meetings or threads; put the subject word in "aka" when you translate it): %s' % '; '.join(disagree[:10]))
    if msgs:
        fail('. '.join(msgs) + '. Every node and output must cite item ids exactly as discover.py printed them (or "signal:<key>" '
             'with hits); remove anything your own data does not show.')
    return data_ev, stated

# Each Skills question is a different kind, backed by the discovery items that kind needs (SKILL.md step 6).
QUESTION_KINDS = {'prep': ('upcoming:',), 'latest': ('meeting:', 'thread:', 'signal:'), 'cares': ('org:', 'thread:', 'meeting:', 'signal:'),
                  'change': ('signal:',), 'escalations': ('esc:',), 'draft': ('sent:',), 'involve': ('meeting:',), 'promised': ('sent:', 'thread:'),
                  'document': ('file:',)}
Q_STOP = set('''a an the is are was what whats what's which who whom why how me my i for on in of with to this that these those
please latest new now right today week it its about any do does did should can could would will be been get give tell'''.split())

def check_question_kinds(cfg, disc):
    items = disc.get('items', {}); grid = cfg['signals']['grid']
    qs = [q for q in cfg['questions'] if not q.get('internal')]
    kinds, bad = [], []
    for i, q in enumerate(qs):
        k = q.get('kind')
        if k not in QUESTION_KINDS:
            bad.append('question %d has no "kind" (one of %s)' % (i + 1, ', '.join(QUESTION_KINDS))); continue
        kinds.append(k)
        refs = [f for f in (q.get('from') or []) if isinstance(f, str)]
        real = [f for f in refs if f in items or (f.startswith('signal:') and sum(grid.get(f[7:], [0])) > 0)]
        if not any(f.startswith(QUESTION_KINDS[k]) for f in real):
            bad.append('question %d (%s) needs "from" with a %s item from your discovery' % (i + 1, k, ' or '.join(QUESTION_KINDS[k])))
    if len(set(kinds)) != len(kinds):
        bad.append('two questions are the same kind (%s)' % ', '.join(sorted(k for k in set(kinds) if kinds.count(k) > 1)))
    sets = [{w for w in W.words(re.sub(r'\{\w+\}', ' ', neutral(q.get('q', '')))) if len(w) >= 3} - Q_STOP for q in qs]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a, b = sets[i], sets[j]
            if (not a and not b) or (a and b and (a <= b or b <= a or len(a & b) / len(a | b) >= 0.6)):
                bad.append('questions %d and %d ask the same thing in different words' % (i + 1, j + 1))
    if bad:
        fail('Skills questions: %s. Ask 4 DIFFERENT kinds of question your own data supports (SKILL.md step 6), each citing its '
             'discovery items.' % '; '.join(bad[:6]))

def check_questions(cfg):
    seen = set()
    for i, q in enumerate(cfg['questions']):
        toks = [t for t in re.findall(r'\{(\w+)\}', q.get('q', '')) if t != 'me']
        if not toks:
            fail('Skills question %d ("%s") must name one of your own customers, programmes, themes or people with an '
                 '{entity_id} token, so the question is about your work.' % (i + 1, q.get('q', '')[:60]))
        if not [h for h in q.get('highlight', []) if h != 'me']:
            fail('Skills question %d needs highlight ids of your own entities' % (i + 1))
        key = W.norm_text(q['q'])
        if key in seen:
            fail('two Skills questions are the same question with different names ("%s"). Use different kinds of question '
                 'drawn from your own data (see SKILL.md, step 5).' % q['q'][:60])
        seen.add(key)
        if not re.search(r'\d', neutral(q.get('grounding', ''))) and not has_count_ph(q.get('grounding', '')):
            fail('Skills question %d needs a grounding line with counts from your own data' % (i + 1))

def check_copies(cfg, owner, data_ev, fp=None, win=None):
    ex = json.load(open(EXAMPLE, encoding='utf-8')) if os.path.exists(EXAMPLE) else None
    gd = json.load(open(GUARD, encoding='utf-8')) if os.path.exists(GUARD) else {}
    # the example may repeat itself only when it is rebuilt from the shipped sample data (same fingerprint), never
    # because a config or a --self list names the sample person
    s_owner = W.sample_identity()[1]
    building_example = bool(ex) and owner == s_owner and bool(fp) and fp in W.sample_fingerprints(win)
    legacy_exempt = False
    generic = set(gd.get('generic', ['this visual'])) | GENERIC_TEXT | {'built from the work above'}
    ex_names, ex_text, ex_sh = set(), set(), set()
    if ex and not building_example:
        ex_names = {W.norm_text(e['real']) for e in ex['entities'] if e['cls'] not in ('hub', 'product')}
        for _, s in free_texts(ex):
            n = W.norm_text(s)
            if len(n) >= 12: ex_text.add(n)
            ex_sh |= W.shingles(s)
    l_names = set() if legacy_exempt else set(gd.get('legacyNames', []))
    l_text = set() if legacy_exempt else set(gd.get('legacyText', []))
    l_sh = set() if legacy_exempt else set(gd.get('legacyShingles', []))
    hits = []
    for e in cfg['entities']:
        if e['cls'] in ('hub', 'product'):
            continue
        n = W.norm_text(e.get('real', ''))
        if not n or n in generic:
            continue
        if (n in ex_names or W.text_hash(e['real']) in l_names) and not data_ev.get(e['id']):
            hits.append('%s "%s"' % (e['cls'], e['real']))
    for where, s in free_texts(cfg):
        n = W.norm_text(s)
        # short, everyday question shapes ("Draft this week's {x}") are fine; long copied wording is not
        if len(n) < (30 if where.startswith('Skills question') else 12) or n in generic:
            continue
        if n in ex_text or W.text_hash(s) in l_text:
            hits.append('%s "%s"' % (where, re.sub(r'<[^>]+>', '', s)[:50])); continue
        sh = W.shingles(s)
        if len(sh) >= 6:
            if ex_sh and len(sh & ex_sh) / len(sh) >= 0.6:
                hits.append('%s "%s" (almost the same as the example)' % (where, re.sub(r'<[^>]+>', '', s)[:50]))
            elif l_sh and len(W.shingle_hashes(s) & l_sh) / len(sh) >= 0.6:
                hits.append('%s "%s" (almost the same as an earlier sample)' % (where, re.sub(r'<[^>]+>', '', s)[:50]))
    if hits:
        fail('these were copied from the bundled example or an earlier version\'s sample, not found in your own data: %s. '
             'Rewrite them from your own discovery.json and signals, or remove them.' % '; '.join(hits[:15]))

def refresh_changes(prev, cfg):
    """What changed since the saved config, for the refresh summary, plus the stated items to confirm again."""
    def ents(c):
        return {'%s "%s"' % (e.get('cls'), e.get('real')) for e in c.get('entities', []) if e.get('cls') != 'hub'}
    def totals(c):
        s_ = c.get('signals') or {}; v = s_.get('vol') or {}
        try:
            t = {'emails': sum(v['mail_in']) + sum(v['mail_out']), 'calendar_events': sum(v['meet']), 'chats': s_.get('chats', 0)}
        except (KeyError, TypeError):
            return {}
        if isinstance(s_.get('files'), dict):
            t['files_worked_on'] = s_['files'].get('worked_on', 0)
        t['total_signals'] = sum(x for x in t.values() if isinstance(x, int))
        return t
    said = [x.get('real') or x.get('title') for x in cfg.get('entities', []) + cfg.get('outputs', [])
            if any(isinstance(f, str) and f.startswith('stated:') for f in x.get('from') or [])]
    a, b = ents(prev), ents(cfg)
    return {'added': sorted(b - a)[:20], 'removed': sorted(a - b)[:20], 'before': totals(prev), 'now': totals(cfg),
            'stated_items_to_confirm_again': said}

def guard(cfg, disc):
    """The whole fresh-analysis guard, shared by build_workiq.py and fill_slide.py so the sphere and slide cannot drift."""
    for k in REQ:
        if k not in cfg: fail('config is missing "%s"' % k)
    owner, dmeta = check_owner(cfg, disc)
    check_signals(cfg, dmeta)
    s_owner = W.sample_identity()[1]
    building_example = owner == s_owner and dmeta.get('fingerprint') in W.sample_fingerprints(W.window_from_meta(dmeta))
    data_ev, stated = check_evidence(cfg, disc, building_example=building_example)
    check_questions(cfg)
    check_question_kinds(cfg, disc)
    check_copies(cfg, owner, data_ev, dmeta.get('fingerprint'), W.window_from_meta(dmeta))
    check_identity(cfg, disc, building_example)
    check_choices(cfg, dmeta)
    check_focus(cfg, disc)
    check_memory(cfg, dmeta)
    check_window(cfg, dmeta)
    check_names(cfg, disc)
    check_placeholders(cfg, disc)
    for w in check_numbers(cfg, disc)[:8]:
        print('WARNING: a number not found in your own counts (check it): %s' % w)
    return owner, dmeta, data_ev, stated

MONTHS = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}
DATE_RX = re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+(\d{4}))?\b'
                     r'|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s+(\d{4}))?', re.I)
KW_RX = re.compile(r'\b(?:kw|cw)\s*(\d{1,2})\b', re.I)
NUM_RX = re.compile(r'(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?![\w])')

def window_label(dm):
    return W.window_label(W.window_from_meta(dm), dt.date.fromisoformat(dm['today']))

def check_identity(cfg, disc, building_example):
    """The sphere is about the config owner: owner, hub, title and source may not name anybody else."""
    dm = disc.get('meta') or {}
    display = next((x for x in dm.get('self', []) if '@' not in x), '')
    others = {it.get('label') for it in disc.get('items', {}).values() if it.get('kind') == 'person'} - {None, ''}
    ex = json.load(open(EXAMPLE, encoding='utf-8')) if os.path.exists(EXAMPLE) and not building_example else None
    if ex and ex.get('owner'):
        others.add(ex['owner'])
    others = {o for o in others if W.fold(o) != W.fold(display) and len(o) >= 5 and ' ' in o.strip()}
    hub = next((e for e in cfg['entities'] if e['cls'] == 'hub'), {})
    bad = []
    for where, t in (('owner', cfg.get('owner', '')), ('title', cfg.get('title', '')), ('source', cfg.get('source', '')),
                     ('the hub (you)', hub.get('real', ''))):
        hit = next((o for o in others if re.search(r'(?<![a-z])' + re.escape(W.fold(o)) + r'(?![a-z])', W.fold(t))), None)
        if hit:
            bad.append('%s names %s' % (where, hit))
    if bad:
        fail('the sphere must be about you (%s): %s. Use your own display name, or a role such as "A Microsoft specialist".'
             % (display or 'the config owner', '; '.join(bad)))

def _date_ok(d, start, last):
    return start <= d <= last

def check_window(cfg, dm):
    """Every date the visual mentions falls in the person's own window, or just after it for upcoming meetings: the five
    weeks after a weekly window, and the rest of this week (the look-ahead discover.py lists) after the last 7 days."""
    win = W.window_from_meta(dm)
    start, end = win['start'], win['end']
    last = end + dt.timedelta(days=35)
    if win['unit'] == 'day':
        last = W.ahead_end(win, dt.date.fromisoformat(dm['today'])) - dt.timedelta(days=1)
    want = window_label(dm)
    t = cfg.get('text') or {}
    if t.get('windowLabel') and W.norm_text(t['windowLabel']) != W.norm_text(want):
        fail('text.windowLabel is "%s" but your data covers %s. Leave windowLabel out and the build writes it.' % (t['windowLabel'], want))
    kws = set()
    d = start
    while d < (last if win['unit'] == 'week' else last + dt.timedelta(days=1)):
        kws.add(d.isocalendar()[1]); d += dt.timedelta(days=7)
    if win['unit'] == 'day':
        kws.add(last.isocalendar()[1])
    bad = []
    for where, s in all_texts(cfg):
        plain = re.sub(r'<[^>]+>', ' ', neutral(s))
        for m in DATE_RX.finditer(plain):
            day, mon, yr = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(5), m.group(4), m.group(6))
            day, mon = int(day), MONTHS[mon[:3].lower()]
            years = [int(yr)] if yr else [start.year, end.year, end.year + 1]
            ok = False
            for y in years:
                try:
                    ok = ok or _date_ok(dt.date(y, mon, day), start, last)
                except ValueError:
                    pass
            if not ok:
                bad.append('%s mentions "%s"' % (where, m.group(0)))
        for m in KW_RX.finditer(plain):
            if int(m.group(1)) not in kws and not re.search(r'\d+\s*(?:weeks?)\b', plain[m.start():m.end() + 6], re.I):
                bad.append('%s mentions "%s"' % (where, m.group(0)))
    if bad:
        fail('these dates are outside your own window (%s): %s. Write them from your own signals and discovery.' % (want, '; '.join(bad[:8])))

def _lane_agrees(name, rx):
    try:
        if re.search(rx, name, re.I):
            return True
    except re.error:
        return False
    alt_words = set(re.findall(r'[a-z0-9]+', W.fold(re.sub(r'\\[a-z]', ' ', rx))))
    return any(_stem_hit(w, alt_words) for w in _sig_words(name, 'theme'))

def check_names(cfg, disc):
    """Lane names must describe their own keyword series, and portals must be Microsoft experiences or the person's own."""
    kw = (cfg['signals'].get('meta') or {}).get('keywords') or {}
    bad = [('lane "%s" (%s)' % (l.get('name'), l['key'])) for l in cfg['lanes'] if l['key'] in kw and not _lane_agrees(l.get('name', ''), kw[l['key']])]
    labels = set()
    for it in disc.get('items', {}).values():
        labels.update(W.words(it.get('label') or ''))
    own = {W.fold(e.get('real', '')) for e in cfg['entities'] if e['cls'] in ('product', 'asset', 'programme')}
    for p_ in cfg.get('portals') or []:
        n = p_.get('name', '') if isinstance(p_, dict) else str(p_)
        if W.fold(n) in {W.fold(x) for x in W.DEFAULT_PORTALS} or W.fold(n) in own:
            continue
        sw = _sig_words(n, 'programme')
        if not sw or not all(_stem_hit(w, labels) for w in sw):
            bad.append('portal "%s"' % n)
    if bad:
        fail('these names are not backed by your own data: %s. A lane is named after what its keyword finds; a portal is a '
             'Microsoft Copilot experience or one of your own products, programmes or agents.' % '; '.join(bad[:8]))

def _nums(s):
    return {float(x) for x in re.findall(r'\d+', s or '')}

def _series(v):
    try:
        return {float(x) for x in v} | {float(sum(v)), float(max(v)), float(min(v)), float(len(v))}
    except (TypeError, ValueError):
        return set()

def _item_nums(it):
    out = set()
    for k, v in it.items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            out.add(float(v))
        elif isinstance(v, str):
            out |= _nums(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str): out |= _nums(x)
    return out

def check_numbers(cfg, disc):
    """Every number of 100 or more in the text must come from the person's own counts (warn for 13 to 99)."""
    sig, items = cfg['signals'], disc.get('items', {})
    grid, vol, dm = sig['grid'], sig['vol'], disc.get('meta') or {}
    em, ev, ch = sum(vol['mail_in']) + sum(vol['mail_out']), sum(vol['meet']), sig.get('chats') or 0
    G = {float(x) for x in (em, ev, ch, em + ev + ch, sum(vol['mail_in']), sum(vol['mail_out']), sig.get('senders') or 0,
                            sig.get('orgs') or 0, sig.get('pub_orgs') or 0, len(cfg['weeks']), len(cfg['entities']) - 1,
                            len(cfg['relations']), dm.get('emails') or 0, dm.get('calendarEvents') or 0)}
    G |= {float(sum(1 for e in cfg['entities'] if e['cls'] == c)) for c in CLASSES}
    fsig = sig.get('files') if isinstance(sig.get('files'), dict) else None
    if fsig:                                     # files: their counts and the total that includes them
        G |= {float(v) for k, v in fsig.items() if k != 'byContainer' and _whole(v)}
        G |= {float(v) for v in (fsig.get('byContainer') or {}).values() if _whole(v)}
        G |= {float(em + ev + ch + (fsig.get('worked_on') or 0))} | _series(vol.get('files') or [])
    G |= {float(v) for v in (dm.get('chats') or {}).values() if isinstance(v, int)}
    fsg = sig.get('focus') if isinstance(sig.get('focus'), dict) else {}
    fgrid = fsg.get('grid') if isinstance(fsg.get('grid'), dict) else {}
    if fsg:                                      # a focus: its counts, their totals and its series (version 1.7)
        fv = fsg.get('vol') if isinstance(fsg.get('vol'), dict) else {}
        def tot(k):
            return sum(x for x in fv.get(k) or [] if _whole(x))
        fem, fev, fch, ffi = tot('mail_in') + tot('mail_out'), tot('meet'), tot('chats'), tot('files')
        G |= {float(x) for x in (fem, fev, fch, ffi, fem + fev, fem + fev + fch, fem + fev + fch + ffi, tot('mail_in'), tot('mail_out'))}
        for v in fv.values():
            G |= _series(v)
    for e in cfg['entities']:
        G |= _nums(e.get('real')) | set().union(*[_nums(a) for a in (e.get('aka') or []) if isinstance(a, str)] or [set()])
    for it in items.values():
        G |= _nums(it.get('label'))
    ents = {e['id']: e for e in cfg['entities']}
    def scope(ids, refs):
        A = set()
        for i in ids:
            e = ents.get(i)
            if not e: continue
            for f in e.get('from') or []:
                if f in items: A |= _item_nums(items[f])
            if e.get('signal') in grid: A |= _series(grid[e['signal']]) | _series(fgrid.get(e['signal']) or [])
        for f in refs:
            if f in items: A |= _item_nums(items[f])
            if isinstance(f, str) and f.startswith('signal:') and f[7:] in grid: A |= _series(grid[f[7:]]) | _series(fgrid.get(f[7:]) or [])
        return A
    lanes = cfg['lanes']
    texts = []
    for e in cfg['entities']:
        for k in ('detail', 'internalDetail'):
            if e.get(k): texts.append(('detail of %s' % e['id'], e[k], [e['id']], []))
    for i, q in enumerate(cfg['questions']):
        for t in [q.get('q', '')] + list(q.get('answer') or []) + [q.get('grounding', '')]:
            texts.append(('Skills question %d' % (i + 1), t, q.get('highlight', []), q.get('from') or []))
    for i, o in enumerate(cfg['outputs']):
        for k in ('title', 'text', 'internalText'):
            if o.get(k): texts.append(('output %d' % (i + 1), o[k], [], o.get('from') or []))
    for i, m in enumerate(cfg['memory']):
        lane = lanes[m['lane']]['key'] if 0 <= m.get('lane', -1) < len(lanes) else None
        texts.append(('memory callout %d' % (i + 1), m.get('text', ''), [], ['signal:' + lane] if lane else []))
    t = cfg.get('text') or {}
    for k in COPY_TEXT + LABEL_TEXT:
        if isinstance(t.get(k), str) and t[k]:
            texts.append(('text.%s' % k, t[k], [], []))
    for k in ('title', 'source'):
        texts.append((k, cfg.get(k, ''), [], []))
    bad, warn = [], []
    for where, s, ids, refs in texts:
        plain = re.sub(r'<[^>]+>', ' ', neutral(s))
        A = G | scope(set(ids) | set(re.findall(r'\{(\w+)\}', s or '')), refs)
        for m in NUM_RX.finditer(plain):
            if m.group(2):
                continue                                   # averages and ratios are derived
            val = float(m.group(1).replace(',', ''))
            after, before = plain[m.end():m.end() + 6], plain[:m.start()]
            if val <= 12 or 2000 <= val <= 2100 or re.match(r'\s*x\b', after) or val in A:
                continue
            if val <= 31 and (re.match(r'\s*(?:st|nd|rd|th)?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', after, re.I)
                              or re.search(r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*$', before, re.I)):
                continue
            if re.match(r'[:.]\d\d', after) or re.search(r'\d[:.]$', before):
                continue
            if val <= 53 and re.search(r'\b(?:kw|cw|wk|weeks?)\s*(?:\d+\s*(?:,|and|to|-)\s*)*$', before, re.I):
                continue
            (bad if val >= 100 else warn).append('%s: "%s"' % (where, plain[max(0, m.start() - 20):m.end() + 12].strip()))
    if bad:
        fail('these numbers are not in your own counts or discovery: %s. Every number comes from signals.json or '
             'discovery.json (computed with code), never typed in or carried over.' % '; '.join(bad[:8]))
    return warn

# The only keys the renderer reads; anything else (evidence ids, emails, notes an agent added) never reaches the HTML.
EMBED_KEYS = {'top': {'owner', 'title', 'source', 'meta', 'weeks', 'signals', 'text', 'portals', 'lanes', 'memory', 'entities',
                      'relations', 'questions', 'outputs', 'internal', 'lockSafe'},
              'entities': {'id', 'cls', 'real', 'safe', 'sector', 'detail', 'internalDetail', 'signal', 'weight', 'internal'},
              'questions': {'q', 'highlight', 'answer', 'grounding', 'internal'},
              'outputs': {'title', 'text', 'internalText', 'internal'},
              'memory': {'text', 'lane', 'week', 'internal'},
              'lanes': {'key', 'name', 'color'},
              'portals': {'name'},
              'signals': {'grid', 'vol', 'senders', 'orgs', 'pub_orgs', 'chats', 'weeks', 'files', 'focus'},
              'internal': {'nav', 'kicker', 'headline', 'intro', 'kpis', 'cards', 'note', 'total', 'totalLabel', 'legend', 'pillars'}}

def embed_copy(cfg):
    """What goes into the HTML: only the keys the renderer reads; no evidence ids, owner UPN or discovery details."""
    c = {k: json.loads(json.dumps(v)) for k, v in cfg.items() if k in EMBED_KEYS['top']}
    told = {e.get('id') for e in cfg.get('entities') or [] if isinstance(e, dict)
            and any(isinstance(f, str) and f.startswith('stated:') for f in e.get('from') or [])}
    for k in ('entities', 'questions', 'outputs', 'memory', 'lanes', 'portals'):
        if isinstance(c.get(k), list):
            c[k] = [{kk: vv for kk, vv in x.items() if kk in EMBED_KEYS[k]} if isinstance(x, dict) else x for x in c[k]]
    for x in c.get('entities') or []:            # version 2.0: Memory shows what the person told Copilot, apart from the data
        if isinstance(x, dict) and x.get('id') in told:
            x['told'] = 1
    c['signals'] = {k: v for k, v in c['signals'].items() if k in EMBED_KEYS['signals']}
    c['text'] = {k: v for k, v in (c.get('text') or {}).items() if k in set(COPY_TEXT + LABEL_TEXT) | {'orgMetric'}}
    if isinstance(c.get('internal'), dict):
        c['internal'] = {k: v for k, v in c['internal'].items() if k in EMBED_KEYS['internal']}
    m = c.get('meta') or {}
    c['meta'] = {'skillVersion': m.get('skillVersion'), 'generatedAt': m.get('generatedAt')}
    return c

# Organisation and sector words that may appear in safe aliases and ordinary text without identifying anyone.
COMMON_WORDS = set('''healthcare health research insurance medical medtech clinics clinic labs lab institute design graphic diagnostics biotech
pharmaceuticals pharma group holdings bank banking services solutions systems global international university college school
council department ministry office government national trust foundation company industries digital data energy retail foods
coffee toys traders importers airlines motors partners consulting technologies technology software networks media travel
customer customers colleague colleagues manager sponsor escalation public sector agency authority city county police fire
hospital hospitals care home homes education science innovation defence defense justice transport work pensions revenue
customs treasury'''.split())
MONTH_DAY_WORDS = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november',
                   'december', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}

# Words of the skill's own fixed wording (the slide's source line says "Outlook mail", "Teams group and 1:1 chats" and
# "OneDrive and SharePoint"): a domain stem that equals one of them is not an identity on its own (version 1.7.1).
FIXED_WORDS = {'outlook', 'teams', 'onedrive', 'sharepoint', 'microsoft', 'copilot', 'calendar'}

def safe_leak_terms(cfg, disc):
    """Everything that would identify a customer, person or escalation in a customer-safe file: full names, their
    distinctive words (first names, surnames, a customer's own word), email addresses and domains, and every person and
    organisation discovery found, on the sphere or not. Returns {term: what it identifies}."""
    items = disc.get('items', {})
    mine = set(W.words(cfg.get('owner', ''))) | {w for x in (disc.get('meta') or {}).get('self', []) for w in W.words(x.split('@')[0])}
    safe_words = {w for e in cfg['entities'] for w in W.words(e.get('safe') or '')}
    skip = COMMON_WORDS | MONTH_DAY_WORDS | mine | safe_words | W.GENERIC_WORDS
    terms = {}
    for e in cfg['entities']:
        if e['cls'] == 'hub' or not (e['cls'] in ('customer', 'person', 'uat') or e.get('internal') or (e.get('safe') and e['safe'] != e['real'])):
            continue
        real = e.get('real') or ''
        terms[real] = e['id']
        if e['cls'] not in ('customer', 'person', 'uat') and not e.get('internal'):
            continue   # a programme, theme or asset alias hides a whole site or file name; its plain words are not identities
        for t in re.findall(r"[^\W\d_][\w'-]*", real):
            if len(t) >= 3 and t[0].isupper() and W.fold(t) not in skip:
                terms[t] = e['id']
        for n in re.findall(r'\b\d{6}\b', real):
            terms[n] = e['id']
        for f in e.get('from') or []:
            it = items.get(f) or {}
            if it.get('email'):
                terms[it['email']] = e['id']
            if it.get('kind') == 'org' and not W.consumer_domain(it.get('label')):
                terms[it['label']] = e['id']
                stem = it['label'].split('.')[0]
                if len(stem) >= 4 and stem not in skip and stem not in FIXED_WORDS:
                    terms[stem] = e['id']
    # file and site names (discover.py --files) often carry customer and people names: a whole name may appear only as
    # the displayed name of an entity (whose own words are checked like any other text)
    shown = [W.fold(e.get('safe') or e.get('real') or '') for e in cfg['entities'] if e['cls'] != 'hub']
    for it in items.values():
        if it.get('kind') in ('file', 'site'):
            lab = (it.get('label') or '').strip()
            if re.search('[A-Za-z]', lab) and (len(lab.split()) >= 2 or len(lab) >= 10) and not any(W.fold(lab) in x for x in shown if x):
                what = 'a %s name in your data' % it['kind']
                terms.setdefault(lab, what)
                terms.setdefault(lab.lower(), what)      # any capitalisation
    for it in items.values():
        if it.get('kind') == 'person':
            if it.get('email') and not any(w in mine for w in W.words(it['email'].split('@')[0])):
                terms.setdefault(it['email'], 'a person in your data')
            lab = (it.get('label') or '').strip()
            if ' ' in lab and not set(W.words(lab)) <= mine:
                terms.setdefault(lab, 'a person in your data')
        elif it.get('kind') == 'org' and not it.get('automated') and not W.consumer_domain(it.get('label')):
            terms.setdefault(it['label'], 'an organisation in your data')
            stem = it['label'].split('.')[0]
            if len(stem) >= 6 and stem not in skip and stem not in FIXED_WORDS:
                terms.setdefault(stem, 'an organisation in your data')
    return terms

def document_names(disc):
    """Folded names of the person's sites and files (discover.py --files), for the customer-safe name rule."""
    out = {}
    for it in (disc or {}).get('items', {}).values():
        if it.get('kind') in ('file', 'site'):
            lab = (it.get('label') or '').strip()
            if re.search('[A-Za-z]', lab) and (len(lab.split()) >= 2 or len(lab) >= 10):
                out.setdefault(W.fold(lab), it['kind'])
    return out

def check_document_names(cfg, disc):
    """Customer-safe files never show a raw site or file name: an entity named after one needs a safe alias of its own."""
    docs = document_names(disc)
    if not docs:
        return
    def hit(name):
        f = W.fold(name or '')
        return next((k for d, k in docs.items() if f and (f == d or (len(d) >= 10 and d in f))), None)   # the whole site or file name is shown
    bad = []
    for e in cfg['entities']:
        if e['cls'] in ('hub', 'product') or e.get('internal'):
            continue
        k = hit(e.get('real'))
        if k and (not e.get('safe') or W.fold(e['safe']) == W.fold(e['real']) or hit(e['safe'])):
            bad.append('%s "%s" (the name of one of your %ss)' % (e['id'], e.get('real'), k))
    for i, o in enumerate(cfg.get('outputs') or []):
        if not o.get('internal') and hit(o.get('title')):
            bad.append('output %d "%s" (the name of one of your files)' % (i + 1, o.get('title')))
    if bad:
        fail('a customer-safe file must not show the raw names of your SharePoint sites or files: %s. Give each entity a "safe" '
             'alias in your own words (for example "Works council programme" or "AI regulation checklist"), and word output '
             'titles as what you produced rather than the file name; then build again.' % '; '.join(bad[:10]))

def check_safe_aliases(cfg, disc=None):
    if disc is not None:
        check_document_names(cfg, disc)
    bad = []
    for e in cfg['entities']:
        # identities only: a programme, theme or asset alias may reuse its own plain words (it hides a site or file name)
        if e['cls'] not in ('customer', 'person', 'uat') or not e.get('safe') or e['safe'] == e['real']:
            continue
        real_words = {W.fold(t) for t in re.findall(r"[^\W\d_][\w'-]*", e['real']) if len(t) >= 3} - COMMON_WORDS - MONTH_DAY_WORDS
        shown = set(W.words(e['safe']))
        if real_words & shown or set(re.findall(r'\d{6}', e['real'])) & set(re.findall(r'\d{6}', e['safe'])):
            bad.append('"%s" for %s' % (e['safe'], e['id']))
    if bad:
        fail('these safe aliases give the real name away: %s. Use a neutral alias such as "Healthcare Customer A" or "Customer sponsor".'
             % '; '.join(bad[:8]))

# ============================================================================================ views (version 1.8)
# One data collection, three views in one sphere: the last 7 days (day by day), the last month and the last three months
# (week by week). The config is written once from the three-month discovery; the build computes, for each view, its
# numbers, columns, node sizes and visibility, the numbers in shared text ({#...} placeholders), the Memory callouts of
# the week and the month, and the "In this view" findings, all from that view's own discovery.json and signals.json.

PH_RX = re.compile(r'\{#([^{}]*)\}')
PH_KIND_FIELDS = {'meeting': ('count', 'weeks', 'first', 'last'), 'thread': ('count', 'in', 'out', 'first', 'last'),
                  'sent': ('count', 'first', 'last'), 'org': ('count', 'mails', 'meetings', 'people', 'first', 'last'),
                  'person': ('count', 'mails', 'meetings', 'first', 'last'), 'escalation': ('count', 'first', 'last'),
                  'chat': ('count', 'last'), 'term': ('count',), 'file': ('count', 'last'), 'site': ('count', 'edited', 'last')}
PH_DATES = ('first', 'last')
PH_STATS = ('sum', 'max', 'last', 'nonzero', 'peak')
PH_WORDS = ('period', 'unit', 'current')
VIEW_SHARED = 'shared'          # texts every view shows (details, questions, answers, grounding, outputs, exampleChain)


class Missing(Exception):
    """A placeholder that has no value in this view (a date of something this view does not show)."""


def split_forms(p):
    """A placeholder may carry its noun, "{#sent:x.count|time|times}" ("1 time", "3 times"), or "|unit" for the view's
    column word ("4 days", "1 week")."""
    parts = [x.strip() for x in (p or '').split('|')]
    return parts[0], parts[1:]


def forms_ok(forms):
    return (not forms or forms == ['unit'] or (len(forms) == 2 and all(f and not re.search(r'[\d{}<>]', f) for f in forms)))


def parse_ph(p):
    p = split_forms(p)[0]
    if p in PH_WORDS:
        return ('word', p)
    if p.startswith('signal:'):
        key, _, stat = p[7:].rpartition('.')
        return ('sig', key, stat) if key and stat else None
    iid, _, field = p.rpartition('.')
    return ('item', iid, field) if iid and field else None


def text_fields(cfg):
    """(where, owner id or None, scope, text) for every config text a placeholder may sit in. scope is VIEW_SHARED for
    texts every view shows, 'base' for texts only the three-month view and the slide show (memory, slide lines)."""
    for e in cfg.get('entities', []):
        for k in ('detail', 'internalDetail'):
            if isinstance(e.get(k), str) and e[k]:
                yield ('%s of %s' % (k, e.get('id')), e.get('id'), VIEW_SHARED, e[k])
    for i, q in enumerate(cfg.get('questions', [])):
        yield ('Skills question %d' % (i + 1), None, VIEW_SHARED, q.get('q', ''))
        for line in q.get('answer') or []:
            yield ('answer to question %d' % (i + 1), None, VIEW_SHARED, line)
        if q.get('grounding'):
            yield ('grounding of question %d' % (i + 1), None, VIEW_SHARED, q['grounding'])
    for i, o in enumerate(cfg.get('outputs', [])):
        for k in ('title', 'text', 'internalText'):
            if isinstance(o.get(k), str) and o[k]:
                yield ('output %d %s' % (i + 1, k), None, VIEW_SHARED, o[k])
    for i, m in enumerate(cfg.get('memory', [])):
        yield ('memory callout %d' % (i + 1), None, 'base', m.get('text', ''))
    t = cfg.get('text') or {}
    for k in COPY_TEXT + LABEL_TEXT:
        if isinstance(t.get(k), str) and t[k]:
            yield ('text.%s' % k, None, VIEW_SHARED if k == 'exampleChain' else 'base', t[k])


def check_placeholders(cfg, disc):
    """Every {#...} placeholder names an item of the person's own discovery.json and a field that kind of item has, a
    keyword series with a statistic, or a view word; owner, title, source and names never hold one."""
    items, grid = disc.get('items', {}), cfg['signals'].get('grid') or {}
    bad = []
    for where, _, _, s in text_fields(cfg):
        for m in PH_RX.finditer(s or ''):
            ph = parse_ph(m.group(1))
            forms = split_forms(m.group(1))[1]
            ok = False
            if not forms_ok(forms) or (forms and (not ph or ph[0] == 'word' or (ph[0] == 'item' and ph[2] in PH_DATES)
                                                  or (ph[0] == 'sig' and ph[2] == 'peak'))):
                ok = False
            elif ph and ph[0] == 'word':
                ok = True
            elif ph and ph[0] == 'sig':
                ok = ph[1] in grid and ph[2] in PH_STATS
            elif ph and ph[0] == 'item':
                it = items.get(ph[1])
                ok = bool(it) and ph[2] in PH_KIND_FIELDS.get(it.get('kind'), ())
            if not ok:
                bad.append('%s: "%s"' % (where, m.group(0)))
    for k in ('owner', 'title', 'source'):
        if PH_RX.search(str(cfg.get(k) or '')):
            bad.append('%s: placeholders are only for numbers in the story text' % k)
    for e in cfg.get('entities', []):
        for k in ('real', 'safe', 'sector'):
            if PH_RX.search(str(e.get(k) or '')):
                bad.append('%s of %s: a name never holds a placeholder' % (k, e.get('id')))
    if bad:
        fail('these placeholders do not match your own data: %s. Write a count as {#<item id>.<field>} with an item id from '
             'your discovery.json and a field that kind of item has (count, mails, meetings, people, in, out, edited, weeks, '
             'first, last), a keyword series as {#signal:<key>.<sum|max|last|nonzero|peak>}, or {#period}, {#unit} and {#current}; a '
             'count may carry its noun, {#sent:<id>.count|time|times}, or |unit for days or weeks.'
             % '; '.join(bad[:8]))


def has_count_ph(s):
    """True when the text holds a placeholder that fills in a count (not a date, a column or a word)."""
    for m in PH_RX.finditer(s or ''):
        ph = parse_ph(m.group(1))
        if ph and ((ph[0] == 'item' and ph[2] not in PH_DATES) or (ph[0] == 'sig' and ph[2] != 'peak')):
            return True
    return False


def neutral(s):
    """Text with its placeholders taken out, for the checks that read typed-in numbers and dates."""
    return PH_RX.sub(' ', s or '')


def day_label(iso):
    d = dt.date.fromisoformat(iso[:10])
    return '%d %s' % (d.day, W.MONTH_NAMES[d.month - 1])


class ViewCtx:
    """What a view resolves placeholders and evidence against: its items (the three-month items, or the same items
    counted in this view), its keyword series and columns."""

    def __init__(self, name, disc, sig, base_items, tracked=None):
        self.name, self.disc, self.sig, self.base_items = name, disc, sig, base_items
        self.tracked = tracked
        win = W.window_from_meta(disc['meta'])
        self.win, self.unit = win, win['unit']
        self.labels = list(sig.get('weeks') or [])
        self.n = len(self.labels)
        self.grid = sig.get('grid') or {}
        fs = sig.get('focus') if isinstance(sig.get('focus'), dict) else None
        self.sgrid = (fs or {}).get('grid') or self.grid           # node sizes and lanes follow the focus subset
        v = sig['vol']
        self.emails, self.events, self.chats = sum(v['mail_in']) + sum(v['mail_out']), sum(v['meet']), sig.get('chats') or 0
        self.files = (sig.get('files') or {}).get('worked_on', 0) if isinstance(sig.get('files'), dict) else 0
        self.total = self.emails + self.events + self.chats + self.files
        self.today = dt.date.fromisoformat(disc['meta']['today'])

    def item(self, iid):
        if self.tracked is None:
            it = self.base_items.get(iid)
            if it and it.get('kind') == 'file' and 'cols' not in it and isinstance(it.get('week'), int):
                it = dict(it, cols=[1 if i == it['week'] else 0 for i in range(self.n)])
            return it
        return self.tracked.get(iid)

    def kind(self, iid):
        return (self.base_items.get(iid) or {}).get('kind')

    def when(self, col):
        lab = self.labels[col]
        return ('on ' + lab) if self.unit == 'day' else ('in the week of ' + lab)

    def words(self, w):
        if w == 'period':
            return W.VIEW_PERIOD[self.name] if self.name in W.VIEW_PERIOD else 'this window'
        if w == 'current':
            return 'today' if self.unit == 'day' else 'this week'
        return 'day' if self.unit == 'day' else 'week'

    def resolve(self, s):
        """The text with every placeholder filled for this view. A sentence whose placeholder has no value in this view
        (the date of something it does not show) is left out; None when nothing is left."""
        if not PH_RX.search(s or ''):
            return s
        parts = [x for x in (self._resolve(p) for p in re.split(r'(?<=[.!?])\s+(?=[A-Z{<])', s)) if x is not None]
        return ' '.join(parts) if parts else None

    def _resolve(self, s):
        def sub(m):
            ph, forms = parse_ph(m.group(1)), split_forms(m.group(1))[1]
            v = sub_value(ph)
            if forms and not isinstance(v, str):
                one, many = (self.words('unit'), self.words('unit') + 's') if forms == ['unit'] else forms
                return '%s %s' % ('{:,}'.format(v), one if v == 1 else many)
            return v if isinstance(v, str) else '{:,}'.format(v)
        def sub_value(ph):
            if ph[0] == 'word':
                return self.words(ph[1])
            if ph[0] == 'sig':
                ser = list(self.grid.get(ph[1]) or [0] * self.n)
                st = ph[2]
                if st == 'sum':
                    return sum(ser)
                if st == 'max':
                    return max(ser) if ser else 0
                if st == 'last':
                    return ser[-1] if ser else 0
                if st == 'nonzero':
                    return sum(1 for x in ser if x)
                if not ser or max(ser) <= 0:
                    raise Missing()
                return self.when(max(range(len(ser)), key=lambda i: (ser[i], -i)))
            rec = self.item(ph[1])
            if ph[2] in PH_DATES:
                if not rec or not rec.get(ph[2]):
                    raise Missing()
                return day_label(rec[ph[2]])
            v = (rec or {}).get(ph[2], 0)
            return v if isinstance(v, int) and not isinstance(v, bool) else 0
        try:
            return PH_RX.sub(sub, s or '')
        except Missing:
            return None


def load_views(specs):
    """--view NAME DISCOVERY SIGNALS, read and checked for shape."""
    out = {}
    for name, dpath, spath in specs or []:
        if name == 'quarter':
            continue                            # the three-month view is the config itself
        if name not in ('week', 'month'):
            fail('--view takes week or month (the three-month view is the config itself), not "%s".' % name)
        if name in out:
            fail('the %s view was given twice.' % name)
        try:
            out[name] = (json.load(open(dpath, encoding='utf-8')), json.load(open(spath, encoding='utf-8')))
        except (OSError, ValueError) as e:
            fail('cannot read the %s view (%s).' % (name, e))
    return out


def check_views(cfg, disc, views):
    """The fresh-analysis guard for the views: every view is the same person's same collected data, counted for its own
    window on the same day with the same keywords and focus, exactly as discover.py and count_signals.py wrote it."""
    if not views:
        return
    win, _ = read_choices(cfg)
    dm, sig = disc.get('meta') or {}, cfg['signals']
    sm = sig.get('meta') or {}
    today = dt.date.fromisoformat(dm['today'])
    if win != 'quarter' or W.meta_window(dm) != ('week', W.preset_window('quarter', today)['start'].isoformat(), 14):
        fail('the week and month views go with a three-month sphere: build the config from the three-month run '
             '(meta.choices.window "quarter", scripts/window.py --views).')
    if not dm.get('source') or dm.get('source') != sm.get('source'):
        fail('discovery.json and the signals do not record the same collected data (meta.source); run discover.py and '
             'count_signals.py of this version on the same result files.')
    owner = W.addresses(dm.get('self', []))
    for name, (vd, vs) in sorted(views.items()):
        vdm, vsm = vd.get('meta') or {}, vs.get('meta') or {}
        what = 'the %s view' % name
        if W.addresses(vdm.get('self', [])) != owner or W.addresses(vsm.get('self', [])) != owner:
            fail('%s was made for %s, not for %s: every view comes from your own data. Run discover.py and count_signals.py '
                 'for it with the same --self.' % (what, ', '.join(W.addresses(vdm.get('self', [])) or ['nobody']), ', '.join(owner)))
        if vdm.get('today') != dm.get('today'):
            fail('%s was made on %s, but the three-month run on %s: run every view on the same day.' % (what, vdm.get('today'), dm.get('today')))
        want = W.preset_window(name, today)
        exp = (want['unit'], want['start'].isoformat(), want['columns'])
        if W.meta_window(vdm) != exp or W.meta_window(vsm) != exp:
            fail('%s must be counted %s, but discovery.json says %s and signals.json %s; run both with the flags '
                 'scripts/window.py --views prints for it.' % (what, describe_window(exp), describe_window(W.meta_window(vdm)),
                                                                describe_window(W.meta_window(vsm))))
        if vdm.get('source') != dm.get('source') or vsm.get('source') != dm.get('source'):
            fail('%s comes from different data than the three-month run (other result files, chats or files). Run '
                 'discover.py and count_signals.py for it on exactly the same files.' % what)
        vo = vdm.get('viewOf') or {}
        if vo.get('fingerprint') != dm.get('fingerprint') or vo.get('source') != dm.get('source') or not isinstance(vd.get('tracked'), dict):
            fail('%s discovery.json was not made with --view-of your three-month discovery.json.' % what)
        if not vsm.get('digest') or vsm['digest'] != W.signals_digest(vs):
            fail('%s signals.json is not exactly what count_signals.py wrote; run it again and use its file unchanged.' % what)
        if (vsm.get('viewOf') or {}).get('digest') != sm.get('digest'):
            fail('%s signals.json was not counted with --view-of your three-month signals.json.' % what)
        if vsm.get('fingerprint') != vdm.get('fingerprint'):
            fail('%s discovery.json and signals.json come from different data (fingerprints %s and %s).'
                 % (what, vdm.get('fingerprint'), vsm.get('fingerprint')))
        if (vsm.get('keywords') or {}) != (sm.get('keywords') or {}):
            fail('%s was counted with other keywords than the three-month run.' % what)
        if (vsm.get('focus') or None) != (sm.get('focus') or None) or (('focus' in vs) != ('focus' in sig)):
            fail('%s was counted for another focus than the three-month run.' % what)
        v = vs['vol']
        if (sum(v['mail_in']) + sum(v['mail_out']), sum(v['meet'])) != (vdm.get('emails'), vdm.get('calendarEvents')):
            fail('%s signals and discovery.json count different emails or calendar events.' % what)
        ch = vdm.get('chats') or {}
        if vs.get('chats', 0) != (ch.get('group', 0) + ch.get('oneOnOne', 0) if ch.get('listed') else 0):
            fail('%s counts %s chats, but its discovery.json found %s.' % (what, vs.get('chats'), ch.get('group', 0) + ch.get('oneOnOne', 0)))
        if list(vs.get('weeks') or []) != W.column_labels(want):
            fail('%s columns are not the %s of its window.' % (what, W.unit_words(want['unit'])[1]))
        if ('files' in vs) != ('files' in sig):
            fail('%s %s files but the three-month run %s; use the same --files everywhere.'
                 % (what, 'has' if 'files' in vs else 'has no', 'has them' if 'files' in sig else 'has none'))
        check_files(vs, vdm, want['columns'])


SHARED_NUM_OK = re.compile(r'\d+\s*[x\u00d7]\b|\d+:\d+')
MONTH_WORD_RX = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b')


def check_shared_texts(cfg, disc, views):
    """Text every view shows may hold no typed-in count and no date outside the shortest view: its numbers come from
    placeholders the build fills for each view, so a three-month number never reaches the week."""
    if not views:
        return
    names = {n for e in cfg['entities'] for n in [e.get('real') or ''] + [a for a in e.get('aka') or [] if isinstance(a, str)]}
    names |= {l.get('name') or '' for l in cfg.get('lanes') or []} | {p.get('name') or '' for p in cfg.get('portals') or [] if isinstance(p, dict)}
    ok_nums = set()
    for n in names:
        ok_nums |= set(re.findall(r'\d+', n))
    dm = disc['meta']
    today = dt.date.fromisoformat(dm['today'])
    shortest = W.preset_window('week' if 'week' in views else 'month', today)
    first, last = shortest['start'], W.ahead_end(shortest, today) - dt.timedelta(days=1)
    months = {(first + dt.timedelta(days=i)).month for i in range((last - first).days + 1)}
    bad_n, bad_d = [], []
    for where, _, scope, s in text_fields(cfg):
        if scope != VIEW_SHARED:
            continue
        plain = re.sub(r'<[^>]+>', ' ', re.sub(r'\{\w+\}', ' ', neutral(s)))
        spans = []
        for m in DATE_RX.finditer(plain):
            spans.append((m.start(), m.end()))
            day, mon, yr = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(5), m.group(4), m.group(6))
            try:
                d = dt.date(int(yr) if yr else today.year, MONTHS[mon[:3].lower()], int(day))
            except ValueError:
                d = None
            if d is None or not (first <= d <= last):
                bad_d.append('%s: "%s"' % (where, m.group(0)))
        for m in MONTH_WORD_RX.finditer(plain):
            if MONTHS[m.group(1)[:3].lower()] not in months:
                bad_d.append('%s: "%s"' % (where, m.group(0)))
        for m in SHARED_NUM_OK.finditer(plain):
            spans.append((m.start(), m.end()))
        for m in NUM_RX.finditer(plain):
            if any(a <= m.start() < b for a, b in spans):
                continue
            v = m.group(1).replace(',', '')
            if v in ok_nums or (len(v) == 4 and 2000 <= int(v) <= 2100):
                continue
            bad_n.append('%s: "%s"' % (where, plain[max(0, m.start() - 20):m.end() + 12].strip()))
    if bad_n:
        fail('these numbers in text that the week, month and three-month views all show are typed in, so a three-month '
             'number would reach the week: %s. Write each count as a placeholder the build fills for every view, for example '
             '{#meeting:<id>.count}, {#org:<domain>.mails} or {#signal:<key>.sum}, or leave the number out.' % '; '.join(bad_n[:8]))
    if bad_d:
        fail('these dates or months in text that every view shows fall outside the last 7 days: %s. Write {#<item id>.last} or '
             '{#signal:<key>.peak} (filled for each view), or {#period}, instead of a date or month.' % '; '.join(bad_d[:8]))


def _plural(n, one, many=None):
    return '%s %s' % ('{:,}'.format(n), one if n == 1 else (many or one + 's'))


def _list_join(a):
    return a[0] if len(a) < 2 else ', '.join(a[:-1]) + ' and ' + a[-1]


def _pct(n, total):
    if not total or n <= 0:
        return 0
    return max(1, int(round(100.0 * n / total)))


def entity_refs(e, items):
    refs = [f for f in e.get('from') or [] if isinstance(f, str)]
    return [f for f in refs if f in items], [f for f in refs if f.startswith(('stated:', 'source:', 'builtin:'))]


def evidence(e, ctx):
    """An entity's evidence in a view: emails, calendar events, chats, files it was edited in, mentions (escalation
    numbers and terms in subjects) and keyword matches, its activity per column and its total."""
    data, _ = entity_refs(e, ctx.base_items)
    recs = [(ctx.kind(f), ctx.item(f)) for f in data]
    recs = [(k, r) for k, r in recs if r]

    def tot(kinds, field='count'):
        return sum((r.get(field) or 0) for k, r in recs if k in kinds)
    who = [r for k, r in recs if k in ('org', 'person')]
    if who:                                   # an organisation's or a person's own mails and meetings
        emails, meetings = sum(r.get('mails') or 0 for r in who), sum(r.get('meetings') or 0 for r in who)
    else:
        emails, meetings = tot(('thread', 'sent')), tot(('meeting',))
    chats, files = tot(('chat',)), max(tot(('file',)), tot(('site',), 'edited'))
    mentions = tot(('escalation', 'term'))
    ser = list(ctx.sgrid.get(e.get('signal')) or []) if e.get('signal') else []
    keywords = sum(ser)
    if keywords:
        cols = ser
    else:
        cols = [0] * ctx.n
        for _, r in recs:
            for i, x in enumerate((r.get('cols') or [])[:ctx.n]):
                cols[i] += x if isinstance(x, int) else 0
    t = keywords or (emails + meetings + chats + files + mentions)
    fcols = [0] * ctx.n                       # version 2.0: the columns with my own edits in the files it cites
    for k, r in recs:
        if k in ('file', 'site'):
            for i, x in enumerate((r.get('cols') or [])[:ctx.n]):
                fcols[i] += x if isinstance(x, int) else 0
    fl = max((i for i, x in enumerate(fcols) if x > 0), default=None)
    return {'e': [emails, meetings, chats, files, mentions, keywords], 'cols': cols, 't': t, 'fl': fl}


def first_seen(e, base_items):
    """The earliest day the three-month discovery saw an entity's own items (meetings, threads, mail, people,
    organisations, escalations), or None."""
    data, _ = entity_refs(e, base_items)
    days = [base_items[f].get('first') for f in data if base_items[f].get('kind') in ('meeting', 'thread', 'sent', 'org', 'person', 'escalation')]
    days = [d for d in days if d]
    return min(days) if days else None


def view_entities(cfg, ctx, base_ctx, is_base, focus_id):
    """Per entity: shown in this view or not, node size, evidence, busiest column, share and the details for this view."""
    out = {}
    for e in cfg['entities']:
        eid = e['id']
        if e['cls'] == 'hub':
            d = ctx.resolve(e.get('detail') or '')
            out[eid] = {'v': 1, 's': 14, 'd': d or ''}
            continue
        ev = evidence(e, ctx)
        data, said = entity_refs(e, ctx.base_items)
        sig = e.get('signal')
        if is_base or eid == focus_id:
            vis = True
        else:
            vis = bool(ev['t']) or (not data and not sig and bool(said))
        w = e.get('weight') if isinstance(e.get('weight'), (int, float)) and not isinstance(e.get('weight'), bool) else 0
        if is_base:
            size = 3 + math.sqrt(max(0, sum(ctx.sgrid.get(sig) or []))) * 0.5 if sig else 3 + w * 0.8
        elif sig:
            size = 3 + math.sqrt(max(0, sum(ctx.sgrid.get(sig) or [])) * base_ctx.total / max(1, ctx.total)) * 0.5
        else:
            eb = evidence(e, base_ctx)['t']
            if eb > 0:
                ratio = (ev['t'] / max(1, ctx.total)) / (eb / max(1, base_ctx.total))
                f = min(1.6, max(0.5, math.sqrt(ratio))) if ev['t'] else 0.5
            else:
                f = 1.0
            size = 3 + w * 0.8 * f
        rec = {'v': 1 if vis else 0, 's': round(size, 2), 'e': ev['e'], 't': ev['t'],
               'x': round(min(100.0, 100.0 * ev['t'] / ctx.total), 1) if ctx.total else 0}
        if ev['e'][3] and ev['fl'] is not None:     # version 2.0: the "edited by" day of One item, the whole story
            rec['fl'] = ev['fl']
        cols = ev['cols']
        if cols and max(cols) > 0:
            b = max(range(len(cols)), key=lambda i: (cols[i], -i))
            rec['b'] = [b, cols[b]]
        d = ctx.resolve(e.get('detail') or '') if e.get('detail') else ''
        rec['d'] = d if d is not None else None
        if e.get('internalDetail'):
            rec['i'] = ctx.resolve(e['internalDetail'])
        out[eid] = rec
    return out


def _tokens(s):
    return [t for t in re.findall(r'\{(\w+)\}', s or '') if t != 'me']


def view_questions(cfg, ctx, vis):
    out = []
    for q in cfg.get('questions') or []:
        qt = ctx.resolve(q.get('q', ''))
        if qt is None or not all(vis.get(t, True) for t in _tokens(qt)):
            continue
        ans = [r for r in (ctx.resolve(x) for x in q.get('answer') or []) if r is not None and all(vis.get(t, True) for t in _tokens(r))]
        if not ans:
            continue
        g = ctx.resolve(q.get('grounding') or '')
        if g is None or not all(vis.get(t, True) for t in _tokens(g)):
            g = ''
        rec = {'q': qt, 'highlight': [h for h in q.get('highlight') or [] if vis.get(h, True)], 'answer': ans, 'grounding': g}
        if q.get('internal'):
            rec['internal'] = True
        out.append(rec)
    return out


def view_outputs(cfg, ctx, is_base):
    out = []
    for o in cfg.get('outputs') or []:
        refs = [f for f in o.get('from') or [] if isinstance(f, str)]
        timeless = any(f.startswith(('stated:', 'source:', 'builtin:')) for f in refs)
        if not (is_base or timeless or any((ctx.item(f) or {}).get('count') for f in refs if f in ctx.base_items)):
            continue
        title = ctx.resolve(o.get('title', ''))
        if title is None:
            continue
        rec = {'title': title, 'text': ctx.resolve(o.get('text', '')) or ''}
        if o.get('internalText'):
            it = ctx.resolve(o['internalText'])
            if it:
                rec['internalText'] = it
        if o.get('internal'):
            rec['internal'] = True
        out.append(rec)
    return out


def _avg(xs):
    return float(sum(xs)) / len(xs) if xs else 0.0


def view_memory(cfg, ctx):
    """Memory callouts for the week and the month, computed from that view's keyword series (lanes): the biggest topic,
    a peak against the other columns, a topic that came up in every column, and (weekly) one that rose or eased."""
    n, day = ctx.n, ctx.unit == 'day'
    full = list(range(n - 1)) if n > 1 else [0]            # the last column (today, or this week) is partial
    per = 'a day' if day else 'a week'
    others_w = 'other days' if day else 'the other weeks'
    cands = []
    for i, l in enumerate(cfg.get('lanes') or []):
        s = list(ctx.sgrid.get(l['key']) or [0] * n)
        tot = sum(s)
        if not tot:
            continue
        nm_ = '<b>%s</b>' % l['name']
        fv = [s[c] for c in full]
        pk = max(range(n), key=lambda c: (s[c], -c))
        rest = [s[c] for c in full if c != pk]
        usual = statistics.median(rest) if rest else 0
        cands.append(('big', tot, i, pk, '%s was my biggest topic: %s in %s.' % (nm_, _plural(tot, 'signal'), W.VIEW_PERIOD[ctx.name])))
        if len(full) >= 3 and min(fv) >= 1:
            cands.append(('steady', min(fv), i, full[-1], '%s came up every %s: %s, never fewer than %d %s.'
                          % (nm_, 'day' if day else 'week', _plural(tot, 'signal'), min(fv), per)))
        if s[pk] >= 3 and s[pk] >= 2 * max(1, usual):
            against = ('with hardly any on %s' % others_w) if usual < 1 else ('against about %d on %s' % (int(round(usual)), others_w))
            cands.append(('peak', s[pk] / max(1.0, usual), i, pk, '%s peaked %s: %s, %s.' % (nm_, ctx.when(pk), _plural(s[pk], 'signal'), against)))
        half = len(full) // 2
        if not day and half >= 2:
            a, b = _avg(fv[:half]), _avg(fv[half:])
            if b >= 2 and b >= 2 * max(a, 0.5) and int(round(b)) > int(round(a)):
                cands.append(('rise', b / max(a, 0.5), i, full[-1], '%s rose from about %d to %d %s.' % (nm_, round(a), round(b), per)))
            elif a >= 2 and b <= a / 2 and int(round(a)) > int(round(b)):
                cands.append(('ease', a / max(b, 0.5), i, full[-1], '%s eased from about %d to %d %s.' % (nm_, round(a), round(b), per)))
    picked, lanes_used = [], set()
    for kind in ('big', 'peak', 'steady', 'rise', 'ease', 'peak', 'steady'):
        pool = sorted([c for c in cands if c[0] == kind and c[2] not in lanes_used], key=lambda c: -c[1])
        if kind == 'big':
            pool = pool[:1]
        if pool and len(picked) < 4:
            c = pool[0]
            picked.append(c); lanes_used.add(c[2])
    picked.sort(key=lambda c: (c[3], c[2]))
    return [{'text': c[4], 'lane': c[2], 'week': c[3]} for c in picked]


def view_insights(cfg, ctx, base_ctx, ents, vis, focus_id):
    """Three to five findings for this view, in plain words, every number computed from its signals and discovery:
    the busiest day or week, the customers (or people) with the biggest share, what rose or eased against the time
    before, and what is new."""
    out = []
    v = ctx.sig['vol']
    files = v.get('files') or [0] * ctx.n
    per_col = [v['mail_in'][i] + v['mail_out'][i] + v['meet'][i] + (files[i] if i < len(files) else 0) for i in range(ctx.n)]
    if per_col and max(per_col) > 0:
        c = max(range(ctx.n), key=lambda i: (per_col[i], -i))
        parts = [_plural(v['mail_in'][c] + v['mail_out'][c], 'email'), _plural(v['meet'][c], 'calendar event')]
        if ctx.sig.get('files') is not None:
            parts.append(_plural(files[c], 'file'))
        out.append('Busiest %s: <b>%s</b>, with %s.' % ('day' if ctx.unit == 'day' else 'week',
                                                        ctx.labels[c] if ctx.unit == 'day' else 'the week of ' + ctx.labels[c], _list_join(parts)))
    by = {e['id']: e for e in cfg['entities']}
    def top(cls, idx, total):
        rows = [(ents[i]['e'][idx], i) for i, e in by.items() if e['cls'] == cls and vis.get(i) and not e.get('internal')]
        rows = sorted([r for r in rows if r[0] > 0], key=lambda r: (-r[0], r[1]))[:3]
        return [('{%s} (%d%%)' % (i, _pct(n, total))) for n, i in rows] if total else []
    cal = top('customer', 1, ctx.events)
    if len(cal) >= 2 or (cal and focus_id):
        out.append('Customers with the biggest share of my %s: %s.' % (_plural(ctx.events, 'calendar event'), _list_join(cal)))
    else:
        mi = sum(v['mail_in'])
        em = top('customer', 0, mi)
        if em:
            out.append('Customers who sent me the most of the %s I received: %s.' % (_plural(mi, 'email'), _list_join(em)))
    # rose or eased against the time before, from the keyword series (weekly averages)
    bn = base_ctx.n
    if ctx.name == 'week':
        now_of = lambda k: sum(ctx.sgrid.get(k) or [])
        prev_of = lambda k: _avg((base_ctx.sgrid.get(k) or [0] * bn)[bn - 5:bn - 1])
        say_now, say_prev = 'in the last 7 days', 'a week in the 4 weeks before this week'
        now_w = '%d'
    else:
        now_of = lambda k: _avg((base_ctx.sgrid.get(k) or [0] * bn)[bn - 5:bn - 1])
        if ctx.name == 'month':
            prev_of = lambda k: _avg((base_ctx.sgrid.get(k) or [0] * bn)[:bn - 5])
            say_prev = 'a week in the %d weeks before' % (bn - 5)
        else:
            prev_of = lambda k: _avg((base_ctx.sgrid.get(k) or [0] * bn)[:4])
            say_prev = 'a week in the 4 weeks from %s' % base_ctx.labels[0]
        say_now = 'a week in the 4 weeks from %s' % base_ctx.labels[bn - 5]
        now_w = 'about %d'
    series = []
    seen = set()
    for e in cfg['entities']:
        k = e.get('signal')
        if k and vis.get(e['id']) and not e.get('internal') and k in ctx.sgrid and k not in seen:
            seen.add(k); series.append(('{%s}' % e['id'], k))
    for l in cfg.get('lanes') or []:
        if l['key'] in ctx.sgrid and l['key'] not in seen:
            seen.add(l['key']); series.append(('<b>%s</b>' % l['name'], l['key']))
    rising, easing = [], []
    for label, k in series:
        a, b = prev_of(k), now_of(k)
        if b >= 3 and b >= 1.5 * a and int(round(b)) - int(round(a)) >= 2:
            rising.append(((b - a) * b / (a + 1), label, a, b))
        elif a >= 3 and b <= a / 1.5 and int(round(a)) - int(round(b)) >= 2:
            easing.append(((a - b) * a / (b + 1), label, a, b))
    if rising:
        _, label, a, b = max(rising)
        out.append('Rising: %s, %s %s, up from about %d %s.' % (label, now_w % round(b), ('signals ' + say_now) if ctx.name == 'week' else say_now, round(a), say_prev))
    if easing:
        _, label, a, b = max(easing)
        out.append('Easing: %s, %s %s, down from about %d %s.' % (label, now_w % round(b), ('signals ' + say_now) if ctx.name == 'week' else say_now, round(a), say_prev))
    # new: first seen inside this view (for the three months, inside the last month)
    since = W.preset_window('month' if ctx.name == 'quarter' else ctx.name, ctx.today)['start']
    fresh = []
    for e in cfg['entities']:
        if e['cls'] == 'hub' or not vis.get(e['id']) or e.get('internal'):
            continue
        f = first_seen(e, ctx.base_items)
        if f and dt.date.fromisoformat(f) >= since:
            fresh.append((f, e['id']))
    fresh.sort(key=lambda x: (x[0], x[1]), reverse=True)
    if fresh:
        bits = ['{%s} (%s)' % (i, day_label(f)) for f, i in fresh[:3]]
        out.append('First seen in %s: %s%s.' % (W.VIEW_PERIOD['month' if ctx.name == 'quarter' else ctx.name], _list_join(bits),
                                         (', and %d more' % (len(fresh) - 3)) if len(fresh) > 3 else ''))
    mi = sum(v['mail_in'])
    ppl = top('person', 0, mi)
    if len(out) < 5 and len(ppl) >= 2:
        out.append('People who sent me the most of the %s I received: %s.' % (_plural(mi, 'email'), _list_join(ppl)))
    return out[:5]


def view_text(cfg, ctx, name, is_base, focus_id, vis):
    t0 = cfg.get('text') or {}
    if is_base:
        t = {}
        for k, v in t0.items():
            if isinstance(v, str):
                r = ctx.resolve(v)
                t[k] = r if r is not None else ''
        return t
    lab = W.window_label(ctx.win, ctx.today)
    short = lab.rsplit(' ', 1)[0]
    word = {'week': 'Seven days', 'month': 'A month'}.get(name, 'A while')
    t = {'kicker': 'My Work IQ \u00b7 ' + lab, 'windowLabel': lab, 'sparkRange': short,
         'headline': ('%s of {%s}, understood.' % (word, focus_id)) if focus_id else ('%s of my work, understood.' % word),
         'period': '%s (%s)' % (W.VIEW_PERIOD[name], short)}
    if ctx.unit == 'day':
        t['memoryNote'] = 'Today, %s, is partial.' % ctx.labels[-1]
    else:
        t['memoryNote'] = 'The week of %s is partial (to %s).' % (ctx.labels[-1], day_label(ctx.today.isoformat()))
    ex = t0.get('exampleChain')
    r = ctx.resolve(ex) if ex else None
    t['exampleChain'] = r if r and all(vis.get(x, True) for x in _tokens(r)) else ''
    return t


def build_views(cfg, disc, views):
    """The per-view payload the renderer switches between: the three-month view from the config itself, the week and the
    month from their own discovery and signals."""
    base_items = disc.get('items', {})
    focus = read_choices(cfg)[1]
    fid = focus['id'] if focus else None
    base_ctx = ViewCtx('quarter', disc, cfg['signals'], base_items)
    base_label = W.window_label(base_ctx.win, base_ctx.today)
    ctxs = {'quarter': base_ctx}
    for name, (vd, vs) in views.items():
        ctxs[name] = ViewCtx(name, vd, vs, base_items, vd.get('tracked') or {})
    out = {'order': [v for v in W.VIEWS if v in ctxs], 'start': 'quarter', 'list': {}}
    for name in out['order']:
        ctx, is_base = ctxs[name], name == 'quarter'
        ents = view_entities(cfg, ctx, base_ctx, is_base, fid)
        vis = {i: bool(r['v']) for i, r in ents.items()}
        lab = W.window_label(ctx.win, ctx.today)
        rec = {'name': W.VIEW_NAME[name], 'period': W.VIEW_PERIOD[name], 'label': lab, 'unit': ctx.unit, 'weeks': ctx.labels,
               'signals': {k: v for k, v in ctx.sig.items() if k in EMBED_KEYS['signals']},
               'text': view_text(cfg, ctx, name, is_base, fid, vis),
               'title': cfg.get('title', '') if is_base else cfg.get('title', '').replace(base_label, lab),
               'source': cfg.get('source', '') if is_base else cfg.get('source', '').replace(base_label, lab),
               'questions': view_questions(cfg, ctx, vis), 'outputs': view_outputs(cfg, ctx, is_base),
               'ent': ents, 'insights': view_insights(cfg, ctx, base_ctx, ents, vis, fid),
               'hidden': sum(1 for e in cfg['entities'] if e['cls'] != 'hub' and not e.get('internal') and not vis.get(e['id']))}
        if is_base:
            rec['memory'] = [{'text': ctx.resolve(m.get('text', '')) or '', 'lane': m.get('lane'), 'week': m.get('week')}
                             for m in cfg.get('memory') or [] if not (m.get('internal'))]
        else:
            rec['memory'] = view_memory(cfg, ctx)
        rec['signals'] = json.loads(json.dumps(rec['signals']))
        out['list'][name] = rec
    return out


def resolve_config(cfg, disc):
    """The config with every placeholder filled for its own (three-month) window: what the slide shows and what the
    sphere embeds as its base texts."""
    c = json.loads(json.dumps(cfg))
    ctx = ViewCtx('quarter' if read_choices(cfg)[0] in (None, 'quarter') else 'base', disc, cfg['signals'], disc.get('items', {}))
    def r(s):
        x = ctx.resolve(s)
        return x if x is not None else ''
    for e in c.get('entities', []):
        for k in ('detail', 'internalDetail'):
            if isinstance(e.get(k), str):
                e[k] = r(e[k])
    for q in c.get('questions', []):
        q['q'] = r(q.get('q', ''))
        q['answer'] = [r(x) for x in q.get('answer') or []]
        if isinstance(q.get('grounding'), str):
            q['grounding'] = r(q['grounding'])
    for o in c.get('outputs', []):
        for k in ('title', 'text', 'internalText'):
            if isinstance(o.get(k), str):
                o[k] = r(o[k])
    for m in c.get('memory', []):
        if isinstance(m.get('text'), str):
            m['text'] = r(m['text'])
    t = c.get('text') or {}
    for k, v in list(t.items()):
        if isinstance(v, str):
            t[k] = r(v)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--discovery', required=True, help='discovery.json made by discover.py from the same data')
    ap.add_argument('--template', default=DEFAULT_TPL)
    ap.add_argument('--official-slide', default=os.path.join(HERE, '..', 'templates', 'official_workiq_slide.jpg'),
                    help='Image shown as the opening chapter; pass "" to leave it out')
    ap.add_argument('--customer-safe', action='store_true', help='Bake in safe names only and strip all internal content (for files you send to customers)')
    ap.add_argument('--previous', help='refresh: the saved config read by exact path from your own OneDrive; it must be yours')
    ap.add_argument('--view', nargs=3, action='append', metavar=('NAME', 'DISCOVERY', 'SIGNALS'),
                    help='version 1.8: a view of the same data, week or month, with its discovery.json and signals.json '
                         '(discover.py and count_signals.py with that view\'s window flags and --view-of)')
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8'))
    disc = json.load(open(a.discovery, encoding='utf-8'))
    # ---- fresh-analysis guard ----
    owner, dmeta, data_ev, stated = guard(cfg, disc)
    views = load_views(a.view)
    check_views(cfg, disc, views)              # version 1.8: every view is the same person's same data
    check_shared_texts(cfg, disc, views)
    if a.previous:
        prev = json.load(open(a.previous, encoding='utf-8'))
        p_owner = str((prev.get('meta') or {}).get('ownerUpn', '')).strip().lower()
        if p_owner != owner or vtuple((prev.get('meta') or {}).get('skillVersion')) < MIN_VERSION:
            fail('the saved config %s was made for %s, not by a fresh analysis for you (%s). Do a New build from your own data '
                 'and do not reuse anything from it.' % (a.previous, p_owner or 'nobody (an earlier version)', owner))
        print('CHANGES: ' + json.dumps(refresh_changes(prev, cfg), ensure_ascii=False))

    # ---- structural checks ----
    ids = {e['id'] for e in cfg['entities']}
    hubs = [e for e in cfg['entities'] if e['cls'] == 'hub']
    if len(hubs) != 1: fail('exactly one entity must have cls "hub" (the owner)')
    if hubs[0]['id'] != 'me':
        old = hubs[0]['id']
        for e in cfg['entities']:
            if e['id'] == old: e['id'] = 'me'
        cfg['relations'] = [[('me' if x == old else x) for x in r[:2]] + r[2:] for r in cfg['relations']]
        for q in cfg['questions']: q['highlight'] = ['me' if x == old else x for x in q['highlight']]
        ids = {e['id'] for e in cfg['entities']}
    for e in cfg['entities']:
        if e['cls'] not in CLASSES: fail('entity %s has unknown cls %s' % (e['id'], e['cls']))
        if e.get('signal') and e['signal'] not in cfg['signals']['grid']: fail('entity %s signal "%s" not in signals.grid' % (e['id'], e['signal']))
    unsized = []                           # version 1.7.1: node size and labels follow the signal, else the weight
    for e in cfg['entities']:
        if e['cls'] == 'hub' or e.get('signal'):
            continue
        w = e.get('weight')
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
            unsized.append(e['id'])
    if unsized:
        print('WARNING: these entities have neither a "signal" nor a numeric "weight", so the sphere draws them too small '
              'to be labelled: %s. Give each a weight computed from discovery (SKILL.md step 7).' % ', '.join(unsized))
    for r in cfg['relations']:
        for x in r[:2]:
            if x not in ids: fail('relation %s refers to unknown entity %s' % (r, x))
    for q in cfg['questions']:
        for x in q['highlight']:
            if x not in ids: fail('question "%s" highlights unknown entity %s' % (q['q'], x))
    for l in cfg['lanes']:
        if l['key'] not in cfg['signals']['grid']: fail('lane %s not in signals.grid' % l['key'])
    nweeks = len(cfg['weeks'])
    unit = W.meta_window(dmeta)[0]
    one, many = W.unit_words(unit)
    for k, v in cfg['signals']['grid'].items():
        if len(v) != nweeks: fail('signals.grid.%s has %d values, expected %d (one per %s)' % (k, len(v), nweeks, one))
    for k in ('mail_in', 'mail_out', 'meet'):
        if len(cfg['signals']['vol'][k]) != nweeks: fail('signals.vol.%s must have one value per %s' % (k, one))
    portals = cfg.get('portals')
    if portals is not None and (not isinstance(portals, list) or not 1 <= len(portals) <= 5 or any(not p.get('name') for p in portals)):
        fail('portals must be a list of 1 to 5 {"name": ...} items')
    if 'chats' not in cfg['signals']: print('WARNING: signals.chats missing; Teams chats will show 0')
    t = cfg['text']
    t['windowLabel'] = window_label(dmeta)
    vpay = build_views(cfg, disc, views) if views else None
    cfg = resolve_config(cfg, disc)        # version 1.8: placeholders filled for the base window

    extra_leaks = {}
    if a.customer_safe:
        check_safe_aliases(cfg, disc)
        extra_leaks = safe_leak_terms(cfg, disc)
    focus = read_choices(cfg)[1]
    cfg = embed_copy(cfg)
    if vpay:
        cfg['views'] = vpay
    if unit != 'week':                     # version 1.7: the renderer words a day-by-day window in days
        cfg['window'] = {'unit': unit, 'columns': nweeks}
    if focus:                              # version 1.7: the renderer puts the focus next to the hub and names it
        cfg['focus'] = {'type': focus['type'], 'id': focus['id']}
    real_names, leak_terms = set(), set()
    if a.customer_safe:
        drop = {e['id'] for e in cfg['entities'] if e.get('internal')}
        for e in cfg['entities']:
            if e.get('safe') and e['safe'] != e['real'] and e['cls'] != 'hub':
                e['_anon'] = True
                real_names.add(e['real'])
                real_names.update(re.findall(r'\b\d{6}\b', e['real']))
            if e.get('safe'): e['real'] = e['safe']
            e.pop('internalDetail', None)
        cfg['entities'] = [e for e in cfg['entities'] if e['id'] not in drop]
        cfg['relations'] = [r for r in cfg['relations'] if r[0] not in drop and r[1] not in drop]
        for v in ((cfg.get('views') or {}).get('list') or {}).values():
            v['ent'] = {k: {kk: vv for kk, vv in x.items() if kk != 'i'} for k, x in v['ent'].items() if k not in drop}
            v['questions'] = [q for q in v['questions'] if not q.get('internal')]
            for q in v['questions']:
                q['highlight'] = [x for x in q['highlight'] if x not in drop]
            v['outputs'] = [o for o in v['outputs'] if not o.get('internal')]
            for o in v['outputs']:
                o.pop('internalText', None)
        cfg['questions'] = [q for q in cfg['questions'] if not q.get('internal')]
        for q in cfg['questions']: q['highlight'] = [x for x in q['highlight'] if x not in drop]
        cfg['outputs'] = [o for o in cfg['outputs'] if not o.get('internal')]
        for o in cfg['outputs']: o.pop('internalText', None)
        cfg.pop('internal', None); cfg['lockSafe'] = True
        hub = [e for e in cfg['entities'] if e['cls'] == 'hub'][0]
        hub['real'] = hub.get('safe') or 'Me'
        ids = {e['id'] for e in cfg['entities']}
        # neutral ids for every anonymised entity and every signal key, so no real name survives in the file source
        blob = json.dumps(cfg, ensure_ascii=False)
        taken = set(ids); cnt = {}
        def fresh(prefix):
            while True:
                cnt[prefix] = cnt.get(prefix, 0) + 1
                cand = '%s%d' % (prefix, cnt[prefix])
                if cand not in taken:
                    taken.add(cand); return cand
        ren = {}
        for e in cfg['entities']:
            if e['cls'] == 'hub': continue
            if e['cls'] in ('customer', 'person', 'uat') or e.get('_anon'):
                ren[e['id']] = fresh({'customer': 'org', 'person': 'person', 'uat': 'esc'}.get(e['cls'], 'item'))
        for k in list(cfg['signals']['grid']):
            ren[k] = fresh('sig')
        anon_ids = {e['id'] for e in cfg['entities'] if e.get('_anon')}
        for old in ren:
            stem = old[2:] if old[:2] in ('c_', 'p_', 't_') else old
            if old in anon_ids or stem in anon_ids or old.startswith('c_'):
                leak_terms.add(old)
                if len(stem) >= 3: leak_terms.add(stem)
        for old in sorted(ren, key=len, reverse=True):
            blob = blob.replace('"%s"' % old, '"%s"' % ren[old]).replace('{%s}' % old, '{%s}' % ren[old])
        cfg = json.loads(blob)
        for e in cfg['entities']: e.pop('_anon', None)
        ids = {e['id'] for e in cfg['entities']}
    blob = json.dumps(cfg, ensure_ascii=False)
    for tok in set(re.findall(r'\{(\w+)\}', blob)):
        if tok not in ids: fail('text token {%s} does not match an entity id' % tok)
    if re.search('[\u2013\u2014]', blob): fail('config contains an em or en dash; use commas, colons, parentheses or "to"')
    shown = {e['id']: e.get('safe') or e['real'] for e in cfg['entities']}
    def untoken(v):                        # the static title, source and owner cannot switch views: a {token} shows its alias
        return re.sub(r'\{(\w+)\}', lambda m: shown.get(m.group(1), m.group(0)), v)
    for v in ((cfg.get('views') or {}).get('list') or {}).values():
        v['title'], v['source'] = untoken(v.get('title') or ''), untoken(v.get('source') or '')
    blob = json.dumps(cfg, ensure_ascii=False)
    tpl = open(a.template, encoding='utf-8').read()
    out = (tpl.replace('__CONFIG__', blob.replace('</', '<\\/'))
              .replace('__TITLE__', html.escape(untoken(cfg['title'])))
              .replace('__SOURCE__', html.escape(untoken(cfg['source'])))
              .replace('__OWNER__', html.escape(untoken(cfg['owner']))))
    official = ''
    if a.official_slide and os.path.exists(a.official_slide):
        ext = os.path.splitext(a.official_slide)[1].lower()
        mime = 'image/png' if ext == '.png' else 'image/jpeg'
        official = 'data:%s;base64,%s' % (mime, base64.b64encode(open(a.official_slide, 'rb').read()).decode('ascii'))
    out = out.replace('__OFFICIAL_SLIDE__', official)
    if a.customer_safe:
        scan = '\n'.join([blob, cfg['title'], cfg['source'], cfg['owner']])
        safe_text = ' '.join(e.get('safe', '') for e in cfg['entities']).lower()
        leak_terms = {x for x in leak_terms if not re.search(r'(?<![a-z0-9])' + re.escape(x.lower()) + r'(?![a-z0-9])', safe_text)}
        found = sorted(x for x in (real_names | leak_terms | set(extra_leaks)) if len(x) >= 2 and
                       re.search(r'(?<![A-Za-z0-9])' + re.escape(x) + r'(?![A-Za-z0-9])', scan, 0 if any(c.isupper() for c in x) else re.I))
        if found:
            fail('customer-safe file would still contain real names or ids: %s. Rewrite the text that mentions them '
                 '(use {entity_id} tokens, which show the safe alias; a programme, theme or asset named after a customer, '
                 'person, file or site needs a "safe" alias too), then build again.' % ', '.join(found))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(out)
    by = {}
    for e in cfg['entities']:
        if e['cls'] != 'hub': by[e['cls']] = by.get(e['cls'], 0) + 1
    print(json.dumps({'status': 'ok', 'out': a.out, 'customer_safe': bool(a.customer_safe), 'owner': owner,
                      'fresh_analysis': {'fingerprint': dmeta.get('fingerprint'), 'evidence_checked': True,
                                         'items_from_what_you_told_me': len(stated)},
                      'entities': len(ids) - 1, 'by_class': by, 'relations': len(cfg['relations']), 'weeks': nweeks, 'unit': unit,
                      'internal_module': bool(cfg.get('internal')), 'official_slide': bool(official), 'bytes': len(out.encode('utf-8')),
                      'views': {k: {'entities_shown': sum(1 for i, x in v['ent'].items() if x.get('v') and i in ids and i != 'me'),
                                    'signals': sum(sum(v['signals']['vol'][c]) for c in ('mail_in', 'mail_out', 'meet'))
                                    + (v['signals'].get('chats') or 0) + ((v['signals'].get('files') or {}).get('worked_on', 0)
                                                                          if isinstance(v['signals'].get('files'), dict) else 0),
                                    'insights': len(v['insights']), 'questions': len(v['questions']), 'memory': len(v['memory'])}
                                for k, v in (cfg.get('views') or {}).get('list', {}).items()} or None}))
    if stated:
        print('NOTE: %d item(s) are on the sphere because you said so, not because your data shows them: %s' % (len(stated), '; '.join(stated[:8])))

if __name__ == '__main__':
    main()
