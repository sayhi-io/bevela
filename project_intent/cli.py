"""Service, explicit scoped export, and standalone offline orientation."""
import argparse
import json
from pathlib import Path
import re
import os
import fcntl
from datetime import timedelta

from .model import project, utcnow, validate_snapshot, date
from .runtime import Store, read_json, write_json
from .server import serve
from .enrollment import registration, telemetry_path, find_codex_session, SAFE_SESSION
from .worker_context import checkout_identity, relative_paths, local_states, resolve_assignment, discovery, nearby_workers


def markdown(snapshot):
    lines=['# Project Intent — '+snapshot.get('scope_id','selected scope'),'','> Last-known provider snapshot; not remote authority.',
           '> Captured: '+snapshot['source']['captured_at'],'',snapshot['mission'],'']
    for r in sorted(snapshot['records'],key=lambda r:r['id']):
        lines += ['## '+r['id'],'',r['statement'],'','- State: '+r['state'],'- Revision: '+r['revision']]
        if r['kind']=='workstream':
            lines += ['- Scope: '+r['scope'],'- Readiness: '+json.dumps(r.get('readiness',{}),sort_keys=True),'- Must prove:']
            lines += ['  - '+a for a in r['acceptance']]
            if r.get('handoff_summary'):lines += ['- Handoff: '+r['handoff_summary']]
        lines += ['']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['serve','export','discover','onboard','start','presence','enroll','report','report-status','publish-report','provider-list','reconcile','session-attach','session-continue'])
    from .session_connector import add_arguments
    add_arguments(p)
    p.add_argument('--input',help='JSON report or confirmed reconciliation packet')
    p.add_argument('--submit',action='store_true',help='Queue local report for operator publication')
    p.add_argument('--report-id')
    p.add_argument('--config');p.add_argument('--port',type=int,default=8290)
    p.add_argument('--scope');p.add_argument('--output');p.add_argument('--snapshot')
    p.add_argument('--workstream');p.add_argument('--directory');p.add_argument('--session')
    p.add_argument('--working',default='');p.add_argument('--approaching',action='append',default=[])
    p.add_argument('--avoid',action='append',default=[]);p.add_argument('--inactive',action='store_true')
    p.add_argument('--telemetry-file',help='Explicit own-session Codex rollout file')
    p.add_argument('--codex',action='store_true',help='Use CODEX_THREAD_ID and locate only its matching log filename')
    p.add_argument('--worker-config',default=os.environ.get('PROJECT_INTENT_WORKER_CONFIG'),help='Credential-free local scope/snapshot/enrollment-directory map')
    p.add_argument('--query',default='',help='Filter discovery by task words')
    p.add_argument('--checkout',help='Actual execution checkout; default current directory')
    p.add_argument('--access',choices=['inspect','edit'],help='Declared intent, not an authorization grant')
    p.add_argument('--touching-path',action='append',default=None,help='Explicit checkout-relative file or directory')
    p.add_argument('--touching-seam',action='append',default=None,help='Opaque architectural boundary currently touched')
    p.add_argument('--avoid-path',action='append',default=None)
    args=p.parse_args()
    if args.command in ('provider-list','reconcile','publish-report'):
        from .provider_write import configured,reconcile
        from .reporting import publish
        if not args.config or not args.scope:p.error('--config and --scope required for operator command')
        try:
            cfg=read_json(args.config);entry,provider=configured(cfg,args.scope)
            if args.command=='provider-list':out=provider.inventory()
            elif args.command=='reconcile':
                if not args.input:p.error('--input required')
                out=reconcile(provider,args.scope,read_json(args.input),cfg['operator']['journal_directory'])
            else:
                out=publish(entry['report_directory'],args.scope,args.report_id,provider)
            print(json.dumps(out,indent=2));return
        except (OSError,ValueError,KeyError,TypeError) as exc:p.error(str(exc))
    if args.command=='serve':
        if not args.config:p.error('--config required')
        return serve(read_json(args.config),args.port)
    if args.command=='export':
        if not all((args.config,args.scope,args.output)):p.error('--config --scope --output required')
        store=Store(read_json(args.config));store.refresh()
        state=next((s for s in store.view() if s['id']==args.scope),None)
        if not state or not state['snapshot']:p.error('Scope has no usable snapshot')
        snapshot=state['snapshot'];directory=Path(args.output)
        write_json(directory/'snapshot.json',snapshot)
        (directory/'PROJECT.md').write_text(markdown(snapshot))
        print('Exported selected scope only; provider status '+state['provider_status'])
        return
    entries={};states=[];source_errors=[]
    if args.worker_config:
        try:entries=read_json(args.worker_config)['scopes']
        except (OSError,ValueError,KeyError,TypeError):
            if not args.snapshot:p.error('Local worker scope map unavailable; supply an explicit snapshot instead')
        if args.scope:
            if args.scope not in entries:p.error('Scope unavailable in local worker configuration')
            entries={args.scope:entries[args.scope]}
        states,source_errors=local_states(entries,read_json)
    if args.command in ('discover','onboard'):
        try:checkout=checkout_identity(args.checkout or Path.cwd())
        except (ValueError,OSError):checkout=None
        result=discovery(states,checkout,args.query);result['source_errors']=source_errors
        if args.command=='onboard':
            response={'discovery':result,
                      'contract':'Discovery and orientation are read-only. Candidates are not assignments; enrollment remains an explicit worker action.'}
            if not args.workstream:
                response['next_step']='Select an exact scope and alias/native ID, then rerun onboard with --scope and --workstream.'
                response['enrollment_required']='After inspecting the selected orientation, run enroll with explicit access, paths, seams and working summary.'
                print(json.dumps(response,indent=2));return
            try:
                state,selected=resolve_assignment(states,args.workstream,args.scope)
                selected_scope=state['id'];view=project([state],[selected_scope])
                work=next(w for w in view['workstreams'] if w['id']==selected['id'])
                response['orientation']={'scope':view['scopes'][0],'assignment':work,
                    'checkout':checkout,
                    'nearby_workers':nearby_workers([state],checkout,[],work['boundaries'],selected_scope),
                    'attention':[a for a in view['attention'] if a.get('workstream') in (None,work['key'])],
                    'convergence':[c for c in view['convergence'] if work['key'] in c['workstreams']],
                    'coverage':'Offline orientation only: last-known durable snapshot plus locally registered leases. No PM mutation or provider credential required.'}
                response['next_step']='Review the orientation against the actual task, then enroll explicitly.'
                response['enrollment_template']='/home/meanaverage/sayhi/bin/project-intent enroll --scope '+selected_scope+' --workstream '+selected['id']+' --codex --access edit --touching-path relative/path --touching-seam current/seam --approaching next/seam --working "bounded task"'
            except ValueError as exc:
                p.error(str(exc))
            print(json.dumps(response,indent=2));return
        print(json.dumps(result,indent=2));return
    if entries and not args.snapshot:
        try:
            state,record=resolve_assignment(states,args.workstream,args.scope)
            args.scope=state['id'];args.workstream=record['id']
        except ValueError as exc:p.error(str(exc))
    if entries and args.scope:
        try:
            entry=entries[args.scope]
            args.snapshot=args.snapshot or entry['snapshot']
            args.directory=args.directory or entry['enrollment_directory']
        except (OSError,ValueError,KeyError,TypeError):p.error('Scope unavailable in local worker configuration')
    if not args.snapshot:p.error('--snapshot required (or --scope with --worker-config)')
    snapshot=validate_snapshot(read_json(args.snapshot));scope=snapshot['scope_id']
    if args.scope and scope!=args.scope:p.error('Snapshot belongs to a different scope')
    matched=next((s for s in states if s['id']==scope),None)
    if matched:matched['snapshot']=snapshot
    else:states.append({'id':scope,'label':scope,'snapshot':snapshot,'provider_status':'offline'})
    try:
        _,selected=resolve_assignment([{'id':scope,'snapshot':snapshot}],args.workstream,scope)
        args.workstream=selected['id']
        touching=relative_paths(args.touching_path or [])
        avoid_paths=relative_paths(args.avoid_path or [])
    except ValueError as exc:p.error(str(exc))
    result=project(states,[scope]);work=next(w for w in result['workstreams'] if w['id']==args.workstream)
    if args.command in ('session-attach','session-continue'):
        from .session_connector import dispatch
        args.scope=scope;args.intent_context=selected
        try:print(json.dumps(dispatch(args),indent=2))
        except (OSError,ValueError,KeyError,TypeError) as exc:p.error(str(exc))
        return
    if args.command in ('report','report-status'):
        from .reporting import directory_for,submit,reports
        try:
            report_directory=directory_for(entries[scope]) if scope in entries else Path(args.directory or '').resolve()/'reports'
            if args.command=='report':
                if not args.input:p.error('--input required')
                out=submit(report_directory,scope,args.workstream,args.session,read_json(args.input),args.submit)
            else:out=reports(report_directory,scope,args.workstream)
            print(json.dumps(out,indent=2));return
        except (OSError,ValueError,KeyError,TypeError) as exc:p.error(str(exc))
    if args.command=='enroll':
        session=args.session or (os.environ.get('CODEX_THREAD_ID') if args.codex else None)
        if not session or not SAFE_SESSION.fullmatch(session) or not args.directory:
            p.error('enroll requires --directory and --session (or --codex with CODEX_THREAD_ID)')
        try:
            directory=Path(args.directory).resolve();directory.mkdir(parents=True,exist_ok=True,mode=0o700)
            file=directory/(session+'.json')
            # Per-session lock serializes enrollment/renewal; it grants no work lock.
            fd=os.open(directory/(session+'.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'w') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                if file.is_symlink():raise ValueError('Refusing symlink registration')
                old=read_json(file) if file.exists() else None
                checkout=(old or {}).get('checkout') if args.inactive else checkout_identity(args.checkout or Path.cwd())
                if old and old.get('checkout') and checkout and old['checkout']['root']!=checkout['root'] and old['status']=='active' and date(old['expires_at'])>utcnow():
                    raise ValueError('Session checkout changed: release the old enrollment before enrolling the new checkout')
                path=telemetry_path(args.telemetry_file,session) if args.telemetry_file else None
                if args.codex and not path and not old and not args.inactive:
                    path=find_codex_session(Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'sessions',session)
                record=registration(snapshot,args.workstream,session,args.working or (old or {}).get('working',''),
                    args.approaching or (old or {}).get('approaching',[]),args.avoid or (old or {}).get('avoid',[]),path,old,args.inactive)
                record.update(checkout=checkout,access=args.access or (old or {}).get('access','unspecified'),
                    touching_paths=touching if args.touching_path is not None else (old or {}).get('touching_paths',[]),
                    touching_seams=args.touching_seam if args.touching_seam is not None else (old or {}).get('touching_seams',[]),
                    avoid_paths=avoid_paths if args.avoid_path is not None else (old or {}).get('avoid_paths',[]))
                if record['status']=='active' and record['access']=='edit' and not record['touching_paths']:
                    raise ValueError('Declare --touching-path for edit intent (use . only for an explicitly whole-checkout task)')
                if len(json.dumps(record).encode())>65536:raise ValueError('Registration exceeds 64 KiB; keep coordination summaries bounded')
                write_json(file,record)
            print(json.dumps({'scope':scope,'workstream':args.workstream,'session':session,'status':record['status'],
                'expires_at':record['expires_at'],'telemetry':'registered' if record['telemetry'] else 'not-connected',
                'checkout':checkout,'access':record['access'],'touching_paths':record['touching_paths'],'touching_seams':record['touching_seams'],
                'scope_coverage':'Declared paths supplied' if record['touching_paths'] else 'Paths unspecified; do not infer a narrow edit boundary',
                'nearby_workers':[w for w in nearby_workers(states,checkout,record['touching_paths'],record['touching_seams']+record['approaching'],scope) if w['session']!=session],
                'reference_warning':'Workstream source reference differs from execution checkout; it may be inspection material, not an edit target.' if checkout and work.get('source_checkout') and str(Path(work['source_checkout']).resolve())!=checkout['root'] else None,
                'meaning':'Local registration only; observer must watch this scope directory. No PM assignment or execution authority granted.'},indent=2))
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:p.error(str(exc))
        return
    if args.command=='start':
        try:checkout=checkout_identity(args.checkout or Path.cwd())
        except (ValueError,OSError):checkout=None
        print(json.dumps({'contract':result['contract'],'scope':result['scopes'][0],'assignment':work,
            'checkout':checkout,'nearby_workers':nearby_workers(states,checkout,touching,(args.touching_seam or [])+args.approaching+work['boundaries'],scope),
            'attention':[a for a in result['attention'] if a.get('workstream') in (None,work['key'])],
            'convergence':[c for c in result['convergence'] if work['key'] in c['workstreams']],
            'coverage':'Offline orientation only: last-known durable snapshot plus locally registered leases. Checkout is observed only here; paths/seams are declarations, not detected edits or permissions. No remote calls.'},indent=2))
        return
    if not args.directory or not args.session or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',args.session):p.error('--directory and safe --session required')
    now=utcnow()
    write_json(Path(args.directory)/(args.session+'.json'),{'scope':scope,'workstream':args.workstream,
        'session':args.session,'status':'inactive' if args.inactive else 'active','working':args.working,
        'approaching':args.approaching,'avoid':args.avoid,'heartbeat_at':now.isoformat(),'expires_at':(now+timedelta(hours=1)).isoformat()})
    print('Advisory presence updated; no execution authority')


if __name__=='__main__':main()
