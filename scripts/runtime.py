"""Deterministic lifecycle helpers. Structural checks are not human approval proof."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile,datetime,shutil,importlib.util,fcntl

STATUSES={'planned','ready','running','verifying','blocked','awaiting-decision','done','cancelled'}
CONDITIONS={'inputs','decisions','design','dependencies','environment','tools','authority','verification'}
KINDS={'static','simulated','prototype','runtime','review'}
RESULTS={'passed','failed','blocked','not-run'}
COMPLETION_POLICY=2
class ContractError(ValueError):pass

def atomic_state_write(path, text):
    """Replace a complete state file; an interrupted write retains the old state."""
    path=Path(path)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:
            handle.write(text);handle.flush();os.fsync(handle.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ContractError('duplicate-key: '+str(k))
        d[k]=v
    return d

def load(path):
    text=Path(path).read_text(encoding='utf-8')
    try:return json.loads(text,object_pairs_hook=unique_pairs)
    except json.JSONDecodeError:
        try:import yaml
        except ImportError:raise ContractError('YAML parser unavailable; use JSON syntax (valid YAML) or provide PyYAML explicitly')
        class Loader(yaml.SafeLoader):pass
        def mapping(loader,node,deep=False):
            return unique_pairs([(loader.construct_object(k,deep=deep),loader.construct_object(v,deep=deep)) for k,v in node.value])
        Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)
        try:return yaml.load(text,Loader=Loader)
        except yaml.YAMLError as e:raise ContractError('invalid-document: '+str(e).splitlines()[0]) from None

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def safe(root,rel,exists=True):
    root=Path(root).resolve()
    if not isinstance(rel,str) or not rel or Path(rel).is_absolute():raise ContractError('invalid-relative-path: '+str(rel))
    target=(root/rel).resolve()
    if not target.is_relative_to(root) or target==root:raise ContractError('path-outside-root: '+rel)
    # Internal symlinks are resolved; links out of root always fail above.
    if exists and not target.is_file():raise ContractError('missing-file: '+rel)
    return target

def check_object(root,obj):
    if not isinstance(obj,dict) or not isinstance(obj.get('files'),dict) or not obj['files']:raise ContractError('invalid-object-files')
    for rel,h in obj['files'].items():
        if not isinstance(h,str) or not re.fullmatch('[a-f0-9]{64}',h):raise ContractError('invalid-sha256: '+str(rel))
        if sha(safe(root,rel))!=h:raise ContractError('object-hash-mismatch: '+rel)
    # Other explicit object attributes, e.g. configuration, remain identity fields.
    return obj

def check_manifest(root,rel,expected=None):
    p=safe(root,rel);m=load(p)
    if not isinstance(m,dict) or type(m.get('schema_version')) is not int or m.get('schema_version')!=1:raise ContractError('invalid-evidence-schema')
    for k in ['run_id','environment','method','kind','result','object','outputs']:
        if k not in m:raise ContractError('missing-evidence-field: '+k)
    if m['kind'] not in KINDS or m['result'] not in RESULTS:raise ContractError('invalid-evidence-kind-or-result')
    if not m['run_id'] or not m['method'] or not isinstance(m['environment'],dict):raise ContractError('invalid-evidence-metadata')
    check_object(root,m['object'])
    if expected is not None and m['object']!=expected:raise ContractError('evidence-object-mismatch')
    if not isinstance(m['outputs'],list) or (m['result']=='passed' and not m['outputs']):raise ContractError('missing-evidence-outputs')
    for output in m['outputs']:
        if not isinstance(output,dict) or not {'path','sha256'}<=output.keys():raise ContractError('invalid-output-index')
        if sha(safe(root,output['path']))!=output['sha256']:raise ContractError('output-hash-mismatch: '+output['path'])
    return m

def command_expectation(task,command):
    """Only a task's predeclared exact-command negative case can change the default."""
    rows=task.get('command_expectations',[])
    if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
        raise ContractError('invalid-command-expectations')
    matches=[row for row in rows if row.get('command')==command]
    if len(matches)>1:raise ContractError('duplicate-command-expectation')
    if not matches:return None
    row=matches[0]
    if (type(row.get('returncode')) is not int or not 1<=row['returncode']<=255
            or not any(isinstance(row.get(k),str) and row[k].strip() for k in ['stdout_contains','stderr_contains'])
            or any(k in row and (not isinstance(row[k],str) or not row[k].strip()) for k in ['stdout_contains','stderr_contains'])):
        raise ContractError('negative-case-needs-exact-code-and-output-assertion')
    return row

