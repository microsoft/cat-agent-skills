"""Trusted first-party evaluator: validate the bundled schema subset without importing candidate code.
Fail closed on unsupported validation keywords. This is not a general JSON Schema implementation.
"""
import json,re,math,pathlib,sys
VALIDATION={'type','required','properties','items','enum','const','minimum','maximum','exclusiveMinimum','pattern'}
ANNOTATIONS={'$schema','$id','title','description','default'}
def validate(value,schema,path='$'):
 unknown=set(schema)-VALIDATION-ANNOTATIONS
 if unknown: raise ValueError(path+': unsupported schema keywords '+str(sorted(unknown)))
 types=schema.get('type');types=[types] if isinstance(types,str) else types
 def istype(t):
  return {'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),'boolean':isinstance(value,bool),'null':value is None,'number':isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value),'integer':isinstance(value,int) and not isinstance(value,bool)}.get(t,False)
 if types and not any(istype(t) for t in types):raise ValueError(path+': expected '+str(types))
 if 'enum' in schema and value not in schema['enum']:raise ValueError(path+': value outside enum')
 if 'const' in schema and value!=schema['const']:raise ValueError(path+': wrong constant')
 if isinstance(value,(int,float)) and not isinstance(value,bool):
  if not math.isfinite(value):raise ValueError(path+': nonfinite number')
  for key,bad in [('minimum',lambda x:value<x),('maximum',lambda x:value>x),('exclusiveMinimum',lambda x:value<=x)]:
   if key in schema and bad(schema[key]):raise ValueError(path+': violates '+key)
 if isinstance(value,str) and 'pattern' in schema and not re.search(schema['pattern'],value):raise ValueError(path+': pattern mismatch')
 if isinstance(value,dict):
  for k in schema.get('required',[]):
   if k not in value:raise ValueError(path+'.'+k+': required')
  for k,v in value.items():
   if k in schema.get('properties',{}):validate(v,schema['properties'][k],path+'.'+k)
 if isinstance(value,list) and 'items' in schema:
  for i,v in enumerate(value):validate(v,schema['items'],path+f'[{i}]')
def validate_payload(payload,schema_path=None):
 if schema_path is None:schema_path=pathlib.Path(__file__).resolve().parents[1]/'contracts/mfg.maintenance-triage.v1.json'
 validate(payload,json.loads(pathlib.Path(schema_path).read_text()))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--instance',required=True);ap.add_argument('--schema',required=True);a=ap.parse_args()
 try:validate_payload(json.loads(pathlib.Path(a.instance).read_text()),a.schema)
 except (ValueError,TypeError,KeyError,OSError) as e:print('BLOCKED: '+str(e),file=sys.stderr);sys.exit(2)
 print('PASS: bundled contract subset validated (not general JSON Schema)')
