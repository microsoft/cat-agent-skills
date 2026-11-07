#!/usr/bin/env python3
"""Offline, finite-valued, draft-only tolerance engine. Stdlib only."""
import argparse,csv,json,math,sys
from datetime import datetime,timezone
ENGINE='engine:tolerance_check'
CONTRACT='mfg.quality-inspection.v2'

def finite(v,label,nullable=False):
 if nullable and v is None:return None
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError(label+': finite numeric value required')
 return v

def position(v,l,u,n):
 if l is None or u is None:return None
 c=n if n is not None else (l+u)/2
 width=(u-c) if v>=c else (c-l)
 return abs(v-c)/width if width>0 else (0.0 if v==c else float('inf'))

def load(path):
 def bad(x):raise ValueError('nonfinite JSON constant '+x)
 with open(path,encoding='utf-8') as h:return json.load(h,parse_constant=bad)

def run(spec,rows,coc):
 for key in ['part_number','part_revision','lot_id']:
  if not isinstance(spec.get(key),str) or not spec[key].strip():raise ValueError('missing identity '+key)
 q=spec.get('lot_quantity')
 if type(q) is not int or q<1:raise ValueError('lot_quantity must be positive integer')
 chars=spec.get('characteristics')
 if not isinstance(chars,list) or not chars:raise ValueError('characteristics must be nonempty')
 names=[c.get('name') for c in chars]
 if any(not isinstance(n,str) or not n for n in names) or len(set(names))!=len(names):raise ValueError('duplicate/missing characteristic ID')
 index={c['name']:c for c in chars}; grouped={n:[] for n in names}; seen=set(); serials=set();esc=list(spec.get('escalations',[]))
 for row in rows:
  name=row.get('characteristic');serial=row.get('part_serial')
  if name not in index:raise ValueError('unknown characteristic '+str(name))
  if not serial:raise ValueError('missing part_serial')
  if (serial,name) in seen:raise ValueError('duplicate serial/characteristic measurement')
  seen.add((serial,name));serials.add(serial)
  try:v=float(row['value'])
  except (ValueError,KeyError,TypeError):raise ValueError('invalid measurement value')
  finite(v,'measurement')
  for key in ['part_number','part_revision','lot_id']:
   if row.get(key) and row[key]!=spec[key]:raise ValueError('measurement '+key+' mismatch')
  if row.get('unit') and row['unit']!=index[name].get('unit'):raise ValueError('unit mismatch; no silent conversion')
  grouped[name].append((v,serial))
 if len(serials)>q:raise ValueError('sample exceeds lot quantity')
 claimed={}
 for claim in coc.get('claims',[]):
  if not isinstance(claim.get('characteristics'),list) or not isinstance(claim.get('claim'),str) or not claim.get('citation'):raise ValueError('malformed CoC claim')
  for name in claim['characteristics']:claimed[name]=claim
 for key in ['part_number','part_revision','lot_id']:
  if coc.get(key) and coc[key]!=spec[key]:raise ValueError('CoC '+key+' mismatch')
 output=[]
 for c in chars:
  name=c['name'];l=finite(c.get('lsl'),'lsl',True);u=finite(c.get('usl'),'usl',True);n=finite(c.get('nominal'),'nominal',True)
  if l is not None and u is not None and l>=u:raise ValueError('reversed/zero bounds')
  if n is not None and ((l is not None and n<l) or (u is not None and n>u)):raise ValueError('nominal outside bounds')
  crit=c.get('criticality')
  if crit is not None and crit not in ['critical','major','minor']:raise ValueError('invalid criticality')
  if crit is None:crit='critical';esc.append(name+': unresolved criticality treated conservatively as critical; human review required')
  rework=c.get('rework_permitted')
  if rework is not None and type(rework) is not bool:raise ValueError('rework permission must be boolean/null')
  citation=c.get('citation')
  if not isinstance(citation,str) or not citation:raise ValueError('missing drawing citation')
  vals=[v for v,s in grouped[name]];present={s for v,s in grouped[name]};kind=c.get('tolerance_kind','two_sided')
  one=(kind=='upper_limit_only' and u is not None) or (kind=='lower_limit_only' and l is not None)
  missing=not vals or (not one and (l is None or u is None))
  base={'name':name,'unit':c.get('unit',''),'nominal':n,'lower_tolerance':l,'upper_tolerance':u,'criticality':crit,'criticality_source':c.get('criticality_source',citation),'rework_permitted':rework is True,'doc_conflict':False,'source':ENGINE,'citation':citation}
  if missing:
   reason='no measurements found' if not vals else 'missing tolerance';base.update(actual=None,stats={'n':len(vals)},n_out_of_tolerance=0,incidence_pct=0.0,status='not_evaluated',confidence=0.0);esc.append(name+': '+reason+' - grading blocked (disposition-rules.md #4.4)');output.append(base);continue
  out=[v for v in vals if (l is not None and v<l) or (u is not None and v>u)]
  def priority(v):
   pos=position(v,l,u,n)
   return pos if pos is not None else max((v-u) if u is not None else 0,(l-v) if l is not None else 0)
  worst=max(vals,key=priority);pos=position(worst,l,u,n);status='out_of_tolerance' if out else ('in_tolerance_marginal' if pos is not None and pos>0.90 else 'in_tolerance')
  conf=0.99
  if present!=serials:conf=0.0;esc.append(name+': incomplete sample characteristic coverage - hold (#4.4)')
  base.update(actual=worst,stats={'n':len(vals),'mean':round(sum(vals)/len(vals),4),'min':min(vals),'max':max(vals),'band_consumed_pct':round(100*pos,1) if pos is not None and math.isfinite(pos) else None},above_usl=round(max(0,max(vals)-u),8) if u is not None else None,below_lsl=round(max(0,l-min(vals)),8) if l is not None else None,n_out_of_tolerance=len(out),incidence_pct=round(100*len(out)/len(vals),2),status=status,confidence=conf)
  if out and name in claimed:
   base['doc_conflict']=True;cl=claimed[name];esc.append(f"{name}: CoC {coc.get('doc_id','?')} claims '{cl['claim']}' but {len(out)}/{len(vals)} measurements are out of tolerance - measurements govern; supplier-quality review / SCAR candidate (disposition-rules.md #4.3; ISO 9001 8.4.3)")
  output.append(base)
 return {'contract_version':CONTRACT,'part_number':spec['part_number'],'part_revision':spec['part_revision'],'lot_id':spec['lot_id'],'lot_quantity':q,'sample_size':len(serials),'coc':coc,'characteristics':output,'escalations':esc,'provenance':{'engines':['tolerance_check/3.0'],'generated_at':datetime.now(timezone.utc).isoformat(timespec='seconds')}}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--spec',required=True);ap.add_argument('--measurements',required=True);ap.add_argument('--coc');ap.add_argument('--out',required=True);a=ap.parse_args()
 try:
  spec=load(a.spec);coc=load(a.coc) if a.coc else {}
  with open(a.measurements,encoding='utf-8-sig',newline='') as h:rows=list(csv.DictReader(h))
  p=run(spec,rows,coc)
  with open(a.out,'w',encoding='utf-8') as h:json.dump(p,h,indent=2,allow_nan=False)
 except (ValueError,KeyError,TypeError,OSError) as e:print('BLOCKED: '+str(e),file=sys.stderr);return 2
 print('Draft deviations produced; quality engineer review required: '+a.out);return 0
if __name__=='__main__':sys.exit(main())
