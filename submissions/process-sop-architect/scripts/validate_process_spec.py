from __future__ import annotations
import argparse,json
from pathlib import Path

def validate(spec):
    errors=[];warnings=[]
    for f in ['process_name','purpose','trigger','roles','steps']: 
        if not spec.get(f):errors.append(f'Missing required field: {f}')
    def _objects(key):
        val=spec.get(key)
        if val is None:return []
        if not isinstance(val,list):
            errors.append(f"Field '{key}' must be a list of objects");return []
        result=[]
        for i,item in enumerate(val,start=1):
            if isinstance(item,dict):result.append(item)
            else:errors.append(f'{key}[{i}] must be an object')
        return result
    roles_list=_objects('roles');steps_list=_objects('steps');controls_list=_objects('controls')
    roles = {r.get('name') for r in roles_list}
    steps = {}
    for i, step in enumerate(steps_list, start=1):
        sid = step.get('id')
        if not sid or not str(sid).strip():
            errors.append(f'Step #{i}: missing nonblank id')
            continue
        if sid in steps:
            errors.append(f'Duplicate step id: {sid}')
            continue
        steps[sid] = step
    controls = {c.get('id') for c in controls_list}
    for sid,s in steps.items():
        if not s.get('name'):errors.append(f'{sid}: missing step name')
        if not s.get('owner'):errors.append(f'{sid}: missing owner')
        elif s.get('owner') not in roles:warnings.append(f"{sid}: owner '{s.get('owner')}' is not listed in roles")
        typ=s.get('type','task')
        if typ=='decision':
            for key in ['yes_next','no_next']:
                if not s.get(key):errors.append(f'{sid}: decision missing {key}')
                elif s.get(key) not in steps:errors.append(f"{sid}: {key} references unknown step {s.get(key)}")
        else:
            nxt=s.get('next')
            if nxt and nxt not in steps:errors.append(f'{sid}: next references unknown step {nxt}')
        for cid in (s.get('control_ids') or []):
            if cid not in controls:errors.append(f'{sid}: unknown control {cid}')
    for c in controls_list:
        for f in ['id','name','objective','owner','frequency','evidence']:
            if not c.get(f):warnings.append(f"Control {c.get('id','?')} missing {f}")
    if len(steps)>25:warnings.append('Process has more than 25 steps; consider subprocesses')
    return errors,warnings

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True,type=Path);a=p.parse_args();spec=json.loads(a.input.read_text(encoding='utf-8'));errors,warnings=validate(spec)
    for w in warnings:print('WARN:',w)
    if errors:
        for e in errors:print('ERROR:',e)
        raise SystemExit(2)
    print('Validation passed')
if __name__=='__main__':main()
