#!/usr/bin/env python3
"""Auditable three-statement analysis. Core uses standard library only."""
__version__='0.8.3'
import argparse, csv, json, math, re, html, zipfile
from pathlib import Path
from datetime import datetime, timezone
from xml.etree import ElementTree as ET  # nosec B405 - XLSX parts are parsed only after the DTD/ENTITY guard in safe_xml()

ALLOWED_UNITS={'ones','thousands','ten_thousands','lakhs','millions','crores','billions'}
UNIT_FACTOR={'ones':1,'thousands':1e3,'ten_thousands':1e4,'lakhs':1e5,'millions':1e6,'crores':1e7,'billions':1e9}   # lakhs/crores: Indian reports
CAS_FRAMEWORKS={'CAS','PRC GAAP','CHINA GAAP','CN GAAP','ASBE'}
STATEMENTS={'income_statement':'Income Statement','balance_sheet':'Balance Sheet','cash_flow':'Cash Flow','supplementary':'Supplementary'}
REQUIRED_STATEMENTS=('income_statement','balance_sheet')   # cash_flow optional: some entities are exempt (e.g. FRS 101 / IAS 7)
ENTITY_TYPES=('operating','conglomerate','bank','insurer','asset_manager','payment_institution','broker_dealer','other_financial')
FINANCIAL_MODEL=('bank','insurer','broker_dealer','other_financial')   # balance sheet is the business: operating-company ratios do not apply

def infer_entity_type(data):
    et=str(data.get('entity_type','')).strip().lower()
    if et:
        if et not in ENTITY_TYPES: raise ValueError('entity_type must be one of '+', '.join(ENTITY_TYPES))
        return et
    ind=str(data.get('industry','')).lower()
    for keys,t in ((('bank',),'bank'),(('insur','reinsur'),'insurer'),(('payment','e-money','emoney','remittance'),'payment_institution'),
                   (('asset manag','investment fund','fund manag','wealth manag'),'asset_manager'),(('broker','securities firm','investment bank'),'broker_dealer')):
        if any(k in ind for k in keys): return t
    return 'operating'
SECTION_TITLES={'revenue':'Revenue','operating_expenses':'Operating expenses','non_operating':'Non-operating items','current_assets':'Current assets','non_current_assets':'Non-current assets','current_liabilities':'Current liabilities','non_current_liabilities':'Non-current liabilities','liabilities':'Liabilities','equity':'Equity','operating':'Operating activities','investing':'Investing activities','financing':'Financing activities','cash':'Cash reconciliation','memo':'Memo items','per_share':'Per-share and market data'}
GRAND_TOTALS={'net_income','total_assets','total_liabilities','total_liabilities_and_equity','cash_end'}
# Sign convention (v2): values as presented; expenses and cash outflows are negative so subtotals are plain sums.
EXPECTED_SIGN={'revenue':1,'cogs':-1,'interest_expense':-1,'capex':-1,'dividends_paid':-1,'share_buybacks':-1,'total_assets':1,
               # Liabilities are positive even when the source prints them in brackets (e.g. net-current-liabilities layouts).
               'current_liabilities':1,'non_current_liabilities':1,'total_liabilities':1,'payables':1,'short_term_debt':1,'long_term_debt':1,'lease_liabilities':1}

def is_demo(data):
    return data.get('demo') is True   # explicit flag only; company-name matching refused real companies
ID_RE=re.compile(r'^[a-z][a-z0-9_]*$')

# Legacy v1 flat fields -> v2 lines: (statement, section, v2 id, v1 key, sign, total_of, tags)
FIELDS={
'revenue':'Revenue','cogs':'Cost of goods sold (positive expense)','gross_profit':'Gross profit','ebitda':'EBITDA','operating_income':'Operating income (EBIT)','interest_expense':'Interest expense (positive)','pretax_income':'Income before tax','tax_expense':'Tax expense (positive)','net_income':'Net income','total_assets':'Total assets','current_assets':'Current assets','cash':'Cash and equivalents','short_term_investments':'Short-term investments','receivables':'Trade receivables','inventory':'Inventory','total_liabilities':'Total liabilities','current_liabilities':'Current liabilities','equity':'Total equity','debt':'Total interest-bearing debt','payables':'Trade payables','ocf':'Cash flows from operating activities','icf':'Cash flows from investing activities','fcf_financing':'Cash flows from financing activities','capex':'Capital expenditure (positive cash spend)','cash_begin':'Cash at start of period','cash_end':'Cash at end of period','fx_cash':'FX/other movement in cash','dividends':'Dividends paid (positive)'}
V1_LAYOUT=[
('income_statement',None,'revenue','revenue',1,None,[]),('income_statement',None,'cogs','cogs',-1,None,[]),('income_statement',None,'gross_profit','gross_profit',1,['revenue','cogs'],[]),
('income_statement',None,'operating_income','operating_income',1,None,[]),('income_statement',None,'interest_expense','interest_expense',-1,None,[]),('income_statement',None,'pretax_income','pretax_income',1,None,[]),
('income_statement',None,'tax_expense','tax_expense',-1,None,[]),('income_statement',None,'net_income','net_income',1,None,[]),('income_statement','memo','ebitda','ebitda',1,None,[]),
('balance_sheet','current_assets','cash','cash',1,None,[]),('balance_sheet','current_assets','short_term_investments','short_term_investments',1,None,[]),('balance_sheet','current_assets','receivables','receivables',1,None,[]),
('balance_sheet','current_assets','inventory','inventory',1,None,[]),('balance_sheet','current_assets','current_assets','current_assets',1,None,[]),('balance_sheet',None,'total_assets','total_assets',1,None,[]),
('balance_sheet','liabilities','payables','payables',1,None,[]),('balance_sheet','liabilities','current_liabilities','current_liabilities',1,None,[]),('balance_sheet','liabilities','total_liabilities','total_liabilities',1,None,[]),
('balance_sheet','equity','equity','equity',1,None,[]),('balance_sheet','memo','debt','debt',1,None,['debt']),
('cash_flow','operating','ocf','ocf',1,None,[]),('cash_flow','investing','capex','capex',-1,None,[]),('cash_flow','investing','icf','icf',1,None,[]),
('cash_flow','financing','dividends_paid','dividends',-1,None,[]),('cash_flow','financing','financing_cf','fcf_financing',1,None,[]),
('cash_flow','cash','cash_begin','cash_begin',1,None,[]),('cash_flow','cash','fx_cash','fx_cash',1,None,[]),('cash_flow','cash','cash_end','cash_end',1,None,[])]

def safe(x):
    if x is None or isinstance(x,bool): return None
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (TypeError,ValueError): return None

def ratio(a,b, allow_negative=True):
    x,y=safe(a),safe(b)
    if x is None or y is None or abs(y)<1e-12 or (not allow_negative and y<=0): return None
    return x/y

def fmt(x, pct=False):
    if x is None: return 'N/A'
    return f'{x*100:,.2f}%' if pct else f'{x:,.2f}'

def display(v,kind):
    if v is None: return 'N/A'
    return {'pct':f'{v*100:,.1f}%','x':f'{v:,.2f}x','int':f'{v:,.0f}','ps':f'{v:,.2f}'}.get(kind,f'{v:,.1f}')

def fmt_date(d):
    try: return datetime.strptime(d,'%Y-%m-%d').strftime('%d %b %Y').lstrip('0')
    except (TypeError,ValueError): return str(d)

# ---------------------------------------------------------------- input model
def convert_v1(data):
    """Map the legacy flat per-period `values` layout onto v2 statements."""
    periods=data['periods']; present=set()
    for p in periods:
        for field,val in p.get('values',{}).items():
            if field not in FIELDS: raise ValueError('Unknown financial field: '+field)
            if val is not None and safe(val) is None: raise ValueError(f"Invalid value {field} in {p['year']}")
            if safe(val) is not None and (field not in p.get('sources',{}) or not p['sources'][field].get('document') or not p['sources'][field].get('location')):
                raise ValueError(f"Missing provenance for {field} in {p['year']}")
            present.add(field)
    st={k:[] for k in ('income_statement','balance_sheet','cash_flow')}
    for statement,section,lid,key,sign,total_of,tags in V1_LAYOUT:
        if key not in present: continue
        line={'id':lid,'label':FIELDS[key].replace(' (positive expense)','').replace(' (positive)','').replace(' (positive cash spend)',''),'section':section,'tags':tags,'values':{},'sources':{}}
        if total_of and all(c in present for c in total_of): line['total_of']=total_of
        for p in periods:
            v=safe(p.get('values',{}).get(key))
            line['values'][str(p['year'])]=None if v is None else sign*v
            if key in p.get('sources',{}): line['sources'][str(p['year'])]=p['sources'][key]
        st[statement].append(line)
    out={k:v for k,v in data.items() if k!='periods'}
    out.update(schema_version='1.0-converted',periods=[{'year':p['year'],'days':p.get('days',365)} for p in periods],statements=st)
    return out

def load_model(data):
    for key in ('company','currency','unit','periods'):
        if key not in data: raise ValueError('Missing required field: '+key)
    if data['unit'] not in ALLOWED_UNITS: raise ValueError(f"unsupported unit '{data['unit']}' - use one of {', '.join(sorted(ALLOWED_UNITS))}")
    if not data['periods']: raise ValueError('At least one period required')
    entity_type=infer_entity_type(data)
    if 'statements' not in data: data=convert_v1(data)
    periods=[p if isinstance(p,dict) else {'year':p} for p in data['periods']]
    years=[int(p['year']) for p in periods]
    if len(years)!=len(set(years)): raise ValueError('Duplicate fiscal years')
    days={}; pinfo={}
    for p in periods:
        y=int(p['year']); ptype=p.get('period_type','annual')
        if ptype not in ('annual','interim'): raise ValueError(f'period_type must be "annual" or "interim" ({y})')
        d=int(p.get('days') or (365 if ptype=='annual' else 0))
        if d<=0 or d>731: raise ValueError(f'Invalid fiscal period days {y}'+('; interim periods must state days' if ptype=='interim' else ''))
        days[y]=d
        label=p.get('label') or ((f'FY{y}' if 360<=d<=371 else f'FY{y} ({d} days)') if ptype=='annual' else f'{y} interim ({d} days)')
        bdate=p.get('balance_date'); fend=p.get('flow_end')
        pinfo[y]={'type':ptype,'label':label,'balance_date':bdate,'flow_end':fend,'audited':p.get('audited'),
                  'balance_label':('As at '+fmt_date(bdate)) if bdate else label}
    years=sorted(years)
    framework=str(data.get('accounting_framework','')).strip()
    ebit_method=data.get('ebit_method') or ('pretax_plus_interest' if framework.upper() in CAS_FRAMEWORKS else 'operating_income')
    if ebit_method not in ('operating_income','pretax_plus_interest','operating_plus_interest_income'): raise ValueError('ebit_method must be operating_income, pretax_plus_interest or operating_plus_interest_income')
    for k in REQUIRED_STATEMENTS:
        if k not in data['statements']: raise ValueError('Missing statement: '+k)
    data=dict(data,statements=dict(data['statements'])); data['statements'].setdefault('cash_flow',[])
    lines={}; order={}
    for st,items in data['statements'].items():
        if st not in STATEMENTS: raise ValueError('Unknown statement: '+st)
        order[st]=[]
        for raw in items or []:
            lid=raw.get('id')
            if not isinstance(lid,str) or not ID_RE.match(lid): raise ValueError(f'Invalid line id: {lid!r}')
            if lid in lines: raise ValueError('Duplicate line id: '+lid)
            vals={}
            for k,v in (raw.get('values') or {}).items():
                y=int(k)
                if y not in days: raise ValueError(f'{lid}: value for {y} which is not a declared period')
                if v is not None and safe(v) is None: raise ValueError(f'Invalid value {lid} in {y}')
                vals[y]=safe(v)
            srcs={}
            for y,v in vals.items():
                src=(raw.get('sources') or {}).get(str(y)) or raw.get('source')
                if v is not None and (not src or not src.get('document') or not src.get('location')):
                    raise ValueError(f'Missing provenance for {lid} in {y}')
                if src: srcs[y]=src
            lines[lid]={'id':lid,'label':raw.get('label') or lid.replace('_',' ').capitalize(),'statement':st,'section':raw.get('section'),
                        'values':vals,'sources':srcs,'total_of':raw.get('total_of'),'tags':raw.get('tags') or []}
            order[st].append(lid)
    for ln in lines.values():
        for c in ln['total_of'] or []:
            if c not in lines: raise ValueError(f"{ln['id']}: total_of references unknown line {c}")
    resolved={}
    def resolve(lid,y,stack=()):
        if (lid,y) in resolved: return resolved[(lid,y)]
        if lid in stack: raise ValueError('Circular total_of: '+' -> '.join(stack+(lid,)))
        ln=lines[lid]; reported=ln['values'].get(y)
        if ln['total_of']:
            comps=[resolve(c,y,stack+(lid,))[0] for c in ln['total_of']]
            if all(c is not None for c in comps):
                sv=sum(comps); q=1 if all(float(x).is_integer() for x in comps+[reported if reported is not None else 0]) else 0.01
                rounding=reported is not None and 1e-9<abs(sv-reported)<=0.51*len(comps)*q
                r=(reported,'reported_rounded') if rounding else (sv,'formula')
            else: r=(reported,'reported_total' if reported is not None else None)
        else: r=(reported,'input' if reported is not None else None)
        resolved[(lid,y)]=r; return r
    for lid in lines:
        for y in years: resolve(lid,y)
    # Display unit: large source figures (e.g. CNY in ones) are shown in millions via Excel number formats; cell values stay exact.
    unit=data['unit']; disp=data.get('display_unit')
    if disp and disp not in UNIT_FACTOR: raise ValueError('Unsupported display_unit')
    if not disp:
        mx=max((abs(v) for (lid,_),(v,_) in resolved.items() if v is not None and lines[lid]['statement']!='supplementary'),default=0)*UNIT_FACTOR[unit]
        disp='millions' if UNIT_FACTOR[unit]<1e6 and mx>=1e9 else 'thousands' if UNIT_FACTOR[unit]<1e3 and mx>=1e7 else unit
    ratio_=UNIT_FACTOR[disp]/UNIT_FACTOR[unit]; commas=round(math.log10(ratio_)/3) if ratio_>=1 else -1
    if commas<0 or abs(10**(3*commas)-ratio_)>1e-6: disp,commas=unit,0
    return {'company':data['company'],'currency':data['currency'],'unit':unit,'basis':data.get('basis','unspecified'),'industry':data.get('industry',''),
            'fiscal_year_end':data.get('fiscal_year_end',''),'schema_version':str(data.get('schema_version','2.0')),'years':years,'days':days,'lines':lines,'order':order,
            'resolved':resolved,'ebit_includes_associates':data.get('ebit_includes_associates'),'period_info':pinfo,'unaudited':any(pinfo[y]['audited'] is False for y in years),'framework':framework,'ebit_method':ebit_method,
            'display_unit':disp,'display_commas':commas,'interim':any(pinfo[y]['type']=='interim' for y in years),
            'annualise':any(pinfo[y]['type']=='interim' or not 360<=days[y]<=371 for y in years),
            'entity_type':entity_type,'financial_model':entity_type in FINANCIAL_MODEL,'has_cash_flow':bool(order.get('cash_flow')),
            'audited':all(pinfo[y]['audited'] is True for y in years),'going_concern':bool(data.get('going_concern_uncertainty')),
            'owners_profit_excludes_perpetual':bool(data.get('owners_profit_excludes_perpetual')),
            'key_disclosures':[d for d in ((d if isinstance(d,dict) else {'text':str(d)}) for d in (data.get('key_disclosures') or []))
                               if order.get('cash_flow') or not re.match(r'\s*no (?:cash[- ]flow|statement of cash flows)',str(d.get('text','')),re.I)],'no_cash_flow_reason':data.get('no_cash_flow_reason','')}

# ---------------------------------------------------------- formula engine
# Each calculation is a small expression tree. One evaluator yields both the Python value and the live
# Excel formula, so the workbook and analysis.json cannot disagree.
def L(i): return ('L',i,0)
def LP(i): return ('L',i,-1)
def X(i): return ('X',i,0)
def XP(i): return ('X',i,-1)
def K(c): return ('K',c)
def add(*a): return ('add',)+a
def sub(a,b): return ('sub',a,b)
def mul(*a): return ('mul',)+a
def div(a,b): return ('div',a,b)  # N/A unless denominator > 0
def neg(a): return ('neg',a)
def avg(a,b): return ('avg',a,b)
def first(*a): return ('first',)+a
def within(a,lo,hi): return ('within',a,lo,hi)
def ann(a): return ('ann',a)    # annualise a flow-based ratio for interim periods (x 365 / days)
def cmp(a): return ('cmp',a)    # only defined when the prior period has the same type and length
def gt(a,lo,e): return ('gt',a,lo,e)   # e, only when a > lo (e.g. leverage multiples only with positive net debt)
def savg(a,b): return ('savg',a,b)     # average of opening and closing, N/A when the balance moves more than 5x (dividends, capital reductions)
def bsflow(a): return ('bsflow',a)     # only when the balance sheet date equals the cash flow period end
def nextbegin(lid): return ('nextbegin',lid)   # next column's opening value when this balance sheet date is the day before it starts
DAYS=('D',)

def item(iid,label,kind,expr,definition,style='line',optional=False):
    return {'id':iid,'label':label,'kind':kind,'expr':expr,'definition':definition,'style':style,'optional':optional}

def col(n):
    s=''; n+=1
    while n: n,rem=divmod(n-1,26);s=chr(65+rem)+s
    return s

def num(v): return str(int(v)) if float(v).is_integer() else repr(float(v))

def strip_outer(f):
    if not (f.startswith('(') and f.endswith(')')): return f
    depth=0
    for i,ch in enumerate(f):
        depth+=ch=='('; depth-=ch==')'
        if depth==0 and i<len(f)-1: return f
    return f[1:-1]

class Ctx:
    def __init__(self,model):
        self.m=model; self.years=model['years']; self.line_addr={}; self.items={}; self.item_addr={}; self.memo={}
    def ref(self,sheet,row,yi,cur):
        a=f'{col(yi+1)}{row}'
        return a if sheet==cur else f"'{sheet}'!{a}"
    def line(self,lid,yi):
        if lid not in self.m['lines'] or not 0<=yi<len(self.years): return None
        return self.m['resolved'][(lid,self.years[yi])][0]
    def calc(self,iid,yi):
        key=(iid,yi)
        if key in self.memo: return self.memo[key]
        if iid not in self.items or not 0<=yi<len(self.years): return (None,None)
        self.memo[key]=(None,None)
        it=self.items[iid]
        r=(float(self.m['days'][self.years[yi]]),None) if it['expr']==DAYS else self.ev(it['expr'],yi,self.item_addr[iid][0])
        if r[1] is not None: r=(r[0],strip_outer(r[1]))
        self.memo[key]=r; return r
    def ev(self,n,yi,cur):
        t=n[0]; NA=(None,None)
        if t=='L':
            j=yi+n[2]
            if j==-1 and 'opening_'+n[1] in self.m['lines']:   # opening balance supplied from the statement of changes in equity
                v=self.line('opening_'+n[1],0)
                return NA if v is None else (v,self.ref(*self.line_addr['opening_'+n[1]],0,cur))
            v=self.line(n[1],j)
            return NA if v is None else (v,self.ref(*self.line_addr[n[1]],j,cur))
        if t=='gt':
            a=self.ev(n[1],yi,cur)[0]
            return self.ev(n[3],yi,cur) if a is not None and a>n[2] else NA
        if t=='bsflow':
            return self.ev(n[1],yi,cur) if bs_matches_flow(self.m,yi) else NA
        if t=='nextbegin':
            if yi+1>=len(self.years) or not opens_next(self.m,yi): return NA
            v=self.line(n[1],yi+1)
            return NA if v is None else (v,self.ref(*self.line_addr[n[1]],yi+1,cur))
        if t=='X':
            j=yi+n[2]; v=self.calc(n[1],j)[0]
            return NA if v is None else (v,self.ref(*self.item_addr[n[1]],j,cur))
        if t=='K': return (float(n[1]),num(n[1]))
        if t=='first':
            for a in n[1:]:
                r=self.ev(a,yi,cur)
                if r[0] is not None: return r
            return NA
        if t=='within':
            v,f=self.ev(n[1],yi,cur)
            return (v,f) if v is not None and n[2]<=v<=n[3] else NA
        if t=='ann':
            v,f=self.ev(n[1],yi,cur)
            if v is None: return NA
            y=self.years[yi]
            d=self.m['days'][y]
            if self.m['period_info'][y]['type']!='interim' and 360<=d<=371: return (v,f)
            dref=self.ref(*self.item_addr['days'],yi,cur) if 'days' in self.item_addr else str(d)
            return (v*365/d,f'({f}*365/{dref})')   # parenthesised so a/ann(b) stays a/(b*365/d) when Excel recalculates
        if t=='cmp':
            if yi<1: return NA
            a,b=self.m['period_info'][self.years[yi]],self.m['period_info'][self.years[yi-1]]
            if a['type']!=b['type'] or abs(self.m['days'][self.years[yi]]-self.m['days'][self.years[yi-1]])>5: return NA
            return self.ev(n[1],yi,cur)
        parts=[self.ev(a,yi,cur) for a in n[1:]]
        if t in ('add','mul') and not parts: return NA   # an empty sum is not a value (and '()' is not a valid Excel formula)
        if any(v is None for v,_ in parts): return NA
        vs=[v for v,_ in parts]; fs=[f for _,f in parts]
        if t=='add': return (sum(vs),'('+'+'.join(fs)+')')
        if t=='sub': return (vs[0]-vs[1],'('+fs[0]+'-'+fs[1]+')')
        if t=='mul': return (math.prod(vs),'('+'*'.join(fs)+')')
        if t=='neg': return (-vs[0],'-'+fs[0])
        if t=='avg': return ((vs[0]+vs[1])/2,f'AVERAGE({fs[0]},{fs[1]})')
        if t=='savg':
            lo,hi=min(vs),max(vs)
            if lo>0 and hi/lo>5: return NA
            return ((vs[0]+vs[1])/2,f'AVERAGE({fs[0]},{fs[1]})')
        if t=='div': return NA if vs[1]<=1e-12 else (vs[0]/vs[1],'('+fs[0]+'/'+fs[1]+')')
        raise ValueError('Unknown node '+t)
    def leaves(self,n,yi,out):
        if n[0]=='L':
            j=yi+n[2]
            if 0<=j<len(self.years) and n[1] in self.m['lines']: out[f'{n[1]}[{self.years[j]}]']=self.line(n[1],j)
            elif j==-1 and 'opening_'+n[1] in self.m['lines']: out[f'opening_{n[1]}[{self.years[0]}]']=self.line('opening_'+n[1],0)
        elif n[0]=='nextbegin':
            if yi+1<len(self.years) and n[1] in self.m['lines']: out[f'{n[1]}[{self.years[yi+1]}]']=self.line(n[1],yi+1)
        elif n[0]=='X':
            j=yi+n[2]
            if 0<=j<len(self.years) and n[1] in self.items: out[f'{n[1]}[{self.years[j]}]']=self.calc(n[1],j)[0]
        elif n[0] not in ('K','D'):
            for a in n[1:]:
                if isinstance(a,tuple): self.leaves(a,yi,out)
        return out

def available(n,lines,specs,seen=()):
    t=n[0]
    if t=='L': return n[1] in lines
    if t=='nextbegin': return n[1] in lines
    if t=='X': return n[1] in specs and n[1] not in seen and available(specs[n[1]]['expr'],lines,specs,seen+(n[1],))
    if t in ('K','D'): return True
    if t=='first': return any(available(a,lines,specs,seen) for a in n[1:])
    if t in ('add','mul') and len(n)==1: return False
    if t=='within': return available(n[1],lines,specs,seen)
    if t=='gt': return available(n[1],lines,specs,seen) and available(n[3],lines,specs,seen)
    return all(available(a,lines,specs,seen) for a in n[1:] if isinstance(a,tuple))

# ------------------------------------------------------------ calculation specs
def bs_matches_flow(m,yi):
    p=m['period_info'][m['years'][yi]]
    if p['balance_date'] and p['flow_end']: return p['balance_date']==p['flow_end']
    return p['type']=='annual'

def opens_next(m,yi):
    """This column's balance sheet date is the day before the next column's flows start (e.g. 31 Dec 2024 -> 9M 2025)."""
    if yi+1>=len(m['years']): return False
    p,q=m['period_info'][m['years'][yi]],m['period_info'][m['years'][yi+1]]
    bd=p['balance_date'] or (p['flow_end'] if p['type']=='annual' else None)
    return bool(bd) and bd.endswith('-12-31') and int(bd[:4])+1==m['years'][yi+1] and q['type']=='interim'

def bs_cash(m):
    """Balance sheet cash excluding restricted deposits that are shown (used by the cash checks). Always consolidated cash:
    the cash flow statement's closing cash is consolidated too, so a conglomerate's non-financial cash belongs only in net debt."""
    lines=m['lines']
    if 'cash_equivalents' in lines: return first(L('cash_equivalents'),L('cash'))
    if 'restricted_cash' in lines and 'cash' in lines and 'restricted_cash' in (lines['cash']['total_of'] or []): return sub(L('cash'),L('restricted_cash'))
    return L('cash')

def unrestricted_cash(m):
    """Cash for net debt: shown restricted deposits removed; otherwise the cash flow statement's cash and cash equivalents
    at the same date (this also removes deposits that are not cash equivalents), else balance sheet cash."""
    lines=m['lines']
    # Groups with banking/insurance arms: consolidated cash includes the financial businesses' cash, which is not available
    # to repay group debt. Net debt needs cash excluding those businesses; without it, net-debt measures are N/A.
    if m.get('entity_type')=='conglomerate': return L('cash_non_financial')
    if 'cash_equivalents' in lines: return first(L('cash_equivalents'),L('cash'))
    if 'restricted_cash' in lines and 'cash' in lines and 'restricted_cash' in (lines['cash']['total_of'] or []): return sub(L('cash'),L('restricted_cash'))
    if 'cash_end' in lines and 'restricted_cash' not in lines: return first(bsflow(L('cash_end')),nextbegin('cash_begin'),L('cash'))
    return L('cash')

def ord_profit(m):
    """Profit attributable to ordinary shareholders. When perpetual bonds are deducted from equity, the distributions to their
    holders must be deducted from profit too, unless the owners' profit line already excludes them (the report shows the
    perpetual holders' share as its own attribution line: owners_profit_excludes_perpetual). Otherwise the ordinary basis is
    N/A (never a mixed basis)."""
    if m.get('owners_profit_excludes_perpetual'): return L('net_income_attributable')
    if 'perpetual_bonds' in m['lines']: return sub(L('net_income_attributable'),L('perpetual_distributions'))
    return first(sub(L('net_income_attributable'),L('perpetual_distributions')),L('net_income_attributable'))

def ordinary_equity_prev(m):
    """Prior-period ordinary shareholders' equity from the sourced balances (prior column, or opening_* lines in the first
    period), on the same basis as ordinary_equity: perpetual instruments are deducted whenever the entity has them."""
    if 'perpetual_bonds' in m['lines']: return sub(LP('shareholders_equity'),LP('perpetual_bonds'))
    return LP('shareholders_equity')

def tagged(m,tag,st=None):
    return [lid for s in m['order'] for lid in m['order'][s] if tag in m['lines'][lid]['tags'] and (st is None or s==st)]

def cash_bridge_options(m):
    """Opening cash + flows expressions for the cash-flow check, most complete first: with FX and the bridging lines,
    then without FX (many reports have none), then without the bridging lines. The cash schedule uses the same rows."""
    base=[L('cash_begin'),L('ocf'),L('icf'),L('financing_cf')]; rec=[L(x) for x in cash_reconciling(m)]
    return ([add(*base,L('fx_cash'),*rec),add(*base,*rec)] if rec else [])+[add(*base,L('fx_cash')),add(*base)]

def cash_reconciling(m):
    """Cash flow lines that bridge opening and closing cash besides the three activities and FX: tagged
    "cash_reconciling", or labelled as cash held for sale / in a disposal group, and not inside another total."""
    out=[]
    for lid in m['order'].get('cash_flow',[]):
        ln=m['lines'][lid]
        if lid in ('cash_begin','cash_end','fx_cash','ocf','icf','financing_cf') or ln['total_of']: continue
        if any(in_tree(m,t,lid) for t in m['order']['cash_flow'] if t!='cash_end'): continue
        if 'cash_reconciling' in ln['tags'] or re.search(r'held for sale|classified as held|disposal group',str(ln.get('label','')),re.I): out.append(lid)
    return out

