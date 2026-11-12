"""Collect the signed-in person's OWN file activity (OneDrive, SharePoint and Teams libraries) for the Work IQ sphere.

READ-ONLY tool script for RunScript (from aether_tools import tools). It never writes, uploads, shares or changes anything in Microsoft 365;
it only writes two local files in the workspace:
  working/files.json         {"meta": {"owner", "self", "window", ...}, "files": [one object per file the person edited,
                             created or opened in the window]}; discover.py and count_signals.py refuse it unless
                             meta.owner is the first --self address
  working/files_report.json  counts, sources, caps and warnings (no file names)

Run (copy this file to .aether/scripts/ or pass it as "code"):
  RunScript {"path": ".aether/scripts/collect_files.py", "code": "<this file>",
             "args": {"start": "2026-07-20", "end": "2026-10-26"}}
  The window is "start" to "end" (end exclusive, as scripts/window.py prints them under "files"); "weeks" instead of
  "end" counts whole weeks from start, as in version 1.6.
Optional args:
  "out": "working/files.json", "report": "working/files_report.json",
  "selves": ["upn", "mail", "object id"]   (default: read from /me),
  "exclude": "<regex>"                      extra personal-file patterns to drop (matched on file and site names),
  "include_media": false                    true keeps images, video and audio too,
  "onedrive_search": false                  true adds own-OneDrive documents found by SearchDrive (partial, see below).

Sources (chosen from a read-only probe, 21 Oct 2026):
  1. /me/drive/recent?$top=1000 (one call): the person's own recent list across their OneDrive, other people's
     OneDrives and SharePoint and Teams libraries, newest access first. It is the only source with "opened by me"
     (fileSystemInfo.lastAccessedDateTime) and it names the last editor and the creator (email and display name, no id).
     It does not page; $top above 1000 falls back to 200. If its oldest access is newer than the window start the
     report says the early weeks may be missing.
  2. Names: /drives/{id} (owner group = the site or team name) and /sites/{host,siteId,webId} for other libraries;
     /me/joinedTeams marks libraries of the person's own teams as "Teams" (/groups/{id} is tried once for other groups).
  3. Opt-in: SearchDrive on the person's own OneDrive (queries docx, xlsx, pptx, pdf). It finds documents the person
     edited or created that never reached the recent list (sync clients, apps, agents), but it is relevance ranked and
     its paging stops after a few thousand hits, so it is a partial sample; items are marked source "onedrive-search".
  Not used: /me/insights/used and /me/insights/shared (not permitted), /me/insights/trending (other people's
  suggestions), files search via SearchM365 (25 hits, no dates, no paging), ExecuteSql drive_children (one folder at a
  time, editor names without email), /shares/ (refused by QueryGraph).

Never collected: the skill's own files and outputs, whoever made them (a colleague's Work IQ sphere or slide, saved setups,
working files), and anything in a skills folder (OneDrive path Cowork/skills); they are counted under skipped.skillFiles.

Every failed Graph call counts towards a per-conversation limit (20 permanent failures disable QueryGraph), so
lookups stop after a few failures and fall back to names taken from the site URL. If this script fails (for example
because the limit was reached earlier in the conversation), build without files and say so.
"""
import datetime as dt
import json
import os
import re
import time
import urllib.parse

try:
    from aether_tools import tools, log, args, set_result
except ImportError:                      # imported by local tests, outside RunScript
    tools = None

    def log(*a, **k):
        pass

    def args():
        return {}

    def set_result(v):
        print(json.dumps(v, indent=1))

TYPES = {
    'Word': ('doc', 'docx', 'docm', 'dot', 'dotx', 'dotm', 'rtf', 'odt'),
    'Excel': ('xls', 'xlsx', 'xlsm', 'xlsb', 'xlt', 'xltx', 'xltm', 'csv', 'ods'),
    'PowerPoint': ('ppt', 'pptx', 'pptm', 'pot', 'potx', 'potm', 'pps', 'ppsx', 'odp'),
    'PDF': ('pdf',),
    'OneNote': ('one', 'onetoc2', 'onepkg'),
    'Loop': ('loop', 'fluid'),
    'Other': ('vsd', 'vsdx', 'vsdm', 'whiteboard', 'txt', 'md', 'pages', 'numbers', 'key'),
}
EXT_TYPE = {e: t for t, exts in TYPES.items() for e in exts}
MEDIA = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'heic', 'webp', 'tif', 'tiff', 'mp4', 'mov', 'webm', 'avi', 'mkv',
         'm4a', 'mp3', 'wav', 'clipchamp'}
