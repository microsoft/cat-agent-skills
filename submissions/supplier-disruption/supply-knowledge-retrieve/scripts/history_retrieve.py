"""Compute supplied-log delivery history, as-of bounded; no network or supplier actions."""
import argparse,csv,json,sys
from datetime import date,timedelta
from pathlib import Path
from output_safety import check_outputs,write_outputs

def history(rows,as_of,window_days,chronic_threshold=None,source='supplied history CSV'):
    asof=date.fromisoformat(as_of)
    if not isinstance(window_days,int) or isinstance(window_days,bool) or window_days<1:raise ValueError('positive history window required')
    if chronic_threshold is not None and (not isinstance(chronic_threshold,int) or isinstance(chronic_threshold,bool) or chronic_threshold<1):raise ValueError('positive chronic threshold required')
    included=[];excluded=[];seen=set()
    for i,row in enumerate(rows,2):
        po=row.get('po_number');promised=date.fromisoformat(row['promised_date']);actual=date.fromisoformat(row['actual_date']);cite=source+':row '+str(i)
        if not po or po in seen:raise ValueError('missing/duplicate historical PO identity')
        seen.add(po)
        if actual>asof or actual<asof-timedelta(days=window_days):excluded.append({'po_number':po,'citation':cite,'reason':'not realized in as-of window'});continue
        days=(actual-promised).days
        if 'days_late' in row and float(row['days_late'])!=days:raise ValueError('reported days_late disagrees with dates')
        included.append({'po_number':po,'date':row.get('date',row['promised_date']),'part_no':row.get('part_no',''),'promised_date':row['promised_date'],'actual_date':row['actual_date'],'days_late':days,'citation':cite})
    late=sum(x['days_late']>0 for x in included)
    result={'window_days':window_days,'as_of':as_of,'late_count':late,'on_time_pct':round(100*(len(included)-late)/len(included),3) if included else None,'prior_shipments':included,'excluded_records':excluded,'policy_status':'provided threshold' if chronic_threshold else 'chronic threshold unknown; confirmation required'}
    if chronic_threshold:result['chronic_pattern']=late>=chronic_threshold;result['chronic_threshold']=chronic_threshold
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--csv',required=True);ap.add_argument('--as-of',required=True);ap.add_argument('--window-days',required=True,type=int);ap.add_argument('--chronic-threshold',type=int);ap.add_argument('--out',required=True);a=ap.parse_args()
    check_outputs([a.out],[a.csv])
    with open(a.csv,encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    r=history(rows,a.as_of,a.window_days,a.chronic_threshold,Path(a.csv).name)
    write_outputs([(a.out,json.dumps(r,indent=2,allow_nan=False))],[a.csv]);return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,TypeError,KeyError,OSError,csv.Error) as e:
        print('BLOCKED: '+str(e),file=sys.stderr);sys.exit(2)
