#!/usr/bin/env python3
"""Render a local draft only, with recomputed grade comparison and no network."""
import argparse,json,sys,subprocess,tempfile
from replay_quality import original_deviations,clean
from pathlib import Path

def text(v):return 'NOT AVAILABLE' if v is None else str(v).replace('|','\\|').replace('\n',' ')
def render(p):
 if p.get('contract_version')!='mfg.quality-inspection.v2':raise ValueError('requires v2 contract; rerun v3 engines on original inputs')
 if not isinstance(p.get('graded_defects'),list) or 'recommended_disposition' not in p:raise ValueError('terminal grade missing')
 chars=p.get('characteristics',[]); names=[c.get('name') for c in chars]
 if len(set(names))!=len(names):raise ValueError('duplicate characteristic')
 index={c['name']:c for c in chars}
 if any(d['characteristic'] not in index for d in p['graded_defects']):raise ValueError('orphan grade')
 if any(c.get('status')=='not_evaluated' or c.get('confidence',0)<.75 for c in chars) and p['recommended_disposition']!='hold_for_review':raise ValueError('incomplete evidence cannot accept')
 lines=['# NONCONFORMANCE REPORT — '+text(p['lot_id']),'','> DRAFT — QUALITY ENGINEER REVIEW REQUIRED. Nothing filed, sent, quarantined or released.','', '## Open escalations']
 lines+=['- '+text(x) for x in p.get('escalations',[])] or ['- None supplied; this is not a release approval.']
 lines+=['','## Lot identification',f"Part {text(p['part_number'])} revision {text(p.get('part_revision'))}; lot {text(p['lot_id'])}; quantity {text(p.get('lot_quantity'))}; sample {text(p.get('sample_size'))}.",'Certificate '+text(p.get('coc',{}).get('doc_id')),'','## Inspection summary','Sample incidence is not whole-lot incidence. Unknown values remain NOT AVAILABLE.','', '| Characteristic | Worst | Unit | Lower | Upper | OOT/n | Sample % | Band % | Status | Citation |','|---|---|---|---|---|---|---|---|---|---|']
 for c in chars:
  st=c.get('stats',{});values=[c['name'],c.get('actual'),c.get('unit'),c.get('lower_tolerance'),c.get('upper_tolerance'),str(c.get('n_out_of_tolerance'))+'/'+str(st.get('n')),c.get('incidence_pct'),st.get('band_consumed_pct'),c.get('status'),c.get('citation')];lines.append('| '+' | '.join(map(text,values))+' |')
 lines+=['','## Graded defects']
 for d in p['graded_defects']:
  c=index[d['characteristic']];lines+=['- **'+text(d['characteristic'])+'**: '+text(d['severity'])+'; proposed '+text(d['disposition'])+'. '+text(d.get('rationale'))+' ['+text(d['citation'])+']','  Drawing: '+text(c.get('citation'))+'; criticality evidence: '+text(c.get('criticality_source')),'  Measurement source '+text(c.get('source'))+'; confidence '+text(c.get('confidence'))+'. Grade source '+text(d.get('source'))+'; confidence '+text(d.get('confidence'))+'.']
  if c.get('doc_conflict'):lines+=['  Certificate '+text(p.get('coc',{}).get('doc_id'))+' conflicts with measured evidence; measurements govern (#4.3; ISO 9001 8.4.3, paraphrased local reference).']
 lines+=['','**Proposed lot disposition: '+text(p['recommended_disposition'])+'** — never permission to ship.','','## Watch list']
 lines+=['- '+text(w.get('characteristic'))+': '+text(w.get('note'))+' ['+text(w.get('citation'))+']' for w in p.get('watch_list',[])] or ['- None supplied.']
 lines+=['','## Proposed review only','Quality engineer / MRB reviews the evidence and any open escalations. No specific containment is asserted as performed. Supplier messages, QMS filing, stock movement, shipment authorization and CAPA execution are outside this plugin. CAPA owner receives this reviewed contract as handoff; this plugin does not produce its corrective-action plan.','','## Contract payload','```json',json.dumps(p,indent=2,ensure_ascii=False,allow_nan=False),'```','']
 return '\n'.join(lines)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--graded',required=True);ap.add_argument('--out',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--measurements',required=True);ap.add_argument('--coc');a=ap.parse_args()
 try:
  if Path(a.out).suffix.lower() != '.md':
   raise ValueError('Markdown-only release: --out must end in .md; DOCX/PDF and other formats are not supported')
  with open(a.graded,encoding='utf-8') as h:p=json.load(h)
  dev=original_deviations(a.spec,a.measurements,a.coc)
  grader=Path(__file__).resolve().parents[2]/'defect-grade/scripts/defect_grade.py'
  with tempfile.TemporaryDirectory() as tmp:
   temp=Path(tmp);(temp/'deviations.json').write_text(json.dumps(dev,allow_nan=False))
   cmd=[sys.executable,str(grader),'--deviations',str(temp/'deviations.json'),'--out',str(temp/'graded.json'),'--spec',a.spec,'--measurements',a.measurements]
   if a.coc:cmd+=['--coc',a.coc]
   result=subprocess.run(cmd,capture_output=True,text=True)
   if result.returncode:raise ValueError('grade replay blocked: '+result.stderr.strip())
   fresh=json.loads((temp/'graded.json').read_text())
  if clean(p)!=clean(fresh):raise ValueError('terminal payload differs from source replay; do not narrate stale or forged grades')
  output=render(p)
  Path(a.out).write_text(output,encoding='utf-8')
 except (ValueError,KeyError,TypeError,OSError) as e:print('BLOCKED: '+str(e),file=sys.stderr);return 2
 print('Draft NCR rendered: '+a.out);return 0
if __name__=='__main__':sys.exit(main())
