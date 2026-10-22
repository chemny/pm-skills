#!/usr/bin/env python3
"""Usage: check_state.py PROJECT_ROOT STATE_RELATIVE_PATH. Never writes."""
import sys,json
from runtime import load,safe,evaluate,check_task,ContractError
if __name__=='__main__':
    try:
        if len(sys.argv)!=3:raise ContractError('usage: check_state.py PROJECT_ROOT STATE_RELATIVE_PATH')
        state=load(safe(sys.argv[1],sys.argv[2]));r=evaluate(sys.argv[1],state)
        r['execution_ready_tasks']=[t['id'] for t in state['tasks'] if check_task(sys.argv[1],state,t['id'])['can_start']]
        if state.get('schema_version')==1:
            r['legacy_candidate_tasks']=r['ready_tasks'];r['ready_tasks']=[];r['execution_requires_migration']=True
        print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['valid'] else 1)
    except (ContractError,OSError,ValueError) as e:print(json.dumps({'valid':False,'error':str(e)},ensure_ascii=False));sys.exit(2)
