#!/usr/bin/env python3
import argparse, copy, os, re
from safety_text import *
ENGINE="engine:scope_digest"; STAFF="ps.engagement-staffing-bench-match.v1"  # role-access-matrix.md #3.1
SOW_CONTROLS_CONFLICTS=True  # confidentiality-and-ethical-wall-rules.md #1.2
CONFIRMED_ROSTER_CONTROLS=True  # role-access-matrix.md #4.1
INELIGIBLE_STAFFING_EXCLUDED=True  # role-access-matrix.md #3.2
VERDICTS={"eligible","ineligible","conflicted","blocked","needs_review"}  # role-access-matrix.md #3.2-#3.4
INELIGIBLE={"ineligible","conflicted","blocked"}  # role-access-matrix.md #3.2
RANK={"eligible":0,"needs_review":2,"unrecognised":2.5,"ineligible":3,"conflicted":3,"blocked":3}
ONBOARDING={"active","joining","mid-engagement joiner","new_joiner"}; JOINING={"joining","mid-engagement joiner","new_joiner"}  # role-access-matrix.md #4.2,#4.4
ROSTER_COLUMNS=("person","role","onboarding_status","assignment_status")
def fld(t,n):
    # One labelled line in any variant form (label_parts: indentation, quote, heading, bullet or numbered marker, bold
    # or backtick key, key case and spacing): [ \t] and [^\r\n], never \s, so a blank "Client:" reads blank instead of
    # consuming the next line (#1.2).
    k=label_key(n); return next((p[1] for p in map(label_parts,(t or "").splitlines()) if p and p[0]==k),"")
# The declared labelled fields (safety_text SOW_FIELDS, LETTER_FIELDS, PURSUIT_FIELDS) and the one source file that owns each (#1.2, #4.4).
FIELD_OWNERS=(("raw/sow-extract.md",SOW_FIELDS+DOMAIN_LABELS),("raw/engagement-letter-extract.md",LETTER_FIELDS+DOMAIN_LABELS),("raw/pursuit-record.md",PURSUIT_FIELDS))
DECLARED={label_key(x) for _,fs in FIELD_OWNERS for x in fs}
def _content(line):
    """True when a line below a declared label is section content, not another field: an unlabelled line, a table
    separator, or a bullet, numbered, task-box, quoted, indented or table item whose key (if any) is not declared."""
    p=label_parts(line)
    return p is None or table_separator(line) or (p[0] not in DECLARED and bool(re.match(r"[ \t>|]|[-*+\u2022]|\d{1,3}[.)]",line)))
def field_lines(text,where):
    """{canonical label: 1-based line} for the declared fields in one source file, read in any variant form. A declared
    field that another file owns, a field repeated in the file, a declared label with no value on its own line (a
    heading such as "## Exclusions", "## 1. Exclusions:", a setext heading, a bare "**Systems**", a table header row, or
    "Exclusions:" with its items on the lines below) is refused, never ignored, read blank or resolved first-wins;
    errors name the file and line, never the text (#1.2)."""
    own={label_key(x) for w,fs in FIELD_OWNERS if w==where for x in fs}; out={}; ls=(text or "").splitlines()
    for n,l in enumerate(ls,1):
        p=label_parts(l); k=p[0] if p else bare_label(l)
        if k not in DECLARED: continue
        nxt=next((x for x in ls[n:] if x.strip()),None)
        section=p is None or (not p[1] and (is_heading(l) or (nxt is not None and _content(nxt)))) or (table_cells(l) is not None and nxt is not None and table_separator(nxt))
        need(not section,f"{where} line {n} is a declared field label with no ':' value on its line (a heading, table header or section label is not a field; text not repeated); write each field as one 'Label: value' line; nothing written; fail closed (confidentiality-and-ethical-wall-rules.md #1.2)")
        need(k in own,f"{where} line {n} declares a field that another source file owns (text not repeated); each declared field is read only from its own file; nothing written; fail closed (confidentiality-and-ethical-wall-rules.md #1.2)")
        need(k not in out,f"{where} line {n} repeats a declared field first given on line {out.get(k)} (text not repeated); each field appears once; nothing written; fail closed (confidentiality-and-ethical-wall-rules.md #1.2)")
        out[k]=n
    return out
def field_value(raw,scanned,lines,n):
    """Declared field n of a source file: its value on the scanned line, or the placeholder when scanning withheld the
    line, whatever its variant form (#1.2, #4.3)."""
    i=lines.get(label_key(n))
    if i is None: return ""
    rl,sl=raw.splitlines()[i-1],scanned.splitlines()[i-1]
    return label_parts(rl)[1] if sl==rl else WITHHELD
def lst(v): return split_items(v)
# A demo label only: a short slug, never free text, because it is copied into run_metadata (#1.3).
SCENARIO_RE=re.compile(r"(?:|[A-Za-z0-9][A-Za-z0-9._-]{0,63})")
def declarations(docs):
    """([(doc index, line index, [well-formed trustable domains])] for the first line of each domain label in each
    document whose value does not trip the wire on its own, the count of malformed or untrustable domains)."""
    out=[]; bad=0
    for di,doc in enumerate(docs):
        ls=doc.splitlines()
        for lab in DOMAIN_LABELS:
            i=next((n for n,l in enumerate(ls) if (label_parts(l) or ("",))[0]==label_key(lab)),None)
            if i is None: continue
            line=declaration_value(ls[i])
            if not line or hits(line): continue
            ds,b=declared_domains(line); bad+=b  # one parser for scope_digest and every later stage's re-derivation (#4.4)
            out.append((di,i,ds))
    return out,bad
