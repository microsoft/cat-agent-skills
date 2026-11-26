#!/usr/bin/env python3
import argparse, copy, re
from safety_text import *
import wall_check
from wall_check import govern
ENGINE="engine:access_checklist"
M={"delivery analyst":{"engagement-sharepoint":"viewer","delivery-planner":"viewer","client-teams-channel":"member","knowledge-repository":"viewer"},"delivery manager":{"engagement-sharepoint":"contributor","delivery-planner":"contributor","client-teams-channel":"member","knowledge-repository":"viewer"},"client delivery manager":{"engagement-sharepoint":"contributor","delivery-planner":"contributor","client-teams-channel":"member","knowledge-repository":"viewer"},"engagement coordinator":{"engagement-sharepoint":"viewer","delivery-planner":"contributor","client-teams-channel":"member","knowledge-repository":"viewer"}}  # role-access-matrix.md #1.1-#1.3
O={"none":0,"viewer":1,"member":2,"contributor":3,"admin":4,"owner":5}  # role-access-matrix.md #2.1-#2.3: every permission has its own rank
NAMES={v:k for k,v in O.items() if k!="owner"}
ADMIN_EXCLUDED=True  # workspace-inventory-rules.md #3.2
WALL_STATUSES={"clear","denied","hold"}  # confidentiality-and-ethical-wall-rules.md #2.2
INVENTORY_COLUMNS=wall_check.INVENTORY_COLUMNS  # workspace-inventory-rules.md #1.3 (one definition, checked by wall_check.inventory_problem)
KNOWN_CLASSIFICATIONS={"client_confidential","confidential","restricted","internal","public"}  # workspace-inventory-rules.md #2.3
def low(v): return canon_text(v)  # enums and roles: the one canonical comparison form (confidentiality-and-ethical-wall-rules.md #1.3)
def cset(xs): return {join_key(x) for x in xs or []}-{None}  # workspace IDs, types and classifications compare canonically; a blank key is in no set (#1.3)
def safe(x): return WITHHELD if hits(x) else x  # confidentiality-and-ethical-wall-rules.md #4.3
def strs(xs): return [x for x in (xs or []) if isinstance(x,str)]  # contract-valid arrays render without a TypeError (#1.3)
DECISION_COLUMNS=("workspace_id","workspace_type","default_permission","requested_permission","depends_on_knowledge","data_classification")  # workspace-inventory-rules.md #1.3
def _src(*xs): return rendered_values(*xs)
def _role_src(r): return () if low(r) in {low(k) for k in M} else _src(r)  # a matrix role is fixed vocabulary, not free text
def _hold_src(h):
    """The supplied text a hold line renders, in rendered order: its ID, reason, location and citation, each unless it
    is an engine template (#4.5)."""
    return _src(*(h.get(k) for k in ("hold_id","reason","path","citation") if not engine_text(k,h.get(k))))
# A first-week item that directs the joiner to read or use a knowledge item still pending practice review is never
# rendered as written: it is restated as a title-and-citation-only note (knowledge-reuse-rules.md #2.3, #2.5). Only an
# explicit cleared_for_internal_reuse status is cleared; anything else counts as pending. Reading order:
# 1. exact references (a knowledge ID or a full title, any separators between their words) are resolved against ALL
#    digest items, longest first, and blanked, so text naming a cleared item is never re-read as a pending one;
# 2. title words in the remaining text are compared with pending items only (two distinctive words - words this
#    engagement's own scope does not use - or one distinctive word there and a second title word anywhere in the item),
#    and only when the item has knowledge context or holds every distinctive title word and names no client location;
# 3. a generic reference to knowledge content (prior knowledge, the knowledge digest, lessons learned, reusable or
#    Closeout assets) is a reference to every pending digest item; with nothing pending it is rendered as written, so a
#    restatement always names concrete pending items;
# 4. any reference to knowledge content counts as consuming it, whatever the verb, voice or noun form ("should be
#    reviewed", "a review of prior knowledge is required"): there is no list of reading verbs. The only exemption is an
#    item that is clearly administrative about the review itself (_admin): every clause is an administrative action
#    (schedule, book, request, chase, confirm, check, ask, follow up, attend, escalate ...) whose object is the review,
#    its status, sign-off or approval, or the practice lead, followed only by plain prepositional phrases;
# 5. adjacent entries are read together in rendered order (as the pack's other run screens are): a pending ID or title,
#    or a knowledge-content phrase, that only the joined entries spell is a reference by every entry in the run, and
#    the cleared items any entry of the run names are kept.
# When uncertain, the item is qualified (fail toward caution).
CLEARED="cleared_for_internal_reuse"
_SEP=r"[^a-z0-9]*"
_KN_NOT=r"(?![ -]?(?:of|transfer|transfers|sharing|share|session|sessions|handover|hand over|gap|gaps|management|manager|managers|lead|leads|owner|owners|team|teams|check|checks|test|tests|area|areas|level|levels|worker|workers))"
_FW_GENERIC=re.compile(r"(?<![a-z0-9])(?:"
    r"(?:prior|previous|past|existing|historical|earlier|firm|practice|closeout|close out|released|reusable|shared|cleared|pending|harvested)[ -]?knowledge(?:[ -](?:items?|assets?|base|digest|pack|content|records?|library|repository|candidates?))?"
    r"|knowledge[ -](?:digest|items?|assets?|base|pack|content|records?|library|repository|candidates?)"
    r"|(?:the|this|that|our|any|all|its|their|such)\s+knowledge"+_KN_NOT+
    r"|knowledge\s+(?:from|in|of)\s+(?:the\s+)?(?:closeout|close out|previous|prior|last|earlier|digest|harvest)"
    r"|(?<!scope )(?<!sow )(?<!status )(?<!weekly )(?<!daily )(?<!news )(?<!email )(?<!e mail )digest"
    r"|lessons?[ -](?:learned|learnt|log|register|library)"
    r"|(?:reusable|released|harvested|closeout|close out)[ -](?:assets?|materials?|content|lessons?|records?|outputs?)"
    r"|assets?\s+from\s+the\s+(?:closeout|close out|previous|prior|digest))(?![a-z0-9])")
