#!/usr/bin/env python3
"""Usage: check_artifact_refs.py ROOT STATE_REL | --manifest MANIFEST_REL."""
import sys,json
from runtime import load,safe,evaluate,check_manifest,ContractError
if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[2]=='--manifest':
            m=check_manifest(sys.argv[1],sys.argv[3]);r={'valid':True,'run_id':m['run_id'],'result':m['result']}
        elif len(sys.argv)==3:r=evaluate(sys.argv[1],load(safe(sys.argv[1],sys.argv[2])))
        else:raise ContractError('usage: check_artifact_refs.py ROOT STATE_REL | ROOT --manifest MANIFEST_REL')
        print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['valid'] else 1)
    except (ContractError,OSError,ValueError) as e:print(json.dumps({'valid':False,'error':str(e)},ensure_ascii=False));sys.exit(2)
