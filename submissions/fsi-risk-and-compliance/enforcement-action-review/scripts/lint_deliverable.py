#!/usr/bin/env python3
"""Mechanical marker and ID lint for Risk & Compliance deliverables.

Runs the house-rules.md checks that a reader can miss but a script cannot:
marker tokens and NOT DETERMINED without their IDs, gap sentences without an
ID, D-bullets without the NOT DETERMINED token, date cells without a value or
NOT FOUND marker, interpreted Exemption cells, unlabelled day counts, hedge
words, footer counts that differ from the lists, IDs that do not resolve,
non-existence claims ("has not been published"), Bites on dates without their
DATES citation, day counts anchored on "today", absence bullets without a
leading NOT FOUND, source conflicts without a GAP bullet, version spans to
confirm, a DRAFT analysed with no control of record named, entity words
inside any rule, preamble or DATES quote while the definitions are not
retrieved, SAR wording beyond the fixed decline, binding-on-you phrasing,
unquoted month and year forms, plain-English remedy paraphrases, private
names in captions, URLs and rejected people-search hits, grouped rejected
hits, D-bullets joining two provisions, cited bullets of the wrong
marker type, sufficiency claims, statements that the firm has a deficiency
or violation (the firm's bare name and "our ... program" included), a
respondent's conduct stated as fact, possible person names beside a SAR,
vendor rating or approval wording ("low risk", "clean opinion", "Approved",
"tier 2", "minor exception") in a vendor-risk-review deliverable, and
screening, PEP, rating and guilt wording ("is not a PEP", "not on the SDN
list", "high risk", "committed fraud") in a kyc-research-pack record.

Usage:
    python scripts/lint_deliverable.py <artifact.md|.txt|.docx> [--reply reply.md]
                                       [--searches searches.md] [--skill <skill>]

The skill is taken from --skill, else from the artifact's title line (for
example "THIRD-PARTY RISK REVIEW" or "KYC / EDD PUBLIC-SOURCE RESEARCH
RECORD"), else from the skills/<skill>/scripts folder this script runs from.
The vendor wording check (E33) runs only for vendor-risk-review and the KYC
wording check (E34) only for kyc-research-pack.

The search log has one line per request and one per document a search returned:
    REQ | <source or call> | ok | failed | not attempted
    HIT | <query or route> | <document name> | used
    HIT | <query or route> | <document name> | rejected (Gn)
    HIT | <query or route> | <document name> | set aside   (unrelated by title, unopened)
    HIT | <query or route> | <document name> | duplicate (Gn)   (another copy, shares Gn)
A used hit must be named in the artifact; a rejected hit needs its own
'GAP - scope mismatch, not a candidate: <document>' G-bullet. NOT RETRIEVED
and 'did not return' need a failed REQ line. The register's 'Owners
unidentified: n' count is checked against its Owner column, numbering-gap
rows excluded.

Exit code 0: no ERROR lines. Exit code 1: fix every ERROR and run again.
Exit code 2: a usage error, or a named file that cannot be read or is empty.
CHECK lines are gap-phrase sentences with no (Gn)/(Dn): cite the ID, or leave
the sentence only if it is one of the exceptions in house-rules.md section 4
(a fact sentence about what a source contains, a decline, a statement of what
the skill never does, verbatim quoted text, a column heading or summary label).

Standard library only. Reads the files named on the command line and nothing
else; writes nothing.
"""

import html
import os
import re
import sys
import zipfile

DASH = r"\s*[-–—]\s*"
MARKERS = [
    ("NOT FOUND", r"NOT FOUND"),
    ("NOT RETRIEVED", r"NOT RETRIEVED"),
    ("NEEDS FEED", r"NEEDS FEED"),
    ("NOT LEGIBLE", r"NOT LEGIBLE"),
    ("UNRESOLVED MATCH", r"UNRESOLVED MATCH"),
    ("PENDING CODIFICATION", r"PENDING CODIFICATION"),
    ("PROPOSED", r"PROPOSED" + DASH + r"not in force"),
    ("DRAFT", r"(?<!Status: )DRAFT" + DASH + r"not approved"),
    ("AS OF", r"AS OF(?=\s+\d)"),
    # a GAP marker is followed by its dash, a colon, or its ID; "GAP ANALYSIS" in a title is not one
    ("GAP", r"(?<![A-Za-z])GAP(?=\s*(?:[-–—:]|\(G\d))"),
]
MARKER_RE = re.compile("|".join("(?P<m%d>%s)" % (i, p) for i, (_, p) in enumerate(MARKERS)))
ND_RE = re.compile(r"NOT DETERMINED")
ID_RE = re.compile(r"(?<![A-Za-z0-9])([GD])(\d+)(?![0-9])")
RANGE_RE = re.compile(r"(?<![A-Za-z0-9])([GD])(\d+)\s*(?:to|-|–)\s*\1?(\d+)(?![0-9])")
BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+\.)?\s*\**\s*([GD])(\d+)\s*\**\s*(?:[-–—:.]|\s)")
COUNT_RE = re.compile(
    r"(NOT FOUND|NOT RETRIEVED|NEEDS FEED|NOT LEGIBLE|UNRESOLVED MATCH|PENDING CODIFICATION|"
    r"PROPOSED(?:\s*[-–—]\s*not in force)?|DRAFT(?:\s*[-–—]\s*not approved)?|"
    r"AS OF|GAP|NOT DETERMINED)\s*:\s*(\d+)\s+items?\b")
D_INTRO = "Decisions outstanding (each NOT DETERMINED below cites its own Dn):"

GAP_PHRASES = [
    "not retrieved", "retrieval not attempted", "not opened", "did not return",
    "returned nothing", "not found", "no record", "not located", "none located",
    "none retrieved", "not provided", "not configured", "not stated", "states no",
    "not verified", "unverified", "not performed", "not checked", "not covered",
    "out of scope", "incomplete", "omitted", "extract", "excerpt", "unidentified",
    "does not mention", "rejected", "nothing responsive", "does not address",
    "did not cover", "could not locate", "not mapped", "undated", "skipped",
    "withheld", "not needed", "left unopened", "none found", "no candidate",
    "conflicting", "discrepancy", "inconsistent", "differs from", "disagree",
    "could not open", "couldn't open", "could not read", "not in the documents searched",
    "not consulted", "not reviewed", "not searched", "unavailable", "unable to",
]
NONEXIST_RE = re.compile(
    r"\b(has not (?:yet )?been (?:published|issued|finali[sz]ed|adopted|released)|"
    r"hasn't (?:yet )?been (?:published|issued|finali[sz]ed|adopted|released)|"
    r"(?:is|are) not yet (?:published|final|issued|in the Federal Register)|"
    r"not yet (?:been )?(?:published|issued|finali[sz]ed)|yet to be (?:published|issued|finali[sz]ed)|"
    r"no final rule (?:exists|has been|is available)|there is no final rule|"
    r"does not exist|doesn't exist|do not exist|never (?:been )?published|"
    r"in no (?:instrument|rule|regulation|source|document|official document)s?|"
    r"appears? nowhere|nowhere in)\b", re.I)
SAR_RE = re.compile(r"\bSARs?\b")
HEDGED_RE = re.compile(r"\bwhether\b|\bnever\b|\bnot\b|\bno\b|NOT DETERMINED|\(D\d+|owner confirms|\?\s*$", re.I)
SUFFICIENCY_RE = re.compile(
    r"\b(?:satisf(?:y|ies|ied)|fully (?:answers|addresses|responds to)|demonstrates? compliance|"
    r"(?:is|are) sufficient|sufficiently (?:addresses|evidences)|evidences? (?:the|this|item \S+) request|"
    r"meets the request|responsive and complete|answers the request|fully responsive|"
    r"(?:is|are) responsive to (?:the|this|item)|complete response to|adequately (?:evidences?|addresses|"
    r"demonstrates?|supports?)|(?:is|are) adequate evidence|(?:is|are) adequate for|fully covers|"
    r"covers the request|closes (?:the|this) item|"
    # "these minutes demonstrate that item 2 is covered", "the report covers item 6 in full"
    r"(?:demonstrates?|shows?|proves?|confirms?|establish(?:es)?) that (?:item|request|requirement|"
    r"this item|this request|it)\b[^.;]{0,25}?\b(?:is|are) (?:fully )?(?:covered|met|satisfied|addressed|"
    r"answered|closed|complete|evidenced)|covers (?:item|request) \S+ (?:in full|fully|completely)|"
    r"meets (?:the )?(?:examiner'?s? )?(?:request|requirement))\b", re.I)
_ACCUSED = (r"(?:a |an |any )?(?:material |significant |serious )?(?:deficien\w*|violat\w*|"
            r"non-?compliant|noncompliance|non-compliance|in violation|out of compliance|compliance gap|"
            r"gap in compliance|control failure|failed to|breached|"
            r"gaps? in (?:its|our|their|the (?:firm|bank)'s))")
_VERB = r"(?:has|have|had|is|are|was|were|shows?|showed|lacks?)"
SELF_ACCUSE_RE = re.compile(
    r"\b(?:the firm|the bank|we|our (?:bank|firm|institution|company))\s+" + _VERB + r"\s+" + _ACCUSED + r"\b|"
    # "our transaction monitoring program has a deficiency"
    r"\bour (?:[\w-]+ ){0,4}(?:program|programme|controls?|process|procedures?|policy|framework|function)\s+"
    + _VERB + r"\s+" + _ACCUSED + r"\b|"
    r"\bwe (?:failed to|violated|breached|are not compliant)\b|"
    # comparing the firm to the respondent: "we have the same gap"
    r"\b(?:has|have|shares?|shows?) the same (?:gap|weakness|deficiency|failure|problem|issue|shortcoming)\b",
    re.I)