# A fuzzy title match (#2.5 title words) counts only beside knowledge context, or when every distinctive title word is
# present; a client-owned document or system location without knowledge context is never fuzzy-matched.
_FW_KCTX=re.compile(r"(?<![a-z0-9])(?:digest|knowledge|closeout|close out|lessons?|reusable assets?|(?:previous|prior|earlier|past) engagements?)(?![a-z0-9])")
_FW_CLIENT=re.compile(r"(?<![a-z0-9])(?:clients?\s+s(?![a-z0-9])|clients?'s?(?![a-z0-9])|clients'|(?:client|customer)\s+(?:portal|system|systems|site|sites|sharepoint|tool|tools|environment|tenant|workspace|intranet)|service\s+portal)")
_FW_ADMIN_V=re.compile(r"(?:please\s+)?(?:schedule|reschedule|book|request|chase|confirm|check|ask|follow up(?:\s+(?:on|with|about))?|attend|escalate|arrange|organi[sz]e|set up|track|invite|contact|remind|raise|log|query|notify)(?![a-z0-9])\s*")
_FW_REVIEW_OBJ=re.compile(r"(?<![a-z0-9])(?:review|reviews|reviewers?|status|sign ?offs?|approvals?|clearance|confirmation|practice leads?|knowledge management leads?|km leads?|knowledge managers?)(?![a-z0-9])")
_FW_PREP={"of","for","with","before","after","by","on","at","from","in","to","into","about","that","so","when","until","once","while","during","within","via","regarding","if","because","since","unless"}
_FW_CONT=re.compile(r"(?:the|a|an|its|their|our|with|for|of|by|on|before|after|in|at|during|within)(?![a-z0-9])")
_FW_ING_NOUN={"meeting","meetings","briefing","briefings","morning","evening","onboarding","training","thing","something","anything","everything","building","standing"}
def _fw_text(x): return id_spaced(norm(unwithheld(x) or "")) if isinstance(x,str) else ""
def _compact(t): return re.sub(r"[^a-z0-9]","",t)
def _target_rx(v):
    """An exact reference to an ID or title: its words in order with any separators between them, word-bounded."""
    w=re.findall(r"[a-z0-9]+",_fw_text(v)) if isinstance(v,str) and not is_withheld(v) else []
    return re.compile(r"(?<![a-z0-9])"+_SEP.join(map(re.escape,w))+r"(?![a-z0-9])") if w else None
def scope_words(p):
    """Words this engagement's own scope uses (title, client, objectives, scope, exclusions, deliverables): a title word
    that is one of them does not single out a knowledge item (#2.5)."""
    e=p.get("engagement") or {}; s=p.get("scope_summary") or {}
    return toks(e.get("title") or "",e.get("client_name") or "",*(x for k in ("objectives","in_scope","exclusions","deliverables") for x in strs(s.get(k))))
def _pending(i): return i.get("review_status")!=CLEARED
def _resolve(text,items):
    """(indices of digest items the text names exactly, the text with those references blanked). Every ID and full title
    of every item is tried, longest first and pending before cleared on a tie, so a longer cleared title is never
    re-read as a shorter pending one and a shared title counts as pending (#2.5)."""
    tg=sorted(((len(_compact(_fw_text(v))),0 if _pending(i) else 1,n,rx) for n,i in enumerate(items) for v in (i.get("knowledge_id"),i.get("title")) for rx in [_target_rx(v)] if rx),key=lambda t:(-t[0],t[1],t[2]))
    hit=[]
    for _,_,n,rx in tg:
        if rx.search(text): hit.append(n); text=rx.sub(lambda m:" "*len(m.group()),text)
    return sorted(set(hit)),text
def _fuzzy(i,T,own,Tall=frozenset()):
    """True when the unresolved words T name pending item i by its title's distinctive words: two of them, or one with a
    second title word anywhere in the item (Tall), so "the onboarding guide and checklist" still names the checklist."""
    W=toks(unwithheld(i.get("title")) or "") if isinstance(i.get("title"),str) else set(); D=W-own
    return len(D&T)>=2 or (bool(D&T) and len(W&(T|Tall))>=2)
def _sibling(i,T,cw,Tall):
    """True when the unresolved words T hold a title word of pending item i that the named cleared titles (words cw)
    lack, and the item shares a second word with i's title."""
    W=toks(unwithheld(i.get("title")) or "") if isinstance(i.get("title"),str) else set()
    return bool((W-cw)&T) and len(W&Tall)>=2
def _tail_ok(tail):
    """True when the words after an administrative object are plain prepositional phrases: no further clause, no
    gerund or verb after a preposition ("before reading ...", "to read ...")."""
    w=tail.split()
    for k,x in enumerate(w):
        if x in {"that","so","when","until","once","while","if","because","since","unless","then","also","plus","but","or","not","don't","dont","never"}: return False
        if x in _FW_PREP and k+1<len(w):
            y=w[k+1]
            if y.endswith("ing") and y not in _FW_ING_NOUN: return False
            if x=="to" and not re.fullmatch(r"(?:the|a|an|this|that|these|those|its|their|our|your|his|her|my|each|every|all|any|km|knowledge|practice)",y): return False
    return True
