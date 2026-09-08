"""Cooperative local enrollment, not provider assignment or execution authority."""
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import stat

from .model import utcnow, valid_presence, date

SAFE_SESSION = re.compile(r'[A-Za-z0-9_-]{1,100}')


def telemetry_path(path, session, roots=None):
    path=Path(path)
    if path.is_symlink():raise ValueError('Telemetry symlinks are not supported')
    resolved=path.resolve(strict=True)
    if roots is not None and not any(resolved.is_relative_to(Path(root).resolve()) for root in roots):
        raise ValueError('Telemetry path outside configured roots')
    # Nonblocking + descriptor type check also avoids FIFO/device hangs and leaf races.
    fd=os.open(resolved, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('Regular telemetry file required')
        header=json.loads(stream.readline(1024*1024))
    if header.get('type')!='session_meta' or header.get('payload',{}).get('id')!=session:
        raise ValueError('Telemetry session identity does not match')
    return str(resolved)


def find_codex_session(root,session):
    if not SAFE_SESSION.fullmatch(session):raise ValueError('Safe session identifier required')
    root=Path(root).resolve(strict=True)
    # Names only: never inspect other workers' log contents to infer ownership.
    candidates=list(root.glob('????/??/??/rollout-*-'+session+'.jsonl'))
    if len(candidates)!=1:raise ValueError('Expected one matching session file; supply --telemetry-file explicitly')
    return telemetry_path(candidates[0],session,[root])


def registration(snapshot,workstream,session,working,approaching,avoid,path=None,old=None,inactive=False,now=None):
    now=now or utcnow()
    if not SAFE_SESSION.fullmatch(session):raise ValueError('Safe session identifier required')
    if not any(r['id']==workstream and r['kind']=='workstream' for r in snapshot['records']):
        raise ValueError('Workstream absent from snapshot; enroll durable intent with its owner first')
    scope=snapshot['scope_id']
    if old and (old.get('scope'),old.get('workstream'),old.get('session'))!=(scope,workstream,session):
        raise ValueError('Session already bound elsewhere; use a separate session, do not overwrite ownership')
    prior=old.get('telemetry') if old else None
    if path and prior and prior.get('path')!=path:raise ValueError('Cannot silently replace session telemetry source')
    contiguous=old and old.get('status')=='active' and date(old['expires_at'])>now
    # Preserve attribution boundary while renewing; restart after a lapse excludes gap work.
    claimed=old['claimed_at'] if contiguous else now.isoformat()
    telemetry=({'kind':'codex-local-usage','path':path,'since':claimed} if path else dict(prior,since=claimed) if prior else None)
    return {'version':1,'scope':scope,'workstream':workstream,'session':session,
            'status':'inactive' if inactive else 'active','claimed_at':claimed,
            'heartbeat_at':now.isoformat(),'expires_at':(now+timedelta(hours=1)).isoformat(),
            'working':working,'approaching':approaching,'avoid':avoid,'telemetry':telemetry}


def read_registrations(source,scope,known,now=None,include_telemetry=True):
    now=now or utcnow();records=[];failures=0
    directory=Path(source['directory'])
    try:
        if not directory.is_dir():return [],1
        # scandir surfaces permission errors that glob can silently suppress.
        # An unreadable optional feed must not become an API authorization error.
        with os.scandir(directory) as entries:
            files=sorted(Path(entry.path) for entry in entries if entry.name.endswith('.json'))
    except OSError:
        return [],1
    if len(files)>128:failures+=1
    for file in files[:128]:
        try:
            if file.is_symlink() or not file.is_file():raise ValueError('Regular registration file required')
            fd=os.open(file,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
            with os.fdopen(fd,'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('Regular registration required')
                raw=stream.read(65537)
            if len(raw)>65536:raise ValueError('Registration too large')
            r=json.loads(raw)
            if r.get('version')!=1 or r.get('scope')!=scope or r.get('workstream') not in known or not valid_presence(r,now):
                raise ValueError('Invalid scope, assignment or lease')
            if not SAFE_SESSION.fullmatch(r['session']) or file.stem!=r['session']:raise ValueError('Session filename mismatch')
            if date(r['claimed_at'])>date(r['heartbeat_at']):raise ValueError('Invalid claim time')
            binding=None
            if include_telemetry and r.get('telemetry') and r['status']=='active' and date(r['expires_at'])>now:
                # Invalid telemetry should not hide valid worker presence.
                try:
                    t=r['telemetry']
                    if t['kind']!='codex-local-usage' or t['since']!=r['claimed_at']:raise ValueError('Invalid telemetry binding')
                    path=telemetry_path(t['path'],r['session'],source.get('telemetry_roots',[]))
                    binding={'kind':t['kind'],'session':r['session'],'path':path,'since':t['since']}
                except (OSError,ValueError,KeyError,TypeError,AttributeError):
                    failures+=1
                    binding={'kind':'unavailable','session':r['session']}
            records.append((r,binding))
        except (OSError,ValueError,KeyError,TypeError,AttributeError):failures+=1
    return records,failures