def one(v): return WITHHELD if hits(v) else v
def items(line):
    # Flagged SOW/letter text never travels (#4.3): withhold each flagged item and its clean split partners (#4.5);
    # if the line only trips the wire as a whole, withhold every item from it.
    xs=lst(line)
    if not hits(line): return xs
    sp=split_indices(xs); out=[WITHHELD if hits(x) or n in sp else x for n,x in enumerate(xs)]
    return out if WITHHELD in out else [WITHHELD]
def unique_records(recs,key,where,f=canon_id):
    """Records keyed by `key` (canonical, #1.3) appear once: a repeat is refused before any screening or linking, never
    resolved last-wins or rendered twice. `recs` is [(path, record)]; blank keys are not keys (join_key)."""
    seen={}
    for w,c in recs:
        k=join_key(c.get(key),f) if isinstance(c,dict) else None
        if k is None: continue
        if k in seen: raise InputError(f"{w}.{key} repeats {seen[k]}.{key} (value not repeated); each record keyed by {key} appears once (confidentiality-and-ethical-wall-rules.md #1.3); fail closed")
        seen[k]=w
def validate_staffing(st):
    need(isinstance(st,dict),f"staffing adapter expected a JSON object, got {type(st).__name__}; fail closed")
    if st.get("contract_version")!=STAFF: raise InputError(f"staffing adapter expected contract {STAFF} at upstream/staffing.contract_version (supplied value not repeated); fail closed")
    W="upstream/staffing"; check_timestamps(st,W)  # carried timestamps are format-checked (confidentiality-and-ethical-wall-rules.md #1.3)
    check_ids(st,W)  # every identifier member (engagement_id, role_id, candidate_id ...) has the identifier shape (#1.3)
    check_names(st,W)  # no name member (candidate, client, role, affiliate) is in an engine label form (#1.3)
    field(st,"governed_roles","objlist",W,required=True)
    eng=field(st,"engagement","obj",W,default={})
    for k in ("engagement_id","client_name"): field(eng,k,"str",W+".engagement",nullable=True)
    field(eng,"affiliates","strlist",W+".engagement",nullable=True)
    for e in field(st,"escalations","list",W,default=[]): esc_text(e,W+".escalations")
    # Every section and nested record any reader uses (statuses, staffing_links) is type-checked before screening or
    # linking: a malformed section is a clean InputError, never silently skipped (#1.3, #1.5).
    bench=field(st,"bench_candidates","objlist",W,nullable=True,default=[]) or []
    for i,c in enumerate(bench):
        cw=f"{W}.bench_candidates[{i}]"; field(c,"candidate_id","str",cw,nullable=True); field(c,"name","str",cw,nullable=True)
    # Every keyed staffing collection is checked for canonical duplicates before linking (#1.3): the bench by
    # candidate_id and name, each role's slate or scores by candidate_id and name, roles by role_id, and the
    # recommendations by candidate_id and name across every governed role (one person is proposed once).
    unique_records([(f"{W}.bench_candidates[{i}]",c) for i,c in enumerate(bench)],"candidate_id",W)
    unique_records([(f"{W}.bench_candidates[{i}]",c) for i,c in enumerate(bench)],"name",W,canon_person)
    for sec,key,nk in (("scored_roles","candidate_scores","candidate_name"),("ranked_roles","candidate_slate","candidate_name")):
        rs=field(st,sec,"objlist",W,nullable=True,default=[]) or []
        for i,r in enumerate(rs):
            w=f"{W}.{sec}[{i}]"; field(r,"role_title","str",w,nullable=True); field(r,"role_id","str",w,nullable=True)
            cs=field(r,key,"objlist",w,nullable=True,default=[]) or []
            for j,c in enumerate(cs):
                cw=f"{w}.{key}[{j}]"; field(c,"candidate_id","str",cw,nullable=True); field(c,nk,"str",cw,nullable=True)
            unique_records([(f"{w}.{key}[{j}]",c) for j,c in enumerate(cs)],"candidate_id",w)
            unique_records([(f"{w}.{key}[{j}]",c) for j,c in enumerate(cs)],nk,w,canon_person)
        unique_records([(f"{W}.{sec}[{i}]",r) for i,r in enumerate(rs)],"role_id",W)
    recs=[]
    for i,r in enumerate(st["governed_roles"]):
        w=f"{W}.governed_roles[{i}]"; field(r,"role_title","str",w,nullable=True); field(r,"role_id","str",w,nullable=True)
        for key in ("candidate_slate","recommended_candidates"):
            cs=field(r,key,"objlist",w,default=[])
            if key=="candidate_slate":
                unique_records([(f"{w}.{key}[{j}]",c) for j,c in enumerate(cs)],"candidate_id",w)
                unique_records([(f"{w}.{key}[{j}]",c) for j,c in enumerate(cs)],"candidate_name",w,canon_person)
            else: recs+=[(f"{w}.{key}[{j}]",c) for j,c in enumerate(cs)]
            for j,c in enumerate(cs):
                cw=f"{w}.{key}[{j}]"; field(c,"candidate_id","str",cw,nullable=True); field(c,"candidate_name","str",cw,nullable=True); field(c,"confidence","num01",cw); field(c,"fit_score","num",cw,nullable=True); field(c,"citation","str",cw,nullable=True)
                el=field(c,"eligibility","obj",cw,nullable=True)
                if el:
                    for k in ("verdict","recommendation_status","blocking_rule","citation"): field(el,k,"str",cw+".eligibility",nullable=True)
    unique_records([(f"{W}.governed_roles[{i}]",r) for i,r in enumerate(st["governed_roles"])],"role_id",W)
    unique_records(recs,"candidate_id",W); unique_records(recs,"candidate_name",W,canon_person)
