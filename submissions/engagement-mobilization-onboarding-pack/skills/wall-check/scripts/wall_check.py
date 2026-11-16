#!/usr/bin/env python3
import argparse, hashlib, re
from safety_text import *
import knowledge_match
ENGINE="engine:wall_check"; CLEAR={"clear","cleared"}  # confidentiality-and-ethical-wall-rules.md #2.2
RESTRICT={"restricted","walled","conflicted","deny"}  # confidentiality-and-ethical-wall-rules.md #2.3
MISSING_REGISTER_REFUSED=True  # confidentiality-and-ethical-wall-rules.md #2.1, #3.3: no register, no other-client screen, no output (register_rows)
UNKNOWN_STATUS_HOLDS=True  # confidentiality-and-ethical-wall-rules.md #2.2
CLEAR_NEEDS_NAMED_PERSON=True  # confidentiality-and-ethical-wall-rules.md #2.2
FREE_TEXT_NOT_BRIEFED=True  # confidentiality-and-ethical-wall-rules.md #3.1
BRIEFING_TOPICS_SCREENED=True  # confidentiality-and-ethical-wall-rules.md #3.2
KNOWN_CLASSIFICATIONS={"client_confidential","confidential","restricted","internal","public"}  # workspace-inventory-rules.md #2.3
OTHER_CLIENTS_SCREENED=True  # confidentiality-and-ethical-wall-rules.md #3.3
INVENTORY_LABEL="raw/workspace-inventory.csv"
INVENTORY_COLUMNS=("workspace_id","workspace_type","default_permission","depends_on_knowledge","data_classification")  # workspace-inventory-rules.md #1.3
def inventory_problem(ws):
    """(hold ID, path, reason, rule) when the workspace inventory cannot be used, else None. The one check wall_check
    and access_checklist (and so verify_render) apply, on the rows AS READ, before screening rewrites a cell: a
    missing file holds (#1.2); a header that repeats a column or lacks a required one (a zero-byte or blank file has
    no header) or a repeated workspace_id is malformed and holds (#1.3). Only a well-formed header with no rows is an
    explicitly empty inventory (#1.2)."""
    if ws is None: return "HOLD-MISSING-WORKSPACE-INVENTORY",INVENTORY_LABEL,"missing workspace inventory; no access is requested","#1.2"
    bad="HOLD-MALFORMED-WORKSPACE-INVENTORY"
    if ws.duplicate_columns: return bad,INVENTORY_LABEL+" header","workspace inventory "+DUPLICATE_HEADER_REASON+"; no access is requested","#1.3"
    miss=missing_columns(ws,INVENTORY_COLUMNS)
    if miss: return bad,INVENTORY_LABEL+" header",f"workspace inventory is missing required column(s): {', '.join(miss)}; no access is requested","#1.3"
    dup=duplicate_rows(ws,"workspace_id")  # keyed by workspace_id: a repeat holds, never last-wins (#1.3)
    if dup: return bad,INVENTORY_LABEL+" rows "+", ".join(map(str,dup))+" workspace_id","workspace inventory workspace_id "+DUPLICATE_ID_REASON+"; no access is requested","#1.3"
    return None
def inventory_hold(problem,engine):
    hid,path,why,rule=problem; return {"hold_id":hid,"path":path,"reason":why,"source":engine,"confidence":.99,"citation":"workspace-inventory-rules.md "+rule}
def foreign_rows(ws):
    """File row numbers of inventory rows with a cell the other-client screen withheld (screen_csv_other has run): the
    workspace is identified with another client, so the row is quarantined. It is never requested, denied, held or
    listed by its supplied ID or name; only its positional other-client hold names it (confidentiality-and-ethical-
    wall-rules.md #3.3)."""
    return {i for i,w in enumerate(ws or [],2) if any(isinstance(v,str) and OTHER_WITHHELD in v for v in w.values())}
