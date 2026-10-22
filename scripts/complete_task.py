#!/usr/bin/env python3
"""Usage: complete_task.py ROOT STATE_REL TASK_ID REASON MANIFEST_REL [MANIFEST_REL ...].

Reuses existing evidence without running a command. Caller reviews actual assertions first.
"""
import sys,json
from runtime import complete_task,ContractError

if __name__=='__main__':
    try:
        if len(sys.argv)<6:raise ContractError(__doc__)
        state=complete_task(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[5:],sys.argv[4])
        task=next(t for t in state['tasks'] if t['id']==sys.argv[3])
        print(json.dumps({'task_id':task['id'],'status':task['status'],'evidence_refs':task['evidence_refs']},ensure_ascii=False))
    except (ContractError,OSError,ValueError) as exc:
        print(json.dumps({'error':str(exc)},ensure_ascii=False));sys.exit(1)