def _admin_clause(rest):
    """True when the words after an administrative verb are an object that is the review, its status, sign-off or
    approval, or the practice lead, followed only by plain prepositional phrases."""
    w=rest.split(); k=0; obj=[]
    while k<len(w) and w[k] not in _FW_PREP: obj.append(w[k]); k+=1
    if not obj and k<len(w) and w[k] in {"with","to","for","about","on"}:  # "confirm with the practice lead", "ask about the review"
        k+=1
        while k<len(w) and w[k] not in _FW_PREP: obj.append(w[k]); k+=1
    if not _FW_REVIEW_OBJ.search(" ".join(obj)): return False
    if k<len(w) and w[k]=="to":  # "ask the KM lead to confirm the review status ..."
        m=_FW_ADMIN_V.match(" ".join(w[k+1:]))
        if m: return _admin_clause(" ".join(w[k+1:])[m.end():])
    return _tail_ok(" ".join(w[k:]))
def _admin(text):
    """True when first-week text is clearly administrative about the practice review itself and says nothing else about
    the content: each clause is an administrative action on the review (or the practice lead), or continues a noun
    phrase of the previous one ("... with the practice lead and the knowledge management lead"). When in doubt, False."""
    cl=[c.strip(" -:()") for c in re.split(r"\s*(?:[;.!?]+|,|(?<![a-z0-9])(?:and then|then|and|also|plus)(?![a-z0-9]))\s*",text)]
    cl=[c for c in cl if c]
    if not cl: return False
    for n,c in enumerate(cl):
        m=_FW_ADMIN_V.match(c)
        if m:
            if not _admin_clause(c[m.end():]): return False
        elif n==0 or not (_FW_CONT.match(c) and _tail_ok(c)): return False
    return True
def pending_refs(x,items,own):
    """(pending items first-week item x points at, cleared items it names exactly) or None when x is rendered as written
    (#2.5). Any reference to knowledge content while the digest holds a pending item counts, whatever the verb; only a
    clearly administrative item about the review is exempt. A generic reference names every pending digest item; when
    uncertain, x is qualified."""
    if not isinstance(x,str) or is_withheld(x): return None
    items=[i for i in items if isinstance(i,dict)]; text=_fw_text(x)
    if _admin(text): return None  # an action about the review itself, saying nothing else about the content (#2.5)
    hit,rest=_resolve(text,items)
    named=[items[n] for n in hit if _pending(items[n])]; cleared=[items[n] for n in hit if not _pending(items[n])]
    T=toks(rest); Ta=toks(text)
    cw=set().union(*(toks(unwithheld(c.get("title")) or "") for c in cleared if isinstance(c.get("title"),str)))
    # Beside a cleared item it names, a pending title word the cleared title lacks ("... onboarding guide and checklist")
    # still names the pending sibling (#2.5).
    kctx=bool(_FW_KCTX.search(text)); cloc=bool(_FW_CLIENT.search(text))
    def fz(i):
        D=toks(unwithheld(i.get("title")) or "")-own if isinstance(i.get("title"),str) else set()
        return _fuzzy(i,T,own,Ta) and (kctx or (not cloc and bool(D) and D<=T))
    named+=[i for i in items if _pending(i) and i not in named and (fz(i) or (cleared and _sibling(i,T,cw,Ta)))]
    if named: return named,cleared
    if cleared: return None  # names a cleared item (and no pending one): a location word ("from the digest") is not a reference
    if not _FW_GENERIC.search(rest): return None
    pend=[i for i in items if _pending(i)]
    if pend: return pend,[i for i in items if not _pending(i)]
    return None  # nothing pending in the digest: stale "pending review" wording alone never restricts an item
def _hit(t,c,v):
    """True when the normalised text t (compact form c) spells ID or title v exactly; a split long target is also read
    with every separator removed."""
    rx=_target_rx(v); k=_compact(_fw_text(v))
    return bool(rx and rx.search(t)) or (len(k)>=6 and k in c)
def _crosses(rx,parts,sep):
    """True when a match of rx in the parts joined by sep spans a boundary between two parts."""
    b=[]; o=0
    for p in parts[:-1]: o+=len(p); b.append(o); o+=len(sep)
    return any(m.start()<x<m.end() for x in b for m in rx.finditer(sep.join(parts)))
def split_refs(xs,items,own=frozenset()):
    """[(entry indices, pending items, cleared items)] for runs of 2 to RUN_MAX adjacent first-week entries (blank,
    filler and withheld entries are skipped and never break a run) whose join spells a pending ID or title, or a
    knowledge-content phrase, that no single entry of the run spells; the cleared items the joined run names exactly
    are kept. A run whose joined text is clearly administrative about the review is not a reference, and a run
    containing a smaller flagged run is not read again (#2.5, #4.5 run reading)."""
    items=[i for i in items if isinstance(i,dict)]; pend=[i for i in items if _pending(i)]
    if not pend: return []
    seq=[k for k,x in enumerate(xs) if isinstance(x,str) and not is_withheld(x) and not filler(x)]
    T={k:_fw_text(xs[k]) for k in seq}; C={k:_compact(T[k]) for k in seq}; out=[]; done=[]
    for size in range(2,min(RUN_MAX,len(seq))+1):
        for a in range(len(seq)-size+1):
            span=seq[a:a+size]; ss=set(span)
            if any(d<=ss for d in done): continue
            t=" ".join(T[k] for k in span); c="".join(C[k] for k in span)
            named=[i for i in pend if any(_hit(t,c,v) and not any(_hit(T[k],C[k],v) for k in span) for v in (i.get("knowledge_id"),i.get("title")))]
            parts=[T[k] for k in span]; gen=_crosses(_FW_GENERIC,parts," ") or _crosses(_FW_GENERIC,parts,"")
            if (named or gen) and not _admin(t):
                hit,_=_resolve(t,items); cc=_compact(t)
                cl=[i for n,i in enumerate(items) if not _pending(i) and (n in hit or any(_hit(t,cc,v) for v in (i.get("knowledge_id"),i.get("title"))))]
                out.append((span,named or pend,cl)); done.append(ss)
    return out
