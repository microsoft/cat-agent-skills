"""Shared offline terminal integrity and null-aware draft rendering.

Recomputes from supplied original facts, not a trusted/authenticated source store.
No network, clock reads, notification, filing, approval, persistence or closure.
"""
import copy
import html
import re
import sys
from pathlib import Path
from safety_common import ROOT, RELEASE, validate
sys.path.insert(0, str(ROOT / 'skills/severity-recordability/scripts'))
sys.path.insert(0, str(ROOT / 'skills/routing-notify/scripts'))
from recordability_classify import classification_hop
from routing_notify import route

REQUIRED_HOPS = ('classification', 'history', 'governance', 'routing', 'next_best_action')
EVIDENCE = ('osha_criteria', 'iso_clauses', 'jha', 'policies')


def terminal_validate(packet):
    """Reject missing/altered/stale output hops before constructing any draft."""
    validate(packet)
    for key in REQUIRED_HOPS:
        if key not in packet:
            raise ValueError(f'Terminal stage missing: {key}')
    engines = packet.get('provenance', {}).get('engines', [])
    expected_engines = [f'recordability_classify/{RELEASE}', f'routing_notify/{RELEASE}']
    if not all(engine in engines for engine in expected_engines):
        raise ValueError('Terminal stage requires current classifier and router provenance labels; labels are not authentication')
    if engines.index(expected_engines[0]) >= engines.index(expected_engines[1]):
        raise ValueError('Classifier must precede router')
    original = copy.deepcopy(packet)
    for key in (*REQUIRED_HOPS, 'writeup', 'escalations'):
        original.pop(key, None)
    # Exclude supplied output escalation text from required safety messages. These are
    # derived again, so deleting URGENT/HOLD or source-completeness warnings is rejected.
    expected = route(classification_hop(original))
    for key in REQUIRED_HOPS:
        if packet[key] != expected[key]:
            raise ValueError(f'Terminal {key} missing/stale/altered; rerun the entire local chain')
    if not set(expected.get('escalations', [])).issubset(packet.get('escalations', [])):
        raise ValueError('Required derived safety escalation missing/altered')
    missing = [key for key in EVIDENCE if not packet.get('retrieved', {}).get(key)]
    return {'status': 'review_required' if missing else 'local_draft_evidence_complete',
            'missing': missing,
            'authority': 'Citations and supplied provenance are unverified. Local ISO summaries are not authoritative standard text.'}


def text(value, *, probability=False):
    if value is None or value == '':
        return 'NOT ESTIMATED' if probability else 'UNDETERMINED — EHS REVIEW REQUIRED'
    if type(value) is bool:
        return 'YES' if value else 'NO'
    # Treat input text as inert quoted evidence: escape HTML and Markdown constructs,
    # including image/link syntax, table separators, line breaks and heading prefixes.
    result = html.escape(str(value), quote=True)
    for character in ('\\', '`', '*', '_', '[', ']', '|', '#', '>', '!'):
        result = result.replace(character, '\\' + character)
    return result.replace('\r', ' ').replace('\n', ' / ')


