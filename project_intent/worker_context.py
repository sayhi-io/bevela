"""Worker-side checkout observation and local discovery; no assignment authority."""
import os
import re
from pathlib import Path, PurePosixPath
import socket
import subprocess

from .model import project, utcnow, date, validate_snapshot
from .enrollment import read_registrations


def checkout_identity(directory):
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env['GIT_OPTIONAL_LOCKS']='0'
    def git(*args,optional=False):
        r=subprocess.run(['git','-C',str(directory),*args],env=env,capture_output=True,text=True,timeout=5)
        if r.returncode and not optional:raise ValueError('Checkout must be an accessible Git worktree; specify --checkout')
        return r.stdout.strip() if r.returncode==0 else None
    root=git('rev-parse','--show-toplevel')
    return {'host':socket.gethostname(),'root':str(Path(root).resolve()),
            'repository_common_dir':str(Path(git('rev-parse','--path-format=absolute','--git-common-dir')).resolve()),
            'branch':git('symbolic-ref','--short','-q','HEAD',optional=True),
            'head':git('rev-parse','--verify','HEAD',optional=True),
            'observed_at':utcnow().isoformat()}


def relative_paths(values):
    paths=[]
    for value in values:
        if not value or '\\' in value or any(c in value for c in '*?[]'):
            raise ValueError('Use explicit checkout-relative files/directories, not globs')
        p=PurePosixPath(value)
        if p.is_absolute() or '..' in p.parts:raise ValueError('Touch/avoid paths must remain checkout-relative')
        paths.append(str(p))
    return sorted(set(paths))


def same_repository(a,b):
    return bool(a and b and a.get('host')==b.get('host') and a.get('repository_common_dir')==b.get('repository_common_dir'))


def path_overlap(left,right):
    a,b=PurePosixPath(left),PurePosixPath(right)
    return a==b or a in b.parents or b in a.parents


def local_states(entries,read_json):
    states=[];errors=[]
    for scope,entry in entries.items():
        try:
            snapshot=validate_snapshot(read_json(entry['snapshot']))
            if snapshot['scope_id']!=scope:raise ValueError('Scope mismatch')
            known={r['id'] for r in snapshot['records'] if r['kind']=='workstream'}
            rows,failed=read_registrations({'directory':entry['enrollment_directory']},scope,known,include_telemetry=False)
            states.append({'id':scope,'label':scope,'snapshot':snapshot,'provider_status':'offline',
                           'presence':[r for r,b in rows],'execution':{'status':'partial' if failed else 'observed',
                           'meaning':'Local cooperative registration leases; no provider request or telemetry log read'}})
            from .reporting import directory_for,reports
            try:
                states[-1]['local_reports']=reports(directory_for(entry),scope)
                states[-1]['report_coverage']='configured-local-list'
            except (OSError,ValueError):
                states[-1]['local_reports']=[]
                states[-1]['report_coverage']='unavailable-or-over-limit; exact report publication remains available'
        except (OSError,ValueError,KeyError,TypeError):errors.append({'scope':scope,'status':'snapshot-unavailable'})
    return states,errors


def resolve_assignment(states,reference,scope=None):
    matches=[]
    for state in states:
        if scope and state['id']!=scope:continue
        for work in state['snapshot']['records']:
            if work['kind']=='workstream' and reference in (work['id'],work.get('provider_identifier'),state['id']+':'+work['id']):
                matches.append((state,work))
    if len(matches)!=1:raise ValueError('Assignment absent or ambiguous; run discover, then select an exact scope and alias/native ID')
    return matches[0]


def discovery(states,checkout=None,query=''):
    view=project(states,[s['id'] for s in states])
    tokens=list(dict.fromkeys(re.findall(r'[\w]+(?:[-/][\w]+)*',query.casefold())))
    candidates=[]
    for work in view['workstreams']:
        text=' '.join(str(work.get(k) or '') for k in ('id','provider_identifier','statement','scope','source_checkout','delegate_name')).casefold()
        matched=[t for t in tokens if t in text]
        if tokens and not matched:continue
        reference=work.get('source_checkout')
        match=bool(checkout and reference and str(Path(reference).resolve())==checkout['root'])
        candidates.append({k:work.get(k) for k in ('key','id','scope_id','provider_identifier','statement','state','provider_lifecycle','delegate_name','assignee_name','source_checkout','scope','avoid')})
        candidates[-1].update(checkout_reference_match=match,workers=work['workers'],
            query_match={'matched_terms':matched,'unmatched_terms':[t for t in tokens if t not in matched],
                         'matched_count':len(matched),'query_term_count':len(tokens)})
    candidates.sort(key=lambda w:(-w['query_match']['matched_count'],not w['checkout_reference_match'],w['key']))
    return {'checkout':checkout,'candidates':candidates,'sources':view['scopes'],
            'matching':'Ranked partial keyword matches, then checkout reference and stable key. Query match is not assignment confidence. An empty query lists the scoped cached inventory.',
            'instruction':'Candidates are not assignments. Inspect with start; confirm against your user task and declared delegate. Do not take over mismatched ownership. Use enroll only after inspection.',
            'coverage':'Last-known enrolled provider subset plus live local leases. Missing candidates are not proof no PM issue exists. No PM mutation or provider credential required.'}


