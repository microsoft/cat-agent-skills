# Work IQ sphere: workflow details (skill version 2.0.0)

Read the section a step of SKILL.md names, when it names it. The rules in SKILL.md (Parts A and B, the Guardrails) always apply.

## Final reply (D4)

Read this before step 13 (and before the reply to a refresh or a small change). Reply exactly this shape, numbers table included (numbers from script output written with thousands separators, for example 1,803; safe aliases; no dashes):

```
**Your Work IQ sphere is ready.** Built fresh from your own data only: <display name>, <focus words>, with Week, Month and 3 months views (<label>), fingerprint <fingerprint>.

| Signals | Week | Month | 3 months |
|---|---|---|---|
| Emails (junk and duplicate copies removed) | <emails> | <emails> | <emails> (<received> received, <sent> sent) |
| Calendar events | <events> | <events> | <events> |
| Teams chats (group and 1:1) | <chats> | <chats> | <chats> |
| Files I worked on (OneDrive and SharePoint) | <files> | <files> | <files> (<edited> edited or created, <opened> opened) |
| **Total signals** | **<total>** | **<total>** | **<total>** |
| About <focus> | <focus total> | <focus total> | <focus total> (<focus emails> emails, <focus events> calendar events, <focus chats> chats, <focus files> files) |
| On the sphere | <shown> entities | <shown> entities | <entities> entities in <types> types, <relations> relationships |

**What your Work IQ remembers**
- <3 to 6 memory callouts of the three months, safe names in bold>

**Your files** (keep them in the same folder)
- Work IQ Sphere.html: for presenting. Starts customer-safe; press S to see which alias is which. Never send it.
- Work IQ Sphere (customer-safe).html: the only version to send to customers.
- Work IQ Sphere Slide.pptx: customer-safe slide with the 3 months numbers; the sphere opens the customer-safe HTML.

**Check before you present**
- Added because you told me: <items, or "nothing">.
- Internal only: <what, or "nothing">. Sensitivity-labelled sources: <list, or "none">.
- Left out: <personal files, a view with no activity, or sources not counted and why; omit the line if nothing>.
- Theme counts are keyword matches, so read them as direction. File counts come from your recent files list, so read them as a floor. <Partial> is partial.

**Presenting:** download the HTML and open it in Edge or Chrome (OneDrive and Teams previews do not run it). It opens on Microsoft's Work IQ slide and shows the 3 months view: W switches to Week and Month (Shift+W goes back), and every number, size and finding follows. Right arrow steps in, left arrow goes back, P plays the story in the view on screen, / searches for a customer, person or topic, L shows the legend, and selecting a dot shows why it's here. The story opens with "Same model. Different context.", shows One item, the whole story after Context (your most active item and what your data shows around it) and, after Why it matters, the story shows Connector or Work IQ: one call per item, or a single pass (its two buttons switch between the two). In Week, the sphere is your working set. S switches names, O shows Microsoft's Work IQ slide and Esc leaves it. K loops the story for booth screens, F goes full screen, ? lists every key.

Your setup is saved in your OneDrive (Documents/Cowork/work-iq-sphere), so say "Refresh my Work IQ" any time, or ask for changes ("rename Health Customer A", "remove ...", "add the agent I built").
```
   <focus words> is "covering all your work", or "focused on" followed by the focus entity's `safe` alias in bold (its name only when it has no alias), never the real name of a customer. <label> is `views.quarter.label` from step 1. Each column comes from that view's step 8 status line (`emails`, `calendar_events`, `chats`, `files_worked_on`, `total_signals`; <received> and <sent> are the three-month `mail_in` and `mail_out`, <edited> and <opened> its `files_edited` and `files_opened`) and the "On the sphere" row from step 10's `views` line (`entities_shown` for the week and the month). <Partial> is `views.quarter.partial` with a capital ("The week of 19 Oct"). The "About <focus>" row is only for a focused sphere: <focus> is the focus's safe alias in bold and the numbers are the `focus` totals of each view's step 8 status line (leave out files when they were not counted); then add "Focus counts match names, mail domains and keywords, so read them as direction." (for a programme or topic: "names and keywords") after the theme-count sentence. Drop the Week or Month column when that view was left out (step 6) and say why under "Left out". Drop the Files row when files were not included and say why under "Left out" (then also drop the file-count sentence); write "not counted" in the Teams row when chats were not read; list the internal slide under Your files when it was built. If saving the setup failed, replace the last line's first sentence with "Your setup could not be saved, so a refresh will start from your earlier saved setup of <date>." when an earlier saved setup of theirs is still in their OneDrive (the one a refresh read, or one step 12 found), and with "Your setup could not be saved, so a refresh will start from scratch." only when there is none.

