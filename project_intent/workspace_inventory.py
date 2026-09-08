"""Bounded repository-root observation, distinct from durable scope enrollment."""
from datetime import datetime, timezone
import os
from pathlib import Path


def observe(config, principal, projection, selected=None):
    """Operator-only inventory; never discover code, credentials, or other sessions."""
    if principal.get('workspace_inventory') is not True:
        return None
    settings=config.get('workspace_inventory')
    if not settings:
        return {'status':'not-configured','repositories':[]}
    if not isinstance(settings,dict) or not isinstance(settings.get('root'),str) or not isinstance(settings.get('scope_by_repository',{}),dict):
        return {'status':'unavailable','repositories':[]}
    root=Path(settings['root'])
    if not root.is_absolute() or root.is_symlink():
        return {'status':'unavailable','repositories':[]}
    allowed=set(principal.get('scopes',[]))
    scopes={s['id']:s for s in projection['scopes']}
    mappings=settings.get('scope_by_repository',{})
    result={'status':'observed','observed_at':datetime.now(timezone.utc).isoformat(),
            'repositories':[], 'meaning':'Immediate canonical repository directories only. Not a source-content scan, PM project inventory, or discovery of unregistered agents.'}
    try:
        entries=[]
        with os.scandir(root) as source:
            for entry in source:
                if len(entries)>=200:
                    result['status']='partial-limit';break
                entries.append(entry)
        for entry in sorted(entries,key=lambda e:e.name):
            if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):continue
            path=root/entry.name
            if not (path/'.git').exists():continue
            scope=mappings.get(entry.name)
            # Explicit mappings to forbidden scopes never reveal repository names.
            if scope and scope not in allowed:continue
            if selected and scope!=selected:continue
            source=scopes.get(scope)
            work=[w for w in projection['workstreams'] if w['scope_id']==scope] if source else []
            result['repositories'].append({'repository':entry.name,'checkout':str(path),
                'scope':scope,'intent_status':'configured' if source else 'scope-not-connected' if scope else 'not-mapped',
                'provider_status':source['provider_status'] if source else 'not-connected',
                'execution_status':source['execution']['status'] if source else 'not-connected',
                'enrolled_workstreams':len(work) if source else None,
                'meaning':'Scope-level observations; not all work or sessions in this repository.' if source else 'No scope mapping/connection in this service; remote PM state and worker activity unknown.'})
    except OSError:
        result['status']='unavailable';result['repositories']=[]
    result['repository_count']=len(result['repositories'])
    result['connected_count']=sum(r['intent_status']=='configured' for r in result['repositories'])
    return result