def applies(r,e,j):
    # Every populated field must match; blank person = engagement-wide row; a row must name this client or matter.
    # One canonical comparison (canon_person / canon_id): `Taylor  Reed` and `taylor reed` are the same joiner (#1.3).
    # A withheld value on either side never matches: two different flagged names both read "[withheld ...]" (#4.3).
    for a,b in (("person","person"),("client_name","client_name"),("matter_id","matter_id")):
        if (r.get(a) or "").strip() and (is_withheld(r.get(a)) or is_withheld((j if a=="person" else e).get(b))): return False
    p,c,m=canon_person(r.get("person")),canon_person(r.get("client_name")),canon_id(r.get("matter_id"))
    if p and p!=canon_person(j.get("person")): return False
    if c and c!=canon_person(e.get("client_name")): return False
    if m and m!=canon_id(e.get("matter_id")): return False
    return bool(c or m)
def cin(v,xs): return join_key(v) in {join_key(x) for x in xs}-{None}  # ID membership by canonical form; a blank key is a member of nothing (#1.3)
def row_cite(r): return r.get("citation") or "raw/ethical-wall-register.csv"
def topics(r): return [x.strip() for x in (r.get("briefing_topics") or "").split(";") if x.strip()]
def names_other(text,terms,own,own_ids):
    """Briefing topics get the strictest screen: known identities, any other matter-like ID and any capitalised name
    that is not this engagement's own (#3.2)."""
    if names_client(text,terms): return True
    if any(canon_id(x) not in own_ids for x in re.findall(r"\b[A-Za-z]{2,}(?:-[A-Za-z0-9]+)*-\d{2,}[A-Za-z0-9-]*\b",text or "")): return True
    for run,start in cap_runs(text):
        ws=words(run)
        if not ws or ws<=own|ALLOW_CAPS or (start and len(run.split())==1): continue
        return True
    return False
def check_matched(p):
    need(isinstance(p,dict),f"matched input must be a JSON object, got {type(p).__name__}; fail closed")
    if p.get("contract_version")!=CONTRACT_VERSION: raise InputError(f"expected contract {CONTRACT_VERSION} in matched input")
    if "prior_knowledge_candidates" not in p or "knowledge_digest" not in p: raise InputError("matched input has no prior_knowledge_candidates/knowledge_digest; run knowledge_match first; fail closed")
    field(p,"knowledge_digest","obj","matched",required=True); check_contract(p,"matched","matched")  # confidentiality-and-ethical-wall-rules.md #1.3
    # Every placeholder, escalation or held status from an earlier stage must still have its hold (#1.4); the rest of
    # the document is proved equal to its re-derivation from the raw inputs (same_document).
    check_hold_evidence(p,"matched")