# the firm or another named entity: "Northwind Bank, N.A. has a deficiency", or a bare name: "Northwind has"
NAMED_ACCUSE_RE = re.compile(
    r"\b((?:[A-Z][\w&'-]*\.?,? ){0,4}(?:Bank|Bancorp|Trust|Credit Union|Financial|Inc\.?|LLC|"
    r"Corp\.?|Corporation|N\.A\.|Company))\s+" + _VERB + r"\s+" + _ACCUSED + r"\b")
BARE_ACCUSE_RE = re.compile(r"\b((?:[A-Z][\w&'-]+ ){0,2}[A-Z][\w&'-]+)\s+" + _VERB + r"\s+" + _ACCUSED + r"\b")
BARE_STOP = {"This", "That", "It", "There", "Which", "Each", "The", "A", "An", "Item", "Theme", "Row",
             "Section", "Policy", "Procedure", "Nothing", "No", "None", "Whether", "If",
             # a vendor review paraphrasing the auditor: "Exception shows a control failure"
             "Exception", "Exceptions", "Deviation", "Deviations", "Finding", "Findings", "Management",
             "Auditor", "Report", "Control", "Test", "Testing", "Response", "Opinion", "Gap"}
# the outline's disclaimer phrasings, and nothing broader: "that" is required, except where the
# accused subject follows the phrase directly ("This memo does not say we failed to file",
# "Nothing here suggests the firm has", "None of this means the firm has"); no turn ("but",
# "however") may sit between the phrase and the subject
_NO_TURN = r"(?:(?!\b(?:but|however|although|though|yet|still)\b)[^.;:!?])"
_SAY = r"(?:say|find|mean|state|conclude|show|suggest)"
_NOTHING = (r"nothing (?:here|in (?:this|the) \w+) (?:suggests|says|means|finds|indicates|shows)|"
            r"none of (?:this|these|it|that|the above) (?:means|suggests|says|shows|indicates|finds)")
DISCLAIMER_RE = re.compile(
    r"(?:\b(?:(?:is|are) not a finding|no finding|not a conclusion|makes no finding|is not a statement|"
    r"without (?:finding|concluding|suggesting)|(?:does|do|did) not " + _SAY + r"|doesn't " + _SAY + r"|"
    + _NOTHING + r")\s+that\s+" + _NO_TURN + r"{0,40}"
    r"|\b(?:(?:does|do|did) not|doesn't|don't) " + _SAY + r"\s+|\b(?:" + _NOTHING + r")\s+"
    r"|\bwhether\s+" + _NO_TURN + r"{0,40})$", re.I)
# a negation that governs the wording right after it: "gives no risk rating", "is not a clean
# result", "I can't say it is safe to approve"; idioms such as "no doubt" do not negate
NEG_IDIOM_RE = re.compile(r"\bno (?:doubt|question)\b|\bnot (?:surprisingly|only|just|least)\b", re.I)
NEG_BEFORE_RE = re.compile(
    r"\b(?:no|not|never|without|cannot|can't|won't|isn't|aren't|doesn't|don't|neither|nor)\s+"
    r"(?:(?!(?:but|however|yet|and|so|though|although)\b)[\w'-]+\s+){0,3}$", re.I)
RESPONDENT_RE = re.compile(r"\b(?:the )?respondents?(?:'s)?\b|\bthe (?:peer|penali[sz]ed) bank\b", re.I)
# "the bank" in a read-across is the respondent unless the sentence reports a missing input
THE_BANK_RE = re.compile(r"\bthe bank\b", re.I)
SKILLS = ("enforcement-action-review", "exam-request-response", "kyc-research-pack",
          "policy-gap-analysis", "reg-change-triage", "vendor-risk-review")
SKILL_ALIASES = {"enforcement": SKILLS[0], "exam": SKILLS[1], "kyc": SKILLS[2], "policy-gap": SKILLS[3],
                 "gap": SKILLS[3], "reg-change": SKILLS[4], "triage": SKILLS[4], "vendor": SKILLS[5]}
# the outline title lines (and short forms of them) that name the deliverable
TITLE_RES = [
    ("vendor-risk-review", re.compile(r"third[- ]party risk review|vendor (?:risk )?review|"
                                      r"vendor due diligence|SOC ?[123] (?:vendor )?review", re.I)),
    ("kyc-research-pack", re.compile(r"\bKYC\b|\bEDD\b[^.\n]{0,40}\b(?:record|pack|research)|"
                                     r"public-source research record", re.I)),
    ("enforcement-action-review", re.compile(r"enforcement action read-across|\bread[- ]across\b", re.I)),
    ("exam-request-response", re.compile(r"response to .{0,60}request list|\brequest list\b|"
                                         r"first-day letter", re.I)),
    ("policy-gap-analysis", re.compile(r"policy-to-regulation gap analysis|\bpolicy gap\b|"
                                       r"\bgap analysis\b|\bgap memo\b", re.I)),
    ("reg-change-triage", re.compile(r"regulatory change triage|\breg(?:ulatory)? change\b", re.I)),
]
APPROVAL_RE = re.compile(
    r"\b(?:low|lower|medium|moderate|elevated|high|higher|minimal|acceptable|limited|little)[- ]risk\b|"
    r"\b(?:poses?|presents?|carry|carries) (?:little|minimal|low|limited|no (?:material|significant)) risk\b|"
    r"\brisk (?:rating|score|tier|level|grade)\s*(?:is|was|of|:|=|would be|should be)\s*\**"
    r"(?:low|medium|moderate|high|elevated|minimal|\d)\b|\brated (?:as )?(?:low|medium|moderate|high)\b|"
    r"\bclean (?:SOC ?[123] )?(?:opinion|report|result|bill of health|audit)\b|\bclean SOC ?[123]\b|"
    r"\b(?:is|looks|came back|was) clean\b|"
    r"\b(?:safe|fine|ok|okay|good|clear|cleared) to (?:approve|onboard|use|rely on|proceed|go ahead|"
    r"contract|sign)\b|\bgo ahead (?:and|with) (?:onboard\w*|approv\w*|sign\w*|contract\w*|us(?:e|ing))\b|"
    r"\b(?:we )?(?:recommend|suggest|advise)(?:s|ed)? (?:approv\w+|onboard\w*)\b|"
    r"\b(?:approve|approved) (?:the )?vendor\b|\bacceptable\b(?!\s+use\b)|"
    r"\b(?:minor|immaterial|insignificant) (?:exceptions?|deviations?|findings?|issues?)\b|"
    r"\btier\s*[:=]?\s*(?:[1-4]|one|two|three|four|I{1,3}|IV)\b|\bno adverse findings\b|"
    r"(?:^|[:|]\s*)[\W_]*approved[\W_]*$|"
    r"\b(?:decision|recommendation|outcome|status|approval)\s*:\s*\**approved\b", re.I)
# the vendor outline's required sentence (vendor-outline.md section 6), quoted or not
VENDOR_REQUIRED_RE = re.compile(r"A clean opinion with unadopted (?:or undetermined )?complementary "
                                r"user[- ]entity controls is not a clean result\.?", re.I)
# a question echoed before a decline: "**Is it safe to approve?** I can't make that call."
QUESTION_RE = re.compile(r"[^.!?]*\?[*_\"”')\]]*")
AFFIRM_RE = re.compile(r"^\W*(?:yes|yep|yeah|it is|absolutely|correct|definitely|certainly)\b", re.I)
VERBATIM_COL_RE = re.compile(r"verbatim|quot|auditor comment", re.I)
# kyc-research-pack record-outline.md "Wording that must not appear"
_NOT_SCREEN = r"(?!\s+(?:screen|screening|check|determination|status|list|database|flag))"
KYC_FORBID = [
    (re.compile(r"\b(?:is|are|was|were)\s+not\s+(?:an?\s+)?(?:PEPs?|politically exposed persons?)\b"
                + _NOT_SCREEN, re.I), "PEP status stated as a conclusion", False),
    (re.compile(r"\b(?:is|are|was|were)\s+(?:an?\s+)?(?:PEPs?|politically exposed persons?)\b"
                + _NOT_SCREEN, re.I), "PEP status stated as a conclusion", True),
    (re.compile(r"\bnot\s+(?:on|listed on|named on|included on|in)\s+(?:the\s+|any\s+)?(?:OFAC\s+|UN\s+|EU\s+|"
                r"HMT\s+|OFSI\s+|consolidated\s+)?(?:SDN|sanctions?|OFAC|watch)\s*lists?\b|"
                r"\b(?:is|are|was|were)\s+not\s+(?:sanctioned|designated|a sanctioned \w+|"
                r"subject to (?:any )?sanctions)\b|"
                r"\b(?:cleared|passed|clear of)\s+(?:the\s+)?(?:sanctions|OFAC|SDN|watch\s*list)\b|"
                r"\bno\s+(?:sanctions|SDN|OFAC|watch\s*list)\s+(?:hits?|matches?|concerns?)\b|"
                r"\bscreening\s+(?:was\s+|has\s+been\s+|is\s+)?(?:completed|complete|clear|passed)\b", re.I),
     "sanctions or screening result stated", False),
    (re.compile(r"\b(?:is|are|was|were|be|rated|rates?|classified|considered|deemed|assessed|treated)\s+"
                r"(?:as\s+)?(?:an?\s+)?(?:high|higher|medium|moderate|low|lower|elevated|minimal)[- ]risk\b"
                r"(?!\s+(?:sector|industr|jurisdiction|countr|geograph|business|product|activit|area|region|"
                r"typolog|indicator|factor|corridor|categor|list|third countr))|"
                r"\b(?:high|medium|moderate|low|elevated)[- ]risk\s+(?:rating|score|profile)\b|"
                r"\brisk\s+(?:rating|score|tier|level|grade)\s*(?:is|was|of|:|=|would be|should be)\s*\**"
                r"(?:high|medium|moderate|low|elevated|minimal|\d)\b", re.I),
     "risk rating", False),
    (re.compile(r"\bcommitted\s+(?:[\w-]+\s+){0,2}?(?:fraud|money laundering|bribery|corruption|embezzlement|"
                r"tax evasion|a crime|crimes|an offen[cs]e|offen[cs]es)\b|"
                r"\b(?:is|are|was|were)\s+(?:a\s+)?(?:guilty|fraudster|criminal|money launderer)\b", re.I),
     "guilt stated as fact", True),
    (re.compile(r"\bno adverse findings\b|\b(?:the\s+)?(?:subject|customer|counterparty|entity|individual|"
                r"client)\s+(?:is|was|came back|looks)\s+clean\b", re.I), "absence of adverse information stated",
     False),
    (re.compile(r"\brecommend\w*\s+(?:filing|that\s+\w+\s+file|a SAR|an? STR|exit\w*|onboard\w*|restrict\w*|"
                r"offboard\w*|terminat\w*|declin\w*|approv\w*)", re.I), "filing or onboarding recommendation",
     False),
]
# a source named for the statement: "according to", "the registry lists", "was convicted"
ATTRIB_RE = re.compile(r"\baccording to\b|\bas stated\b|\bper (?:the|a|its)\b|\b(?:states?|stated|reports?|"
                       r"reported|lists?|listed|identif(?:y|ies|ied)|describes?|described|"
                       r"records?|recorded)\b|alleg|accus|convict|\bpleaded\b|\bplea\b|\bcourt\b|judg(?:e)?ment|"
                       r"\bjury\b|\bverdict\b|indict", re.I)