PERSONAL = r'\b(payslips?|pay slips?|tax returns?|p60|p45|passport|bank statements?|mortgage|personal vault)\b'
# keep in step with wiq_data.SKILL_FILE and wiq_data.SKILLS_FOLDER (this script runs on its own inside RunScript)
SKILL_FILE = re.compile(
    r'work[\s_-]*iq[\s_-]*(?:sphere|slide|story|ontology)'
    r'|^workiq[\s_-]*(?:config|keywords|sphere)'
    r'|^(?:discovery|signals|keywords|chats|chats_partial|files|files_report|folders)\b[^/\\]*\.jsonl?$'
    r'|^(?:skill|slide_style|workflow_details|error_table)\.md$|^(?:example_config|example_keywords|guard_data)\.json$', re.I)
SKILLS_FOLDER = re.compile(r'/cowork/skills(?:/|$)', re.I)
VERSION = '1.8.0'
LOOKUP_FAILS_PER_KIND = 3
LOOKUP_FAILS_TOTAL = 8
# the runtime refused the tool, the script's tool budget is spent or the user declined: make no further calls
STOP = ('ToolRefused', 'ScriptBudgetExceeded', 'ToolDenied')


def iso_day(s):
    return (s or '')[:10]


def file_type(name, package_type=None):
    if (package_type or '').lower() == 'onenote':
        return 'OneNote'
    ext = name.rsplit('.', 1)[-1].lower() if '.' in (name or '') else ''
    if ext in EXT_TYPE:
        return EXT_TYPE[ext]
    return 'Media' if ext in MEDIA else None


def identity(x):
    u = (x or {}).get('user') or {}
    return (u.get('email') or '').strip().lower(), (u.get('id') or '').strip().lower(), (u.get('displayName') or '').strip()


def make_is_me(selves, my_name):
    low = {s.strip().lower() for s in selves if s}

    def is_me(x):
        email, uid, name = identity(x)
        if email or uid:
            return (email in low) or (uid in low), False
        return bool(name and my_name and name.lower() == my_name.lower()), bool(name and my_name and name.lower() == my_name.lower())
    return is_me


def site_name_from_url(url):
    p = urllib.parse.urlparse(url or '')
    parts = [x for x in p.path.split('/') if x]
    if len(parts) >= 2 and parts[0].lower() in ('sites', 'teams'):
        return re.sub(r'[-_]+', ' ', urllib.parse.unquote(parts[1])).strip() or None
    return None


def stable_id(ri, item):
    spi = ri.get('sharepointIds') or {}
    if spi.get('listItemUniqueId'):
        return spi['listItemUniqueId'].strip('{}').lower()
    m = re.search(r'sourcedoc=(?:%7b|\{)?([0-9a-f-]{36})', (ri.get('webUrl') or item.get('webUrl') or '').lower())
    if m:
        return m.group(1)
    drive = (ri.get('parentReference') or {}).get('driveId') or ''
    return '%s!%s' % (drive, ri.get('id') or item.get('id') or '')


def skill_file(name, *urls):
    """The skill's own files and outputs (whoever made them) and anything in a skills folder."""
    if SKILL_FILE.search((name or '').strip()):
        return True
    return any(isinstance(u, str) and u and SKILLS_FOLDER.search(urllib.parse.unquote(u)) for u in urls)


def url_key(ri):
    u = ri.get('webDavUrl') or ri.get('webUrl') or ''
    if 'sourcedoc=' in u.lower():
        return None
    return urllib.parse.unquote(u).lower().split('?')[0] or None


class Lookups:
    """Read-only name lookups with a failure budget, cached per drive."""

    def __init__(self, api):
        self.api = api
        self.fails = {}
        self.stats = {}
        self.stopped = None

    def ok(self, kind):
        return (not self.stopped and self.fails.get(kind, 0) < LOOKUP_FAILS_PER_KIND
                and sum(self.fails.values()) < LOOKUP_FAILS_TOTAL)

    def get(self, kind, path, params=None):
        if not self.ok(kind):
            self.stats[kind + '_skipped'] = self.stats.get(kind + '_skipped', 0) + 1
            return None
        try:
            r = self.api.get(path, params or {})
            self.stats[kind + '_ok'] = self.stats.get(kind + '_ok', 0) + 1
            return r
        except Exception as e:   # each failure counts against the conversation's QueryGraph limit
            if type(e).__name__ in STOP:
                self.stopped = type(e).__name__
                self.stats['stopped'] = self.stopped
                return None
            self.fails[kind] = self.fails.get(kind, 0) + 1
            self.stats[kind + '_failed'] = self.stats.get(kind + '_failed', 0) + 1
            log('lookup %s failed (%s)', kind, str(e)[:80])
            return None


