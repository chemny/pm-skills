"""Lifecycle v2 policy. References and scope checks, not human-approval authentication."""
from pathlib import Path
import hashlib

ACTIVITIES={'documentation','research','prototype','experiment','implementation','test','delivery'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def file_ref(root,obj):
    if not isinstance(obj,dict):raise ValueError('missing-reference')
    rel=obj.get('path');h=obj.get('sha256')
    if not isinstance(rel,str) or not rel or Path(rel).is_absolute():raise ValueError('invalid-reference-path')
    p=(Path(root)/rel).resolve()
    if not p.is_relative_to(Path(root).resolve()) or not p.is_file():raise ValueError('missing-or-external-reference')
    if digest(p)!=h:raise ValueError('reference-hash-mismatch')
    if not p.read_bytes().strip():raise ValueError('empty-reference')
    return p

def policy_reasons(root,state,task):
    reasons=[];ctx=state.get('context',{})
    if not isinstance(ctx,dict):return ['missing-execution-context']
    for key,allowed in [('entry',{'new','change','bug','single'}),('interface',{'ui','cli','api','service','skill'}),('mode',{'discussion','planning','execution'})]:
        if ctx.get(key) not in allowed:reasons.append('invalid-context:'+key)
    if not isinstance(ctx.get('paused'),bool):reasons.append('missing-pause-state')
    if ctx.get('paused') is not False and task.get('status')!='done':reasons.append('user-paused')
    scope=ctx.get('scope');activity=task.get('activity')
    if not isinstance(scope,str) or not scope.strip() or task.get('scope')!=scope:reasons.append('task-scope-mismatch')
    if activity not in ACTIVITIES:reasons.append('missing-or-invalid-activity')
    if ctx.get('mode')=='discussion' and task.get('status')!='done':reasons.append('discussion-does-not-authorize-writing')
    if ctx.get('mode')=='planning' and task.get('status')!='done' and activity not in {'documentation','research','prototype'}:reasons.append('planning-does-not-authorize-execution')
    if task.get('entry') not in (None,ctx.get('entry')):reasons.append('cannot-reclassify-project-as-small-task')
    try:file_ref(root,ctx.get('authority'))
    except ValueError as e:reasons.append('authority:'+str(e))
    for collection in ['artifacts','reviews']:
        rows=state.get(collection)
        if not isinstance(rows,list) or not all(isinstance(x,dict) and isinstance(x.get('id'),str) for x in rows):reasons.append('invalid-registry:'+collection);continue
        if len({x['id'] for x in rows})!=len(rows):reasons.append('duplicate-registry-id:'+collection)
    reviews={x.get('id'):x for x in state.get('reviews',[]) if isinstance(x,dict)}
    artifacts={x.get('id'):x for x in state.get('artifacts',[]) if isinstance(x,dict)}
    def review(ident,objects,kind=None,user=False):
        r=reviews.get(ident,{})
        if r.get('status')!='approved' or r.get('scope')!=scope or (kind and r.get('kind')!=kind) or (user and r.get('actor')!='user'):raise ValueError('review-not-approved-for-scope')
        file_ref(root,r.get('source'))
        if not objects or any(r.get('objects',{}).get(a['id'])!=a.get('sha256') for a in objects):raise ValueError('review-object-mismatch')
        return r
    def artifact(ident):
        a=artifacts.get(ident,{})
        if a.get('scope')!=scope:raise ValueError('artifact-scope-mismatch')
        p=file_ref(root,a);text=p.read_text(encoding='utf-8')
        if not text.strip() or any(t in text for t in ['PROJECT_ID','DRAFT_REVISION','填写当前范围的具体内容','未填实不得执行']):raise ValueError('placeholder-artifact')
        if a.get('section') and a['section'] not in text:raise ValueError('missing-artifact-section')
        if any(other.get('path')==a.get('path') and other.get('id')!=a.get('id') for other in artifacts.values()) and not a.get('section'):raise ValueError('merged-artifact-without-section')
        review(a.get('review_ref'),[a])
        return a
    refs=task.get('artifact_refs',[])
    if not isinstance(refs,list) or not all(isinstance(x,str) for x in refs):reasons.append('invalid-artifact-refs');refs=[]
    valid=[]
    for ident in refs:
        try:valid.append(artifact(ident))
        except (ValueError,OSError,UnicodeError) as e:reasons.append('artifact:'+str(ident)+':'+str(e))
    kinds={x.get('kind') for x in valid}
    if activity=='implementation':
        if ctx.get('entry')=='new':
            needed={'project','requirements','experience','architecture','plan','validation'}
            for kind in sorted(needed-kinds):reasons.append('missing-deliverable:'+kind)
            selected=[a for a in valid if a.get('kind') in {'requirements','experience','prototype','examples'}]
            if ctx.get('interface')=='ui' and 'prototype' not in kinds:
                try:
                    w=review(task.get('waiver_ref'),selected,'waiver',True)
                    if 'examples' not in kinds or not all(w.get(x) for x in ['reason','risk','alternative']):raise ValueError('waiver-needs-alternative-and-risk')
                except ValueError as e:reasons.append('missing-core-prototype-or-approved-waiver:'+str(e))
            elif ctx.get('interface')!='ui' and 'examples' not in kinds:reasons.append('missing-deliverable:examples')
            try:review(task.get('product_review_ref'),selected,'product',True)
            except ValueError as e:reasons.append('product-review:'+str(e))
            if task.get('conditions',{}).get('design',{}).get('applicable') is not True:reasons.append('new-product-design-cannot-be-na')
        else:
            baselines=task.get('baseline_refs',[])
            if not isinstance(baselines,list) or not baselines:reasons.append('missing-effective-change-baseline')
            for ident in baselines if isinstance(baselines,list) else []:
                try:artifact(ident)
                except (ValueError,OSError) as e:reasons.append('baseline:'+str(e))
    if activity=='experiment':
        exp=task.get('experiment',{})
        if not isinstance(exp,dict):exp={}
        for key in ['problem','necessity','method','sample','expected','pass_criteria','fail_criteria','stop','data_scope','return_to_product']:
            if not isinstance(exp.get(key),str) or not exp[key].strip():reasons.append('experiment-missing:'+key)
        for key in ['max_attempts','timeout_seconds']:
            if type(exp.get(key)) is not int or exp[key]<=0:reasons.append('experiment-invalid:'+key)
        effects=exp.get('effects',{})
        ds={d.get('id'):d for d in state.get('decisions',[]) if isinstance(d,dict)}
        for key in ['capture','upload','install','pay','permissions','configuration']:
            value=effects.get(key) if isinstance(effects,dict) else None
            if value is False:continue
            d=ds.get(exp.get('effect_refs',{}).get(key),{})
            try:
                if value is not True or d.get('status')!='approved' or d.get('kind')!='operation' or d.get('operation')!=key or d.get('scope')!=scope or d.get('id') not in task.get('decision_ids',[]):raise ValueError('effect-without-scoped-permission')
                file_ref(root,d.get('source'))
            except ValueError:reasons.append('experiment-effect-needs-specific-review:'+key)
        d=ds.get(exp.get('authorization_id'),{})
        if d.get('status')!='approved' or d.get('kind')!='experiment' or d.get('scope')!=scope or exp.get('authorization_id') not in task.get('decision_ids',[]):reasons.append('experiment-without-explicit-scope-authorization')
        try:file_ref(root,d.get('source'))
        except ValueError as e:reasons.append('experiment-authorization:'+str(e))
    if activity in {'documentation','implementation','experiment','prototype','test','delivery'}:
        paths=task.get('write_paths')
        if not isinstance(paths,list) or not paths:reasons.append('missing-write-scope')
        for rel in paths if isinstance(paths,list) else []:
            if not isinstance(rel,str) or not rel or Path(rel).is_absolute():reasons.append('invalid-write-scope');continue
            p=(Path(root)/rel).resolve()
            if p==Path(root).resolve() or not p.is_relative_to(Path(root).resolve()):reasons.append('external-or-root-write-scope')
    if task.get('status')!='done' and activity in {'experiment','implementation','prototype','test','delivery'}:
        budget=task.get('experiment',{}).get('max_attempts') if activity=='experiment' else task.get('max_attempts')
        if type(budget) is not int or budget<1:reasons.append('missing-attempt-budget')
        elif task.get('status') not in {'running','verifying'} and len(task.get('runs',[]))>=budget:reasons.append('attempt-budget-exhausted')
    return reasons

def audit(root,before,after,task):
    root=Path(root).resolve();paths=task.get('write_paths',[])
    allowed=[(root/p).resolve() for p in paths if isinstance(p,str)]
    changed=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
    outside=[]
    for rel in changed:
        p=(root/rel).resolve()
        if not p.is_relative_to(root) or not any(p==a or p.is_relative_to(a) for a in allowed):outside.append(rel)
    return {'changed':changed,'out_of_scope':outside,'result':'failed' if outside else 'passed','limitations':'Declared project file changes only; not a sandbox and not complete observation of external systems or unlogged tools.'}