def render_markdown(packet):
    evidence = terminal_validate(packet)
    c = packet['classification']; r = packet['routing']; g = packet['governance']
    i = packet.get('injury', {})
    context = [('| Field | Supplied value |'), '|---|---|']
    for label, value in [('Incident ID', packet['incident_id']), ('Type', packet.get('incident_type')),
                         ('Asset', packet['asset_or_area']), ('Location', packet.get('location')),
                         ('Occurred at', packet.get('occurred_at')), ('Reported at', packet.get('reported_at')),
                         ('Report channel', packet.get('report_channel')),
                         ('Description (supplied account, not cause proof)', packet.get('description')),
                         ('Employee identity', 'OMITTED — use authorized source reference'), ('Body / nature', ' / '.join(i.get(k, 'UNDETERMINED') for k in ('body_part','nature'))),
                         ('Treatment', i.get('treatment_given')), ('Outcome', i.get('outcome')),
                         ('Exact days away', i.get('days_away')), ('Qualitative days-away evidence', i.get('days_away_evidence')),
                         ('Clinical citation', i.get('citation')), ('Immediate actions (reported, not performed here)', packet.get('immediate_actions'))]:
        context.append(f'| {label} | {text(value)} |')
    for index, witness in enumerate(packet.get('witnesses', []), 1):
        context.append(f"| Supplied witness {index} (identity omitted) | {text(witness.get('role'))}; {text(witness['citation'])} |")
    classification = ['| Draft recommendation (human review required) | Draft value | Citation |', '|---|---|---|']
    for label, value, cite in [('Severity', c['severity'], c['citation']), ('Near miss', c['near_miss'], c['citation']),
                              ('Recordable', c['recordable']['value'], c['recordable']['citation']),
                              ('OSHA 300 column (blank is not a determination)', c['recordable']['osha_300_column'], c['recordable']['citation']),
                              ('Recording reason', c['recordable']['reason'], c['recordable']['citation']),
                              ('Reportable', c['reportable']['value'], c['reportable']['citation']),
                              ('Reporting reason', c['reportable']['reason'], c['reportable']['citation']),
                              ('Deadline hours', c['reportable']['deadline_hours'], c['reportable']['citation'])]:
        classification.append(f'| {label} | {text(value)} | {text(cite)} |')
    classification.append('| Classification probability | NOT ESTIMATED | engine:recordability_classify |')
    classification.extend('- Review reason: ' + text(reason) for reason in c['review_reasons'])
    routing = [f"Proposed investigator: **{text(r['investigator']['role'])}** (NOT ASSIGNED)",
               f"Rationale: {text(r['investigator']['rationale'])}; {text(r['investigator']['citation'])}",
               '', '| Draft recipient (NOT SENT) | Reason | Citation |', '|---|---|---|']
    for n in r['notifications']:
        routing.append(f"| {text(n['role'])} | {text(n['reason'])} | {text(n['citation'])} |")
    routing.extend(['', f"History: {text(packet['history']['status'])}; repeat count {text(packet['history']['repeat_count'])}; repeat flag {text(packet['history']['repeat_pattern'])}.",
                    f"Downgrade HOLD: {text(g['downgrade_hold'])}.",
                    'EHS approval verified: NO. Filing confirmation verified: NO. Closure allowed: NO. Action execution allowed: NO.',
                    'These gates remain blocked in this candidate, even if approval is claimed. No input can unlock them.'])
    citations = [f"Evidence completeness: **{text(evidence['status'])}** — never operational readiness.", evidence['authority']]
    if evidence['missing']:
        citations.append('REVIEW REQUIRED — missing evidence classes: ' + ', '.join(evidence['missing']))
    for kind in EVIDENCE:
        for item in packet.get('retrieved', {}).get(kind, []):
            citations.append(f"- {kind}: {text(item.get('ref', item.get('doc')))}; {text(item['note'])}; {text(item['evidence_kind'])}; {text(item['citation'])}")
    if packet.get('retrieved'):
        citations.append('- Retrieval assembly citation: ' + text(packet['retrieved']['citation']))
    for conflict in packet.get('source_conflicts', []):
        citations.append(f"- Unresolved supplied source discrepancy (UNVERIFIED): {text(conflict['field'])}; {text(conflict['detail'])}; {text(conflict['citation'])}")
    for factor in packet.get('incident_factors', []):
        citations.append(f"- Supplied factor (UNVERIFIED, not cause proof): {text(factor['name'])}; {text(factor.get('detail'))}; {text(factor['citation'])}; confidence NOT ESTIMATED")
    rca = ['Problem statement (supplied account, not a proven cause): ' + text(packet.get('description')), '', '5-Why — hypotheses only; each needs evidence:']
    rca.extend(f'{n}. Why? — ______ (evidence: ______)' for n in range(1,6))
    if c['severity'] in ('high', 'critical'):
        rca.extend(['', 'Fishbone — all six categories, no causes inferred:', '| Category | Hypothesis | Evidence to verify |', '|---|---|---|'])
        rca.extend(f'| {category} | ______ | ______ |' for category in ('People','Process/Method','Equipment/Machine','Materials','Environment','Management'))
    rca.extend(['', 'JHA/HIRA control linkage to investigate: ______ (citation: ______).',
                'Corrective action proposal: ______; proposed owner: ______; proposed due date: ______; verification evidence: ______.',
                'No action, owner, due date, cause or effectiveness is asserted.'])
    values = {'release': RELEASE, 'incident_id': text(packet['incident_id']), 'context': '\n'.join(context),
              'classification': '\n'.join(classification), 'routing': '\n'.join(routing),
              'escalations': '\n'.join('- ' + text(e) for e in packet.get('escalations', [])),
              'next_best_action': text(packet['next_best_action']), 'evidence': '\n'.join(citations),
              'rca': '\n'.join(rca)}
    template = (ROOT / 'skills/incident-writeup/templates/incident-writeup-template.md').read_text(encoding='utf-8')
    def substitute(match):
        key = match.group(1)
        if key not in values:
            raise ValueError('Unfilled template placeholder')
        return values[key]
    # Match incomplete openings too, without rescanning inserted evidence.
    return re.sub(r'\{\{([^{}]*)\}\}|\{\{', substitute, template)