def collect(api, a):
    """Pure collection logic. api.get(path, params) returns a Graph body (dict); api.search_drive_pages(drive_id, query)
    yields lists of items. Returns (records, report)."""
    start = dt.date.fromisoformat(a['start'])
    end = dt.date.fromisoformat(a['end']) if a.get('end') else start + dt.timedelta(days=7 * int(a.get('weeks', 14)))
    S, E = start.isoformat(), end.isoformat()

    def inwin(s):
        return bool(s) and S <= iso_day(s) < E

    warnings = []
    me = api.get('/me', {'$select': 'id,userPrincipalName,mail,displayName'}) if not a.get('selves') else {}
    selves = list(a.get('selves') or [me.get('userPrincipalName'), me.get('mail'), me.get('id')])
    my_name = a.get('display_name') or me.get('displayName') or ''
    if not any('@' in (s or '') for s in selves):
        raise ValueError('no UPN or mail for the signed-in person; pass "selves"')
    is_me = make_is_me(selves, my_name)
    own_drive = None
    if a.get('onedrive_search'):
        try:
            own_drive = (api.get('/me/drive', {'$select': 'id'}) or {}).get('id')
        except Exception as e:
            warnings.append('own OneDrive id not readable (%s), so no OneDrive search' % type(e).__name__)
    excl = re.compile(PERSONAL + ('|' + a['exclude'] if a.get('exclude') else ''), re.I)
    keep_media = bool(a.get('include_media'))

    recent, rec_err = [], None
    for attempt in range(2):
        try:
            body = api.get('/me/drive/recent', {'$top': '1000'})
            recent = body.get('value') or []
            if body.get('@odata.nextLink'):
                warnings.append('the recent list offered another page, which this recipe does not read')
            rec_err = None
            break
        except Exception as e:
            rec_err = str(e)[:160]
            if type(e).__name__ in STOP or not re.search(r'\b(429|5\d\d)\b', rec_err):
                break
            time.sleep(5)
    if rec_err:
        raise RuntimeError('could not read /me/drive/recent: %s' % rec_err)

    skipped = {'outsideWindow': 0, 'folder': 0, 'notDocument': 0, 'personal': 0, 'duplicate': 0, 'skillFiles': 0}
    by_name_match = 0
    raw = []
    accessed = []
    for it in recent:
        ri = it.get('remoteItem') or it
        la = (it.get('fileSystemInfo') or {}).get('lastAccessedDateTime') or (ri.get('fileSystemInfo') or {}).get('lastAccessedDateTime')
        if la:
            accessed.append(iso_day(la))
        if 'folder' in ri or 'folder' in it:
            skipped['folder'] += 1
            continue
        name = ri.get('name') or it.get('name') or ''
        if skill_file(name, ri.get('webUrl'), ri.get('webDavUrl'), it.get('webUrl'), (ri.get('parentReference') or {}).get('path')):
            skipped['skillFiles'] += 1
            continue
        ftype = file_type(name, (ri.get('package') or {}).get('type'))
        if ftype is None or (ftype == 'Media' and not keep_media):
            skipped['notDocument'] += 1
            continue
        lm_me, n1 = is_me(ri.get('lastModifiedBy') or it.get('lastModifiedBy'))
        cr_me, n2 = is_me(ri.get('createdBy') or it.get('createdBy'))
        lm = ri.get('lastModifiedDateTime') or it.get('lastModifiedDateTime')
        cr = ri.get('createdDateTime') or it.get('createdDateTime')
        if not ((lm_me and inwin(lm)) or (cr_me and inwin(cr)) or inwin(la)):
            skipped['outsideWindow'] += 1
            continue
        by_name_match += bool(n1 or n2)
        raw.append({'ri': ri, 'it': it, 'name': name, 'type': 'Other' if ftype == 'Media' else ftype, 'lm': lm, 'cr': cr,
                    'la': la, 'lm_me': lm_me, 'cr_me': cr_me, 'source': 'recent'})
    oldest = min(accessed) if accessed else None
    coverage = 'complete' if (oldest and oldest < S and len(recent) < 1000) else 'unproven'
    if coverage != 'complete':
        warnings.append('the recent list (%d items) starts on %s, so files from earlier in the window may be missing'
                        % (len(recent), oldest or 'no date'))

    # names and container types for SharePoint and Teams libraries
    L = Lookups(api)
    joined = set()
    teams_body = L.get('teams', '/me/joinedTeams', {'$select': 'id'})
    if teams_body:
        joined = {t.get('id') for t in teams_body.get('value') or []}
    drives = {}
    for r in raw:
        pr = r['ri'].get('parentReference') or {}
        if pr.get('driveType') != 'documentLibrary':
            continue
        did = pr.get('driveId')
        if did in drives:
            continue
        spi = r['ri'].get('sharepointIds') or {}
        info = {'name': None, 'group': None, 'url': spi.get('siteUrl') or ''}
        d = L.get('drives', '/drives/%s' % did, {'$select': 'id,name,owner'}) if did else None
        grp = ((d or {}).get('owner') or {}).get('group') or {}
        if grp.get('displayName'):
            info['name'], info['group'] = grp['displayName'], grp.get('id')
        elif spi.get('siteId') and spi.get('webId') and info['url']:
            host = urllib.parse.urlparse(info['url']).netloc
            s = L.get('sites', '/sites/%s,%s,%s' % (host, spi['siteId'], spi['webId']), {'$select': 'displayName'})
            info['name'] = (s or {}).get('displayName')
        info['name'] = info['name'] or site_name_from_url(info['url']) or 'SharePoint site'
        drives[did] = info
    groups = {}
    for info in drives.values():
        g = info['group']
        if not g or g in groups:
            continue
        if g in joined:
            groups[g] = True
            continue
        gb = L.get('groups', '/groups/%s' % g, {'$select': 'resourceProvisioningOptions'})
        groups[g] = bool(gb) and 'Team' in (gb.get('resourceProvisioningOptions') or [])

    records, seen, seen_url = [], {}, {}
    def add(rec, key_url):
        if rec['id'] in seen or (key_url and key_url in seen_url):
            skipped['duplicate'] += 1
            old = seen.get(rec['id']) or seen_url.get(key_url)
            for k in ('lastModifiedByMe', 'createdByMe'):
                old[k] = old[k] or rec[k]
            for k in ('lastModifiedDateTime', 'createdDateTime', 'lastAccessedDateTime'):
                if rec.get(k) and (not old.get(k) or rec[k] > old[k]):
                    old[k] = rec[k]
            return
        seen[rec['id']] = rec
        if key_url:
            seen_url[key_url] = rec
        records.append(rec)

    for r in raw:
        ri, it = r['ri'], r['it']
        pr = ri.get('parentReference') or {}
        dtp = pr.get('driveType')
        if dtp == 'documentLibrary':
            info = drives.get(pr.get('driveId')) or {'name': site_name_from_url((ri.get('sharepointIds') or {}).get('siteUrl')) or 'SharePoint site', 'group': None}
            container, ctype = info['name'], ('Teams' if info['group'] and groups.get(info['group']) else 'SharePoint')
            cid = ((ri.get('sharepointIds') or {}).get('siteId') or pr.get('driveId') or '').lower() or None
        else:
            container, ctype, cid = 'OneDrive', 'OneDrive', None
        if excl.search(r['name']) or excl.search(container):
            skipped['personal'] += 1
            continue
        add({'id': stable_id(ri, it), 'name': r['name'], 'type': r['type'], 'container': container, 'containerType': ctype,
             'containerId': cid, 'lastModifiedDateTime': r['lm'], 'lastModifiedByMe': bool(r['lm_me']), 'createdDateTime': r['cr'],
             'createdByMe': bool(r['cr_me']), 'lastAccessedDateTime': r['la'], 'sharedByMe': None, 'source': 'recent'},
            url_key(ri))

    search_rep = 'off'
    if a.get('onedrive_search') and own_drive:
        added = errors = pages = 0
        for q in ('docx', 'xlsx', 'pptx', 'pdf'):
            if errors >= 3:
                break
            try:
                for items in api.search_drive_pages(own_drive, q):
                    pages += 1
                    for x in items:
                        if 'folder' in x or 'file' not in x:
                            continue
                        if skill_file(x.get('name'), x.get('webUrl'), x.get('webDavUrl'), (x.get('parentReference') or {}).get('path')):
                            skipped['skillFiles'] += 1
                            continue
                        ftype = file_type(x.get('name') or '')
                        if ftype in (None, 'Media'):
                            continue
                        lm_me, _ = is_me(x.get('lastModifiedBy'))
                        cr_me, _ = is_me(x.get('createdBy'))
                        if not ((lm_me and inwin(x.get('lastModifiedDateTime'))) or (cr_me and inwin(x.get('createdDateTime')))):
                            continue
                        if excl.search(x.get('name') or ''):
                            skipped['personal'] += 1
                            continue
                        before = len(records)
                        add({'id': stable_id(x, x), 'name': x.get('name'), 'type': ftype, 'container': 'OneDrive',
                             'containerType': 'OneDrive', 'containerId': None, 'lastModifiedDateTime': x.get('lastModifiedDateTime'),
                             'lastModifiedByMe': bool(lm_me), 'createdDateTime': x.get('createdDateTime'),
                             'createdByMe': bool(cr_me), 'lastAccessedDateTime': None, 'sharedByMe': None,
                             'source': 'onedrive-search'}, url_key(x))
                        added += len(records) - before
                    if pages >= int(a.get('search_max_pages', 40)):
                        break
            except Exception as e:
                errors += 1
                log('SearchDrive stopped for %s (%s)', q, str(e)[:80])
                if type(e).__name__ in STOP:
                    break
        search_rep = {'added': added, 'pages': pages, 'errors': errors, 'partial': True}
        warnings.append('own-OneDrive search is relevance ranked and stops after a few thousand hits: its %d added files are a sample' % added)

    if L.stopped:
        warnings.append('name lookups stopped early (%s); remaining site names come from the site address' % L.stopped)

    def edited(f):
        return (f['lastModifiedByMe'] and inwin(f['lastModifiedDateTime'])) or (f['createdByMe'] and inwin(f['createdDateTime']))
    n_edit = sum(1 for f in records if edited(f))
    by_ct = {}
    for f in records:
        by_ct[f['containerType']] = by_ct.get(f['containerType'], 0) + 1
    addrs = []
    for x in selves:
        x = (x or '').strip().lower()
        if '@' in x and x not in addrs:
            addrs.append(x)
    owner = (me.get('userPrincipalName') or '').strip().lower() or addrs[0]
    if owner not in addrs:
        addrs.insert(0, owner)
    meta = {'tool': 'work-iq-sphere collect_files_recipe', 'version': VERSION, 'owner': owner,
            'self': [owner] + [x for x in addrs if x != owner], 'window': {'start': S, 'end': E},
            'generatedAt': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}
    report = {'status': 'ok' if coverage == 'complete' else 'partial', 'owner': owner,
              'window': {'start': S, 'end': E}, 'files': len(records), 'edited': n_edit, 'opened': len(records) - n_edit,
              'created': sum(1 for f in records if f['createdByMe'] and inwin(f['createdDateTime'])),
              'byContainerType': by_ct, 'sites': len({f.get('containerId') or f['container'] for f in records if f['containerType'] != 'OneDrive'}),
              'sources': {'recent': {'returned': len(recent), 'oldestAccess': oldest, 'coverage': coverage},
                          'onedriveSearch': search_rep},
              'skipped': skipped, 'matchedByDisplayName': by_name_match, 'lookups': L.stats, 'warnings': warnings}
    return {'meta': meta, 'files': records}, report


