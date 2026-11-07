#!/usr/bin/env python3
import argparse, copy, re
from safety_text import *
import safety_text
import scope_digest
ENGINE="engine:knowledge_match"; CLOSE="ps.engagement-closeout-knowledge-harvest.v1"  # knowledge-reuse-rules.md #1.1
STATES={"RELEASE_CANDIDATE_SANITISED","RELEASE_CANDIDATE_SANITIZED"}  # knowledge-reuse-rules.md #2.1
PERM="cleared_for_internal_engagement_reuse"  # knowledge-reuse-rules.md #2.2
LESSON_NOT_WRITTEN="lesson_text_not_written_in_governed_closeout_record"  # knowledge-reuse-rules.md #2.4
DESCRIPTION_IS_GUIDANCE="description_is_stage_guidance_not_written_content"  # knowledge-reuse-rules.md #2.6
CLEARED="cleared_for_internal_reuse"
PENDING_SUMMARY="Released Closeout knowledge candidate; use the title and citation only until practice review confirms."  # #2.3
NO_DESCRIPTION="No written description is supplied in the governed Closeout record; refer to the title and citation."  # #1.4
def review_status(*xs):  # knowledge-reuse-rules.md #2.3: only an explicit false clears review
    return "pending_practice_review" if any(x.get("review_required") is not False for x in xs if isinstance(x,dict)) else CLEARED
# knowledge-reuse-rules.md #2.6: a description that is guidance addressed to whoever produces the text, rather than
# written content, is never rendered. It is recognised by structure, not by one list of verbs, after NFKC, case and
# look-alike folding (norm):
# (i) it addresses a producer: "For the drafter, ...", "Whoever writes the next version ...", "the next stage should
#     ...", "for the next version", "you should ...", "Preparation note for the next stage: ...";
# (ii) it is a directive to produce text: an imperative or a modal construction (should, must, needs to, is to, to be
#     ...) whose verb produces or transforms text. Verbs that only produce text (write, draft, summarise, synthesise,
#     rephrase ...) count with any object; verbs that also produce other things (create, turn, convert, make, build,
#     prepare ...) count when their object is text (a summary, lesson, note, overview, the citations ...) or they turn
#     something "into" it; and "into a <...> summary/lesson/note/overview" counts on its own;
# (iii) it is a placeholder for text not yet written ("to be written", "TBD") or a drafting rule ("Do not quote ...",
#     "from the title and citations only").
# Factual descriptions that merely mention drafters or summaries ("Checklist used by the drafting team", "Summary of
# the governance cadence", "Onboarding guide written by the delivery team") render unchanged.
def _forms(v):
    """Every inflection of verb v (first word inflected for phrasal verbs): base, -s, past/participle, -ing."""
    w,_,tail=v.partition(" "); tail=(" "+tail) if tail else ""
    irr={"write":("writes","wrote","written","writing"),"rewrite":("rewrites","rewrote","rewritten","rewriting"),"make":("makes","made","making"),"build":("builds","built","building"),"recast":("recasts","recasting"),"put":("puts","putting"),"distil":("distils","distilled","distilling"),"set":("sets","setting")}
    if w in irr: f=(w,)+irr[w]
    elif w.endswith("e"): f=(w,w+"s",w+"d",w[:-1]+"ing")
    elif w.endswith("y") and w[-2:-1] not in "aeiou": f=(w,w[:-1]+"ies",w[:-1]+"ied",w+"ing")
    elif w.endswith(("s","sh","ch","x","z")): f=(w,w+"es",w+"ed",w+"ing")
    else: f=(w,w+"s",w+"ed",w+"ing")
    return [x+tail for x in f]
