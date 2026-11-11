"""Conservative draft source-reconciliation tripwires, not clinical NLP.

Only emit review reasons; never infer diagnosis, exact days, scope or absence.
Explicit cited source_conflicts block even when language is unrecognized.
Regexes are bounded fallbacks: unmatched wording remains a human/intake limit.
Negated, historical or ambiguous markers deliberately may over-escalate.
"""
import re
import unicodedata


def normalized(value):
    # Normalize punctuation/compatibility forms for matching only. Raw facts are
    # neither rewritten nor promoted into clinical or authenticated evidence.
    value = unicodedata.normalize('NFKC', value).casefold()
    value = ''.join(c for c in value if unicodedata.category(c) != 'Cf')
    return re.sub(r'\s+', ' ', re.sub(r'[-_\u2010-\u2015]', ' ', value))


DIAGNOSIS = r'\b(?:fractur\w*|cracked\s+bone|punctured\s+ear\s*drum|cancer|chronic\s+(?:\w+\s+){0,2}irreversible\s+(?:disease|condition)|irreversible\s+chronic\s+(?:disease|condition))\b'
HARM = r'\b(?:bruis\w*|lacerat\w*|crush\w*|burn\w*|cut|strain\w*|fractur\w*|sprain\w*|twist\w*|tweak\w*|injured|injuries|hurt|hurting|wound\w*|bleed\w*|pain|swoll\w*|swelling)\b'
# The generic word "injury" also names a negative-screen field/concept. It is
# not itself a physical-harm marker; keep the explicit cited no-injury control.
# Other negated physical/clinical markers remain conservatively review-required.
# Concept families, not a memorized single failing sentence. Matching is only
# contrary/ambiguous evidence against a structured negative screen.
RECORDING = (
    r'\b(?:[1-9][0-9]*|one|two|three|four|five|six|seven|several|multiple)\s+days?\s+away\b',
    r'\b(?:off|away\s+from|absen\w*\s+from|out\s+of|unable\s+to|cannot|could\s+not|can\x27t)\s+(?:attend\s+|return\s+to\s+)?work\b',
    r'\b(?:miss\w*|los[st]\w*)\s+(?:\w+\s+){0,2}(?:shifts?|work\s*days?|days?\s+of\s+work)\b',
    r'\b(?:fortnight|week)\s+(?:away|off)\b',
    r'\b(?:work\s+restriction|restricted\s+(?:work|duty|duties)|light\s+duties|modified\s+(?:work|duty|duties)|job\s+transfer|sutures?|stitch\w*|surgery|surgical|loss\s+of\s+consciousness|unconscious|passed\s+out)\b',
    DIAGNOSIS,
)


def reconciliation_issues(payload, *, blank_detail):
    inj = payload.get('injury', {})
    issues = []
    for item in payload.get('source_conflicts', []):
        # Detail stays inert in rendering; citation content is not authenticated.
        issues.append('Unresolved cited source conflict for ' + item['field'] +
                      '; reconcile evidence without diagnosis/day inference (' + item['citation'] + ').')
    nature = normalized(inj.get('nature', ''))
    if inj.get('significant_diagnosis') == 'none' and re.search(DIAGNOSIS, nature):
        issues.append('Narrative nature conflicts with no significant diagnosis; clinician clarification required, no diagnosis inferred.')
    # Do not scan policy/history boilerplate as current injury evidence. Clinical
    # description, nature and qualitative days-away accounts are current facts.
    text = normalized(' '.join((payload.get('description', ''), inj.get('nature', ''),
                               inj.get('days_away_evidence', ''))))
    if blank_detail and re.search(HARM, text):
        issues.append('Narrative harm marker with blank injury detail; absence cannot be established, reconcile cited evidence without diagnosis inference.')
    negative = (inj.get('treatment_given') in ('none', 'first_aid') and
                inj.get('outcome') == 'none' and inj.get('days_away') == 0 and
                inj.get('significant_diagnosis') == 'none' and
                inj.get('loss_of_consciousness') is not True)
    # A verified positive diagnosis/LOC is not a negative screen merely because
    # treatment is first aid and days are zero; do not suppress positive criteria.
    if negative and (inj.get('days_away_evidence') or any(re.search(p, text) for p in RECORDING)):
        issues.append('Positive or ambiguous narrative marker conflicts with structured negative screen; reconcile cited sources, no diagnosis or exact days inferred.')
    return list(dict.fromkeys(issues))
