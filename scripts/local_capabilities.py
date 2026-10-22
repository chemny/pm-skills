"""Bounded local discovery and declared compatibility; never runs or installs a candidate."""
from pathlib import Path
import argparse,fnmatch,json,os,stat

def discover(roots,patterns,max_depth=6,max_entries=5000):
    if not roots or not patterns or max_depth<0 or max_entries<1:
        raise ValueError('explicit roots/patterns and positive scan budget required')
    receipts=[];candidates=[];seen=0
    for item in roots:
        root=Path(item).absolute()
        receipt={'root':str(root),'status':'covered','entries':0,'errors':[],'limits':[]}
        receipts.append(receipt)
        if root.is_symlink():
            receipt.update(status='partial');receipt['limits'].append('root-symlink-not-followed');continue
        if not root.exists():receipt['status']='missing';continue
        if not root.is_dir():
            receipt.update(status='partial');receipt['limits'].append('not-a-directory');continue
        pending=[(root,0)]
        while pending:
            folder,depth=pending.pop()
            try:
                # No recursive glob and no sorted materialization of a large directory.
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if seen>=max_entries:
                            receipt['limits'].append('entry-budget');receipt['status']='partial';pending.clear();break
                        seen+=1;receipt['entries']+=1
                        path=Path(entry.path);rel=str(path.relative_to(root))
                        try:
                            if entry.is_symlink():
                                receipt['limits'].append('symlink-not-followed:'+rel);receipt['status']='partial';continue
                            if entry.is_file(follow_symlinks=False) and any(fnmatch.fnmatch(entry.name,p) or fnmatch.fnmatch(rel,p) for p in patterns):
                                mode=entry.stat(follow_symlinks=False).st_mode
                                candidates.append({'path':str(path),'root':str(root),'relative_path':rel,'bytes':entry.stat(follow_symlinks=False).st_size,'executable_bit':bool(mode & (stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)),'verification':'discovered-not-invoked'})
                            elif entry.is_dir(follow_symlinks=False):
                                if depth>=max_depth:
                                    receipt['limits'].append('depth:'+rel);receipt['status']='partial'
                                else:pending.append((path,depth+1))
                        except OSError as exc:
                            receipt['errors'].append({'path':rel,'error':type(exc).__name__});receipt['status']='partial'
            except OSError as exc:
                receipt['errors'].append({'path':str(folder),'error':type(exc).__name__});receipt['status']='partial'
        receipt['limits']=sorted(set(receipt['limits']))
    return {'candidates':candidates,'search':receipts,'entries_examined':seen,'patterns':patterns,
            'conclusion':'candidates-found' if candidates else 'not-found-within-declared-scope',
            'limitations':'File discovery only; no global absence, runtime compatibility, prior success, or product recommendation is established. No symlinks followed, processes executed, downloads or writes performed.'}

def assess_compatibility(model,runtime,input_format):
    """Compare documented declarations. Matching declarations never imply a successful run."""
    reasons=[]
    fields=['family','format']+[f for f in ['quantization','revision'] if model.get(f) is not None]
    for field in fields:
        value=model.get(field);allowed=runtime.get('supported_'+field)
        if not value or not isinstance(allowed,list) or not allowed:
            reasons.append('unknown:'+field)
        elif value not in allowed:reasons.append('unsupported:'+field)
    if not input_format or not runtime.get('input_formats'):reasons.append('unknown:input-format')
    elif input_format not in runtime['input_formats']:reasons.append('unsupported:input-format')
    if not runtime.get('support_source'):reasons.append('missing-runtime-support-source')
    return {'status':'blocked' if reasons else 'declared-compatible-not-run','reasons':reasons,
            'quality':'not-assessed','download_required':'not-established'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',action='append',required=True)
    parser.add_argument('--name',action='append',required=True,help='filename or relative path glob')
    parser.add_argument('--max-depth',type=int,default=6)
    parser.add_argument('--max-entries',type=int,default=5000)
    args=parser.parse_args()
    print(json.dumps(discover(args.root,args.name,args.max_depth,args.max_entries),ensure_ascii=False,indent=2))