def staffing_links(st):
    """Staffing records name a candidate by candidate_id in several places (bench, scored, ranked and governed slates,
    recommendations). A candidate_id whose records state different people (canonical names, #1.3) links one person's
    verdict or recommendation to another: every record with that ID is held and not used (#1.5).
    Returns (conflicted canonical IDs, holds)."""
    seen={}; first={}
    def add(path,c,nk):
        if not isinstance(c,dict) or not stated(c.get("candidate_id")) or not stated(c.get(nk)): return  # withheld text is already held (#4.3)
        k=join_key(c["candidate_id"])
        if k is None: return  # a blank key links nothing (#1.3)
        seen.setdefault(k,set()).add(canon_person(c[nk])); first.setdefault(k,[]).append(path)
    W="upstream/staffing"
    for i,c in enumerate(st.get("bench_candidates") or []): add(f"{W}.bench_candidates[{i}].name",c,"name")
    for sec,key in (("scored_roles","candidate_scores"),("ranked_roles","candidate_slate"),("governed_roles","candidate_slate"),("governed_roles","recommended_candidates")):
        for i,r in enumerate(st.get(sec) or []):
            if isinstance(r,dict) and isinstance(r.get(key),list):
                for j,c in enumerate(r[key]): add(f"{W}.{sec}[{i}].{key}[{j}].candidate_name",c,"candidate_name")
    bad={k for k,v in seen.items() if len(v)>1}
    return bad,[link_hold(first[k][1],ENGINE) for k in sorted(bad)]
def slate_verdict(c,bad):
    el=c.get("eligibility") or {}; v=el.get("verdict")
    v=canon_text(v) if isinstance(v,str) else None
    if v not in VERDICTS: v="unrecognised"  # blank, null or unknown verdicts fail closed (#3.4)
    if join_key(c.get("candidate_id")) in bad: v="unrecognised"  # a candidate_id naming two people is not evidence (#1.5)
    return v
def invalid_verdicts(st,bad=frozenset()):
    """[(path, canonical person or None)] for every governed slate or recommendation record whose stated eligibility
    verdict is not one of VERDICTS. The verdict grammar is validated whether or not the record is later used: a record
    for someone not on the roster, unconfirmed or excluded is not skipped unchecked (role-access-matrix.md #3.4).
    A blank or withheld verdict, or a record whose candidate_id names two people (held as a link mismatch), is left
    to the existing rules."""
    out=[]
    for i,r in enumerate(st.get("governed_roles") or []):
        for key in ("candidate_slate","recommended_candidates"):
            for j,c in enumerate(r.get(key) or []):
                v=(c.get("eligibility") or {}).get("verdict"); nm=c.get("candidate_name")
                if not isinstance(v,str) or not v.strip() or is_withheld(v) or canon_text(v) in VERDICTS or join_key(c.get("candidate_id")) in bad: continue
                out.append((f"upstream/staffing.governed_roles[{i}].{key}[{j}].eligibility.verdict",join_key(nm,canon_person)))
    return out
def statuses(st,bad=frozenset()):
    """(verdicts by canonical person, proposed staffing, paths of recommendations not proposed). A recommendation is
    proposed only when the slate holds a record for the same candidate (canonical candidate_id AND name, #1.3; both
    sides must state the ID - a blank or missing key never matches anything, including another blank key) and the
    most restrictive verdict across those records and any other slate record for the same person is eligible.
    Blocked, conflicted, ineligible, needs-review, unrecognised and unmatched recommendations are never proposed and
    are held (role-access-matrix.md #3.2-#3.4; confidentiality-and-ethical-wall-rules.md #1.5)."""
    s={}; p=[]; slate=[]; notp=[]
    for r in st["governed_roles"]:
        rt=r.get("role_title") if (r.get("role_title") or "").strip() else "role"
        for c in r.get("candidate_slate",[]):
            if not (c.get("candidate_name") or "").strip(): continue
            v=slate_verdict(c,bad)
            if is_withheld(c["candidate_name"]): continue  # a withheld name joins no roster row (confidentiality-and-ethical-wall-rules.md #4.3)
            slate.append((join_key(c.get("candidate_id")),canon_person(c["candidate_name"]),v))
            s.setdefault(canon_person(c["candidate_name"]),[]).append({"role_title":rt,"verdict":v,"blocking_rule":(c.get("eligibility") or {}).get("blocking_rule"),"confidence":c.get("confidence",.9),"citation":(c.get("eligibility") or {}).get("citation") or c.get("citation") or "staffing"})
    for i,r in enumerate(st["governed_roles"]):
        rt=r.get("role_title") if (r.get("role_title") or "").strip() else "role"
        for j,c in enumerate(r.get("recommended_candidates",[])):
            if join_key(c.get("candidate_id")) in bad: continue  # never propose through an ID that names another person; held as a link mismatch (#1.5)
            nm=c.get("candidate_name")
            if not (nm or "").strip() or is_withheld(nm) or is_withheld(c.get("candidate_id")): continue  # blank names nobody; withheld text is already held (#4.3)
            rk=join_key(c.get("candidate_id"))  # None never equals a slate key: blank IDs match nothing (#1.3)
            same=[v for k,n,v in slate if rk is not None and k==rk and n==canon_person(nm)]
            v=max(same+[v for k,n,v in slate if n==canon_person(nm)],key=lambda x:RANK.get(x,2.5)) if same else None
            if v!="eligible": notp.append(f"upstream/staffing.governed_roles[{i}].recommended_candidates[{j}]"); continue
            p.append({"candidate_name":nm,"role_title":rt,"fit_score":c.get("fit_score"),"assignment_status":"proposed_not_assigned","source":"adapter:staffing-slate","confidence":c.get("confidence",.9),"citation":c.get("citation") or "staffing recommended_candidates"})
    return s,p,notp
