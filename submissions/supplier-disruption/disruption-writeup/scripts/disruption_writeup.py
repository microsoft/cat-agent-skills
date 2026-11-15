"""Offline integrity check and null-aware Markdown draft; never sends or commits."""
import argparse,copy,json,subprocess,sys,tempfile
from datetime import datetime
from pathlib import Path
from validation import read_json,validate_planning
from output_safety import check_outputs,write_outputs

HERE=Path(__file__).resolve().parent
DERIVED=['impact_map','impact_summary','mitigation','notifications','next_best_action']

def verify_packet(packet):
    validate_planning(packet,mitigation=True)
    evidence=copy.deepcopy(packet)
    for k in DERIVED+['provenance','writeup','impact_escalations']:
        evidence.pop(k,None)
    evidence['escalations']=list(packet.get('intake_escalations',[]))
    with tempfile.TemporaryDirectory(prefix='supplier-draft-') as tmp:
        d=Path(tmp);src=d/'input.json';impact=d/'impact.json';final=d/'packet.json'
        src.write_text(json.dumps(evidence,allow_nan=False),encoding='utf-8')
        for script,flag,inp,out in [('shortage_impact_map.py','--intake',src,impact),('mitigation_recommend.py','--impact',impact,final)]:
            r=subprocess.run([sys.executable,str(HERE/script),flag,str(inp),'--out',str(out)],capture_output=True,text=True,timeout=30)
            if r.returncode:raise ValueError('blocked upstream validation: '+r.stderr)
        rebuilt=read_json(final)
    inconsistent=[k for k in DERIVED+['escalations'] if packet.get(k)!=rebuilt.get(k)]
    if inconsistent:raise ValueError('blocked: derived packet mismatch in '+', '.join(inconsistent)+'; rerun trusted cited evidence through both engines')
    return rebuilt

