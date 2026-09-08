"""Disposable matched-team study runner; not a Project Intent runtime feature."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from project_intent.provider_write import configured, reconcile
from project_intent.reporting import digest
from project_intent.runtime import read_json, write_json

BASE = '92b68abbca805af45f2161409770ebe746146e9f'
SOURCE = Path('/home/meanaverage/sayhi/repos/sayhi-status')
PI = Path('/home/meanaverage/sayhi/state/project-intent/current').resolve()
PI_CLI = PI / '.venv/bin/project-intent'
STATE = Path('/home/meanaverage/sayhi/state/project-intent')
ROOT = STATE / 'evaluations/20260906-status-shared-contract-02'
CHECKOUT = Path(__file__).resolve().parents[1]
ORDER = ['A-control','A-aware','B-aware','B-control']
TASKS = {'api':'Incident history storage and API', 'browser':'Shareable incident-history browser', 'integration':'Incident-history integration successor'}
CORRECTION = '''This is a bounded correction by a fresh session in the SAME owner role.
Read your existing TRIAL_HANDOFF.md, source, ordinary notes and the actual finding packet below.
You do not have the prior conversation. PI-aware sessions also retain their normal scoped PI channel.
Fix only findings assigned to your owner role; preserve accepted behavior and peer boundaries.
Commit your correction locally and update the handoff/evidence; do not edit peer checkouts.
Budget:10 minutes per correction round, at most two rounds. Findings are observations, not invented tasks.
'''
REVIEW = '''Independently review this disposable candidate against TRIAL_TASKS.md.
You are blind to treatment assignment. Do not seek trial labels, transcripts, other
candidate branches/directories, provider state or global workspace context.
Inspect only this candidate, its parent/base diff and the provided acceptance files.
Do not edit implementation, create commits, deploy, contact live services or spawn workers.
Run npm test and npm run check plus the supplied common acceptance where feasible.
Attempt to find concrete correctness, integration, compatibility and handoff deficiencies.
Do not invent findings or use test-count as a quality score. Explain any blinding clues.
Write REVIEW.json: {"verdict":"accepted|changes-required","findings":[{"owner":"api|browser|integration","reason":"concrete finding","severity":"blocking|nonblocking"}],"tests":["actually executed"],"blinding":"observed limitations"}.
Also write TRIAL_HANDOFF.md summarizing exact head and review evidence. Budget:10 minutes.
'''


def call(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT)


def stamp(): return datetime.now(timezone.utc).isoformat()


def identity(pair, task): return 'PI-AB2-'+pair+'-'+task.upper()


def setup():
    started=time.monotonic()
    ROOT.mkdir(parents=True,exist_ok=False)
    (ROOT/'DISPOSABLE_TRIAL').touch()
    write_json(ROOT/'setup-start.json',{'at':stamp()})
    frozen=ROOT/'frozen'; frozen.mkdir()
    files=['cli_harness.py','shared_contract_study.py','incident_history_acceptance.mjs',
           'incident_history_browser.py','incident_history_browser_server.mjs','BROWSER_CONTRACT.md']
    for name in files:shutil.copyfile(CHECKOUT/'experiments'/name,frozen/name)
    protocol=(CHECKOUT/'docs/CLI_AB_SHARED_CONTRACT.md').read_text()
    (frozen/'PROTOCOL.md').write_text(protocol)
    # Both arms see exactly the same feature request and browser acceptance contract.
    task_text=protocol.split('## Product request given identically to both arms\n',1)[1].split('## Why this is harder',1)[0]
    task_text += '\n## Browser acceptance interface\n'+(frozen/'BROWSER_CONTRACT.md').read_text()
    (frozen/'TASKS.md').write_text(task_text)
    (frozen/'CORRECTION.txt').write_text(CORRECTION)
    (frozen/'REVIEW.txt').write_text(REVIEW)
    timings=[]; enrollment=[]
    config=read_json(STATE/'config.json');entry,provider=configured(config,'sayhi/project-intent')
    inventory=provider.inventory()
    write_json(ROOT/'provider-inventory-before.json',inventory)
    for arm in ORDER:
        t0=time.monotonic(); directory=ROOT/arm;directory.mkdir()
        repo=directory/'repository'
        call('git','clone','--no-local',str(SOURCE),str(repo))
        call('git','-C',str(repo),'remote','remove','origin')
        call('git','-C',str(repo),'config','user.name','Status feature study')
        call('git','-C',str(repo),'config','user.email','study@example.invalid')
        for name in TASKS:
            target=directory/name
            call('git','-C',str(repo),'worktree','add','-b',name,str(target),BASE)
            (target/'TRIAL_TASKS.md').write_text(task_text)
        for name in ('notes','coordination','artifacts'): (directory/name).mkdir()
        acceptance=directory/'acceptance';acceptance.mkdir()
        for name in files[2:]:shutil.copyfile(frozen/name,acceptance/name)
        # Reproducible evaluator-owned environment, no legacy borrowed venv.
        call('python3','-m','venv',str(directory/'.venv'))
        install=call(str(directory/'.venv/bin/python'),'-m','pip','install','--disable-pip-version-check','playwright==1.55.0')
        (directory/'artifacts/environment-install.txt').write_text(install)
        local_records=[]
        if arm.endswith('aware'):
            for name,title in TASKS.items():
                record={'kind':'workstream','id':identity(arm[0],name),'revision':'1','state':'active',
                    'statement':title+' in disposable SayHi Status shared-contract study pair '+arm[0],
                    'scope':task_text+'\nAssigned owner role: '+name,
                    'acceptance':['Common frozen API/browser acceptance passes; existing tests/check pass.','Detailed source-bound handoff with evidence and unresolved work.'],
                    'avoid':'No production, remote Git, monitored endpoints, other trial arms, global context, credential access or extra worker spawning. No PI product changes.',
                    'boundaries':['status/incident-history','status/pagination-contract','status/browser-url-state'],
                    'source_checkout':str(directory/name),
                    'readiness':{'implementation':'not-started','review':'not-started','merge':'not-authorized','production':'not-authorized'},
                    'environment':{'requirement':'Disposable SayHi Status checkout; Node22 stdlib plus arm-local Playwright1.55.0 evaluation venv; local loopback only.'}}
                packet={'scope':'sayhi/project-intent','confirmed':True,'record':record,'title':record['statement'],'expected_digest':digest(None)}
                write_json(ROOT/(record['id']+'-enrollment.json'),packet)
                result=reconcile(provider,'sayhi/project-intent',packet,config['operator']['journal_directory'])
                if result['state']!='published':raise RuntimeError('Enrollment uncertain; inspect '+record['id'])
                enrollment.append(result)
                native=provider.resolve(result['identifier'])
                local_records.append({**native['record'],'provider_id':native['native_id'],'provider_identifier':native['identifier']})
            snapshot={'version':1,'scope_id':'sayhi/project-intent','mission':'Disposable matched incident-history implementation study; not product deployment.',
                'records':local_records,'initiatives':[], 'source':{'provider':'itsaplan','project':'SAYINT','captured_at':stamp(),'authoritative':False,'mode':'offline_snapshot'}}
            snap=directory/'coordination/snapshot.json';write_json(snap,snapshot)
            (directory/'coordination/enrollments').mkdir()
            (directory/'coordination/reports').mkdir()
            write_json(directory/'coordination/worker-scopes.json',{'scopes':{'sayhi/project-intent':{
                'snapshot':str(snap),'enrollment_directory':str(directory/'coordination/enrollments'),
                'report_directory':str(directory/'coordination/reports')}}})
        timings.append({'arm':arm,'setup_seconds':round(time.monotonic()-t0,3)})
        print(json.dumps(timings[-1]),flush=True)
    write_json(ROOT/'enrollment-receipts.json',enrollment)
    call('python3','-m','venv',str(ROOT/'review-environment'))
    (ROOT/'review-environment-install.txt').write_text(call(str(ROOT/'review-environment/bin/python'),'-m','pip','install','--disable-pip-version-check','playwright==1.55.0'))
    # Freeze every initial prompt before either arm runs.
    prompts=ROOT/'prompts';prompts.mkdir()
    for arm in ORDER:
        for task in TASKS:
            (prompts/(arm+'-'+task+'.txt')).write_text(prompt(arm,task))
    execution_files=list(frozen.iterdir())+list(prompts.iterdir())
    for arm in ORDER:
        execution_files+=list((ROOT/arm/'acceptance').iterdir())
        execution_files += [ROOT/arm/name/'TRIAL_TASKS.md' for name in TASKS]
        if arm.endswith('aware'):execution_files += [ROOT/arm/'coordination/snapshot.json',ROOT/arm/'coordination/worker-scopes.json']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in execution_files}
    write_json(ROOT/'manifest.json',{'base':BASE,'model':'gpt-6-astra','reasoning':'medium',
        'cli':call('codex','--version').strip(),'node':call('node','--version').strip(),'created_at':stamp(),
        'order':ORDER,'setup':timings,'total_setup_seconds':round(time.monotonic()-started,3),'hashes':hashes,
        'limits':{'owner_seconds':1200,'integration_seconds':900,'correction_rounds':2,'correction_seconds':600},
        'limitations':['Single feature, two pairs; not general efficacy evidence.','Model alias is fixed but provider snapshot identity is not exposed.',
                      'Same-user cooperative read isolation, not hostile-code containment.','Pre-study harness engineering is separate from measured per-arm setup.']})
    print('Frozen study setup complete: '+str(ROOT),flush=True)


def prompt(arm,task):
    directory=ROOT/arm
    common=f'''Implement the real product request in TRIAL_TASKS.md inside this disposable fork only.
Read repository AGENTS.md and README.md explicitly; automatic instruction discovery is disabled.
Your role: {task} — {TASKS[task]}. Both owners see the entire identical request and acceptance.
API owner owns src/state.mjs, src/worker.mjs, added server modules, test/history-api*.mjs and API docs.
Browser owner owns src/ui.mjs, added browser modules, test/history-browser*.mjs and browser docs.
Keep shared README changes additive; coordinate via {directory/'notes'}/api.md and browser.md.
Peer checkouts: {directory/'api'} and {directory/'browser'}. Read peers when useful; do not write their files.
No mandatory handshakes. Solve ordinary obstacles within scope; do not stop just because a dependency exists.
Do not read other trial arms, coordinator files, user conversations, global skills/configs or credentials.
Do not push, deploy, call monitored endpoints, run live schedules, modify canonical source, or spawn extra workers.
Use ordinary Node tooling. Shared evaluator Python is {directory/'.venv/bin/python'}; browser cache is /home/meanaverage/sayhi/state/project-intent/browser-test.
Run npm test and npm run check. Frozen common acceptance is in {directory/'acceptance'} (read-only).
API: TRIAL_CHECKOUT="$PWD" node --test {directory/'acceptance/incident_history_acceptance.mjs'}
Browser: TRIAL_CHECKOUT="$PWD" {directory/'.venv/bin/python'} {directory/'acceptance/incident_history_browser.py'}
Your own owner checkout may not pass combined acceptance before integration; report that precisely.
Do not edit frozen acceptance files or manufacture findings. Both APIs and UI must satisfy the same contract.
You may create local commits of your OWN implementation in this disposable repository. Do not stage TRIAL_TASKS.md,
TRIAL_HANDOFF.md, coordination files, browser screenshots, logs or generated evidence.
Write detailed TRIAL_HANDOFF.md: exact commits, files, real tests, interface decisions, coordination effect,
remaining work and successor instructions. CLI saves your final response elsewhere; do not overwrite your handoff.
Budget: 20 minutes per initial owner; no changes to production or PI itself.
'''
    if task=='integration':
        common+='''\nYou are a FRESH integration successor, not an initial owner. Your budget is 15 minutes.
Inspect owner handoffs and notes, then integrate local branches api and browser into YOUR integration checkout.
Resolve textual integration conflicts if needed, preserving both intents. Run common acceptance and regressions.
Do not silently implement missing owner features. If an owner correction is needed, write CORRECTIONS.json as
{"requests":[{"owner":"api|browser","reason":"concrete observed finding","preserve":"constraints"}]}.
No findings means an empty requests list. Finish your integration handoff with evidence and current source.
'''
    if arm.endswith('aware'):
        alias=identity(arm[0],task)
        common+=f'''\nAdditional available channel: Project Intent, using ONLY the trial-scoped map.
CLI: {PI_CLI} --worker-config {directory/'coordination/worker-scopes.json'}
Run discover --query incident, start --workstream {alias}, then enroll your own presence:
--workstream {alias} --session study02-{arm}-{task} --access edit --touching-path src --touching-path test
--working "Your bounded task" --touching-seam status/incident-history --approaching status/pagination-contract
Snapshot is last-known organizational context, not execution authority. All requirements also exist in TRIAL_TASKS.md.
Inspect start for nearby context/reports when useful. Ordinary notes remain available. No journaling quota.
For a report, write a JSON FILE in your checkout, e.g. {{"summary":"Actual outcome","next_step":"Bounded next step","readiness":{{"implementation":"actual state"}}}}.
Use report --workstream {alias} --session study02-{arm}-{task} --input /absolute/path/to/that-file.json.
Do not pass JSON text as --input. Reports remain local; do not seek provider credentials or global scope maps.
At finish report meaningful evidence/handoff and enroll --inactive using the same identity.
If PI is unavailable continue authorized work using repo/notes and record the actual deficiency.
'''
    return common


def load_harness():
    file=ROOT/'frozen/cli_harness.py'
    spec=importlib.util.spec_from_file_location('study_harness',file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def verify_frozen():
    manifest=read_json(ROOT/'manifest.json')
    for name,expected in manifest['hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen artifact changed: '+name)


def run_arm(arm):
    verify_frozen()
    gate=read_json(ROOT/'base-gate/results.json')
    if not gate['passed']:raise RuntimeError('Base validation gate did not pass')
    index=ORDER.index(arm)
    if index and not (ROOT/ORDER[index-1]/'adjudication.json').exists():raise RuntimeError('Prior arm not adjudicated')
    directory=ROOT/arm;harness=load_harness();start=time.monotonic()
    with (directory/'started.json').open('x') as stream:json.dump({'at':stamp()},stream)
    def launch(task):
        result=harness.run(ROOT,directory/task,directory/'artifacts'/('initial-'+task),
            (ROOT/'prompts'/(arm+'-'+task+'.txt')).read_text(),
            [directory/'notes',directory/'coordination'],timeout=1200 if task!='integration' else 900)
        print(json.dumps({'task':task,**result}),flush=True);return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={task:pool.submit(launch,task) for task in ('api','browser')}
        owners={task:future.result() for task,future in futures.items()}
    owner_wall=time.monotonic()-start
    integration=launch('integration')
    write_json(directory/'initial-execution.json',{'owners':owners,'integration':integration,
        'owner_wall_seconds':round(owner_wall,3),'arm_wall_seconds':round(time.monotonic()-start,3)})


def validate(arm,label):
    verify_frozen()
    directory=ROOT/arm;target=directory/'integration';output=directory/'artifacts'/label;output.mkdir(exist_ok=False)
    env={**os.environ,'TRIAL_CHECKOUT':str(target),'PLAYWRIGHT_BROWSERS_PATH':'/home/meanaverage/sayhi/state/project-intent/browser-test'}
    commands={'regression':['npm','test'],'syntax':['npm','run','check'],
        'api':['node','--test',str(directory/'acceptance/incident_history_acceptance.mjs')],
        'browser':[str(directory/'.venv/bin/python'),str(directory/'acceptance/incident_history_browser.py')]}
    results={}
    for name,cmd in commands.items():
        t0=time.monotonic()
        with (output/(name+'.log')).open('x') as log:
            try:result=subprocess.run(cmd,cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180);code=result.returncode
            except subprocess.TimeoutExpired:code=124
        results[name]={'exit_code':code,'elapsed_seconds':round(time.monotonic()-t0,3)}
    write_json(output/'results.json',results);print(json.dumps(results,indent=2))


def base_gate():
    verify_frozen();output=ROOT/'base-gate';output.mkdir(exist_ok=False)
    # All arms have the exact same base/input hashes. This is an evaluator gate,
    # not worker exposure to another arm's implementation (none has launched).
    target=ROOT/ORDER[0]/'repository'
    env={**os.environ,'TRIAL_CHECKOUT':str(target)}
    commands={'regression':['npm','test'],'syntax':['npm','run','check'],
        'api':['node','--test',str(ROOT/'frozen/incident_history_acceptance.mjs')],
        'browser':[str(ROOT/ORDER[0]/'.venv/bin/python'),str(ROOT/'frozen/incident_history_browser.py')]}
    results={}
    for name,cmd in commands.items():
        r=subprocess.run(cmd,cwd=target,env=env,capture_output=True,text=True,timeout=180)
        log=r.stdout+r.stderr;(output/(name+'.log')).write_text(log)
        results[name]={'exit_code':r.returncode}
        if name=='api':results[name]['expected_missing_route']='404 !== 200' in log and 'db.batch is not a function' not in log
        if name=='browser':results[name]['expected_missing_filter']='Missing feature: Incident component history filter' in log and 'errors=' not in log
    results['passed']=(results['regression']['exit_code']==results['syntax']['exit_code']==0
        and results['api']['exit_code']!=0 and results['api']['expected_missing_route']
        and results['browser']['exit_code']!=0 and results['browser']['expected_missing_filter'])
    write_json(output/'results.json',results);print(json.dumps(results,indent=2))


def correct(arm,round_number):
    verify_frozen()
    if round_number not in (1,2):raise ValueError('Two correction rounds maximum')
    directory=ROOT/arm;packet=read_json(directory/f'corrections-{round_number}.json')
    if not packet.get('requests'):raise ValueError('No actual owner findings')
    if any(r.get('owner') not in ('api','browser') or not r.get('reason') for r in packet['requests']):
        raise ValueError('Bounded observed owner findings required')
    harness=load_harness();results={}
    for task in ('api','browser'):
        requests=[r for r in packet['requests'] if r['owner']==task]
        if not requests:continue
        text=(ROOT/'prompts'/(arm+'-'+task+'.txt')).read_text()
        text+='\n'+(ROOT/'frozen/CORRECTION.txt').read_text()+'\n'+json.dumps(requests,indent=2)
        results[task]=harness.run(ROOT,directory/task,directory/'artifacts'/f'correction-{round_number}-{task}',text,
            [directory/'notes',directory/'coordination'],timeout=600)
    spent=read_json(directory/'initial-execution.json')['integration']['elapsed_seconds']
    for old in range(1,round_number):
        spent+=read_json(directory/f'correction-{old}.json').get('integration',{}).get('elapsed_seconds',0)
    remaining=max(0,int(900-spent))
    if remaining:
        text=(ROOT/'prompts'/(arm+'-integration.txt')).read_text()
        text+=f'\nFresh successor continuation: read existing integration handoff, integrate updated api/browser branches, and reverify only. Remaining TOTAL successor budget {remaining}s. Prior findings:\n'+json.dumps(packet)
        results['integration']=harness.run(ROOT,directory/'integration',directory/'artifacts'/f'correction-{round_number}-integration',text,
            [directory/'notes',directory/'coordination'],timeout=remaining)
    else:results['integration']={'elapsed_seconds':0,'budget_exhausted':True}
    write_json(directory/f'correction-{round_number}.json',results);print(json.dumps(results,indent=2))


def review(arm,label):
    verify_frozen()
    marker=ROOT/arm/(label+'-review.json')
    if marker.exists():raise ValueError('Review already recorded')
    directory=ROOT/'reviews'/uuid.uuid4().hex[:12];directory.mkdir(parents=True)
    target=directory/'repository'
    call('git','clone','--no-local',str(ROOT/arm/'integration'),str(target))
    call('git','-C',str(target),'remote','remove','origin')
    (target/'TRIAL_TASKS.md').write_bytes((ROOT/'frozen/TASKS.md').read_bytes())
    tests=directory/'acceptance';tests.mkdir()
    for source in (ROOT/'frozen').glob('incident_history*'):shutil.copyfile(source,tests/source.name)
    text=(ROOT/'frozen/REVIEW.txt').read_text()
    text+=f'\nBase:{BASE}. API command: TRIAL_CHECKOUT="$PWD" node --test {tests}/incident_history_acceptance.mjs\nBrowser command: TRIAL_CHECKOUT="$PWD" {ROOT}/review-environment/bin/python {tests}/incident_history_browser.py\n'
    result=load_harness().run(ROOT,target,directory/'artifacts',text,timeout=600)
    report=read_json(target/'REVIEW.json') if (target/'REVIEW.json').exists() else {'verdict':'missing-review'}
    write_json(marker,{'directory':str(directory),'execution':result,'review':report})
    print(json.dumps({'execution':result,'review':report},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['setup','run-arm','validate','base-gate','correct','review'])
    parser.add_argument('--arm',choices=ORDER);parser.add_argument('--round',type=int);parser.add_argument('--label',default='validation-01');args=parser.parse_args()
    if args.action=='setup':setup()
    elif args.action=='run-arm':run_arm(args.arm)
    elif args.action=='base-gate':base_gate()
    elif args.action=='correct':correct(args.arm,args.round)
    elif args.action=='review':review(args.arm,args.label)
    else:validate(args.arm,args.label)