def command_assertion(root,manifest,expectation):
    if expectation is None:return manifest.get('returncode')==0
    if manifest.get('returncode')!=expectation['returncode']:return False
    for key,name in [('stdout_contains','stdout.txt'),('stderr_contains','stderr.txt')]:
        if key in expectation:
            path=safe(root,f"evidence/{manifest['run_id']}/outputs/{name}")
            if expectation[key] not in path.read_text(encoding='utf-8',errors='replace'):return False
    return True

def managed_completion_reasons(root,task):
    """Bind runtime completion to the actual task/attempt and captured process output.

    Historical observations can remain indexed, but cannot manufacture a preflight.
    This checks records, not human approval or the meaning of program assertions.
    """
    reasons=[];runtime_manifests=[]
    attempts=task.get('runs',[])
    if not isinstance(attempts,list) or any(not isinstance(r,dict) for r in attempts):
        reasons.append('invalid-attempt-records');attempts=[]
    for rel in task.get('evidence_refs',[]):
        try:m=check_manifest(root,rel,task.get('object'))
        except (ContractError,OSError):continue  # evaluate reports the detailed hash/reference error.
        if m['kind']!='runtime':continue
        runtime_manifests.append(m)
        runs=[r for r in attempts if r.get('run_id')==m['run_id']]
        pre=m.get('preflight');post=m.get('postflight');audit=m.get('scope_audit')
        pre=pre if isinstance(pre,dict) else {};post=post if isinstance(post,dict) else {};audit=audit if isinstance(audit,dict) else {}
        if (str(m.get('provenance','')).startswith('retrospective') or m.get('task_id')!=task['id']
                or m.get('scope')!=task.get('scope')
                or len(runs)!=1 or runs[0].get('status')!='passed'
                or not runs[0].get('state_digest')
                or pre.get('task_id')!=task['id'] or pre.get('can_start') is not True
                or pre.get('state_digest')!=runs[0].get('state_digest')):
            reasons.append('runtime-without-matching-managed-attempt:'+m['run_id'])
        if (audit.get('result')!='passed'
                or m.get('control_state_changed') is not False
                or post.get('task_id')!=task['id'] or post.get('can_start') is not True):
            reasons.append('runtime-execution-checks-not-passed:'+m['run_id'])
        if m.get('provenance')=='managed-command':
            output_paths={o['path'] for o in m['outputs']}
            if not {f"evidence/{m['run_id']}/outputs/{name}" for name in ['stdout.txt','stderr.txt']}<=output_paths:
                reasons.append('runtime-process-output-missing:'+m['run_id'])
            try:
                expectation=command_expectation(task,m.get('command'))
                if (m.get('command') not in task.get('commands',[]) or not command_assertion(root,m,expectation)
                        or (expectation is not None and (m.get('command_expectation')!=expectation
                            or len(runs)!=1 or runs[0].get('command_expectation')!=expectation))):
                    reasons.append('runtime-command-assertion-not-passed:'+m['run_id'])
                if expectation is not None:
                    snapshot=load(_policy().file_ref(root,pre.get('state_ref')))
                    old_task=next(t for t in snapshot['tasks'] if t['id']==task['id'])
                    original=check_task(root,snapshot,task['id'],m.get('command'))
                    if (not original['can_start'] or original['state_digest']!=pre.get('state_digest')
                            or command_expectation(old_task,m.get('command'))!=expectation):
                        reasons.append('negative-case-not-predeclared:'+m['run_id'])
            except (ContractError,OSError,ValueError,TypeError,StopIteration):reasons.append('runtime-command-assertion-invalid:'+m['run_id'])
        elif m.get('provenance')=='task-bound-host-tool':
            # Evidence contract only, not a new tool runner or a permission issuer.
            call=m.get('tool_call');receipt=m.get('receipt',{})
            if (not isinstance(call,dict) or not call or call not in task.get('tool_calls',[])
                    or not isinstance(receipt,dict) or not receipt.get('call_id')
                    or receipt.get('tool')!=call.get('tool') or not call.get('tool')
                    or m.get('execution_result')!='passed' or m.get('assertion_result')!='passed'
                    or not any(o.get('role')=='tool-response' for o in m['outputs'])):
                reasons.append('host-tool-receipt-or-assertion-missing:'+m['run_id'])
            try:
                ref=pre.get('state_ref');snapshot=load(_policy().file_ref(root,ref))
                actual=check_task(root,snapshot,task['id'])
                old_task=next(t for t in snapshot['tasks'] if t['id']==task['id'])
                budget=old_task.get('experiment',{}).get('max_attempts') if old_task.get('activity')=='experiment' else old_task.get('max_attempts')
                if (not actual['can_start'] or actual['state_digest']!=pre.get('state_digest')
                        or call not in old_task.get('tool_calls',[]) or old_task.get('scope')!=task.get('scope')
                        or type(budget) is not int or len(old_task.get('runs',[]))>=budget):
                    raise ContractError('host-tool-preflight-mismatch')
            except (ContractError,OSError,ValueError,TypeError,StopIteration,RecursionError):
                reasons.append('host-tool-preflight-not-verified:'+m['run_id'])
        else:reasons.append('unsupported-runtime-provenance:'+m['run_id'])
    if not runtime_manifests:reasons.append('managed-runtime-evidence-required')
    # Failed/interrupted history stays visible; it needs reviewed disposition, not deletion.
    resolutions=task.get('attempt_resolutions',{})
    if not isinstance(resolutions,dict):resolutions={};reasons.append('invalid-attempt-resolutions')
    for run in attempts:
        if run.get('status')=='passed':continue
        resolution=resolutions.get(run.get('run_id'),{})
        if (not isinstance(resolution,dict) or resolution.get('status') not in {'resolved','superseded','not-applicable'}
                or not isinstance(resolution.get('reason'),str) or not resolution['reason'].strip()
                or not isinstance(resolution.get('evidence_refs'),list) or not resolution['evidence_refs']
                or any(ref not in task.get('evidence_refs',[]) for ref in resolution['evidence_refs'])):
            reasons.append('unresolved-attempt:'+str(run.get('run_id')))
    return reasons