class GraphApi:
    """RunScript adapter: QueryGraph bodies (oversize answers are read from the file the payload names) and SearchDrive pages."""

    def get(self, path, params):
        r = tools.graph.QueryGraph(path=path, query_params=params, description='Read-only: list my own recent files')
        p = r.payload
        if isinstance(p, dict) and 'value' not in p and p.get('file_path'):
            fp = p['file_path']
            for _ in range(30):
                for cand in (fp, os.path.join(os.getcwd(), fp), os.path.join('/mnt/workspace', fp)):
                    if os.path.exists(cand):
                        try:
                            return json.load(open(cand, encoding='utf-8'))
                        except ValueError:
                            pass
                time.sleep(1)
            raise RuntimeError('oversize answer could not be read')
        return p if isinstance(p, dict) else {}

    def search_drive_pages(self, drive_id, query):
        for page in tools.sharepoint_onedrive.SearchDrive.pages(drive_id=drive_id, query=query, top=200):
            yield page.items


def main():
    a = dict(args() or {})
    if not a.get('start'):
        raise ValueError('pass "start" and "end" (the window, as scripts/window.py prints it), or "start" and "weeks"')
    doc, report = collect(GraphApi(), a)
    out, rep = a.get('out', 'working/files.json'), a.get('report', 'working/files_report.json')
    for path, obj in ((out, doc), (rep, report)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    log('files.json: %d files (%d edited or created by me, %d only opened), %d SharePoint or Teams sites',
        report['files'], report['edited'], report['opened'], report['sites'])
    set_result(dict(report, out=out, report_path=rep))


if __name__ == '__main__' and tools is not None:
    main()