def clean(value):
    if value is None:return 'UNKNOWN'
    # Avoid rendering evidence as active HTML, remote image links or Markdown cells.
    return str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','\\|').replace('\n',' ').replace('![','! [').replace('[','\\[').replace(']','\\]')

def render(packet,response_by=None):
    if response_by:
        try: deadline=datetime.fromisoformat(response_by.replace("Z","+00:00"))
        except (ValueError,TypeError):raise ValueError("response-by must be supplied ISO datetime with timezone")
        if deadline.tzinfo is None:raise ValueError("response-by timezone required")
        # Date-only reports lack a time/zone: conservatively require a later date.
        asof=packet.get('reported_at','')[:10]
        if deadline.date().isoformat()<=asof:raise ValueError('response-by must be after supplied report as-of date; request corrected future date/time/timezone')
    p=verify_packet(packet);s=p['impact_summary'];m=p['mitigation'];part=p.get('part',{})
    response=response_by or '[RESPONSE-BY REQUIRED — buyer supplies date, time and timezone]'
    state='DRAFT — BUYER/PLANNER REVIEW REQUIRED' if response_by else 'DRAFT INCOMPLETE — RESPONSE-BY REQUIRED; NOT READY FOR COMMUNICATION'
    lines=['# Supplier disruption '+clean(p['disruption_id']),state,'','## Open items / escalations']
    lines.extend('- '+clean(x) for x in p.get('escalations',[]))
    if not response_by:lines.append('- Buyer must supply an explicit response-by date/time/timezone; do not fabricate it.')
    lines+=['- Confirm contact names, source snapshot freshness, receipt-versus-ship date, feasible PO-level quantities and approvals outside this plugin.','', '## Impact summary',f"Worst severity: {clean(s['worst_severity'])}; first impact: {clean(s['first_impact_date'])}; original-need-by demand risk: {s['total_qty_at_risk']:g}; affected orders: {s['affected_orders']}; delayed PO quantity: {p['supply']['on_order']:g}. Aggregate risk is NOT a PO expedite quantity.",'','| Order | Product / line | Need-by | Risk | Status | Evidence |','|---|---|---|---:|---|---|']
    for r in p['impact_map']:
        lines.append('| '+ ' | '.join(clean(x) for x in [r['order_id'],r['product']+' / '+r['line'],r['need_by'],r['qty_at_risk'],r['status'],r['citation']])+' |')
    lines+=['','## Recommended mitigation',clean(m['option'])+' / '+clean(m['urgency']),clean(m['rationale'])]
    lines.extend('- PROPOSED ONLY: '+clean(x) for x in m['actions'])
    lines.append('Buyer/planner review must separately determine feasible PO-level quantity and timing. Aggregate demand risk is not a quantity to purchase, substitute or expedite; no PO issuance, hold or cancellation is instructed.')
    lines+=['','## Unsent owners to review']
    lines.extend('- '+clean(n['role'])+' — named owner UNKNOWN; '+clean(n['reason'])+' ['+clean(n['citation'])+']' for n in p['notifications'])
    lines+=['','## Supplier follow-up — draft','Dear [supplier contact — buyer to confirm],',f"Regarding {clean(p.get('po_number'))}, {clean(part.get('part_no'))}: original promised date {clean(p.get('promised_date'))}, revised receipt basis {clean(p.get('revised_date'))}; delayed PO quantity {p['supply']['on_order']:g}. {clean(p.get('reason'))}",f"The supplied local evidence shows {clean(s['worst_severity'])} impact, first impact {clean(s['first_impact_date'])}, with {s['total_qty_at_risk']:g} total demand units exposed at original need-by dates. This is not a request to expedite that aggregate quantity."]
    if s['affected_sales_orders']:lines.append('A customer sales order is at risk of late shipment; do not soften or omit this risk.')
    ask='Please confirm the revised receipt date in writing and flag further slippage.' if m['option']=='reschedule' else 'Please propose a feasible partial-shipment/recovery plan with PO-level quantities and dates; no commitment or approval is made here.'
    lines +=[ask,'Response-by: '+clean(response),'Basis: supplied PO, inventory/master/order citations; engine:shortage_impact_map and engine:mitigation_recommend.','', '## Internal escalation brief — draft',f"Decision needed: buyer/planner reviews {clean(m['option'])}/{clean(m['urgency'])} and validates feasibility, quantities, dates and approvals outside this plugin. Impact: {clean(s['worst_severity'])}; first impact {clean(s['first_impact_date'])}; {s['affected_orders']} orders; {s['total_qty_at_risk']:g} original-need-by demand units at risk.",clean(p['next_best_action']),'Notifications remain unsent; all contacts unresolved. No ERP, supplier, purchase, spend or schedule action has occurred.','', '## Provenance', 'Derived fields were recomputed and checked, not trusted on receipt. Local hashes establish file identity, not source authenticity. The synthetic scenario is not a live stock check.','', '## Packet appendix','```json',json.dumps(p,indent=2,allow_nan=False),'```']
    return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--packet',required=True);ap.add_argument('--out',required=True);ap.add_argument('--response-by');ap.add_argument('--allow-incomplete',action='store_true');a=ap.parse_args()
    check_outputs([a.out],[a.packet])
    if Path(a.out).suffix.lower()!='.md':raise ValueError('Only deterministic Markdown (.md) drafts are supported')
    if not a.response_by and not a.allow_incomplete:raise ValueError('response-by missing: ask buyer for explicit date/time/timezone, or request an explicitly incomplete draft')
    packet=read_json(a.packet)
    if not isinstance(packet,dict):raise ValueError('payload must be object')
    result=render(packet,a.response_by);write_outputs([(a.out,result)],[a.packet]);print('Draft saved locally; no operational action. Complete-for-review='+str(bool(a.response_by)))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,TypeError,KeyError,OSError,subprocess.TimeoutExpired) as e:print('BLOCKED: '+str(e),file=sys.stderr);sys.exit(2)
