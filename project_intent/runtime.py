"""Independent cache and observation reader. No Git/product subprocess calls."""
import copy
import json
import os
from pathlib import Path
import tempfile
import threading

from .model import validate_snapshot, valid_presence
from .provider import adapter, MAX_BYTES
from .activity import codex_activity
from .enrollment import read_registrations


def read_json(path):
    with Path(path).open('rb') as stream: raw=stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError('File exceeds read bound')
    return json.loads(raw)


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
            stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


class Store:
    def __init__(self,config):
        self.config=config
        self.lock=threading.RLock()
        self.states={}
        for scope in config['scopes']:
            if scope['id'] in self.states: raise ValueError('Duplicate scope')
            snapshot=None
            try:snapshot=validate_snapshot(read_json(scope['cache']))
            except (OSError,ValueError,KeyError,TypeError):pass
            if snapshot and snapshot.get('scope_id') != scope['id']:
                snapshot=None
            self.states[scope['id']]={'id':scope['id'],'label':scope['label'],'snapshot':snapshot,'provider_status':'not-yet-observed'}

    def refresh(self):
        for scope in self.config['scopes']:
            try:
                snapshot=adapter(scope['provider']).snapshot()
                if snapshot.get('scope_id',scope['id']) != scope['id']:
                    raise ValueError('Snapshot scope binding differs')
                snapshot['scope_id']=scope['id']
                write_json(scope['cache'],snapshot)
                with self.lock:
                    self.states[scope['id']].update(snapshot=snapshot,provider_status='offline' if scope['provider']['kind']=='snapshot' else 'live')
            except (OSError,ValueError,KeyError,TypeError,StopIteration,AttributeError):
                with self.lock:self.states[scope['id']]['provider_status']='unavailable'

    def view(self):
        with self.lock: states=copy.deepcopy(self.states)
        for scope in self.config['scopes']:
            sources=scope.get('presence_sources',[]);present=[]; failures=0
            from .reporting import reports
            try:
                states[scope['id']]['local_reports']=reports(scope['report_directory'],scope['id']) if scope.get('report_directory') else []
                states[scope['id']]['report_coverage']='configured-local-list' if scope.get('report_directory') else 'not-configured'
            except (OSError,ValueError):
                states[scope['id']]['local_reports']=[]
                states[scope['id']]['report_coverage']='unavailable-or-over-limit; exact report publication remains available'
            activity={}
            for binding in scope.get('activity_sources',[])[:16]:
                # Explicit one-source-per-workstream v0, never guess attribution.
                key=binding['workstream']
                if key in activity:
                    activity[key]={'status':'ambiguous-binding','points':[]}
                else:
                    activity[key]=codex_activity(binding)
            known={r['id'] for r in (states[scope['id']]['snapshot'] or {}).get('records',[]) if r['kind']=='workstream'}
            enrolled_activity={}
            for source in scope.get('enrollment_sources',[])[:16]:
                enrolled,failed=read_registrations(source,scope['id'],known)
                failures+=failed
                for record,binding in enrolled:
                    present.append(record)
                    if binding:
                        metric=codex_activity(binding)
                        enrolled_activity.setdefault(record['workstream'],[]).append(metric)
            for key,metrics in enrolled_activity.items():
                # Separate per-worker measurements; never sum mismatched reporting intervals.
                if len({m['session'] for m in metrics})!=len(metrics):
                    activity[key]={'status':'ambiguous-binding','points':[]}
                elif len(metrics)==1:
                    activity[key]=metrics[0]
                else:
                    last=max((m.get('last_report_at') or 0 for m in metrics),default=0)
                    activity[key]={'status':'recent' if any(m['status']=='recent' for m in metrics) else 'not-observed',
                                   'last_report_at':last or None,'points':[],'sessions':metrics,
                                   'meaning':'Separate session rates, not an aggregate throughput.'}
            states[scope['id']]['activity']=activity
            for source in sources:
                path=Path(source)
                try:
                    if not path.is_dir():raise OSError('Observation source unavailable')
                    files=sorted(path.glob('*.json'))
                    if len(files)>500:failures+=1
                    for file in files[:500]:
                        if file.is_symlink():failures+=1;continue
                        try:
                            record=read_json(file)
                            if not valid_presence(record):raise ValueError('Invalid lease')
                            present.append(record)
                        except (OSError,ValueError):failures+=1
                except OSError:failures+=1
            # Presence directories are explicit cooperative feeds, never authoritative occupancy.
            states[scope['id']].update(presence=present,execution={
                'status':('not-connected' if not sources and not scope.get('enrollment_sources') else 'unavailable' if failures and not present else 'partial' if failures else 'observed'),
                'meaning':'Cooperative local presence only; not fleet availability or safe environment occupancy'})
        return list(states.values())