def _alt(xs): return "(?:"+"|".join(sorted({re.escape(x).replace("\\ ",r"\s+") for x in xs},key=len,reverse=True))+")"
_TEXT_V=("write","write up","draft","redraft","rewrite","compose","summarise","summarize","synthesise","synthesize","condense","rephrase","reword","paraphrase","restate","recast","generalise","generalize","author","reconstruct","distil","distill","abridge","flesh out","boil down")
_MAKE_V=("create","produce","generate","prepare","turn","convert","make","build","outline","expand","adapt","transform","rework","revise","compile","craft","polish","simplify","shorten","fill in","put together","elaborate","formulate","assemble","edit","update","extend","develop","derive","extract")
_TV=_alt(_TEXT_V); _MV=_alt(_MAKE_V); _TVF=_alt(f for v in _TEXT_V for f in _forms(v)); _MVF=_alt(f for v in _MAKE_V for f in _forms(v)); _AVF=_alt(f for v in _TEXT_V+_MAKE_V for f in _forms(v))
_TVP=_alt(_forms(v)[-2] for v in _TEXT_V); _MVP=_alt(_forms(v)[-2] for v in _MAKE_V)  # participles
_TEXTN=r"(?:summary|summaries|lessons?|notes?|overviews?|text|paragraphs?|sentences?|descriptions?|narratives?|abstracts?|synopsis|synopses|write ?ups?|blurbs?|prose|guidance|versions?|drafts?|citations?|evidence(?: ids?)?|titles?|category|bullets?|brief|recaps?|wording|statements?|entry|entries|account)"
_OBJ=r"(?:a|an|the|this|these|those|that|it|them|one|each|every|all|any|some|its|their|our|your|short|brief|concise|clear|generali[sz]ed|generic|new|plain|simple|single|final|joiner facing|"+_TEXTN[3:-1]+r")"
_LEAD=r"(?:^|[.;:!?,]\s*|\s-+\s*)(?:(?:please|just|now|first|then|simply|kindly|next)\s+)*"
_PRODUCER=r"(?:drafters?|writers?|authors?|editors?|reviewers?|summari[sz]ers?|copywriters?|preparers?|compilers?|(?:next|later|following|subsequent|downstream)\s+(?:drafting\s+)?(?:stage|step|version|draft|drafter|writer|pass|iteration|revision)s?|drafting\s+(?:stage|step|team)s?)"
_MODAL=r"(?:should|must|shall|needs? to|has to|have to|is to|are to|ought to|(?:is|are) (?:required|expected|asked) to|will need to)"
_W=r"(?:[a-z0-9'-]+\s+)"
_GUIDE=tuple(re.compile(p) for p in (
    # (i) addresses a producer
    r"(?:^|[.;:!?]\s*)(?:(?:a\s+)?(?:note|message|instructions?|guidance|reminder)\s+)?(?:for|to|attention|attn)\s*:?\s*(?:the\s+|any\s+|a\s+|our\s+|each\s+)?"+_PRODUCER+r"(?![a-z0-9])\s*(?:[,:;]|-+|$)",
    r"(?<![a-z0-9])(?:for|to)\s+(?:the|any|a|our|each)\s+(?:drafters?|writers?|editors?|summari[sz]ers?|copywriters?)(?![a-z0-9])(?!\s+(?:team|teams|group|community|guild|role|roles|function|pool)(?![a-z0-9]))",
    r"(?<![a-z0-9])(?:whoever|whomever|anyone who|anybody who|someone who|the person who|whichever (?:stage|step|agent|model|person|team|writer|drafter))\s+(?:next\s+|later\s+|then\s+)?(?:"+_AVF[3:-1]+r"|picks? (?:this|it) up|takes? (?:this|it) (?:on|over))(?![a-z0-9])",
    r"(?<![a-z0-9])(?:for|to|by)\s+(?:the\s+)?(?:next|later|following|subsequent|downstream)\s+(?:drafting\s+)?(?:stage|step|version|draft|drafter|writer|pass|iteration|revision)s?(?![a-z0-9])",
    r"(?<![a-z0-9])(?:next|later|following|subsequent|downstream)\s+(?:drafting\s+)?(?:stage|step|version|draft|pass|iteration|revision)s?\s*(?:[:,]|-+\s|"+_MODAL+r"(?![a-z0-9])|will(?![a-z0-9])|can(?![a-z0-9])|may(?![a-z0-9]))",
    r"(?<![a-z0-9])(?:(?:next|later|following|subsequent|downstream|drafting|writing|authoring|summary|summari[sz]ing|harvest|closeout|final)\s+(?:stage|step|pass|agent|model|engine|skill)s?|drafters?|the (?:writer|model|assistant|agent|llm))(?![a-z0-9])\W+"+_W+r"{0,8}?"+_AVF+r"(?![a-z0-9])",
    r"(?<![a-z0-9])(?:you|your team)\s+(?:"+_MODAL[3:-1]+r"|will|can|could|may|might)\s+"+_W+r"{0,2}?(?:"+_TV[3:-1]+r"|"+_MV[3:-1]+r")(?![a-z0-9])",
    r"(?:^|[.;:!?,]\s*)you\s+(?:"+_TV[3:-1]+r"|"+_MV[3:-1]+r")(?![a-z0-9])",
    # (ii) a directive to produce or transform text
    _LEAD+_TV+r"\s+"+_OBJ+r"(?![a-z0-9])",
    _LEAD+_MV+r"\s+"+_W+r"{0,8}?(?:"+_TEXTN[3:-1]+r"|into)(?![a-z0-9])",
    r"(?<![a-z0-9])"+_MODAL+r"\s+(?:be\s+)?"+_W+r"{0,2}?(?:"+_TVF[3:-1]+r")(?![a-z0-9])",
    r"(?<![a-z0-9])"+_MODAL+r"\s+"+_W+r"{0,2}?"+_MV+r"\s+"+_W+r"{0,8}?(?:"+_TEXTN[3:-1]+r"|into)(?![a-z0-9])",
    r"(?<![a-z0-9])(?:to be|still to be|yet to be|should be|must be|needs to be|has to be|is to be|are to be)\s+"+_MVP+r"\s+"+_W+r"{0,6}?(?:from|into|using|based on|out of)(?![a-z0-9])",
    # (iii) placeholders and drafting rules
    r"(?<![a-z0-9])(?:to be|still to be|yet to be|will be|should be|must be|needs to be)\s+"+_TVP+r"(?![a-z0-9])",
    r"(?<![a-z0-9])(?:drafting|preparation|writer'?s?|editor'?s?|stage|hand ?off)\s+(?:note|guidance|instructions?|brief)(?![a-z0-9])",
    r"(?<![a-z0-9])(?:note|instructions?|guidance)\s+(?:for|to)\s+(?:the\s+)?(?:drafters?|writers?|editors?|next|later|following|downstream|drafting)(?![a-z0-9])(?!\s+(?:team|teams|group|community|guild|function)(?![a-z0-9]))",
    r"(?<![a-z0-9])do not (?:quote|reconstruct|paraphrase|copy|reproduce|repeat)(?![a-z0-9])",
    r"(?<![a-z0-9])(?:using|from|use)\s+(?:only\s+)?the (?:title|category|citations?|evidence ids?)(?:\s+(?:and|or)\s+(?:the\s+)?(?:title|category|citations?|evidence ids?))*\s+only(?![a-z0-9])",
    r"(?<![a-z0-9])using only the (?:title|category|citations?|evidence)(?![a-z0-9])",
    r"^\W*(?:tbd|tbc|todo|to do|placeholder)(?![a-z0-9])"))
