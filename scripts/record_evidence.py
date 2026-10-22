#!/usr/bin/env python3
"""Usage: record_evidence.py ROOT REQUEST_REL. Executes argv after caller authorization."""
import sys,json
from runtime import load,safe,record,ContractError
if __name__=='__main__':
    try:
        if len(sys.argv)!=3:raise ContractError('usage: record_evidence.py ROOT REQUEST_REL')
        m=record(sys.argv[1],load(safe(sys.argv[1],sys.argv[2])));print(json.dumps(m,ensure_ascii=False,indent=2));sys.exit(0 if m['result']=='passed' else 1)
    except (ContractError,OSError,ValueError) as e:print(json.dumps({'error':str(e)},ensure_ascii=False));sys.exit(2)