## Files recipe (step 5)

The recipe reads only the person's own recent files list (`/me/drive/recent`: their OneDrive, other people's files they opened, SharePoint and Teams libraries) and the names of those sites. It never reads file contents, never writes to OneDrive or SharePoint, and never uses search, trending, shared-with-me lists or insights. It leaves out folders, media and personal files (pay slips, tax returns, passports, bank statements, mortgages, plus your `exclude`), and the skill's own files and outputs whoever made them (any Work IQ sphere, slide or saved setup, and anything in a skills folder). It writes `working/files.json` as `{"meta": {"owner": "<UPN>", "self": [...], "window": {...}}, "files": [one row per file the person edited, created or opened in the window]}` and `working/files_report.json` (counts and warnings, no names).

## Own-data check (step 11)

Save this block as `working/check_own.py` exactly (never change it), then run `python -B working/check_own.py "<skill>" working <UPN>`:
```python
import html, json, os, re, sys, zipfile
sys.dont_write_bytecode = True
SK, W, ME = sys.argv[1], sys.argv[2], sys.argv[3].strip().lower()
sys.path.insert(0, os.path.join(SK, 'scripts')); import wiq_data as WD
def load(n, d=W, default=None):
    p = os.path.join(d, n)
    return json.load(open(p, encoding='utf-8')) if default is None or os.path.exists(p) else default
cfg, disc = load('workiq_config.json'), load('discovery.json')
views = [load(os.path.join('views', v), W, {}) for v in ('discovery_week.json', 'discovery_month.json', 'signals_week.json', 'signals_month.json')]
ex = load('example_config.json', os.path.join(SK, 'examples'), {'meta': {}, 'owner': '', 'entities': [], 'lanes': []})
gd = load('guard_data.json', os.path.join(SK, 'scripts'), {})
first = lambda m: str(m.get('owner') or next((s for s in m.get('self', []) if '@' in s), '')).strip().lower()
owners = {str((cfg.get('meta') or {}).get('ownerUpn', '')).strip().lower(), first(cfg['signals'].get('meta') or {}), first(disc['meta'])}
owners |= {first(v['meta']) for v in views if isinstance(v.get('meta'), dict)}
bad = [] if owners == {ME} else ['the files are stamped for %s, not for %s' % (', '.join(sorted(o for o in owners if o)) or 'nobody', ME)]
if not bad and ME == (ex['meta'].get('ownerUpn') or '').lower(): sys.exit(print('OWN-DATA CHECK: OK (the fictional example itself)'))
def text(n):
    p = os.path.join(W, n)
    if not os.path.exists(p): return None
    if n.endswith('.pptx'):
        z = zipfile.ZipFile(p); x = ' '.join(z.read(i).decode('utf-8', 'ignore') for i in z.namelist() if i.endswith('.xml'))
        x = ' '.join(re.findall(r'>([^<>]+)<', x) + re.findall(r'(?:descr|title)="([^"]*)"', x))
    else:
        x = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', ' ', open(p, encoding='utf-8').read())
    return re.sub(r'\s+', ' ', html.unescape(x)).lower()
has = lambda t, s: bool(s) and re.search(r'(?<![a-z0-9])' + re.escape(s.lower()) + r'(?![a-z0-9])', t) is not None
grid, items = cfg['signals']['grid'], dict(disc.get('items', {}))
for v in views[:2]: items.update(v.get('items') or {})
mine = open(os.path.join(W, 'discovery.json'), encoding='utf-8').read().lower() + ' ' + ' '.join(
    [f for e in cfg['entities'] for f in e.get('from', []) if f.startswith('stated:')] +
    [v for k, v in load('keywords.json').items() if sum(grid.get(k, [0])) > 0]).lower()
sample = {ex['owner'], 'fictional sample', 'sam.taylor'} - {''} | {e['real'] for e in ex['entities'] if e['cls'] not in ('hub', 'product')}
sample |= {l['name'] for l in ex['lanes']} - {e['real'] for e in ex['entities'] if e['cls'] == 'product'}
shown = {x.lower() for x in [cfg.get('owner', '')] + [l['name'] for l in cfg['lanes']] + [p.get('name', '') for p in cfg.get('portals') or []]
         + [e.get('safe') or '' for e in cfg['entities']] + [e['real'] for e in cfg['entities'] if e['cls'] in ('product', 'programme', 'theme', 'asset') and not e.get('safe')] if x}
secret = {v.get('email') or '' for v in items.values() if v.get('kind') == 'person'}
secret |= {v['label'] for v in items.values() if ((v.get('kind') == 'person' and re.search(r'[ .]', v['label'])) or v.get('kind') in ('escalation', 'org', 'file', 'site'))
           and not (v.get('kind') == 'org' and WD.consumer_domain(v['label']))}
secret = {s for s in secret if len(s) >= 5 and s.lower() != 'onedrive' and not any(has(x, s) for x in shown)}
for n in ('workiq_config.json', 'Work IQ Sphere.html', 'Work IQ Sphere (customer-safe).html', 'Work IQ Sphere Slide.pptx', 'Work IQ Sphere Slide (internal).pptx'):
    t = text(n)
    if t is None: continue
    bad += ['%s: "%s" is from the fictional sample' % (n, s) for s in sample if has(t, s) and not has(mine, s)]
    if n in ('Work IQ Sphere (customer-safe).html', 'Work IQ Sphere Slide.pptx'):
        bad += ['%s: "%s" is a real name, address, number, file or site name in a customer-safe file' % (n, s) for s in secret if has(t, s)]
legacy = set(gd.get('legacyText', []))
said = [cfg.get('title', ''), cfg.get('source', '')] + [v for v in (cfg.get('text') or {}).values() if isinstance(v, str)] + [l['name'] for l in cfg['lanes']]
bad += ['"%s" is from an earlier version\'s sample' % s for s in said if WD.text_hash(s) in legacy]
for e in cfg['entities']:
    if e['cls'] in ('customer', 'person', 'uat') and (e.get('safe') or '').strip().lower() in ('', e['real'].strip().lower()):
        bad.append('%s "%s" needs a safe alias that differs from its real name' % (e['cls'], e['real']))
print('OWN-DATA CHECK: ' + ('OK' if not bad else 'FAIL\n' + '\n'.join(sorted(set(bad)))))
sys.exit(1 if bad else 0)
```
    It checks that the config, the signals, the discovery and the week and month views are all stamped for the signed-in user (a mail address that differs from the UPN is fine), that nothing from the fictional sample or an earlier version's sample appears unless the user's own data has it, that every customer, person and escalation has an alias that differs from its real name, and that the customer-safe HTML (every view and its search included) and slide contain no real person name, email address, organisation domain, escalation number, file name or site name from the user's discovery of any view (other than the shown name of an entity).