# a named bank as the actor ("Peer Bank failed to"); case-sensitive so "the bank" stays out
RESP_NAME_RE = re.compile(r"\b(?:[A-Z][\w&'-]*\s){1,3}(?:Bank|Bancorp|Credit Union)(?:,? N\.A\.)?\b")
# a regulator or central bank is never the respondent: "The Reserve Bank did not give a date"
REGULATOR_IN_RE = re.compile(r"\b(?:Reserve|Federal|Central|Bundesbank|Home Loan|World|Export-Import|"
                             r"Swiss National|Development|Settlements)\b")
REGULATOR_AFTER_RE = re.compile(
    r"\s+of\s+(?:England|Canada|Japan|France|Italy|Spain|Korea|Mexico|Israel|Thailand|Jamaica|Ghana|"
    r"Uganda|Tanzania|Zambia|Botswana|Namibia|Mauritius|Russia|Greece|Portugal|Finland|Latvia|Lithuania|"
    r"Estonia|Slovenia|Slovakia|Albania|Ireland|Lebanon|Sierra Leone|Papua New Guinea|Guyana|"
    r"International Settlements|the [A-Z]\w+)\b")
FIRM_CONDUCT_RE = re.compile(r"\s+(?:has |have |had )?(?:failed to|violated|breached|ignored|neglected|"
                             r"concealed|falsified|misled)\b", re.I)
# a missing input to this review, not the respondent's conduct
INFO_GAP_RE = re.compile(
    r"\bdid not (?:provide|give|supply|state|include|specify|produce|send|share|return|list|name|identify|"
    r"submit)\b|\bhad no\b[^.;]{0,80}?\b(?:located|found|retrieved|supplied|provided|on file|in (?:the|this) "
    r"(?:search|register|export|review|files?|documents?))\b", re.I)
REVIEW_CUE_RE = re.compile(r"\b(?:to|for|in) (?:this|the) review\b|\bsearch\b|\blocated\b|\bretrieved\b|"
                           r"\bsupplied\b|\bexport\b", re.I)
FIRM_LINE_RE = re.compile(r"^\W*(?:Firm|Institution|Our firm|Prepared for|Client|Read[- ]across (?:for|to))"
                          r"\b[^:|\n]{0,60}(?::|\|)\s*(.+)$", re.I)
RESP_LINE_RE = re.compile(r"^\W*Respondents?\b[^:|\n]{0,20}(?::|\|)\s*(.+)$", re.I)
# a neutral sentence about the document itself: "The excerpt does not name the respondent"
NEUTRAL_DOC_RE = re.compile(
    r"\b(?:excerpt|order|document|paragraph|passage|text|filing|¶\s*\d+)\s+(?:does not|doesn't|did not|"
    r"names? no|gives? no|states? no)\b|\b(?:does not|doesn't) (?:name|say|state|give|identify|specify|"
    r"mention|describe|quantify)\b", re.I)
# a clause whose subject is the document: "the order caused no change here"
DOC_SUBJECT_RE = re.compile(r"^\W*(?:the |this |that )?(?:excerpt|order|document|paragraph|passage|text|"
                            r"filing|memo|review|record|search|¶\s*\d+)\b", re.I)
CLAUSE_SPLIT_RE = re.compile(r"[,;:()]|\s[-\u2013\u2014]\s|\s(?:and|but|while|whereas|although|though|because|so)\s",
                             re.I)
CONDUCT_RE = re.compile(r"\b(?:charged|failed(?: to)?|violated|misled|engaged in|ignored|did not|deceived|"
                        r"overcharged|assessed|concealed|falsified|knowingly|neglected|allowed|permitted|"
                        r"lacked|had no|accumulated|maintained an? (?:ineffective|inadequate)|"
                        r"resulting in|caused|let|(?:went|go|gone|left) unreviewed|unreviewed|"
                        r"had an? (?:backlog|failure|weakness))\b", re.I)
ALLEGED_RE = re.compile(r"alleg|the order (?:states|says|finds|found|requires|describes)|found that|"
                        r"admit|according to the order|the (?:bureau|agency|board|occ|cfpb|tribunal) found", re.I)
NAME_PAIR_RE = re.compile(r"\b([A-Z][a-z]+(?: [A-Z]\.)? [A-Z][a-z]+)\b")
NAME_STOP = set("""Suspicious Activity Report Reports Bank Secrecy Act Federal Register Compliance Officer
Office Financial Crimes Enforcement Network Customer Due Diligence Risk Assessment Program Policy Procedure
Committee Board Exam Examination Letter First Day The This That Consent Order Section Item Theme Control
Case Reference Annual Review Quality Assurance Sample Training Records Team Unit Department Director
Senior Management Internal Audit Data Minimisation Minimization Not Found Open Items Determinations
Outstanding Decisions Owner Chief Deputy Head Group Holdings Trading Services Capital Securities""".split())
CITATION_RE = re.compile(r"\b\d+\s+(?:CFR|U\.S\.C\.?)\s*(?:§\s*)?\d|FR Doc|\b\d+ Fed\. ?Reg\.|¶\s*\d|§\s*\d")
SAR_LAW_RE = re.compile(r"confidential|prohibit|forbid|forbidden|\bmay not\b|\bcannot\b|\bmust not\b|"
                        r"\brequires?\b|\blaw\b|statut|tipping|5318|1020\.320|\bdisclos|\bmeans\b|"
                        r"\bbars?\b|\bbarred\b", re.I)
SAR_DECLINE_RE = re.compile(r"^\W*[^.]{0,120}withheld under data minimi[sz]ation\.?\W*$", re.I)
BINDING_RE = re.compile(
    r"\b(?:will|would|does|shall) require (?:you|us|the firm|the bank|your (?:bank|firm|institution))\b|"
    r"\brequires? (?:you|us)\b|"
    r"\byou (?:must|will need to|will have to|are required to|have to) (?:comply|implement|document|"
    r"record|update|verify|collect|obtain|file|adopt|change|meet)\b|"
    r"\bapplies to (?:you|us|your)\b|\bbinds (?:you|us|your)\b|"
    r"\byour (?:bank|firm|institution|company) (?:must|will need to|is required to|has to)\b", re.I)
PERIOD_FORM_RE = re.compile(
    r"\b\d+-(?:months?|years?)\b|\b(?:one|two|three|five|six|seven|ten|twelve|eighteen|"
    r"twenty-four|thirty-six)-(?:months?|years?)\b|\bwithin \d+ (?:months?|years?)\b|"
    r"\bevery \d+ (?:months?|years?)\b", re.I)
REMEDY_RE = re.compile(
    r"\b(?:stop|cease|end|quit|halt) (?:charging|collecting|using|engaging|doing|making|imposing|"
    r"assessing|marketing|enrolling|opening)\b|\bno longer (?:charge|collect|impose|assess|use)\b|"
    r"\b(?:refund|pay back|repay|reimburse) (?:the |these |its |affected )?(?:customers|consumers|fees|"
    r"borrowers)\b|\bagreed to (?:stop|cease|refund|pay back|repay|fix)\b|"
    # a remedy restated in plain words instead of quoted: "the Bank must submit a better program"
    r"\b(?:must|has to|have to|is required to|are required to|agreed to|will need to|needs to)\s+"
    r"(?:submit|implement|hire|retain|pay|adopt|enhance|improve|clear|remediate|reduce|eliminate|"
    r"fix|overhaul|strengthen)\b|"
    r"\brequires? (?:the )?(?:respondent|bank|company|firm|institution) to (?![\"“\s]*\")", re.I)
ENFORCEMENT_CUE_RE = re.compile(r"consent order|cease[- ]and[- ]desist|the order alleges|respondent|"
                                r"enforcement action", re.I)
CAPTION_RE = re.compile(r"(?<![\[\w])((?:[A-Z][a-z]+\.? ){0,3}[A-Z][a-z]+),? v\.? (?=[A-Z\[])")
CAPTION_ENTITY_RE = re.compile(
    r"\b(Inc|LLC|L\.L\.C|Corp|Corporation|Co|Company|Bank|N\.A|Ltd|Limited|Union|CUSO|Trust|Group|"
    r"Holdings|Association|Partners|LP|LLP|PLC|Fund|Services|Financial|Capital|Securities|"
    r"United|States?|People|Commonwealth|Commission|Bureau|Department|Board|Agency|Authority|"
    r"Government|City|County|Republic|Federal|National)\b")