# "into a <...> summary/lesson/note/overview" is a directive on its own, except inside a relative clause of a noun
# phrase ("Template that turns raw notes into a status summary"), which describes what the asset does.
_INTO=re.compile(r"(?<![a-z0-9])into\s+(?:a|an|one|the|this|that|its|their)\s+"+_W+r"{0,5}?(?:summary|lesson|note|overview|abstract|synopsis|paragraph|description|narrative|write ?up|blurb|brief|recap|statement)(?![a-z0-9])")
_RELCL=re.compile(r"(?<![a-z0-9])(?:that|which)\s+(?:also\s+|automatically\s+)?[a-z]+s(?![a-z0-9])")
# Imperative mood (round 3): a sentence that opens with a base-form verb, not an article, determiner, numeral, pronoun,
# a noun-phrase head (Checklist, Template, Guide, Summary ...), a participle ("Used by ...", "Covering ...") or a
# third-person verb ("Covers ..."), followed by its object ("Use the ...", "Populate the ...", "Refer to ..."), and
# naming a text product anywhere in the sentence, is a directive to whoever writes the text.
_NONVERB={"a","an","the","this","these","those","that","its","their","our","your","his","her","my","each","every","all","any","some","no","one","two","three","four","five","it","they","we","he","she","i","you","there","here","of","for","by","with","from","in","on","at","to","as","and","or","but","if","when","how","what","why","where","who","which","is","are","was","were","be","been","has","have","had","can","will","would","should","must","may","might","not","also","only","new","first","final","internal","external","reusable","cleared","approved","standard","weekly","monthly","daily","annual","quarterly","key","short","brief","concise","patient","client","onboarding","access","governance","steering","status","project","programme","program","delivery","risk","data","quick","step","joiner","team","practice","sample","example"}
_NOUNHEAD={"checklist","checklists","template","templates","guide","guides","guidance","summary","summaries","lesson","lessons","playbook","playbooks","overview","overviews","note","notes","outline","outlines","draft","drafts","reference","handbook","manual","pattern","framework","toolkit","kit","deck","document","report","record","log","list","map","matrix","plan","catalogue","catalog","library","glossary","briefing","brief","process","procedure","policy","template","case","set","pack","collection","cheat","sheet","form","agenda","minutes","digest","narrative","section","paragraph","description","write","writeup","primer","walkthrough","explainer","faq","q","tips","starter","intro","introduction"}
_PARTICLE={"the","a","an","this","these","those","that","it","them","each","every","all","any","your","our","its","their","to","up","in","out","through","together","down","over","with","only","both","one"}
_TEXTPROD=re.compile(r"(?<![a-z0-9])(?:summary|summaries|overviews?|lessons?|notes?|write ?ups?|write-ups?|narratives?|briefs?|sections?|drafts?|paragraphs?|descriptions?|digests?)(?![a-z0-9])")
_NOUNSUF=("tion","sion","ment","ness","ance","ence","ity","ship","ism","ology","ics","ary","ory")
_PARTICIPLE={"written","made","built","done","taken","given","drawn","kept","held","run","won","shown","known","seen","set","put","read"}
def _imperative(t):
    for snt in re.split(r"[.;!?\n]+",t):
        w=re.findall(r"[a-z0-9]+(?:'[a-z]+)?",snt)
        while w and w[0] in {"please","just","then","now","simply","kindly","next","also"}: w=w[1:]
        if len(w)<2: continue
        v=w[0]
        if (v in _NONVERB or v in _NOUNHEAD or v in _PARTICIPLE or v.isdigit() or v.endswith(("ing","ed")+_NOUNSUF)
                or (v.endswith("s") and not v.endswith(("ss","us","is")))): continue
        if w[1] in _PARTICLE and _TEXTPROD.search(" ".join(w[1:])): return True
    return False
def stage_guidance(v):
    """True when a supplied description is guidance addressed to a drafter or later stage, or a placeholder (#2.6)."""
    t=norm(unwithheld(v) or "") if isinstance(v,str) else ""
    if not t: return False
    if any(p.search(t) for p in _GUIDE) or _imperative(t): return True
    for m in _INTO.finditer(t):
        a=max(t.rfind(c,0,m.start()) for c in ".;!?")+1
        if not _RELCL.search(t[a:m.start()]): return True
    return False