def govern(p,register,inventory,closeout,staffing,raised=None):
    """Derive the wall decision, the workspace decisions and the digest gating for document p from the raw wall
    register and workspace inventory, screening with the one other-client identity set (knowledge_match.
    other_client_terms: register, Closeout and staffing identities). access_checklist re-runs this on the governed
    document to re-derive, never trust, the decision state (confidentiality-and-ethical-wall-rules.md #1.4, #3.3)."""
    p,mh=screen_upstream(p,"matched",ENGINE)  # every upstream string screened and redacted before use; any hit holds the wall (#4.1, #4.3)
    if mh: p.setdefault("escalations",[]).append(upstream_escalation(len(mh)))
    rows=register_rows(register); ws=read_csv(inventory,False,"workspace inventory"); check_csv_ids(ws,"raw/workspace-inventory.csv",("workspace_id",)); check_csv_names(ws,"raw/workspace-inventory.csv",("name",)); up=list(p.get("holds",[])); holds=list(mh); deniedk=[]; deniedw=[]; heldw=[]; may=[]; withheld_names=[]; j=p.get("joiner") or {}; e=p.get("engagement") or {}; esc=p.setdefault("escalations",[])
    status="clear"; reason="wall register marks joiner clear for this client/matter"; cit="confidentiality-and-ethical-wall-rules.md #2.2"
    own=own_words(p); own_ids={canon_id(e.get("matter_id")),canon_id(e.get("engagement_id"))}-{""}
    def hold_status(hid,path,why,rule):
        holds.append({"hold_id":hid,"path":path,"reason":why,"source":ENGINE,"confidence":.99,"citation":f"confidentiality-and-ethical-wall-rules.md {rule}"}); return "hold",why,f"confidentiality-and-ethical-wall-rules.md {rule}"
    # Other-client identities are harvested whatever the register's validity for the decision: a register with a
    # missing or repeated column still names the clients it lists (every copy of a repeated column counts), so the
    # names are withheld everywhere while the decision holds (#2.1, #3.3). They are harvested from the register AS
    # READ, before scan_rows rewrites a flagged cell: a restriction that trips the wire still names its client (#3.3).
    # The register is one source of the shared identity set; the Closeout and staffing identities are the others (#3.3).
    terms,_=knowledge_match.other_client_terms(p,closeout,register,staffing)
    idh=unreadable_identity_holds(rows,REGISTER_LABEL,ENGINE) if rows is not None else []  # a tripped identity cell naming no one usable holds (#3.3)
    scr=(scan_rows(rows,REGISTER_LABEL) if rows is not None else [])+idh
    p,oh=screen_other(p,terms,ENGINE,"matched.")  # every text field, not only the briefing (#3.3)
    esc=p.setdefault("escalations",[])  # screen_other returns a new document: always rebind (#3.2)
    if oh: esc.append(other_escalation(len(oh)))
    if idh: esc.append(other_escalation(len(idh)))
    scr+=oh; j=p.get("joiner") or {}; e=p.get("engagement") or {}
    if not canon_person(j.get("person")):
        status,reason,cit=hold_status("HOLD-NO-JOINER","scope.joiner","no joiner identified; wall status cannot be determined","#2.2"); holds+=scr
    elif missing_columns(rows,REGISTER_COLUMNS):
        status,reason,cit=hold_status("HOLD-MALFORMED-WALL-REGISTER","raw/ethical-wall-register.csv header",f"ethical-wall register is missing required column(s): {', '.join(missing_columns(rows,REGISTER_COLUMNS))}","#2.1"); holds+=scr
    elif rows.duplicate_columns:
        # A repeated column (status,status) is ambiguous: csv keeps only the last value (restricted,clear -> clear) (#2.1).
        status,reason,cit=hold_status("HOLD-MALFORMED-WALL-REGISTER","raw/ethical-wall-register.csv header","ethical-wall register "+DUPLICATE_HEADER_REASON,"#2.1"); holds+=scr
    else:
        if rows.malformed: hold_status("HOLD-MALFORMED-WALL-REGISTER","raw/ethical-wall-register.csv rows "+", ".join(map(str,rows.malformed)),"ethical-wall register row(s) carry more fields than the header","#2.1")
        holds+=scr
        matches=[(i,r) for i,r in enumerate(rows,2) if applies(r,e,j)]
        # Every data row's grammar is validated before the applicability filter excludes it: a row for another person,
        # client or matter with a blank or unrecognised status, or a row naming neither a client nor a matter (which
        # could never apply), holds instead of being skipped. A wholly blank row is not a record (#2.1, #2.2).
        mi={i for i,_ in matches}; others=[(i,r) for i,r in enumerate(rows,2) if i not in mi and any(isinstance(v,str) and v.strip() for v in r.values())]
        bad_st=[i for i,r in others if canon_text(r.get("status")) not in RESTRICT|CLEAR]; no_id=[i for i,r in others if not (r.get("client_name") or "").strip() and not (r.get("matter_id") or "").strip()]
        if bad_st: hold_status("HOLD-UNKNOWN-WALL-STATUS","raw/ethical-wall-register.csv rows "+", ".join(map(str,bad_st))+" status","unknown wall status value (not repeated); treated as hold","#2.2")
        if no_id: hold_status("HOLD-MALFORMED-WALL-REGISTER","raw/ethical-wall-register.csv rows "+", ".join(map(str,no_id)),REGISTER_NO_SUBJECT_REASON,"#2.1")
        # Every cell of a row that applies to this engagement is screened before it is derived from: its citation and
        # restricted workspaces reach the decision and the briefing. Restriction text is never copied (#3.1) and is the
        # source of the identities; briefing topics have the stricter screen below (#3.2, #3.3).
        rh=screen_csv_other(rows,REGISTER_LABEL,terms,ENGINE,only={i for i,_ in matches},skip=("restriction","briefing_topics"))
        if rh: holds+=rh; esc.append(other_escalation(len(rh)))
        restricted=[(i,r) for i,r in matches if canon_text(r.get("status")) in RESTRICT]
        unknown=[r for i,r in matches if canon_text(r.get("status")) not in RESTRICT|CLEAR]
        named_clear=[r for i,r in matches if canon_text(r.get("status")) in CLEAR and canon_person(r.get("person"))]
        if restricted:
            status="denied"; reason="joiner restricted by ethical-wall register; restriction details are held by Risk/Conflicts (need-to-know)"; cit="; ".join(row_cite(r) for i,r in restricted)
            deniedk=[x.get("knowledge_id") for x in p.get("prior_knowledge_candidates",[])]
            for i,r in restricted:
                for w in (r.get("restricted_workspaces") or "").split(";"):
                    if w.strip() and not cin(w,deniedw) and not is_withheld(w): deniedw.append(w.strip())  # a withheld ID is held, never published (#3.3); the register's spelling is kept, compared canonically (#1.3)
            briefed=[]; screened=0; groups={}
            # Topics are grouped canonically before they are screened: a group is briefed once, in its first spelling,
            # and is withheld when ANY spelling trips a screen (#1.3, #3.2, #4.3).
            for i,r in restricted:
                for t in topics(r): groups.setdefault(item_key(t,canon_text),[]).append((i,t))
            for g in groups.values():
                if any(is_withheld(t) or hits(t) for _,t in g): briefed.append(WITHHELD); screened+=1; continue  # tripwire hold already raised by scan_rows (#4.3)
                oth=[(i,t) for i,t in g if names_other(t,terms,own,own_ids)]
                if oth:
                    briefed.append(TOPIC_WITHHELD); screened+=1
                    for i,t in oth: holds.append({"hold_id":"HOLD-BRIEFING-TOPIC-"+hashlib.sha256(strip_cf(t).encode()).hexdigest()[:12],"path":f"raw/ethical-wall-register.csv row {i}.briefing_topics","reason":"briefing topic names another client, matter or identifying detail; withheld from the pack","source":ENGINE,"confidence":.97,"citation":"confidentiality-and-ethical-wall-rules.md #3.1,#3.2"})
                    continue
                briefed.append(g[0][1])
            if screened: esc.append(f"{screened} wall briefing topic(s) withheld from the pack; Risk/Conflicts brief the joiner directly (confidentiality-and-ethical-wall-rules.md #3.2)")
            rtext=("may not access or discuss: "+"; ".join(canon_union(briefed,f=canon_text))) if briefed else "restricted subject matter - confirm specifics with Risk/Conflicts before starting work"
            # Topics from different register rows are joined into one restriction: the joined topics are read in their
            # rendered order (pairs and runs), so a claim split across rows is held like one written in a single cell (#3.2, #4.5).
            vis=[x for x in canon_union(briefed,f=canon_text) if x not in (WITHHELD,TOPIC_WITHHELD) and not is_withheld(x)]
            jh=hits(rtext) or next((f for _,f in rendered_runs(vis)),[])
            if jh: holds.append(hold("raw/ethical-wall-register.csv briefing_topics (rows joined)",rtext,["split_across_fields"] if "oversize" not in jh else jh)); rtext=WITHHELD
            may.append({"item":next((x for x in (e.get("client_name"),e.get("matter_id")) if (x or "").strip()),"this client or matter"),"type":"client_or_matter","restriction":rtext,"citation":f"{cit}; confidentiality-and-ethical-wall-rules.md #2.3,#3.1,#3.2"})
        elif unknown:
            status,reason,cit=hold_status("HOLD-UNKNOWN-WALL-STATUS","raw/ethical-wall-register.csv.status","unknown wall status value (not repeated); treated as hold","#2.2")
        elif not named_clear:
            status,reason,cit=hold_status("HOLD-UNKNOWN-WALL-STATUS","raw/ethical-wall-register.csv","no wall register row clears this joiner for this client or matter","#2.2")
        else: cit="; ".join(row_cite(r) for r in named_clear)
    # The workspace inventory gates the wall like every other source: a missing file, an unusable header (a zero-byte
    # file has none) or a repeated workspace_id holds here, so the wall stage never yields a clear decision or an
    # allowed-knowledge list while the inventory is absent or malformed (workspace-inventory-rules.md #1.2, #1.3).
    bad=inventory_problem(ws); foreign=set()
    if bad: holds.append(inventory_hold(bad,ENGINE))
    if ws is not None:
        # Every inventory cell is screened, for instructions and for other clients, from the rows AS READ - IDs,
        # types, permissions, classifications and citations as well as names - before any decision uses them, and
        # before an unusable header or a repeated ID empties the collection the decisions use: an inventory that
        # is not used is still screened and its flagged cells held. A withheld identifier is never a decision key (#1.3, #3.3, #4.3).
        holds+=scan_rows(ws,INVENTORY_LABEL)
        ih=screen_csv_other(ws,INVENTORY_LABEL,terms,ENGINE)
        if ih: holds+=ih; esc.append(other_escalation(len(ih)))
        if bad: ws=Rows()
        foreign=foreign_rows(ws)  # another client's workspace: quarantined, named only by its positional hold (#3.3)
        for i,w in enumerate(ws,2):
            if i in foreign: continue
            nm=w.get("name") or ""; wid=w.get("workspace_id")
            if (hits(nm) or is_withheld(nm)) and wid and not is_withheld(wid) and not cin(wid,withheld_names): withheld_names.append(wid)
    # Upstream holds are supplied content: another client's name or steering text in them never travels (#3.3, #4.3).
    up,uh=screen_holds(up,terms,ENGINE,"matched.holds")
    if any(hold_is(h,"HOLD-OTHER-CLIENT-") for h in uh): esc.append(other_escalation(sum(hold_is(h,"HOLD-OTHER-CLIENT-") for h in uh)))
    if raised is not None: raised.extend(dedup_holds(holds+uh))  # the holds this derivation raised itself, before carried holds are merged (access_checklist reconciles each by content, #1.4)
    holds=merge_own_holds(up,holds+uh)  # an upstream hold with the key of one raised here is carried as this engine's own copy: re-derivable field for field (#1.4)
    if holds and status=="clear": status="hold"; reason="source holds require review before knowledge/access release"; cit="confidentiality-and-ethical-wall-rules.md #4.1"
    odd=[]
    for i,w in enumerate(ws or [],2):
        wid=w.get("workspace_id")
        if is_withheld(wid): continue  # never requested (access_checklist: invalid row) and never published
        if i in foreign:
            # Another client's inventory row is never requested, held or listed. A workspace the applicable register
            # row restricts is still briefed, by the register's own spelling and citation, never the row's (#2.3, #3.3).
            if status=="denied" and cin(wid,deniedw): may.append({"item":next(x for x in deniedw if join_key(x)==join_key(wid)),"type":"workspace","restriction":"workspace restricted by ethical-wall register","citation":f"{cit}; confidentiality-and-ethical-wall-rules.md #2.3; workspace-inventory-rules.md #2.2"})
            continue
        conf=client_confidential(w.get("data_classification")); dep=depends_on_knowledge(w.get("depends_on_knowledge"))  # blank/unknown fail closed (workspace-inventory-rules.md #2.3)
        if not cin(w.get("data_classification"),KNOWN_CLASSIFICATIONS) or canon_text(w.get("depends_on_knowledge")) not in TRUE_VALUES|FALSE_VALUES: odd.append(str(i))
        if status=="denied" and cin(wid,deniedw):
            name=wid if cin(wid,withheld_names) or not (w.get("name") or "").strip() else w["name"]
            may.append({"item":name,"type":"workspace","restriction":"workspace restricted by ethical-wall register","citation":f"{w.get('citation') or 'raw/workspace-inventory.csv'}; confidentiality-and-ethical-wall-rules.md #2.3; workspace-inventory-rules.md #2.2"})
        elif status in {"denied","hold"} and (conf or dep) and not cin(wid,heldw): heldw.append(wid)
    if odd: esc.append(f"Workspace inventory row(s) {', '.join(odd)} have a blank or unrecognised data_classification/depends_on_knowledge; treated as client-confidential and knowledge-dependent (workspace-inventory-rules.md #2.3)")
    allowed=[] if status in {"denied","hold"} else p.get("prior_knowledge_candidates",[])
    p["wall_decision"]={"status":status,"reason":reason,"allowed_knowledge_ids":[x.get("knowledge_id") for x in allowed],"denied_knowledge_ids":deniedk,"denied_workspace_ids":deniedw,"held_workspace_ids":heldw,"name_withheld_workspace_ids":withheld_names,"may_not_access_discuss":may,"source":ENGINE,"confidence":.98 if status!="hold" else .8,"citation":cit}
    kd=p.get("knowledge_digest",{})
    if status=="clear": kd["items"]=allowed
    elif status=="denied": kd.update({"status":"denied_by_wall","items":[],"denied_items":deniedk})
    else: kd.update({"status":"hold","items":[]})
    p["knowledge_digest"]=kd; p["holds"]=holds; return p