## Refresh (steps 1 to 6)

1. Read the saved setup under rule A8 and copy it to `working/previous_config.json` (step 12 replaces the saved copy before you reply, and you need the old callouts to say what changed). If it is missing or unusable, do a New build.
2. Never show a question card and never reuse the saved window or focus, whichever version saved the setup: the refresh builds all three views (Week, Month, 3 months) for all their work, unless the refresh request itself names one customer, programme or topic ("refresh my Work IQ for Contoso"); then run focus.py with that name in step 6, and when the saved setup has an entity for it, keep that entity's id and alias. Send the opening message (the refresh form for the version that saved it, D1), then run steps 1 to 6: every source again, files included even if the saved setup had none.
3. Start the new config from the saved one: keep a saved entity only if the new three-month discovery still gives it evidence, replace its `from` with ids from the new `discovery.json` (ids can change between versions), and keep its `safe` alias; drop the rest. Keep a role alias such as "My manager" only when the manager lookup in B1 confirms it again; otherwise give that person a neutral alias such as "Colleague A" and list the change under "Changed since". Keep saved weights, but recompute every person's `weight` from the new discovery, and give any newly added entity without a `signal` a `weight` as in step 7. Keep a saved relationship only if both ends are kept and the new data still supports it (drop `focuses on` unless the request names that focus again). Keep a `stated:` item only after asking the user again whether it still holds. Add what the data now shows (step 7, with its numbers for three months, whatever window the saved setup had), give any kept item named like one of their sites or files the alias B3 asks for, and re-stamp `meta` (A6: version 2.0.0, `"window": "quarter"`, the focus only if named).
4. Run steps 8 and 9, recomputing keywords, numbers, callouts, questions, answers and outputs; never reuse the old ones (the build refuses numbers that are no longer in the user's counts). Write every kept `detail` again with placeholders (step 9): a setup saved by 1.6 or 1.7 has typed-in counts and dates in its details, which the build refuses in text that every view shows.
5. Build the first sphere with the saved setup as `--previous`: `python -B "<skill>/scripts/build_workiq.py" --config working/workiq_config.json --discovery working/discovery.json --view week working/views/discovery_week.json working/views/signals_week.json --view month working/views/discovery_month.json working/views/signals_month.json --out "working/Work IQ Sphere.html" --previous working/previous_config.json`. It refuses a setup stamped for anyone else or made by an earlier version, and prints one `CHANGES:` line (entities added and removed, totals then and now, and the `stated:` items to confirm again). Then run the rest of steps 10 to 13.
6. Add to the reply "Changed since <previous generatedAt date>": entities added and removed (safe aliases), total signals then and now (from `CHANGES:`), and new or changed callouts. When the saved setup covered another window than three months (its `meta.choices.window` is not `"quarter"`, or its `weeks` are not 14 weekly columns), name both windows with the totals ("then 1,279 signals in the last month (21 Sep to 21 Oct 2026), now 3,264 in the last three months").

## Presenting (G)

- Download the HTML and open it from the PC in Edge or Chrome; it needs no internet. OneDrive, SharePoint and Teams previews do not run it.
- It opens on Microsoft's Work IQ slide: talk to it, then press the right arrow, Space or Enter (or click "Step into my Work IQ") to zoom into the sphere; P zooms in and starts playing. Clicking (or tabbing to and pressing Enter on) any part of the slide goes to that chapter. O, the "Work IQ slide" button, 0 or the left arrow from chapter 1 brings the slide back; O or Esc hides it again and returns to where you were.
- Views: the Week, Month and 3 months toggle at the top left (or W, and Shift+W to go back) switches the whole sphere between the last 7 days (day by day), the last month and the last three months (week by week); every number, node size, caption, chart, Memory callout, Skills answer and finding follows. It starts on 3 months. Play and kiosk mode play the view on screen. A node with no activity in a view is hidden there. Add `#week`, `#month` or `#3months` to the end of the file address to open on that view.
- Chapters: Same model, My Work IQ, Business data, Context, One item, Memory, Skills, Copilot and agents, Why it matters, Connector or Work IQ, the Internal chapter (Internal view only, when built) and Explore. Right and left arrows (also Page Down and Page Up, so presentation clickers work, and Space for next) or the chapter bar move between them; Home and End go to the first chapter and to Explore; 1 to 9 go straight to the first nine chapters (the chapter bar or the arrows reach Connector or Work IQ; End reaches Explore). P plays or pauses the story; from Explore or the last chapter it starts again at chapter 1 and it ends with "End of the story".
- Connector or Work IQ ("Access is not understanding."): the same dots twice. It starts as a connector sees them (every item the same small grey dot, no names, no lines) and after about 2.5 seconds (at once with reduced motion) shows them as Work IQ connects them, as in Context. "A connector sees" and "Work IQ understands" switch between the two and hold the choice. Its cards use the view on screen: the connector climbs to at least one call per signal plus a search ("Illustrative: one call per item."); Work IQ makes a single pass over the entities and relationships Context shows and returns only the selected context (the "Selected context" strip). The quote under them is credited to Charles Lamanna, Microsoft, Nov 2026, never the person's result.
- Same model ("Same model. Different context."), the first chapter: three identical MODEL boxes; the person's own dots gather under the middle one (the other two clouds are illustrative), and "No two people have the same Work IQ." leads into their data.
- Business data: the dots stream in from eight named sources, as on the whiteboard: Email, Meetings, Chat, Files, People (distinct email senders) and Activity (emails sent and files worked on) with the view's counts, and CRM and Websites greyed, "via connectors, not in my sphere yet", with no number. People and Activity describe the signals and add no dots. The 600 TB quote is credited to Charles Lamanna.
- Week is "My working set" in its kicker, caption, legend and tooltip (the toggle still reads Week): Work IQ's working set is the current active work, so it changes every day and every week.
- One item, the whole story (after Context): for each view, the item with files the person edited or created and the most signals (else the top topic or programme). The sphere flies to it and boxes draw in only for what their data shows: edited by me (with the last day or week), opened by me, chats, meetings, emails, the customers and people linked to it. Version history, approvals and other people who opened it stay greyed, "not in my sphere yet". Customer-safe shows its alias.
- Memory adds "Some context carries from one task to the next." and, under "Because I told Copilot", the items that rest on what the person said (stated:), apart from what the data shows. Copilot and agents: a "Selected context" strip feeds the same MODEL box in every ring, and it closes with "Every company will have the same model. No two companies, and no two people, have the same context."
- The knowledge spine (Jared Spataro, Microsoft Copilot Blog, Oct 2026: shared knowledge updated once, used by every agent). The hook shows its one credited quote under "No two people have the same Work IQ." Memory adds "From me to every agent". Copilot and agents adds a caption under the strip and a second closing line, "Models will keep changing. My context, and what we learn from it, stays." Why it matters has an "Ask your organisation" button (Enter or Space) that opens three questions adapted from Microsoft and Keystone research; on wide screens the panel widens and the card sits beside the five cards. Connector or Work IQ adds our own line beside the 80% quote, hidden on screens 800 px tall or less. The full and customer-safe files show the same text.
- Every chapter starts with "What you're seeing", a caption for the view on screen; L (or its Legend button) shows what the colours, sizes, lines and dots mean there. The opening chapter and Explore show "In this view", 3 to 5 findings worked out from the view's own numbers; select a name in them to explore it. Business data charts the emails, calendar events and files per day (Week) or per week (Month, 3 months).
- Search: / jumps to the search box at the top left in any chapter (or click it); type a customer, person or topic, use the up and down arrows to move through the matches, Enter flies to one and Esc clears. A match that is only in another view says so and switches to it.
- Click or tap a dot (or fly to it from the search) to explore it: its links light up and "Why it's here" says which of the person's own emails, calendar events, chats and files put it there in this view, its busiest day or week and its strongest links.
- S (or the switch at the top right) switches between customer-safe and Internal view in `Work IQ Sphere.html` only (an amber frame shows while real names are on screen). The customer-safe file shows the same switch locked on as a "Customer-safe file" badge; S there only explains that real names are not in the file. The switch is always visible, on the opening slide, over the help, in kiosk mode and on small screens, so the presenter can always see which view is on screen (while help is open it shows but does not click).
- K starts or stops kiosk mode for booth screens: customer-safe view, Microsoft's Work IQ slide, then the story, on a loop. Any key, click, touch or wheel pauses it; after a minute without interaction it starts again from the slide. F toggles full screen (if the browser refuses, F11). ? or H lists every key and gesture. M pauses or resumes all motion (it also follows the computer's reduce-motion setting). + and - zoom, R resets the view, Esc closes help, the slide or the legend, or clears a selection or a search.
- Drag to spin, scroll or pinch to zoom, double-click empty space to reset, point at a dot to see its share of the work in the view.
- Add `#sphere` to the end of the file address to skip the opening slide, `#kiosk` to start in kiosk mode (`#kiosk&sphere` loops without the slide, `#kiosk&month` loops the Month view). For a booth screen, open the customer-safe file, press K for kiosk mode and F for full screen (or add `#kiosk` to the link), turn on Do not disturb so notifications don't appear over it, and turn sleep off.
- The slide's links work in PowerPoint desktop when the slide and the customer-safe HTML sit in the same folder; PowerPoint for the web and Teams download the HTML instead. "Microsoft's Work IQ slide" shows the hidden official slide; click it or "Back to my Work IQ" to return. When files were counted, the Business data card shows a fourth row: the files the person worked on in OneDrive and SharePoint, included in the total.