def _label(xs): return ", ".join(f"{i.get('title')} ({i.get('knowledge_id')})" for i in xs)
def _items_label(ns): return f"item {ns[0]}" if len(ns)==1 else "items "+", ".join(map(str,ns[:-1]))+f" and {ns[-1]}"
def _restate(n,pend,cleared,ns):
    """The restated line for SOW first-week item(s) ns, rendered at number n: cleared items named in the item may be
    read; each pending item is named by title and ID as title-and-citation only. It never repeats the SOW wording, so
    it never says both "read" and "do not read" for the same item (#2.3, #2.5)."""
    cite=f"(SOW first-week {_items_label(ns)}; knowledge-reuse-rules.md #2.3,#2.5)"; one=len(pend)==1
    src=_src(*(v for i in cleared+pend for v in (i.get("title"),i.get("knowledge_id"))))
    note=f"note only the title{'' if one else 's'} and citation{'' if one else 's'} of {_label(pend)}"+(" in the prior-knowledge digest" if not cleared else "")+f"; {'its' if one else 'their'} content is pending practice review - do not read or reuse {'it' if one else 'them'} until review confirms."
    if cleared: return (f"{n}. In the prior-knowledge digest, read only the cleared item{'' if len(cleared)==1 else 's'} {_label(cleared)}; {note} {cite}",src)
    return (f"{n}. {note[0].upper()}{note[1:]} {cite}",src)
def first_week_row(n,x,items,own):
    """(line, rendered values) for SOW first-week item n read alone (#2.5)."""
    r=pending_refs(x,items,own)
    return (f"{n}. {x}",_src(x)) if r is None else _restate(n,r[0],r[1],[n])
def first_week_rows(xs,items,own):
    """[(line, rendered values)] for the SOW first-week items, numbered as the SOW lists them. Items pointing at pending
    knowledge, alone or as part of an adjacent run, are restated; every other item is unchanged (#2.5)."""
    xs=list(xs); items=[i for i in items if isinstance(i,dict)]; refs={k:pending_refs(x,items,own) for k,x in enumerate(xs)}
    grp={}; runs=split_refs(xs,items,own)
    for span,_,_ in runs:
        g=set(span).union(*(grp[k] for k in span if k in grp))
        for k in g: grp[k]=g
    R=[]
    for k,x in enumerate(xs):
        n=k+1
        if k in grp:
            g=sorted(grp[k]); ns=[j+1 for j in g]
            if k!=g[0]: R.append((f"{n}. Continues SOW first-week item {g[0]+1}, restated in item {g[0]+1} above as a title-and-citation-only note. (SOW first-week item {n}; knowledge-reuse-rules.md #2.5)",())); continue
            # Every pending and cleared item that any entry of the run names, alone or as part of the run, is kept (#2.5).
            pend=[]; cl=[]
            for j in g:
                for i in (refs[j] or ([],[]))[0]+[i for s_,p_,_ in runs if j in s_ for i in p_]:
                    if i not in pend: pend.append(i)
                for i in (refs[j] or ([],[]))[1]+[i for s_,_,c_ in runs if j in s_ for i in c_]+[items[m] for m in _resolve(_fw_text(xs[j]),items)[0] if not _pending(items[m])]:
                    if i not in cl: cl.append(i)
            R.append(_restate(n,pend,cl,ns)); continue
        r=refs[k]
        R.append(first_week_row(n,x,items,own) if r is not None else (f"{n}. {x}",_src(x)))
    return R