def derive(p,register,inventory,ts,closeout,staffing):
    """governed.json for a matched document (knowledge_match's output, or a carried one proved equal to it), the wall
    register, the workspace inventory, this stage's run timestamp and the Closeout and staffing inputs the identity
    set is derived from. access_checklist re-runs it (rederive, #1.4)."""
    adopt_trust(p)  # from the declaration lines scope_digest accepted, never a carried list (#1.4, #4.4)
    p=govern(p,register,inventory,closeout,staffing)
    p.setdefault("provenance",{}).setdefault("engines",[]).append(f"wall_check/{VERSION}"); p["provenance"]["generated_at"]=ts
    p=bind_withheld(settle_trust(p),"governed",ENGINE); check_contract(p,"governed","governed"); return p  # the document written is held to the same contract (#1.3)
def rederive(doc,raw_dir,staffing,roster,closeout,register,inventory,ts,where):
    """The governed document the raw inputs give: scope_digest, knowledge_match and this engine, re-run whole. The
    matched stage ran under its own timestamp, which only the governed document's provenance overwrote (#1.4)."""
    m=knowledge_match.rederive(doc,raw_dir,staffing,roster,closeout,register,ts,where)
    return derive(reread(m,"re-derived matched document"),register,inventory,ts,closeout,staffing)
def main():
    ap=ArgParser()
    for k in ("--matched","--raw-dir","--staffing","--confirmed-roster","--closeout","--wall-register","--workspace-inventory","--out","--generated-at"): ap.add_argument(k,required=True)
    a=ap.parse_args(); ts=require_iso_z(a.generated_at)
    p=load_json(a.matched,"matched input"); check_matched(p)
    m=knowledge_match.rederive(p,a.raw_dir,a.staffing,a.confirmed_roster,a.closeout,a.wall_register,stage_timestamp(p,"matched input"),"matched input")
    same_document(p,m,"matched input")  # every field equals the scope_digest + knowledge_match re-derivation from the raw inputs (#1.4)
    dump_json(a.out,derive(p,a.wall_register,a.workspace_inventory,ts,a.closeout,a.staffing),"governed output")
if __name__=="__main__": guard(main)