URL_RE = re.compile(r"https?://([^/\s)>\]|]+)(/[^\s)>\]|]*)?", re.I)
PEOPLE_SITE_RE = re.compile(
    r"whitepages|spokeo|peoplefinder|truepeoplesearch|fastpeoplesearch|beenverified|radaris|"
    r"mylife|intelius|instantcheckmate|peoplelooker|thatsthem|zabasearch|linkedin\.com|facebook\.com|"
    r"instagram\.com|twitter\.com|x\.com|legacy\.com|obituar", re.I)
REJECTED_CUE_RE = re.compile(r"not a candidate|scope mismatch|UNRESOLVED MATCH|rejected", re.I)
PROVISION_RE = re.compile(r"\b\d{1,4}\.\d{1,4}(?:\([a-z0-9]+\))*|§\s*\d[\w.()-]*|"
                          r"\b\d+ U\.S\.C\.? ?§? ?\d+[\w()]*", re.I)
TODAY_RE = re.compile(r"\b(?:days?|weeks?|months?)\s+(?:from|after|before|since)\s+today\b", re.I)
ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
SPAN_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\s*(?:to|through|until|-|–|—)\s*\d{4}-\d{2}-\d{2}\b")
SPAN_WORDS_RE = re.compile(r"in force|in effect|effective|span|supersed|was current|governed|"
                           r"applied from|prior version|v\d+\.\d+", re.I)
# two sources disagreeing; a rule's own word ("resolve any discrepancy") is not a conflict
CONFLICT_RE = re.compile(r"\bconflicting (?:sources|figures|values|dates)\b|\bconflict between\b|"
                         r"\bdiffers? from (?:the|its|that|this)\b|\bdiscrepanc\w* between\b|"
                         r"\binconsistent with (?:the )?(?:minutes|workbook|log|report|letter|record)|\bdisagree", re.I)
ABSENCE_HEAD_RE = re.compile(r"does not say|not say|absent|silent|states no|not stated", re.I)
ABSENCE_LINE_RE = re.compile(r"\bstates no\b|\bdoes not (?:say|state|give|specify|split|identify|"
                             r"quantify|break down|name)\b|\bsilent on\b", re.I)
LIST_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
QUOTE_RE = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')
ENTITY_RE = re.compile(r"\b(covered financial institutions?|financial institutions?|institutions?|"
                       r"banks?|firms?|brokers?|dealers?)\b", re.I)
RULE_COL_RE = re.compile(r"prior text|new text|obligation|requirement|exemption|rule text|"
                         r"text relied on|actually requires|quote|binds whom|trigger|condition|"
                         r"bites on|dates|value|ladder|compliance", re.I)
FIRM_DOC_RE = re.compile(r"\bpolicy\b|\bprocedure\b|\bminutes\b|\bworkbook\b|\bmemo\b|\bemail\b|"
                         r"\bletter\b|\bSOC 2\b", re.I)
RULE_CUE_RE = re.compile(r"\bCFR\b|FR Doc|preamble|Fed\. ?Reg|Federal Register|\bDATES\b|"
                         r"the (?:prior|final|proposed) rule", re.I)
GAP_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in GAP_PHRASES) + r")", re.I)
HEDGE_RE = re.compile(
    r"\b(probably|presumably|likely|unlikely|appears to|appear to|seems|seem to|"
    r"would likely|should be)\b", re.I)
DAYS_RE = re.compile(r"\b\d+\s+days?\b|\b\d+-days?\b", re.I)
BITES_COL_RE = re.compile(r"bites on|compliance date|comply by|must comply|applies from|"
                          r"when it bites", re.I)
DAYS_OK_RE = re.compile(r"\b\d+\s+(calendar|business)\s+days?\b|\b\d+-(calendar|business)-days?\b", re.I)
NEG_MARKER_RE = re.compile(
    r"\bnot\s+(?:a\s+|an\s+)?(NOT FOUND|NOT RETRIEVED|NEEDS FEED|PENDING CODIFICATION|"
    r"UNRESOLVED MATCH|GAP\b|DRAFT\b|PROPOSED\b)")
DATE_COL_RE = re.compile(
    r"date|due|bites on|effective|published|deadline|version|approval|period requested|"
    r"comment (?:deadline|period|date|due)|compliance", re.I)
# template lines that name markers as labels: "Rows not scored (markers):  n  <- NOT RETRIEVED / GAP"
# and "  NOT RETRIEVED — reg text      2" (label, two or more spaces, a count)
SUMMARY_LABEL_RE = re.compile(r"^\W*[A-Za-z][^:|]{0,60}?(?::\s*|\s{2,})\d+\b(?!-\d)")
LEAD_LABEL_RE = re.compile(r"^[A-Za-z][\w /()-]{0,30}:\s*(?=[A-Z])")
MANDATED_RE = re.compile(r"none - defining provision not retrieved|\(not scored\)|"
                         r"not performed: no rule text relied on", re.I)
REJECTED_HEAD_RE = re.compile(r"^\W*Rejected candidates\W*(?:\(G\d+(?: to G\d+)?\))?\W*$", re.I)
FIELD_COL_RE = re.compile(r"^\W*(?:field|attribute|item|label|check|element|row)\W*$", re.I)
# outline-required scope and coverage labels that state a definition, not a shortfall
SCOPE_LABEL_RE = re.compile(r"^\W*(?:Out of scope|In scope|Nature|Subject set)\s*:", re.I)
DATE_BAD_RE = re.compile(
    r"^\W*(none stated|none|undated|n/?a|not applicable|tbd|unknown|not dated|no date|"
    r"in force|-|—|–)?\W*$|none stated|undated|\bn/a\b|not applicable", re.I)
MARKER_COL_RE = re.compile(r"marker|status|candidate|coverage|evidence|owner|determination|"
                           r"location|retrieved|disposition", re.I)
EXEMPT_COL_RE = re.compile(r"exemption|exception|proviso", re.I)
EXEMPT_OK_RE = re.compile(r'^\W*(["“‘]|none stated in|NOT DETERMINED)', re.I)
INTERP_RE = re.compile(
    r"\b(applies only|only to the|only the .{0,40}element|limited to|does not exempt|"
    r"exempts? only|is exempt|are exempt|not exempt|carves? out|excludes?)\b", re.I)
SCOPE_OK_RE = re.compile(r"\b(scope ok|population ok)\b", re.I)


# ---------------------------------------------------------------- loading
def read_docx(path):
    """Text of a .docx, tables as markdown rows. Regex only: no XML parser is used."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")

    def ptext(p):
        return html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p)))

    out = []
    for m in re.finditer(r"<w:tbl>.*?</w:tbl>|<w:p[\s>].*?</w:p>|<w:p\s*/>", xml, re.S):
        block = m.group(0)
        if block.startswith("<w:tbl>"):
            first = True
            for tr in re.findall(r"<w:tr[\s>].*?</w:tr>", block, re.S):
                cells = [" ".join(ptext(p) for p in re.findall(r"<w:p[\s>].*?</w:p>", tc, re.S)).strip()
                         for tc in re.findall(r"<w:tc[\s>].*?</w:tc>", tr, re.S)]
                out.append("| " + " | ".join(cells) + " |")
                if first:
                    out.append("|" + "---|" * len(cells))
                    first = False
            out.append("")
        else:
            out.append(ptext(block))
    return out


def read_lines(path):
    if path.lower().endswith(".docx"):
        return read_docx(path)
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


# ---------------------------------------------------------------- helpers
def strip_quotes(s):
    """Blank out verbatim quoted text so it is not linted."""
    s = re.sub(r'"[^"\n]*"', lambda m: '"' + " " * (len(m.group(0)) - 2) + '"', s)
    s = re.sub(r"“[^”\n]*”", lambda m: " " * len(m.group(0)), s)
    return s


def sentences(text):
    # no split after abbreviations that end a token mid-sentence ("Smith v. CUSO", "No. 12")
    parts = re.split(r"(?<=[.!?])(?<!\bv\.)(?<!\bvs\.)(?<!\bNo\.)(?<!\bInc\.)(?<!\bCo\.)(?<!\bCorp\.)"
                     r"(?<!\bLtd\.)(?<!\bU\.S\.)(?<!\bFed\.)(?<!\bReg\.)\s+(?=[A-Z*\"(\[`“])", text)
    return [p for p in parts if p.strip()]


def cited_ids(text):
    ids = set()
    for kind, a, b in RANGE_RE.findall(text):
        a, b = int(a), int(b)
        if 0 < b - a < 500:
            ids.update("%s%d" % (kind, n) for n in range(a, b + 1))
    for kind, n in ID_RE.findall(text):
        ids.add("%s%s" % (kind, n))
    return ids


def is_table(line):
    return line.strip().startswith("|") and line.strip().count("|") >= 2


def is_sep(line):
    return re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", line) is not None and "-" in line


def split_cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def short(s, n=140):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 3] + "..."


def marker_name(m):
    return [MARKERS[i][0] for i in range(len(MARKERS)) if m.group("m%d" % i)][0]


def lead_text(s):
    return re.sub(r"^[\s*_`>\-•]+", "", s)


def negated(prefix):
    """True when a negation or a disclaimer phrase governs the words that follow the prefix."""
    p = NEG_IDIOM_RE.sub(" ", prefix)
    return bool(NEG_BEFORE_RE.search(p) or DISCLAIMER_RE.search(p))


def clause_of(t, pos):
    start, end = 0, len(t)
    for m in CLAUSE_SPLIT_RE.finditer(t):
        if m.end() <= pos:
            start = m.end()
        elif m.start() > pos:
            end = m.start()
            break
    return t[start:end]


def blank(t, rx):
    return rx.sub(lambda m: " " * len(m.group(0)), t)


def detect_skill(docs, wanted=None):
    """The skill whose checks apply: --skill, else the artifact title, else this script's folder."""
    if wanted:
        return wanted, "--skill"
    lines = [l for l in docs[0][1] if l.strip()][:8] if docs else []
    for line in lines:
        hits = [(m.start(), name) for name, rx in TITLE_RES for m in [rx.search(line)] if m]
        if hits:
            return min(hits)[1], "the artifact title"
    parts = os.path.normpath(os.path.abspath(__file__)).split(os.sep)
    if len(parts) >= 3 and parts[-2] == "scripts" and parts[-3] in SKILLS:
        return parts[-3], "the script folder"
    return None, "not detected"


