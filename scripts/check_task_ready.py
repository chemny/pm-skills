#!/usr/bin/env python3
"""Read-only: check_task_ready.py ROOT STATE_REL TASK_ID [REQUEST_REL]."""
import sys,json
from runtime import load,safe,check_task,ContractError
if __name__=='__main__':
    try:
        if len(sys.argv) not in (4,5):raise ContractError('usage: check_task_ready.py ROOT STATE_REL TASK_ID [REQUEST_REL]')
        command=load(safe(sys.argv[1],sys.argv[4])).get('command') if len(sys.argv)==5 else None
        result=check_task(sys.argv[1],load(safe(sys.argv[1],sys.argv[2])),sys.argv[3],command)
        print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['can_start'] else 1)
    except (ContractError,OSError,ValueError,TypeError) as e:print(json.dumps({'can_start':False,'error':str(e)},ensure_ascii=False));sys.exit(2)