def verdict_for(entries,role):
    # Prefer the Scenario 02 verdict for the confirmed role; otherwise the most restrictive verdict across roles.
    same=[x for x in entries if canon_text(x.get("role_title"))==canon_text(role)] or entries
    return max(same,key=lambda x:RANK.get(x.get("verdict"),2.5),default={})
def scope_rows(b):
    """[(field path, values)] in the order the roster and the pack render scope.json: every value a rendered line
    shows - IDs, citations, rules and locations included - is read with its line (#4.5)."""
    e=b.get("engagement") or {}; j=b.get("joiner") or {}; s=b.get("scope_summary") or {}; V=rendered_values; C=rendered_citations
    def L(v): return v if isinstance(v,list) else []
    def D(v): return v if isinstance(v,dict) else {}
    def rv(r): return (D(r.get("staffing_review")).get("blocking_rule"),*C(D(r.get("staffing_review")).get("citation")))
    R=[("engagement.title",V(e.get("title"),e.get("engagement_id"))),("engagement.client_name",V(e.get("client_name"))),("joiner",V(j.get("person"),j.get("role")))]
    for k in ("objectives","in_scope","exclusions","deliverables","key_dates"): R+=[(f"scope_summary.{k}[{i}]",V(x)) for i,x in enumerate(L(s.get(k)))]
    R+=[(f"team_roster[{i}]",V(r.get("person"),r.get("role"),*L(r.get("responsibilities")),r.get("point_of_contact"),*C(r.get("citation")),*rv(r))) for i,r in enumerate(L(b.get("team_roster"))) if isinstance(r,dict)]
    R+=[(f"proposed_staffing[{i}]",V(r.get("candidate_name"),r.get("role_title"),*C(r.get("citation")))) for i,r in enumerate(L(b.get("proposed_staffing"))) if isinstance(r,dict)]
    R+=[(f"staffing_exclusions[{i}]",V(r.get("person"),r.get("role"),r.get("blocking_rule"),*C(r.get("citation")))) for i,r in enumerate(L(b.get("staffing_exclusions"))) if isinstance(r,dict)]
    R+=[(f"scope_summary.first_week_focus[{i}]",V(x)) for i,x in enumerate(L(s.get("first_week_focus")))]
    R+=[(f"escalations[{i}]",V(x)) for i,x in enumerate(L(b.get("escalations")))]
    return R+[(f"holds[{i}]",V(*(h.get(k) for k in ("hold_id","reason","path","citation") if not engine_text(k,h.get(k))))) for i,h in enumerate(L(b.get("holds"))) if isinstance(h,dict)]
# The scope.json string members scope_rows does not screen, and why (#4.5): none is on a line the pack or the
# roster presentation renders, or it is engine vocabulary no input supplies. A "*" entry covers a whole object.
# tests/run_tests.py (qa101y_checks) fails if scope.json gains a string member that is neither screened nor listed.
SCOPE_UNSCREENED={
    "contract_version":"engine constant","run_metadata.*":"demo label (SCENARIO_RE slug) and run timestamp; not rendered","provenance.*":"engine and source labels; not rendered",
    "engagement.matter_id":"identifier shape (#1.3); not rendered","engagement.affiliates[]":"not rendered","engagement.sector":"not rendered","engagement.region":"not rendered",
    "engagement.source":"engine label","engagement.citation":"engine citation","engagement.trusted_domains[]":"not rendered","engagement.domain_declarations*":"not rendered",
    "engagement_terms.*":"not rendered (briefing text comes from the wall register)","scope_summary.systems[]":"not rendered","scope_summary.source":"engine label","scope_summary.citation":"engine citation",
    "joiner.*":"the joiner is a copy of a confirmed team_roster row, screened there; the joiner line renders person and role only",
    "team_roster[].onboarding_status":"not rendered (the presented status is derived)","team_roster[].assignment_status":"contract const confirmed","team_roster[].source":"engine label",
    "team_roster[].staffing_review.verdict":"contract enum (role-access-matrix.md #3.3)",
    "proposed_staffing[].assignment_status":"engine label","proposed_staffing[].source":"engine label",
    "staffing_exclusions[].reason":"not rendered: only the verdict and rule citation are presented (role-access-matrix.md #3.2)","staffing_exclusions[].source":"engine label",
    "holds[].source":"engine label"}