def evaluate(root,state):
    diagnostics=[];ready=[];blocked={}
    def error(code,task=None):diagnostics.append({'code':code,'task':task})
    if not isinstance(state,dict) or type(state.get('schema_version')) is not int or state.get('schema_version') not in (1,2):return {'valid':False,'ready_tasks':[],'blocked_tasks':{},'diagnostics':[{'code':'unsupported-state-schema','task':None}]}
    for k in ['project','work_item']:
        if not isinstance(state.get(k),str) or not state[k].strip():error('invalid-'+k)
    tasks=state.get('tasks');inputs=state.get('inputs',[]);decisions=state.get('decisions',[])
    if not isinstance(tasks,list) or not isinstance(inputs,list) or not isinstance(decisions,list):
        return {'valid':False,'ready_tasks':[],'blocked_tasks':{},'diagnostics':[{'code':'invalid-collection-type','task':None}]}
    def index(rows,label):
        result={}
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id']:error('invalid-'+label+'-id');continue
            if row['id'] in result:error('duplicate-'+label+'-id: '+row['id'])
            result[row['id']]=row
        return result
    ti=index(tasks,'task');ii=index(inputs,'input');di=index(decisions,'decision')
    pending=[]
    for ident,d in di.items():
        if d.get('status') not in {'pending','approved','superseded','needs-recheck','rejected'}:error('invalid-decision-status: '+ident)
        if d.get('status') in {'pending','needs-recheck'}:pending.append(ident)
        if d.get('status')=='approved' and (not d.get('selected') or not d.get('approval_ref')):error('approved-decision-without-source: '+ident)
    if not isinstance(state.get('open_decisions'),list) or not all(isinstance(d,str) for d in state.get('open_decisions',[])) or sorted(state['open_decisions'])!=sorted(pending):error('open-decisions-inconsistent')
    for ident,i in ii.items():
        try:
            if i.get('status')!='approved':raise ContractError('input-not-approved: '+ident)
            if sha(safe(root,i.get('path')))!=i.get('sha256'):raise ContractError('input-hash-mismatch: '+ident)
        except (ContractError,OSError) as e:error(str(e))
    visiting=set();visited=set()
    def walk(ident):
        if ident in visiting:error('dependency-cycle: '+ident);return
        if ident in visited:return
        visiting.add(ident)
        deps=ti[ident].get('depends_on',[])
        if not isinstance(deps,list) or not all(isinstance(d,str) for d in deps):error('invalid-dependency-type',ident);deps=[]
        for dep in deps:
            if dep not in ti:error('missing-dependency: '+dep,ident)
            else:walk(dep)
        visiting.remove(ident);visited.add(ident)
    for ident in ti:walk(ident)
    for ident,t in ti.items():
        reasons=[]
        if t.get('status') not in STATUSES:error('invalid-task-status',ident)
        cond=t.get('conditions',{})
        if not isinstance(cond,dict):error('invalid-conditions-type',ident);cond={}
        if set(cond)-CONDITIONS:error('unknown-condition',ident)
        for key in sorted(CONDITIONS):
            c=cond.get(key)
            if not isinstance(c,dict):reasons.append('missing-condition:'+key);continue
            if not isinstance(c.get('applicable'),bool):error('invalid-applicability:'+key,ident);reasons.append('invalid-applicability:'+key);continue
            if not c['applicable']:
                if not isinstance(c.get('reason'),str) or not c['reason'].strip():reasons.append('not-applicable-without-reason:'+key)
            elif c.get('satisfied') is not True or not c.get('basis'):
                reasons.append('unsatisfied-condition:'+key)
        for key in ['input_ids','decision_ids','evidence_refs','required_evidence_kinds']:
            if not isinstance(t.get(key,[]),list) or not all(isinstance(v,str) for v in t.get(key,[])):error('invalid-list:'+key,ident);reasons.append('invalid-list:'+key)
        input_ids=[v for v in t.get('input_ids',[]) if isinstance(v,str)] if isinstance(t.get('input_ids',[]),list) else []
        for iid in input_ids:
            if iid not in ii:reasons.append('unknown-input:'+str(iid))
        c=cond.get('inputs',{})
        if isinstance(c,dict) and c.get('applicable') and not input_ids:reasons.append('missing-task-inputs')
        ds=[v for v in t.get('decision_ids',[]) if isinstance(v,str)] if isinstance(t.get('decision_ids',[]),list) else []
        for did in ds:
            if did not in di or di[did].get('status')!='approved' or not di[did].get('selected') or not di[did].get('approval_ref'):reasons.append('pending-decision:'+str(did))
        deps=t.get('depends_on',[]) if isinstance(t.get('depends_on',[]),list) else []
        for dep in deps:
            if dep not in ti or ti[dep].get('status')!='done':reasons.append('dependency-not-done:'+str(dep))
        if t.get('status')=='cancelled':reasons.append('task-cancelled')
        if t.get('status')=='done':
            try:check_object(root,t.get('object'))
            except (ContractError,OSError) as e:reasons.append(str(e))
            ev=t.get('evidence_refs',[])
            if not isinstance(ev,list) or not ev:reasons.append('done-without-evidence')
            kinds=set()
            for rel in [v for v in ev if isinstance(v,str)] if isinstance(ev,list) else []:
                try:
                    m=check_manifest(root,rel,t.get('object'));kinds.add(m['kind'])
                    if m['result']!='passed':reasons.append('evidence-not-passed:'+rel)
                except (ContractError,OSError) as e:reasons.append(str(e))
            required=t.get('required_evidence_kinds',[])
            if isinstance(required,list):
                if not all(isinstance(v,str) for v in required):required=[];error('invalid-required-evidence-kind',ident)
                if not set(required)<=KINDS:error('invalid-required-evidence-kind',ident)
                if not set(required)<=kinds:reasons.append('required-evidence-kind-missing')
        if state.get('schema_version')==2:
            try:reasons.extend(_policy().policy_reasons(root,state,t))
            except (TypeError,ValueError,KeyError,OSError) as e:reasons.append('invalid-v2-policy-data:'+str(e))
            if t.get('completion_policy') not in (None,1,COMPLETION_POLICY):reasons.append('unsupported-completion-policy')
            if t.get('status')=='done' and t.get('completion_policy')==COMPLETION_POLICY and (t.get('activity')=='experiment' or
                    (t.get('activity') in {'implementation','test'} and 'runtime' in t.get('required_evidence_kinds',[]))):
                reasons.extend(managed_completion_reasons(root,t))
        if reasons:
            blocked[ident]=reasons
            if t.get('status') in {'ready','running','verifying','done'}:
                for reason in reasons:error(reason,ident)
        elif t.get('status')!='done':ready.append(ident)
    # Per-task structural diagnostics must never leave an optimistic ready ID.
    for diagnostic in diagnostics:
        ident=diagnostic.get('task')
        if ident in ti:
            blocked.setdefault(ident,[]).append('invalid-task-state:'+diagnostic['code'])
            if ident in ready:ready.remove(ident)
    # A syntactic upstream 'done' is not sufficient if its evidence is invalid.
    changed=True
    while changed:
        changed=False
        for ident,t in ti.items():
            for dep in t.get('depends_on',[]) if isinstance(t.get('depends_on',[]),list) else []:
                if isinstance(dep,str) and dep in blocked and ident not in blocked:
                    blocked[ident]=['dependency-unverified:'+dep]
                    if ident in ready:ready.remove(ident)
                    if t.get('status') in {'ready','running','verifying','done'}:error('dependency-unverified:'+dep,ident)
                    changed=True
    # Global input/decision/graph inconsistency cannot produce optimistic ready.
    if any(d['task'] is None or d['code'].startswith(('dependency-cycle','missing-dependency')) for d in diagnostics):
        for ident in ready:blocked.setdefault(ident,[]).append('state-inconsistent')
        ready=[]
    legacy=[t['id'] for t in ti.values() if t.get('status')=='done' and t.get('completion_policy')!=COMPLETION_POLICY
            and (t.get('activity')=='experiment' or 'runtime' in t.get('required_evidence_kinds',[]))]
    return {'valid':not diagnostics,'ready_tasks':ready,'blocked_tasks':blocked,'diagnostics':diagnostics,
            'historical_completion_not_rechecked':legacy,
            'limitations':'Structural validation only; historical completion is not newly verified. Basis/approval references do not authenticate human decisions or prove semantic design quality.'}