def ebit_includes_associates(m):
    """True when the EBIT the workbook uses already contains the post-tax share of associates/JVs, so NOPAT must take it out
    before applying tax (and add it back after). Explicit field 'ebit_includes_associates' wins; otherwise:
    reported 'ebit' line -> reconcile it to profit before tax + interest expense - interest income in the years with data;
    pretax-based EBIT -> yes (profit before tax contains the share); operating-profit EBIT -> only if the share is inside that total."""
    if 'share_of_associates' not in m['lines']: return False
    if m.get('ebit_includes_associates') is not None: return bool(m['ebit_includes_associates'])
    if 'ebit' in m['lines']:
        R=m['resolved']; v=lambda lid,y: (R.get((lid,y)) or (None,))[0]
        votes=[]
        for y in m['years']:
            e,pt,ie,ii,sa=v('ebit',y),v('pretax_income',y),v('interest_expense',y),v('interest_income',y) or 0,v('share_of_associates',y)
            if None in (e,pt,ie,sa) or not sa: continue
            base=pt-ie-ii                      # pre-finance profit including the share (interest_expense is negative)
            votes.append(abs(e-base)<=abs(e-(base-sa)))
        return bool(votes) and sum(votes)*2>=len(votes)
    if m['ebit_method']=='pretax_plus_interest': return True
    if m['ebit_method']=='operating_income' and 'operating_income' not in m['lines'] and 'pretax_income' in m['lines']: return True   # derived from profit before tax
    return in_tree(m,'operating_income','share_of_associates')

def in_tree(m,root,leaf):
    ln=m['lines'].get(root)
    if not ln or not ln['total_of']: return False
    return leaf in ln['total_of'] or any(in_tree(m,c,leaf) for c in ln['total_of'])

def schedule_spec(m):
    lines=m['lines']; has=lambda *ids: all(i in lines for i in ids); ucash=unrestricted_cash(m)
    debt_all=[lid for st in m['order'] for lid in m['order'][st] if 'debt' in lines[lid]['tags']]
    debt=[lid for lid in debt_all if not any(in_tree(m,t,lid) for t in debt_all if t!=lid)]   # a tagged subtotal counts once: its tagged components are not added again
    S=[]
    S.append(('Working capital schedule',[
        item('wc_receivables','Trade receivables','num',L('receivables'),'Balance sheet'),
        item('wc_inventory','Inventory','num',L('inventory'),'Balance sheet'),
        item('wc_payables','Less: trade payables','num',neg(L('payables')),'Balance sheet (shown negative)'),
        item('trade_working_capital','Trade working capital','num',add(X('wc_receivables'),X('wc_inventory'),X('wc_payables')),'Receivables + inventory − payables','subtotal'),
        item('change_trade_wc','Change in trade working capital','num',sub(X('trade_working_capital'),XP('trade_working_capital')),'Current year − prior year (increase absorbs cash)'),
        item('twc_pct_revenue','Trade working capital % revenue','pct',div(X('trade_working_capital'),L('revenue')),'Trade working capital / revenue'),
        item('wc_current_assets','Current assets','num',L('current_assets'),'Balance sheet'),
        item('wc_current_liabilities','Less: current liabilities','num',neg(L('current_liabilities')),'Balance sheet (shown negative)'),
        item('net_working_capital','Net working capital','num',add(X('wc_current_assets'),X('wc_current_liabilities')),'Current assets − current liabilities','grand')]))
    dsec=[item('debt__'+lid,lines[lid]['label'],'num',L(lid),'Balance sheet line tagged "debt"') for lid in debt]
    if dsec:
        dsec+=[item('total_debt','Total interest-bearing debt','num',add(*[X('debt__'+lid) for lid in debt]),'Sum of lines tagged "debt"','subtotal'),
               item('nd_cash','Less: cash and equivalents','num',neg(ucash),'Cash excluding financial-services businesses (supply cash_non_financial)' if m.get('entity_type')=='conglomerate' else 'Cash and cash equivalents: excludes restricted deposits that are shown; else the cash flow statement figure at the same date (shown negative)'),
               item('net_debt','Net debt (negative = net cash)','num',add(X('total_debt'),X('nd_cash')),'Total debt − cash','grand')]
        perp=[lid for lid in debt_all if 'perpetual' in lines[lid]['tags']]
        if perp: dsec+=[item('debt_ex_perpetual','Debt excluding perpetual securities','num',sub(X('total_debt'),add(*[L(x) for x in perp])),'Comparable debt when perpetual securities move between equity and debt')]
        if 'cash' in lines and 'cash_end' in lines and 'restricted_cash' not in lines and m.get('entity_type')!='conglomerate':
            dsec+=[item('implied_restricted','Memo: cash not counted (restricted / not cash equivalents)','num',bsflow(sub(L('cash'),L('cash_end'))),'Balance sheet cash − cash flow cash and equivalents at the same date')]
        dl=[lid for st in m['order'] for lid in m['order'][st] if 'debt_like' in lines[lid]['tags']]
        if dl:
            dsec+=[item('dl__'+lid,'Add: '+lines[lid]['label'],'num',L(lid),'Tagged "debt_like": financing-like, excluded from reported debt') for lid in dl]
            dsec+=[item('adj_net_debt','Net debt including debt-like items','num',add(X('net_debt'),*[X('dl__'+lid) for lid in dl]),'Sensitivity: net debt + debt-like items','grand')]
        S.append(('Debt and net debt',dsec))
    if m['ebit_method']=='pretax_plus_interest':
        ebit_expr,ebit_def=add(L('pretax_income'),neg(L('interest_expense'))),'profit before tax + interest expense (reported operating profit is after finance costs)'
    elif m['ebit_method']=='operating_plus_interest_income':
        ebit_expr,ebit_def=add(L('operating_income'),L('interest_income')),'operating profit + interest income (lending entity: interest is its main operating income)'
    elif 'operating_income' not in m['lines'] and 'ebit' not in m['lines'] and 'pretax_income' in m['lines'] and 'interest_expense' in m['lines']:
        ebit_expr=first(sub(sub(L('pretax_income'),L('interest_expense')),L('interest_income')),sub(L('pretax_income'),L('interest_expense')))
        ebit_def='derived: profit before tax + interest expense − interest income (no operating profit line is mapped)'
    else: ebit_expr,ebit_def=L('operating_income'),'operating income per income statement'
    # one-off gains/losses (e.g. remeasurement or disposal gains) that sit inside EBIT are taken out of derived EBITDA too
    eroot='operating_income' if ('operating_income' in lines and m['ebit_method']!='pretax_plus_interest') else 'pretax_income'
    # impairments are added back only when the EBIT basis deducted them: a charge below operating profit never left EBIT.
    # When the EBIT line's components are unknown (no total_of), every tagged impairment is assumed to sit inside it.
    imp=[x for x in tagged(m,'impairment','income_statement') if eroot not in lines or not lines[eroot]['total_of'] or in_tree(m,eroot,x)]
    nrec=[x for x in tagged(m,'non_recurring','income_statement') if x not in imp and in_tree(m,eroot,x)
          and not re.search(r'interest|finance|financial|tax',lines[x]['label'],re.I)] if 'ebit' not in lines else []
    comps=[X('ebit'),X('eb_d_and_a')]+[neg(L(x)) for x in imp]+[neg(L(x)) for x in nrec]+([L('share_of_associates_itda')] if 'share_of_associates_itda' in lines else [])
    eb_def=('Reported EBITDA if supplied, else EBIT + D&A'+(' + impairments (non-cash) added back' if imp else '')
            +(' − one-off gains / + one-off losses tagged "non_recurring" inside EBIT' if nrec else '')
            +(' + share of associates\u2019 interest, tax and D&A' if 'share_of_associates_itda' in lines else ''))
    S.append(('EBITDA and free cash flow',[
        item('ebit','EBIT','num',first(L('ebit'),ebit_expr),'Reported EBIT line if supplied, else '+ebit_def,'subtotal'),
        item('eb_d_and_a','Depreciation and amortisation','num',L('d_and_a'),'Cash flow add-back, or income statement / notes when there is no cash flow statement'),
        item('ebitda','EBITDA' if 'ebitda' in lines else ('EBITDA before one-off items (derived: not the company-reported figure)' if (imp or nrec) else 'EBITDA (derived: not the company-reported figure)'),'num',first(L('ebitda'),add(*comps)),eb_def,'subtotal')]
        +([item('ebitda_derived','EBITDA derived from the statements (cross-check)','num',add(*comps),'EBIT + D&A'+(' + impairments added back' if imp else '')+'; compared with the reported EBITDA',optional=True),
           item('ebitda_ex_imp','EBITDA before tagged impairments','num',sub(L('ebitda'),add(*[L(x) for x in imp])),'Reported EBITDA − lines tagged "impairment" (adds back charges, removes reversals); meaningful when the reported figure is stated after them',optional=True)]
          if 'ebitda' in lines and imp else [])+[
        item('fc_ocf','Cash flow from operating activities','num',L('ocf'),'Cash flow statement'),
        item('fc_capex','Capital expenditure','num',L('capex'),'Cash flow statement (outflow negative)'),
        item('free_cash_flow','Free cash flow','num',add(X('fc_ocf'),X('fc_capex')),'Operating cash flow − capex','subtotal'),
        item('fc_dividends','Dividends paid','num',L('dividends_paid'),'Cash flow statement'),
        item('fcf_after_dividends','Free cash flow after dividends','num',add(X('free_cash_flow'),X('fc_dividends')),'FCF − dividends','grand'),
        item('fcf_incl_distributions','Free cash flow incl. distributions from associates/JVs','num',add(X('free_cash_flow'),L('distributions_from_associates')),'FCF + dividends from equity-accounted investees classified in investing')]
        +([item('ocf_ex_fs','Operating cash flow excl. financial-services balance-sheet flows','num',sub(X('fc_ocf'),add(*[L(x) for x in tagged(m,'fs_operating','cash_flow')])),'OCF − lines tagged "fs_operating": '+'; '.join(lines[x]['label'] for x in tagged(m,'fs_operating','cash_flow'))),
           item('fcf_ex_fs','Free cash flow excl. financial-services flows','num',add(X('ocf_ex_fs'),X('fc_capex')),'OCF excl. FS flows − capex','subtotal')] if tagged(m,'fs_operating','cash_flow') else [])))
    cr=[item('cr_begin','Cash at beginning of period','num',L('cash_begin'),'Cash flow statement'),
        item('cr_ocf','Operating activities','num',L('ocf'),'Cash flow statement'),
        item('cr_icf','Investing activities','num',L('icf'),'Cash flow statement'),
        item('cr_fin','Financing activities','num',L('financing_cf'),'Cash flow statement'),
        item('cr_fx','FX and other movements','num',L('fx_cash'),'Cash flow statement')]
    cr+=[item(f'cr_bridge_{i}',lines[x]['label'],'num',L(x),'Cash flow statement (bridging line; also in the cash-flow check)') for i,x in enumerate(cash_reconciling(m),1)]
    flows=[X(it['id']) for it in cr if it['expr'][1] in lines]
    bridge_complete=all(x in lines for x in ('cash_begin','ocf','icf','financing_cf'))   # FX and bridging rows are optional; the activity totals are not
    cr+=[item('cr_computed','Computed closing cash','num',add(*flows) if bridge_complete else L('cash_begin__unavailable'),'Sum of the rows above','subtotal'),
         item('cr_reported','Reported closing cash (cash flow)','num',L('cash_end'),'Cash flow statement'),
         item('cr_difference','Difference','num',sub(X('cr_reported'),X('cr_computed')),'Reported − computed (should be ~0)'),
         item('cr_bs_cash','Cash per balance sheet (excl. restricted shown)','num',bs_cash(m),'Balance sheet cash excluding restricted deposits that are shown'),
         item('cr_bs_difference','Difference vs balance sheet','num',bsflow(sub(X('cr_reported'),X('cr_bs_cash'))),'Cash flow closing − balance sheet cash (N/A when the dates differ)')]
    S.append(('Cash reconciliation',cr))
    if has('ppe','capex','d_and_a'):
        S.append(('Fixed assets roll-forward (approximate)',[
            item('ppe_open','Opening PP&E','num',LP('ppe'),'Prior-year balance sheet'),
            item('ppe_additions','Additions (capex)','num',neg(first(L('capex_ppe'),L('capex'))),'PP&E capex if supplied (capex_ppe), else total capex (may include intangibles)'),
            item('ppe_depreciation','Depreciation','num',neg(first(L('depreciation_ppe'),L('d_and_a'))),'PP&E depreciation if supplied (depreciation_ppe), else total D&A (includes intangibles and right-of-use)'),
            item('ppe_other','Other movements (derived balancing figure)','num',sub(X('ppe_close'),add(X('ppe_open'),X('ppe_additions'),X('ppe_depreciation'))),'Closing − opening − additions + depreciation; not a source figure'),
            item('ppe_close','Closing PP&E','num',L('ppe'),'Balance sheet','grand')]))
    if has('equity','net_income'):
        moves=[('eq_net_income','Net income','net_income','Income statement'),('eq_dividends','Dividends paid','dividends_paid','Cash flow statement'),('eq_dividends_declared','Dividends declared','dividends_declared','Statement of changes in equity'),('eq_buybacks','Purchase of own shares','share_buybacks','Cash flow statement')]
        if 'dividends_paid' in lines: moves=[mv for mv in moves if mv[2]!='dividends_declared']
        moves=[mv for mv in moves if mv[2] in lines]
        S.append(('Equity roll-forward',[item('eq_open','Opening equity','num',LP('equity'),'Prior-year balance sheet')]+
            [item(i,lab,'num',L(lid),src) for i,lab,lid,src in moves]+
            [item('eq_other','Other movements (derived balancing figure)','num',sub(X('eq_close'),add(X('eq_open'),*[X(mv[0]) for mv in moves])),'OCI, share issues, NCI etc.; not a source figure'),
             item('eq_close','Closing equity','num',L('equity'),'Balance sheet','grand')]))
    if m['financial_model']: S=[sec for sec in S if sec[0] in ('Cash reconciliation','Equity roll-forward')]
    return S

def financial_ratio_spec(m,AN,GR):
    """Banks, insurers, broker-dealers: the balance sheet is the business, so liquidity, working-capital, EBITDA and
    net-debt measures are omitted. 'revenue' = total operating income (net of interest/claims as presented)."""
    avg_loans=avg(L('loans'),LP('loans'))
    return [
    ('Period inputs and intermediate calculations',[
        item('days','Days in period','int',DAYS,'From input periods'),
        item('avg_assets','Average total assets','num',avg(L('total_assets'),LP('total_assets')),'(Opening + closing) / 2'),
        item('avg_equity','Average total equity','num',avg(L('equity'),LP('equity')),'(Opening + closing) / 2, including non-controlling interests'),
        item('ordinary_equity','Ordinary shareholders\u2019 equity','num',first(sub(L('shareholders_equity'),L('perpetual_bonds')),L('shareholders_equity')),'Equity attributable to shareholders, less perpetual / AT1 instruments when supplied',optional=True),
        item('avg_shareholders_equity','Average ordinary shareholders\u2019 equity','num',avg(X('ordinary_equity'),ordinary_equity_prev(m)),'(Opening + closing) / 2 (the first period uses opening_shareholders_equity when supplied)',optional=True),
        item('effective_tax_rate','Effective tax rate','pct',div(neg(L('tax_expense')),L('pretax_income')),'Tax expense / pre-tax income')]),
    ('Profitability and efficiency',[
        item('net_margin','Net margin','pct',div(L('net_income'),L('revenue')),'Net income / total operating income'),
        item('cost_to_income','Cost-to-income ratio','pct',div(neg(L('operating_expenses')),L('revenue')),'Operating expenses / total operating income',optional=True),
        item('nim','Net interest margin','pct',ann(first(div(L('net_interest_income'),avg(L('interest_earning_assets'),LP('interest_earning_assets'))),div(L('net_interest_income'),X('avg_assets')))),
             'Net interest income / average interest-earning assets (average total assets if not supplied)'+AN,optional=True),
        item('nii_share','Net interest income / operating income','pct',div(L('net_interest_income'),L('revenue')),'Share of income from net interest',optional=True),
        item('cost_of_risk','Cost of risk','pct',ann(div(neg(L('impairment_losses')),avg_loans)),'Credit impairment charge / average loans'+AN,optional=True),
        item('combined_ratio','Combined ratio (insurance)','pct',div(neg(L('insurance_service_expenses')),L('insurance_revenue')),'Insurance service expenses / insurance revenue (<100% = underwriting profit)',optional=True)]),
    ('Returns',[
        item('roa','Return on assets','pct',ann(div(L('net_income'),X('avg_assets'))),'Net income / average total assets'+AN),
        item('roe','Return on equity','pct',ann(first(div(ord_profit(m),X('avg_shareholders_equity')),div(L('net_income'),X('avg_equity')))),
             'Shareholder basis when supplied, else net income / average total equity'+AN),
        item('roe_owners','ROE on owners\u2019 equity (incl. perpetual instruments)','pct',ann(div(L('net_income_attributable'),avg(L('shareholders_equity'),LP('shareholders_equity')))),'Profit attributable to owners / average equity attributable to owners, as companies usually report it'+AN,optional=True)]),
    ('Balance sheet and capital',[
        item('equity_to_assets','Equity / total assets','pct',div(L('equity'),L('total_assets')),'Total equity / total assets'),
        item('loan_to_deposit','Loan-to-deposit ratio','pct',div(L('loans'),L('deposits')),'Customer loans / customer deposits',optional=True),
        item('loans_to_assets','Loans / total assets','pct',div(L('loans'),L('total_assets')),'Customer loans / total assets',optional=True),
        item('cet1','CET1 ratio (reported)','pct',L('cet1_ratio'),'As reported by the entity (enter as a decimal, e.g. 0.135)',optional=True),
        item('total_capital','Total capital ratio (reported)','pct',L('total_capital_ratio'),'As reported by the entity',optional=True),
        item('solvency','Solvency ratio (reported)','pct',L('solvency_ratio'),'As reported by the entity (e.g. Solvency II / C-ROSS)',optional=True)]),
    ('Growth',[
        item('revenue_growth','Operating income growth','pct',cmp(sub(div(L('revenue'),LP('revenue')),K(1))),'Total operating income / prior − 1'+GR),
        item('net_income_growth','Net income growth','pct',cmp(sub(div(L('net_income'),LP('net_income')),K(1))),'Net income / prior − 1'+GR),
        item('loan_growth','Loan growth','pct',sub(div(L('loans'),LP('loans')),K(1)),'Loans / prior-period loans − 1',optional=True),
        item('deposit_growth','Deposit growth','pct',sub(div(L('deposits'),LP('deposits')),K(1)),'Deposits / prior-period deposits − 1',optional=True)]),
    ('Per share and valuation',[
        item('eps','Earnings per share (period)','ps',first(div(ord_profit(m),L('shares_outstanding')),div(L('net_income'),L('shares_outstanding'))),'Attributable profit / shares outstanding; not annualised',optional=True),
        item('bvps','Book value per share','ps',first(div(X('ordinary_equity'),L('shares_outstanding')),div(L('equity'),L('shares_outstanding'))),'Ordinary equity / shares outstanding',optional=True),
        item('market_cap','Market capitalisation','num',mul(L('share_price'),L('shares_outstanding')),'Share price × shares outstanding',optional=True),
        item('pe','Price / earnings','x',div(L('share_price'),ann(X('eps'))),'Share price / EPS'+AN.replace('annualised','EPS annualised'),optional=True),
        item('pb','Price / book','x',div(L('share_price'),X('bvps')),'Share price / book value per share',optional=True)])]

def ratio_spec(m):
    AN=' (annualised ×365/days for periods that are not 12 months)' if m['annualise'] else ''
    GR=' (only between periods of the same type and length)' if m['annualise'] else ''
    if m['financial_model']: return financial_ratio_spec(m,AN,GR)
    if m['entity_type']=='conglomerate':
        fin=[it for _,items in financial_ratio_spec(m,AN,GR) for it in items if it['id'] in ('nim','cost_of_risk','combined_ratio','loan_to_deposit','loans_to_assets','cet1','total_capital','solvency','loan_growth','deposit_growth')]
        return operating_ratio_spec(m,AN,GR)+[('Financial services metrics',[dict(it,optional=True) for it in fin])]
    return operating_ratio_spec(m,AN,GR)

def operating_ratio_spec(m,AN,GR):
    lines=m['lines']; has_debt=bool(tagged(m,'debt'))
    share_in=ebit_includes_associates(m)
    sa=L('share_of_associates')
    # tax rate on profit excluding post-tax associates' results; NOPAT adds those results back after tax
    etr=first(div(neg(L('tax_expense')),sub(L('pretax_income'),sa)),div(neg(L('tax_expense')),L('pretax_income'))) if 'share_of_associates' in lines else div(neg(L('tax_expense')),L('pretax_income'))
    ebit_core=sub(X('ebit'),sa) if share_in else X('ebit')
    nopat=add(mul(ebit_core,sub(K(1),within(X('effective_tax_rate'),0,1))),sa) if 'share_of_associates' in lines else mul(X('ebit'),sub(K(1),within(X('effective_tax_rate'),0,1)))
    cov=div(X('ebit'),neg(L('interest_expense')))
    return [
    ('Period inputs and intermediate calculations',[
        item('days','Days in period','int',DAYS,'From input periods'),
        item('avg_assets','Average total assets','num',savg(L('total_assets'),LP('total_assets')),'(Opening + closing) / 2; N/A if the balance moved more than 5×'),
        item('avg_equity','Average total equity','num',savg(L('equity'),LP('equity')),'(Opening + closing) / 2, including non-controlling interests; N/A if equity moved more than 5×'),
        item('ordinary_equity','Ordinary shareholders\u2019 equity','num',first(sub(L('shareholders_equity'),L('perpetual_bonds')),L('shareholders_equity')),'Equity attributable to shareholders, less perpetual bonds / other equity instruments when supplied',optional=True),
        item('avg_shareholders_equity','Average ordinary shareholders\u2019 equity','num',savg(X('ordinary_equity'),ordinary_equity_prev(m)),'(Opening + closing) / 2; N/A if it moved more than 5×',optional=True),
        item('effective_tax_rate','Effective tax rate','pct',within(etr,0,1),'Tax expense / pre-tax income'+(' excluding post-tax results of associates/JVs' if 'share_of_associates' in lines else '')+'; N/A outside 0–100%'),
        item('nopat','NOPAT','num',nopat,'EBIT × (1 − effective tax rate)'+(' on EBIT excluding associates, + post-tax associates\u2019 results' if 'share_of_associates' in lines else '')+'; N/A if rate outside 0–100%'),
        item('invested_capital','Invested capital','num',sub(add(L('equity'),X('total_debt')),unrestricted_cash(m)),'Equity + total debt − cash (excl. restricted)'),
        item('avg_invested_capital','Average invested capital','num',savg(X('invested_capital'),XP('invested_capital')),'(Opening + closing) / 2; N/A if it moved more than 5×')]),
    ('Profitability',[
        item('gross_margin','Gross margin','pct',first(div(L('gross_profit'),L('revenue')),div(add(L('revenue'),L('cogs')),L('revenue'))),'Gross profit / revenue'+('' if 'gross_profit' in lines else ' (gross profit = revenue + cost of sales, which is negative)')),
        item('ebitda_margin','EBITDA margin','pct',div(X('ebitda'),L('revenue')),'EBITDA / revenue'),
        item('operating_margin','EBIT margin','pct',div(X('ebit'),L('revenue')),'EBIT / revenue'),
        item('net_margin','Net margin','pct',div(L('net_income'),L('revenue')),'Net income / revenue'),
        item('net_income_ex_one_offs','Net income before one-off items','num',sub(L('net_income'),add(*[L(x) for x in dict.fromkeys(tagged(m,'non_recurring','income_statement')+tagged(m,'impairment','income_statement'))])),'Net income − lines tagged "non_recurring"/"impairment" (pre-tax amounts; tax effect not adjusted)',optional=True),
        item('net_margin_ex_one_offs','Net margin before one-off items','pct',div(X('net_income_ex_one_offs'),L('revenue')),'Net income before one-offs / revenue',optional=True)]),
    ('Returns',[
        item('roa','Return on assets','pct',ann(div(L('net_income'),X('avg_assets'))),'Net income / average total assets'+AN),
        item('roe','Return on equity','pct',ann(first(div(ord_profit(m),X('avg_shareholders_equity')),div(L('net_income'),X('avg_equity')))),
             'Shareholder basis when supplied (profit attributable to ordinary shareholders / average ordinary equity), else net income / average total equity'+AN),
        item('roe_owners','ROE on owners\u2019 equity (incl. perpetual instruments)','pct',ann(div(L('net_income_attributable'),savg(L('shareholders_equity'),LP('shareholders_equity')))),'Profit attributable to owners / average equity attributable to owners, as companies usually report it'+AN,optional=True),
        item('roic','Return on invested capital','pct',ann(div(X('nopat'),X('avg_invested_capital'))),'NOPAT / average invested capital'+AN),
        item('dupont_roe','DuPont ROE (3-factor)','pct',mul(X('net_margin'),X('asset_turnover'),div(X('avg_assets'),X('avg_equity'))),'Net margin × asset turnover × equity multiplier (total-equity basis)'),
        item('dupont_roe_five','DuPont ROE (5-factor)','pct',mul(div(L('net_income'),L('pretax_income')),div(L('pretax_income'),X('ebit')),X('operating_margin'),X('asset_turnover'),div(X('avg_assets'),X('avg_equity'))),'Tax burden × interest burden × EBIT margin × turnover × equity multiplier')]),
    ('Liquidity',[
        item('current_ratio','Current ratio','x',div(L('current_assets'),L('current_liabilities')),'Current assets / current liabilities'),
        item('quick_ratio','Quick ratio','x',div(first(add(L('cash'),L('receivables'),L('short_term_investments')),add(L('cash'),L('receivables'))),L('current_liabilities')),'(Cash + short-term investments + receivables) / current liabilities'),
        item('cash_ratio','Cash ratio','x',div(L('cash'),L('current_liabilities')),'Cash / current liabilities'),
        item('current_ratio_ex_client','Current ratio excl. client funds','x',div(sub(L('current_assets'),L('client_funds')),sub(L('current_liabilities'),L('client_liabilities'))),'(Current assets − client funds) / (current liabilities − client money owed)',optional=True),
        item('working_capital','Working capital','num',sub(L('current_assets'),L('current_liabilities')),'Current assets − current liabilities')]),
    ('Leverage and coverage',[
        item('debt_to_equity','Debt / equity','x',div(X('total_debt'),L('equity')),'Total debt / equity'),
        item('debt_to_assets','Debt / total assets','pct',div(X('total_debt'),L('total_assets')),'Total debt / total assets'),
        item('net_debt_to_ebitda','Net debt / EBITDA','x',gt(X('net_debt'),0,div(X('net_debt'),ann(X('ebitda')))),'Net debt / EBITDA'+AN.replace('annualised','EBITDA annualised')+'; N/A when the company has net cash'),
        *([item('net_debt_to_ebitda_ex_imp','Net debt / EBITDA before impairments','x',gt(X('net_debt'),0,div(X('net_debt'),ann(X('ebitda_ex_imp')))),'Net debt / EBITDA before tagged impairments (when the reported EBITDA is stated after them)',optional=True)]
          if 'ebitda' in m['lines'] and tagged(m,'impairment','income_statement') else []),
        item('debt_to_ebitda','Gross debt / EBITDA','x',gt(X('total_debt'),0,div(X('total_debt'),ann(X('ebitda')))),'Total debt / EBITDA (use when net debt is N/A)'+AN.replace('annualised','EBITDA annualised'),optional=True),
        item('adj_net_debt_to_equity','Net debt incl. debt-like items / equity','x',div(X('adj_net_debt'),L('equity')),'Sensitivity including lines tagged "debt_like"',optional=True),
        item('interest_coverage','Interest coverage','x',gt(X('total_debt'),0,cov) if has_debt else cov,'EBIT / interest expense'+('; N/A when there is no debt' if has_debt else '')),
        item('interest_coverage_incl_perpetual','Interest coverage incl. perpetual distributions','x',div(X('ebit'),add(neg(L('interest_expense')),L('perpetual_distributions'))),'EBIT / (interest expense + distributions to perpetual holders)',optional=True)]),
    ('Efficiency and working capital',[
        item('asset_turnover','Asset turnover','x',ann(div(L('revenue'),X('avg_assets'))),'Revenue / average total assets'+AN),
        item('dso','Days sales outstanding','days',mul(div(avg(L('receivables'),LP('receivables')),L('revenue')),X('days')),'Average receivables / revenue × days'),
        item('dio','Days inventory outstanding','days',mul(div(avg(L('inventory'),LP('inventory')),neg(L('cogs'))),X('days')),'Average inventory / COGS × days'),
        item('dpo','Days payables outstanding','days',mul(div(avg(L('payables'),LP('payables')),neg(L('cogs'))),X('days')),'Average payables / COGS × days'),
        item('ccc','Cash conversion cycle','days',sub(add(X('dso'),X('dio')),X('dpo')),'DSO + DIO − DPO')]),
    ('Cash flow quality',[
        item('fcf_margin','Free cash flow margin','pct',div(X('free_cash_flow'),L('revenue')),'Free cash flow / revenue'),
        item('cash_conversion','Cash conversion (OCF / net income)','x',div(L('ocf'),L('net_income')),'Operating cash flow / net income'),
        item('cash_conversion_adj','Cash conversion incl. distributions from associates/JVs','x',div(add(L('ocf'),L('distributions_from_associates')),L('net_income')),'(OCF + dividends/distributions from equity-accounted investees classified outside operating cash flow) / net income',optional=True),
        item('capex_intensity','Capex intensity','pct',div(neg(L('capex')),L('revenue')),'Capex / revenue'),
        item('dividend_payout','Dividend payout','pct',div(neg(first(L('dividends_paid'),L('dividends_declared'))),first(L('net_income_attributable'),L('net_income'))),'Dividends paid (else declared) / profit attributable to shareholders (else net income)'),
        item('accrual_proxy','Accrual proxy','pct',ann(div(sub(L('net_income'),L('ocf')),X('avg_assets'))),'(Net income − OCF) / average total assets'+AN)]),
    ('Growth',[
        item('revenue_growth','Revenue growth','pct',cmp(sub(div(L('revenue'),LP('revenue')),K(1))),'Revenue / prior-period revenue − 1'+GR),
        item('ebitda_growth','EBITDA growth','pct',cmp(sub(div(X('ebitda'),XP('ebitda')),K(1))),'EBITDA / prior-period EBITDA − 1'+GR),
        item('net_income_growth','Net income growth','pct',cmp(sub(div(L('net_income'),LP('net_income')),K(1))),'Net income / prior-period net income − 1'+GR)]),
    ('Per share and valuation',[
        item('eps','Earnings per share (period)','ps',first(div(ord_profit(m),L('shares_outstanding')),div(L('net_income'),L('shares_outstanding'))),'Profit attributable to ordinary shareholders (else net income) / shares outstanding; not annualised',optional=True),
        item('bvps','Book value per share','ps',first(div(X('ordinary_equity'),L('shares_outstanding')),div(L('equity'),L('shares_outstanding'))),'Ordinary shareholders\u2019 equity (else total equity) / shares outstanding',optional=True),
        item('market_cap','Market capitalisation','num',mul(L('share_price'),L('shares_outstanding')),'Share price × shares outstanding',optional=True),
        item('enterprise_value','Enterprise value','num',add(X('market_cap'),X('net_debt')),'Market cap + net debt',optional=True),
        item('pe','Price / earnings','x',div(L('share_price'),ann(X('eps'))),'Share price / EPS'+AN.replace('annualised','EPS annualised'),optional=True),
        item('pb','Price / book','x',div(L('share_price'),X('bvps')),'Share price / book value per share',optional=True),
        item('ev_ebitda','EV / EBITDA','x',div(X('enterprise_value'),ann(X('ebitda'))),'Enterprise value / EBITDA'+AN.replace('annualised','EBITDA annualised'),optional=True),
        item('fcf_yield','Free cash flow yield','pct',ann(div(X('free_cash_flow'),X('market_cap'))),'Free cash flow / market cap'+AN,optional=True)])]