def pack_rows(p):
    """[(line, the free-text values it renders)] for the pack, one entry per line, before line screening (#4.3, #4.5)."""
    e=p.get("engagement") or {}; s=p.get("scope_summary") or {}; j=p.get("joiner") or {}; kd=p.get("knowledge_digest") or {}; mp=p.get("mobilization_pack") or {}
    hc=len(p.get("holds",[])); pend=sum(i.get("status")=="hold_pending_wall_review" for i in p.get("access_checklist",[]))
    parts=([f"{hc} open hold(s)"] if hc else [])+([f"{pend} workspace(s) pending wall review"] if pend else [])+(["wall status on hold"] if "wall_status_hold" in mp.get("hold_reasons",[]) and not hc else [])
    E=lambda *xs:[(x,()) for x in xs]
    R=E("# Engagement Mobilization & Onboarding Pack","","**DRAFT - for internal review only. Do not send to the client or provision access.**","",f"Pack status: {mp.get('status','on_hold_internal_only')}"+(" - "+"; ".join(parts)+"; resolve before sharing with the joiner." if parts else ""),f"Generated at: {p.get('run_metadata',{}).get('generated_at',p.get('provenance',{}).get('generated_at',''))}")
    R+=[(f"Engagement: {e.get('title','')} ({e.get('engagement_id','')})",_src(e.get("title"),e.get("engagement_id"))),(f"Client: {e.get('client_name','')}",_src(e.get("client_name"))),(f"Joiner: {j.get('person','')} - {j.get('role','')}",_src(j.get("person"))+_role_src(j.get("role")))]
    R+=E("","## Client context and objectives")+[(f"- {x}",_src(x)) for x in s.get("objectives",[])]+E("","## SOW scope and exclusions","","### In scope")+[(f"- {x}",_src(x)) for x in s.get("in_scope",[])]+E("","### Exclusions")+[(f"- {x}",_src(x)) for x in s.get("exclusions",[])]+E("","## Deliverables and key dates")
    R+=[(f"- Deliverable: {x}",_src(x)) for x in s.get("deliverables",[])]+[(f"- Key date: {x}",_src(x)) for x in s.get("key_dates",[])]
    R+=E("","## Prior-knowledge digest",f"Status: {kd.get('status','unknown')}")
    R+=[(f"- {i.get('title')} ({i.get('knowledge_id')}) [{i.get('review_status','pending_practice_review')}] - {i.get('summary')} Source: {'; '.join(strs(i.get('citations')))}",_src(i.get("title"),i.get("knowledge_id"),i.get("summary"),*rendered_citations(strs(i.get("citations"))))) for i in kd.get("items",[])] or E("- No knowledge items are cleared for this joiner in this run.")
    R+=E("","## Team roster")+[(f"- {r.get('person')} - {r.get('role')} - {', '.join(strs(r.get('responsibilities')))} - POC: {r.get('point_of_contact')}",_src(r.get("person"),*strs(r.get("responsibilities")),r.get("point_of_contact"))+_role_src(r.get("role"))) for r in p.get("team_roster",[])]+[(f"- Proposed, not assigned: {r.get('candidate_name')} for {r.get('role_title')}",_src(r.get("candidate_name"),r.get("role_title"))) for r in p.get("proposed_staffing",[])]
    R+=E("","## Access-request checklist")+([(f"- {i.get('workspace_name')} ({i.get('workspace_id')}): {i.get('status')} - {i.get('requested_permission','none')} - {i.get('reason')}",_src(i.get("workspace_name") if i.get("workspace_name")!=i.get("workspace_id") else None,i.get("workspace_id"))) for i in p.get("access_checklist",[])] or E("- No access is requested in this run; see Escalations and holds."))
    R+=E("","## Confidentiality and ethical-wall briefing")+([(f"- May not access/discuss {i.get('type')}: {i.get('item')} - {i.get('restriction')}",_src(i.get("item"),i.get("restriction"))) for i in (p.get("wall_decision") or {}).get("may_not_access_discuss",[])] or E("- No wall restriction was found for the joiner, subject to human review of this draft."))
    R+=E("","## First-week plan")+first_week_rows(s.get("first_week_focus",[]),kd.get("items") or [],scope_words(p))+E("","## Escalations and holds")+[(f"- {x}",_src(x)) for x in p.get("escalations",[])]+[(f"- HOLD {h.get('hold_id')}: {h.get('reason')} at {h.get('path')} ({h.get('citation')})",_hold_src(h)) for h in p.get("holds",[])]
    return R
# The only values a pack line renders that pack_rows does not hand to the rendered-order screen (#4.5): each is engine
# vocabulary no input supplies (a contract enum, the --generated-at run timestamp, or engine wording built from closed
# vocabularies), proved equal to the engines' re-derivation (same_document). Matrix roles and engine-template hold
# fields are screened unless they equal the fixed vocabulary (_role_src, _hold_src). tests/run_tests.py
# (qa101y_checks) fails if a pack line renders any other value that is not screened.
PACK_UNSCREENED={
    "mobilization_pack.status":"contract enum (draft_internal_only, on_hold_internal_only)",
    "run_metadata.generated_at":"--generated-at run timestamp, ISO-8601 UTC (stage_timestamp)",
    "provenance.generated_at":"--generated-at run timestamp, ISO-8601 UTC (stage_timestamp)",
    "knowledge_digest.status":"contract enum (ready, empty, hold, denied_by_wall)",
    "knowledge_digest.items[].review_status":"contract enum (knowledge-reuse-rules.md #2.3)",
    "access_checklist[].status":"contract enum (workspace-inventory-rules.md #2)",
    "access_checklist[].requested_permission":"contract enum (role-access-matrix.md #2)",
    "access_checklist[].reason":"engine wording from permission names and fixed column names (role-access-matrix.md #2.3)",
    "wall_decision.may_not_access_discuss[].type":"contract enum (client_or_matter, workspace)"}
def pack_lines(p,held_lines=()):
    """The mobilization pack, one entry per rendered line. Every line after the header is screened alone (#4.3); a
    line in a run the whole-pack screen held that carries no free-text value to withhold is withheld whole (#4.5)."""
    L=[x for x,_ in pack_rows(p)]
    return L[:5]+[(("- " if x.startswith("- ") else "")+WITHHELD) if x in held_lines else x if x.startswith(("#","Status:")) or not x else safe(x) for x in L[5:]]  # hold lines are screened too (#4.3)
def pack(p,held_lines=()): return "\n".join(pack_lines(p,held_lines))+"\n"
# The rendered pack is screened as a whole (#4.5): values from different fields, records and sources are placed on
# adjacent lines ("Client: ..." above "Joiner: ..."), so a claim split across them would compose only in the pack.
# The pack is read in its rendered order as scan_lines reads a source: each line's free-text values (joined as the
# line renders them), every pair of neighbouring lines, every run of 3 to RUN_MAX lines and the whole pack. Lines that
# render only engine text (headings, labels, statuses, reasons, hold lines) or are withheld are skipped and never break
# a run: the engine's fixed vocabulary ("pending wall review", "denied") is not source text and would compose with
# ordinary names ("Cleared Healthcare ..."). A hit holds the run, withholds every free-text value on its lines in the
# whole access checklist and the pack, holds the wall like any screening hold, and the pack is re-derived until it
# reads clean (derive). pack-draft's pre-render check (verify_render.py) refuses a pack that does not.
PACK_PASSES=8
PACK_RUN_PATH="mobilization-pack.md"
def pack_screen(p,entries=None):
    """One screening text per rendered pack entry: the free-text values it renders, in pack order ('' for an entry that
    renders only engine text or is withheld)."""
    rows=pack_rows(p); L=pack_lines(p) if entries is None else entries
    return ["" if not s or WITHHELD in x else rendered_text(s) for (_,s),x in zip(rows,L)]
