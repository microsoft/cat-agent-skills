#!/usr/bin/env python3
"""Find the focus of a Work IQ sphere in the person's OWN discovery.json (version 1.7): one customer, or one programme
or topic. Nothing else is read.

Usage:
  python focus.py --discovery working/discovery.json --type customer|programme|theme [--name "<what the person said>"]

Prints one JSON line:
  without --name   {"status": "candidates", "type", "candidates": [{"name", "item", "count"}, ... up to 4]}
                   customers by message volume (org: items with the most emails, automated ones left out, named the way
                   their own subjects name them); programmes from recurring meetings and busy threads (their series
                   names); topics from the busiest subject terms that are not an organisation's name.
  with --name      {"status": "ok", "type", "name", "item", "evidence": [ids], "domains": [...], "regex", "flags"} when it
                   is in their own data, else {"status": "not_found", "closest": [up to 4 of their own candidates]}.
"flags" are the focus flags for count_signals.py (step 8); "name", "item" and "evidence" say which entity to make for the
focus (step 7). Candidates and names are real names from the person's own data: show them only to the person, with the
warning that the list shows real names.
"""
import argparse, difflib, json, os, re, shlex, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wiq_data as W

COMMON = set('''group holdings services solutions systems global international company industries digital data partners consulting
technologies technology software networks media travel healthcare health research medical clinics labs institute design
university college school council department ministry office trust foundation bank insurance retail foods coffee toys'''.split())
SERIES_SKIP = re.compile(r'^(?:re|fw|aw|follow-up|followup|action|uat|help needed|focus time|fokuszeit)\b', re.I)


def compact(s):
    return ''.join(W.words(s))


def customers(items, top):
    """Customer candidates by message volume: organisations that are not automated, named by their own subjects."""
    out = []
    for k in top.get('org', []):
        it = items[k]
        if it.get('automated'):
            continue
        nm = W.org_display_name(it, items)
        if nm:
            out.append({'name': nm, 'item': k, 'count': it.get('mails', 0), 'meetings': it.get('meetings', 0)})
    out.sort(key=lambda c: (-c['count'], -c['meetings'], c['item']))
    return out


def series(items, top, orgs):
    """Programme candidates: the series names (the part before ':') of recurring meetings and busy threads, never an
    organisation's name."""
    groups = {}
    for kind in ('meeting', 'thread', 'sent', 'chat', 'upcoming'):
        for k in top.get(kind, []):
            lab = items[k].get('label') or ''
            pre = re.sub(r'\s*\([^)]*\)', '', lab.split(':', 1)[0]).strip() if ':' in lab else (lab if kind == 'chat' else '')
            if not pre or len(pre.split()) < 2 or SERIES_SKIP.match(pre) or any(o.lower() in pre.lower() for o in orgs):
                continue
            g = groups.setdefault(pre.lower(), {'name': pre, 'item': None, 'evidence': [], 'count': 0, 'recurring': 0})
            g['evidence'].append(k)
            g['count'] += items[k].get('count', 1)
            if kind == 'meeting' and items[k].get('count', 0) >= 2:
                g['recurring'] += 1
            if g['item'] is None or (kind == 'meeting' and not g['item'].startswith('meeting:')):
                g['item'] = k
    out = list(groups.values())
    out.sort(key=lambda g: (-(g['recurring'] > 0), -g['count'], g['name']))
    return out


TOPIC_STOP = set('''follow up notes note agenda invite invitation reminder thanks question questions draft final fyi request
requests recap minutes summary call kw cw'''.split())


def topics(items, top, orgs=()):
    """Topic candidates: the busiest subject terms that say what the work is about: not generic, no numbers, not an
    organisation's name, and not a part of a busier term (Studio after Copilot Studio)."""
    org_words = {w for o in orgs for w in W.words(o) if len(w) >= 4}
    out = []
    for k in top.get('term', []):
        lab = items[k]['label']
        ws = W.words(lab)
        meaning = [w for w in ws if len(w) >= 4 and w not in W.GENERIC_WORDS and w not in TOPIC_STOP]
        if not meaning or re.search(r'\d', lab) or set(ws) & org_words or set(ws) <= W.GENERIC_WORDS | TOPIC_STOP:
            continue
        n = items[k]['count']
        if any(set(ws) <= set(W.words(o['name'])) and o['count'] * 1.25 >= n for o in out):
            continue                                # a part of a term already listed
        out = [o for o in out if not (set(W.words(o['name'])) < set(ws) and n * 1.25 >= o['count'])]   # the longer term says more
        out.append({'name': lab[:1].upper() + lab[1:], 'item': k, 'count': n, 'evidence': [k]})
    out.sort(key=lambda o: -o['count'])
    return out