def nearby_workers(states,checkout,touching,seams,scope=None):
    nearby=[];now=utcnow()
    for state in states:
        for worker in state.get('presence',[]):
            if worker['status']!='active' or date(worker['expires_at'])<=now:continue
            other=worker.get('checkout');same=same_repository(checkout,other)
            shared=sorted(set(seams)&set(worker.get('touching_seams',[])+worker.get('approaching',[]))) if state['id']==scope else []
            paths=sorted({p for p in touching for q in worker.get('touching_paths',[]) if same and path_overlap(p,q)})
            if same or shared:
                nearby.append({'scope':state['id'],'workstream':worker['workstream'],'session':worker['session'],
                    'working':worker.get('working',''),'heartbeat_at':worker.get('heartbeat_at'),
                    'checkout':other,'access':worker.get('access','unspecified'),'touching_paths':worker.get('touching_paths',[]),
                    'touching_seams':worker.get('touching_seams',[]),'approaching':worker.get('approaching',[]),
                    'avoid_paths':worker.get('avoid_paths',[]),'avoid':worker.get('avoid',[]),
                    'overlapping_paths':paths,'shared_seams':shared,'expires_at':worker['expires_at']})
    return nearby


def integration_context(state, selected, checkout, touching=(), seams=(), session=None):
    """Scoped declared peer intent, including unenrolled tasks and ended leases.

    No source inspection, completion inference, messaging or repair arbitration.
    """
    boundaries=set(selected['boundaries']) | set(seams)
    now=utcnow();related=[];workers=[]
    for record in state['snapshot']['records']:
        shared=sorted(boundaries & set(record['boundaries']))
        if record['kind']!='workstream' or record['id']==selected['id'] or not shared:
            continue
        related.append({key:record.get(key) for key in
                        ('id','statement','scope','acceptance','avoid','revision','state','source_checkout')})
        related[-1]['shared_seams']=shared
    related_ids={r['id'] for r in related}
    for worker in state.get('presence',[]):
        if worker['scope']!=state['id'] or worker['session']==session:
            continue
        other=worker.get('checkout');same=same_repository(checkout,other)
        shared=sorted(boundaries & set(worker.get('touching_seams',[])+worker.get('approaching',[])))
        paths=sorted({p for p in touching for q in worker.get('touching_paths',[])
                      if same and path_overlap(p,q)})
        if not (shared or paths or worker['workstream'] in related_ids or
                (same and worker['workstream']==selected['id'])):
            continue
        heartbeat=date(worker['heartbeat_at'])
        observation=('future-timestamp' if heartbeat>now else 'released' if worker['status']=='inactive'
                     else 'expired' if date(worker['expires_at'])<=now else 'active-lease')
        workers.append({key:worker.get(key) for key in
                        ('session','workstream','working','status','heartbeat_at','expires_at',
                         'checkout','access','touching_paths','touching_seams','approaching','avoid_paths','avoid')})
        workers[-1].update(observation=observation,shared_seams=shared,overlapping_paths=paths,
                          same_checkout=bool(same and checkout['root']==other['root']))
    return {'scope':state['id'],'related_work':sorted(related,key=lambda r:r['id']),
            'last_known_workers':sorted(workers,key=lambda r:r['session']),
            'observed_at':now.isoformat(),'snapshot_source':state['snapshot']['source'],
            'presence_coverage':state.get('execution',{}).get('status','unavailable'),
            'meaning':'Peer tasks and working summaries are declarations, not detected changes or verified completion. '
                      'Released/expired registrations remain last-known context, not active workers. '
                      'No registration does not mean no related work; other checkouts are not edit targets.'}
