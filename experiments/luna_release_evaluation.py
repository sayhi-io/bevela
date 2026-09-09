"""Independent, source-bound gates and best-effort blinded Luna review.

Only disposable source exports are executed. Original trial evidence is preserved.
"""
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import time

from experiments.isolation_v2 import command as isolated
from experiments.review_bundle import export as export_handoffs
from project_intent.runtime import read_json, write_json


def archive(checkout, head, destination):
    destination.mkdir(parents=True, exist_ok=False)
    data = subprocess.check_output(['git', '-C', str(checkout), 'archive', head])
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(destination, filter='data')


def process(command, directory, *, task=None, timeout=300):
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory/'command.json', command)
    start = time.monotonic()
    expired = False
    with (directory/'stdout.txt').open('x') as out, (directory/'stderr.txt').open('x') as err:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                 text=True, start_new_session=True)
        try:
            child.communicate(task, timeout=timeout)
        except subprocess.TimeoutExpired:
            expired = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    result = {'exit_code': child.returncode, 'timeout': expired,
              'elapsed_seconds': time.monotonic()-start, 'passed': child.returncode == 0 and not expired}
    write_json(directory/'result.json', result)
    return result


def gates(study, arm):
    directory = study.ROOT/'arms'/arm
    evaluation = directory/'evaluation'
    evaluation.mkdir(exist_ok=False)
    scratch = evaluation/'scratch'
    scratch.mkdir()
    heads, sources = {}, {}
    for product in ('status', 'support'):
        checkout = directory/product/'integration'
        head = study.call('git', '-C', checkout, 'rev-parse', 'HEAD')
        archive(checkout, head, evaluation/product)
        sources[product] = str(evaluation/product)
        allowed={'TRIAL_HANDOFF.md','CORRECTIONS.json','DELIVERY.json'}
        tracked=study.call('git','-C',checkout,'diff','HEAD','--name-only').splitlines()
        untracked=study.call('git','-C',checkout,'ls-files','--others','--exclude-standard').splitlines()
        source_dirt=sorted(set(tracked)|{p for p in untracked if p not in allowed})
        base=study.call('git','-C',directory/product/'repository','rev-parse','main')
        changes=study.call('git','-C',checkout,'diff','--name-status',base,head)
        study.write(evaluation/(product+'.diff'),study.call('git','-C',checkout,'diff',base,head))
        heads[product] = {'head': head, 'dirty_original': study.call('git','-C',checkout,'status','--porcelain'),
                          'base':base,'changed_files':changes,'undelivered_source':source_dirt}
    # The same immutable harness is visible to all roles and used independently here.
    acceptance = directory/'acceptance'
    env = ['env', 'TRIAL_CHECKOUT='+sources['status'], 'SUPPORT_CHECKOUT='+sources['support'],
           'BROWSER_EXECUTABLE='+str(study.ROOT/'tools/common/browser/headless_shell')]
    python = str(study.ROOT/'tools/common/py/bin/python')
    commands = {
        'release-api-export': [*env,'node','--test',str(acceptance/'luna_release_acceptance.mjs')],
        'release-browser': [*env,python,str(acceptance/'luna_release_browser.py')],
        'legacy-api': [*env,'node','--test',str(acceptance/'incident_history_acceptance.mjs')],
        'legacy-browser': [*env,python,str(acceptance/'incident_history_browser.py')],
        'status-tests': ['npm','--prefix',sources['status'],'test'],
        'status-check': ['npm','--prefix',sources['status'],'run','check'],
        'support-tests': ['npm','--prefix',sources['support'],'test'],
        'support-check': ['npm','--prefix',sources['support'],'run','check'],
    }
    results = {}
    for name, argv in commands.items():
        launch = isolated(study.ROOT, scratch, argv, readonly=[acceptance, evaluation/'status',
            evaluation/'support', study.ROOT/'tools/common'])
        results[name] = process(launch, evaluation/'gates'/name, timeout=300)
        if name in ('release-api-export','legacy-api'):
            output = (evaluation/'gates'/name/'stdout.txt').read_text()
            results[name]['no_skips'] = '# skipped 0' in output
            results[name]['passed'] = results[name]['passed'] and results[name]['no_skips']
        print(json.dumps({'arm':arm,'gate':name,**results[name]}), flush=True)
    outcome=read_json(directory/'arm-outcome.json') if (directory/'arm-outcome.json').exists() else None
    procedure_valid=outcome is not None and outcome['state']=='delivered-awaiting-independent-gates'
    result = {'heads': heads, 'gates': results, 'procedure_valid':procedure_valid,
              'procedure_outcome':outcome and {'state':outcome['state'],'failures':outcome.get('procedure_failures',[])},
              'mechanical_pass': all(r['passed'] for r in results.values()) and procedure_valid
                                 and not any(r['undelivered_source'] for r in heads.values())}
    write_json(evaluation/'gates.json', result)
    return result