def regex_for(name, extra=()):
    ws = W.words(name)
    alts = [r'\b' + r'\W*'.join(re.escape(w) for w in ws) + r'\b'] if ws else []
    alts += [x for x in extra if x and x not in alts]
    return '|'.join(dict.fromkeys(alts))


def resolve(disc, kind, name):
    """(the focus found in the person's own discovery, or None; the pool of candidates it was looked up in)."""
    items, top = disc.get('items', {}), disc.get('top', {})
    custs = customers(items, top)
    orgs = [c['name'] for c in custs]
    q, qw = compact(name), set(W.words(name)) - W.GENERIC_WORDS
    if kind == 'customer':
        hits = [c for c in custs if q and (compact(c['name']) == q or (len(q) >= 4 and compact(c['name']).startswith(q))
                                          or (len(q) >= 4 and q in compact(c['item'].split(':', 1)[1].split('.')[0])))]
        if not hits:
            return None, custs
        c = hits[0]
        org = items[c['item']]
        stem = re.sub(r'[^a-z0-9]', '', org['label'].split('.')[0].lower())
        first = W.words(c['name'])[0] if W.words(c['name']) else ''
        extra = [stem] if stem != compact(c['name']) else []
        if len(first) >= 5 and first not in COMMON and first not in W.GENERIC_WORDS and len(W.words(c['name'])) > 1 and \
                sum(1 for o in orgs if W.words(o) and W.words(o)[0] == first) == 1:
            extra.append(r'\b%s\b' % first)
        sites = [s for s in top.get('site', []) if items[s].get('edited', 0) >= 2 and items[s]['label'].lower().startswith(c['name'].lower())]
        return {'name': c['name'], 'item': c['item'], 'evidence': [c['item']] + sites[:1], 'domains': [org['label']],
                'regex': regex_for(c['name'], extra)}, custs
    pool = series(items, top, orgs) if kind == 'programme' else (topics(items, top, orgs) + series(items, top, orgs))
    hits = [g for g in pool if qw and qw <= set(W.words(g['name']))] or [g for g in pool if q and q in compact(g['name'])]
    if not hits:
        return None, pool
    g = hits[0]
    return {'name': g['name'], 'item': g['item'], 'evidence': g['evidence'][:6], 'domains': [], 'regex': regex_for(g['name'])}, pool


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--discovery', required=True)
    ap.add_argument('--type', required=True, choices=('customer', 'programme', 'theme'))
    ap.add_argument('--name')
    ap.add_argument('--top', type=int, default=4)
    a = ap.parse_args()
    disc = json.load(open(a.discovery, encoding='utf-8'))
    items, top = disc.get('items', {}), disc.get('top', {})
    if not a.name:
        orgs = [c['name'] for c in customers(items, top)]
        pool = customers(items, top) if a.type == 'customer' else series(items, top, orgs) if a.type == 'programme' else topics(items, top, orgs)
        print(json.dumps({'status': 'candidates', 'type': a.type, 'candidates': [{'name': c['name'], 'item': c['item'], 'count': c['count']}
                                                                             for c in pool[:a.top]]}, ensure_ascii=False))
        return
    found, pool = resolve(disc, a.type, a.name)
    if not found:
        names = list(dict.fromkeys(c['name'] for c in pool))
        close = difflib.get_close_matches(a.name, names, n=a.top, cutoff=0.3) or names[:a.top]
        print(json.dumps({'status': 'not_found', 'type': a.type, 'asked': a.name,
                          'closest': [next({'name': c['name'], 'item': c['item'], 'count': c['count']} for c in pool if c['name'] == n) for n in close]},
                         ensure_ascii=False))
        return
    flags = '--focus-type %s --focus-regex %s' % (a.type, shlex.quote(found['regex']))
    if found['domains']:
        flags += ' --focus-domains %s' % shlex.quote('|'.join(found['domains']))
    print(json.dumps(dict({'status': 'ok', 'type': a.type}, **found, flags=flags), ensure_ascii=False))


if __name__ == '__main__':
    main()