def derive(raw_dir,staffing,confirmed_roster,scenario,ts):
    """scope.json for the raw inputs (SOW, engagement letter, pursuit record and wall register in raw_dir; the staffing
    input; the confirmed roster), the demo label and the run timestamp. Every later stage re-runs this derivation on the
    raw inputs and requires the carried scope to equal it in every field (confidentiality-and-ethical-wall-rules.md #1.4)."""
    sowp=os.path.join(raw_dir,"sow-extract.md")
    if not os.path.exists(sowp): raise InputError("missing required SOW extract: raw/sow-extract.md")
    sow=read_text(sowp,"SOW extract"); letter=read_text(os.path.join(raw_dir,"engagement-letter-extract.md"),"engagement letter extract"); pursuit=read_text(os.path.join(raw_dir,"pursuit-record.md"),"pursuit record"); rows=read_csv(confirmed_roster,label="confirmed roster"); st=load_json(staffing,"staffing input")  # fixed labels: no message echoes a supplied path (#1.3)
    # Missing is not empty: a zero-byte or blank engagement letter or pursuit record is refused like a missing one, so
    # it never passes as a source with no terms, domains or conflicts (#1.2). A blank SOW holds (HOLD-SOW-IDENTITY-MISSING).
    for t_,lab in ((letter,"engagement letter extract"),(pursuit,"pursuit record")):
        if not t_.strip(): raise InputError(f"the {lab} is empty (a blank required file is not an empty source); fail closed")
    miss=missing_columns(rows,ROSTER_COLUMNS)
    if miss: raise InputError(f"confirmed roster is missing required column(s): {', '.join(miss)}; fail closed")
    if rows.duplicate_columns: raise InputError("confirmed roster "+DUPLICATE_HEADER_REASON+"; fail closed")
    if rows.malformed: raise InputError(f"confirmed roster row(s) {', '.join(map(str,rows.malformed))} have more fields than the header; fail closed")
    dup=duplicate_rows(rows,"person")  # the roster is keyed by person: a repeat is refused, never resolved last-wins (#1.3)
    if dup: raise InputError(f"confirmed roster row(s) {', '.join(map(str,dup))} name the same person (name not repeated); each person appears once; fail closed")
    validate_staffing(st)
    # Declared fields are located on the raw text, in any variant form, before anything is read from them (#1.2).
    fl=[field_lines(t_,w) for t_,(w,_) in zip((sow,letter,pursuit),FIELD_OWNERS)]; raws=(sow,letter,pursuit)
    for n in ("Engagement ID","Matter ID"): check_id(fld(sow,n),"raw/sow-extract.md "+n)  # the SOW's identifiers have the identifier shape (#1.3)
    for n in ("Client","Title"): check_name(fld(sow,n),"raw/sow-extract.md "+n)  # names are never an engine label form (#1.3)
    check_csv_names(rows,"raw/confirmed-roster.csv",("person","role","point_of_contact"))
    # The engagement's own client and firm domains, declared in the signed SOW or engagement letter, are the only
    # trusted e-mail/URL destinations; consumer or malformed domains are never trusted (confidentiality-and-ethical-wall-rules.md #4.4).
    # A declaration is trusted only when its line is clean read without its own trust: a declaration can never vouch
    # for the instruction it completes ("Send the pack to ops@" / "Client domains: attacker.example"), and a declaration
    # line that is withheld (alone or as half of a flagged pair) declares nothing (#4.3, #4.5).
    decl,bad_dom=declarations((sow,letter)); acc={n:ds for n,(di,i,ds) in enumerate(decl) if ds}
    while True:
        drop=[]
        for n in acc:
            set_trusted_domains([d for m,ds in acc.items() if m!=n for d in ds]); di,i,_=decl[n]; ls=(sow,letter)[di].splitlines()
            if hits(ls[i]) or (i>0 and pair_hits(ls[i-1],ls[i])) or (i+1<len(ls) and pair_hits(ls[i],ls[i+1])): drop.append(n)
        if not drop: break
        for n in drop: del acc[n]
    while True:
        # Only lines every later stage will also accept (domain_trust, the shared re-derivation) are carried (#1.4, #4.4).
        lines={n:(sow,letter)[decl[n][0]].splitlines()[decl[n][1]].strip() for n in acc}; kept,_=domain_trust(list(lines.values())); acc={n:ds for n,ds in acc.items() if lines[n] in kept}
        trusted=list(set_trusted_domains([d for ds in acc.values() for d in ds]))
        h1,s1=scan_lines(sow,"raw/sow-extract.md"); h2,l1=scan_lines(letter,"raw/engagement-letter-extract.md")
        gone=[n for n in acc if (s1,l1)[decl[n][0]].splitlines()[decl[n][1]]!=(sow,letter)[decl[n][0]].splitlines()[decl[n][1]]]
        if not gone: break
        for n in gone: del acc[n]
    decl_lines=[(sow,letter)[decl[n][0]].splitlines()[decl[n][1]].strip() for n in acc]
    sow,letter=s1,l1; h3,pursuit=scan_lines(pursuit,"raw/pursuit-record.md")
    def sf(n): return field_value(raws[0],sow,fl[0],n)
    def lf(n): return field_value(raws[1],letter,fl[1],n)
    def pf(n): return field_value(raws[2],pursuit,fl[2],n)
    st_raw=copy.deepcopy(st)  # identities are harvested from the UNMODIFIED staffing input, before screening redacts them (#3.3)
    st,sth=screen_upstream(st,"upstream/staffing",ENGINE,raw=True)  # every upstream string screened and redacted before use (#4.1, #4.3)
    # Other clients named in the wall register are screened out of the staffing upstream and every raw roster cell
    # before the roster is derived. The trusted own vocabulary is the SOW's own identity only: a roster person or a
    # staffing affiliate never makes another client trusted (#3.3).
    own=engagement_words(sf("Client"),sf("Engagement ID"),sf("Matter ID"),sf("Title"))
    rterms=register_terms(os.path.join(raw_dir,"ethical-wall-register.csv"),{"client_name":sf("Client"),"matter_id":sf("Matter ID")},own)
    # --scenario is copied into run_metadata: a short slug only, and never instruction-like or another client's name (#1.3, #3.3).
    sc=re.sub(r"[._-]+"," ",scenario)
    need(bool(SCENARIO_RE.fullmatch(scenario)) and not hits(sc) and not names_client(sc,rterms),"--scenario must be a short slug (letters, digits, '.', '_' or '-'; at most 64 characters) that is not instruction-like and names no other client (value not repeated); fail closed")
    st,soh=screen_other(st,rterms,ENGINE,"upstream/staffing.")
    rsh=scan_rows(rows,"raw/confirmed-roster.csv"); roh=screen_csv_other(rows,"raw/confirmed-roster.csv",rterms,ENGINE)
    # A register client_name/matter_id that trips the wire and names no usable identity holds anyway (#3.3).
    soh=soh+roh+register_identity_holds(os.path.join(raw_dir,"ethical-wall-register.csv"),ENGINE)
    holds=h1+h2+h3+rsh+sth+soh
    # A staffing file for another client or engagement is another client's data: hold it and screen its identity out
    # of every output (confidentiality-and-ethical-wall-rules.md #3.3). Its identity is read from the raw staffing
    # input (identity_parts: a client_name that also trips the wire still names the client), compared canonically
    # with the SOW; a value the SOW does not declare is unconfirmed and differs (#1.2, #1.3).
    eng=st.get("engagement") or {}; reng=st_raw.get("engagement") or {}; sow_client=sf("Client"); sow_eid=sf("Engagement ID")
    other={k_:other_parts(reng.get(k_),unwithheld(mine),k_,own) for k_,mine in (("client_name",sow_client),("engagement_id",sow_eid))}
    # A staffing identity that trips the wire and names no usable identity cannot be confirmed: a mismatch (#1.2, #3.3).
    mism=[k_ for k_ in ("client_name","engagement_id") if other[k_] or identity_unreadable(reng.get(k_))]
    # A staffing input identified as another engagement's is quarantined: it was screened above (its own holds are
    # positional), but none of its records - verdicts, slates, recommendations, escalations or link holds - is used,
    # so no candidate name, role title, rule or citation it supplies reaches any output (#3.3; role-access-matrix.md #3.1).
    rec=st if not mism else {"governed_roles":[]}
    # Linked staffing records must name the same person: read from the screened staffing input only (#1.5, #4.3).
    badlinks,lh=staffing_links(rec); holds+=lh
    smap,prop,notp=statuses(rec,badlinks); holds+=[rec_hold(x,ENGINE) for x in notp]; roster=[]; excl=[]; names=set(); unrec=set(); joiner={}; unconfirmed=[]; joiners=[]; esc=[esc_text(e,"upstream/staffing.escalations") for e in rec.get("escalations",[])]+([other_escalation(len(soh))] if soh else [])
    for i,r in enumerate(rows,2):
        name=(r.get("person") or "").strip()
        if not name:
            # The roster is keyed by person: a row with a blank key but other values is malformed and refused before it
            # is skipped; only a wholly blank row is ignored (role-access-matrix.md #1.1; confidentiality-and-ethical-wall-rules.md #1.3).
            if any(isinstance(v,str) and v.strip() for k,v in r.items() if base_col(k)!="person"): raise InputError(f"raw/confirmed-roster.csv row {i}.person is blank but the row has other values; every roster row names its person (role-access-matrix.md #1.1); fail closed")
            continue
        # Every rendered display string is non-blank (contract $defs/roster_member): a named roster row without a role is
        # malformed and refused, never rendered blank (confidentiality-and-ethical-wall-rules.md #1.3; role-access-matrix.md #1.1).
        if not (r.get("role") or "").strip(): raise InputError(f"raw/confirmed-roster.csv row {i}.role is blank; every named roster row needs a role (role-access-matrix.md #1.1); fail closed")
        # One canonical person key (#1.3). A withheld roster name joins no Scenario 02 verdict and fails closed as
        # unrecognised: a placeholder is not an identity (confidentiality-and-ethical-wall-rules.md #4.3).
        if is_withheld(name): ss={"verdict":"unrecognised"}
        else: names.add(canon_person(name)); ss=verdict_for(smap.get(canon_person(name),[]),r.get("role",""))
        # The row's onboarding_status grammar is checked before an ineligible verdict or an unconfirmed assignment
        # excludes it: an excluded row with a blank or unrecognised status holds, never passes because it was skipped
        # (role-access-matrix.md #4.4). The escalation does not repeat the excluded row's name.
        if (ss.get("verdict") in INELIGIBLE or canon_text(r.get("assignment_status"))!="confirmed") and canon_text(r.get("onboarding_status","")) not in ONBOARDING:
            holds.append({"hold_id":"HOLD-UNKNOWN-ONBOARDING-STATUS","path":f"raw/confirmed-roster.csv row {i}.onboarding_status","reason":"blank or unrecognised onboarding_status; joiner status cannot be determined","source":ENGINE,"confidence":.99,"citation":"role-access-matrix.md #4.4"})
            esc.append(f"Roster row {i} has a blank or unrecognised onboarding_status; held until the engagement manager confirms the row (role-access-matrix.md #4.4)")
        if ss.get("verdict") in INELIGIBLE:
            excl.append({"person":name,"role":r.get("role",""),"reason":f"{ss.get('verdict')} in Scenario 02 for {ss.get('role_title')}; independence/conflict details stay in the staffing record (need-to-know)","blocking_rule":ss.get("blocking_rule"),"source":"adapter:staffing-slate","confidence":ss.get("confidence",.95),"citation":ss.get("citation","role-access-matrix.md #3.2")}); continue
        if canon_text(r.get("assignment_status"))!="confirmed": unconfirmed.append(name); continue  # role-access-matrix.md #4.1
        item={"person":name,"role":r.get("role",""),"responsibilities":lst(r.get("responsibilities","")),"point_of_contact":r.get("point_of_contact") if (r.get("point_of_contact") or "").strip() else "Engagement manager","onboarding_status":r.get("onboarding_status",""),"assignment_status":"confirmed","source":"raw:confirmed-roster.csv","confidence":.97,"citation":r.get("citation") or "raw/confirmed-roster.csv"}
        if ss.get("verdict")=="unrecognised":
            item["staffing_review"]={"verdict":"unrecognised","blocking_rule":None,"citation":"role-access-matrix.md #3.4"}; unrec.add(join_key(name,canon_person))
            holds.append({"hold_id":"HOLD-UNRECOGNISED-STAFFING-VERDICT","path":f"raw/confirmed-roster.csv row {i}.person" if is_withheld(name) else f"upstream/staffing candidate_slate (raw/confirmed-roster.csv row {i}).eligibility.verdict","reason":"blank, null or unrecognised Scenario 02 verdict for a confirmed roster member","source":ENGINE,"confidence":.99,"citation":"role-access-matrix.md #3.4"})
            esc.append(f"Confirmed roster row {name} has a blank or unrecognised Scenario 02 verdict; held for the engagement manager (role-access-matrix.md #3.4)")
        elif ss.get("verdict") not in (None,"eligible"): item["staffing_review"]={"verdict":ss.get("verdict"),"blocking_rule":ss.get("blocking_rule"),"citation":ss.get("citation")}; esc.append(f"Confirmed roster row {name} is {ss.get('verdict')} in Scenario 02 for {ss.get('role_title')}; confirm with the engagement manager before onboarding ({ss.get('citation')}; role-access-matrix.md #3.3)")
        onb=canon_text(item["onboarding_status"])
        if onb not in ONBOARDING:
            holds.append({"hold_id":"HOLD-UNKNOWN-ONBOARDING-STATUS","path":f"raw/confirmed-roster.csv row {i}.onboarding_status","reason":"blank or unrecognised onboarding_status; joiner status cannot be determined","source":ENGINE,"confidence":.99,"citation":"role-access-matrix.md #4.4"})
            esc.append(f"Roster row {i} has a blank or unrecognised onboarding_status; held until the engagement manager confirms whether {name} is joining (role-access-matrix.md #4.4)")
        roster.append(item)
        if onb in JOINING:
            joiners.append(name)
            if not joiner: joiner=dict(item)
    prop=[p for p in prop if canon_person(p["candidate_name"]) not in names]
    # An excluded subject is named in no derived section (#1.4, #1.5; role-access-matrix.md #3.2): a proposed candidate
    # or a point of contact naming an excluded roster member is dropped and held, name not repeated.
    xs={join_key(x["person"],canon_person) for x in excl}-{None}
    for p in [p for p in prop if join_key(p["candidate_name"],canon_person) in xs]: prop.remove(p); holds.append(excluded_hold("scope.proposed_staffing",ENGINE))
    for n,r in enumerate(roster):
        if join_key(r.get("point_of_contact"),canon_person) in xs:
            r["point_of_contact"]="Engagement manager"; holds.append(excluded_hold(f"raw/confirmed-roster.csv team_roster[{n}].point_of_contact",ENGINE))
            if joiner and canon_person(joiner.get("person"))==canon_person(r.get("person")): joiner["point_of_contact"]="Engagement manager"
    if any(canon_id(h.get("hold_id"))==canon_id(EXCLUDED_HOLD_ID) for h in holds): esc.append("A derived section named a person excluded from this engagement; the name was dropped and held for the engagement manager (role-access-matrix.md #3.2)")
    # A slate or recommendation verdict outside the enum is held at its record even when the person is not on the roster,
    # unconfirmed or excluded; a confirmed member's own unrecognised verdict is already held above (role-access-matrix.md #3.4).
    iv=[x for x,pn in invalid_verdicts(rec,badlinks) if pn is None or pn not in unrec]
    holds+=[{"hold_id":"HOLD-UNRECOGNISED-STAFFING-VERDICT","path":x,"reason":VERDICT_GRAMMAR_REASON,"source":ENGINE,"confidence":.99,"citation":"role-access-matrix.md #3.4"} for x in iv]
    if iv: esc.append(verdict_grammar_escalation(len(iv)))
    exclusions=items(sf("Exclusions")); pt=canon_text(pursuit)
    for e in exclusions:
        if e!=WITHHELD and canon_text(e).split(" - ")[0] in pt and re.search(r"\b(?:include|included|request|requested|add|added|reuse)\b",pt): esc.append(f"SOW exclusion controls over pursuit conflict: '{e}' (confidentiality-and-ethical-wall-rules.md #1.2)"); break
    for n in unconfirmed: esc.append(f"Roster row for {n} has no confirmed assignment_status; treated as not assigned (role-access-matrix.md #4.1)")
    if not joiners: esc.append("No joining team member found in the confirmed roster; wall check and access checklist will hold (confidentiality-and-ethical-wall-rules.md #2.2)")
    elif len(joiners)>1: esc.append(f"Multiple joiners found ({', '.join(joiners)}); this pack covers {joiners[0]} only - run again per joiner (role-access-matrix.md #4.1)")
    for x in excl: esc.append(f"Confirmed roster row excluded: {x['person']} is ineligible/conflicted in Scenario 02 ({x['citation']})")
    if bad_dom:
        holds.append({"hold_id":"HOLD-DOMAIN-NOT-TRUSTED","path":"raw/sow-extract.md or raw/engagement-letter-extract.md domain declaration","reason":f"{bad_dom} declared client/firm domain(s) are malformed or consumer/file-sharing domains and are not trusted (not repeated)","source":ENGINE,"confidence":.97,"citation":"confidentiality-and-ethical-wall-rules.md #4.4"})
        esc.append("A declared client/firm domain is malformed or a consumer/file-sharing domain; confirm the engagement's domains with the engagement manager (confidentiality-and-ethical-wall-rules.md #4.4)")
    holds=dedup_holds(holds)
    # The SOW alone declares the engagement's identity (#1.2): a blank SOW Client or Engagement ID is never filled
    # from the staffing file, and the run holds.
    blank=[n for n,v in (("Client",sow_client),("Engagement ID",sow_eid)) if not v]  # a withheld line already holds (#4.3)
    if blank:
        holds.append({"hold_id":"HOLD-SOW-IDENTITY-MISSING","path":"raw/sow-extract.md "+"/".join(blank),"reason":"the SOW does not declare the engagement's client or engagement ID; the engagement identity cannot be confirmed","source":ENGINE,"confidence":.99,"citation":"confidentiality-and-ethical-wall-rules.md #1.2"})
        esc.append("The SOW does not declare the engagement's client or engagement ID; confirm the engagement identity with the engagement manager (confidentiality-and-ethical-wall-rules.md #1.2)")
    # A staffing input that does not state the client or engagement ID cannot be confirmed to be this engagement's:
    # an absent identity never passes the check as a match (#1.2, #3.3).
    unstated=[k_ for k_ in ("client_name","engagement_id") if k_ not in mism and not canon_text(unwithheld(reng.get(k_)) if isinstance(reng.get(k_),str) else "")]
    if lh: esc.append(link_escalation(len(lh)))
    if notp: esc.append(rec_escalation(len(notp)))
    if mism:
        holds.append({"hold_id":"HOLD-STAFFING-ENGAGEMENT-MISMATCH","path":"upstream/staffing.engagement."+"/".join(mism),"reason":"staffing input names a different client or engagement than the SOW (name not repeated); staffing evidence not trusted","source":ENGINE,"confidence":.99,"citation":"confidentiality-and-ethical-wall-rules.md #3.3; role-access-matrix.md #3.1"})
        esc.append("Staffing input is for a different client or engagement than the SOW; staffing evidence held for the engagement manager (confidentiality-and-ethical-wall-rules.md #3.3)")
    if unstated:
        holds.append({"hold_id":"HOLD-STAFFING-ENGAGEMENT-MISMATCH","path":"upstream/staffing.engagement."+"/".join(unstated),"reason":STAFFING_UNSTATED_REASON,"source":ENGINE,"confidence":.99,"citation":"confidentiality-and-ethical-wall-rules.md #1.2, #3.3; role-access-matrix.md #3.1"})
        esc.append(STAFFING_UNSTATED_ESCALATION)
    affiliates=[x for x in (eng.get("affiliates") or []) if x.strip()] if not (mism or unstated) else []
    if any(h.get("source")=="engine:safety_text" for h in holds): esc.append(f"{sum(h.get('source')=='engine:safety_text' for h in holds)} source field(s) held for embedded instruction review (confidentiality-and-ethical-wall-rules.md #4.1-#4.5)")
    body={"engagement":{"engagement_id":one(sow_eid),"matter_id":one(sf("Matter ID")),"title":one(sf("Title")),"client_name":one(sow_client),"affiliates":affiliates,"sector":one(pf("Sector")),"region":one(pf("Region")),"source":ENGINE,"confidence":.95,"citation":"raw/sow-extract.md header; raw/pursuit-record.md context",**({"trusted_domains":trusted,"domain_declarations":decl_lines} if trusted else {})},"joiner":joiner,"scope_summary":{"objectives":items(sf("Objectives")),"in_scope":items(sf("In scope")),"exclusions":exclusions,"deliverables":items(sf("Deliverables")),"key_dates":items(sf("Key dates")),"systems":items(sf("Systems")),"first_week_focus":items(sf("First-week")),"source":ENGINE,"confidence":.94,"citation":"raw/sow-extract.md; confidentiality-and-ethical-wall-rules.md #1.2"},"engagement_terms":{"confidentiality_terms":items(lf("Confidentiality")),"ethical_wall_terms":items(lf("Ethical walls")),"source":"raw:engagement-letter-extract.md","confidence":.93,"citation":"raw/engagement-letter-extract.md"},"team_roster":roster,"proposed_staffing":prop,"staffing_exclusions":excl,"escalations":esc}
    body=redact(body)
    # Other clients named in the wall register never reach scope.json either: the same identities and own words every
    # later engine uses, whatever the register's validity for the wall decision (#2.1, #3.3).
    body,rh=screen_other(body,register_terms(os.path.join(raw_dir,"ethical-wall-register.csv"),body["engagement"],own_words(body)),ENGINE,"scope.")
    if rh: holds=dedup_holds(holds+rh); body["escalations"].append(other_escalation(len(rh)))
    if mism:
        body,oh=screen_other(body,client_terms([x for k_ in mism for x in other[k_]],own),ENGINE,"scope.")  # only the identity that differs, from the raw input
        if oh: holds=dedup_holds(holds+oh); body["escalations"].append(other_escalation(len(oh)))
    body=settle_trust(body)  # a declaration line screening withheld backs no trusted domain (#4.4)
    # The roster and the pack show the SOW's and the roster's values side by side ("Client: ..." above "Joiner: ..."):
    # scope.json is read in that rendered order too, so a claim split across sources is held and withheld here, at the
    # first stage, and never reaches a later document (#4.5).
    sb,sh=screen_rendered({**body,"holds":holds},scope_rows,"scope.json")
    if sh: holds=dedup_holds(sb.pop("holds")+sh); body=sb; body["escalations"].append(rendered_escalation("scope.json",len(sh)))
    out={"contract_version":CONTRACT_VERSION,"run_metadata":{"generated_at":ts,"demo_scenario":scenario},**body,"holds":holds,"provenance":{"engines":[f"scope_digest/{VERSION}"],"generated_at":ts,"sources":["raw/sow-extract.md","raw/engagement-letter-extract.md","raw/pursuit-record.md","raw/confirmed-roster.csv","upstream/staffing"]}}
    out=bind_withheld(out,"scope",ENGINE)  # every placeholder bound to a hold at its field (#1.4, #4.3)
    check_contract(out,"scope","scope"); return out  # the document written is held to the contract (#1.3)
def main():
    ap=ArgParser(); ap.add_argument("--raw-dir",required=True); ap.add_argument("--staffing",required=True); ap.add_argument("--confirmed-roster",required=True); ap.add_argument("--out",required=True); ap.add_argument("--generated-at",required=True); ap.add_argument("--scenario",default=""); a=ap.parse_args(); ts=require_iso_z(a.generated_at)
    dump_json(a.out,derive(a.raw_dir,a.staffing,a.confirmed_roster,a.scenario,ts),"scope output")
if __name__=="__main__": guard(main)
