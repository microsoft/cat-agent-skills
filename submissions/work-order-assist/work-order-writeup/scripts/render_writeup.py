"""Recompute local draft evidence and render Markdown. No operational capability."""
import argparse
import html
import re
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from contract_validate import validate_payload
from output_safety import check_outputs, write_outputs

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ('similar_work','superseding_fix','parts_readiness','next_best_action','writeup','provenance')

def safe(value):
    if value is None or value == '': return 'UNVERIFIED / not supplied'
    text = html.escape(str(value)).replace('|','\\|').replace('\n',' ')
    # Keep evidence as inert text, not Markdown links/images or fence syntax.
    for token in ('[',']','`','*','_'):
        text = text.replace(token, '\\' + token)
    return text

def recompute(payload):
    current=json.loads(json.dumps(payload))
    if not isinstance(current,dict): raise ValueError('Payload must be an object')
    for key in DERIVED: current.pop(key,None)
    validate_payload(current)
    current.get('history',{}).pop('repeat_promotion',None)
    current.get('history',{}).pop('repeat_failures',None)
    # Do not turn a partial intake into a calculated status.
    prerequisites=all(current.get(k) for k in ('component','asset_criticality','sop_ref','required_parts'))
    if not prerequisites:
        current['escalations']=list(current.get('escalations',[]))+['Incomplete source prerequisites: ranking and readiness NOT COMPUTED. Supply the missing asset/SOP/parts evidence and obtain planner review.']
        current['next_best_action']='No repair proposal established; request missing evidence.'
        return current
    validate_payload(current,'similar_work')
    with tempfile.TemporaryDirectory(prefix='wo-draft-') as directory:
        d=Path(directory); intake=d/'intake.json'; si=d/'similar.json'; packet=d/'packet.json'; intake.write_text(json.dumps(current))
        for skill,engine,flag,inp,out in [('similar-work-rank','similar_work','--intake',intake,si),('parts-readiness','parts_readiness','--similar',si,packet)]:
            result=subprocess.run([sys.executable,'-B',str(ROOT/f'{skill}/scripts/{engine}.py'),flag,str(inp),'--out',str(out)],capture_output=True,text=True,timeout=30)
            if result.returncode: raise ValueError('Evidence calculation failed: '+result.stderr.strip())
        current=json.loads(packet.read_text()); validate_payload(current,'parts_readiness')
    return current

def render(payload):
    p=recompute(payload)
    appendix = json.dumps(p,indent=2,allow_nan=False)
    fence = '`' * max(3, max((len(x) + 1 for x in re.findall(r'`+', appendix)), default=3))
    lines=['# WORK-ORDER DRAFT — '+safe(p.get('work_order_id'))+' · '+safe(p.get('asset_id')),'',
        '> DRAFT — HUMAN PLANNER / SUPERVISOR REVIEW REQUIRED. Synthetic/offline source snapshots only. No live availability, reservation, scheduling, purchase, assignment, closure, CMMS update or repair authorization is performed.',
        '', '## 1. Work order and asset context','', '| Field | Source value |','|---|---|']
    for key in ['work_order_id','asset_id','asset_name','component','location','asset_criticality','redundancy','reported_by','reported_at','problem_description']:
        lines.append('| '+key+' | '+safe(p.get(key))+' |')
    lines.extend(['','## 2. Issue and cited SOP',''])
    sop=p.get('sop_ref',{}); lines.append('SOP: '+safe(sop.get('doc'))+' · '+safe(sop.get('section'))+' ['+safe(sop.get('citation'))+']')
    lines.append('Default remedy (source evidence, not authorization): '+safe(sop.get('default_remedy')))
    lines.extend(['','## Open escalations — read before any proposed action',''])
    lines.extend('- '+safe(x) for x in p.get('escalations',[]))
    if not p.get('escalations'): lines.append('- No escalations recorded in supplied evidence; this is not safety clearance.')
    lines.extend(['','## 3. Similar past work (engine recomputed)','', '| Rank | WO | Score share | Raw / denominator | Confidence | Outcome | Repeat | Citation |','|---|---|---|---|---|---|---|---|'])
    for x in p.get('similar_work',[]):
        calc=x.get('score_calculation',{})
        vals=[x.get('rank'),x.get('wo_id'),x.get('similarity_score'),str(calc.get('raw_score'))+' / '+str(calc.get('normalization_denominator')),x.get('confidence'),x.get('outcome'),x.get('repeat_failure'),x.get('citation')]
        lines.append('| '+' | '.join(safe(v) for v in vals)+' |')
    if not p.get('similar_work'): lines.append('No computed matches; see uncertainty/escalations. A score share is not the probability of repair success.')
    lines.extend(['','## 4. Parts snapshot (engine recomputed)',''])
    readiness=p.get('parts_readiness',{}); lines.append('Status: '+safe(readiness.get('status','NOT COMPUTED'))+' ['+safe(readiness.get('citation'))+']')
    lines.extend(['','| SOP part | Effective part | Required | Effective on hand | Status | Citation |','|---|---|---|---|---|---|'])
    for x in readiness.get('lines',[]):
        vals=[x.get('part_no'),x.get('effective_part'),x.get('required_qty'),x.get('on_hand'),x.get('line_status'),x.get('citation')]
        lines.append('| '+' | '.join(safe(v) for v in vals)+' |')
    lines.extend(['','## 5. Proposed next action — draft only','',safe(p.get('next_best_action')), '',
        'A qualified person must confirm physical stock, current approved engineering guidance, isolation and safety procedures before deciding on real work.', '',
        '## 6. Review and handoff','', 'No labor estimate, cost, completed repair, reservation or approval is inferred. Scheduling, assignment, inventory, purchasing and CMMS actions remain outside this plugin, even if requested or approved.', '',
        '## Appendix — recomputed contract payload','', fence+'json',appendix,fence,''])
    return '\n'.join(lines), p

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--input',required=True); parser.add_argument('--out',required=True); parser.add_argument('--packet-out')
    args=parser.parse_args(); source=Path(args.input); destination=Path(args.out)
    targets = [destination] + ([Path(args.packet_out)] if args.packet_out else [])
    check_outputs(targets, [source])
    if destination.suffix.lower() != '.md': raise ValueError('Only deterministic Markdown (.md) drafts are supported')
    text,p=render(json.loads(source.read_text(encoding='utf-8')))
    outputs = [(destination, text)]
    if args.packet_out:
        outputs.append((Path(args.packet_out), json.dumps(p,indent=2,allow_nan=False)))
    write_outputs(outputs, [source])
    print('Local draft rendered; no operational action: '+str(destination))
    return 0
if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr)
        sys.exit(2)