def check_asset(a,w,released=False):  # knowledge-reuse-rules.md #1.4
    for k in ("asset_id","title","description","category","confidentiality_permission","citation","engagement_id","client_name","matter_id")+(("clearance_state",) if released else ()): field(a,k,"str",w,nullable=True)
    field(a,"tags","strlist",w,nullable=True); field(a,"evidence_ids","list",w,nullable=True); field(a,"review_required","bool",w,nullable=True); field(a,"confidence","num01",w)  # evidence_ids is read as a list (unattributed_names); its items are identifiers (check_ids)
def check_lesson(l,w):
    for k in ("cluster_id","category","drafting_guidance","confidentiality_permission","citation","engagement_id","client_name","matter_id"): field(l,k,"str",w,nullable=True)
    for k in ("tags","evidence_citations"): field(l,k,"strlist",w,nullable=True)
    field(l,"evidence_ids","list",w,nullable=True)  # read as a list (unattributed_names); its items are identifiers (check_ids)
    for k in ("rewrite_required","review_candidate"): field(l,k,"bool",w,nullable=True)
    field(l,"confidence","num01",w)
def adapt(p):
    x=load_json(p,"closeout input")
    if not isinstance(x,dict) or x.get("contract_version")!=CLOSE: raise InputError(f"closeout adapter expected a JSON object with contract_version {CLOSE} (supplied value not repeated); fail closed")
    kr=x.get("knowledge_record")
    if not kr or not isinstance(kr,dict): raise InputError("closeout adapter requires top-level knowledge_record object; fail closed")
    # Required members are present: an absent list is refused, never read as an empty one (knowledge-reuse-rules.md #1.4).
    if "released_assets" not in x or not isinstance(x["released_assets"],list) or any(not isinstance(r,dict) for r in x["released_assets"]): raise InputError("closeout adapter requires top-level released_assets[] of objects (an absent member is not an empty list); fail closed")
    ra=x["released_assets"]
    for key in ("reusable_assets","lessons"):
        if key not in kr or not isinstance(kr[key],list) or any(not isinstance(r,dict) for r in kr[key]): raise InputError(f"closeout adapter requires knowledge_record.{key}[] of objects (an absent member is not an empty list); fail closed")
    W="upstream/closeout"; check_timestamps(x,W)  # carried timestamps are format-checked (confidentiality-and-ethical-wall-rules.md #1.3)
    check_ids(x,W)  # every identifier member (asset_id, cluster_id, record_id, evidence_ids, engagement_id, matter_id ...) is a string or null of the identifier shape (#1.3)
    check_names(x,W)  # no title, client or affiliate name is in an engine label form (#1.3)
    field(kr,"record_id","str",W+".knowledge_record",nullable=True)  # read by unattributed_names: type-checked like every field a reader uses (#1.3)
    for i,r in enumerate(ra): check_asset(r,f"{W}.released_assets[{i}]",True)
    for i,r in enumerate(kr["reusable_assets"]): check_asset(r,f"{W}.knowledge_record.reusable_assets[{i}]")
    for i,r in enumerate(kr["lessons"]): check_lesson(r,f"{W}.knowledge_record.lessons[{i}]")
    # Records keyed by ID are never indexed last-wins: released assets by asset_id; reusable assets and lessons share
    # the knowledge_id space they are published under (confidentiality-and-ethical-wall-rules.md #1.3).
    dup=duplicate_ids([(ra,"asset_id","released_assets")],W)+duplicate_ids([(kr["reusable_assets"],"asset_id","knowledge_record.reusable_assets"),(kr["lessons"],"cluster_id","knowledge_record.lessons")],W)
    if dup: raise InputError("closeout records keyed by ID must be unique (values not repeated): "+"; ".join(dup)+"; fail closed")
    # The closed engagement's identity block may be absent or null (it is then unattributed: see unattributed_names).
    ce=field(x,"engagement","obj",W,nullable=True,default={})
    for k in ("engagement_id","client_name","matter_id","title"): field(ce,k,"str",W+".engagement",nullable=True)  # every field a reader uses (OWNER) is type-checked (#1.3)
    return {"knowledge_record":kr,"released_assets":ra,"engagement":ce,"provenance":x.get("provenance",x.get("run_metadata",{}))}
def check_scope(s):
    need(isinstance(s,dict),f"scope input must be a JSON object, got {type(s).__name__}; fail closed")
    if s.get("contract_version")!=CONTRACT_VERSION: raise InputError(f"expected contract {CONTRACT_VERSION} in scope input")
    field(s,"scope_summary","obj","scope",required=True); check_contract(s,"scope","scope")  # confidentiality-and-ethical-wall-rules.md #1.3
    check_hold_evidence(s,"scope")  # holds are cumulative: a placeholder, escalation or held status without its hold is refused (#1.4)
# A Closeout record belongs to the closed engagement, and a released-asset clearance to the reusable asset with its
# asset_id: both must state the same subject, compared canonically (confidentiality-and-ethical-wall-rules.md #1.5).
OWNER={"engagement_id":canon_id,"client_name":canon_person,"matter_id":canon_id}
ASSET=dict(OWNER,title=canon_text)
def nb(*vs):
    """The first non-blank string: a rendered display string is never blank (contract $defs/knowledge_item, #1.3)."""
    return next((v for v in vs if isinstance(v,str) and v.strip()),None)
