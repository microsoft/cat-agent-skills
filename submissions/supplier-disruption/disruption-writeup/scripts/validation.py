"""Dependency-free offline phase preflight. Not a live ERP or operational validator."""
import math,re,json
from pathlib import Path
from datetime import date

def number(value,label,positive=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or (positive and value<=0):
        raise ValueError(label+': finite nonnegative number required')
    return value

def boolean(value,label):
    if not isinstance(value,bool):raise ValueError(label+': boolean required, no string coercion')

def day(value,label):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError(label+': ISO date required')
    try:return date.fromisoformat(value)
    except ValueError:raise ValueError(label+': invalid calendar date')

def text(value,label):
    if not isinstance(value,str) or not value.strip():raise ValueError(label+': nonempty cited identifier required')

def read_json(path):
    if Path(path).stat().st_size > 8*1024*1024:raise ValueError("input exceeds offline 8 MiB limit; narrow the evidence export")
    def bad_constant(s):raise ValueError('nonfinite JSON token '+s)
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise ValueError('duplicate JSON key '+k)
            d[k]=v
        return d
    with open(path,encoding='utf-8') as f:return json.load(f,parse_constant=bad_constant,object_pairs_hook=unique)


def validate_evidence(p):
    """Planner-supplied attestations are prerequisites, not proof of source authenticity."""
    e=p.get('planning_evidence')
    if not isinstance(e,dict):raise ValueError('planning_evidence required: cited freshness/UOM/usability/demand/receipt confirmations')
    text(e.get('citation'),'planning_evidence citation')
    asof=day(p.get('reported_at','')[:10],'reported_at as-of date')
    snapshot=day(e.get('snapshot_date'),'planning snapshot_date')
    age=e.get('max_age_days')
    if isinstance(age,bool) or not isinstance(age,int) or not 0<=age<=366:raise ValueError('planner policy max_age_days integer 0..366 required')
    if not 0<=(asof-snapshot).days<=age:raise ValueError('planning snapshot stale or future relative to supplied as-of/policy; provide fresh evidence')
    part=p.get('part')
    if not isinstance(part,dict):raise ValueError('cited component part and UOM required')
    text(part.get('part_no'),'part.part_no');text(part.get('uom'),'part.uom')
    for key in ['inventory_uom','demand_uom','receipt_uom']:
        text(e.get(key),key)
        if e[key]!=part['uom']:raise ValueError(key+': UOM mismatch; supply explicit governed conversion outside this single-UOM model')
    for key in ['usable_unreserved_on_hand_confirmed','complete_open_orders_confirmed','demand_deduplicated_confirmed','single_component_single_receipt_confirmed']:
        boolean(e.get(key),key)
        if e[key] is not True:raise ValueError(key+': unresolved planning prerequisite; no coverage conclusion')
    if e.get('receipt_basis')!='confirmed_available_date':raise ValueError('receipt_basis must be confirmed_available_date, not shipment or unconfirmed date')

def validate_planning(p,mitigation=False):
    if not isinstance(p,dict):raise ValueError('payload must be object')
    if p.get('contract_version')!='mfg.supplier-disruption.v1':raise ValueError('wrong contract version')
    for k in ['disruption_id','supplier_or_po']:text(p.get(k),k)
    validate_evidence(p)
    revised=day(p.get('revised_date'),'revised_date')
    if 'promised_date' in p:day(p['promised_date'],'promised_date')
    supply=p.get('supply')
    if not isinstance(supply,dict):raise ValueError('supply object required')
    for k in ['on_hand','on_order','safety_stock']:number(supply.get(k),'supply.'+k)
    if 'lead_time_days' in supply:number(supply['lead_time_days'],'supply.lead_time_days')
    retrieved=p.get('retrieved') or {}
    if not isinstance(retrieved,dict):raise ValueError('retrieved must be an object')
    orders=retrieved.get('open_orders')
    if not isinstance(orders,list):raise ValueError('explicit complete open_orders list required')
    if len(orders)>10000:raise ValueError('order export exceeds 10000 rows; narrow supplied scope')
    ids=set();demand_ids=set();total_demand=0.0
    for i,o in enumerate(orders):
        if not isinstance(o,dict):raise ValueError('order must be object')
        text(o.get('order_id'),'order_id');text(o.get('product'),'product');text(o.get('citation'),'order citation')
        if o['order_id'] in ids:raise ValueError('duplicate order_id '+o['order_id'])
        ids.add(o['order_id'])
        if o.get('order_type') not in ['production','sales']:raise ValueError('invalid order_type')
        number(o.get('finished_qty'),'finished_qty');number(o.get('per_unit'),'per_unit',positive=True);day(o.get('need_by'),'need_by');boolean(o.get('high_runner'),'high_runner')
        text(o.get('demand_identity'),'demand_identity')
        if o['demand_identity'] in demand_ids:raise ValueError('duplicate component demand_identity '+o['demand_identity']+'; deduplicate linked sales/production outside this model')
        demand_ids.add(o['demand_identity'])
        if o.get('component_part_no')!=p['part']['part_no']:raise ValueError('order component_part_no mismatch; single-component scope required')
        demand=o['finished_qty']*o['per_unit']
        number(demand,'component demand arithmetic')
        total_demand+=demand
        number(total_demand,'cumulative demand arithmetic')
    number(supply['on_hand']+supply['on_order'],'combined supply arithmetic')
    if mitigation:
        if not isinstance(p.get('history') or {},dict):raise ValueError('history must be an object')
        boolean(supply.get('single_source'),'single_source');boolean((p.get('history') or {}).get('chronic_pattern'),'chronic_pattern')
        reported=p.get('reported_at')
        if not isinstance(reported,str):raise ValueError('reported_at required')
        day(reported[:10],'reported_at')
        for collection in ['substitutes','alternates']:
            entries=supply.get(collection)
            if not isinstance(entries,list):raise ValueError(collection+' must be explicit list')
            for x in entries:
                if not isinstance(x,dict):raise ValueError(collection+' item must be object')
                if collection=='substitutes':
                    text(x.get('part_no'),'substitute part');boolean(x.get('approved'),'approved');number(x.get('available_qty'),'available_qty')
                else:
                    text(x.get('supplier'),'alternate supplier');boolean(x.get('qualified'),'qualified');number(x.get('lead_time_days'),'alternate lead_time_days')
                text(x.get('citation'),collection+' citation')
        s=p.get('impact_summary')
        if not isinstance(s,dict) or not isinstance(p.get('impact_map'),list):raise ValueError('mapped impact evidence required')
        if s.get('worst_severity') not in ['none','low','medium','high','critical']:raise ValueError('invalid severity')
        number(s.get('total_qty_at_risk'),'total_qty_at_risk');number(s.get('confidence'),'confidence')
        if not 0.80<=s['confidence']<=1:raise ValueError('insufficient confidence')
        if s.get('first_impact_date') is not None:day(s['first_impact_date'],'first_impact_date')
    return True