# ---------------------------------------------------------------- lint
class Linter:
    def __init__(self, skill=None):
        self.skill = skill
        self.firms = set()  # the user's firm, from a "Firm: <name>" header line
        self.respondents = set()  # names on a "Respondent" line or row
        self.tables = []  # (header, rows)
        self.rowtext = {}  # "artifact:12" -> the whole table row, for row-level exceptions
        self.errors = []
        self.checks = []
        self.warns = []

    def err(self, code, where, msg, text):
        self.errors.append("ERROR %s %s %s: %s" % (code, where, msg, short(text)))

    def chk(self, where, msg, text):
        self.checks.append("CHECK C1 %s %s: %s" % (where, msg, short(text)))

    def warn(self, code, where, msg, text):
        self.warns.append("WARN  %s %s %s: %s" % (code, where, msg, short(text)))

    def run(self, docs):
        glist, dlist = {}, {}
        segments = []  # (where, text, in_table, header)
        has_d_intro = False
        footer_counts = []
        bullets = []  # (where, line, heading) for list lines that are not G/D bullets
        heading = ""

        for name, lines in docs:
            header = None
            for i, raw in enumerate(lines, 1):
                where = "%s:%d" % (name, i)
                line = raw.rstrip()
                if not line.strip():
                    header = None
                    continue
                if line.strip().startswith(D_INTRO) or D_INTRO in line:
                    has_d_intro = True
                    continue
                for m in COUNT_RE.finditer(line):
                    footer_counts.append((where, m.group(1), int(m.group(2)), line))
                bm = BULLET_RE.match(line) if not is_table(line) else None
                if bm:
                    key = bm.group(1) + bm.group(2)
                    book = glist if bm.group(1) == "G" else dlist
                    if key in book:
                        self.err("E4", where, "%s defined twice (first at %s)" % (key, book[key][0]), line)
                    book[key] = (where, line)
                    continue
                if is_table(line):
                    if is_sep(line):
                        continue
                    cells = split_cells(line)
                    if header is None:
                        header = cells
                        self.tables.append((header, []))
                        continue
                    self.tables[-1][1].append(cells)
                    self.rowtext[where] = line
                    for ci, cell in enumerate(cells):
                        col = header[ci] if ci < len(header) else ""
                        segments.append(("%s [col %s]" % (where, col or ci + 1), cell, True, col))
                    continue
                header = None
                if line.lstrip().startswith("#"):
                    heading = line
                    continue
                if re.fullmatch(r"\s*\*\*[^*]+\*\*\s*", line):
                    heading = line
                if LIST_RE.match(line):
                    bullets.append((where, line, heading))
                for s in sentences(line):
                    segments.append((where, s, False, ""))
            heading = ""

        self.segments = segments
        for _, lines in docs:
            for line in lines:
                for rx, book in ((FIRM_LINE_RE, self.firms), (RESP_LINE_RE, self.respondents)):
                    fm = rx.match(line)
                    if fm:
                        book.update(re.sub(r"^The\s+", "", n.group(0)).strip()
                                    for n in RESP_NAME_RE.finditer(fm.group(1)))
        self.firms -= self.respondents
        self.check_lists(glist, dlist, has_d_intro)
        self.check_segments(segments, glist, dlist)
        self.check_ids(segments, glist, dlist)
        self.check_counts(footer_counts, glist, dlist)
        self.check_scope_ok(segments, glist)
        self.check_content(segments, bullets, glist, docs)
        self.check_owner_count(docs)
        return glist, dlist

    def check_owner_count(self, docs):
        """'Owners unidentified: n' counts register rows with no owner, never G-bullets."""
        best = None
        for header, rows in self.tables:
            cols = [i for i, h in enumerate(header)
                    if re.fullmatch(r"\W*(suggested\s+)?owner\W*", h, re.I)]
            if cols and (best is None or len(rows) > len(best[1])):
                best = (cols[0], rows)
        if best is None:
            return
        ci, rows = best

        def numbering_gap(r):
            # an item number the list skips: every cell after the first is a marker or blank
            rest = [c for c in r[1:] if c.strip() not in ("", "-", "—", "–")]
            return re.search(r"numbering gap", " ".join(r), re.I) or (
                rest and all(MARKER_RE.match(lead_text(c)) for c in rest))

        keys = {r[0].strip() for r in rows
                if ci < len(r) and re.match(r"\W*NOT FOUND", r[ci]) and r[0].strip()
                and not numbering_gap(r)}
        for name, lines in docs:
            for i, line in enumerate(lines, 1):
                m = re.search(r"Owners? (?:unidentified|not identified)\W*\s*(\d+)", line, re.I)
                if m and int(m.group(1)) != len(keys):
                    self.err("E21", "%s:%d" % (name, i), "owner count says %s but %d register rows "
                             "have no owner (%s): count rows, not G-bullets"
                             % (m.group(1), len(keys), ", ".join(sorted(keys)) or "none"), line)

    def check_searches(self, hits, glist, docs):
        """Walk the search log: every hit is used in the artifact or has its own rejection bullet."""
        def norm(s):
            return re.sub(r"\s+", " ", s.replace("\\", "/").split("/")[-1]).strip().lower()

        alltext_full = " ".join(" ".join(lines) for _, lines in docs).lower()
        set_aside = 0
        for where, query, doc, disp in hits:
            name = norm(doc)
            stem = re.sub(r"\.[a-z0-9]{2,5}$", "", name)
            if not name:
                self.err("E22", where, "search-log line names no document", doc)
                continue
            if disp.startswith("used"):
                if name not in alltext_full and stem not in alltext_full:
                    self.err("E22", where, "hit logged as used but the artifact never names it", doc)
            elif disp.startswith("rejected"):
                own = [k for k, (_, l) in glist.items()
                       if (name in l.lower() or stem in l.lower())
                       and re.search(r"not a candidate|scope mismatch", l, re.I)]
                if not own:
                    self.err("E22", where, "rejected hit has no 'GAP - scope mismatch, not a "
                             "candidate: <document>' G-bullet of its own", doc)
                elif len(own) > 1:
                    self.warn("W22", where, "rejected hit appears in %d rejection bullets" % len(own), doc)
            elif disp.startswith("set aside"):
                set_aside += 1  # unrelated by title and unopened: log only, counted in Coverage
            elif disp.startswith("duplicate"):
                # another copy of a document already logged: it shares that document's bullet
                ref = re.search(r"\bG(\d+)\b", disp, re.I)  # the log line is lower-cased
                if not ref or ("G" + ref.group(1)) not in glist:
                    self.err("E22", where, "duplicate hit must cite the G-bullet of the document it "
                             "copies: 'duplicate (Gn)'", doc)
            else:
                self.err("E22", where, "search-log line must end 'used', 'rejected (Gn)', "
                         "'duplicate (Gn)' or 'set aside'", doc)
        if set_aside and not re.search(r"set aside", alltext_full):
            self.err("E22", "searches", "%d hits are set aside but the artifact's Coverage line does "
                     "not give the set-aside count" % set_aside, "set aside")
        # the Coverage line's count must equal the search log's set-aside lines
        for m in re.finditer(r"(\d+)\s+(?:other\s+|more\s+)?(?:results?|hits?|documents?|items?)\b[^.]{0,80}?"
                             r"set aside|set aside[^.]{0,40}?\b(\d+)\b", alltext_full):
            n = int(m.group(1) or m.group(2))
            if n != set_aside:
                self.err("E22", "artifact", "Coverage says %d results were set aside but the search "
                         "log has %d 'set aside' lines" % (n, set_aside), m.group(0))

    # content checks that do not depend on IDs alone
    def check_private_names(self, where, text, in_table):
        """Rejected or unresolved hits never carry a private name, title or URL path."""
        for m in CAPTION_RE.finditer(text):
            if not CAPTION_ENTITY_RE.search(m.group(1)):
                self.err("E28", where, "HARD STOP: case caption names a private party '%s': write "
                         "'[another individual] v. <entity>'" % m.group(0).strip(), text)
        rejected = bool(REJECTED_CUE_RE.search(text))
        for m in URL_RE.finditer(text):
            path = (m.group(2) or "").strip("/")
            if not path or path.startswith("[") or "path withheld" in path:
                continue
            if PEOPLE_SITE_RE.search(m.group(0)) or rejected:
                self.err("E28", where, "HARD STOP: URL path on a people-search, social or rejected "
                         "hit: keep the domain only ('https://%s/[path withheld]')" % m.group(1), text)
        if rejected and (PEOPLE_SITE_RE.search(text) or re.search(r"people[- ]?search", text, re.I)):
            for m in re.finditer(r"\b([A-Z][a-z]+(?: [A-Z]\.)? [A-Z][a-z]+)\b", strip_quotes(text) + " "
                                 + " ".join(q.group(1) or q.group(2) for q in QUOTE_RE.finditer(text))):
                words = m.group(1).split()
                if any(PEOPLE_SITE_RE.search(w) or w in ("People", "Search", "Result", "Results", "Page",
                                                          "Profile", "Record", "Records", "Report",
                                                          "Background", "Check", "Public")
                       for w in words) or CAPTION_ENTITY_RE.search(m.group(1)):
                    continue
                self.err("E28", where, "HARD STOP: rejected people-search hit carries a name '%s': "
                         "name the hit by site and page type only" % m.group(1), text)

    def check_requests(self, reqs):
        """Retrieval wording follows the search log's REQ lines."""
        for where, source, status in reqs:
            key = source.lower()[:60].strip()
            if not key:
                continue
            for swhere, text, _, _ in self.segments:
                low = text.lower()
                if key not in low:
                    continue
                # a CHECK, not an ERROR: a sentence can name this source while reporting another
                # source's failure, so a person confirms which call the wording describes
                if status.startswith("not attempted") and re.search(
                        r"not retrieved|did not return|returned no result|request failed", low):
                    self.chk(swhere, "E29 '%s' is logged as not attempted: if this sentence reports "
                             "that call, write 'GAP - <source> retrieval not attempted (Gn)'" % source, text)
                if status.startswith("failed") and "retrieval not attempted" in low:
                    self.chk(swhere, "E29 '%s' is logged as failed: if this sentence reports that "
                             "call, write 'NOT RETRIEVED - <source> did not return (Gn)'" % source, text)

    def is_firm(self, m):
        """The user's own firm, named on a "Firm: <name>" header line and not as the respondent."""
        core = re.sub(r"^The\s+", "", m.group(0), flags=re.I).strip().lower()
        if core in ("bank", "bancorp", "credit union") or core in {r.lower() for r in self.respondents}:
            return False
        return any(f.lower().startswith(core) or core.startswith(f.lower()) for f in self.firms)

    def not_respondent(self, t, m):
        """A regulator, or the user's own firm named in the header, is never the respondent."""
        if REGULATOR_IN_RE.search(m.group(0)) or REGULATOR_AFTER_RE.match(t, m.end()):
            return True
        return self.is_firm(m)

    def respondent_conduct(self, t):
        strong = RESPONDENT_RE.search(t)
        weak = [m for rx in (RESP_NAME_RE, THE_BANK_RE) for m in rx.finditer(t)
                if not self.not_respondent(t, m)]
        if not strong and not weak:
            return False
        # "does not say" and a document as subject are neutral only inside their own clause
        conduct = [m for m in CONDUCT_RE.finditer(t)
                   if not NEUTRAL_DOC_RE.search(clause_of(t, m.start()))
                   and not DOC_SUBJECT_RE.match(clause_of(t, m.start()))]
        if not conduct:
            return False
        if strong:
            return True
        # "Wexcombe Bank did not provide a control inventory to this review (G4)": a missing input
        gaps = [g.span() for g in INFO_GAP_RE.finditer(t)]
        if all(any(a <= m.start() < b for a, b in gaps) for m in conduct) \
                and (ID_RE.search(t) or REVIEW_CUE_RE.search(t)):
            return False
        return True

    def check_content(self, segments, bullets, glist, docs):
        gtext = " ".join(l for _, l in glist.values())
        enforcement = any(ENFORCEMENT_CUE_RE.search(" ".join(lines)) for _, lines in docs)
        for key, (where, line) in glist.items():
            self.check_private_names(where, line, False)
            if REJECTED_CUE_RE.search(line):
                body = strip_quotes(line)
                files = set(re.findall(r"\b[\w-]+\.(?:pdf|docx?|xlsx?|pptx?|msg|txt|csv|html?)\b", body, re.I))
                urls = URL_RE.findall(line)
                if len(files) > 1 or len(urls) > 1 or re.search(
                        r"\b\d+ (?:web )?(?:results|hits|pages|sites|documents|files)\b|results from",
                        body, re.I):
                    self.err("E27", where, "%s groups several rejected hits: one document or page "
                             "per bullet" % key, line)
        for where, line, _ in bullets:
            if not BULLET_RE.match(line):
                self.check_private_names(where, line, False)
        for where, text, in_table, col in segments:
            t = strip_quotes(text)
            for m in NONEXIST_RE.finditer(t):
                self.err("E14", where, "non-existence claim '%s': say what was searched "
                         "('NOT FOUND - <source> has no record of <x> as of <date> (Gn)') or "
                         "nothing" % m.group(0), text)
            if TODAY_RE.search(t):
                self.err("E16", where, "day count anchored on 'today': name the anchor date, for "
                         "example '18 calendar days after 2026-10-15'", text)
            if SAR_RE.search(t) and SAR_LAW_RE.search(t) and not SAR_DECLINE_RE.match(t) \
                    and not CITATION_RE.search(text):
                self.err("E24", where, "HARD STOP: SAR wording beyond the fixed decline: write only "
                         "'<category> withheld under data minimisation.' with no statement of "
                         "SAR law and no person next to a SAR", text)
            # a question or a D-bullet asking whether a rule binds the firm is the right form
            question = t.rstrip().endswith("?") or re.search(r"NOT DETERMINED|\(D\d+", t)
            for m in ([] if question else BINDING_RE.finditer(t)):
                self.err("E25", where, "HARD STOP: binding-on-you phrasing '%s' is an applicability "
                         "statement: quote what the rule says about [covered entity]" % m.group(0), text)
            for m in PERIOD_FORM_RE.finditer(t):
                self.err("E7", where, "month or year form '%s' outside quotation marks: quote it "
                         "verbatim with its paragraph number" % m.group(0), text)
            if enforcement:
                for m in REMEDY_RE.finditer(t):
                    self.err("E26", where, "HARD STOP: plain-English remedy paraphrase '%s' "
                             "presupposes the conduct: write 'The order requires the respondent "
                             "to \"<text>\" (¶ n)'" % m.group(0), text)
            if not HEDGED_RE.search(t):
                for m in SUFFICIENCY_RE.finditer(t):
                    self.err("E30", where, "HARD STOP: sufficiency claim '%s': a document is candidate "
                             "evidence; whether it satisfies a request is 'NOT DETERMINED - owner "
                             "confirms (Dn)'" % m.group(0), text)
            if not re.search(r"\bwhether\b|NOT DETERMINED|\(D\d+|\?\s*$", t):
                for m in SELF_ACCUSE_RE.finditer(t):
                    # only the outline's disclaimer phrasings exempt the sentence, for example
                    # "it is not a finding that the firm has a deficiency"
                    if DISCLAIMER_RE.search(t[: m.start()]):
                        continue
                    self.err("E31", where, "HARD STOP: statement that the firm has a deficiency or "
                             "violation '%s': write what was located, what was not, and who assesses "
                             "(NOT DETERMINED (Dn))" % m.group(0), text)
                if not ALLEGED_RE.search(t):
                    named = list(NAMED_ACCUSE_RE.finditer(t))
                    # a bare name ("Northwind has a deficiency") when no suffixed name matched
                    named += [m for m in BARE_ACCUSE_RE.finditer(t)
                              if m.group(1).split()[0] not in BARE_STOP
                              and not any(n.start() <= m.start() < n.end() for n in named)]
                    # the firm named in the header, with conduct words: "Wexcombe Bank failed to file"
                    named += [m for m in RESP_NAME_RE.finditer(t)
                              if self.is_firm(m) and FIRM_CONDUCT_RE.match(t, m.end())
                              and not any(n.start() <= m.start() < n.end() for n in named)]
                    for m in named:
                        if DISCLAIMER_RE.search(t[: m.start()]):
                            continue
                        self.err("E31", where, "HARD STOP: '%s' states a deficiency or violation as fact "
                                 "about a named entity: for the firm, write what was located and who "
                                 "assesses (Dn); for a respondent, 'The order alleges that ...'"
                                 % m.group(0).strip(), text)
            if enforcement and not ALLEGED_RE.search(t) and self.respondent_conduct(t):
                self.err("E32", where, "HARD STOP: the respondent's conduct stated as fact: write "
                         "'The order alleges that ...' (or the admitted or found register the "
                         "posture allows)", text)
            hedged = re.search(r"\bwhether\b|NOT DETERMINED|\(D\d+|\?\s*$", t)
            verbatim = in_table and VERBATIM_COL_RE.search(col or "")
            # vendor reviews carry no rating and no approval decision
            if self.skill == "vendor-risk-review" and not hedged and not verbatim:
                tv = blank(t, VENDOR_REQUIRED_RE)
                for q in QUESTION_RE.finditer(tv):
                    if APPROVAL_RE.search(q.group(0)) and AFFIRM_RE.match(tv[q.end():]):
                        self.err("E33", where, "HARD STOP: an approval question answered yes: give the "
                                 "factors observed and leave approval to the third-party risk owner "
                                 "(NOT DETERMINED (Dn))", text)
                tv = blank(tv, QUESTION_RE)  # "**Is it safe to approve?** I can't make that call."
                for m in APPROVAL_RE.finditer(tv):
                    if negated(tv[: m.start()]):
                        continue  # "this review gives no risk rating", "I can't say it is safe to approve"
                    self.err("E33", where, "HARD STOP: rating or approval wording '%s': give the factors "
                             "observed, each cited, and leave rating and approval to the third-party risk "
                             "owner (NOT DETERMINED (Dn))" % m.group(0).strip(), text)
            # KYC records carry no screening result, PEP determination, rating or finding of guilt
            if self.skill == "kyc-research-pack" and not hedged and not verbatim:
                tk = blank(t, QUESTION_RE)
                for rx, what, attributable in KYC_FORBID:
                    for m in rx.finditer(tk):
                        if negated(tk[: m.start()]) or (attributable and ATTRIB_RE.search(tk)):
                            continue
                        self.err("E34", where, "HARD STOP: %s '%s': this is research, not a screen; "
                                 "write what a named source states, quoted and cited, and leave the "
                                 "determination to the compliance owner (NOT DETERMINED (Dn))"
                                 % (what, m.group(0).strip()), text)
            if SAR_RE.search(t):
                for m in NAME_PAIR_RE.finditer(t):
                    if not set(m.group(1).replace(".", "").split()) & NAME_STOP \
                            and not CAPTION_ENTITY_RE.search(m.group(1)):
                        self.chk(where, "possible person '%s' in a sentence about a SAR: no person is "
                                 "ever linked to a SAR; confirm this is not a person" % m.group(1), text)
                        break
            self.check_private_names(where, text, in_table)
            if in_table and BITES_COL_RE.search(col) and ISO_DATE_RE.search(t) \
                    and "DATES" not in text and not MARKER_RE.match(lead_text(t)):
                self.err("E15", where, "Bites on date without its DATES citation, for example "
                         "'2027-03-01 (DATES, FR Doc. <n> p. <n>)'", text)
            if SPAN_RE.search(t) and SPAN_WORDS_RE.search(t):
                self.chk(where, "date span for a version or period: confirm a document prints this "
                         "exact span; never infer a superseded version's span", text)
            if CONFLICT_RE.search(t) and not re.search(r"conflict", gtext, re.I):
                self.err("E18", where, "sources disagree but no 'GAP - conflicting sources' "
                         "G-bullet exists", text)
        for where, line, heading in bullets:
            if BULLET_RE.match(line):
                continue
            body = lead_text(LIST_RE.sub("", line, count=1))
            # a field-label bullet ("Population: NOT FOUND - ...") leads with its marker after the label
            body = LEAD_LABEL_RE.sub("", lead_text(re.sub(r"^\*\*([^*]+)\*\*", r"\1", body)), count=1)
            if MARKER_RE.match(body) or body.startswith("NOT DETERMINED"):
                continue
            in_absence = bool(heading and ABSENCE_HEAD_RE.search(heading))
            if in_absence or (ABSENCE_LINE_RE.search(strip_quotes(body)) and ID_RE.search(body)):
                self.err("E17", where, "absence bullet must lead with 'NOT FOUND - <source> "
                         "states no <what> (Gn)'", line)
        alltext = "\n".join("\n".join(lines) for _, lines in docs)
        self.check_entity_quotes(segments, glist, alltext)
        # a DRAFT that is only a rejected candidate needs no control of record: skip E19 when every
        # DRAFT bullet's document also has its own "not a candidate" bullet
        def draft_doc(line):
            m = re.search(r"not approved\s*:\s*([^(,;]+)", line)
            return m.group(1).strip().lower() if m else ""

        drafts = [draft_doc(gl) for _, gl in glist.values()
                  if re.search(r"DRAFT\s*[-–—]\s*not approved", gl)]
        rejected = " ".join(gl.lower() for _, gl in glist.values() if REJECTED_CUE_RE.search(gl))
        rejected_only = bool(drafts) and all(d and d in rejected for d in drafts)
        if re.search(r"DRAFT\s*[-–—]\s*not approved", alltext) and not rejected_only \
                and not re.search(r"control of record|approved version", alltext, re.I):
            self.err("E19", "-", "a DRAFT document is analysed but no control of record is named: "
                     "'Control of record: <doc> v<x>, approved <date> (<location>)' or "
                     "'NOT FOUND - <repository> has no record of an approved version of <doc> (Gn)'",
                     "DRAFT - not approved")

    # G-list and D-list bullets
    def check_lists(self, glist, dlist, has_d_intro):
        for key, (where, line) in glist.items():
            body = re.sub(r"^\s*(?:[-*•]|\d+\.)?\s*\**\s*G\d+\s*\**\s*[-–—:.]?\s*", "", line)
            body = lead_text(body)
            m = MARKER_RE.match(body)
            if not m:
                self.err("E3", where, "%s does not lead with a marker token" % key, line)
            # warn only when the part after ";" is itself a shortfall, not a remedy or a location
            after = [p for p in strip_quotes(body).split(";")[1:]]
            if any((GAP_RE.search(p) or MARKER_RE.search(p))
                   and not re.match(r"\s*(?:recovered via|proposed:|remedy|next step|ask|request)", p, re.I)
                   for p in after):
                self.warn("W3", where, "%s may hold two shortfalls (';'): split if so" % key, line)
            if re.search(r"\b(GRC|DMS|screening|FIU|audit platform)\b.*\b(and|or|/)\b.*\bconnector", body, re.I):
                self.err("E3", where, "%s joins two connectors: one connector, one bullet" % key, line)
            sb = strip_quotes(body)
            if re.search(r"\(\s*[a-z0-9]+\s*\)\s*(?:/|and|or)\s*\(\s*[a-z0-9]+\s*\)", sb):
                self.err("E3", where, "%s covers two paragraphs: split" % key, line)
        for key, (where, line) in dlist.items():
            body = strip_quotes(line)
            if "NOT DETERMINED" not in line:
                self.err("E3", where, "%s lacks the NOT DETERMINED token: write "
                         "'%s - NOT DETERMINED - <question> - <decider> decides'" % (key, key), line)
            if not re.search(r"\bdecides?\b|\bdecider\b|\bowner\b|\bcounsel\b|\bcommittee\b", line, re.I):
                self.err("E3", where, "%s names no decider" % key, line)
            if re.search(r"\s(and|or)\s", body) or body.count("?") > 1:
                self.err("E3", where, "%s may join two decisions (' and ', ' or ', two '?'): "
                         "one decision and one decider per bullet" % key, line)
            if re.search(r"\(\s*[a-z0-9]+\s*\)\s*/\s*\(\s*[a-z0-9]+\s*\)", body):
                self.err("E3", where, "%s covers two paragraphs: split" % key, line)
            provs = list(PROVISION_RE.finditer(body))
            for a, b in zip(provs, provs[1:]):
                between = body[a.end():b.start()]
                if re.fullmatch(r"\s*(?:,|and|or|&|/)\s*(?:\d+\s+(?:CFR|U\.S\.C\.?)\s*)?(?:§\s*)?", between) \
                        and a.group(0).replace(" ", "") != b.group(0).replace(" ", ""):
                    self.err("E3", where, "%s joins two provisions ('%s', '%s'): one provision per "
                             "D-bullet" % (key, a.group(0), b.group(0)), line)
        if dlist and not has_d_intro:
            self.err("E3", "-", "D-list intro line missing; it reads exactly", D_INTRO)

    def check_segments(self, segments, glist, dlist):
        for where, text, in_table, col in segments:
            t = strip_quotes(text)
            if not in_table and SUMMARY_LABEL_RE.match(t):
                continue  # a summary-block count line; markers there are labels
            # marker tokens need an ID after them in the same cell or sentence
            for m in MARKER_RE.finditer(t):
                if COUNT_RE.match(t, m.start()):
                    continue
                if t.strip().startswith("Status: DRAFT") or "PROPOSED DRAFTING" in t:
                    continue
                idm = ID_RE.search(t, m.end())
                if not idm:
                    self.err("E1", where, "marker '%s' has no (Gn) after it" % m.group(0), text)
                    continue
                key = idm.group(1) + idm.group(2)
                nxt = MARKER_RE.search(t, m.end())
                if key in glist and (nxt is None or nxt.start() > idm.start()):
                    want = marker_name(m)
                    body = lead_text(re.sub(r"^\s*(?:[-*•]|\d+\.)?\s*\**\s*G\d+\s*\**\s*[-–—:.]?\s*",
                                            "", glist[key][1]))
                    gm = MARKER_RE.match(body)
                    if gm and marker_name(gm) != want:
                        self.err("E23", where, "'%s' cites %s, which is a %s bullet: cite a %s bullet "
                                 "for this shortfall" % (want, key, marker_name(gm), want), text)
            for m in ND_RE.finditer(t):
                if COUNT_RE.match(t, m.start()):
                    continue
                rest = t[m.end():]
                if not re.search(r"(?<![A-Za-z0-9])D\d+", rest):
                    self.err("E2", where, "NOT DETERMINED has no (Dn) after it", text)
            for m in NEG_MARKER_RE.finditer(t):
                self.err("E13", where, "negated marker '%s': state the positive result" % m.group(0), text)
            # marker cell leads with its marker
            if in_table:
                lt = lead_text(t)
                # an outline-mandated short label before the marker ("unknown: NOT FOUND ...")
                lt2 = LEAD_LABEL_RE.sub("", lt, count=1)
                mm = MARKER_RE.search(lt2)
                if mm and mm.start() > 0 and not ID_RE.search(lt2[: mm.start()]) \
                        and not re.match(r"^(partial|not found|conflicts|covered)\b", lt, re.I):
                    msg = ("marker is not the cell's lead: write the marker and (Gn) first, "
                           "the explanation after")
                    if DATE_COL_RE.search(col) or MARKER_COL_RE.search(col):
                        self.err("E10", where, msg, text)
                    else:
                        self.warn("W10", where, msg, text)
                # date, version and approval cells
                if DATE_COL_RE.search(col) and not EXEMPT_COL_RE.search(col):
                    if not lt.strip() or (DATE_BAD_RE.search(lt) and not MARKER_RE.match(lt)):
                        self.err("E8", where, "date/version cell has no value: lead with "
                                 "'NOT FOUND - <source> states no <field> (Gn)'", text or "(blank)")
                elif not lt.strip() or re.fullmatch(r"[\s\-–—]*", lt):
                    # gap-outline mandates "-" in a non-scored row's Policy section cell
                    if not (text.strip() and "not scored" in self.rowtext.get(where.split(" [col")[0], "")):
                        self.err("E9", where, "blank cell: no blank cells", "(blank)")
                # Exemption cells: quote, 'none stated in <citation>', or NOT DETERMINED (Dn)
                if EXEMPT_COL_RE.search(col) and text.strip():
                    if not EXEMPT_OK_RE.match(lead_text(text)):
                        self.err("E11", where, "HARD STOP: an Exemption cell holds only a verbatim "
                                 "quote with citation, 'none stated in <citation>', or "
                                 "'NOT DETERMINED - counsel decides (Dn)'", text)
                    elif INTERP_RE.search(t):
                        self.err("E11", where, "HARD STOP: interpretation words outside the quote "
                                 "in an Exemption cell", text)
            elif INTERP_RE.search(t) and re.search(r"\(\s*[a-z0-9]\s*\)", t):
                self.warn("W11", where, "possible interpretation of a provision: quote it or mark "
                          "NOT DETERMINED (Dn)", text)
            # hedge words
            for m in HEDGE_RE.finditer(t):
                self.err("E6", where, "hedge word '%s'" % m.group(0), text)
            # day counts name their unit
            for m in DAYS_RE.finditer(t):
                if not DAYS_OK_RE.match(t, m.start()):
                    self.err("E7", where, "day count '%s' does not say calendar or business days "
                             "(or quote it verbatim)" % m.group(0), text)
            # gap phrases need an ID in the same sentence or cell
            if in_table and col and text.strip() == col.strip():
                continue
            if re.match(r"\W*Status:\s*DRAFT", text) or SAR_DECLINE_RE.match(t) or SCOPE_LABEL_RE.match(t):
                continue  # the status header line, or the fixed decline wording
            if MANDATED_RE.search(t) and not GAP_RE.search(MANDATED_RE.sub("", t)):
                continue  # outline-mandated wording such as "none - defining provision not retrieved"
            if in_table and (FIELD_COL_RE.match(col or "") or re.fullmatch(r"\s*\*\*[^*]+\*\*\s*", text)):
                continue  # a row label in a field table ("Review period not covered")
            if COUNT_RE.search(t) and not GAP_RE.search(COUNT_RE.sub("", t)):
                continue
            if REJECTED_HEAD_RE.match(text):
                continue  # the required "Rejected candidates" sub-heading of the G-list
            # a quote locator such as "(SOC 2 excerpt, p. 3)" is not a gap phrase
            gm = GAP_RE.search(re.sub(r"\([^)]*\bexcerpts?\b[^)]*\)", "", COUNT_RE.sub("", t)))
            if gm and not ID_RE.search(t):
                self.chk(where, "gap phrase '%s' with no (Gn)/(Dn)" % gm.group(0), text)

    def check_ids(self, segments, glist, dlist):
        cited = set()
        for _, text, _, _ in segments:
            cited |= cited_ids(text)
        all_text_ids = set(cited)
        for book in (glist, dlist):
            for _, line in book.values():
                body = re.sub(r"^\s*(?:[-*•]|\d+\.)?\s*\**\s*[GD]\d+", "", line)
                all_text_ids |= cited_ids(body)
        for key in sorted(all_text_ids, key=lambda k: (k[0], int(k[1:]))):
            book = glist if key[0] == "G" else dlist
            if key not in book:
                self.err("E4", "-", "%s is cited but has no bullet in the %s-list" % (key, key[0]), key)
        for key, (where, line) in glist.items():
            if key not in cited:
                self.warn("W4", where, "%s is never cited outside the G-list (allowed only if it "
                          "is the sole record of its shortfall)" % key, line)

    def check_counts(self, footer_counts, glist, dlist):
        if not footer_counts:
            if glist or dlist:
                self.warn("W5", "-", "no footer counts found ('NOT FOUND: n items')", "")
            return
        actual = {}
        for _, line in glist.values():
            body = re.sub(r"^\s*(?:[-*•]|\d+\.)?\s*\**\s*G\d+\s*\**\s*[-–—:.]?\s*", "", line)
            m = MARKER_RE.match(lead_text(body))
            if m:
                name = [MARKERS[i][0] for i in range(len(MARKERS)) if m.group("m%d" % i)][0]
                actual[name] = actual.get(name, 0) + 1
        actual["NOT DETERMINED"] = len(dlist)
        seen = {}
        for where, name, n, line in footer_counts:
            seen.setdefault(re.split(r"\s*[-–—]", name)[0], (where, n, line))
        for name, (where, n, line) in seen.items():
            if actual.get(name, 0) != n:
                self.err("E5", where, "footer says %s: %d items, lists hold %d"
                         % (name, n, actual.get(name, 0)), line)
        for name, n in actual.items():
            if n and name not in seen:
                self.err("E5", "-", "footer has no count for %s (%d bullets)" % (name, n), name)

    def check_entity_quotes(self, segments, glist, alltext):
        """[covered entity]: entity words inside rule or preamble quotes while the
        definitions section is not retrieved (house-rules.md section 2)."""
        defs_missing = "[covered entity]" in alltext or any(
            re.search(r"NOT RETRIEVED|retrieval not attempted", l) and re.search(r"defin", l, re.I)
            for _, l in glist.values())
        if not defs_missing:
            return
        for where, text, in_table, col in segments:
            # quotes of the firm's own documents keep their wording
            if in_table and re.search(r"policy|excerpt", col, re.I):
                continue
            rule_ctx = (in_table and RULE_COL_RE.search(col)) or RULE_CUE_RE.search(text)
            if FIRM_DOC_RE.search(text) and not rule_ctx:
                continue
            if "[covered entity]" in text:
                # a note explaining the substitution never names the term it replaces
                for m in re.finditer(r"\b(?:covered )?financial institutions?\b", strip_quotes(text), re.I):
                    self.err("E20", where, "HARD STOP: '%s' written beside the [covered entity] "
                             "substitution: write only 'Entity terms in rule quotes are shown as "
                             "[covered entity] (Gn).'" % m.group(0), text)
            for q in QUOTE_RE.finditer(text):
                quote = q.group(1) or q.group(2)
                for m in ENTITY_RE.finditer(quote):
                    before = quote[: m.start()].rstrip()
                    prev = before.split()[-1] if before.split() else ""
                    if prev[:1].isupper() and prev.lower() not in ("the", "a", "an", "such", "each",
                                                                     "any", "covered", "every"):
                        continue  # a proper name such as "Northwind Bank"
                    if m.group(0)[:1].isupper() and not rule_ctx:
                        continue  # "the Bank" in a firm document
                    self.err("E20", where, "HARD STOP: entity word '%s' inside a rule or preamble "
                             "quote while the definitions section is not retrieved: write "
                             "[covered entity]" % m.group(0), text)

    def check_scope_ok(self, segments, glist):
        bad = {k for k, (_, l) in glist.items()
               if re.search(r"population does not match|scope mismatch|period mismatch|"
                            r"period does not match", l, re.I)}
        if not bad:
            return
        for where, text, _, _ in segments:
            if SCOPE_OK_RE.search(text) and (cited_ids(text) & bad or MARKER_RE.search(text)):
                self.err("E12", where, "'scope ok'/'population ok' beside a scope, population or "
                         "period GAP", text)