def pack_runs(texts):
    """[(entry indices, families)] for every pack entry whose values trip together (joined, or side by side on the
    line: line_hits), and every pair or run of entries that trips only when read together (#4.5)."""
    return [([k],h) for k,x in enumerate(texts) if x for h in [line_hits(x)] if h]+rendered_runs(texts)
def pack_run_hold(entries,span,h):
    first=[0]
    for e in entries: first.append(first[-1]+e.count("\n")+1)
    a,b=first[span[0]]+1,first[span[-1]+1]
    return hold(f"{PACK_RUN_PATH} line {a}" if a==b else f"{PACK_RUN_PATH} lines {a}-{b}","\n".join(entries[k] for k in span),h)
def pack_escalation(n): return rendered_escalation("pack",n)
PACK_KEEP=RENDER_KEEP+("mobilization_pack",)
def check_governed(p):
    need(isinstance(p,dict),f"governed input must be a JSON object, got {type(p).__name__}; fail closed")
    if p.get("contract_version")!=CONTRACT_VERSION: raise InputError(f"expected contract {CONTRACT_VERSION} in governed input")
    if not isinstance(p.get("wall_decision"),dict): raise InputError("governed input has no wall_decision object; run wall_check first; fail closed")
    check_contract(p,"governed","governed")  # whole stage schema, closed enums included (confidentiality-and-ethical-wall-rules.md #1.3)
    check_hold_evidence(p,"governed")  # holds are cumulative (#1.4); every other field is proved equal to its re-derivation (same_document)
UNION=("held_workspace_ids","name_withheld_workspace_ids")  # merged canonically with late screening holds' re-derivation (most restrictive wins)
def effective_wall(p,register,inventory,closeout,staffing,new=()):
    """The effective wall decision for a governed document already proved equal to its re-derivation from the raw
    inputs (same_document, #1.4). wall_check's derivation is re-run on the screened document; the holds this engine
    raised itself while screening it (new) are then merged and the decision re-derived once more, so a late screening
    hold gates knowledge and access exactly as an upstream hold would (#1.4, #2.1). Held and name-withheld workspace
    IDs are merged canonically with the carried ones (most restrictive wins)."""
    W=p["wall_decision"]; R=govern(copy.deepcopy(p),register,inventory,closeout,staffing)["wall_decision"]
    for k in UNION: R[k]=canon_union(W.get(k),R[k])
    if new:
        q=copy.deepcopy(p); q["holds"]=dedup_holds(list(q.get("holds",[]))+list(new)); R2=govern(q,register,inventory,closeout,staffing)["wall_decision"]
        for k in UNION: R2[k]=canon_union(R[k],R2[k])
        R=R2
    return R
def main():
    ap=ArgParser()
    for k in ("--governed","--raw-dir","--staffing","--confirmed-roster","--closeout","--wall-register","--workspace-inventory","--out","--pack-out","--generated-at"): ap.add_argument(k,required=True)
    a=ap.parse_args(); ts=require_iso_z(a.generated_at)
    p=load_json(a.governed,"governed input"); check_governed(p)
    g=wall_check.rederive(p,a.raw_dir,a.staffing,a.confirmed_roster,a.closeout,a.wall_register,a.workspace_inventory,stage_timestamp(p,"governed input"),"governed input")
    same_document(p,g,"governed input")  # every field equals the scope_digest + knowledge_match + wall_check re-derivation from the raw inputs (#1.4)
    d,txt=derive(p,a.wall_register,a.workspace_inventory,ts,a.closeout,a.staffing)
    write_atomic([(a.out,json_bytes(a.out,d,"access checklist output"),"access checklist output"),(a.pack_out,text_bytes(a.pack_out,txt,"pack output"),"pack output")])  # both serialised first, then written atomically together
def derive(p,register,inventory,ts,closeout,staffing):
    """(access checklist document, mobilization pack text) for a governed document already proved equal to its
    re-derivation from the raw inputs (#1.4). pack-draft's pre-render check (verify_render.py) re-runs this too."""
    d,entries=derive_entries(p,register,inventory,ts,closeout,staffing); return d,"\n".join(entries)+"\n"
def derive_entries(p,register,inventory,ts,closeout,staffing):
    """(access checklist document, rendered pack entries). The rendered pack is screened whole (pack_runs); each held
    run adds a hold and withholds its text, and the document is derived again until the pack reads clean (#4.5)."""
    ph=[]; blocked=set(); held=set()
    for _ in range(PACK_PASSES):
        d=_derive(copy.deepcopy(p),register,inventory,ts,closeout,staffing,ph,blocked); entries=pack_lines(d,held)
        found=pack_runs(pack_screen(d,entries))
        if not found: return d,entries
        rows=pack_rows(d); grew=False
        for span,h in found:
            x=pack_run_hold(entries,span,h)
            if hold_key(x) not in {hold_key(y) for y in ph}: ph.append(x); grew=True
            for k in span:
                src=[v for v in rows[k][1] if v not in blocked]
                if src: blocked.update(src); grew=True
                elif rows[k][0] not in held: held.add(rows[k][0]); grew=True
        if not grew: break
    raise InputError("the rendered mobilization pack still reads as an instruction across lines after its text was withheld (text not repeated); nothing written; fail closed (confidentiality-and-ethical-wall-rules.md #4.5)")