def review(study, arm):
    """Reviewer gets committed sources + exact-source handoffs, never owner chat.

    Neutral aliases conceal launch order; textual redactions are audited and are
    explicitly imperfect. Reviewer cannot edit either product export.
    """
    directory = study.ROOT/'arms'/arm
    original = directory/'evaluation'
    gate_report = read_json(original/'gates.json')
    labels = dict(zip(study.ORDER, ('candidate-72','candidate-19','candidate-84','candidate-36')))
    labels.update({'rehearsal-control':'candidate-11','rehearsal-aware':'candidate-58'})
    label = labels[arm]
    root = study.ROOT/'reviews'/label
    root.mkdir(parents=True, exist_ok=False)
    scratch = root/'working'
    scratch.mkdir()
    for product in ('status','support'):
        shutil.copytree(original/product, root/product)
    artifacts, missing = {}, []
    for path in sorted((directory/'artifacts').glob('*/execution.json')):
        execution = read_json(path)
        handoff = path.parent/'handoff.md'
        name = execution['stage']+'-'+execution['role']+'.md'
        if handoff.is_file():
            artifacts[name] = (handoff, execution['head'])
        else:
            missing.append(name)
    replacements = [(str(directory), '/trial'), ('PI-LUNA03-'+arm.upper(), 'COORDINATION-ASSIGNMENT'),
                    ('luna03-'+arm, 'SESSION'), (arm,label), ('Project Intent','coordination channel'),
                    ('project-intent','coordination-tool')]
    if artifacts:
        audit = export_handoffs(root/'handoffs', artifacts, replacements)
        write_json(original/'review-redaction-audit.json', audit)
    else:
        (root/'handoffs').mkdir()
    (root/'context').mkdir()
    write_json(root/'context/missing-handoffs.json', missing)
    write_json(root/'context/gates.json', gate_report)
    for product in ('status','support'):
        content=(original/(product+'.diff')).read_text()
        for old,new in replacements: content=content.replace(old,new)
        study.write(root/'context'/(product+'.diff'),content)
    # Preserve test logs and redact only provenance/condition labels.
    for path in (original/'gates').glob('*/*.txt'):
        content = path.read_text()
        for old,new in replacements:
            content = content.replace(old,new)
        study.write(root/'context'/path.parent.name/path.name, content)
    shutil.copyfile(directory/'instructions/CONTRACT.md',root/'context/CONTRACT.md')
    task = f'''Independently review a disposable two-repository release against {root/'context/CONTRACT.md'}.
Required revision is 2. Product exports {root/'status'} and {root/'support'} are read-only exact committed candidates.
Source-bound original-stage handoffs are under {root/'handoffs'}; missing handoffs and independent mechanical gates/logs are under {root/'context'}.
The context also contains source diffs against the common accepted baseline; check for deleted/disabled regressions and unrelated changes.
Do not assume passing tests establish every contract clause. Inspect cross-client agreement, persistence, revision2 retroactive expiry,
restart/handoff continuity, output durability and regressions. Identify concrete source-backed gaps without implementing fixes.
Do not access other candidates, host context, credentials, production or network; do not create other agents.
Do not infer which treatment should win. Report any blinding clues and uncertainty explicitly.
Write REVIEW.json in your writable working directory with:
{{"accepted":true_or_false,"blockers":[{{"requirement":"contract clause","evidence":"file/line and observed failure"}}],
"unverified":["unverified requirement"],"blinding_clues":["clue or empty"],"summary":"bounded conclusion"}}.
Only accept if revision2 has no blocking contract gaps and independent gates passed. Missing evidence is not affirmative success.
Finish within {study.LIMITS['review']//60} minutes. No candidate repair or coordinator coaching.
'''
    study.write(root/'context/prompt.txt', task)
    home = study.ROOT/'session-homes'/'reviews'/label
    home.mkdir(parents=True,mode=0o700)
    argv = [str(study.ROOT/'tools/common/codex-bin/codex'),'-a','never','exec',
        '--ignore-user-config','--ignore-rules','--enable','skip_host_skill_discovery',
        '--disable','plugins','--disable','apps','--disable','memories','--disable','multi_agent',
        '-c','project_doc_max_bytes=0','-c','web_search="disabled"',
        '-c','model_context_window=200000','-c','model_auto_compact_token_limit=160000',
        '-c','model_reasoning_effort="medium"','-m',study.MODEL,'-s','danger-full-access',
        '--skip-git-repo-check','-C',str(scratch),'--json','-o',str(scratch/'final.md'),'-']
    launch = isolated(study.ROOT,scratch,argv,readonly=[root/'status',root/'support',root/'handoffs',root/'context',study.ROOT/'tools/common'])
    if study.AUTH.is_symlink() or study.AUTH.stat().st_mode & 0o077:
        raise ValueError('Private regular CLI auth required')
    launch[1:1] = ['--bind',str(home),'/home/worker/.codex','--ro-bind',str(study.AUTH),'/home/worker/.codex/auth.json']
    result = process(launch,root/'execution',task=task,timeout=study.LIMITS['review'])
    decision = None
    if (scratch/'REVIEW.json').is_file():
        try:
            decision = read_json(scratch/'REVIEW.json')
        except ValueError:
            pass
    valid = isinstance(decision,dict) and isinstance(decision.get('accepted'),bool) and all(
        isinstance(decision.get(k),list) for k in ('blockers','unverified','blinding_clues'))
    result.update({'label':label,'decision':decision,'valid_review':valid,
        'accepted':result['passed'] and valid and decision['accepted'] and not decision['blockers']
                   and not decision['unverified'] and gate_report['mechanical_pass']})
    usage = {}
    thread=None
    for line in (root/'execution/stdout.txt').read_text().splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        if event.get('type')=='thread.started': thread=event.get('thread_id')
        if event.get('type') == 'turn.completed':
            for key,value in event.get('usage',{}).items(): usage[key]=usage.get(key,0)+value
    result['usage']=usage
    result['observed_model_settings']=study.session_metadata(home,thread)
    result['model_verified']=result['observed_model_settings']=={'model':study.MODEL,'effort':'medium','effective_context_window':190000}
    result['valid_review']=result['valid_review'] and result['model_verified']
    result['accepted']=result['accepted'] and result['model_verified']
    write_json(original/'review.json',result)
    return result