def rel(scope,item):
    ss=scope["scope_summary"]
    over=sorted(toks(item.get("title") or "","" if stage_guidance(item.get("description")) else item.get("description") or ""," ".join(item.get("tags") or []),item.get("category") or "") & toks((scope.get("joiner") or {}).get("role") or ""," ".join(ss.get("objectives",[]))," ".join(ss.get("in_scope",[]))," ".join(ss.get("deliverables",[]))))  # guidance is never scored (#2.6)
    return (round(min(.99,.55+.08*len(over)),2) if over else .4),over
# ---------------------------------------------------------------- one other-client identity set (#3.3)
# Every stage screens with the same identity set, derived here from every identity source: the wall register, the
# Closeout's closed engagement and record-level identities, names in Closeout records that state no identity, and a
# staffing input for a different client or engagement. knowledge_match, wall_check, access_checklist and the pre-render
# check all call other_client_terms, so a name screened at one stage is screened at every stage after it.
def closeout_records(raw):
    """[(path, record)] for every Closeout record a reader uses, from the adapted (unmodified) Closeout."""
    kr=raw["knowledge_record"]
    return [(f"released_assets[{i}]",r) for i,r in enumerate(raw["released_assets"])]+[(f"knowledge_record.reusable_assets[{i}]",r) for i,r in enumerate(kr["reusable_assets"])]+[(f"knowledge_record.lessons[{i}]",r) for i,r in enumerate(kr["lessons"])]
RECORD_TEXT=("title","description","category","drafting_guidance","citation","evidence_citations")  # every record value that renders or travels as text
RECORD_IDS=("asset_id","cluster_id","record_id")
HARVEST_OWN={"id","ids"}  # "evidence IDs" in drafting guidance is vocabulary, not a name
def attributed(r,ce):
    """A Closeout record is attributed when it, or the closed engagement it belongs to, states a usable client
    identity: its client is then compared and screened by name (#3.3)."""
    return bool(identity_parts(r.get("client_name")) or identity_parts(ce.get("client_name")))
def lower_vocab(*docs):
    """Words this engagement's own scope document writes in lowercase: ordinary vocabulary, so an ALL-CAPS or
    capitalised use of them in a Closeout record that states no client names no one. Read from the scope only, so a
    Closeout record cannot clear a name by also writing it in lowercase (#3.2)."""
    out=set(); st=list(docs)
    while st:
        v=st.pop()
        if isinstance(v,dict): st.extend(v.values())
        elif isinstance(v,list): st.extend(v)
        elif isinstance(v,str): out|=set(re.findall(r"(?<![A-Za-z0-9])[a-z][a-z0-9]*(?![A-Za-z0-9])",unwithheld(v)))
    return out
def people_words(s):
    """Words of this engagement's own people (joiner, roster, proposed staffing, exclusions, points of contact): a
    colleague named in a Closeout record is not another client (#3.3)."""
    j=s.get("joiner") or {}; L=lambda k:[x for x in (s.get(k) or []) if isinstance(x,dict)]
    vs=[j.get("person"),j.get("point_of_contact")]+[r.get(k) for r in L("team_roster") for k in ("person","point_of_contact")]+[r.get("candidate_name") for r in L("proposed_staffing")]+[r.get("person") for r in L("staffing_exclusions")]
    return words(*(unwithheld(v) for v in vs if isinstance(v,str)))
def unattributed_names(raw,mine,own,vocab=frozenset()):
    """Identities named in the text of Closeout records that state no client (no engagement block, a null engagement
    or a null record-level client_name): with no stated client to compare, every proper-noun run and matter-like ID in
    such a record's text that is not this engagement's own identity or people, generic or ordinary vocabulary
    (lower_vocab, people_words) or a Closeout record ID is another party, so the text is withheld wherever it travels and held (#3.3). Read from the UNMODIFIED Closeout."""
    ce=raw["engagement"]; recs=closeout_records(raw); kr=raw["knowledge_record"]
    ids=[v for _,r in recs for k in RECORD_IDS for v in [r.get(k)] if isinstance(v,str) and v.strip()]+[v for _,r in recs for v in (r.get("evidence_ids") or []) if isinstance(v,str) and v.strip()]+[v for v in [kr.get("record_id")] if isinstance(v,str) and v.strip()]
    rx=re.compile("|".join(r"(?<![A-Za-z0-9])"+re.escape(v.strip())+r"(?![A-Za-z0-9])" for v in sorted(set(ids),key=len,reverse=True)),re.I) if ids else None
    own_ids={canon_id(mine.get(k)) for k in ("engagement_id","matter_id") if isinstance(mine.get(k),str)}-{""}
    names=[]
    for _,r in recs:
        if attributed(r,ce): continue
        for k in RECORD_TEXT:
            for v in (r.get(k) if isinstance(r.get(k),list) else [r.get(k)]):
                if not isinstance(v,str) or not v.strip(): continue
                v=unwithheld(v); v=rx.sub(" ",v) if rx else v
                names+=[m for m in safety_text._MATTER_ID_RE.findall(v) if canon_id(m) not in own_ids]
                names+=proper_names(v,own|HARVEST_OWN|vocab)
    return names