def same_date(m,yi):
    p=m['period_info'][m['years'][yi]]
    if p['balance_date'] and p['flow_end']:
        return None if p['balance_date']==p['flow_end'] else f"Balance sheet date ({p['balance_date']}) differs from the cash flow period end ({p['flow_end']}); not comparable"
    return None if p['type']=='annual' else 'Interim comparative: balance sheet and cash flow dates not supplied or differ; not comparable'

def consecutive(m,yi):
    a,b=m['period_info'][m['years'][yi]],m['period_info'][m['years'][yi-1]]
    return None if a['type']=='annual' and b['type']=='annual' else 'Comparative is not the immediately preceding period (interim report); not comparable'

def LP_bs_cash(m):
    e=bs_cash(m)
    return ('L',e[1],-1) if e[0]=='L' else ('sub',('L',e[1][1],-1),('L',e[2][1],-1)) if e[0]=='sub' else LP('cash')

def prior_year_end(m,yi):
    return None if opens_next(m,yi-1) else 'Comparative balance sheet is not the opening date of this period; not comparable'

def check_spec(m):
    """(name, lhs, rhs, needs_prior, applicability rule, REVIEW-not-FAIL rule)"""
    attr=tagged(m,'attribution','income_statement')
    extra=[('Profit attribution: owners + others = net income',L('net_income'),add(L('net_income_attributable'),*[L(x) for x in attr]),False,None,False)] if attr else []
    if any(m['period_info'][y]['type']=='interim' for y in m['years']):
        extra.append(('Opening cash = prior year-end balance sheet cash',L('cash_begin'),LP_bs_cash(m),True,prior_year_end,True))
    return extra+[
        ('Balance sheet: assets = liabilities + equity',L('total_assets'),first(L('total_liabilities_and_equity'),add(L('total_liabilities'),L('equity'))),False,None,False),
        ('Cash flow: opening cash + net flows = closing cash',L('cash_end'),first(*cash_bridge_options(m)),False,None,False),
        ('Cash flow closing cash = balance sheet cash (excl. restricted)',L('cash_end'),bs_cash(m),False,same_date,True),
        ('Profit before tax: income statement = cash flow statement',L('cf_pretax_income'),L('pretax_income'),False,None,False),
        ('Opening cash = prior-period closing cash',L('cash_begin'),LP('cash_end'),True,consecutive,False),
        ('Net income: income statement = cash flow statement',L('cf_net_income'),L('net_income'),False,None,False)]

# ------------------------------------------------------------------ analysis
def run_analysis(data):
    m=load_model(data); ctx=Ctx(m); years=m['years']; lines=m['lines']
    sched=schedule_spec(m); ratios=ratio_spec(m)
    specs={it['id']:it for _,items in sched+ratios for it in items}
    layout={'Schedules':[],'Ratios & Calculations':[]}
    for sheet,secs,keep in (('Schedules',sched,lambda it:available(it['expr'],lines,specs)),('Ratios & Calculations',ratios,lambda it:not it['optional'] or available(it['expr'],lines,specs))):
        for title,items in secs:
            kept=[it for it in items if keep(it)]
            if kept: layout[sheet].append((title,kept))
            for it in kept: ctx.items[it['id']]=dict(it,sheet=sheet)
    # Row positions must be known before any formula is generated.
    statement_rows={st:layout_rows(m['order'][st],lambda lid:lines[lid]['section'],lambda lid:lid in GRAND_TOTALS,STATEMENTS[st],ctx.line_addr) for st in m['order'] if m['order'][st]}
    computed_rows={sh:layout_rows([it['id'] for _,its in secs for it in its],None,None,sh,ctx.item_addr,sections=secs) for sh,secs in layout.items()}
    def src_refs(keys,y):
        out=[]
        for k in keys:
            lid,yr=k[:k.index('[')],int(k[k.index('[')+1:-1])
            if lid in lines and yr in lines[lid]['sources']:
                s=lines[lid]['sources'][yr]; out.append(f"{lid}[{yr}]: {s.get('document')} @ {s.get('location')}")
        return '; '.join(out)
    checks=[]
    for yi,y in enumerate(years):
        for lid,ln in lines.items():
            v,kind=m['resolved'][(lid,y)]; rep=ln['values'].get(y)
            if ln['total_of'] and rep is not None:
                if kind=='formula': checks.append(mk_check(y,f"Subtotal ties: {ln['label']}",rep,v,src_refs([f'{lid}[{y}]'],y),('const',rep),('ref',lid)))
                elif kind=='reported_rounded':
                    sv=sum(m['resolved'][(c,y)][0] for c in ln['total_of'])
                    ck=mk_check(y,f"Subtotal ties: {ln['label']}",rep,sv,src_refs([f'{lid}[{y}]'],y),('ref',lid),('refs',list(ln['total_of'])))   # live: printed total cell vs the sum of its component cells
                    q=1 if all(float(x).is_integer() for x in [m['resolved'][(c,y)][0] for c in ln['total_of']]+[rep]) else 0.01
                    ck['tolerance']=max(ck['tolerance'],round(0.51*len(ln['total_of'])*q,6)); ck['rounding_tol']=True   # same threshold as load_model; the live Excel check uses it too
                    ck['status']='pass'; ck['message']=f'Printed total kept; its components add up to {sv:,.2f} (difference {rep-sv:,.2f} is rounding in the source; tolerance {ck["tolerance"]:.3f})'
                    checks.append(ck)
                else: checks.append(mk_check(y,f"Subtotal ties: {ln['label']}",None,None,src_refs([f'{lid}[{y}]'],y),None,None,'Components incomplete; reported total used'))
            if lid in EXPECTED_SIGN and v is not None and v*EXPECTED_SIGN[lid]<0:
                checks.append({'year':y,'check':f"Sign convention: {ln['label']}",'status':'fail','difference':None,'lhs':v,'rhs':None,'tolerance':None,'message':f"Expected {'positive' if EXPECTED_SIGN[lid]>0 else 'negative (outflow/expense)'} value",'source_refs':src_refs([f'{lid}[{y}]'],y),'kind':'sign','line':lid})
        for name,lhs,rhs,needs_prior,rule,review in check_spec(m):
            if not (available(lhs,lines,{}) and available(rhs,lines,{})) or (needs_prior and yi==0): continue
            refs=src_refs(list(ctx.leaves(lhs,yi,{}))+list(ctx.leaves(rhs,yi,{})),y)
            why=rule(m,yi) if rule else None
            if why: checks.append(mk_check(y,name,None,None,refs,None,None,why)); continue
            lv,lf=ctx.ev(lhs,yi,'Checks'); rv,rf=ctx.ev(rhs,yi,'Checks')
            c=mk_check(y,name,lv,rv,refs,('f',lf and strip_outer(lf)),('f',rf and strip_outer(rf)),'Missing inputs for validation' if lv is None or rv is None else None)
            if review and 'restricted_cash' not in lines:
                c['review_rule']=True
                if c['status']=='fail' and c['difference']<0:
                    c['status']='review'; c['message']+=(f"; balance sheet cash exceeds cash equivalents by {-c['difference']:,.2f} (restricted cash or deposits over 3 months)."
                                                         " Net debt uses the cash flow statement's cash equivalents where the dates match; add a sourced restricted_cash line to reconcile.")
            checks.append(c)
    audit=[]; metrics={y:{} for y in years}
    for sheet in layout:
        for _,items in layout[sheet]:
            for it in items:
                for yi,y in enumerate(years):
                    v,f=ctx.calc(it['id'],yi); metrics[y][it['id']]=v
                    inputs=ctx.leaves(it['expr'],yi,{}) if it['expr']!=DAYS else {}
                    audit.append({'year':y,'sheet':sheet,'metric':it['id'],'label':it['label'],'formula':it['definition'],'excel_formula':('='+f) if f else '',
                                  'inputs':json.dumps(inputs),'source_refs':src_refs(list(inputs),y),'value':round(v,9) if v is not None else None,'display':display(v,it['kind']),
                                  'status':'calculated' if v is not None else 'not_available','reason':'' if v is not None else 'Missing inputs, prior period required, or zero/negative denominator'})
    periods=[{'year':y,'days':m['days'][y],'label':m['period_info'][y]['label'],'period_type':m['period_info'][y]['type'],'balance_date':m['period_info'][y]['balance_date'],'flow_end':m['period_info'][y]['flow_end'],'values':{lid:m['resolved'][(lid,y)][0] for lid in lines},'metrics':metrics[y]} for y in years]
    statements={st:[{'id':lid,'label':lines[lid]['label'],'section':lines[lid]['section'],'subtotal':bool(lines[lid]['total_of']),'tags':lines[lid]['tags'],
                      'values':{str(y):m['resolved'][(lid,y)][0] for y in years},'sources':{str(y):s for y,s in lines[lid]['sources'].items()}} for lid in m['order'][st]] for st in m['order']}
    res={'company':m['company'],'currency':m['currency'],'unit':m['unit'],'basis':m['basis'],'industry':m['industry'],'fiscal_year_end':m['fiscal_year_end'],
         'schema_version':m['schema_version'],'years':years,'periods':periods,'statements':statements,'checks':checks,'audit':audit,
         'unaudited':m['unaudited'],'audited':m['audited'],'framework':m['framework'],'going_concern':m['going_concern'],'owners_profit_excludes_perpetual':m['owners_profit_excludes_perpetual'],'key_disclosures':m['key_disclosures'],'no_cash_flow_reason':m['no_cash_flow_reason'],'interim':m['interim'],'annualise':m['annualise'],'entity_type':m['entity_type'],'has_cash_flow':m['has_cash_flow'],'display_unit':m['display_unit'],'ebit_method':m['ebit_method'],'demo':is_demo(data),'generated_utc':datetime.now(timezone.utc).isoformat()}
    res['_render']={'model':m,'ctx':ctx,'layout':layout,'statement_rows':statement_rows,'computed_rows':computed_rows}
    return res

def mk_check(y,name,lhs,rhs,refs,lf,rf,missing=None):
    if lhs is None or rhs is None:
        return {'year':y,'check':name,'status':'not_tested','difference':None,'lhs':lhs,'rhs':rhs,'tolerance':None,'message':missing or 'Missing inputs for validation','source_refs':refs,'kind':'pair','lf':lf,'rf':rf}
    diff=lhs-rhs; tol=max(0.02,abs(lhs)*0.001)
    return {'year':y,'check':name,'status':'pass' if abs(diff)<=tol else 'fail','difference':round(diff,6),'lhs':lhs,'rhs':rhs,'tolerance':tol,
            'message':f'Tolerance {tol:.3f}; discrepancy {diff:.3f}','source_refs':refs,'kind':'pair','lf':lf,'rf':rf}

HEADER_ROW=5
def layout_rows(ids,section_of,is_grand,sheet,addr,sections=None):
    """Assign worksheet rows. Returns [(kind,row,payload)] with section headers and spacer rows."""
    rows=[]; r=HEADER_ROW+1
    if sections:
        for si,(title,items) in enumerate(sections):
            if si: r+=1
            rows.append(('section',r,title)); r+=1
            for it in items:
                rows.append(('item',r,it['id'])); addr[it['id']]=(sheet,r); r+=1
        return rows
    prev=object()
    for lid in ids:
        sec=section_of(lid)
        if sec!=prev:
            if sec is not None:
                if rows: r+=1
                rows.append(('section',r,SECTION_TITLES.get(sec,sec.replace('_',' ').capitalize()))); r+=1
            prev=sec
        if is_grand(lid) and rows and sec is None: r+=1
        rows.append(('line',r,lid)); addr[lid]=(sheet,r); r+=1
    return rows

def R_lines(res): return res['_render']['model']['lines'] if '_render' in res else {}

def column_labels(m):
    out=[]
    for y in m['years']:
        p=m['period_info'][y]
        out.append(f"{p['label']} | BS {fmt_date(p['balance_date'])}" if p['balance_date'] and p['flow_end'] and p['balance_date']!=p['flow_end'] else p['label'])
    return out

def pct_txt(v): return 'N/A' if v is None else (f'{v*100:,.2f}%' if abs(v)<0.01 else f'{v*100:,.1f}%')

def famt(v,res):
    """An amount in the unit the workbook displays (e.g. EUR thousands when the source is in ones)."""
    if v is None: return 'N/A'
    du=res.get('display_unit') or res.get('unit'); f=UNIT_FACTOR.get(res.get('unit'),1)/UNIT_FACTOR.get(du,1); x=v*f
    word={'ones':'','thousands':' thousand','ten_thousands':' ten-thousand','lakhs':' lakh','millions':' million','crores':' crore','billions':' billion'}.get(du,'')
    num=f'{x:,.0f}' if abs(x)>=100 or float(x).is_integer() else f'{x:,.1f}'
    return f"{res.get('currency') or ''} {num}{word}".strip()   # e.g. 'EUR 178,450 thousand': the reader sees currency and unit

CLIENT_RX=r"""client (?:money|funds?|cash|liabilit|balances?|accounts?)|safeguard|held (?:on behalf of|for) (?:clients?|customers?)|customer (?:funds|money)|segregated"""

def agent_hints(res):
    """Mapping suggestions for the agent: printed by analyze as HINT lines, never written into the workbook."""
    per=res['periods']; lines=R_lines(res); out=[]
    if 'operating_income' not in lines and 'ebit' not in lines and res.get('entity_type') not in FINANCIAL_MODEL and 'pretax_income' in lines:
        out.append("No operating profit line is mapped, so EBIT is derived from profit before tax and net interest; if the report gives EBIT or operating profit (e.g. a segment note or 'profit before net financing costs'), add it as operating_income or ebit.")
    if 'share_of_associates' in lines and 'ebitda' not in lines and 'share_of_associates_itda' not in lines:
        out.append("The report has associates/JVs and EBITDA is derived (it leaves out their EBITDA): add the company's statutory EBITDA (supplementary 'ebitda') if the report gives one (see mapping-rules 'EBITDA').")
    if not any({'non_recurring','impairment'} & set(l['tags']) and l['statement']=='income_statement' for l in lines.values()):
        for lid,l in lines.items():
            if l['statement']!='income_statement' or l['total_of']: continue
            if re.search(r'impairment|other charge|gain (?:on|from) (?:the )?(?:transfer|disposal|sale)|restructuring|one-?off|exceptional|exceptionnel',l['label'],re.I):
                for p in per:
                    v=p['values'].get(lid); ni=p['values'].get('net_income')
                    if v and ni and abs(v)>0.2*abs(ni): out.append(f"'{l['label']}' ({lid}) is {abs(v)/abs(ni):.0%} of net income in {p['label']}: if it is one-off, tag it non_recurring or impairment.")
    if res.get('entity_type')=='conglomerate' and res.get('has_cash_flow') and not any('fs_operating' in l['tags'] for l in lines.values()):
        out.append('Tag the banking/card/securities balance-sheet flows inside operating cash flow fs_operating to show free cash flow excluding them.')
    # C: a debt line given for some periods only leaves total debt, net debt and ROIC N/A in the others
    dl=[lid for lid,l in lines.items() if 'debt' in l['tags'] and not l['total_of']]
    for p in per:
        miss=[lid for lid in dl if p['values'].get(lid) is None]
        if dl and miss and len(miss)==len(dl) or (miss and any(p2['values'].get(m) is not None for p2 in per for m in miss)):
            out.append(f"Debt line(s) {', '.join(miss)} have no value in {p['label']}, so total debt, net debt and ROIC are N/A there: enter the figure from that period's note (comparative column or the prior report), or 0 only when the notes confirm there were no borrowings in that period; otherwise leave it empty (an undisclosed value is never 0).")
            break
    if res.get('entity_type') in ('payment_institution','asset_manager') and per[-1]['metrics'].get('current_ratio_ex_client') is None:
        out.append('Supply client_funds and client_liabilities to show liquidity excluding client money.')
    if any({'non_recurring','impairment'} & set(l['tags']) and l['statement']!='income_statement' for l in lines.values()):
        bad=[lid for lid,l in lines.items() if {'non_recurring','impairment'} & set(l['tags']) and l['statement']!='income_statement']
        out.append(f"One-off tags on non-income-statement lines are ignored ({', '.join(bad[:4])}): tag the income statement line instead (split it out of its face line with the note if needed).")
    if res.get('entity_type') not in FINANCIAL_MODEL+('payment_institution','asset_manager') and 'client_funds' not in lines:
        cl=[l['label'] for l in lines.values() if l['statement']=='balance_sheet' and re.search(CLIENT_RX,l['label'],re.I)]
        if cl: out.append(f"Balance-sheet labels mention client money ({'; '.join(cl[:3])}): if the company holds client or safeguarded funds (payment institution, broker, asset manager), set entity_type accordingly and supply client_funds and client_liabilities so the current ratio excluding client money is shown.")
    for lid,l in lines.items():
        if l['statement']!='income_statement' or l['total_of'] or {'non_recurring','impairment','attribution'} & set(l['tags']): continue
        if any(f"({lid})" in h for h in out): continue   # already raised above: one hint per line
        if not re.search(r'other (?:operating )?(?:income|gains?|expenses?|losses?|charges?)|gains?\b|remeasurement|fair value|disposal|exceptional|non-operating|营业外|资产处置|公允价值变动|投资收益|autres (?:produits|charges)|exceptionnel',l['label'],re.I): continue
        for p in per:
            v=p['values'].get(lid); ni=p['values'].get('net_income')
            if v and ni and abs(v)>0.5*abs(ni):
                out.append(f"'{l['label']}' ({lid}) is {abs(v)/abs(ni):.0%} of net income in {p['label']}: read its note and split out and tag any one-off part (e.g. remeasurement, disposal or fair-value gains) non_recurring."); break
    if 'perpetual_bonds' in lines and 'perpetual_distributions' not in lines and not res.get('owners_profit_excludes_perpetual'):
        out.append('Perpetual bonds are deducted from equity: add perpetual_distributions (profit attributable to perpetual holders) so ROE on ordinary equity can be shown, or set owners_profit_excludes_perpetual: true when the owners’ profit line already excludes them.')
    first=per[0]; et=res.get('entity_type')
    # client money: restricted cash that is large against current liabilities, or a disclosure that mentions client money
    if et not in FINANCIAL_MODEL+('payment_institution','asset_manager') and 'client_funds' not in lines and 'restricted_cash' in lines:
        dtext=' '.join(str(d.get('text','')) for d in res.get('key_disclosures') or [])
        big=any((p['values'].get('restricted_cash') or 0)>0.25*(p['values'].get('current_liabilities') or float('inf')) for p in per)
        cm=bool(re.search(CLIENT_RX,dtext,re.I))
        if big or cm:
            out.append("Restricted cash is "+('large against current liabilities' if big else 'present')+(' and the disclosures mention client money' if cm else '')+": if it is client or safeguarded money, set entity_type (payment_institution / asset_manager / broker_dealer) and add client_funds and client_liabilities so liquidity excluding client money is shown.")
    # first-period returns: opening balances from the statement of changes in equity
    if et not in FINANCIAL_MODEL and 'opening_equity' not in lines and len(per)>=2 and first['values'].get('equity') is not None and first['metrics'].get('roe') is None and per[-1]['metrics'].get('roe') is not None:
        out.append(f"{first['label']} ROE, ROA and ROIC are N/A for lack of opening balances: add opening_equity (and opening_shareholders_equity) from the opening row of the statement of changes in equity, in the first period's column.")
    # key disclosures are expected on every run
    if not res.get('key_disclosures'):
        out.append('No key_disclosures supplied: add 2-5 (text + page) from the notes already read - impairments, one-off gains, restatements, going concern, acquisitions or disposals, regulatory breaches.')
    # disposal / remeasurement gains of any material size are one-off candidates
    for lid,l in lines.items():
        if l['statement']!='income_statement' or l['total_of'] or {'non_recurring','impairment','attribution'} & set(l['tags']) or any(f"({lid})" in h for h in out): continue
        if re.search(r'\bexcl(?:\.|uding)?\b|\bother than\b|\bnet of\b',l['label'],re.I): continue
        if re.search(r'gains?\s+(?:or losses?\s+)?(?:on|from)\s+(?:the\s+)?(?:sales?|disposals?|transfer|remeasurement)|remeasurement gain|losses?\s+on\s+(?:the\s+)?disposals?\s+of\s+(?:subsidiar|associate|joint|business|investment)',l['label'],re.I):
            for p in per:
                v=p['values'].get(lid); ni=p['values'].get('net_income')
                if v and ni and abs(v)>=0.02*abs(ni):
                    out.append(f"'{l['label']}' ({lid}) is a disposal/remeasurement item ({abs(v)/abs(ni):.0%} of net income in {p['label']}): tag it non_recurring unless the note shows it is recurring.")
                    break
    return out