def _derive(p,register,inventory,ts,closeout,staffing,ph=(),blocked=()):
    """The access checklist document for the governed document p, with the whole-pack holds raised so far (ph) and
    the pack values they withhold (blocked)."""
    adopt_trust(p)  # from the declaration lines scope_digest accepted, never a carried list (#1.4, #4.4)
    # The governed document is untrusted input: its upstream holds and every content field are screened for embedded
    # instructions and for other clients named in the wall register, and flagged text withheld, before anything is
    # derived from it (confidentiality-and-ethical-wall-rules.md #3.3, #4.1, #4.3).
    terms,_=wall_check.knowledge_match.other_client_terms(p,closeout,register,staffing)  # the one identity set every stage uses (#3.3)
    p,gh=screen_upstream(p,"governed",ENGINE,terms); p,oh=screen_other(p,terms,ENGINE,"governed.")
    esc=p.setdefault("escalations",[])
    if gh: esc.append(f"{len(gh)} governed field(s) held for embedded instruction review (confidentiality-and-ethical-wall-rules.md #4.1-#4.5)")
    if oh: esc.append(other_escalation(len(oh)))
    fixed=[]; screened=[]
    def add_hold(hs,hid,path,why,cit): hs.append({"hold_id":hid,"path":path,"reason":why,"source":ENGINE,"confidence":.99,"citation":cit})
    # The workspace inventory is read and every cell screened (instructions and other clients) before anything is
    # gated: screening holds, like the governed document's own, are merged before the decision is re-derived, so they
    # hold the wall, the digest and knowledge-dependent or client-confidential access (#1.4, #2.1, #3.3; checklist B6).
    # Cells are screened from the rows AS READ, before an unusable header or a repeated ID empties the collection the
    # decisions use: an inventory that is not used is still screened and its flagged cells held (#1.3, #3.3, #4.3).
    rows=read_csv(inventory,False,"workspace inventory"); check_csv_ids(rows,"raw/workspace-inventory.csv",("workspace_id",)); check_csv_names(rows,"raw/workspace-inventory.csv",("name",))  # identifier shape (#1.3)
    as_read=[dict(r) for r in rows or []]  # the cells before screening rewrites them: a quarantined row's grammar is read from these (#1.3)
    bad=wall_check.inventory_problem(rows)  # the one missing/malformed check wall_check applies, on the rows as read (#1.2, #1.3)
    if bad: fixed.append(wall_check.inventory_hold(bad,ENGINE))
    if rows is not None:
        screened=scan_rows(rows,"raw/workspace-inventory.csv")+screen_csv_other(rows,"raw/workspace-inventory.csv",terms,ENGINE)
    if bad: rows=[]
    foreign=wall_check.foreign_rows(rows)  # another client's workspace: never requested or listed by its supplied ID or name (#3.3)
    bad_rows=set(getattr(rows,"malformed",()))
    role=low((p.get("joiner") or {}).get("role")); allowed={canon_id(k):v for k,v in next((v for k,v in M.items() if low(k)==role),{}).items()}
    if not allowed: add_hold(fixed,"HOLD-ROLE-NOT-IN-MATRIX","scope.joiner.role","joiner role (not repeated) is not in the role-access matrix; no access is requested","role-access-matrix.md #4.3")
    def row_problems(r,n):
        """The grammar problems of inventory row n, in fixed vocabulary that repeats no cell value (#1.3, #2.3)."""
        wid=(r.get("workspace_id") or "").strip(); req=low(r.get("requested_permission")) or low(r.get("default_permission")); default=low(r.get("default_permission")) or req
        withheld=[c for c in DECISION_COLUMNS if is_withheld(r.get(c))]  # a withheld identifier or enum is never a decision key (#3.3, #4.3)
        return [x for x,bad in (("workspace_id blank",not wid),("withheld field(s): "+", ".join(withheld),bool(withheld)),("row has more fields than the header",n in bad_rows),("no requested or default permission",not req),("unrecognised default_permission",default not in O),("unrecognised data_classification",canon_id(r.get("data_classification")) not in cset(KNOWN_CLASSIFICATIONS)),("unrecognised depends_on_knowledge",low(r.get("depends_on_knowledge")) not in TRUE_VALUES|FALSE_VALUES)) if bad]
    def invalid_hold(ah,n,invalid): add_hold(ah,"HOLD-INVALID-WORKSPACE-ROW",f"raw/workspace-inventory.csv row {n}","invalid workspace inventory row: "+"; ".join(invalid),"workspace-inventory-rules.md #1.3,#2.3")
    def build(wall):
        """The checklist for one effective wall decision; returns (items, the access holds it raises)."""
        denied=cset(wall.get("denied_workspace_ids")); held=cset(wall.get("held_workspace_ids")); hidden=cset(wall.get("name_withheld_workspace_ids")); wstat=wall.get("status"); out=[]; ah=[]
        for n,r in enumerate(rows,2):
            if n in foreign:
                # Another client's row is quarantined (never listed), but only after its grammar is checked, on its
                # cells as read: an invalid row holds by position instead of passing because it is excluded (#1.3, #3.3).
                bad_=row_problems(as_read[n-2],n)
                if bad_: invalid_hold(ah,n,bad_)
                continue
            wid=(r.get("workspace_id") or "").strip(); wt=low(r.get("workspace_type")); req=low(r.get("requested_permission")) or low(r.get("default_permission")); default=low(r.get("default_permission")) or req; dep=depends_on_knowledge(r.get("depends_on_knowledge")); conf=client_confidential(r.get("data_classification")); maxp=allowed.get(canon_id(wt)); status="request"; reason="role matrix allows requested workspace access"; perm=req; cit=f"{r.get('citation') or 'raw/workspace-inventory.csv'}; role-access-matrix.md #2.1; workspace-inventory-rules.md #3.1"
            invalid=row_problems(r,n)
            if join_key(wid) in denied:
                status="denied_by_wall"; reason="workspace denied by wall_check"; perm="none"; cit+="; confidentiality-and-ethical-wall-rules.md #2.3"
                if invalid: invalid_hold(ah,n,invalid)  # denied either way, but an invalid row still holds (#1.3)
            elif invalid:
                status="not_requested_invalid_row"; reason="invalid inventory row ("+"; ".join(invalid)+"); nothing requested"; perm="none"; cit+="; workspace-inventory-rules.md #1.3,#2.3"
                invalid_hold(ah,n,invalid)
            elif join_key(wid) in held or (wstat in {"hold","denied"} and (dep or conf)): status="hold_pending_wall_review"; reason="prior-knowledge dependent access held until wall status is clear" if dep else "client-confidential workspace held pending wall review"; perm="none"; cit+="; workspace-inventory-rules.md #2.1"
            elif not maxp: status="not_requested_role_not_allowed"; reason="role matrix does not allow this workspace type"; perm="none"; cit+="; role-access-matrix.md #1"
            elif req not in O or O[req]>=O["admin"]: status="not_requested_exceeds_role"; reason=f"requested {req} exceeds role ceiling {maxp}; admin rights are never requested" if req in O else f"unrecognised requested permission exceeds role ceiling {maxp}"; perm="none"; cit+="; role-access-matrix.md #2.1,#2.2; workspace-inventory-rules.md #3.2"
            elif O[req]>min(O[default],O[maxp]):
                # Request = min(requested, workspace default, role ceiling); anything wider is clamped and held, never granted (#2.3).
                perm=NAMES[min(O[req],O[default],O[maxp])]; reason=f"requested {req} clamped to {perm} (workspace default {default}, role ceiling {maxp}); held for engagement manager review"; cit+="; role-access-matrix.md #2.3"
                add_hold(ah,"HOLD-PERMISSION-CLAMPED",f"raw/workspace-inventory.csv row {n}.requested_permission",f"requested {req} is wider than min(workspace default {default}, role ceiling {maxp}); request clamped to {perm}","role-access-matrix.md #2.3")
                if perm=="none": status="not_requested_exceeds_role"
            name=r.get("name") if (r.get("name") or "").strip() else wid
            if not (name or "").strip() or join_key(wid) in hidden or hits(name) or is_withheld(name): name=wid or "(blank workspace_id)"  # never rendered blank (#1.3)
            out.append({"workspace_id":wid,"workspace_name":name,"workspace_type":r["workspace_type"] if is_withheld(r.get("workspace_type")) else wt,"status":status,"requested_permission":perm,"reason":reason,"source":ENGINE,"confidence":.96,"citation":cit})
        return out,ah
    # Access-decision holds (role not in the matrix, and below an invalid row or a clamped permission) govern their
    # checklist rows and the pack status, not the wall (role-access-matrix.md #2.3). A missing or malformed inventory
    # holds the wall too: wall_check raised the same hold, carried in the governed document (workspace-inventory-rules.md #1.2, #1.3).
    wall=effective_wall(p,register,inventory,closeout,staffing,gh+oh+screened+list(ph)); out,ah=build(wall)
    p["wall_decision"]=wall; wstat=wall.get("status"); need(wstat in WALL_STATUSES,"re-derived wall status is not recognised; fail closed")
    if wstat in {"hold","denied"}:
        # No knowledge is released while the effective wall status is hold or denied, whatever the digest says (#2.2, #2.3).
        kd=p.get("knowledge_digest") or {}
        if kd.get("status") not in {"hold","denied_by_wall"}: kd["status"]="denied_by_wall" if wstat=="denied" else "hold"
        kd["items"]=[]; p["knowledge_digest"]=kd; wall["allowed_knowledge_ids"]=[]
    holds=list(p.get("holds",[]))+gh+oh+screened+fixed+ah+list(ph)
    if ph: esc.append(pack_escalation(len(ph)))
    holds=dedup_holds(holds); pend=sum(i["status"]=="hold_pending_wall_review" for i in out)
    reasons=(["open_holds"] if holds else [])+(["wall_status_hold"] if wstat=="hold" else [])+(["workspaces_pending_wall_review"] if pend else [])  # workspace-inventory-rules.md #3.3
    if pend: esc.append(f"{pend} workspace(s) held pending wall review; the pack stays on hold until Risk/Conflicts resolve the wall decision (workspace-inventory-rules.md #3.3)")
    p["access_checklist"]=out; p["holds"]=holds; p["mobilization_pack"]={"status":"on_hold_internal_only" if reasons else "draft_internal_only","hold_reasons":reasons,"label":"DRAFT - for internal review only. Do not send to the client or provision access.","sections":["client_context","scope","prior_knowledge","team_roster","access_checklist","wall_briefing","first_week_plan"],"source":ENGINE,"confidence":.94,"citation":"workspace-inventory-rules.md #3.1,#3.3; confidentiality-and-ethical-wall-rules.md #3.1"}; p.setdefault("provenance",{}).setdefault("engines",[]).append(f"access_checklist/{VERSION}"); p["provenance"]["generated_at"]=ts
    p=withhold_values(p,blocked,PACK_KEEP)  # text on a held pack run is withheld everywhere it appears (#4.5)
    p=bind_withheld(settle_trust(p),"access",ENGINE); check_contract(p,"access","access")  # the document written is held to the contract (#1.3)
    return p
if __name__=="__main__": guard(main)