def summarize(study):
    rows=[]
    for arm in study.ORDER:
        directory=study.ROOT/'arms'/arm
        executions=[read_json(p) for p in (directory/'artifacts').glob('*/execution.json')]
        usage={}
        for execution in executions:
            for key,value in execution.get('usage',{}).items(): usage[key]=usage.get(key,0)+value
        outcome=read_json(directory/'arm-outcome.json') if (directory/'arm-outcome.json').exists() else None
        review_result=read_json(directory/'evaluation/review.json') if (directory/'evaluation/review.json').exists() else None
        gate_report=read_json(directory/'evaluation/gates.json') if (directory/'evaluation/gates.json').exists() else None
        setup_seconds=read_json(directory/'setup.json')['setup_seconds'] if (directory/'setup.json').exists() else None
        gate_seconds=sum(r['elapsed_seconds'] for r in gate_report['gates'].values()) if gate_report else None
        review_seconds=review_result and review_result['elapsed_seconds']
        arm_seconds=outcome and outcome.get('elapsed_seconds')
        rows.append({'arm':arm,'outcome':outcome and outcome['state'],
            'accepted':bool(review_result and review_result['accepted']),
            'review_available':review_result is not None,'worker_usage':usage,
            'worker_seconds':sum(r['elapsed_seconds'] for r in executions),
            'setup_seconds':setup_seconds,
            'setup_timing':read_json(directory/'setup.json').get('setup_timing',{'measurement':'monotonic setup process duration'}) if setup_seconds is not None else None,
            'wall_seconds':arm_seconds,'independent_gate_seconds':gate_seconds,
            'review_seconds':review_seconds,'measured_end_to_end_seconds':sum((setup_seconds,arm_seconds,gate_seconds,review_seconds))
                if all(v is not None for v in (setup_seconds,arm_seconds,gate_seconds,review_seconds)) else None,
            'correction_sessions':sum(r['stage'].startswith('correction') for r in executions),
            'timeouts':sum(r['timeout'] for r in executions),
            'failed_processes':sum(r['exit_code']!=0 for r in executions),
            'updated_handoffs':sum(r['handoff_updated'] for r in executions),
            'review':review_result})
    complete=all(r['review_available'] for r in rows)
    report={'complete':complete,'arms':rows,'limitations':[
        'Two matched pairs are descriptive, not statistical proof or general capability ranking.',
        'Named model alias may change upstream; requested Luna medium is recorded, not an immutable weight revision.',
        'PI treatment includes onboarding/presence/reporting instructions and offline native snapshots, not only a UI.',
        'Outer filesystem namespaces isolate context, not hostile shared-network or writable common-Git abuse.',
        'Shared facts and scheduled revision are known to both conditions; blinding is explicitly imperfect.']}
    write_json(study.ROOT/'results.json',report)
    return report