def transition(root,state,task_id,new_status,reason):
    if new_status not in STATUSES or not isinstance(reason,str) or not reason.strip():raise ContractError('invalid-transition-or-reason')
    result=json.loads(json.dumps(state));task=next((t for t in result['tasks'] if t['id']==task_id),None)
    if task is None:raise ContractError('unknown-task')
    old=task['status']
    allowed={'planned':{'ready','blocked','awaiting-decision','cancelled'},'ready':{'running','blocked','awaiting-decision','cancelled'},'running':{'verifying','blocked','awaiting-decision','cancelled'},'verifying':{'done','running','blocked','cancelled'},'blocked':{'planned','ready','awaiting-decision','cancelled'},'awaiting-decision':{'planned','ready','blocked','cancelled'},'done':{'planned','blocked'},'cancelled':{'planned'}}
    if new_status not in allowed.get(old,set()):raise ContractError('illegal-transition:'+old+'->'+new_status)
    if new_status=='done' and not evaluate(root,state)['valid']:
        raise ContractError('completion-current-state-not-ready')
    task['status']=new_status
    if new_status in {'running','done'}:task['completion_policy']=COMPLETION_POLICY
    check=evaluate(root,result)
    if not check['valid']:raise ContractError('transition-invalid:'+json.dumps(check['diagnostics'],ensure_ascii=False))
    task.setdefault('history',[]).append({'from':old,'to':new_status,'reason':reason,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return result

SENSITIVE_OUTPUT_PATTERN=re.compile(r'TEST_SECRET_[A-Za-z0-9]+|(?:api[_-]?key|password|secret|token)\s*[=:]\s*[\w\-/+.]{4,}',re.I)
def clean(data):
    if SENSITIVE_OUTPUT_PATTERN.search(data.decode('utf-8',errors='replace')):raise ContractError('sensitive-output-refused: manually redact before ordinary evidence storage')
    return data

def sensitive_metadata(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if re.fullmatch(r'api[_-]?key|password|secret|token|authorization',str(key),re.I) and item not in ('',None,'<redacted>','[REDACTED]'):return True
            if sensitive_metadata(item):return True
    elif isinstance(value,list):return any(sensitive_metadata(v) for v in value)
    elif isinstance(value,str):return bool(SENSITIVE_OUTPUT_PATTERN.search(value))
    return False

def _record_command(root,request):
    root=Path(root).resolve()
    if not isinstance(request,dict):raise ContractError('invalid-record-request')
    if sensitive_metadata(request):raise ContractError('sensitive-request-metadata-refused')
    run_id=request.get('run_id','')
    if not isinstance(run_id,str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',run_id):raise ContractError('invalid-run-id')
    obj=check_object(root,request.get('object'))
    if request.get('kind') not in KINDS or not request.get('method') or not isinstance(request.get('environment'),dict):raise ContractError('invalid-record-metadata')
    command=request.get('command')
    if not isinstance(command,list) or not command or not all(isinstance(a,str) for a in command) or not command[0]:raise ContractError('command-must-be-argv-list')
    clean(json.dumps(command,ensure_ascii=False).encode())
    sources=request.get('output_paths',[])
    if not isinstance(sources,list):raise ContractError('invalid-output-paths')
    timeout=request.get('timeout_seconds',60)
    if not isinstance(timeout,(int,float)) or not 0<timeout<=3600:raise ContractError('invalid-timeout')
    final=safe(root,'evidence/'+run_id,exists=False)
    final.parent.mkdir(parents=True,exist_ok=True)
    request_hash=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if final.exists():
        old=check_manifest(root,str((final/'manifest.yaml').relative_to(root)),obj)
        if old.get('request_hash')==request_hash:return old
        raise ContractError('run-id-conflict')
    pending=safe(root,'evidence/.pending-'+run_id,exists=False)
    if pending.exists():raise ContractError('incomplete-run-must-be-inspected-before-retry')
    pending.mkdir();(pending/'journal.json').write_text(json.dumps({'run_id':run_id,'request_hash':request_hash,'state':'command-starting'}))
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p=subprocess.run(command,cwd=root,capture_output=True,timeout=timeout,shell=False)
        code=p.returncode;stdout=p.stdout;stderr=p.stderr;result='passed' if code==0 else 'failed'
    except subprocess.TimeoutExpired as e:
        code=None;stdout=e.stdout or b'';stderr=e.stderr or b'';result='failed'
    except OSError as e:
        code=None;stdout=b'';stderr=str(e).encode();result='blocked'
    (pending/'journal.json').write_text(json.dumps({'run_id':run_id,'request_hash':request_hash,'state':'command-finished','returncode':code}))
    outputs=[]
    # Capture actual sanitized process output before validating additional artifacts.
    # Missing output/object failure must retain the real failure diagnostics.
    blobs=[('stdout.txt',clean(stdout)),('stderr.txt',clean(stderr))]
    for name,data in blobs:
        out=pending/'outputs'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    check_object(root,obj)
    for n,rel in enumerate(sources):blobs.append((f'{n}-{Path(rel).name}',clean(safe(root,rel).read_bytes())))
    for name,data in blobs:
        out=pending/'outputs'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
        outputs.append({'path':str((final/'outputs'/name).relative_to(root)),'sha256':sha(out),
                        'role':'process-stdout' if name=='stdout.txt' else 'process-stderr' if name=='stderr.txt' else 'copied-artifact'})
    m={'schema_version':1,'run_id':run_id,'object':obj,'environment':request['environment'],'method':request['method'],'kind':request['kind'],'result':result,'command':command,'returncode':code,'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request_hash':request_hash,'outputs':outputs,'limitations':'Actual command execution and indexed outputs only; caller must verify command authority and assertions. Exit zero alone is not product acceptance.'}
    (pending/'manifest.yaml').write_text(json.dumps(m,ensure_ascii=False,indent=2))
    pending.rename(final)
    return m


_POLICY=None
def _policy():
    global _POLICY
    if _POLICY is None:
        spec=importlib.util.spec_from_file_location('pm_task_policy',Path(__file__).with_name('task_policy.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);_POLICY=module
    return _POLICY

def check_task(root,state,task_id,command=None):
    """Fresh, read-only decision for one task. No persistent bearer permit."""
    report=evaluate(root,state);task=next((t for t in state.get('tasks',[]) if t.get('id')==task_id),None)
    reasons=list(report.get('blocked_tasks',{}).get(task_id,[]))
    if state.get('schema_version')!=2:reasons.append('legacy-read-only-migrate-before-execution')
    if not report['valid']:reasons.append('state-inconsistent')
    if task is None:reasons.append('unknown-task')
    else:
        if task.get('status') not in {'planned','ready','running'}:reasons.append('task-not-startable')
        activity=task.get('activity');budget=task.get('experiment',{}).get('max_attempts') if activity=='experiment' else task.get('max_attempts')
        if command is not None:
            if command not in task.get('commands',[]):reasons.append('command-outside-approved-task')
            if type(budget) is not int or len(task.get('runs',[]))>=budget:reasons.append('attempt-budget-exhausted')
            # Deliberately conservative: managed research only permits basic read/version argv.
            if activity=='research' and command and not ((len(command)==2 and command[1] in {'--version','-version'}) or Path(command[0]).name in {'cat','rg','ls','pwd'}):reasons.append('research-command-needs-experiment-classification')
    snapshot=hashlib.sha256(json.dumps(state,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'structure_valid':report['valid'],'task_id':task_id,'can_start':not reasons,'blocked_reasons':sorted(set(reasons)),'state_digest':snapshot,'limitations':'Reference/scope checks only. Caller verifies actual approval and design quality; not a host-wide tool sandbox.'}

def snapshot_files(root):
    root=Path(root).resolve()
    return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and not p.is_symlink()}

def audit_changes(root,state,task_id,before,after):
    task=next((t for t in state.get('tasks',[]) if t.get('id')==task_id),None)
    if task is None:raise ContractError('unknown-task')
    return _policy().audit(root,before,after,task)

def record(root,request):
    """Managed execution: state/task binding, fresh check, exact argv, budget and audit."""
    root=Path(root).resolve()
    if not isinstance(request,dict) or not request.get('state_path') or not request.get('task_id'):raise ContractError('managed-record-requires-state-path-and-task-id')
    state_path=safe(root,request['state_path']);task_id=request['task_id'];command=request.get('command')
    if not isinstance(command,list) or not command or not all(isinstance(a,str) for a in command) or not command[0]:raise ContractError('command-must-be-argv-list')
    if isinstance(request.get('run_id'),str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',request['run_id']):
        previous=root/'evidence'/request['run_id']/'manifest.yaml'
        if previous.is_file():
            old=check_manifest(root,str(previous.relative_to(root)),request.get('object'))
            rh=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            if old.get('request_hash')!=rh:raise ContractError('run-id-conflict')
            return old
    initial=check_task(root,load(state_path),task_id,command)
    if not initial['can_start']:raise ContractError('task-not-ready:'+json.dumps(initial['blocked_reasons'],ensure_ascii=False))
    if request.get('kind') not in KINDS or not request.get('method') or not isinstance(request.get('environment'),dict):raise ContractError('invalid-record-metadata')
    outputs=request.get('output_paths',[])
    if not isinstance(outputs,list):raise ContractError('invalid-output-paths')
    for rel in outputs:safe(root,rel,exists=False)
    # Lock is a coordination measure for this API; external tools can still bypass it.
    lock=state_path.parent/'.execution.lock'
    with lock.open('a+') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        state=load(state_path)
        run_id=request.get('run_id','')
        if not isinstance(run_id,str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',run_id):raise ContractError('invalid-run-id')
        prior=root/'evidence'/run_id/'manifest.yaml'
        if prior.is_file():
            old=check_manifest(root,str(prior.relative_to(root)),request.get('object'))
            rh=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            if old.get('request_hash')!=rh:raise ContractError('run-id-conflict')
            return old  # Read-only idempotent retrieval, no new attempt.
        decision=check_task(root,state,task_id,command)
        if not decision['can_start']:raise ContractError('task-not-ready:'+json.dumps(decision['blocked_reasons'],ensure_ascii=False))
        task=next(t for t in state['tasks'] if t['id']==task_id)
        expectation=command_expectation(task,command)
        preflight_snapshot=json.dumps(state,ensure_ascii=False,indent=2)+'\n'
        timeout=request.get('timeout_seconds',60);limit=task.get('experiment',{}).get('timeout_seconds') if task.get('activity')=='experiment' else task.get('timeout_seconds',60)
        if not isinstance(timeout,(int,float)) or not isinstance(limit,(int,float)) or not 0<timeout<=limit:raise ContractError('timeout-outside-task-budget')
        check_object(root,request.get('object'))
        if sensitive_metadata(request):raise ContractError('sensitive-request-metadata-refused')
        if (root/'evidence'/('.pending-'+run_id)).exists():raise ContractError('incomplete-run-must-be-inspected-before-retry')
        for status in (['ready','running'] if task['status']=='planned' else ['running'] if task['status']=='ready' else []):state=transition(root,state,task_id,status,'Managed execution fresh preflight')
        task=next(t for t in state['tasks'] if t['id']==task_id)
        task.setdefault('runs',[]).append({'run_id':run_id,'state_digest':decision['state_digest'],'status':'reserved','command_expectation':expectation})
        atomic_state_write(state_path,json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        before=snapshot_files(root);control_hash=sha(state_path);control_changed=False
        try:
            manifest=_record_command(root,request)
            if expectation is not None:
                rel=f'evidence/{run_id}/outputs/preflight-state.json'
                captured=safe(root,rel,exists=False);captured.write_text(preflight_snapshot)
                decision['state_ref']={'path':rel,'sha256':sha(captured)}
                manifest['outputs'].append({**decision['state_ref'],'role':'preflight-state'})
            manifest['execution_result']=manifest['result']
            manifest['command_expectation']=expectation
            if expectation is not None:
                matched=command_assertion(root,manifest,expectation)
                manifest['assertion_result']='passed' if matched else 'failed'
                manifest['result']=manifest['assertion_result']
            after=snapshot_files(root);audit=audit_changes(root,state,task_id,before,after)
            control_changed=sha(state_path)!=control_hash
            postflight=check_task(root,state,task_id)
            control_changed=control_changed or not state_path.is_file() or sha(state_path)!=control_hash
            manifest.update(postflight=postflight,control_state_changed=control_changed)
            manifest.update(task_id=task_id,activity=task['activity'],preflight=decision,scope=task['scope'],scope_audit=audit,provenance='managed-command')
            if audit['result']!='passed' or control_changed or not postflight['can_start']:manifest['result']='failed'
            # Experimental success never claims product approval or product acceptance.
            manifest['product_acceptance']='not-asserted'
            (root/'evidence'/run_id/'manifest.yaml').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
            if control_changed:raise ContractError('control-state-changed-during-command: inspect actual state before recovery')
            task['runs'][-1]['status']=manifest['result']
            task['runs'][-1]['evidence_ref']='evidence/'+run_id+'/manifest.yaml'
            if manifest['result']!='passed':task['status']='blocked'
            atomic_state_write(state_path,json.dumps(state,ensure_ascii=False,indent=2)+'\n')
            return manifest
        except Exception:
            control_changed=not state_path.is_file() or sha(state_path)!=control_hash
            if not control_changed:
                task['runs'][-1]['status']='incomplete';task['status']='blocked';atomic_state_write(state_path,json.dumps(state,ensure_ascii=False,indent=2)+'\n')
            raise

def complete_task(root,state_path,task_id,manifest_refs,reason):
    """Close a reviewed task using existing evidence; never execute or re-run a command."""
    root=Path(root).resolve();path=safe(root,state_path)
    if not isinstance(manifest_refs,list) or not manifest_refs or not all(isinstance(x,str) for x in manifest_refs):
        raise ContractError('completion-requires-explicit-evidence-refs')
    with (path.parent/'.execution.lock').open('a+') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        state=load(path);task=next((t for t in state.get('tasks',[]) if t.get('id')==task_id),None)
        if task is None or task.get('status') not in {'running','verifying'}:raise ContractError('task-not-awaiting-completion')
        manifests=[check_manifest(root,ref) for ref in manifest_refs]
        obj=manifests[0]['object']
        if any(m['object']!=obj for m in manifests):raise ContractError('completion-object-mismatch')
        historical=task.setdefault('history_evidence_refs',[])
        for ref in task.get('evidence_refs',[]):
            if ref not in manifest_refs and ref not in historical:historical.append(ref)
        task['object']=obj;task['evidence_refs']=manifest_refs
        if task['status']=='running':state=transition(root,state,task_id,'verifying',reason)
        state=transition(root,state,task_id,'done',reason)
        # No partial state update on any validation failure above.
        atomic_state_write(path,json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        return state


def plan_impact(state, changed_input_ids=(), changed_task_ids=()):
    """Read-only affected dependency closure; never approves or modifies scope."""
    changed_inputs=set(changed_input_ids);affected=set(changed_task_ids)
    for task in state.get('tasks',[]):
        if changed_inputs.intersection(task.get('input_ids',[])):affected.add(task['id'])
    progress=True
    while progress:
        progress=False
        for task in state.get('tasks',[]):
            if affected.intersection(task.get('depends_on',[])) and task['id'] not in affected:
                affected.add(task['id']);progress=True
    return sorted(affected)


def inspect_recovery(root,state):
    """Inspect actual journals and objects before suggesting next steps; no writes."""
    root=Path(root).resolve();pending=[]
    evidence=root/'evidence'
    if evidence.is_symlink() and not evidence.resolve().is_relative_to(root):raise ContractError('evidence-root-outside-project')
    if evidence.is_dir():
        for path in sorted(evidence.glob('.pending-*')):
            journal=path/'journal.json'
            safe(root,str(journal.relative_to(root)))
            pending.append({'path':str(path.relative_to(root)),'journal':load(journal)})
    validation=evaluate(root,state)
    return {'pending_runs':pending,'validation':validation,'next':'inspect-actual-side-effects-first' if pending else 'reconcile-actual-state' if not validation['valid'] else 'select-ready-task','writes_performed':False}


def select_parallel(root,state):
    """Select non-overlapping ready write scopes; does not launch agents/tools."""
    validation=evaluate(root,state);selected=[];deferred={};claimed=[]
    for task in state.get('tasks',[]):
        ident=task['id']
        if ident not in validation['ready_tasks']:continue
        if task.get('interfaces_stable') is not True:
            deferred[ident]='shared-interfaces-not-confirmed-stable';continue
        paths=task.get('write_paths')
        if not isinstance(paths,list) or not all(isinstance(p,str) for p in paths):
            deferred[ident]='missing-write-scope';continue
        resolved=[safe(root,p,exists=False) for p in paths]
        conflict=next((owner for path in resolved for other,owner in claimed if path==other or path.is_relative_to(other) or other.is_relative_to(path)),None)
        if conflict:deferred[ident]='write-conflict-with:'+conflict;continue
        selected.append(ident);claimed.extend((p,ident) for p in resolved)
    return {'selected':selected,'deferred':deferred,'launches_performed':False,'limitations':'Declared boundaries only; actual tools and authorization still govern execution.'}


def retry_allowed(attempts,limit,previous_failure,current_failure,new_evidence=False):
    """Bounded decision helper, never retries or alters permission itself."""
    if not isinstance(attempts,int) or not isinstance(limit,int) or attempts<0 or limit<1:raise ContractError('invalid-retry-budget')
    return attempts<limit and (attempts==0 or new_evidence is True or previous_failure!=current_failure)