def staffing_names(staffing,mine,own):
    """A staffing input for a different client or engagement is another client's: the identity parts that differ from
    this engagement's, read from the UNMODIFIED staffing input as scope_digest reads them (#1.2, #3.3)."""
    st=load_json(staffing,"staffing input"); scope_digest.validate_staffing(st)
    reng=st.get("engagement") or {}  # absent: unstated, held by scope_digest (HOLD-STAFFING-ENGAGEMENT-MISMATCH); it names no one
    return [x for k_ in ("client_name","engagement_id") for x in other_parts(reng.get(k_),unwithheld(mine.get(k_)) if isinstance(mine.get(k_),str) else mine.get(k_),k_,own)]
def other_client_terms(s,closeout,register,staffing):
    """(terms, identity holds): the one other-client identity set every stage screens with, derived from every
    identity source for the document s's engagement (#3.3). Identity holds are raised by knowledge_match only."""
    raw=adapt(closeout); ce=copy.deepcopy(raw["engagement"]); rid=closeout_records(raw)
    mine=s.get("engagement") or {}; own=own_words(s)
    # The closed engagement is usually another client: its name and IDs never reach this pack. Its identity comes from
    # the raw Closeout: a client_name that also trips the wire still names the client, and only the parts that are not
    # this engagement's own become terms (identity_parts). The scope's engagement identity is carried state: a closed
    # engagement for a different client is another client's in full, so its engagement ID is screened even when it
    # equals the carried one (#1.4, #3.3). Each record may state its own client, engagement or matter (OWNER).
    cdiff=bool(other_parts(ce.get("client_name"),mine.get("client_name"),"client_name"))
    names=[x for k_ in ("client_name","engagement_id") for x in (identity_parts(ce.get(k_)) if cdiff and k_=="engagement_id" else other_parts(ce.get(k_),mine.get(k_),k_,own))]
    names+=[x for _,r in rid for k_ in OWNER for x in other_parts(r.get(k_),mine.get(k_),k_,own)]
    names+=unattributed_names(raw,mine,own,lower_vocab(s)|people_words(s))+staffing_names(staffing,mine,own)
    terms=client_terms(names,own)
    # Every other client named in the wall register (#2.1, #3.3).
    terms+=[t for t in register_terms(register,mine,own) if t[0] not in {x[0] for x in terms}]
    # A structured identity (Closeout engagement or record, register client_name/matter_id) that trips the wire and
    # names no usable identity holds anyway: the other-client screen cannot be confirmed (#3.3).
    ih=[other_hold(f"upstream/closeout.engagement.{k_}",ce.get(k_),ENGINE) for k_ in ("client_name","engagement_id") if identity_unreadable(ce.get(k_))]+[other_hold(f"upstream/closeout.{w}.{k_}",r.get(k_),ENGINE) for w,r in rid for k_ in ("client_name","engagement_id") if identity_unreadable(r.get(k_))]+register_identity_holds(register,ENGINE)
    return terms,ih
def knowledge_rows(doc):
    """[(field path, values)] for the knowledge items in the order the pack renders them: title, ID, summary and every
    supplied citation share one line ("- title (id) [...] - summary Source: citations"), so they are read together (#4.5)."""
    return [(f"prior_knowledge_candidates[{i}]",rendered_values(x.get("title"),x.get("knowledge_id"),x.get("summary"),*rendered_citations(x.get("citations")))) for i,x in enumerate(doc.get("prior_knowledge_candidates") or []) if isinstance(x,dict)]
def foreign_exclusion(lh,exc,key,where):
    """A Closeout record that names a different engagement, client or matter than the closed engagement is another
    subject's: it is held and excluded by its position, never by its supplied ID (a shape-valid ID is still that
    record's own text), and none of its fields reach any output (confidentiality-and-ethical-wall-rules.md #1.5, #3.3)."""
    lh.append(link_hold(where,ENGINE)); exc.append({key:None,"reason":"linked_record_subject_mismatch","citation":f"{where}; {LINK_CITATION}"})