def findings(res):
    per=res['periods']; last=per[-1]['metrics']; prev=per[-2]['metrics'] if len(per)>1 else {}; lv=per[-1]['values']; pv=per[-2]['values'] if len(per)>1 else {}
    lab=[p['label'] for p in per]; lines=R_lines(res)
    cfail=[c for c in res['checks'] if c['status']=='fail']; out=[]; warn=[]
    if res.get('going_concern'): warn.append('The auditor reports a material uncertainty related to going concern.')
    if lv.get('revenue') in (0,0.0) and (pv.get('revenue') or 0)>0: warn.append(f"No revenue in {lab[-1]} ({lab[-2]}: {famt(pv['revenue'],res)}): the company appears to have stopped trading, so operating margins, turnover and growth are not meaningful.")
    if last.get('revenue_growth') is not None:out.append(f"Revenue {'grew' if last['revenue_growth']>0 else 'declined' if last['revenue_growth']<0 else 'was flat'} {abs(last['revenue_growth'])*100:.1f}% versus the prior period.")
    imp_ids=[lid for lid,l in lines.items() if 'impairment' in l['tags'] and l['statement']=='income_statement']; after_imp=[]
    if 'ebitda' in lines and imp_ids:
        for p in per:
            I=sum(p['values'].get(x) or 0 for x in imp_ids); rv,dv=p['metrics'].get('ebitda'),p['metrics'].get('ebitda_derived')
            if I and rv is not None and dv is not None: after_imp.append((p,I,abs(rv-(dv+I))<abs(rv-dv)))
    ex_imp=bool(after_imp) and all(a for _,_,a in after_imp)
    if ex_imp:
        ys=', '.join(f"{p['label']} ({famt(I,res)})" for p,I,_ in after_imp)
        lv_=[f"{p['label']} {display(p['metrics'].get('net_debt_to_ebitda_ex_imp'),'x')}" for p in per if p['metrics'].get('net_debt_to_ebitda_ex_imp') is not None]
        warn.append(f"The reported EBITDA is stated after the impairments tagged as one-off in {ys}"+(f"; before them, net debt / EBITDA is {', '.join(lv_)}." if lv_ else '.'))
    for name,label,kind in [('net_margin','Net margin','pct'),('operating_margin','EBIT margin','pct'),('cash_conversion','Cash conversion','x'),
                            ('net_debt_to_ebitda_ex_imp' if ex_imp else 'net_debt_to_ebitda','Net debt / EBITDA before impairments' if ex_imp else 'Net debt / EBITDA','x')]:
        if last.get(name) is not None and prev.get(name) is not None and not (name.startswith('net_debt_to_ebitda') and (last[name]<=0 or prev[name]<=0)):
            d=last[name]-prev[name]; better=d<0 if name.startswith('net_debt_to_ebitda') else d>0
            f=pct_txt if kind=='pct' else (lambda v:display(v,kind))
            out.append(f"{label} {'improved' if better and d else 'weakened' if d else 'was unchanged'} ({f(prev[name])} → {f(last[name])}).")
    if last.get('cash_conversion_adj') is not None:
        out.append(f"Including distributions from associates/JVs (classified as investing), cash conversion is {display(last['cash_conversion_adj'],'x')}"+(f" ({display(prev.get('cash_conversion_adj'),'x')} in {lab[-2]})" if prev.get('cash_conversion_adj') is not None else '')+'.')
    elif lv.get('ocf') is not None and lv.get('net_income') is not None and lv['ocf']<lv['net_income']:
        out.append('Operating cash flow is below net income; review working capital and non-cash items before inferring earnings quality.')
    nd=last.get('net_debt')
    if nd is not None and nd<0: out.append(f"Net cash position of {famt(-nd,res)} in {lab[-1]}: debt-to-EBITDA multiples are not meaningful.")
    # one-off items
    one=[lid for lid,l in lines.items() if {'non_recurring','impairment'} & set(l['tags']) and l['statement']=='income_statement']
    for p in per:
        ni=p['values'].get('net_income'); tot=sum(p['values'].get(x) or 0 for x in one)
        if one and ni and abs(tot)>0.2*abs(ni): warn.append(f"{p['label']} results include one-off items of {famt(tot,res)} ({abs(tot)/abs(ni):.0%} of net income); margins, growth and EBITDA should be read with the 'before one-off items' metrics.")
    if not one:
        for lid,l in lines.items():
            if l['statement']!='income_statement' or l['total_of']: continue
            if re.search(r'impairment|other charge|gain (?:on|from) (?:the )?(?:transfer|disposal|sale)|restructuring|one-?off|exceptional|exceptionnel',l['label'],re.I):
                for p in per:
                    v=p['values'].get(lid); ni=p['values'].get('net_income')
                    if v and ni and abs(v)>0.2*abs(ni): warn.append(f"'{l['label']}' of {famt(v,res)} in {p['label']} is {abs(v)/abs(ni):.0%} of net income and may be a one-off; margins and EBITDA include it.")
    for p in per:
        nm=p['metrics'].get('net_margin')
        if nm is not None and nm>1: warn.append(f"Net margin of {pct_txt(nm)} in {p['label']} exceeds 100%: profit comes from items outside revenue (e.g. one-off gains or interest income).")
    # balance swings and tax-driven earnings
    for k,name in (('equity','Equity'),('total_assets','Total assets')):
        a,b=pv.get(k),lv.get(k)
        if a and b and a>0 and b>0 and max(a,b)/min(a,b)>5: warn.append(f"{name} moved from {famt(a,res)} to {famt(b,res)} (more than 5×, e.g. a large dividend or capital reduction); average-based returns are N/A.")
    if prev:
        pt0,pt1,ni0,ni1=pv.get('pretax_income'),lv.get('pretax_income'),pv.get('net_income'),lv.get('net_income')
        e0,e1=prev.get('effective_tax_rate'),last.get('effective_tax_rate'); xa=' excluding the share of associates/JVs' if 'share_of_associates' in lines else ''
        if None not in (pt0,pt1,ni0,ni1) and pt0>0 and ni0>0 and ((pt1-pt0)*(ni1-ni0)<0 or (e0 is not None and e1 is not None and abs(e1-e0)>0.10)):
            out.append(f"Profit before tax moved {(pt1/pt0-1)*100:+.1f}% while net income moved {(ni1/ni0-1)*100:+.1f}%: driven by the tax charge"+(f" (effective rate{xa} {pct_txt(e0)} → {pct_txt(e1)})" if e0 is not None and e1 is not None else '')+'.')
    e1=last.get('effective_tax_rate')
    if e1 is not None and not 0.15<=e1<=0.40: out.append(f"Effective tax rate{' (excluding the share of associates/JVs)' if 'share_of_associates' in lines else ''} of {pct_txt(e1)} in {lab[-1]} is outside 15–40%; NOPAT and ROIC use it, so read them with care.")
    nm=last.get('net_margin')
    if nm is not None and 0<nm<0.01: out.append('Thin net margin (below 1%): small cost, price or hedge movements swing profit, and cash conversion (OCF / net income) is volatile.')
    if 'share_of_associates' in lines and 'ebitda' not in lines and 'share_of_associates_itda' not in lines:
        warn.append("EBITDA is derived as EBIT + D&A and excludes associates'/JVs' interest, tax and D&A, so EBITDA-based ratios can differ from the company's own EBITDA.")
    perp=[lid for lid,l in lines.items() if 'perpetual' in l['tags'] and 'debt' in l['tags']]
    if 'perpetual_bonds' in lines and 'perpetual_distributions' not in lines and not res.get('owners_profit_excludes_perpetual') and last.get('roe') is not None:
        warn.append('Perpetual bonds are part of equity attributable to owners but the distributions to their holders are not given, so return on equity is shown on net income / total equity rather than on ordinary shareholders\u2019 equity.')
    if perp: warn.append('Perpetual securities are classified as debt in at least one period; debt and leverage are not comparable across periods. See "Debt excluding perpetual securities".')
    if res.get('annualise') and any(last.get(k) is not None for k in ('roe','roa','roic','asset_turnover')):
        out.append('Periods are not all 12 months: flow ratios compare like-for-like periods only, and return and turnover ratios are annualised (×365/days).')
    et=res.get('entity_type','operating')
    if et in FINANCIAL_MODEL: out.append(f"Financial institution ({et.replace('_',' ')}): liquidity, working-capital, EBITDA and net-debt measures for operating companies do not apply and are omitted; sector metrics are shown where the inputs were supplied.")
    elif et=='conglomerate':
        out.append('Group with material financial-services operations: operating-company metrics are shown, with financial-services metrics where supplied. Bank deposits and financial-services funding are excluded from debt; net debt uses cash excluding the financial businesses'+('.' if 'cash_non_financial' in lines else ' (not supplied, so net-debt measures are N/A; gross debt / EBITDA is shown instead).')+' Asset-based ratios (ROA, asset turnover, debt / assets) include the financial businesses\u2019 balance sheets.')
        if not any('fs_operating' in l['tags'] for l in lines.values()) and res.get('has_cash_flow'):
            warn.append('Operating cash flow includes banking/card/securities balance-sheet flows (deposits, loans, securities); free cash flow is not comparable with operating companies.')
    elif et in ('payment_institution','asset_manager'):
        out.append(f"{et.replace('_',' ').capitalize()}: the balance sheet may include client or safeguarded funds"+('; see the current ratio excluding client funds.' if last.get('current_ratio_ex_client') is not None else '; liquidity excluding client funds is not shown because they are not separately disclosed.'))
    if not res.get('has_cash_flow'): out.append('No cash flow statement: '+(res.get('no_cash_flow_reason') or 'not presented in the source')+'. Cash flow metrics and checks are not available.')
    if res.get('unaudited'): warn.insert(0,'Source statements are UNAUDITED.')
    if cfail: warn.insert(0,f"WARNING: {len(cfail)} accounting reconciliation check(s) failed. Findings are preliminary until resolved.")
    out=warn+out
    return out or ['Available data are insufficient for a robust multi-year conclusion; review missing metrics and source completeness.']

