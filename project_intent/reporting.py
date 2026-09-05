"""Immutable local report outbox, distinct from provider organizational truth."""
import hashlib
import json
import re
from pathlib import Path
from contextlib import contextmanager
import fcntl
import os

from .model import utcnow


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def directory_for(entry):
    return Path(entry.get('report_directory', str(Path(entry['enrollment_directory']).parent / (Path(entry['enrollment_directory']).name+'-reports'))))


@contextmanager
def locked(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(directory/'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        yield


def validate_packet(packet):
    if not isinstance(packet,dict) or set(packet)-{'summary','readiness','evidence','assertions','next_step'}:
        raise ValueError('Unsupported report fields')
    if not isinstance(packet.get('summary'),str) or not packet['summary'].strip():raise ValueError('Report summary required')
    if not isinstance(packet.get('readiness',{}),dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in packet.get('readiness',{}).items()):raise ValueError('Readiness must be named string assertions')
    if not isinstance(packet.get('next_step',''),str):raise ValueError('Next step must be a string')
    if not isinstance(packet.get('evidence',[]),list) or not isinstance(packet.get('assertions',[]),list):raise ValueError('Evidence and assertions must be lists')
    for e in packet.get('evidence',[]):
        if not isinstance(e,dict) or set(e)!={'ref','sha256'} or not isinstance(e['ref'],str) or not re.fullmatch('[0-9a-f]{64}',e['sha256']):raise ValueError('Evidence requires ref and sha256; hashes are reported, not independently verified')
    for a in packet.get('assertions',[]):
        if not isinstance(a,dict) or any(not isinstance(a.get(k),str) or not a[k] for k in ('invariant','revision','subject')):raise ValueError('Assertion requires invariant, revision and subject')
    if len(json.dumps(packet).encode())>65536:raise ValueError('Report exceeds 64 KiB')
    return packet


def submit(directory,scope,workstream,session,packet,queue=False):
    from .runtime import read_json,write_json
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',session or ''):raise ValueError('Explicit safe own session required')
    payload={'scope':scope,'workstream':workstream,'session':session,'packet':validate_packet(packet)}
    report_id=digest(payload);directory=Path(directory)
    with locked(directory):
        file=directory/(report_id+'.json')
        if file.is_symlink():raise ValueError('Symlink report refused')
        if file.exists():
            old=read_json(file)
            if old['payload']!=payload:raise ValueError('Immutable report collision')
        else:write_json(file,{'id':report_id,'created_at':utcnow().isoformat(),'payload':payload})
        state_file=directory/(report_id+'.status')
        status=read_json(state_file) if state_file.exists() else {'state':'local'}
        if queue and status['state']=='local':status={'state':'pending'}
        write_json(state_file,status)
    return {'id':report_id,**status,'meaning':'Local report assertion; provider publication and independent verification are separate'}


def read_report(directory,scope,report_id):
    from .runtime import read_json
    if not re.fullmatch('[0-9a-f]{64}',report_id or ''):raise ValueError('Invalid report id')
    file=Path(directory)/(report_id+'.json')
    if file.is_symlink():raise ValueError('Symlink report refused')
    r=read_json(file);p=r['payload']
    if digest(p)!=r['id'] or report_id!=r['id'] or p['scope']!=scope:raise ValueError('Report integrity or scope mismatch')
    validate_packet(p['packet'])
    status_file=file.with_suffix('.status')
    if status_file.is_symlink():raise ValueError('Symlink receipt refused')
    status=read_json(status_file) if status_file.exists() else {'state':'local'}
    return {**r,'publication':status,'meaning':'Worker-reported local evidence, not provider readiness or verified conformance'}


def reports(directory,scope,workstream=None):
    result=[];directory=Path(directory)
    files=list(directory.glob('*.json'))
    if len(files)>500:raise ValueError('Local report listing exceeds 500 records; exact report publication remains available')
    for file in sorted(files):
        try:
            r=read_report(directory,scope,file.stem)
            if workstream and r['payload']['workstream']!=workstream:continue
            result.append(r)
        except (OSError,ValueError,KeyError,TypeError):continue
    return sorted(result,key=lambda x:x['created_at'],reverse=True)


def publish(directory,scope,report_id,provider):
    from .runtime import read_json,write_json
    if not re.fullmatch('[0-9a-f]{64}',report_id or ''):raise ValueError('Invalid report id')
    with locked(directory):
        report=read_report(directory,scope,report_id);status=report['publication'];state_file=Path(directory)/(report_id+'.status')
        if status['state']=='published':return status
        if status['state']=='local':raise ValueError('Report is local only; submit it before publication')
        marker='project-intent-report:'+report_id
        issue=provider.resolve(report['payload']['workstream'])
        existing=provider.find_comment(issue['native_id'],marker)
        if existing:
            status={'state':'published','native_comment':existing['id'],'reconciled':True}
        elif status['state']=='uncertain':
            return status  # Never blindly resend after ambiguous transport/crash.
        else:
            write_json(state_file,{'state':'uncertain','reason':'Publication attempt started; reconcile provider marker before retry'})
            try:
                comment=provider.comment(issue['native_id'],marker+'\n\nWorker report; not independent verification.\n'+json.dumps(report['payload'],indent=2))
                status={'state':'published','native_comment':comment['id'],'published_at':utcnow().isoformat()}
            except (OSError,ValueError,KeyError):
                return read_json(state_file)
        write_json(state_file,status)
        return status