def derive(s,closeout,register,ts,staffing):
    """matched.json for a scope document (scope_digest's output, or a carried scope proved equal to it), the Closeout
    record, the wall register, this stage's run timestamp and the staffing input. Later stages re-run it (rederive, #1.4)."""
    adopt_trust(s)  # from the declaration lines scope_digest accepted, never a carried list (#1.4, #4.4)
    # Both upstream documents are screened whole (every string, holds included) and redacted before use (#4.1, #4.3).
    s,sh=screen_upstream(s,"scope",ENGINE)
    raw=adapt(closeout)
    c,own_h=screen_upstream(raw,"upstream/closeout",ENGINE,raw=True); rels={canon_id(x.get("asset_id")):x for x in c["released_assets"] if x.get("clearance_state") in STATES and canon_id(x.get("asset_id")) and not is_withheld(x.get("asset_id"))}  # joined by canon_id (#1.3); a blank or withheld ID joins nothing (#4.3)
    inc=[]; exc=[]; unw=[]; und=[]; kr=c["knowledge_record"]; ceng=c.get("engagement") or {}; lh=[]  # subjects compared on screened text only (#4.3)
    for i,asset in enumerate(kr["reusable_assets"]):
        aid=asset.get("asset_id")
        if not canon_id(aid) or is_withheld(aid) or canon_id(aid) not in rels: exc.append({"asset_id":aid,"reason":"not_in_released_assets","citation":"knowledge-reuse-rules.md #2.1"}); continue
        if subjects_differ(asset,rels[canon_id(aid)],ASSET) or subjects_differ(asset,ceng,OWNER) or subjects_differ(rels[canon_id(aid)],ceng,OWNER):
            foreign_exclusion(lh,exc,"asset_id",f"upstream/closeout.knowledge_record.reusable_assets[{i}]"); continue
        perm=asset.get("confidentiality_permission",rels[canon_id(aid)].get("confidentiality_permission"))
        if perm is not None and perm!=PERM: exc.append({"asset_id":aid,"reason":"confidentiality_permission_not_internal_reuse","citation":"knowledge-reuse-rules.md #2.2"}); continue
        # Review status first (#2.3): a pending item never renders its supplied description, only the fixed
        # title-and-citation-only statement. A cleared item renders its description unless it is guidance addressed to
        # a drafter or later stage, which is not written content: that item is excluded (#2.6, as lessons are, #2.4).
        rs=review_status(asset,rels[canon_id(aid)]); desc=asset.get("description")
        if isinstance(desc,str) and desc.strip() and (rs!=CLEARED or stage_guidance(desc)): und.append({"knowledge_id":aid,"title":nb(asset.get("title"),rels[canon_id(aid)].get("title"),f"Released knowledge asset {aid}"),"description":desc,"citations":[nb(asset.get("citation"),"knowledge_record.reusable_assets"),nb(rels[canon_id(aid)].get("citation"),"released_assets")],"path":f"upstream/closeout.knowledge_record.reusable_assets[{i}].description"})
        if rs==CLEARED and stage_guidance(desc): exc.append({"asset_id":aid,"reason":DESCRIPTION_IS_GUIDANCE,"citation":"knowledge-reuse-rules.md #2.6"}); continue
        score,over=rel(s,asset)
        if score<.5: exc.append({"asset_id":aid,"reason":"below_relevance_floor","citation":"knowledge-reuse-rules.md #3.1"}); continue
        inc.append({"knowledge_id":aid,"title":nb(asset.get("title"),rels[canon_id(aid)].get("title"),f"Released knowledge asset {aid}"),"summary":nb(desc,NO_DESCRIPTION) if rs==CLEARED else PENDING_SUMMARY,"relevance_score":score,"matched_terms":over,"clearance_state":rels[canon_id(aid)].get("clearance_state"),"confidentiality_permission":perm or "release_candidate_state","review_status":rs,"source":"adapter:closeout-governed.knowledge_record","confidence":min(asset.get("confidence",.9),rels[canon_id(aid)].get("confidence",.9)),"citations":[nb(asset.get("citation"),"knowledge_record.reusable_assets"),nb(rels[canon_id(aid)].get("citation"),"released_assets"),"knowledge-reuse-rules.md #1.3,#2.1,#2.2,#3.1"]})
    for i,lesson in enumerate(kr["lessons"]):
        lp=lesson.get("confidentiality_permission")
        if not canon_id(lesson.get("cluster_id")) or is_withheld(lesson.get("cluster_id")): exc.append({"lesson_id":lesson.get("cluster_id"),"reason":"no_lesson_id","citation":"knowledge-reuse-rules.md #1.4"}); continue  # every knowledge item carries its identity (contract $defs/knowledge_item)
        if subjects_differ(lesson,ceng,OWNER): foreign_exclusion(lh,exc,"lesson_id",f"upstream/closeout.knowledge_record.lessons[{i}]"); continue
        if lp is not None and lp!=PERM: exc.append({"lesson_id":lesson.get("cluster_id"),"reason":"confidentiality_permission_not_internal_reuse","citation":"knowledge-reuse-rules.md #2.2"}); continue
        if lesson.get("rewrite_required") is not False: exc.append({"lesson_id":lesson.get("cluster_id"),"reason":"rewrite_required_or_unknown","citation":"knowledge-reuse-rules.md #2.4"}); continue
        # The governed Closeout lesson carries no finished lesson text: drafting_guidance is an instruction to the
        # Closeout drafting step, never lesson content, so it is never rendered or scored. A lesson with no written text
        # is not reusable content and is excluded with its citations (knowledge-reuse-rules.md #2.4).
        cites=[x for x in (lesson.get("evidence_citations") or [])]+[lesson.get("citation")]
        exc.append({"lesson_id":lesson.get("cluster_id"),"reason":LESSON_NOT_WRITTEN,"citation":"; ".join(("knowledge-reuse-rules.md #2.4",)+rendered_values(*cites))})
        unw.append({"lesson_id":lesson.get("cluster_id"),"category":lesson.get("category"),"drafting_guidance":lesson.get("drafting_guidance"),"citations":[x for x in cites if isinstance(x,str)],"path":f"upstream/closeout.knowledge_record.lessons[{i}]"})
    inc=redact(inc)  # flagged Closeout text never travels (confidentiality-and-ethical-wall-rules.md #4.3)
    # The one other-client identity set (other_client_terms): Closeout engagement and record identities, names in
    # unattributed Closeout records, a different staffing client and every client in the wall register (#3.3).
    terms,ih=other_client_terms(s,closeout,register,staffing)
    # Upstream scope holds are supplied content: screened for other-client names and steering text (#3.3, #4.3).
    if ih: s.setdefault("escalations",[]).append(other_escalation(len(ih)))
    up,uh=screen_holds(s.get("holds",[]),terms,ENGINE,"scope.holds"); holds=dedup_holds(up+sh+own_h+uh+ih+lh)
    if lh: s.setdefault("escalations",[]).append(link_escalation(len(lh)))
    if sh or own_h: s.setdefault("escalations",[]).append(upstream_escalation(len(sh)+len(own_h)))
    if any(hold_is(h,"HOLD-OTHER-CLIENT-") for h in uh): s.setdefault("escalations",[]).append(other_escalation(sum(hold_is(h,"HOLD-OTHER-CLIENT-") for h in uh)))
    # An excluded unwritten lesson's citations still travel and its record is Closeout text, so the record (ID, category,
    # guidance, citations) is screened beside the items, then dropped: a name or split instruction in it holds, and the
    # excluded entry's citation carrying any of it is withheld (#2.4, #3.3, #4.5). An asset description that is never
    # rendered (a pending item's, or cleared stage guidance) is Closeout text too: it is read with its item's title, ID and
    # citations, so a claim split across it and a citation holds and the citation is withheld (#2.3, #2.6).
    s["excluded_lesson_records"]=unw; s["unrendered_descriptions"]=und
    if terms:
        s["prior_knowledge_candidates"]=inc; s["excluded_items"]=exc; s,oh=screen_other(s,terms,ENGINE,"matched."); inc=s.pop("prior_knowledge_candidates"); exc=s.pop("excluded_items")
        if oh: holds=dedup_holds(holds+oh); s.setdefault("escalations",[]).append(other_escalation(len(oh)))
    # Each knowledge item is read as the pack renders it - title, ID, summary and supplied citations on one line, item
    # after item - so a claim split across a summary and its citation is held here and withheld everywhere (#4.5).
    def rows(d): return knowledge_rows(d)+[(x["path"],rendered_values(x.get("category"),x.get("lesson_id"),x.get("drafting_guidance"),*rendered_citations(x.get("citations")))) for x in d.get("excluded_lesson_records") or [] if isinstance(x,dict)]+[(x["path"],rendered_values(x.get("title"),x.get("knowledge_id"),x.get("description"),*rendered_citations(x.get("citations")))) for x in d.get("unrendered_descriptions") or [] if isinstance(x,dict)]
    s["prior_knowledge_candidates"]=inc; s["excluded_items"]=exc; s,rh=screen_rendered(s,rows,"matched knowledge items"); inc=s.pop("prior_knowledge_candidates"); exc=s.pop("excluded_items"); s.pop("excluded_lesson_records",None); s.pop("unrendered_descriptions",None)
    if rh: holds=dedup_holds(holds+rh); s.setdefault("escalations",[]).append(rendered_escalation("knowledge item",len(rh)))
    status="ready" if inc and not holds else "hold" if holds else "empty"
    if not inc and not holds: s.setdefault("escalations",[]).append("No released, permissioned prior-knowledge records matched the engagement (knowledge-reuse-rules.md #2.1,#2.2,#3.1)")
    s["prior_knowledge_candidates"]=inc; s["knowledge_digest"]={"status":status,"items":inc,"excluded_items":exc,"source":ENGINE,"confidence":.92 if inc else .7,"citation":"knowledge-reuse-rules.md #1.1-#3.2"}; s["holds"]=holds; s.setdefault("provenance",{}).setdefault("engines",[]).append(f"knowledge_match/{VERSION}"); s["provenance"]["generated_at"]=ts
    s=bind_withheld(settle_trust(s),"matched",ENGINE); check_contract(s,"matched","matched"); return s  # the document written is held to the same contract (#1.3)
def rederive_scope(doc,raw_dir,staffing,roster,where):
    """scope_digest's document for the raw inputs, under the run parameters the carried document states (#1.4)."""
    return scope_digest.derive(raw_dir,staffing,roster,*run_parameters(doc,where))
def rederive(doc,raw_dir,staffing,roster,closeout,register,ts,where):
    """The matched document the raw inputs give: scope_digest then this engine, re-run whole (#1.4)."""
    return derive(reread(rederive_scope(doc,raw_dir,staffing,roster,where),"re-derived scope"),closeout,register,ts,staffing)
def main():
    ap=ArgParser()
    for k in ("--scope","--raw-dir","--staffing","--confirmed-roster","--closeout","--wall-register","--out","--generated-at"): ap.add_argument(k,required=True)
    a=ap.parse_args(); ts=require_iso_z(a.generated_at)
    s=load_json(a.scope,"scope input"); check_scope(s)
    same_document(s,rederive_scope(s,a.raw_dir,a.staffing,a.confirmed_roster,"scope input"),"scope input")  # every field equals scope_digest's re-derivation from the raw inputs (#1.4)
    dump_json(a.out,derive(s,a.closeout,a.wall_register,ts,a.staffing),"matched output")
if __name__=="__main__": guard(main)
