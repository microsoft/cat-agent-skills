#!/usr/bin/env python3
"""Sync the canonical shared/ assets into every skills/<name>/ folder.
Cowork installs each skill folder on its own, so each skill must carry its own copy.
  --sync   copy shared/{config,contracts,references,demo-data} into every skill (skill-specific files untouched)
  --check  exit 1 if any skill copy differs from shared/ (run before packaging)
"""
import sys,os,shutil,filecmp
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED=os.path.join(ROOT,"shared"); SKILLS=os.path.join(ROOT,"skills")
DIRS=["config","contracts","references","demo-data"]
def files(base):
    for dp,_,fs in os.walk(base):
        for f in fs: yield os.path.relpath(os.path.join(dp,f),base)
def sync():
    for s in sorted(os.listdir(SKILLS)):
        for d in DIRS:
            src=os.path.join(SHARED,d)
            if os.path.isdir(src): shutil.copytree(src,os.path.join(SKILLS,s,d),dirs_exist_ok=True)
    print("synced shared/ into",len(os.listdir(SKILLS)),"skills")
def check():
    bad=[]
    for s in sorted(os.listdir(SKILLS)):
        for d in DIRS:
            src=os.path.join(SHARED,d)
            if not os.path.isdir(src): continue
            for rel in files(src):
                dst=os.path.join(SKILLS,s,d,rel)
                if not os.path.exists(dst) or not filecmp.cmp(os.path.join(src,rel),dst,shallow=False): bad.append(f"skills/{s}/{d}/{rel}")
    if bad:
        print("DRIFT:"); [print(" ",b) for b in bad]; sys.exit(1)
    print("OK: all skill copies match shared/")
if __name__=="__main__":
    a=sys.argv[1:] or ["--check"]
    sync() if "--sync" in a else check()