def main(argv):
    # print UTF-8 whatever the console code page, so quoted text never crashes the run
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    args = argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__)
        return 0
    opts, pos, i = {}, [], 0
    while i < len(args):
        a = args[i]
        if a in ("--reply", "--searches", "--skill"):
            if i + 1 >= len(args):
                print("usage error: %s needs a value (run with --help)" % a)
                return 2
            opts[a] = args[i + 1]
            i += 2
            continue
        if a.startswith("--"):
            print("usage error: unknown option %s (run with --help)" % a)
            return 2
        pos.append(a)
        i += 1
    if len(pos) != 1:
        print(__doc__)
        print("usage error: name exactly one artifact file")
        return 2
    wanted = opts.get("--skill")
    if wanted is not None:
        wanted = SKILL_ALIASES.get(wanted.strip().lower(), wanted.strip().lower())
        if wanted not in SKILLS:
            print("usage error: --skill must be one of: %s" % ", ".join(SKILLS))
            return 2
    paths = [("artifact", pos[0])]
    if "--reply" in opts:
        paths.append(("reply", opts["--reply"]))
    if "--searches" in opts:
        paths.append(("searches", opts["--searches"]))
    loaded = {}
    for label, p in paths:
        try:
            loaded[label] = read_lines(p)
        except (OSError, zipfile.BadZipFile, KeyError) as e:
            print("cannot read %s: %s" % (p, e))
            return 2
        if not any(l.strip() for l in loaded[label]):
            print("ERROR E0 %s: %s is empty or holds only whitespace: nothing to lint; save the "
                  "%s and run again" % (label, p, label))
            return 2
    docs = [(label, loaded[label]) for label, _ in paths if label != "searches"]
    skill, source = detect_skill(docs, wanted)
    lint = Linter(skill)
    glist, dlist = lint.run(docs)
    if "searches" in loaded:
        p = opts["--searches"]
        log = loaded["searches"]
        hits, reqs = [], []
        for i, line in enumerate(log, 1):
            parts = [x.strip() for x in line.strip().strip("|").split("|")]
            if parts and parts[0].upper() == "HIT":
                parts += [""] * (4 - len(parts))
                hits.append(("searches:%d" % i, parts[1], parts[2], parts[3].lower()))
            elif parts and parts[0].upper() == "REQ":
                parts += [""] * (3 - len(parts))
                reqs.append(("searches:%d" % i, parts[1], parts[2].lower()))
        lint.check_searches(hits, glist, docs)
        lint.check_requests(reqs)
        for i, line in enumerate(log, 1):
            lint.check_private_names("searches:%d" % i, line, False)
        if not hits:
            lint.warn("W22", "searches", "search log has no 'HIT | <query> | <document> | "
                      "used/rejected' lines", p)
    for line in lint.errors + lint.checks + lint.warns:
        print(line)
    print("\nSkill checks: %s (from %s)" % (skill or "none", source))
    print("G-bullets: %d  D-bullets: %d  ERROR: %d  CHECK: %d  WARN: %d"
          % (len(glist), len(dlist), len(lint.errors), len(lint.checks), len(lint.warns)))
    if lint.errors:
        print("Fix every ERROR, resolve every CHECK, then run again.")
        return 1
    if lint.checks:
        print("No ERROR. Resolve every CHECK: cite its (Gn)/(Dn), or confirm it is a listed exception.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