# ------------------------------------------------------------------- HTML
def report_html(res):
    R=res['_render']; m=R['model']; years=res['years']; checks=res['checks']; audits=res['audit']; cfail=[c for c in checks if c['status']=='fail']
    scale=10**(3*m['display_commas']); pi=m['period_info']
    def dv(v,kind): return display(v/scale if kind=='num' and v is not None else v,kind)
    flow_h=column_labels(m)
    def esc(s):return html.escape(str(s))
    def table(headers,rows,cls=()):
        body=''.join(f'<tr class="{c}">'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row,c in zip(rows,list(cls)+['']*len(rows)))
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+body+'</tbody></table></div>'
    st_html=''
    for st,rows in R['statement_rows'].items():
        tr=[];cl=[]
        for kind,_,p in rows:
            if kind=='section': tr.append([p]+['']*len(years)); cl.append('sec')
            else:
                ln=m['lines'][p]; tr.append([ln['label']]+[dv(m['resolved'][(p,y)][0],'raw' if st=='supplementary' else 'num') for y in years]); cl.append('tot' if ln['total_of'] or p in GRAND_TOTALS else '')
        st_html+=f'<h3>{esc(STATEMENTS[st])}</h3>'+table(['Line item']+([pi[y]['balance_label'] for y in years] if st=='balance_sheet' else flow_h),tr,cl)
    rt=[];rc=[]
    for title,items in R['layout']['Ratios & Calculations']:
        rt.append([title]+['']*len(years)); rc.append('sec')
        for it in items: rt.append([it['label']]+[dv(p['metrics'].get(it['id']),it['kind']) for p in res['periods']]); rc.append('')
    checktable=table(['Year','Check','Status','Difference','Details','Source refs'],[[c['year'],c['check'],c['status'],fmt(c['difference']),c['message'],c['source_refs']] for c in checks])
    audittable=table(['Year','Metric','Definition','Excel formula','Result','Status'],[[a['year'],a['label'],a['formula'],a['excel_formula'],a['display'],a['status']] for a in audits if a['sheet']!='Schedules'])
    disc=[(str(d.get('text','')),((d['source'].get('location','') if isinstance(d.get('source'),dict) else d.get('source')) or '') if d.get('source') else '') for d in res.get('key_disclosures') or []]
    disc_html=('<h2>Key disclosures (from the report)</h2><ul>'+''.join('<li>'+esc(t)+(f' <span class="sub">[{esc(s)}]</span>' if s else '')+'</li>' for t,s in disc)+'</ul>') if disc else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Financial Intelligence — {esc(res['company'])}</title><style>body{{font:15px/1.55 system-ui,Arial,sans-serif;color:#15243b;background:#f1f5fa;margin:0}}main{{max-width:1100px;margin:36px auto;background:white;padding:40px;border-radius:16px;box-shadow:0 8px 30px #172b4d15}}h1{{font-size:30px;margin:0}}h2{{margin-top:38px;padding-bottom:9px;border-bottom:2px solid #dbe8f4}}h3{{margin:24px 0 4px;color:#1f3864}}.sub{{color:#607188}}.flag{{padding:14px;background:#fff1e8;border-left:4px solid #df7a24}}.ok{{padding:14px;background:#eaf6f2;border-left:4px solid #16896d}}table{{border-collapse:collapse;width:100%;font-size:12px;margin:10px 0 22px}}td,th{{padding:7px 9px;border-bottom:1px solid #e2e8f0;text-align:right;vertical-align:top}}td:first-child,th:first-child{{text-align:left}}th{{background:#1f3864;color:white}}tr.sec td{{background:#dce6f1;font-weight:600;color:#1f3864}}tr.tot td{{font-weight:600;border-top:1px solid #8aa0bf}}.scroll{{overflow-x:auto}}footer{{color:#526475;font-size:12px;margin-top:30px}}@media print{{body{{background:white}}main{{margin:0;box-shadow:none;padding:12px}}}}</style></head><body><main>{'<div class="flag" style="background:#fde8e7;border-color:#b42318;color:#b42318;font-weight:700">DEMO DATA: synthetic figures for testing only. This is not an analysis of any real company.</div>' if res.get('demo') else ''}<p class="sub">FINANCIAL STATEMENT INTELLIGENCE · AUDITABLE ANALYSIS</p><h1>{esc(res['company'])}</h1><p class="sub">{esc(res['currency'])} · {esc(m['display_unit'])} · {esc(res['basis'])} · {esc(flow_h[0])} – {esc(flow_h[-1])}{' · <strong>UNAUDITED</strong>' if m['unaudited'] else ''}</p><div class="{'flag' if cfail else 'ok'}"><strong>{'Reconciliation issues detected' if cfail else 'No detected reconciliation failures'}</strong><div>{len(cfail)} failed checks; {sum(c['status']=='not_tested' for c in checks)} checks not testable. A passing check does not prove audit assurance or extraction accuracy.</div></div><h2>Executive assessment</h2><ul>{''.join('<li>'+esc(f)+'</li>' for f in findings(res))}</ul>{disc_html}<p><strong>Interpretation limits:</strong> Automated findings describe observed movements only. Missing fields, business models, notes and restatements may change conclusions. Do not treat this report as investment advice.</p><h2>Financial statements</h2>{st_html}<h2>Ratio and trend dashboard</h2>{table(['Ratio / metric']+flow_h,rt,rc)}<h2>Reconciliation controls</h2>{checktable}<h2>Calculation register</h2>{audittable}<footer>Expenses and cash outflows are shown as negative values. Source references appear in each calculation and check; detailed source metadata remains in analysis.json and the workbook Sources sheet. Generated {esc(res['generated_utc'])}. This report must be reviewed against the original audited sources.</footer></main></body></html>'''

def csv_safe(v):
    """Text that a spreadsheet would run as a formula (leading = + - @ or a control character) is exported as literal text:
    labels come from the uploaded statement, and the audit's Excel formulas are documentation, not something to execute."""
    if isinstance(v,str) and v[:1] in ('=','+','-','@','\t','\r') and not re.fullmatch(r'[-+]?\d[\d,]*(?:\.\d+)?',v): return "'"+v
    return v

def write_csv(path,rows,fields):
    with open(path,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows({k:csv_safe(x) for k,x in r.items()} for r in rows)

# ------------------------------------------------------------------- XLSX
NAVY='1F3864'; SECTION='DCE6F1'; INPUT='0000CC'; GREY='6B7280'; RULE='8EA9C8'
NUMFMT={'num':'#,##0.0_);(#,##0.0);"–"_)','raw':'#,##0.0_);(#,##0.0);"–"_)','ps':'#,##0.00_);(#,##0.00);"–"_)','pct':'0.0%_);(0.0%);"–"_)','x':'0.00"x"_);(0.00"x");"–"_)','days':'#,##0.0_);(#,##0.0);"–"_)','int':'0_)'}

class Styles:
    BUILTIN={'General':0,'0':1,'0.00':2,'#,##0':3,'#,##0.00':4,'0%':9,'0.00%':10}
    def __init__(self):
        self.fonts=[{}]; self.fills=[None,'gray125']; self.borders=[{}]; self.fmts={}; self.xfs=[(0,0,0,0,None)]; self.cache={}
    def __call__(self,font=None,fill=None,border=None,fmt=None,align=None):
        key=json.dumps([font,fill,border,fmt,align],sort_keys=True)
        if key not in self.cache:
            def idx(lst,v):
                if v not in lst: lst.append(v)
                return lst.index(v)
            fid=idx(self.fonts,font or {}); fl=idx(self.fills,fill) if fill else 0; bd=idx(self.borders,border or {})
            nf=self.BUILTIN.get(fmt) if fmt in self.BUILTIN else self.fmts.setdefault(fmt,164+len(self.fmts)) if fmt else 0
            self.xfs.append((nf,fid,fl,bd,align)); self.cache[key]=len(self.xfs)-1
        return self.cache[key]
    def xml(self):
        def font(f):
            return '<font>'+('<b/>' if f.get('b') else '')+('<i/>' if f.get('i') else '')+f'<sz val="{f.get("sz",10)}"/><color rgb="FF{f.get("color","1F2937")}"/><name val="Aptos"/><family val="2"/></font>'
        def fill(f):
            if f is None: return '<fill><patternFill patternType="none"/></fill>'
            if f=='gray125': return '<fill><patternFill patternType="gray125"/></fill>'
            return f'<fill><patternFill patternType="solid"><fgColor rgb="FF{f}"/><bgColor indexed="64"/></patternFill></fill>'
        def border(b):
            side=lambda s:(f'<{s} style="{b[s]}"><color rgb="FF{b.get("color",RULE)}"/></{s}>' if s in b else f'<{s}/>')
            return '<border>'+''.join(side(s) for s in ('left','right','top','bottom'))+'<diagonal/></border>'
        def xf(nf,fid,fl,bd,al):
            a=''
            if al: a='<alignment'+''.join(f' {k}="{v}"' for k,v in (('horizontal',al.get('h')),('vertical',al.get('v')),('indent',al.get('indent')),('wrapText','1' if al.get('wrap') else None)) if v)+'/>'
            return f'<xf numFmtId="{nf}" fontId="{fid}" fillId="{fl}" borderId="{bd}" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">{a}</xf>'
        nfx=''.join(f'<numFmt numFmtId="{i}" formatCode="{html.escape(c,quote=True)}"/>' for c,i in self.fmts.items())
        dxf=lambda fg,bg:f'<dxf><font><b/><color rgb="FF{fg}"/></font><fill><patternFill><bgColor rgb="FF{bg}"/></patternFill></fill></dxf>'
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                +(f'<numFmts count="{len(self.fmts)}">{nfx}</numFmts>' if self.fmts else '')
                +f'<fonts count="{len(self.fonts)}">'+''.join(font(f) for f in self.fonts)+'</fonts>'
                +f'<fills count="{len(self.fills)}">'+''.join(fill(f) for f in self.fills)+'</fills>'
                +f'<borders count="{len(self.borders)}">'+''.join(border(b) for b in self.borders)+'</borders>'
                +'<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                +f'<cellXfs count="{len(self.xfs)}">'+''.join(xf(*x) for x in self.xfs)+'</cellXfs>'
                +'<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                +'<dxfs count="3">'+dxf('0B6E4F','E3F4EC')+dxf('B42318','FDE8E7')+dxf('8A5A00','FFF4D6')+'</dxfs></styleSheet>')

class Sheet:
    def __init__(self,name,tab=None):
        self.name=name; self.tab=tab; self.cells={}; self.widths={}; self.heights={}; self.freeze=None; self.merges=[]; self.cf=[]; self.autofilter=None
    def put(self,r,c,v=None,s=0,f=None): self.cells[(r,c)]=(v,s,f)
    def xml(self,selected):
        def esc(s): return html.escape(str(s),quote=False)
        rows={}
        for (r,c),cell in self.cells.items(): rows.setdefault(r,[]).append((c,cell))
        out=[]
        for r in sorted(rows):
            cells=[]
            for c,(v,s,f) in sorted(rows[r]):
                ref=f'{col(c)}{r}'; st=f' s="{s}"' if s else ''
                if f is not None:
                    fx=f'<f>{esc(f.lstrip("="))}</f>'
                    if v is None: cells.append(f'<c r="{ref}"{st}>{fx}</c>')
                    elif isinstance(v,str): cells.append(f'<c r="{ref}"{st} t="str">{fx}<v>{esc(v)}</v></c>')
                    else: cells.append(f'<c r="{ref}"{st}>{fx}<v>{num(v)}</v></c>')
                elif v is None: cells.append(f'<c r="{ref}"{st}/>')
                elif isinstance(v,(int,float)) and not isinstance(v,bool): cells.append(f'<c r="{ref}"{st}><v>{num(v)}</v></c>')
                else: cells.append(f'<c r="{ref}"{st} t="inlineStr"><is><t xml:space="preserve">{esc(v)}</t></is></c>')
            ht=f' ht="{self.heights[r]}" customHeight="1"' if r in self.heights else ''
            out.append(f'<row r="{r}"{ht}>'+''.join(cells)+'</row>')
        pane=''
        if self.freeze:
            fr,fc=self.freeze; tl=f'{col(fc)}{fr+1}'
            pane=(f'<pane xSplit="{fc}" ' if fc else '<pane ')+(f'ySplit="{fr}" ' if fr else '')+f'topLeftCell="{tl}" activePane="{"bottomRight" if fc and fr else "bottomLeft" if fr else "topRight"}" state="frozen"/>'
        cols=''.join(f'<col min="{c+1}" max="{c+1}" width="{w}" customWidth="1"/>' for c,w in sorted(self.widths.items()))
        merges=f'<mergeCells count="{len(self.merges)}">'+''.join(f'<mergeCell ref="{m}"/>' for m in self.merges)+'</mergeCells>' if self.merges else ''
        cf=''.join(f'<conditionalFormatting sqref="{rng}">'+''.join(f'<cfRule type="cellIs" dxfId="{d}" priority="{p}" operator="equal"><formula>"{v}"</formula></cfRule>' for p,(v,d) in enumerate(rules,1))+'</conditionalFormatting>' for rng,rules in self.cf)
        tab=f'<tabColor rgb="FF{self.tab}"/>' if self.tab else ''
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'<sheetPr>{tab}<pageSetUpPr fitToPage="1"/></sheetPr><sheetViews><sheetView showGridLines="0" {"tabSelected=\"1\" " if selected else ""}workbookViewId="0">{pane}</sheetView></sheetViews>'
                '<sheetFormatPr defaultRowHeight="15"/>'+(f'<cols>{cols}</cols>' if cols else '')+'<sheetData>'+''.join(out)+'</sheetData>'
                +(f'<autoFilter ref="{self.autofilter}"/>' if self.autofilter else '')+merges+cf
                +'<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/><pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/></worksheet>')

def save_workbook(path,sheets,styles):
    n=len(sheets)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'+''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,n+1))+'<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><bookViews><workbookView activeTab="0"/></bookViews><sheets>'+''.join(f'<sheet name="{html.escape(s.name,quote=True)}" sheetId="{i}" r:id="rId{i}"/>' for i,s in enumerate(sheets,1))+'</sheets>'
                   +'<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,n+1))+f'<Relationship Id="rId{n+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        for i,s in enumerate(sheets,1): z.writestr(f'xl/worksheets/sheet{i}.xml',s.xml(i==1))
        z.writestr('xl/styles.xml',styles.xml())

def write_xlsx(path, res):
    """Formatted workbook: statements with live subtotal formulas, dependent schedules, ratio formulas, checks and provenance."""
    R=res['_render']; m=R['model']; ctx=R['ctx']; years=res['years']; ny=len(years); S=Styles()
    S()  # default
    title=S(font={'b':1,'sz':16,'color':NAVY}); subtitle=S(font={'sz':10,'color':GREY}); legend=S(font={'i':1,'sz':9,'color':GREY})
    hdr=S(font={'b':1,'sz':10,'color':'FFFFFF'},fill=NAVY,align={'h':'center','v':'center'}); hdr_l=S(font={'b':1,'sz':10,'color':'FFFFFF'},fill=NAVY,align={'h':'left','v':'center','indent':1})
    sec=S(font={'b':1,'sz':10,'color':NAVY},fill=SECTION); lab=S(align={'indent':2}); lab_sub=S(font={'b':1},border={'top':'thin'},align={'indent':1}); lab_grand=S(font={'b':1},border={'top':'thin','bottom':'double'},align={'indent':1})
    note=S(font={'sz':9,'color':GREY},align={'indent':1}); na=S(font={'i':1,'color':'9CA3AF'},align={'h':'right'}); text=S(); text_c=S(align={'h':'center','v':'top'})
    numfmt=dict(NUMFMT); cm=','*m['display_commas']
    numfmt['num']=f'#,##0.0{cm}_);(#,##0.0{cm});"–"_)'
    def numst(kind,role='formula',style='line'):
        f={'b':1} if style!='line' else {}
        if role=='input': f=dict(f,color=INPUT)
        b={'top':'thin','bottom':'double'} if style=='grand' else {'top':'thin'} if style=='subtotal' else None
        return S(font=f or None,fmt=numfmt[kind],border=b)
    roles={'line':lab,'subtotal':lab_sub,'grand':lab_grand}
    pi=m['period_info']; flow_h=column_labels(m); bal_h=[pi[y]['balance_label'] for y in years]
    meta=(f"{m['company']}  ·  {m['currency']} {m['display_unit']}"+(f" (source figures in {m['unit']})" if m['display_commas'] else '')+f"  ·  {m['basis']}"
          +(f"  ·  {m['framework']}" if m['framework'] else '')+(f"  ·  FY ends {m['fiscal_year_end']}" if m['fiscal_year_end'] else '')+('  ·  UNAUDITED' if m['unaudited'] else '  ·  audited' if m['audited'] else '')
          +('  ·  GOING CONCERN UNCERTAINTY' if m['going_concern'] else '')
          +(f"  ·  {m['entity_type'].replace('_',' ').upper()}" if m['entity_type']!='operating' else ''))
    src_note=f"  ·  Amounts in source units ({m['currency']} {m['unit']})" if m['display_commas'] else ''
    def head(ws,name,extra_cols,headers=None):
        ws.put(1,0,name,title); ws.heights[1]=24; ws.put(2,0,meta,subtitle)
        ws.put(3,0,'Blue = source input  ·  Black = formula  ·  (x) = negative / outflow  ·  N/A = not computable from supplied data (never zero)',legend)
        ws.put(HEADER_ROW,0,'' if name!='Ratios & Calculations' else 'Metric',hdr_l)
        for yi,h in enumerate(headers or flow_h): ws.put(HEADER_ROW,1+yi,h,hdr)
        for k,h in enumerate(extra_cols): ws.put(HEADER_ROW,1+ny+k,h,hdr_l)
        ws.heights[HEADER_ROW]=20; ws.freeze=(HEADER_ROW,1); ws.widths[0]=46
        for yi in range(ny): ws.widths[1+yi]=max(13,len(str((headers or flow_h)[yi]))+3)
    def fit_labels(ws):
        vis=lambda t:sum(2 if ord(ch)>=0x2E80 else 1 for ch in str(t))
        ws.widths[0]=min(90,max([46]+[vis(v)*0.95+6 for (r,c),(v,_,_) in ws.cells.items() if c==0 and r>HEADER_ROW and v]))
    def section_row(ws,r,label,width):
        for c in range(width): ws.put(r,c,label if c==0 else None,sec)
    sheets=[]
    summary=Sheet('Summary',NAVY); sheets.append(summary)
    # statements
    for st,rows in R['statement_rows'].items():
        ws=Sheet(STATEMENTS[st],'2F5597'); head(ws,STATEMENTS[st],['Source (latest year)'],bal_h if st=='balance_sheet' else None); ws.widths[1+ny]=44; sheets.append(ws)
        amt='raw' if st=='supplementary' else 'num'
        for kind,r,p in rows:
            if kind=='section': section_row(ws,r,p,ny+2); continue
            ln=m['lines'][p]; style='grand' if p in GRAND_TOTALS and ln['total_of'] else 'subtotal' if ln['total_of'] else 'line'
            ws.put(r,0,ln['label'],roles[style])
            for yi,y in enumerate(years):
                v,k=m['resolved'][(p,y)]
                if v is None: ws.put(r,1+yi,'N/A',na)
                elif k=='formula':
                    refs=[ctx.line_addr[c] for c in ln['total_of']]; rr=[row for sh,row in refs]
                    same=all(sh==ws.name for sh,_ in refs)
                    if same and rr==list(range(rr[0],rr[0]+len(rr))) and len(rr)>1: f=f'SUM({col(1+yi)}{rr[0]}:{col(1+yi)}{rr[-1]})'
                    else: f='+'.join(ctx.ref(sh,row,yi,ws.name) for sh,row in refs)
                    ws.put(r,1+yi,v,numst(amt,'formula',style),f)
                else: ws.put(r,1+yi,v,numst(amt,'input',style))
            src=next((ln['sources'][y] for y in reversed(years) if y in ln['sources']),None)
            ws.put(r,1+ny,f"{src.get('document')} · {src.get('location')}" if src else ('Calculated subtotal' if ln['total_of'] else ''),note)
    # schedules + ratios
    for name,tab in (('Schedules','548235'),('Ratios & Calculations','C55A11')):
        ws=Sheet(name,tab); head(ws,name,['Definition / basis']); ws.widths[1+ny]=58; sheets.append(ws)
        for kind,r,p in R['computed_rows'][name]:
            if kind=='section': section_row(ws,r,p,ny+2); continue
            it=ctx.items[p]; ws.put(r,0,it['label'],roles[it['style']])
            for yi in range(ny):
                v,f=ctx.calc(p,yi)
                if v is None: ws.put(r,1+yi,'N/A',na)
                elif f is None: ws.put(r,1+yi,v,numst(it['kind'],'input',it['style']))
                else: ws.put(r,1+yi,v,numst(it['kind'],'formula',it['style']),f)
            ws.put(r,1+ny,it['definition'],note)
    for ws in sheets[1:]: fit_labels(ws)
    # checks
    ck=Sheet('Checks','B42318'); sheets.append(ck)
    ck.put(1,0,'Accounting checks',title); ck.heights[1]=24; ck.put(2,0,meta,subtitle)
    ck.put(3,0,'Status cells are live formulas: edit a statement input and the checks re-evaluate. Tolerance = max(0.02, 0.1% of value), or the source’s rounding allowance for a printed total. REVIEW = explainable difference to confirm.'+src_note,legend)
    heads=['Year','Check','Value','Expected','Difference','Tolerance','Status','Source references']
    for c,h in enumerate(heads): ck.put(HEADER_ROW,c,h,hdr_l if c in (1,7) else hdr)
    for c,w in enumerate([8,52,13,13,13,11,13,70]): ck.widths[c]=w
    ck.freeze=(HEADER_ROW,0); r=HEADER_ROW
    nf=numst('raw'); ni=numst('raw','input')
    for c in res['checks']:
        r+=1; ck.put(r,0,c['year'],text_c); ck.put(r,1,c['check'],text); ck.put(r,7,c['source_refs'],note)
        if c['kind']=='sign':
            sh,row=ctx.line_addr[c['line']]; sign=EXPECTED_SIGN[c['line']]; ck.put(r,2,c['lhs'],nf,ctx.ref(sh,row,years.index(c['year']),'Checks'))
            ck.put(r,3,'Expected '+('positive' if sign>0 else 'negative'),S(align={'h':'right'})); ck.put(r,6,'FAIL',S(font={'b':1},align={'h':'center'}),f'IF(C{r}*({sign})>=0,"PASS","FAIL")'); continue   # live: re-evaluates when the input is corrected
        if c['status']=='not_tested':
            for k in (2,3,5): ck.put(r,k,'N/A',na)
            ck.put(r,4,c['message'],note); ck.put(r,6,'NOT TESTED',S(font={'b':1},align={'h':'center'})); continue
        yi=years.index(c['year'])
        for k,(kind,val),v in ((2,c['lf'],c['lhs']),(3,c['rf'],c['rhs'])):
            if kind=='const': ck.put(r,k,v,ni)
            elif kind=='ref': sh,row=ctx.line_addr[val]; ck.put(r,k,v,nf,ctx.ref(sh,row,yi,'Checks'))
            elif kind=='refs': ck.put(r,k,v,nf,'+'.join(ctx.ref(*ctx.line_addr[x],yi,'Checks') for x in val))
            else: ck.put(r,k,v,nf,val)
        ck.put(r,4,c['lhs']-c['rhs'],S(fmt='#,##0.000_);(#,##0.000);"–"_)'),f'C{r}-D{r}')
        ck.put(r,5,c['tolerance'],S(fmt='#,##0.000'),f'MAX(0.02,ABS(C{r})*0.001'+(f",{c['tolerance']}" if c.get('rounding_tol') else '')+')')
        rule=f'IF(ABS(E{r})<=F{r},"PASS",IF(E{r}<0,"REVIEW","FAIL"))' if c.get('review_rule') else f'IF(ABS(E{r})<=F{r},"PASS","FAIL")'
        ck.put(r,6,c['status'].upper(),S(font={'b':1},align={'h':'center'}),rule)
    ck.cf.append((f'G{HEADER_ROW+1}:G{max(r,HEADER_ROW+1)}',[('PASS',0),('FAIL',1),('NOT TESTED',2),('REVIEW',2)]))
    ck.autofilter=f'A{HEADER_ROW}:H{max(r,HEADER_ROW+1)}'
    # calculation audit
    au=Sheet('Calculation Audit','7F7F7F'); sheets.append(au)
    au.put(1,0,'Calculation audit register',title); au.heights[1]=24; au.put(2,0,meta,subtitle)
    au.put(3,0,'Every schedule and ratio cell, its Excel formula, input values and source references.'+src_note,legend)
    heads=['Year','Sheet','Metric','Definition','Excel formula','Value','Status','Inputs','Source references']
    for c,h in enumerate(heads): au.put(HEADER_ROW,c,h,hdr_l)
    for c,w in enumerate([8,12,32,44,52,14,14,60,70]): au.widths[c]=w
    au.freeze=(HEADER_ROW,0); r=HEADER_ROW
    for a in res['audit']:
        r+=1; it=ctx.items[a['metric']]
        for c,v in enumerate([a['year'],ctx.item_addr[a['metric']][0],a['label'],a['formula'],a['excel_formula'],a['value'],a['status'],a['inputs'],a['source_refs']]):
            st=text_c if c==0 else numst('raw' if it['kind']=='num' else it['kind']) if c==5 and v is not None else note if c in (4,7,8) else text
            au.put(r,c,v if c!=5 or v is not None else 'N/A',na if c==5 and v is None else st)
    au.autofilter=f'A{HEADER_ROW}:I{max(r,HEADER_ROW+1)}'
    # sources
    so=Sheet('Sources','7F7F7F'); sheets.append(so)
    so.put(1,0,'Source data and provenance',title); so.heights[1]=24; so.put(2,0,meta,subtitle)
    so.put(3,0,'One row per statement line and year, as supplied in the normalized input.'+src_note,legend)
    heads=['Statement','Line item','Line id','Year','Value','Type','Document','Location','Original label']
    for c,h in enumerate(heads): so.put(HEADER_ROW,c,h,hdr_l)
    for c,w in enumerate([18,40,26,8,14,20,30,16,40]): so.widths[c]=w
    so.freeze=(HEADER_ROW,0); r=HEADER_ROW
    kinds={'input':'Source input','formula':'Calculated subtotal','reported_total':'Reported total (components incomplete)','reported_rounded':'Reported total (components differ by rounding)',None:'Not available'}
    for st in m['order']:
        for lid in m['order'][st]:
            ln=m['lines'][lid]
            for y in years:
                r+=1; v,k=m['resolved'][(lid,y)]; s=ln['sources'].get(y,{})
                for c,val in enumerate([STATEMENTS[st],ln['label'],lid,y,v,kinds[k],s.get('document',''),s.get('location',''),s.get('label','')]):
                    so.put(r,c,'N/A' if c==4 and val is None else val,na if c==4 and val is None else numst('raw','input' if k=='input' else 'formula') if c==4 else text_c if c==3 else text)
    so.autofilter=f'A{HEADER_ROW}:I{max(r,HEADER_ROW+1)}'
    # summary (written last so it can link to everything above)
    sm=summary; cfail=sum(c['status']=='fail' for c in res['checks']); nt=sum(c['status']=='not_tested' for c in res['checks'])
    sm.put(1,0,m['company'],S(font={'b':1,'sz':18,'color':NAVY})); sm.heights[1]=28
    sm.put(2,0,'Financial statement analysis  ·  '+meta.split('  ·  ',1)[1]+f'  ·  {flow_h[0]} – {flow_h[-1]}',subtitle)
    sm.put(4,0,'Reconciliation status',S(font={'b':1}));
    sm.put(4,1,f'{cfail} check(s) failed' if cfail else 'All testable checks passed',S(font={'b':1,'color':'B42318' if cfail else '0B6E4F'},fill='FDE8E7' if cfail else 'E3F4EC',align={'h':'left','indent':1}),
           'IF(COUNTIF(Checks!G:G,"FAIL")>0,COUNTIF(Checks!G:G,"FAIL")&" check(s) failed","All testable checks passed")')
    sm.merges.append(f'B4:{col(max(ny,3))}4')
    sm.put(5,0,'Checks not testable',S(font={'color':GREY})); sm.put(5,1,nt,S(font={'color':GREY},align={'h':'left','indent':1}),'COUNTIF(Checks!G:G,"NOT TESTED")')
    nr=sum(c['status']=='review' for c in res['checks'])
    sm.put(6,0,'Checks to review (explainable differences)',S(font={'color':GREY})); sm.put(6,1,nr,S(font={'color':GREY},align={'h':'left','indent':1}),'COUNTIF(Checks!G:G,"REVIEW")')
    hr=8; sm.put(hr,0,'Key metrics',hdr_l)
    for yi,h in enumerate(flow_h): sm.put(hr,1+yi,h,hdr)
    sm.widths[0]=40
    for yi in range(ny): sm.widths[1+yi]=max(13,len(flow_h[yi])+3)
    kpis=[('Scale','Revenue','L','revenue','num'),('Scale','EBITDA','X','ebitda','num'),('Scale','Net income','L','net_income','num'),('Scale','Free cash flow','X','free_cash_flow','num'),('Scale','FCF incl. distributions from associates/JVs','X','fcf_incl_distributions','num'),('Scale','FCF excl. financial-services flows','X','fcf_ex_fs','num'),
          ('Scale','Net income before one-off items','X','net_income_ex_one_offs','num'),('Scale','Net debt (negative = net cash)','X','net_debt','num'),('Scale','Net debt incl. debt-like items','X','adj_net_debt','num'),('Scale','Debt excluding perpetual securities','X','debt_ex_perpetual','num'),
          ('Profitability and returns','Gross margin','X','gross_margin','pct'),('Profitability and returns','EBIT margin','X','operating_margin','pct'),('Profitability and returns','Net margin','X','net_margin','pct'),('Profitability and returns','Return on equity','X','roe','pct'),('Profitability and returns','ROE on owners\u2019 equity (company basis)','X','roe_owners','pct'),('Profitability and returns','ROIC','X','roic','pct'),
          ('Liquidity, leverage and cash','Current ratio','X','current_ratio','x'),('Liquidity, leverage and cash','Current ratio excl. client funds','X','current_ratio_ex_client','x'),('Liquidity, leverage and cash','Net debt / EBITDA','X','net_debt_to_ebitda','x'),('Liquidity, leverage and cash','Gross debt / EBITDA','X','debt_to_ebitda','x'),('Liquidity, leverage and cash','Interest coverage','X','interest_coverage','x'),('Liquidity, leverage and cash','Cash conversion (OCF / NI)','X','cash_conversion','x'),('Liquidity, leverage and cash','Cash conversion incl. associates\u2019 distributions','X','cash_conversion_adj','x'),('Liquidity, leverage and cash','Cash conversion cycle (days)','X','ccc','days'),
          ('Growth','Revenue growth','X','revenue_growth','pct'),('Growth','Net income growth','X','net_income_growth','pct'),
          ('Financial institution metrics','Cost-to-income','X','cost_to_income','pct'),('Financial institution metrics','Net interest margin','X','nim','pct'),
          ('Financial institution metrics','Cost of risk','X','cost_of_risk','pct'),('Financial institution metrics','Loan-to-deposit','X','loan_to_deposit','pct'),
          ('Financial institution metrics','Equity / total assets','X','equity_to_assets','pct'),('Financial institution metrics','CET1 ratio (reported)','X','cet1','pct'),
          ('Financial institution metrics','Combined ratio','X','combined_ratio','pct'),('Financial institution metrics','Solvency ratio (reported)','X','solvency','pct')]
    r=hr; group=None
    for g,label,kind,key,fk in kpis:
        if kind=='L' and key not in ctx.line_addr or kind=='X' and key not in ctx.item_addr: continue
        if g!=group: r+=1; section_row(sm,r,g,ny+1); group=g
        r+=1; sm.put(r,0,label,lab)
        for yi,y in enumerate(years):
            v=ctx.line(key,yi) if kind=='L' else ctx.calc(key,yi)[0]
            sh,row=ctx.line_addr[key] if kind=='L' else ctx.item_addr[key]
            if v is None: sm.put(r,1+yi,'N/A',na)
            else: sm.put(r,1+yi,v,numst(fk),ctx.ref(sh,row,yi,'Summary'))
    r+=2; sm.put(r,0,'Key findings',S(font={'b':1,'sz':12,'color':NAVY}))
    wide=col(max(ny,3)+2)
    for fnd in findings(res):
        alert=fnd.startswith('WARNING') or re.match(r'(?:The auditor|No revenue|Source statements are UNAUDITED|Possible one-off|.* include one-off|Net margin of .* exceeds|Equity moved|Total assets moved|Perpetual securities|Operating cash flow includes|EBITDA is derived)',fnd)
        r+=1; sm.put(r,0,'•  '+fnd,S(align={'v':'top','wrap':1},font={'b':1,'color':'B42318'} if alert else None)); sm.merges.append(f'A{r}:{wide}{r}'); sm.heights[r]=15*(1+len(fnd)//110)+3
    if m['key_disclosures']:
        r+=2; sm.put(r,0,'Key disclosures (from the report)',S(font={'b':1,'sz':12,'color':NAVY}))
        for d in m['key_disclosures']:
            t=str(d.get('text',''))+(f"  [{d['source'].get('location','') if isinstance(d.get('source'),dict) else d.get('source')}]" if d.get('source') else '')
            r+=1; sm.put(r,0,'•  '+t,S(align={'v':'top','wrap':1})); sm.merges.append(f'A{r}:{wide}{r}'); sm.heights[r]=15*(1+len(t)//110)+3
    r+=2; sm.put(r,0,'How this workbook fits together',S(font={'b':1,'sz':12,'color':NAVY}))
    for line in ['Income Statement, Balance Sheet and Cash Flow hold the source figures (blue) with subtotals as live SUM formulas (black).',
                 'Schedules derive working capital, net debt, EBITDA / free cash flow, cash, PP&E and equity roll-forwards from the statements.',
                 'Ratios & Calculations computes intermediate values and every ratio as a formula referencing the statements and schedules.',
                 'Checks re-tests the accounting identities live; Calculation Audit and Sources give the full formula and provenance trail.',
                 'Decision support only; not investment advice. Review against the original audited statements before relying on any figure.']:
        r+=1; sm.put(r,0,'•  '+line,S(font={'color':'374151'},align={'v':'top','wrap':1})); sm.merges.append(f'A{r}:{wide}{r}'); sm.heights[r]=15*(1+len(line)//110)+3
    for k in range(ny+1,max(ny,3)+3): sm.widths.setdefault(k,13)
    if res.get('demo'):
        flag=S(font={'b':1,'color':'FFFFFF'},fill='B42318',align={'h':'left','v':'center','indent':1})
        for ws in sheets:
            br=3 if ws is sm else 4
            for c in range(max(ny+2,8)): ws.put(br,c,'DEMO DATA — synthetic figures for testing only. Not an analysis of any real company.' if c==0 else None,flag)
            ws.heights[br]=20
    save_workbook(path,sheets,S)

# ------------------------------------------------------------- extraction
_OPEN_DOCS=[]   # documents opened by open_pdf, kept for the life of the process: their pages only weakly reference them

def open_pdf(input_file):
    """List of (page_no, page). PyMuPDF if installed, else pypdfium2; both are fast and keep word positions."""
    reader=pdf_reader()
    if reader=='pymupdf':
        try: import pymupdf as fitz
        except ImportError: import fitz
        doc=fitz.open(input_file); _OPEN_DOCS.append(doc)   # a page's get_text() fails once its Document is garbage-collected
        return [(i+1,pg) for i,pg in enumerate(doc)]
    if reader=='pypdfium2':
        import pypdfium2 as pdfium
        doc=pdfium.PdfDocument(input_file); _OPEN_DOCS.append(doc); return [(i+1,PdfiumPage(doc[i])) for i in range(len(doc))]
    raise SystemExit('ERROR: no fast PDF reader here (PyMuPDF or pypdfium2). Make a text copy with the platform\'s PDF extraction, one file at a time, and pass the .txt instead.')

PAGE_MARK=re.compile(r'^\s*(?:[-=#*_\[<]+\s*)?(?:page|p\.|第)\s*(\d{1,4})\s*(?:页)?\s*(?:(?:of|/)\s*\d+)?\s*(?:[-=#*_\]>]+)?\s*$',re.I|re.M)

class TextPage:
    """A page of OCR / plain text (e.g. the harness's ocr.txt), so statements can be located without PyMuPDF."""
    def __init__(self,text): self.text=text
    def get_text(self,*a): return self.text

def load_document(input_file):
    """Returns (pages, kind). PDFs need PyMuPDF and a text layer; .txt/.md (OCR output) are split into pages on
    form feeds or 'Page N' marker lines; otherwise the whole text is one page."""
    path=Path(input_file)
    if path.suffix.lower() in ('.txt','.md','.text'):
        text=path.read_text(encoding='utf-8',errors='replace')
        if '\f' in text: parts=text.split('\f'); nums=list(range(1,len(parts)+1))
        else:
            marks=list(PAGE_MARK.finditer(text))
            if marks and (len(marks)>=2 or not text[:marks[0].start()].strip()):   # one marker counts when the text starts with it (ocr-pdf --pages 88)
                parts=[text[mk.end():(marks[i+1].start() if i+1<len(marks) else len(text))] for i,mk in enumerate(marks)]; nums=[int(mk.group(1)) for mk in marks]
            else: parts,nums=[text],[1]
        return [(n,TextPage(t)) for n,t in zip(nums,parts)],'text'
    pages=open_pdf(input_file)
    if sum(len(pg.get_text().strip()) for _,pg in pages[:min(len(pages),20)])<200:
        print('WARNING: this PDF has no text layer (scanned image). Run ocr-pdf on the statement pages (or use the platform OCR text) and pass the .txt instead.')
    return pages,'pdf'

def page_rows(page,kind):
    return pdf_rows(page) if kind=='pdf' else [ln.strip() for ln in page.get_text().splitlines() if ln.strip()]

def parse_pages(spec):
    """'197-201,245' -> {197,...,201,245} (1-based)."""
    pages=set()
    for part in (spec or '').split(','):
        part=part.strip()
        if not part: continue
        lo,_,hi=part.partition('-'); pages.update(range(int(lo),int(hi or lo)+1))
    return pages or None

def pdf_rows(page):
    """Rebuild table rows from word positions so a label and its amounts stay on one line ('Revenue | 3 | 90,964 | 87,169').
    Landscape pages are usually two-page spreads, so each half is read separately."""
    W=page.rect.width; halves=[(0,W)] if W<=page.rect.height*1.2 else [(0,W/2),(W/2,W)]
    words=page.get_text('words'); out=[]
    for lo,hi in halves:
        rows=[]
        for w in sorted((w for w in words if lo<=(w[0]+w[2])/2<hi),key=lambda w:((w[1]+w[3])/2,w[0])):
            yc=(w[1]+w[3])/2
            if rows and abs(rows[-1][0]-yc)<=3: rows[-1][1].append(w)
            else: rows.append([yc,[w]])
        for _,rw in rows:
            rw.sort(key=lambda w:w[0]); txt=rw[0][4]
            for prev,w in zip(rw,rw[1:]): txt+=(' | ' if w[0]-prev[2]>12 else ' ')+w[4]
            out.append(txt)
    return out

STATEMENT_PATTERNS={
    'income_statement':(r'statements? of (?:consolidated )?(?:profit or loss|profit (?:and|&) loss|income|operations|earnings|comprehensive income)|income statements?|profit and loss (?:account|statement)|合并利润表|合并损益表|compte de r[ée]sultat',
                        (r'revenue|turnover|sales|营业收入|营业总收入|chiffre d.affaires|ventes de marchandises|production vendue',r'profit before|income before|before (?:income )?tax|利润总额|r[ée]sultat (?:d.exploitation|courant|net|exceptionnel)')),
    'balance_sheet':(r'statements? of (?:consolidated )?financial position|balance sheets?|合并资产负债表|\bbilan\b',(r'non-?current assets|total assets|资产总计|非流动资产|immobilisations|capitaux propres',r'current liabilities|流动负债|actif circulant|dettes')),
    'cash_flow':(r'statements? of (?:consolidated )?cash flows?|cash flow statements?|合并现金流量表|tableau des flux de tr[ée]sorerie',(r'operating activities|经营活动|activit[ée]s? op[ée]rationnelles?|exploitation',r'investing activities|投资活动|investissement'))}
# Statutory layouts (e.g. French comptes sociaux) often print no statement title on the page: recognise them by their structure.
STATEMENT_SIGNATURES={
    'balance_sheet':(r'montant brut.{0,60}amort',r'capitaux propres.{0,4000}(?:dettes|total g[ée]n[ée]ral)'),
    'income_statement':(r'(?:ventes de marchandises|production vendue|chiffre d.affaires net).{0,4000}(?:r[ée]sultat d.exploitation|charges d.exploitation)',r'produits exceptionnels.{0,4000}(?:r[ée]sultat|b[ée]n[ée]fice ou perte)')}
# What follows a real statement title: its period / unit line ("for the year ended", "as at", "(Millions of Yen)", "2025年9月30日").
TITLE_LINE=r'\s*(?:\(continued\)\s*)?(?:for the (?:year|period|financial year|six|nine|three|half)|as (?:at|of)|\(?(?:in )?(?:millions|thousands|billions)|\((?:hk|us|a|rmb|cny)?\$|(?:19|20)\d{2}\s*年|单位|编制单位|au \d|exercice)'
NOT_PRIMARY=r'deed of cross guarantee|closed group|non-?consolidated|unconsolidated'   # guarantee-group / parent-only statements (anywhere on the page)
NOT_PRIMARY_HEAD=r'parent entity|company only|separate financial statements|母公司'          # only when in the page heading ("members of the parent entity" is normal)
NUM_RE=re.compile(r'\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|\(?\d{3,}(?:\.\d+)?\)?')

def score_pages(doc,kind,pages=None):
    """Candidate pages per statement, best first, duplicate copies removed."""
    byno=dict(doc); found={k:[] for k in STATEMENT_PATTERNS}
    for pno,p in doc:
        if pages and pno not in pages: continue
        text=p.get_text(); main=' '.join(text.split()).lower(); nums=len(NUM_RE.findall(text))
        low=main+' '+re.sub(r'\s+','',main)  # CJK titles are often split by spaces in extracted text
        if nums<15: continue
        matched={}
        for st,(title,anchors) in STATEMENT_PATTERNS.items():
            hits=[m for m in re.finditer(title,low) if not re.search(r"(notes? to (?:the )?|company's |company’s |postes du |relatives au )$",low[max(0,m.start()-30):m.start()])]
            if not hits and st in STATEMENT_SIGNATURES:
                hits=[m for m in (re.search(sig,main) for sig in STATEMENT_SIGNATURES[st]) if m][:1]
            if hits: matched[st]=(hits,anchors)
        for st,(hits,anchors) in matched.items():
            score=nums*(2 if all(re.search(a,low) for a in anchors) else 1)*(1.5 if any('consolidated' in m.group(0) or '合并' in m.group(0) for m in hits) else 1)
            if any(re.match(TITLE_LINE,low[m.end():m.end()+70]) for m in hits): score*=3   # a statement title line, not a mention in a note
            if re.search(NOT_PRIMARY,main) or re.search(NOT_PRIMARY_HEAD,main[:80]): score*=0.2
            if 'integral part' in low or '编制单位' in low: score*=2              # boilerplate printed under primary statements
            if len(matched)>1: score*=0.3                    # reviews/summaries mention several statements on one page
            if re.search(r'(?:five|ten|5|10)[- ]year|financial summary|highlights|last year',low): score*=0.3
            found[st].append({'page':pno,'score':round(score,1),'title':hits[0].group(0)})
    for st,cands in found.items():
        cands.sort(key=lambda c:-c['score']); best=[]; seen=[]
        for c in cands:   # skip duplicate copies of the same statement (some filings print the statements twice)
            sig=frozenset(NUM_RE.findall(byno[c['page']].get_text()))
            if any(len(sig & o)>0.9*max(len(sig),1) for o in seen): continue
            best.append(c); seen.append(sig)
        found[st]=best
    return found

def locate_statements(input_file,out,pages=None,top=2):
    """Find the primary statements in a long annual report and return only those pages, as reconstructed rows."""
    doc,kind=load_document(input_file); byno=dict(doc); found=score_pages(doc,kind,pages)
    result={'source':str(input_file),'input_kind':kind,'page_count':len(doc),'status':'unverified_extraction_do_not_analyze_directly','statements':{}}
    for st,cands in found.items():
        best=cands[:top]; cands=cands[top:]
        for c in best:
            txt=byno[c['page']].get_text()
            c['unit_hints']=sorted(set(m.group(0) for m in re.finditer(r"(?:HK|US|A|S|NZ|C)?\$\s?(?:M|m|mn|million|’000|'000|bn)\b|RMB\s?(?:million|’000)|in (?:millions|thousands|billions)|£\s?m|€\s?m|单位[:：]\s*(?:人民币)?\s*(?:元|千元|万元|百万元|亿元)|en (?:k ?eur|milliers d.euros|euros)|k ?€|币种[:：]\s*\S+|审计类型[:：]\s*\S+",txt)))
            c['year_headers']=sorted(set(re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',txt[:600])))
            c['rows']=page_rows(byno[c['page']],kind)
        result['statements'][st]={'pages':best,'other_candidate_pages':[c['page'] for c in cands[:8]]}
    out=write_text_safe(out,json.dumps(result,indent=2,ensure_ascii=False))
    for st,v in result['statements'].items():
        print(f"{st}: "+(', '.join(f"p.{c['page']} (score {c['score']})" for c in v['pages']) or 'NOT FOUND - ask the user for the page numbers or an XLSX/CSV export'))
    print(f'Report has {len(doc)} pages ({kind}); wrote {Path(out).stat().st_size//1024} KB to {Path(out).resolve()}. Next: draft-map on the same file (it reuses these pages).')

# ------------------------------------------------------------- fast PDF readers (PyMuPDF, else pypdfium2)
class _Rect:
    def __init__(self,w,h): self.width=w; self.height=h

class PdfiumPage:
    """pypdfium2 page exposing the small PyMuPDF surface this script uses: rect, get_text(), get_text('words')."""
    def __init__(self,page):
        self._p=page; w,h=page.get_size(); self.rect=_Rect(float(w),float(h)); self._tp=None; self._t=None; self._w=None
    def _textpage(self):
        if self._tp is None: self._tp=self._p.get_textpage()
        return self._tp
    def get_text(self,mode=None):
        if mode=='words':
            if self._w is None: self._w=self._words()
            return self._w
        if self._t is None: self._t=self._textpage().get_text_range() or ''
        return self._t
    def _words(self):
        """Words from character boxes. Punctuation such as ',' sits below the digit baseline, so lines are compared on
        the word's baseline with tolerances scaled to the tallest glyph, not on each character's own centre."""
        tp=self._textpage(); H=self.rect.height; words=[]; cur=None   # cur = [x0, x1, text, baseline, top]
        for i in range(tp.count_chars()):
            ch=tp.get_text_range(i,1)
            if not ch or ch.isspace():
                if cur: words.append(cur); cur=None
                continue
            l,b,r,t=tp.get_charbox(i)
            if cur:
                ref=max(cur[4]-cur[3],t-b,4.0)
                # digits, thousands separators and decimal points split by a kerning gap ('21 ,450', '1 10') belong to the same number
                num=(ch in ',.' and cur[2][-1:].isdigit()) or (cur[2][-1:] in ',.' and ch.isdigit() and cur[2][-2:-1].isdigit()) or (ch.isdigit() and cur[2][-1:].isdigit())
                if l-cur[1]>(1.0 if num else 0.4)*ref or b>cur[4]+0.2*ref or t<cur[3]-0.6*ref or l<cur[0]-0.5*ref:   # gap, or clearly another line = new word
                    words.append(cur); cur=None
            # baseline = highest glyph bottom (descenders and commas sit lower); top = highest glyph top
            if cur: cur=[cur[0],max(cur[1],r),cur[2]+ch,max(cur[3],b),max(cur[4],t)]
            else: cur=[l,r,ch,b,t]
        if cur: words.append(cur)
        return [(w[0],H-w[4],w[1],H-w[3],w[2]) for w in words]
    def render(self,dpi):
        return self._p.render(scale=dpi/72).to_pil()

def pdf_reader():
    for mod,name in (('pymupdf','pymupdf'),('fitz','pymupdf'),('pypdfium2','pypdfium2')):
        try: __import__(mod); return name
        except ImportError: continue
    return None

# ------------------------------------------------------------- OCR (scanned statements)
def ocr_engine_available():
    import importlib.util
    return any(importlib.util.find_spec(m) for m in ('rapidocr_onnxruntime','rapidocr'))

def ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR; return RapidOCR()
    except ImportError: pass
    try:
        from rapidocr import RapidOCR; return RapidOCR()
    except ImportError: return None

def ocr_items(result):
    """Normalise rapidocr output (old tuple API or new object API) to [(box, text)]."""
    if isinstance(result,tuple): result=result[0]
    if result is None: return []
    if hasattr(result,'txts'):
        return list(zip(getattr(result,'boxes',None) if getattr(result,'boxes',None) is not None else [],result.txts or []))
    return [(r[0],r[1]) for r in result]

def ocr_rows(items):
    """Group OCR boxes into table rows; cells separated by ' | ' when the horizontal gap is wide."""
    boxes=[]
    for box,text in items:
        xs=[p[0] for p in box]; ys=[p[1] for p in box]
        boxes.append((min(xs),min(ys),max(xs),max(ys),str(text).strip()))
    if not boxes: return []
    hs=sorted(b[3]-b[1] for b in boxes); hmed=hs[len(hs)//2] or 10
    rows=[]
    for b in sorted(boxes,key=lambda b:((b[1]+b[3])/2,b[0])):
        yc=(b[1]+b[3])/2
        if rows and abs(rows[-1][0]-yc)<=0.5*hmed: rows[-1][1].append(b)
        else: rows.append([yc,[b]])
    out=[]
    for _,rw in rows:
        rw.sort(key=lambda b:b[0]); txt=rw[0][4]
        for prev,b in zip(rw,rw[1:]): txt+=(' | ' if b[0]-prev[2]>1.0*hmed else ' ')+b[4]
        out.append(txt)
    return out

def ocr_pdf(input_file,out,pages=None,dpi=200):
    """OCR scanned pages to text with 'Page N' markers, so locate-statements and draft-map can read them."""
    import time
    eng=ocr_engine()
    if eng is None: raise SystemExit('ERROR: no OCR engine is installed (rapidocr). Use the OCR text the platform produced for this scanned PDF, or ask the user for the statement pages as text or XLSX.')
    try: import numpy as np
    except ImportError: raise SystemExit('ERROR: OCR needs numpy, which is not installed. Use the platform OCR text instead.')
    reader=pdf_reader(); parts=[]; t0=time.time()
    if reader=='pymupdf':
        try: import pymupdf as fitz
        except ImportError: import fitz
        doc=fitz.open(input_file); n=doc.page_count
        def render(i):
            from PIL import Image
            pm=doc[i].get_pixmap(dpi=dpi); return Image.frombytes('RGB',(pm.width,pm.height),pm.samples)
    elif reader=='pypdfium2':
        import pypdfium2 as pdfium
        doc=pdfium.PdfDocument(input_file); n=len(doc)
        def render(i): return doc[i].render(scale=dpi/72).to_pil()
    else: raise SystemExit('ERROR: no PDF reader (PyMuPDF or pypdfium2) to render pages for OCR. Use the platform OCR text instead.')
    todo=sorted(pages) if pages else list(range(1,n+1))
    if not pages and n>60: raise SystemExit(f'ERROR: {n} pages; OCR only the statement pages, e.g. --pages 10-14 (find them in the contents page).')
    for pno in todo:
        if not 1<=pno<=n: continue
        img=render(pno-1).convert('RGB'); rows=ocr_rows(ocr_items(eng(np.array(img))))
        parts.append(f'--- Page {pno} ---\n'+'\n'.join(rows)); print(f'  OCR page {pno}: {len(rows)} rows ({time.time()-t0:.0f}s)')
    out=write_text_safe(out,'\n'.join(parts)+'\n'); print('Wrote OCR text:',Path(out).resolve())

# ------------------------------------------------------------- draft mapping
AMT_CELL=re.compile(r'^\(?\s*[-–−]?\s*(?:\d{1,3}(?:[,\s  ]\d{3})+|\d+)(?:\.\d+)?\s*\)?$')
DASH_CELL=re.compile(r'^[-–—−－―‐]+$')
NOTE_CELL=re.compile(r'^(?:[A-Z]{1,2}\.\d+(?:\.\d+)?|\d{1,2}\([a-z]\)|\d{1,2}(?:\s*,\s*\d{1,2})+|[IVX]{1,4}|note \d+)$',re.I)
YEAR_RE=re.compile(r'(?<!\d)((?:19|20)\d{2})(?!\d)')
SKIP_ROW=re.compile(r'integral part|approved|signed on behalf|^director|annual report|季度报告|编制单位|单位[:：]|币种|审计类型|^rubriques|^note$|^项目$|^notes?\s*\$|^\(?(?:in )?(?:millions|thousands|billions) of|^\$m|^hk\$m|^£000|^€|^page \d+|^\d+$|^total des (?:produits|charges)\s*\(|^\d+\s*/\s*\d+$',re.I)
TITLE_ANY=re.compile('|'.join(f'(?:{t})' for t,_ in STATEMENT_PATTERNS.values())+r'|changes in (?:shareholders.? |owners.? )?equity|所有者权益变动表|股东权益变动表|notes to the|母公司|comprehensive income|综合收益表',re.I)
TERMINAL={'income_statement':r'per share|每股收益|r[ée]sultat de l.exercice|b[ée]n[ée]fice ou perte',
          'balance_sheet':r'total liabilities and (?:shareholders.? |owners.? )?equity|total equity and liabilities|equity and non-current liabilities|负债和所有者权益|负债和股东权益|total g[ée]n[ée]ral',
          'cash_flow':r'(?:cash|equivalents)\b.{0,40}\bat (?:the )?end|期末现金|end of (?:the )?(?:financial )?(?:year|period)'}
EXPENSE_WORDS=r'cost|expense|charge|loss|depreciation|amorti|impairment|\btax\b|taxation|purchases|staff|employee|finance costs|成本|费用|税金|损失|支出|减：|achats|charges|imp[ôo]ts|dotations|salaires|variation de stock|participation des salari'
OUTFLOW_WORDS=r'paid|payment|purchase|acquisition of|acquisitions|repayment|redemption|outflow|spent|支付|偿还|购建|投资支付|流出|décaissement'

def parse_amount(t):
    t=t.strip().replace('−','-')
    if DASH_CELL.match(t): return 0.0
    if not AMT_CELL.match(t): return None
    neg=t.startswith('(') or t.lstrip('( ').startswith(('-','–'))
    try: v=float(re.sub(r'[^\d.]','',t))
    except ValueError: return None
    return -v if neg else v

def pdf_cells(page):
    """Rows of (text, x0, x1) cells from word positions; spreads are read half by half."""
    W=page.rect.width; halves=[(0,W)] if W<=page.rect.height*1.2 else [(0,W/2),(W/2,W)]
    words=page.get_text('words'); out=[]
    for h,(lo,hi) in enumerate(halves):
        rows=[]
        for w in sorted((w for w in words if lo<=(w[0]+w[2])/2<hi),key=lambda w:((w[1]+w[3])/2,w[0])):
            yc=(w[1]+w[3])/2
            if rows and abs(rows[-1][0]-yc)<=3: rows[-1][1].append(w)
            else: rows.append([yc,[w]])
        for _,rw in rows:
            rw.sort(key=lambda w:w[0]); cells=[[rw[0][4],rw[0][0],rw[0][2]]]
            for prev,w in zip(rw,rw[1:]):
                if w[0]-prev[2]>12: cells.append([w[4],w[0],w[2]])
                else: cells[-1][0]+=' '+w[4]; cells[-1][2]=w[2]
            out.append({'half':h,'cells':[tuple(c) for c in cells]})
    return out

def text_cells(line):
    """Cells of one text line: ' | ' separated (our OCR / extract output), tab or 2+ spaces, else trailing amount tokens."""
    if ' | ' in line:
        parts=[x.strip() for x in line.split('|')]
        while parts and not parts[0]: parts.pop(0)
        while parts and not parts[-1]: parts.pop()
        if len(parts)>1 and any(parse_amount(x) is not None for x in parts):
            return [(x if x else '\u2400',None,None) for x in parts]   # U+2400 marks an empty value slot
    elif re.search(r'\t|\s{2,}',line.strip()): parts=re.split(r'\t+|\s{2,}',line.strip())
    else:
        toks=re.findall(r'\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?|\(?-?\d+(?:\.\d+)?\)?|(?<!\w)[-–—](?!\w)|\S+',line.strip()); k=len(toks)
        while k>0 and parse_amount(toks[k-1]) is not None: k-=1
        parts=([' '.join(toks[:k])] if k else [])+toks[k:]
    return [(p.strip(),None,None) for p in parts if p.strip()]

def page_cells(page,kind):
    if kind=='pdf': return pdf_cells(page)
    rows=[text_cells(l) for l in page.get_text().splitlines() if l.strip()]
    def amounts_only(c): return bool(c) and all(parse_amount(x[0]) is not None for x in c)
    # stacked text (some extractors put every cell on its own line): join each label with the amount lines below it
    if rows and sum(1 for c in rows if amounts_only(c) and len(c)==1)>=0.3*len(rows):
        out=[]
        for c in rows:
            prev=out[-1] if out else None
            if prev and amounts_only(c) and parse_amount(prev[0][0]) is None: prev.extend(c)
            elif prev and not any(parse_amount(x[0]) is not None for x in prev+c) and YEAR_RE.search(c[0][0]) and YEAR_RE.search(' '.join(x[0] for x in prev)): prev.extend(c)
            else: out.append(list(c))
        rows=out
    return [{'half':0,'cells':c} for c in rows]

def tidy_label(t):
    """Remove spaces some PDF readers put around punctuation: "D ' AFFAIRES" -> "D'AFFAIRES", "其中： 营业收入" -> "其中：营业收入"."""
    t=re.sub(r"\s+(['’])\s*(?=\w)",lambda mt:mt.group(1),t)      # "D ' AFFAIRES" -> "D'AFFAIRES" (keeps "Shareholders’ funds")
    t=re.sub(r"\s*([\-/])\s*(?=\w)",lambda mt:mt.group(1),t)
    t=re.sub(r'\s*([、：，（）《》“”])\s*',lambda mt:mt.group(1),t)
    t=re.sub(r'(?<=[一-鿿])\s+(?=[一-鿿])','',t)
    return re.sub(r'\s{2,}',' ',t).strip()

SIGN_NOTE=re.compile(r'[（(][^（）()]{0,12}以\s*[“"‘]?\s*[-－—]?\s*[”"’]?\s*号填列[）)]?|[（(][^（）()]{0,12}以\s*[“"‘]?\s*[-－—]?\s*[”"’]?\s*号?填?$')

def clean_label(t):
    """Drop the CAS sign instruction, e.g. '投资收益（损失以“-”号填列）' -> '投资收益'."""
    return SIGN_NOTE.sub('',str(t)).strip() or str(t)

def split_row(cells,N,anchors):
    k=len(cells)
    while k>0 and (parse_amount(cells[k-1][0]) is not None or cells[k-1][0]=='\u2400'): k-=1
    trail=cells[k:]; label=tidy_label(' '.join(c[0] for c in cells[:k] if not NOTE_CELL.match(c[0].strip()))).strip(' :：')
    vals=[None]*N; amb=False
    if not trail: return label,vals,False,False
    if anchors and trail[0][2] is not None:
        for c in trail:   # each amount goes to the year of the nearest column (note and breakdown columns map to None)
            x,yi=min(anchors,key=lambda a:abs(c[2]-a[0]))
            if abs(c[2]-x)<=30 and yi is not None and vals[yi] is None: vals[yi]=parse_amount(c[0])
    else:
        tv=[None if c[0]=='\u2400' else parse_amount(c[0]) for c in trail][-N:]
        if len(tv)<N: amb=True; vals[N-len(tv):]=tv
        else: vals=tv
    label=label.replace('\u2400','').strip()
    return label,vals,any(v is not None for v in vals),amb

def years_in(cells):
    return [int(y) for c in cells for y in YEAR_RE.findall(c[0])]

def gather_rows(st,start,byno,kind,max_extra=3):
    """Rows of one statement: from its title row on the start page, across continuation pages, until another statement's title or this statement's closing line."""
    got=[]; started=False; terminal=False
    for step in range(1+max_extra):
        pno=start+step; page=byno.get(pno)
        if page is None: break
        rows=page_cells(page,kind); has_own=any(re.search(STATEMENT_PATTERNS[st][0],' '.join(c[0] for c in r['cells']).lower()) for r in rows)
        stop=False
        for r in rows:
            txt=' '.join(c[0] for c in r['cells']); low=txt.lower(); lowc=re.sub(r'\s+','',low)
            own=re.search(STATEMENT_PATTERNS[st][0],low) or re.search(STATEMENT_PATTERNS[st][0],lowc)
            other=(TITLE_ANY.search(low) or TITLE_ANY.search(lowc)) and not own and len(txt)<90
            if not started:
                if own or step>0 or not has_own: started=True
                else: continue
            elif other and not any(parse_amount(c[0]) is not None for c in r['cells']): stop=True; break
            got.append((pno,r))
            if re.search(TERMINAL[st],low) or re.search(TERMINAL[st],lowc): terminal=True
        if stop or terminal: break
        if step==0 and not has_own and kind=='pdf': break   # untitled statutory pages: only extend through explicit extra pages
    return got

def col_anchors(rows,N):
    """Per page half: amount columns as (x, year index). Clusters right edges of amount cells; note columns (small
    integers) map to None; 2N columns with at most N amounts per row are detail/total pairs per year (e.g. CLP cash flow);
    otherwise the rightmost N columns are the years (French 'France | Exportation | 2023 | 2022')."""
    by={}
    for pno,r in rows:
        cells=r['cells']; k=len(cells)
        while k>0 and parse_amount(cells[k-1][0]) is not None: k-=1
        tr=cells[k:]
        if tr and tr[-1][2] is not None: by.setdefault((pno,r['half']),[]).append([(c[2],parse_amount(c[0]),c[0]) for c in tr])
    out={}
    for key,lst in by.items():
        pts=sorted(p for row in lst for p in row); clusters=[]
        for p in pts:
            if clusters and p[0]-clusters[-1][-1][0]<=20: clusters[-1].append(p)
            else: clusters.append([p])
        cols=[]
        for c in clusters:
            note=all(abs(v)<100 and float(v).is_integer() and ',' not in t and ' ' not in t for _,v,t in c)
            if len(c)>=2 and not note: cols.append(sorted(x for x,_,_ in c)[len(c)//2])
        maxper=max(sum(1 for x,v,t in row if not (abs(v)<100 and float(v).is_integer() and ',' not in t)) for row in lst)
        if len(cols)==2*N and maxper<=N: yi=[j//2 for j in range(2*N)]
        elif len(cols)>=N: yi=[None]*(len(cols)-N)+list(range(N))
        else: yi=list(range(N-len(cols),N))
        out[key]=list(zip(cols,yi))
    return out

def build_items(rows,N):
    anchors=col_anchors(rows,N); items=[]; section=None; prev_section=None; pending=None; last_was_amt=False; header_years=[]; memo_run=0
    def is_upper(t): return len(re.sub(r'[^A-Za-zÀ-ÿ]','',t))>4 and t.upper()==t
    # statutory layouts (e.g. French) put headings in capitals; there, mixed-case lines without amounts are blank items
    upper_mode=sum(1 for _,r in rows if is_upper(' '.join(c[0] for c in r['cells'])) and all(parse_amount(c[0]) is None for c in r['cells']))>=3
    medx={}   # usual left edge of labels on rows with amounts, per page half
    for pno,r in rows:
        c=r['cells']
        if c and c[0][1] is not None and parse_amount(c[0][0]) is None and any(parse_amount(x[0]) is not None for x in c[1:]): medx.setdefault((pno,r['half']),[]).append(c[0][1])
    medx={k:sorted(v)[len(v)//2] for k,v in medx.items()}
    stub=None; stub_first=None; stub_heading=False   # last label line without amounts (first half of a wrapped label)
    group=None   # lead-in such as 'Dividends received from' that heads the short lines below it
    for pno,r in rows:
        cells=r['cells']; txt=' '.join(c[0] for c in cells).strip()
        if not txt or SKIP_ROW.search(txt): continue
        label,vals,has,amb=split_row(cells,N,anchors.get((pno,r['half'])))
        if has and label and label[:1].islower() and stub and not last_was_amt:
            # "Increase in investments in and loans to joint" / "ventures (40) (277)": one wrapped label
            label=tidy_label((stub_first or stub)+' '+label)
            if stub_heading: section=prev_section; pending=None
        if has and label and group and label[:1].isupper() and len(label.split())<=4 and not re.search(TOTAL_HINT,norm_label(label),re.I):
            label=group+' '+label[:1].lower()+label[1:]          # 'Dividends received from' + 'Joint ventures'
        elif has and label and group and re.search(TOTAL_HINT,norm_label(label),re.I): group=None
        if has: stub=None
        yrs=years_in(cells)
        if not items and (len(set(yrs))>=2 or (not has and yrs) or (has and yrs and (TITLE_ANY.search(txt.lower()) or re.search(r'\b(?:year|period|months?) ended\b',txt,re.I)))):
            header_years.append(yrs); continue
        if has and not label and all(v is not None and 1990<=abs(v)<=2100 and float(v).is_integer() for v in vals if v is not None):
            header_years.append([int(abs(v)) for v in vals if v is not None]); continue
        if not has:
            if len(txt)>90 or re.search(r'\d+\.\d{2}\b|per share|hk\$|us\$',txt.lower()) and not re.search('[一-鿿]',txt): continue
            cjk=re.search('[一-鿿]',label) is not None
            # a wrapped CJK label continues to the left of where the label above started ("以摊余成本计量的金融资产终" / "止确认收益");
            # headings (colon, 一、, 1.), 加/减/其中 lines and lines after a total are new lines, not continuations
            x0=cells[0][1] if cells and cells[0][1] is not None else None; px=items[-1].get('x0') if items else None
            if cjk and items and last_was_amt and items[-1]['page']==pno and x0 is not None and px is not None and x0<px-4 and x0<medx.get((pno,r['half']),0)-4 and len(label)<=14 \
               and not re.search(r'[：:]\s*$',txt) and not HEADING_RE.match(label) and not re.match(r'^(?:[（(]?[一二三四五六七八九十\d]+[）)、.]|加|减|其中)',label) \
               and not re.search(TOTAL_HINT,norm_label(items[-1]['label']),re.I):
                items[-1]['label']+=label; continue
            nonamt=[c for c in cells if parse_amount(c[0]) is None]
            group=label.rstrip(' :') if (not cjk and re.search(r'\b(?:received from|paid to)\s*:?$',label,re.I)) else None
            stub=label; stub_first=tidy_label(nonamt[0][0]) if len(nonamt)>=2 else None; stub_heading=False
            open_br=items and items[-1]['label'].count('（')+items[-1]['label'].count('(')>items[-1]['label'].count('）')+items[-1]['label'].count(')')
            if items and last_was_amt and len(label)<=45 and (label[:1].islower() or (cjk and (re.match(r'^[的后之及和等中]',label) or len(label)<=3 or open_br))):
                items[-1]['label']+=(' ' if label[:1].isascii() else '')+label; continue
            if upper_mode and not cjk and not is_upper(label): last_was_amt=False; continue
            if cjk and not label.endswith(('：',':')):   # a blank (nil) line item, not a heading
                if label.startswith('其中'): memo_run=3
                last_was_amt=False; continue
            prev_section,section,pending=section,label,label; last_was_amt=False; memo_run=0; stub_heading=True; continue
        if not label:
            if pending: label=pending; section=prev_section
            else: label='Subtotal'
        memo=bool(re.match(r'^(?:其中|of which|including|incl\.|dont)\b',label,re.I)) and not (items and HEADING_RE.match(items[-1]['label']))
        maybe=(not memo) and memo_run>0 and not re.search(TOTAL_HINT,norm_label(label),re.I) and not re.match(r'^(?:加|减)[:：]',label)
        items.append({'label':label,'vals':vals,'page':pno,'section':section,'memo':memo,'maybe_memo':maybe,'amb':amb,'printed':list(vals),
                      'x0':cells[0][1] if cells and cells[0][1] is not None and parse_amount(cells[0][0]) is None else None})
        memo_run=3 if memo else max(0,memo_run-1) if maybe else 0
        pending=None; last_was_amt=True
    return items,header_years

# Labels that can be a subtotal; labelled detail lines are never fitted as totals (stops coincidental sign-flip matches).
TOTAL_HINT=(r'total|subtotal|合计|总计|小计|净额|净利润|利润总额|营业利润|毛利|总收入|总成本|净增加额|期末现金|综合收益总额|^net |^gross|^profit|^loss|'
            r'operating (?:profit|income)|before (?:income )?tax|for the (?:year|period)|at (?:the )?end|at 31|r[ée]sultat|b[ée]n[ée]fice|equity and|net assets|'
            r'net current|less current|shareholders.? funds|equity attributable|attributable to (?:owners|shareholders)|^capital and reserves|cash from operations|^funds from|^subtotal$')

HEADING_RE=re.compile(r'^[一二三四五六七八九十]+(?:、|\s)')

def norm_label(t):
    return re.sub(r'^\s*(?:\d{1,2}[.)]|\(\d{1,2}\)|[ivx]{1,4}[.)]|[a-h][.)])\s+','',str(t),flags=re.I)

def solve_signs(items,comp,T,flippable,q):
    """Smallest set of sign flips among `flippable` comps that makes the comps add up to T in every year with data."""
    from itertools import combinations
    N=len(T); yrs=[j for j in range(N) if T[j] is not None and all(items[c]['vals'][j] is not None for c in comp)]
    if not yrs: return None
    tol=[max(0.51*len(comp)*q,abs(T[j])*1e-6) for j in yrs]
    base=[sum(items[c]['vals'][j] for c in comp) for j in yrs]
    fl=[c for c in comp if c in flippable]
    for r in range(len(fl)+1):
        if r>4 and len(fl)>12 or r>1 and len(fl)>15: break   # long cash flow sections: at most one sign flip
        for sub in combinations(fl,r):
            if all(abs(base[i]-2*sum(items[c]['vals'][j] for c in sub)-T[j])<=tol[i] for i,j in enumerate(yrs)): return set(sub)
    return None

def nil_fill(items,children):
    """A component left blank in a year whose printed total ties without it is nil: enter 0. Returns the filled labels."""
    q=0.01 if any(v is not None and not float(v).is_integer() for it in items for v in it['vals']) else 1; filled=[]
    for i,comp in children.items():
        T=items[i]['vals']
        for j,t in enumerate(T):
            if t is None: continue
            miss=[c for c in comp if items[c]['vals'][j] is None]
            if not miss or len(miss)==len(comp): continue
            tot=sum(items[c]['vals'][j] for c in comp if c not in miss)
            if abs(tot-t)<=max(0.51*len(comp)*q,abs(t)*1e-6):
                for c in miss: items[c]['vals'][j]=0.0; filled.append(items[c]['label'])
    return filled

def flip(items,i,children):
    items[i]['vals']=[-v if v is not None else None for v in items[i]['vals']]
    for c in children.get(i,[]): flip(items,c,children)

KEEP_SIGN=re.compile(r'accumulated|retained|deficit|reserve|other comprehensive|translation|revaluation|hedg|fair value|non-?controlling|minority|'
                     r'total equity|equity attributable|shareholders.? (?:equity|funds)|net assets|capital and reserves|owners.? equity|'
                     r'未分配利润|盈余公积|其他综合收益|储备|股东权益|所有者权益|净资产|少数股东|report à nouveau|réserves|capitaux propres',re.I)

def fit_totals(items,st):
    q=0.01 if any(v is not None and not float(v).is_integer() for it in items for v in it['vals']) else 1
    if st=='balance_sheet':
        # Liabilities printed in brackets (net-current-liabilities layouts) become positive. Genuine deficits are kept:
        # accumulated losses, negative reserves, negative equity and other contra balances stay negative.
        for it in items:
            ded=re.match(r'^(?:减[:：]|less[:：]?\s)',it['label'],re.I) or re.search(r'treasury (?:shares|stock)|own shares held|库存股',it['label'],re.I)
            if ded: it['vals']=[-abs(v) if v is not None else None for v in it['vals']]
            elif not KEEP_SIGN.search(it['label']): it['vals']=[abs(v) if v is not None else None for v in it['vals']]
    nodes=[]; children={}; consumed=set(); forward=set()
    for i,it in enumerate(items):          # totals printed ABOVE their lines, e.g. 二、营业总成本 followed by its costs
        if it['memo'] or not HEADING_RE.match(it['label']): continue
        win=[]
        for j in range(i+1,len(items)):
            if items[j]['memo']: continue
            if HEADING_RE.match(items[j]['label']): break
            win.append(j)
        for k in range(2,min(15,len(win))+1):
            comp=win[:k]; fl=set(c for c in comp if st!='income_statement' or all((v or 0)>=0 for v in items[c]['printed']))
            sol=solve_signs(items,comp,it['vals'],fl,q)
            if sol is not None:
                for c in sol: flip(items,c,children)
                children[i]=comp; it['total_of']=comp; consumed.update(comp); forward.add(i); break
        if i not in forward and i+1<len(items) and re.match(r'^(?:其中|of which)',items[i+1]['label'],re.I) and not items[i+1]['memo']:
            items[i+1]['memo']=True
    for i,it in enumerate(items):
        if it['memo'] or i in consumed: continue
        if i in forward: nodes.append(i); continue
        found=None
        if len(nodes)>=2 and any(v is not None for v in it['vals']) and re.search(TOTAL_HINT,norm_label(it['label']),re.I):
            variants=[it['vals']]
            if st=='balance_sheet' and any(v not in (None,0) for v in it['printed']): variants.append(list(it['printed']))
            def try_fit(pool):
                for k in range(2,min(30 if st=='cash_flow' else 15,len(pool))+1):
                    comp=pool[-k:]
                    # balance sheet: only individual lines may change sign (a negative reserve, treasury shares); a subtotal
                    # never flips, so 'net current liabilities = CA - CL' stays a reported line instead of negating liabilities
                    flippable=set(c for c in comp if (c not in children if st=='balance_sheet' else (st!='income_statement' or all((v or 0)>=0 for v in items[c]['printed']))))
                    for T in variants:
                        sol=solve_signs(items,comp,T,flippable,q)
                        if sol is not None: return (comp,sol,T)
                return None
            found=try_fit(nodes)
            if not found:   # a 其中 breakdown can run over several lines: retry without leading breakdown candidates
                runs=[]; cur=[]
                for n in nodes:
                    if items[n].get('maybe_memo'): cur.append(n)
                    elif cur: runs.append(cur); cur=[]
                if cur: runs.append(cur)
                from itertools import product
                runs=runs[-4:]
                combos=sorted((m for m in product(*[range(len(r)+1) for r in runs]) if any(m)),key=lambda m:(sum(m),m))[:300]
                for m in combos:
                    excl=set(n for r,k in zip(runs,m) for n in r[:k]); found=try_fit([n for n in nodes if n not in excl])
                    if found:
                        for n in excl: items[n]['memo']=True
                        nodes=[n for n in nodes if n not in excl]; break
        if found:
            comp,sol,T=found; it['vals']=list(T)
            for c in sol: flip(items,c,children)
            children[i]=list(comp); it['total_of']=comp; nodes=[n for n in nodes if n not in comp]
        nodes.append(i)
    # lines outside any fitted total: sign by wording (expenses / outflows negative)
    inside=set(c for v in children.values() for c in v)|set(children)
    for i,it in enumerate(items):
        if i in inside or st=='balance_sheet' or it['memo']: continue
        words=EXPENSE_WORDS if st=='income_statement' else OUTFLOW_WORDS
        taxline=re.match(r'imp[ôo]ts? sur les|participation des salari',norm_label(it['label']),re.I)
        if re.search(words,it['label'],re.I) and all((v or 0)>=0 for v in it['vals']) and (taxline or not re.search(r'before|for the (?:year|period)|attributable|profit|income tax credit|r[ée]sultat|b[ée]n[ée]fice|perte|利润|收益|^total',norm_label(it['label']),re.I)):
            flip(items,i,{}); it['sign_guess']=True
    # memo lines (其中 / of which) follow the sign of the line they break down
    for i,it in enumerate(items):
        if not it['memo']: continue
        par=next((j for j in range(i-1,-1,-1) if not items[j]['memo']),None)
        if par is None: continue
        pv=[(a,b) for a,b in zip(items[par]['vals'],items[par]['printed']) if a not in (None,0) and b not in (None,0)]
        if re.search(r'利息收入|interest income',it['label'],re.I) and all((v or 0)>=0 for v in it['printed']): continue
        if pv and (pv[0][0]<0)!=(pv[0][1]<0):
            it['vals']=[-v if v is not None else None for v in it['vals']]
        elif not pv and st=='income_statement' and re.search(EXPENSE_WORDS,it['label'],re.I) and all((v or 0)>=0 for v in it['vals']) and re.search(EXPENSE_WORDS,items[par]['label'],re.I):
            it['vals']=[-v if v is not None else None for v in it['vals']]; it['sign_guess']=True
    return children

ID_RULES={
 'income_statement':[
  (r'^(?:total )?(?:operating )?revenue|^turnover|^net sales|^sales$|营业收入|营业总收入|chiffre d.affaires net','revenue'),
  (r'cost of (?:sales|goods sold|revenue)|^(?:其中[:：]|减[:：])?营业成本$','cogs'),
  (r'^gross profit|毛利|marge brute','gross_profit'),
  (r'^operating (?:profit|income)|profit from operations|营业利润|r[ée]sultat d.exploitation','operating_income'),
  (r'^interest expense|^finance costs?$|interest payable|利息费用|int[ée]r[êe]ts et charges assimil','interest_expense'),
  (r'^interest income|^finance income|interest receivable|利息收入','interest_income'),
  (r'(?:profit|income|loss)[^|]{0,12}before (?:income )?tax|利润总额|r[ée]sultat avant imp','pretax_income'),
  (r'^income tax(?:es)?(?: expense)?$|^tax on profit|^taxation$|所得税费用|imp[ôo]ts? sur les b[ée]n[ée]fices|^income tax expense','tax_expense'),
  (r'^(?:net )?profit (?:\(loss\) )?for the (?:financial )?(?:year|period)|^net (?:profit|income|loss)(?: \(loss\))?$|^profit \(loss\)$|^profit after tax|净利润|r[ée]sultat de l.exercice|b[ée]n[ée]fice ou perte','net_income'),
  (r'(?:owners|shareholders|members|equity holders) of the (?:parent|company)|^shareholders$|归属于母公司(?:股东|所有者)的净利润','net_income_attributable'),
  (r'depreciation and amorti|dotations aux amortissements|^sur immobilisations','depreciation_expense'),
  (r'share of (?:results|profits?|losses)[^|]{0,40}(?:joint ventures|associates)|results of equity accounted|对联营企业和合营企业的投资收益','share_of_associates')],
 'balance_sheet':[
  (r'^cash and (?:cash )?equivalents|^cash and bank|货币资金|disponibilit[ée]s|^cash at bank','cash'),
  (r'restricted cash|restricted deposits|pledged deposits','restricted_cash'),
  (r'^trade (?:and other )?receivables|^accounts receivable|^应收账款$|clients et comptes rattach|^trade debtors','receivables'),
  (r'^inventor(?:y|ies)|^存货|^stocks?\b|marchandises$','inventory'),
  (r'^total current assets|^流动资产合计|total actif circulant','current_assets'),
  (r'^total non-current assets|^非流动资产合计','non_current_assets'),
  (r'^total assets$|^total assets\b(?! less)|^资产总计|^total g[ée]n[ée]ral','total_assets'),
  (r'^trade (?:and other )?payables|^accounts payable|^应付账款|fournisseurs et comptes rattach|^trade creditors','payables'),
  (r'^total current liabilities|^流动负债合计','current_liabilities'),
  (r'^total non-current liabilities|^非流动负债合计','non_current_liabilities'),
  (r'^total liabilities$|^负债合计','total_liabilities'),
  (r'equity attributable to (?:owners|shareholders|equity holders)|归属于母公司(?:所有者|股东)权益|shareholders.? funds','shareholders_equity'),
  (r'^total equity$|^所有者权益(?:（或股东权益）)?合计|^股东权益合计|^net assets$|^total shareholders.? equity','equity'),
  (r'total liabilities and (?:shareholders.? |owners.? )?equity|total equity and liabilities|负债和所有者权益|负债和股东权益|^total g[ée]n[ée]ral','total_liabilities_and_equity'),
  (r'永续债|^other equity instruments','perpetual_bonds')],
 'cash_flow':[
  (r'net cash (?:flows? )?(?:generated |inflow |outflow |provided )?(?:from|by|used in|\(used in\))[ a-z()]{0,14}operating|^cash flows? from operating activities$|经营活动产生的现金流量净额','ocf'),
  (r'net cash (?:flows? )?(?:generated |inflow |outflow |provided )?(?:from|by|used in|\(used in\))[ a-z()]{0,14}investing|投资活动产生的现金流量净额','icf'),
  (r'net cash (?:flows? )?(?:generated |inflow |outflow |provided )?(?:from|by|used in|\(used in\))[ a-z()]{0,14}financing|筹资活动产生的现金流量净额','financing_cf'),
  (r'^(?:purchases? of|acquisition of|payments? for) (?:property|pp&e)|^capital expenditure|购建固定资产','capex'),
  (r'^(?:cash )?dividends paid(?: to (?:shareholders|owners))?$|^dividends paid to (?:shareholders|owners|members)','dividends_paid'),
  (r'depreciation and amorti','d_and_a'),
  (r'^(?:profit|income|loss)[^|]{0,12}before (?:income )?tax','cf_pretax_income'),
  (r'(?:cash|equivalents)\b.{0,40}\bat (?:the )?beginning|期初现金及现金等价物余额|at 1 january|at beginning of','cash_begin'),
  (r'(?:cash|equivalents)\b.{0,40}\bat (?:the )?end|期末现金及现金等价物余额|at end of','cash_end'),
  (r'effect of (?:changes? in )?(?:foreign )?exchange|exchange rate changes|汇率变动','fx_cash'),
  (r'(?:dividends?|distributions?) (?:received )?from (?:joint ventures|associates|equity.accounted)','distributions_from_associates')]}
DEBT_RE=r'borrowings|bank loans|loans and borrowings|interest-bearing|bonds payable|^bonds\b|短期借款|长期借款|应付债券|一年内到期的非流动负债|emprunts|lease liabilit|租赁负债|notes? payable(?! .*bank acceptance)'
SECTION_IDS=[(r'non-?current assets|非流动资产|actif immobilis|immobilisations financi|immobilisations corporelles|immobilisations incorporelles','non_current_assets'),(r'current assets|流动资产|actif circulant|cr[ée]ances|disponibilit|comptes de r[ée]gularisation','current_assets'),
             (r'non-?current liabilities|非流动负债','non_current_liabilities'),(r'current liabilities|流动负债','current_liabilities'),(r'^equity$|capital and reserves|所有者权益|股东权益|capitaux propres','equity')]

def slug_id(label,used,prefix='line'):
    base='_'.join(re.findall(r'[a-z0-9]+',label.lower()))[:40].strip('_') or prefix
    if not re.match(r'^[a-z]',base): base=prefix+'_'+base
    s,i=base,2
    while s in used: s=f'{base}_{i}'; i+=1
    used.add(s); return s

def assign_ids(items,children,st,used):
    canon_used=set()
    for i,it in enumerate(items):
        lab=norm_label(it['label']).lower(); labc=re.sub(r'\s+','',lab); sec=(it['section'] or '').lower(); it['tags']=[]
        cid=None
        if st=='balance_sheet' and re.search(r'应付票据',labc): it['tags']=['debt_like']
        elif st=='balance_sheet' and re.search(DEBT_RE,lab) and not re.search(r'total|合计',lab):
            it['tags']=['debt']; cur=(bool(re.search(r'(?<!non-)(?<!non )current|流动|within one year|一年内',sec+' '+lab)) and not re.search(r'non-?current|非流动',sec)) or bool(re.search(r'短期|short-term|current portion|due within|一年内到期',lab))
            cid='lease_liabilities' if re.search(r'lease|租赁',lab) else ('short_term_debt' if cur else 'long_term_debt')
            if cid in canon_used: cid=None
        if cid is None:
            for rx,c in ID_RULES[st]:
                if c not in canon_used and (re.search(rx,lab) or re.search(rx,labc)) and not (c=='revenue' and it['memo']): cid=c; break
        if cid is None and i in children and (it['label']=='Subtotal' or re.match(r'^total\s*\(?[ivx]+\)?$',lab)):
            for rx,c in SECTION_IDS:
                if re.search(rx,sec) and c not in canon_used and st=='balance_sheet': cid=c; break
        if st=='income_statement' and not it.get('total_of'):
            if re.search(r'non-?controlling|minority|少数股东|perpetual (?:capital )?securities holders|永续债持有人',lab+labc) and not re.search(r'comprehensive|综合收益',lab+labc): it['tags']=it['tags']+['attribution']
            elif re.search(r'impairment|减值损失|dépréciation exceptionnelle',lab+labc) and not re.search(r'credit|receivable|信用|loans? and advances',lab+labc): it['oneoff_candidate']='impairment'
            elif re.search(r'gain (?:on|from) (?:the )?(?:transfer|disposal|sale) of (?:business|subsidiar)|restructuring|^other charge|exceptionnel',lab): it['oneoff_candidate']='non_recurring'
        if cid and cid not in used: canon_used.add(cid); used.add(cid); it['id']=cid
        else: it['id']=slug_id(it['label'] if re.search('[a-z]',lab) else f'{st[:2]}_p{it["page"]}',used)

def detect_meta(texts):
    t=' '.join(texts); low=t.lower()
    unit='TODO'
    for rx,u in ((r'crore','crores'),(r'lakh','lakhs'),(r'百万元','millions'),(r'万元','ten_thousands'),(r'千元','thousands'),(r'millions?\b|\$m\b|\$\s?mn|hk\$m|€m|£m|rmb ?m\b','millions'),
                 (r'thousands?\b|’000|\'000|k ?€|k ?eur|milliers|£000','thousands'),(r'billions?\b|\$bn','billions'),(r'单位[:：]\s*(?:人民币)?\s*元|en euros|montants.{0,60}en €|\(euros?\)','ones')):
        if re.search(rx,low): unit=u; break
    cur='TODO'
    for rx,c in ((r'hk\$','HKD'),(r'人民币|rmb|cny','CNY'),(r'\byen\b|¥|円','JPY'),(r'€|\beur\b|euros?','EUR'),(r'£|gbp','GBP'),(r'a\$|aud','AUD'),(r'us\$|usd','USD'),(r'₹|inr|rupees','INR'),(r's\$|sgd','SGD')):
        if re.search(rx,low): cur=c; break
    return unit,cur

DATE_PATS=[(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',lambda m:(m[1],m[2],m[3])),(r'(\d{1,2})/(\d{1,2})/(\d{4})',lambda m:(m[3],m[2],m[1])),
           (r'([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})',lambda m:(m[3],m[1],m[2])),(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',lambda m:(m[3],m[2],m[1]))]
MONTHS={m:i for i,m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}

def parse_dates(text):
    out=[]
    for rx,f in DATE_PATS:
        for m in re.finditer(rx,text):
            y,mo,d=f(m)
            try:
                mo=int(mo) if str(mo).isdigit() else MONTHS[str(mo)[:3].lower()]
                out.append((m.start(),f'{int(y):04d}-{mo:02d}-{int(d):02d}'))
            except (KeyError,ValueError): continue
    return [d for _,d in sorted(out)]

def draft_map(input_file,out,pages=None,force=False):
    """Draft the normalized v2 input from the located statement pages: columns, signs, subtotals and canonical ids.
    The agent reviews and completes it (TODO fields, entity type, judgement calls); it never replaces that review."""
    import time
    if Path(out).exists() and not force:
        raise SystemExit(f'REFUSED: {out} already exists and may contain your edits. Keep editing it (edit-map), or pass --force to redraft from scratch, or use another --out.')
    if Path(input_file).suffix.lower() in ('.txt','.md') and pdf_reader():
        print('NOTE: a PDF reader is available. Drafting from the original PDF keeps column positions and gives more accurate signs and totals; pass the .pdf instead of this text copy unless the PDF is scanned.')
    t0=time.time(); doc,kind=load_document(input_file); byno=dict(doc)
    found=score_pages(doc,kind)
    chosen={}
    for st in STATEMENT_PATTERNS:
        if pages and pages.get(st): chosen[st]=sorted(pages[st]); continue
        c=found.get(st,[])
        if not c: continue
        first=c[0]['page']; extra=[x['page'] for x in c[1:3] if abs(x['page']-first)==1 and 'comprehensive' not in x['title'] and '综合收益' not in x['title']]
        chosen[st]=sorted(set([first]+extra))
    review=[]; used=set(); statements={}; all_texts=[]; header_years_all={}; N=None
    # number of year columns: from the statement headers (most common count of distinct years, default 2)
    probe={}
    for st,pgs in chosen.items():
        rows=[]; seen_pages=set()
        for p in pgs:
            got=[r for r in gather_rows(st,p,byno,kind) if r[0] not in seen_pages]
            rows+=got; seen_pages.update(pn for pn,_ in got)
        probe[st]=rows
        for pno,r in rows[:25]:
            ys=sorted(set(years_in(r['cells'])),key=years_in(r['cells']).index)
            if len(ys)>=2: header_years_all.setdefault(st,ys); break
    seqs=list(header_years_all.values()); years_order=max(seqs,key=len) if seqs else None
    N=len(years_order) if years_order else 2
    for st,rows in probe.items():
        order=header_years_all.get(st) or years_order
        if not order: review.append(f'{st}: year columns not detected; columns assumed most recent first'); order=list(range(N))
        elif len(order)!=N: review.append(f'{st}: {len(order)} year column(s) here but {N} elsewhere; the periods missing from this statement stay unavailable')
        items,hy=build_items(rows,len(order))   # each statement is parsed with its own column count, so order[j] always exists
        children=fit_totals(items,st) if items else {}
        filled=nil_fill(items,children)
        if filled: review.append(f"{st}: entered 0 for {len(filled)} blank value(s) whose printed subtotal ties without them ({', '.join(sorted(set(filled))[:5])}{'…' if len(set(filled))>5 else ''})")
        assign_ids(items,children,st,used)
        all_texts+= [' '.join(c[0] for c in r['cells']) for _,r in rows[:12]]
        lines=[]; doc_name=Path(input_file).name
        for i,it in enumerate(items):
            vals={str(order[j]):v for j,v in enumerate(it['vals']) if isinstance(order[j],int)}   # source precision is kept; rounding happens only when output is formatted
            it['label']=clean_label(it['label'])
            ln={'id':it['id'],'label':it['label'],'section':('memo' if it['memo'] else re.sub(r'[^a-z0-9]+','_',(it['section'] or '').lower()).strip('_')[:40] or None),'values':vals,
                'source':{'document':doc_name,'location':f"p.{it['page']}",'label':it['label']}}
            if it.get('total_of'): ln['total_of']=[items[c]['id'] for c in it['total_of']]
            if it['tags']: ln['tags']=it['tags']
            if it['id'] in GRAND_TOTALS: ln['section']=None
            lines.append(ln)
            if it['amb']: review.append(f"{st} p.{it['page']} '{it['label']}': fewer amounts than columns; check which year each value belongs to")
            if it.get('sign_guess'): review.append(f"{st} '{it['label']}': sign set from wording (not confirmed by a subtotal)")
            if it['label']=='Subtotal' and not it.get('total_of'): review.append(f"{st} p.{it['page']}: unlabelled amount row; label it or remove it")
            if st=='cash_flow' and re.search(r'held for sale|classified as held|disposal group',it['label'],re.I): review.append(f"cash_flow p.{it['page']} '{it['label']}': counted in the opening + flows = closing cash check (tag other bridging lines \"cash_reconciling\")")
            if it.get('oneoff_candidate'): review.append(f"{st} p.{it['page']} '{it['label']}' ({it['id']}): possible one-off — if it is (check the note), tag it \"{it['oneoff_candidate']}\"; recurring write-downs stay untagged")
        nfit=len(children); ntot=sum(1 for it in items if re.search(r'^total|合计|总计|^net cash|^profit|^gross|^operating (?:profit|income)|subtotal',it['label'],re.I))
        unmatched=[it['label'] for i,it in enumerate(items) if re.search(r'^total|合计|总计',it['label'],re.I) and not re.search(r'\bless\b|net current',it['label'],re.I) and i not in children]
        for u in unmatched[:8]: review.append(f"{st}: total '{u}' did not tie to the lines above it; check its components and signs")
        statements[st]=lines
        print(f"  {st}: pages {','.join(map(str,chosen[st]))} | {len(lines)} lines | {nfit} subtotals tied")
    isl=statements.get('income_statement',[]); idx={l['id']:l for l in isl}
    # share of results printed as "Joint ventures" / "Associates" under a "Share of results" heading -> one share_of_associates line
    if isl and 'share_of_associates' not in idx:
        sh=[l for l in isl if re.search(r'share_of',l.get('section') or '') and re.search(r'^(?:joint ventures?|associates?|associated companies)$',l['label'],re.I) and not l.get('total_of')]
        if len(sh)==1: sh[0]['id'],old='share_of_associates',sh[0]['id']; refs={old:'share_of_associates'}
        elif len(sh)>=2:
            refs={}; pos=isl.index(sh[-1])+1
            isl.insert(pos,{'id':'share_of_associates','label':'Share of results of joint ventures and associates','section':sh[0].get('section'),'total_of':[l['id'] for l in sh],'values':{}})
            for l in isl:
                if l.get('total_of') and l['id']!='share_of_associates' and set(x['id'] for x in sh)<=set(l['total_of']):
                    k=l['total_of'].index(sh[0]['id']); l['total_of']=[c for c in l['total_of'] if c not in {x['id'] for x in sh}]; l['total_of'].insert(k,'share_of_associates')
        else: refs={}
        for l in isl:
            if l.get('total_of'): l['total_of']=[refs.get(c,c) for c in l['total_of']]
        if sh: review.append("income_statement: share of results of joint ventures/associates mapped to share_of_associates (used for the tax rate, NOPAT and ROIC); confirm")
        idx={l['id']:l for l in isl}
    cfl=statements.get('cash_flow',[])
    dv=[l for l in cfl if not l.get('total_of') and re.search(r'(?:dividends?|distributions?).{0,25}(?:joint ventures?|associates?|equity.accounted)',l['label'],re.I)]
    if len(dv)>=2 and not any(l['id']=='distributions_from_associates' and l.get('total_of') for l in cfl):
        ren={}
        for i,l in enumerate(dv):
            if l['id']=='distributions_from_associates': ren[l['id']]=l['id']=f'distributions_from_associates_{i+1}'
        old=[l['id'] for l in dv]; pos=cfl.index(dv[-1])+1
        for l in cfl:   # point parents at the renamed component, then swap the components for the new total
            if l.get('total_of'):
                tot=[ren.get(c,c) for c in l['total_of']]
                hit=[k for k,c in enumerate(tot) if c in old]
                if hit: tot=[c for c in tot if c not in old]; tot.insert(hit[0],'distributions_from_associates')
                l['total_of']=tot
        cfl.insert(pos,{'id':'distributions_from_associates','label':'Dividends received from joint ventures and associates','section':dv[0].get('section'),'total_of':old,'values':{}})
        review.append("cash_flow: dividends from joint ventures and associates combined into distributions_from_associates (adjusted cash conversion); confirm")
    ni=idx.get('net_income'); ids={l['id'] for s in statements.values() for l in s}
    if ni and 'pretax_income' not in ids and 'tax_expense' in (ni.get('total_of') or []) and any(re.search(r'r[ée]sultat courant',idx[c]['label'],re.I) for c in ni['total_of'] if c in idx):
        comps=[c for c in ni['total_of'] if c!='tax_expense']; pos=isl.index(idx['tax_expense'])
        isl.insert(pos,{'id':'pretax_income','label':'Résultat avant impôts (derived: courant + exceptionnel + participation)','section':None,'total_of':comps,'values':{}})
        ni['total_of']=['pretax_income','tax_expense']
        review.append("income_statement: pretax_income derived as résultat courant + résultat exceptionnel + participation des salariés (not printed); confirm")
    ids={l['id'] for s in statements.values() for l in s}
    bs=statements.get('balance_sheet',[])
    if bs and 'total_assets' not in ids and {'current_assets','non_current_assets'}<=ids:
        bs.append({'id':'total_assets','label':'Total assets (derived; not printed)','section':None,'total_of':['current_assets','non_current_assets'],'values':{}})
    if bs and 'total_liabilities' not in ids and {'current_liabilities','non_current_liabilities'}<=ids:
        bs.append({'id':'total_liabilities','label':'Total liabilities (derived; not printed)','section':None,'total_of':['current_liabilities','non_current_liabilities'],'values':{}})
    isl=statements.get('income_statement',[])
    if 'd_and_a' not in ids:
        dep=next((l for l in isl if l['id']=='depreciation_expense'),None)
        if dep: statements.setdefault('supplementary',[]).append({'id':'d_and_a','label':'Depreciation and amortisation (from income statement)','section':'memo',
                    'values':{k:(abs(v) if v is not None else None) for k,v in dep['values'].items()},'source':dep['source']})
    ids={l['id'] for s_ in statements.values() for l in s_}   # include derived totals added above
    bsl=statements.get('balance_sheet',[])
    if any(l['id']=='perpetual_bonds' for l in bsl):
        review.append('perpetual_bonds: add perpetual_distributions (supplementary; profit or interest attributable to perpetual holders, e.g. 归属于永续债持有人的利息) so ROE on ordinary equity is correct; if the owners’ profit line already excludes the perpetual holders’ share, set owners_profit_excludes_perpetual: true instead')
    for l in bsl:
        if re.search(r'perpetual|永续',l['label'],re.I):
            v=[l['values'].get(str(y)) for y in sorted(int(k) for k in l['values'])] if l['values'] else []
            if len(v)>=2 and (v[-1] in (None,0)) and (v[-2] or 0)>0:
                review.append(f"balance_sheet '{l['label']}' fell to nil: check the borrowings note — if the securities were reclassified to borrowings, split that part out and tag it debt + perpetual")
    eb=[]; ent={}; auditor=False
    ENT={'payment_institution':r'payment institution|electronic money institution|e-money institution|safeguard(?:ed|ing) (?:funds|accounts)|payment services regulations',
         'bank':r'deposits from customers|loans and advances to customers|net interest income',
         'insurer':r'insurance contract liabilities|gross written premiums?|insurance service result',
         'asset_manager':r'assets under management',
         'conglomerate':r'banking business|credit card business|securities business|insurance business'}
    for pno,pg in doc:
        t=pg.get_text(); n=len(re.findall(r'\bEBITDAF?\b|息税折旧摊销前',t))
        if n and len(NUM_RE.findall(t))>=10: eb.append((n,pno))
        for k,rx in ENT.items():
            c=len(re.findall(rx,t,re.I))
            if c: ent.setdefault(k,[0,[]]); ent[k][0]+=c; ent[k][1].append(pno)
        if not auditor and re.search(r"independent auditor|auditor[’']s report|report of the (?:independent )?auditors?|rapport du commissaire aux comptes|审计报告|監査報告",t,re.I): auditor=True
    segs={x.lower() for pno,pg in doc for x in re.findall(r'(banking|credit card|securities|insurance) business',pg.get_text(),re.I)}
    sug=[(k,v) for k,v in ent.items() if v[0]>=(2 if k=='payment_institution' else 6) and k!='conglomerate']
    if 'payment_institution' not in ent and len(segs)>=2 and ent.get('conglomerate',[0])[0]>=6: sug=[('conglomerate',ent['conglomerate'])]   # a group with several financial arms
    if sug:
        k,(c,pg_)=max(sug,key=lambda kv:kv[1][0])
        review.append(f"entity_type: the report mentions {k.replace('_',' ')} terms {c} times (p.{', p.'.join(map(str,pg_[:4]))}); consider entity_type={k}"
                      +(' and supply client_funds / client_liabilities (safeguarded client money and the matching creditors)' if k=='payment_institution' else '')+' (see mapping-rules "Entity type")')
    if eb and statements:
        pp=sorted(pn for _,pn in sorted(eb,reverse=True)[:4])
        review.append(f"EBITDA: the report shows EBITDA on p.{', p.'.join(map(str,pp))} - add the company's statutory EBITDA (the figure it reconciles to the income statement) as supplementary 'ebitda' (see mapping-rules 'EBITDA')")
    if 'balance_sheet' in statements and 'current_assets' in ids and 'current_liabilities' not in ids:
        pcg=any(re.search(r'^total iv$',l['label'],re.I) for l in statements['balance_sheet'])
        review.append('balance_sheet: current_liabilities not recognised; '+("French PCG: dettes (TOTAL IV) are usually due within one year - check the état des échéances note, then rename TOTAL IV to current_liabilities (split out any part due after one year)" if pcg else 'rename the current liabilities total to current_liabilities (or add it as a total_of the current lines)')+' so the current ratio can be computed')
    req={'income_statement':['revenue','pretax_income','net_income'],'balance_sheet':['cash','total_assets','equity'],'cash_flow':['ocf','cash_end']}
    for st,need in req.items():
        if st in statements:
            miss=[x for x in need if x not in ids]
            if miss: review.append(f"{st}: map {', '.join(miss)} (canonical ids not recognised automatically)")
        elif st!='cash_flow': review.append(f"{st}: statement not found; pass --{ {'income_statement':'is','balance_sheet':'bs'}[st]} <pages>")
    if 'income_statement' in statements:
        if not ({'operating_income','ebit'} & ids): review.append('EBIT: no operating profit line recognised; add operating_income as a total_of the lines above profit before finance costs, or an ebit line (note), or set ebit_method')
        if 'interest_expense' not in ids: review.append('interest_expense not recognised: map interest on borrowings and leases (finance costs note) as a negative line')
        if 'd_and_a' not in ids and 'depreciation_expense' not in ids: review.append('d_and_a not found on the statements: take depreciation and amortisation from the notes (supplementary, positive) so EBITDA can be computed')
    if 'balance_sheet' in statements and not any('debt' in l.get('tags',[]) for l in statements['balance_sheet']):
        review.append('no borrowings tagged "debt": tag every interest-bearing line, check the notes for leases, and if the company has no borrowings add a borrowings line of 0 tagged debt (so net cash and interest cover are shown correctly)')
    review.append('one-offs: tag impairments (incl. goodwill write-downs shown as "other charge") "impairment" and other one-off gains/losses "non_recurring"; supply the reported EBITDA if the report gives one')
    unit,cur=detect_meta(all_texts+[byno[p].get_text()[:1500] for pgs in chosen.values() for p in pgs[:1]])
    hdr=' '.join(all_texts)
    yrs=sorted(y for y in (years_order or []) if isinstance(y,int))
    interim=re.search(r'前三季度|1[-—–]9\s*月|nine months|\b9m\b|six months|half[- ]year|半年|first half|三季度|first quarter|第一季度|three months',hdr,re.I)
    months=9 if interim and re.search(r'前三季度|1[-—–]9|nine|9m|三季度',interim.group(0),re.I) else 6 if interim and re.search(r'six|half|半年',interim.group(0),re.I) else 3 if interim else 12
    bs_dates=parse_dates(' '.join(' '.join(c[0] for c in r['cells']) for _,r in probe.get('balance_sheet',[])[:12]))
    unaudited=bool(re.search(r'未经审计|unaudited',hdr+' '.join(byno[pgs[0]].get_text()[:1500] for pgs in chosen.values()),re.I))
    periods=[]
    for y in yrs:
        leap=(y%4==0 and y%100!=0) or y%400==0
        days={12:366 if leap else 365,9:274 if leap else 273,6:182 if leap else 181,3:91 if leap else 90}[months]
        p={'year':y,'label':(f'FY{y}' if months==12 else f'{months}M {y}'),'days':days,'period_type':'annual' if months==12 else 'interim'}
        bd=next((d for d in bs_dates if d.startswith(str(y))),None)
        if bd: p['balance_date']=bd
        latest=next((d for d in bs_dates if d.startswith(str(yrs[-1]))),None)
        if months!=12 and latest: p['flow_end']=f'{y}{latest[4:]}'
        if unaudited: p['audited']=False
        elif auditor and months==12: p['audited']=True
        periods.append(p)
    if months!=12: review.append('interim report detected: confirm period labels, days and balance_date (the comparative balance sheet is often the prior year end)')
    cjk=re.search('[一-鿿]',hdr) is not None
    draft={'schema_version':'2.0','company':'TODO','currency':cur,'unit':unit,
           'basis':'consolidated' if re.search(r'consolidated|合并|\bgroup\b',hdr+' '.join(byno[pgs[0]].get_text()[:3000] for pgs in chosen.values()),re.I) else 'TODO','entity_type':'operating',
           **({'accounting_framework':'CAS'} if cjk and re.search(r'合并|项目',hdr) else {}),
           **({'fiscal_year_end':periods[-1]['balance_date'][5:]} if months==12 and periods and periods[-1].get('balance_date') else {}),
           'periods':periods,'statements':statements,
           'draft_review':['Fill every TODO field (company; currency/unit/basis if TODO); set entity_type if not an operating company']+review,
           'draft_notes':f'Drafted automatically by draft-map {__version__} from pages {chosen}. Values and pages are as printed; signs and subtotals were inferred from how the lines add up. Review every draft_review item before analyze.'}
    out=write_text_safe(out,json.dumps(draft,indent=1,ensure_ascii=False))
    print(f'Drafted {sum(len(v) for v in statements.values())} lines in {time.time()-t0:.1f}s -> {Path(out).resolve()}')
    print(f'DETECTED: unit={unit} currency={cur} periods={[p["label"] for p in periods]}')
    print(f'REVIEW ({len(draft["draft_review"])} items):'); [print('  -',r) for r in draft['draft_review'][:40]]
    print('Next: make the review changes with edit-map (or edit the JSON directly), then analyze.')

def edit_map(path,ops):
    """Apply review edits to a normalized input in place, without ad-hoc scripts. Lines are addressed by id (in any statement)."""
    d=json.loads(Path(path).read_text(encoding='utf-8-sig')); log=[]
    def find(i):
        for st,lines in d.get('statements',{}).items():
            for k,l in enumerate(lines):
                if l.get('id')==i: return st,k,l
        raise SystemExit(f'ERROR: no line with id {i!r} in {path}')
    def num(v):
        v=v.strip()
        if v.lower() in ('null','none',''): return None
        return float(v) if re.search(r'[.eE]',v) else int(v)
    def split(arg,sep='='):
        if sep not in arg: raise SystemExit(f'ERROR: expected KEY{sep}VALUE, got {arg!r}')
        return [x.strip() for x in arg.split(sep,1)]
    KNOWN_TAGS={'debt','debt_like','perpetual','impairment','non_recurring','attribution','fs_operating','cash_reconciling','fx_translation'}
    for op,arg in ops:
        if op=='remove': op='omit'
        if op in ('tag','untag'):
            t=arg.split('=',1)[-1].strip()
            if op=='tag' and t not in KNOWN_TAGS: raise SystemExit(f'ERROR: unknown tag {t!r}; use one of: '+', '.join(sorted(KNOWN_TAGS))+' (to stop a line counting as debt, untag it)')
            if op=='tag' and t in ('impairment','non_recurring'):
                hit=find(arg.split('=',1)[0].strip())
                if hit and hit[0]!='income_statement':
                    raise SystemExit(f"ERROR: {t} tags belong on income statement lines only ({hit[2]['id']} is on the {hit[0].replace('_',' ')}; a cash flow add-back has the opposite sign). Tag the income statement line instead.")
        if op=='field':
            k,v=split(arg)
            try: v=json.loads(v)
            except ValueError: pass
            d[k]=v; log.append(f'{k} = {v!r}')
        elif op=='flip':
            for i in arg.split(','):
                _,_,l=find(i.strip()); l['values']={y:(-x if isinstance(x,(int,float)) else x) for y,x in l.get('values',{}).items()}; log.append(f'flipped sign of {i.strip()}')
        elif op=='set':
            k,v=split(arg); i,_,y=k.rpartition('.')
            if not i: raise SystemExit(f'ERROR: --set needs ID.YEAR=VALUE, got {arg!r}')
            _,_,l=find(i); l.setdefault('values',{})[y]=num(v); log.append(f'{i}[{y}] = {v}')
        elif op in ('tag','untag'):
            i,t=split(arg); _,_,l=find(i); tags=[x for x in l.get('tags',[]) if x!=t]
            if op=='tag': tags.append(t)
            if tags: l['tags']=tags
            else: l.pop('tags',None)
            log.append(f'{op} {i} {t}')
        elif op=='rename':
            a,b=split(arg); _,_,l=find(a)
            if any(x.get('id')==b for ls in d['statements'].values() for x in ls): raise SystemExit(f'ERROR: id {b!r} is already used; rename or remove that line first')
            l['id']=b
            for ls in d['statements'].values():
                for x in ls:
                    if x.get('total_of'): x['total_of']=[b if c==a else c for c in x['total_of']]
            log.append(f'renamed {a} -> {b}')
        elif op=='total-of':
            i,v=split(arg); _,_,l=find(i); comps=[c.strip() for c in v.split(',') if c.strip()]
            for c in comps: find(c)
            if comps: l['total_of']=comps
            else: l.pop('total_of',None)
            log.append(f'{i} total_of {comps}')
        elif op=='omit':
            for i in arg.split(','):
                st,k,_=find(i.strip()); del d['statements'][st][k]
                for ls in d['statements'].values():
                    for x in ls:
                        if x.get('total_of') and i.strip() in x['total_of']: x['total_of']=[c for c in x['total_of'] if c!=i.strip()]
                log.append(f'omitted {i.strip()} from the mapping')
        elif op=='add':
            try: ln=json.loads(arg)
            except ValueError as e: raise SystemExit(f'ERROR: --add needs a JSON line object with "statement": {e}')
            st=ln.pop('statement',None)
            if st not in ('income_statement','balance_sheet','cash_flow','supplementary') or not ln.get('id'): raise SystemExit('ERROR: --add needs "statement" (income_statement, balance_sheet, cash_flow or supplementary) and "id"')
            if any(x.get('id')==ln['id'] for ls in d['statements'].values() for x in ls): raise SystemExit(f"ERROR: id {ln['id']!r} already exists")
            after=ln.pop('after',None); lines=d['statements'].setdefault(st,[])
            pos=next((k+1 for k,x in enumerate(lines) if x.get('id')==after),len(lines)) if after else len(lines)
            lines.insert(pos,ln); log.append(f"added {ln['id']} to {st}")
    Path(path).write_text(json.dumps(d,indent=1,ensure_ascii=False),encoding='utf-8')
    for x in log: print('  ',x)
    print(f'Applied {len(log)} edit(s) to {Path(path).resolve()}')


def extract_pdf(input_file,out,pages=None):
    doc,kind=load_document(input_file); res=[]
    if not pages and len(doc)>40:
        print(f'WARNING: {len(doc)}-page document with no --pages filter. Run locate-statements first; full extraction is too large to review reliably.')
    for pno,p in doc:
        if pages and pno not in pages: continue
        rows=[r for r in page_rows(p,kind) if NUM_RE.search(r)]
        if rows: res.append({'page':pno,'rows':rows,'review_required':True})
    out=write_text_safe(out,json.dumps({'source':str(input_file),'input_kind':kind,'candidate_pages':res,'status':'unverified_extraction_do_not_analyze_directly'},indent=2,ensure_ascii=False))
    print('Wrote',Path(out).resolve())

def extract_csv(input_file,out):
    with open(input_file,encoding='utf-8-sig',newline='') as f: rows=list(csv.reader(f))
    out=write_text_safe(out,json.dumps({'source':str(input_file),'rows':rows,'status':'unverified_extraction_do_not_analyze_directly'},indent=2,ensure_ascii=False))
    print('Wrote REVIEW-REQUIRED candidates:',Path(out).resolve())

MAX_XLSX_PART=200*1024*1024; MAX_XLSX_TOTAL=1024*1024*1024
def zread(z,name,budget):
    """Bounded read of one XLSX part: decompression stops at the limit instead of inflating the whole entry first, so a small
    archive that expands to gigabytes cannot exhaust memory. `budget` accumulates the bytes read across parts."""
    with z.open(name) as f: data=f.read(MAX_XLSX_PART+1)
    if len(data)>MAX_XLSX_PART: raise ValueError(f'XLSX part {name} is too large to read safely')
    budget[0]+=len(data)
    if budget[0]>MAX_XLSX_TOTAL: raise ValueError('XLSX expands to more than the supported size')
    return data

def safe_xml(raw):
    """Parse an XLSX part from an untrusted upload: real XLSX parts never contain a DTD, so DOCTYPE/ENTITY is refused."""
    if len(raw)>200*1024*1024: raise ValueError('XLSX part too large to read safely')
    if b'<!DOCTYPE' in raw[:4096].upper() or b'<!ENTITY' in raw.upper(): raise ValueError('XLSX contains a DTD/entity declaration; refusing to parse it')
    return ET.fromstring(raw)  # nosec B314 - DTD/entities refused above

def read_xlsx(input_file):
    """Worksheets of an XLSX as [{'sheet','sheet_xml','rows':[[{'cell','value','formula'}]]}], standard library only."""
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(input_file) as z:
        strings=[]; names={}; budget=[0]
        try:   # map worksheet files to tab names so values can be cited as 'sheet: Balance Sheet'
            rel_ns='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
            wb=safe_xml(zread(z,'xl/workbook.xml',budget)); rels=safe_xml(zread(z,'xl/_rels/workbook.xml.rels',budget))
            tgt={r.get('Id'):r.get('Target') for r in rels}
            for sh in wb.findall('.//x:sheets/x:sheet',ns): names['xl/'+tgt.get(sh.get(rel_ns),'').lstrip('/').replace('xl/','',1)]=sh.get('name')
        except (KeyError,ValueError,ET.ParseError): pass
        if 'xl/sharedStrings.xml' in z.namelist():
            root=safe_xml(zread(z,'xl/sharedStrings.xml',budget))
            strings=[''.join(t.text or '' for t in si.findall('.//x:t',ns)) for si in root.findall('x:si',ns)]
        sheets=[]
        for file in sorted(n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)):
            root=safe_xml(zread(z,file,budget)); rows=[]
            for row in root.findall('.//x:sheetData/x:row',ns):
                values=[]
                for cell in row.findall('x:c',ns):
                    v=cell.find('x:v',ns); inline=cell.find('x:is',ns); raw=v.text if v is not None else ''.join(t.text or '' for t in inline.findall('.//x:t',ns)) if inline is not None else ''
                    if cell.get('t')=='s' and raw:raw=strings[int(raw)]
                    values.append({'cell':cell.get('r'),'value':raw,'formula':cell.find('x:f',ns).text if cell.find('x:f',ns) is not None else None})
                if values:rows.append(values)
            sheets.append({'sheet':names.get(file,file),'sheet_xml':file,'rows':rows})
    return sheets

def extract_xlsx(input_file,out):
    sheets=read_xlsx(input_file)
    out=write_text_safe(out,json.dumps({'source':str(input_file),'sheets':sheets,'status':'unverified_extraction_do_not_analyze_directly'},indent=2,ensure_ascii=False))
    print('Wrote REVIEW-REQUIRED candidates:',Path(out).resolve())

PCT_IDS={'cet1_ratio','total_capital_ratio','solvency_ratio'}   # entered as decimals (0.145); reports print them as percentages (14.5%)
SHEET_SUFFIXES=('.xlsx','.xlsm','.csv','.tsv')

def sheet_pages(doc_file):
    """(sheet name, TextPage) per worksheet of an XLSX, or one page for a CSV/TSV, so spreadsheet citations can be
    checked like PDF pages. Cite the sheet name in the location (e.g. 'Balance Sheet!B12')."""
    p=Path(doc_file); suf=p.suffix.lower()
    # cells are tab-separated: a space between two amounts would read as a thousands separator ("600 310" -> 600310)
    if suf in ('.csv','.tsv'):
        with open(p,encoding='utf-8-sig',newline='') as f: rows=list(csv.reader(f,delimiter='\t' if suf=='.tsv' else ','))
        return [(p.stem,TextPage('\n'.join('\t'.join(r) for r in rows)))]
    return [(sh['sheet'],TextPage('\n'.join('\t'.join(str(c['value']) for c in row) for row in sh['rows']))) for sh in read_xlsx(p)]

def check_sources(json_file,doc_file):
    """Check each source value of a normalized input against the text it cites: a PDF page (page numbers as draft-map
    and page-text show them), a page-marked OCR text, or a worksheet / CSV (cited by sheet name). Reports values not
    found there and where they do appear."""
    d=json.loads(Path(json_file).read_text(encoding='utf-8-sig')); cache={}
    if Path(doc_file).suffix.lower() in SHEET_SUFFIXES: doc,kind=sheet_pages(doc_file),'sheet'
    else: doc,kind=load_document(doc_file)
    byno=dict(doc)
    if kind=='pdf' and sum(len(pg.get_text().strip()) for _,pg in doc[:min(len(doc),20)])<200:
        print('SOURCES: the PDF has no text layer (scanned), so citations were not checked; pass the OCR text copy (with page markers) as --doc instead.'); return
    sep='[ ,\u00a0\u202f\u2009]'
    def nums(pno):
        if pno not in cache:
            t=byno[pno].get_text() if pno in byno else ''; out=set()
            for m_ in re.finditer(r'\d{1,3}(?:'+sep+r'\d{3})+(?:[.,]\d+)?|\d+(?:\.\d+)?',t):
                try: out.add(round(float(re.sub(sep,'',m_.group(0))),4))
                except ValueError: pass
            cache[pno]=out
        return cache[pno]
    def on(pno,a): return a in nums(pno) or (float(a).is_integer() and any(a==round(x) for x in nums(pno) if abs(x-a)<1))
    where_word='sheet' if kind=='sheet' else 'page'; unit='sheet ' if kind=='sheet' else 'p.'
    total=found=0; miss=[]; skipped=0
    for st,lines in d.get('statements',{}).items():
        for l in lines:
            for y,v in (l.get('values') or {}).items():
                if not isinstance(v,(int,float)) or v==0: continue
                src=((l.get('sources') or {}).get(y) or l.get('source') or {}); loc=str(src.get('location',''))
                if re.search(r'\bderived\b|[+=]',loc,re.I): skipped+=1; continue   # only an explicit "(derived ...)" location is skipped, never a label
                if kind=='sheet': where=[k for k in byno if str(k).lower() in loc.lower()]   # the cited sheet only; an unnamed or unknown sheet is a miss
                else:
                    mm=re.search(r'p(?:age)?\.?\s*(\d+)',loc,re.I)
                    if not mm: skipped+=1; continue
                    where=[int(mm.group(1))]
                cands={round(abs(v),4)}
                if l['id'] in PCT_IDS or (st=='supplementary' and l['id'].endswith(('_ratio','_pct')) and abs(v)<1): cands.add(round(abs(v)*100,4))   # 0.145 is printed as 14.5
                total+=1
                if any(on(p,a) for p in where for a in cands): found+=1; continue
                alt=[q for q in (list(byno) if kind=='sheet' else sorted(byno)) if q not in where and any(a in nums(q) for a in cands)][:4]
                miss.append(f"  NOT ON CITED {where_word.upper()}: {l['id']}[{y}] = {v:,} cited {loc!r}"+(' (names no sheet of the workbook)' if kind=='sheet' and not where else '')
                            +(f" - appears on {unit}{(', '+unit).join(map(str,alt))}" if alt else ' - not found in the document'))
    print(f'SOURCES: {found} of {total} values found on their cited {where_word} ({skipped} derived/unnumbered values skipped)'+('' if miss else ' - all citations verified'))
    for x in miss[:40]: print(x)
    if miss: print('Fix each citation (for spreadsheets cite the sheet name; for PDFs use the page number shown by page-text, not the one printed on the page), or mark derived values "(derived ...)" in the location, then re-run analyze.')

def page_text(input_file,pages=None,find=None,width=4000):
    """Print the text of selected pages (with page numbers), or with --find the pages and lines that match a term."""
    doc,kind=load_document(input_file)
    if find:
        rx=re.compile(find,re.I); hits=0
        for pno,pg in doc:
            if pages and pno not in pages: continue
            ls=[l.strip() for l in pg.get_text().splitlines() if rx.search(l)]
            if ls:
                hits+=1; print(f'--- p.{pno}: {len(ls)} match(es)')
                for l in ls[:8]: print('   ',l[:200])
            if hits>=40: print('(stopped after 40 pages; narrow --pages or --find)'); break
        if not hits: print('no matches')
        return
    if not pages: raise SystemExit('ERROR: pass --pages (e.g. 95,100-101) or --find <term>')
    for pno,pg in doc:
        if pno in pages: print(f'--- Page {pno} ---'); print(pg.get_text()[:width])

def check_env(file=None):
    """Report what this runtime can do, so a failure is diagnosed instead of worked around."""
    import sys, platform
    print('python:',platform.python_version(),'| executable:',sys.executable)
    reader=pdf_reader()
    print('pdf reader:',{'pymupdf':'PyMuPDF','pypdfium2':'pypdfium2'}.get(reader,'NOT AVAILABLE - make a text copy with the platform\'s PDF extraction (one file at a time) and pass the .txt. Do not stop.'))
    print('ocr engine:','rapidocr' if ocr_engine_available() else 'none (for scanned PDFs use the platform OCR text)')
    if file:
        p=Path(file)
        if not p.exists(): print('file: NOT FOUND at',p.resolve(),'- the uploaded file is not visible to the script; ask the user to re-attach it or state where it is')
        else:
            print('file: found',p.resolve(),f'({p.stat().st_size//1024} KB)')
            if p.suffix.lower()=='.pdf' and reader:
                try:
                    pg=open_pdf(str(p)); chars=sum(len(x.get_text().strip()) for _,x in pg[:20])
                    print('pdf pages:',len(pg),'| text layer:','yes' if chars>=200 else 'NO (scanned) - run ocr-pdf on the statement pages, or use the platform OCR text')
                    if chars>=200: print('next: pass this PDF itself to draft-map (no text copy or other PDF tool needed)')
                except Exception as e: print('pdf: CANNOT OPEN -',e)  # report, never crash the environment check
            elif p.suffix.lower() in ('.txt','.md'):
                pages,_=load_document(p); print('text pages detected:',len(pages))
    import tempfile
    print('writable working dir:','yes' if os_access_ok() else 'NO','| writable temp dir:','yes' if os_access_ok(tempfile.gettempdir()) else 'NO',f'({tempfile.gettempdir()})')

def os_access_ok(d='.'):
    import tempfile
    try:
        Path(d).mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=d,delete=True): return True
    except OSError: return False

def writable_dir(requested):
    """The requested output directory if it can be written, else a fresh directory under the system temp folder."""
    import tempfile
    if os_access_ok(requested): return Path(requested)
    fb=Path(tempfile.gettempdir())/('fsi-output-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    if not os_access_ok(fb): raise SystemExit(f'Cannot write to {requested} or {fb}. Ask the user where files may be saved.')
    print(f'NOTE: {Path(requested).resolve()} is not writable; writing to {fb.resolve()} instead.')
    return fb

def write_text_safe(out,text):
    out=Path(out); d=writable_dir(out.parent if str(out.parent) else '.'); target=d/out.name
    target.write_text(text,encoding='utf-8'); return target

def output_stem(res,out,name=None):
    """Unique, readable file stem per report, e.g. 'CLP-Holdings-Limited_FY2024' or 'Xiamen-ITG-Group-Corp-Ltd_9M-2025'."""
    def slug(t,n): return '-'.join(re.findall(r'[A-Za-z0-9]+',str(t)))[:n].strip('-')
    base=slug(name,80) if name else f"{slug(res['company'],50) or 'Company'}_{slug(res['periods'][-1]['label'],20) or res['years'][-1]}"
    stem,i=base,2
    while (Path(out)/f'{stem}.xlsx').exists(): stem=f'{base}_{i}'; i+=1
    return stem

def sys_argv_ops():
    """edit-map operations in command-line order (argparse groups them by option)."""
    import sys
    names={'--field','--flip','--set','--tag','--untag','--rename','--total-of','--omit','--remove','--add','--ops'}; argv=sys.argv[1:]; out=[]
    for k,x in enumerate(argv):
        if x in names and k+1<len(argv): out.append((x[2:],argv[k+1]))
        elif '=' in x and x.split('=',1)[0] in names: out.append((x.split('=',1)[0][2:],x.split('=',1)[1]))
    exp=[]
    for op,arg in out:   # --ops edits.json: a list of {"op": "flip", "arg": "id"} (or ["flip","id"]), applied in order
        if op!='ops': exp.append((op,arg)); continue
        try: lst=json.loads(Path(arg).read_text(encoding='utf-8-sig'))
        except (OSError,ValueError) as e: raise SystemExit(f'ERROR: cannot read --ops file {arg}: {e}')
        for o in lst:
            k,v=(o.get('op'),o.get('arg')) if isinstance(o,dict) else (o[0],o[1])
            if k=='add' and not isinstance(v,str): v=json.dumps(v,ensure_ascii=False)
            exp.append((str(k).lstrip('-'),v))
    return exp

def main():
    import sys
    for stream in (sys.stdout,sys.stderr):   # a console that cannot show a character (e.g. cp1252) must not crash the run
        try: stream.reconfigure(errors='replace')
        except (AttributeError,ValueError): pass
    parser=argparse.ArgumentParser(description=__doc__); sub_=parser.add_subparsers(dest='command',required=True)
    for kind in ('locate-statements','extract-pdf','extract-csv','extract-xlsx'):
        p=sub_.add_parser(kind);p.add_argument('input');p.add_argument('--out',required=True)
        if kind in ('locate-statements','extract-pdf'): p.add_argument('--pages',help='1-based pages, e.g. 197-201,245')
    p=sub_.add_parser('draft-map',help='Draft the normalized input from the located statement pages');p.add_argument('input');p.add_argument('--out',required=True)
    for k,h in (('--is','income statement'),('--bs','balance sheet'),('--cf','cash flow')): p.add_argument(k,dest=k[2:]+('_' if k=='--is' else ''),help=f'pages of the {h}, e.g. 197 or 6-8 (overrides auto-detection)')
    p.add_argument('--force',action='store_true',help='overwrite an existing --out file (discards edits made to it)')
    p=sub_.add_parser('edit-map',help='Apply review edits to a normalized input in place');p.add_argument('input')
    for k,h in (('--field','top-level KEY=VALUE, e.g. company="Acme Ltd" or entity_type=bank (JSON values allowed)'),('--flip','negate every value of line ID (comma-separated ids allowed)'),
                ('--set','ID.YEAR=VALUE (null clears)'),('--tag','ID=TAG'),('--untag','ID=TAG'),('--rename','OLD=NEW (total_of references follow)'),
                ('--total-of','ID=comp1,comp2,... (empty clears)'),('--omit','ID: take the line out of the mapping (comma-separated allowed)'),('--remove',argparse.SUPPRESS),
                ('--add','JSON line with "statement" and optional "after": an id'),('--ops','JSON file with a list of {"op": ..., "arg": ...} edits, applied in order')):
        p.add_argument(k,action='append',default=[],help=h)
    p=sub_.add_parser('check-sources',help='Check every cited value against its page in the source document');p.add_argument('input');p.add_argument('--doc',required=True)
    p=sub_.add_parser('page-text',help='Print report pages, or find the pages that mention a term');p.add_argument('input');p.add_argument('--pages');p.add_argument('--find')
    p=sub_.add_parser('ocr-pdf',help='OCR scanned pages to text');p.add_argument('input');p.add_argument('--out',required=True);p.add_argument('--pages');p.add_argument('--dpi',type=int,default=200)
    sub_.add_parser('version')
    p=sub_.add_parser('check-env');p.add_argument('--file',help='Path of the user file to check')
    p=sub_.add_parser('analyze');p.add_argument('input');p.add_argument('--out',required=True)
    p.add_argument('--name',help='Output file name stem; default <Company>_<latest period>, made unique within the output folder')
    p.add_argument('--demo',action='store_true',help='Allow synthetic/demo input. Never use for a user\'s own documents.')
    p.add_argument('--doc',help='The source document (PDF, or the OCR text copy for a scanned PDF): every cited value is then checked against its page')
    a=parser.parse_args()
    if a.command=='version': print('financial-statement-intelligence',__version__); return
    if a.command=='check-env': print('skill version:',__version__); check_env(a.file); return
    if a.command=='draft-map':
        ov={st:parse_pages(v) for st,v in (('income_statement',a.is_),('balance_sheet',a.bs),('cash_flow',a.cf)) if v}
        draft_map(a.input,a.out,ov or None,a.force); return
    if a.command=='edit-map':
        ops=[]
        for raw in sys_argv_ops(): ops.append(raw)
        edit_map(a.input,ops); return
    if a.command=='check-sources': check_sources(a.input,a.doc); return
    if a.command=='page-text': page_text(a.input,parse_pages(a.pages) if a.pages else None,a.find); return
    if a.command=='ocr-pdf': ocr_pdf(a.input,a.out,parse_pages(a.pages),a.dpi); return
    if a.command in ('locate-statements','extract-pdf'):
        {'locate-statements':locate_statements,'extract-pdf':extract_pdf}[a.command](a.input,a.out,pages=parse_pages(a.pages)); return
    if a.command!='analyze':{'extract-csv':extract_csv,'extract-xlsx':extract_xlsx}[a.command](a.input,a.out);return
    data=json.loads(Path(a.input).read_text(encoding='utf-8-sig'))
    if not isinstance(data,dict): raise ValueError('the normalized input must be a JSON object (see references/statement-schema.json)')
    missing=[k for k in ('company','currency','unit','periods','statements') if k not in data]
    if missing: raise ValueError('missing required field(s): '+', '.join(missing))
    todo=[k for k in ('company','currency','unit','basis') if str(data.get(k,'')).strip().upper()=='TODO']
    if todo: raise ValueError('the draft still has TODO in: '+', '.join(todo)+'. Fill them from the document (and work through draft_review) before analyze')
    if a.demo and not is_demo(data): raise ValueError('--demo is only for files marked "demo": true. Never use it for a user\'s documents.')
    if is_demo(data) and not a.demo:
        raise SystemExit('REFUSED: this input is synthetic demo data ("'+str(data.get('company'))+'"). Analyse the user\'s own documents instead. '
                         'Only pass --demo when the user explicitly asked for a demo run, and label the result as demo data.')
    res=run_analysis(data);out=writable_dir(a.out)
    stem=output_stem(res,out,a.name)
    (out/f'{stem}.html').write_text(report_html(res),encoding='utf-8')
    write_xlsx(out/f'{stem}.xlsx',res)
    public={k:v for k,v in res.items() if k!='_render'}
    public['checks']=[{k:v for k,v in c.items() if k not in ('lf','rf','kind','line')} for c in res['checks']]
    (out/f'{stem}_analysis.json').write_text(json.dumps(public,indent=2,allow_nan=False),encoding='utf-8')
    write_csv(out/f'{stem}_ratio-audit.csv',res['audit'],['year','sheet','metric','label','formula','excel_formula','inputs','source_refs','value','display','status','reason'])
    write_csv(out/f'{stem}_validation.csv',res['checks'],['year','check','status','difference','message','source_refs'])
    print('Created report, audit, validations and workbook in',out.resolve())
    print('WORKBOOK:',(out/f'{stem}.xlsx').resolve()); print('REPORT:',(out/f'{stem}.html').resolve())
    pl=[p['label'] for p in res['periods']]
    print(f"ANALYSED: {res['company']} | {res['currency']} {res['unit']} (shown in {res['display_unit']}) | {res['basis']} | {' / '.join(pl)}"
          +(f" | {res['entity_type'].upper()}" if res['entity_type']!='operating' else '')+(' | INTERIM' if res['interim'] else '')+(' | NO CASH FLOW STATEMENT' if not res['has_cash_flow'] else '')+(' | UNAUDITED' if res['unaudited'] else '')+(' | DEMO DATA' if res['demo'] else ''))
    print('Confirm the company, currency and years above match the user\'s document before delivering.')
    fails=[c for c in res['checks'] if c['status']=='fail']
    print('Failed checks:',len(fails))
    for c in fails[:12]: print(f"  FAIL {c['year']}: {c['check']} (difference {c.get('difference')})")
    for c in [c for c in res['checks'] if c['status']=='review'][:6]: print(f"  REVIEW {c['year']}: {c['check']}")
    last=res['periods'][-1]; mt=last['metrics']
    keys=('revenue_growth','gross_margin','operating_margin','net_margin','roe','roic','current_ratio','net_debt_to_ebitda','interest_coverage','cash_conversion',
          'cost_to_income','nim','cost_of_risk','loan_to_deposit','combined_ratio','cet1')
    kp=[f"{k}={mt[k]:.4g}" for k in keys if isinstance(mt.get(k),(int,float))]
    if kp: print(f"KPIs {last['label']}: "+', '.join(kp))
    for fnd in findings(res): print('FINDING:',fnd)
    hints=agent_hints(res)
    for i,h in enumerate(hints,1): print(f'HINT {i}:',h)
    for d in res.get('key_disclosures') or []:
        src=d.get('source'); loc=src.get('location','') if isinstance(src,dict) else (src or '')
        print('DISCLOSURE:',d.get('text',''),f'[{loc}]' if loc else '')
    if a.doc:
        try: check_sources(a.input,a.doc)
        except Exception as e:   # no STATUS line: an unverified mapping must not read as OK. The files above are written but not cleared for delivery.
            raise SystemExit(f'ERROR: citations could not be checked against {a.doc}: {e}. Fix the --doc path (check-env --file shows it) and re-run analyze; do not deliver until SOURCES has run.')
    print('STATUS:',('PRELIMINARY - show the failed checks to the user before calling any conclusion final' if fails else 'OK - no failed reconciliation checks')
          +(f' | {len(hints)} HINT follow-up(s) open: act on each and re-run, or list it with the reason in the judgement calls' if hints else ' | no follow-ups open'))

def cli():
    import sys
    try: main()
    except SystemExit: raise
    except FileNotFoundError as e: print(f'ERROR: file not found: {e.filename}. Run check-env --file <path> and ask the user to re-attach the file if needed.',file=sys.stderr); sys.exit(2)
    except json.JSONDecodeError as e: print(f'ERROR: the input is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}',file=sys.stderr); sys.exit(2)
    except KeyError as e: print(f'ERROR: missing required field {e}. See references/statement-schema.json.',file=sys.stderr); sys.exit(2)
    except (ValueError,TypeError,zipfile.BadZipFile) as e: print(f'ERROR: {e}. Fix the normalized input and re-run; do not substitute other data.',file=sys.stderr); sys.exit(2)

if __name__=='__main__':cli()
