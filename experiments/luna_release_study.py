"""Study03 Luna/medium: isolated multi-client release, never a product runtime.

Preparation, rehearsal, freeze and scored arms are separate explicit commands.
No candidate source is repaired by this runner or its coordinator.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
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
from project_intent.provider_write import configured, reconcile
from project_intent.reporting import digest
from project_intent.runtime import read_json, write_json

SOURCE = Path(__file__).resolve().parents[1]
ROOT = Path('/home/meanaverage/sayhi/state/project-intent/evaluations/20260908-luna-release-03')
BASE_SOURCE = Path('/home/meanaverage/sayhi/state/project-intent/evaluations/20260906-status-shared-contract-02/A-control/integration')
BASE = '782f969409079d743f6b43fb562df79b76b7d21a'
AUTH = Path('/home/meanaverage/.codex/auth.json')
CODEX = Path('/home/meanaverage/.npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-arm64/vendor/aarch64-unknown-linux-musl/bin')
BROWSER = Path('/home/meanaverage/sayhi/state/project-intent/browser-test/chromium_headless_shell-1234/chrome-linux')
MODEL = 'gpt-5.6-luna'
ROLES = ('storage', 'api', 'browser', 'export')
ORDER = ('A-control', 'A-aware', 'B-aware', 'B-control')
LIMITS = {'initial': 1800, 'revision': 1800, 'integration': 1200, 'correction': 900, 'review': 900}
PREFLIGHT_ARMS = ('preflight-control', 'preflight-aware')
REHEARSAL_ARMS = ('rehearsal-control', 'rehearsal-aware')
BASELINE_ARM = 'baseline-calibrated-control'
FILES = ('luna_release_study.py', 'isolation_v2.py', 'LUNA_RELEASE_CONTRACT.md',
         'luna_release_fixture.mjs', 'luna_release_acceptance.mjs', 'luna_release_browser.py',
         'incident_history_acceptance.mjs', 'incident_history_browser.py',
         'incident_history_browser_server.mjs', 'BROWSER_CONTRACT.md')


def inputs():
    names = ['experiments/'+name for name in FILES]
    names += ['experiments/luna_release_evaluation.py', 'experiments/review_bundle.py',
              'docs/CLI_AB_LUNA_RELEASE_03.md']
    return {name: sha(SOURCE/name) for name in names}


def require_preflight():
    for arm in PREFLIGHT_ARMS:
        if not read_json(ROOT/'arms'/arm/'preflight.json')['passed']:
            raise ValueError('Both actual-worker condition preflights must pass')
        if not read_json(ROOT/'arms'/arm/'resume-validation.json')['passed']:
            raise ValueError('Actual resumed model/context metadata must pass the corrected launcher')


def freeze():
    if (ROOT/'freeze.json').exists():
        raise ValueError('Frozen protocol cannot be overwritten')
    require_preflight()
    baseline=read_json(ROOT/'arms'/BASELINE_ARM/'evaluation/gates.json')['gates']
    if any(not baseline[name]['passed'] for name in ('legacy-api','legacy-browser','status-tests','status-check','support-tests','support-check')):
        raise ValueError('Baseline regression/tool gates must pass')
    if baseline['release-api-export']['passed'] or baseline['release-browser']['passed']:
        raise ValueError('Untouched baseline must fail the absent new release features')
    for arm in REHEARSAL_ARMS:
        if not read_json(ROOT/'arms'/arm/'evaluation/review.json')['valid_review']:
            raise ValueError('Rehearsal review must be valid; product failure is allowed, missing review is not')
    approval = read_json(ROOT/'harness-review.json')
    if approval.get('blocking_findings') != [] or approval.get('input_hashes') != inputs():
        raise ValueError('Current exact harness must have independent review and no unresolved blockers')
    equality = []
    for arm in ORDER:
        directory = ROOT/'arms'/arm
        if (directory/'execution-start.json').exists():
            raise ValueError('Scored candidate already started before freeze')
        equality.append({
            'status_tree': call('git','-C',directory/'status/repository','rev-parse','HEAD^{tree}'),
            'support_tree': call('git','-C',directory/'support/repository','rev-parse','HEAD^{tree}'),
            'contract': sha(directory/'instructions/CONTRACT.md'),
            'acceptance': {p.name:sha(p) for p in sorted((directory/'acceptance').iterdir()) if p.is_file()}})
    if any(row != equality[0] for row in equality):
        raise ValueError('Unequal scored source or acceptance inputs')
    for arm in ORDER:
        for role in (*ROLES,'integration'):
            for stage in ('initial','revision','integration','correction'):
                write(ROOT/'frozen-prompts'/arm/(role+'-'+stage+'.txt'), prompt(arm,role,stage))
    write_json(ROOT/'freeze.json',{'at':now(),'inputs':inputs(),'order':ORDER,'limits':LIMITS,
        'equal_common_inputs':equality[0],'toolchain':read_json(ROOT/'toolchain.json'),
        'pi_tool_hashes':{str(p.relative_to(ROOT/'tools/pi')):sha(p) for p in (ROOT/'tools/pi').rglob('*') if p.is_file() and '__pycache__' not in p.parts},
        'prompt_hashes':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'frozen-prompts').rglob('*.txt')},
        'review':approval,'coaching':'No task-specific human or stronger-model candidate fixes'})


def require_frozen(arm):
    frozen = read_json(ROOT/'freeze.json')
    if frozen['inputs'] != inputs() or frozen['limits'] != LIMITS or frozen['order'] != list(ORDER):
        raise ValueError('Protocol/source drift after freeze; stop without changing scored evidence')
    if frozen['toolchain'] != read_json(ROOT/'toolchain.json') or sha(ROOT/'tools/common/codex-bin/codex') != frozen['toolchain']['codex_sha256'] or sha(ROOT/'tools/common/browser/headless_shell') != frozen['toolchain']['browser_sha256']:
        raise ValueError('Frozen toolchain drift')
    if any(sha(ROOT/name) != expected for name,expected in frozen['prompt_hashes'].items()):
        raise ValueError('Frozen prompt evidence drift')
    if any(sha(ROOT/'tools/pi'/name) != expected for name,expected in frozen['pi_tool_hashes'].items()):
        raise ValueError('PI tool drift')
    if arm in ORDER:
        directory=ROOT/'arms'/arm
        if sha(directory/'instructions/CONTRACT.md') != frozen['equal_common_inputs']['contract']:
            raise ValueError('Arm contract drift')
        if {p.name:sha(p) for p in (directory/'acceptance').iterdir() if p.is_file()} != frozen['equal_common_inputs']['acceptance']:
            raise ValueError('Arm acceptance drift')
        for predecessor in ORDER[:ORDER.index(arm)]:
            if not (ROOT/'arms'/predecessor/'evaluation/review.json').is_file():
                raise ValueError('Predeclared scored order not complete through independent review')


def now():
    return datetime.now(timezone.utc).isoformat()


def call(*args, cwd=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def initialize(repo):
    call('git', 'init', '-b', 'main', repo)
    call('git', '-C', repo, 'config', 'user.name', 'Disposable release study')
    call('git', '-C', repo, 'config', 'user.email', 'study@example.invalid')
    call('git', '-C', repo, 'add', '.')
    call('git', '-C', repo, 'commit', '-m', 'Common source-only study baseline')


def source_copy(destination):
    destination.mkdir(parents=True)
    archive = subprocess.check_output(['git', '-C', str(BASE_SOURCE), 'archive', BASE])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter='data')
    initialize(destination)


def setup_tools():
    if (ROOT / 'tools').exists():
        raise ValueError('Tools already prepared; inspect existing evidence instead of overwriting')
    (ROOT / 'DISPOSABLE_TRIAL').touch(exist_ok=False)
    common = ROOT / 'tools/common'
    common.mkdir(parents=True)
    shutil.copytree(CODEX, common / 'codex-bin')
    shutil.copytree(BROWSER, common / 'browser')
    call('python3', '-m', 'venv', common / 'py')
    write(ROOT / 'environment-install.txt', call(common / 'py/bin/python', '-m', 'pip', 'install',
                                                '--disable-pip-version-check', 'playwright==1.55.0'))
    pi = ROOT / 'tools/pi'
    pi.mkdir()
    shutil.copytree(SOURCE / 'project_intent', pi / 'project_intent', ignore=shutil.ignore_patterns('__pycache__'))
    write(pi / 'project-intent', '#!/usr/bin/python3\nimport sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom project_intent.cli import main\nmain()\n')
    (pi / 'project-intent').chmod(0o755)
    write_json(ROOT / 'toolchain.json', {'at': now(), 'model': MODEL, 'effort': 'medium',
        'cli': call(common / 'codex-bin/codex', '--version'), 'node': call('node', '--version'),
        'codex_sha256': sha(common / 'codex-bin/codex'), 'browser_sha256': sha(common / 'browser/headless_shell'),
        'context_window': 200000, 'auto_compact_limit': 160000,
        'model_documentation': 'https://developers.openai.com/api/docs/models/gpt-5.6-luna',
        'auth': 'Explicit read-only mount of existing CLI auth only; no credential copied into evidence'})


def paths(arm, role):
    directory = ROOT / 'arms' / arm
    product = 'support' if role == 'export' else 'status'
    return directory, directory / product / role


def setup_sources(arm):
    directory = ROOT / 'arms' / arm
    directory.mkdir(parents=True, exist_ok=False)
    for folder in ('notes', 'context', 'presence', 'reports', 'artifacts', 'acceptance', 'instructions'):
        (directory / folder).mkdir()
    source_copy(directory / 'status/repository')
    support = directory / 'support/repository'
    support.mkdir(parents=True)
    write_json(support / 'package.json', {'name': 'support-history-client', 'private': True, 'type': 'module',
        'scripts': {'test': 'node --test', 'check': 'node --check bin/export-history.mjs'}})
    write(support / 'bin/export-history.mjs', 'if(process.argv.includes("--help")){console.log("Incident export client: implement the supplied release contract");}else{console.error("Not implemented");process.exitCode=2;}\n')
    write(support / 'README.md', '# Support history client\nImplement the supplied shared release contract. No external dependencies or production access.\n')
    initialize(support)
    for role in (*ROLES, 'integration'):
        _, checkout = paths(arm, role)
        product = 'support' if role == 'export' else 'status'
        call('git', '-C', directory / product / 'repository', 'worktree', 'add', '-b', role, checkout, 'main')
    call('git', '-C', support, 'worktree', 'add', '-b', 'integration', directory / 'support/integration', 'main')
    for name in FILES[3:]:
        shutil.copyfile(SOURCE / 'experiments' / name, directory / 'acceptance' / name)
    shutil.copyfile(SOURCE / 'experiments/LUNA_RELEASE_CONTRACT.md', directory / 'instructions/CONTRACT.md')
    write(directory / 'instructions/CURRENT_REVISION.md', 'Current required product revision: 1. Implement revision1 only. A later stage changes existing-snapshot expiry.\n')


def validate_setup_resume(arm):
    directory=ROOT/'arms'/arm
    if not directory.is_dir() or any((directory/name).exists() for name in (
        'setup.json','execution-start.json','context/snapshot.json','context/map.json')):
        raise ValueError('Only unfinished, unstarted native setup may be resumed')
    for role in (*ROLES,'integration'):
        _,checkout=paths(arm,role)
        product='support' if role=='export' else 'status'
        base=call('git','-C',directory/product/'repository','rev-parse','main')
        if call('git','-C',checkout,'rev-parse','HEAD')!=base or call('git','-C',checkout,'status','--porcelain'):
            raise ValueError('Candidate work exists; setup recovery refused')
    support=directory/'support/integration'
    if call('git','-C',support,'rev-parse','HEAD')!=call('git','-C',directory/'support/repository','rev-parse','main') or call('git','-C',support,'status','--porcelain'):
        raise ValueError('Support integration work exists; setup recovery refused')
    if sha(directory/'instructions/CONTRACT.md')!=sha(SOURCE/'experiments/LUNA_RELEASE_CONTRACT.md') or any(
        sha(directory/'acceptance'/name)!=sha(SOURCE/'experiments'/name) for name in FILES[3:]):
        raise ValueError('Setup input drift; do not overwrite previous setup inputs')


def setup_arm(arm, *, resume=False):
    start=time.monotonic()
    directory=ROOT/'arms'/arm
    if resume:
        validate_setup_resume(arm)
    else:
        setup_sources(arm)
    support=directory/'support/repository'
    records = []
    if arm.endswith('aware'):
        config = read_json('/home/meanaverage/sayhi/state/project-intent/config.json')
        _, provider = configured(config, 'sayhi/project-intent')
        for role in (*ROLES, 'integration'):
            alias = 'PI-LUNA03-' + arm.upper() + '-' + role.upper()
            record = {'id': alias, 'kind': 'workstream', 'revision': '1', 'state': 'active',
                'statement': f'Isolated Luna release study {arm}: {role} owner',
                'scope': (directory / 'instructions/CONTRACT.md').read_text() + '\nCurrent required revision: 1. Owner role: ' + role,
                'acceptance': ['Shared frozen product contract and common acceptance; preserve real source-bound handoff.'],
                'boundaries': ['study03/snapshot-lifecycle', 'study03/public-contract', 'study03/cross-client-consistency'],
                'avoid': 'No production, extra task authority, other arms, secrets, stronger-model repair or global context.',
                'source_checkout': str(paths(arm, role)[1]),
                'readiness': {'implementation': 'not-started', 'review': 'not-started', 'production': 'not-authorized'}}
            packet = {'scope': 'sayhi/project-intent', 'confirmed': True, 'title': record['statement'],
                      'expected_digest': digest(None), 'record': record}
            packet_path=directory/'context'/(role+'-packet.json')
            if packet_path.exists():
                if read_json(packet_path)!=packet:
                    raise ValueError('Saved native packet differs; stop rather than change its identity')
                packet=read_json(packet_path)
            else:
                write_json(packet_path,packet)
            result = reconcile(provider, 'sayhi/project-intent', packet, config['operator']['journal_directory'])
            if result['state'] != 'published':
                raise RuntimeError('Native enrollment uncertain; stop and reconcile exact saved packet')
            native = provider.resolve(result['identifier'])
            records.append({**native['record'], 'provider_id': native['native_id'], 'provider_identifier': native['identifier']})
        snapshot = {'version': 1, 'scope_id': 'sayhi/project-intent', 'mission': 'Isolated Luna release study, not product deployment.',
                    'records': records, 'initiatives': [], 'source': {'provider': 'itsaplan', 'captured_at': now(), 'authoritative': False, 'mode': 'offline_snapshot'}}
        write_json(directory / 'context/snapshot.json', snapshot)
        write_json(directory / 'context/map.json', {'scopes': {'sayhi/project-intent': {
            'snapshot': str(directory / 'context/snapshot.json'), 'enrollment_directory': str(directory / 'presence'),
            'report_directory': str(directory / 'reports')}}})
    elapsed=time.monotonic()-start
    timing={'measurement':'monotonic setup process duration','resume':False}
    if resume:
        born=int(call('stat','-c','%W',directory))
        timing={'measurement':'filesystem birth time through completed setup, including interruption and operator recovery',
                'resolution_seconds':1,'resume':True,'recovery_process_seconds':elapsed,'directory_birth_epoch':born}
        elapsed=time.time()-born if born>0 else None
    write_json(directory / 'setup.json', {'arm': arm, 'setup_seconds': elapsed,'setup_timing':timing,
        'at': now(), 'status_base': call('git', '-C', directory / 'status/repository', 'rev-parse', 'HEAD'),
        'support_base': call('git', '-C', support, 'rev-parse', 'HEAD'), 'provider_records': len(records)})


def prompt(arm, role, stage, findings=''):
    directory, checkout = paths(arm, role)
    roles = {'storage': 'Own new snapshot persistence modules, migrations, src/state.mjs, and storage tests.',
             'api': 'Own src/worker.mjs, added API modules and API tests. Coordinate storage imports; do not edit storage-owned files.',
             'browser': 'Own src/ui.mjs, src/history-browser.mjs, added browser modules and browser tests.',
             'export': 'Own the separate support-tools repository and its export CLI/tests.',
             'integration': 'Integrate only the delivered owner work in both repositories; resolve genuine integration conflicts. Do not independently implement missing owner features; request bounded owner corrections.'}
    peers = '\n'.join(f'{r}: {paths(arm,r)[1]}' for r in ROLES)
    text = f'''You are a {MODEL} medium worker in a disposable product release exercise.
Read {directory/'instructions/CONTRACT.md'} and CURRENT_REVISION.md beside it, and your repository README/AGENTS explicitly.
Your owner role: {role}. {roles[role]}
Stage: {stage}. No global context or previous trials are available. Your exact checkout is {checkout}.
Peer checkouts (read-only; do not write them):\n{peers}
Ordinary shared coordination: {directory/'notes'}. Write your own {role}.md; read peer notes and source as useful.
All owners share the same facts. No mandatory handshake; keep progressing on independent work.
Tools: /usr/bin/node, Git, python3, curl; browser {ROOT/'tools/common/browser/headless_shell'}.
Browser evaluator Python: {ROOT/'tools/common/py/bin/python'}.
Common readonly acceptance: {directory/'acceptance'}.
API/export check: TRIAL_CHECKOUT=/path/to/status SUPPORT_CHECKOUT=/path/to/support node --test {directory/'acceptance/luna_release_acceptance.mjs'}
Browser check: TRIAL_CHECKOUT=/path/to/status BROWSER_EXECUTABLE={ROOT/'tools/common/browser/headless_shell'} {ROOT/'tools/common/py/bin/python'} {directory/'acceptance/luna_release_browser.py'}
Use your checkout and read-only peers to run checks where possible; incomplete integration is not a passing feature.
Run npm test and npm run check. You may make LOCAL commits of your own product changes.
Keep your assigned branch. Shared Git metadata supports normal worktree commits, but you must not change/delete peer branches or rewrite their commits.
Do not commit TRIAL_HANDOFF.md, CORRECTIONS.json, DELIVERY.json, generated evidence, trial instructions or coordination files.
Keep generated evidence and any PI report input JSON beneath {directory/'notes'/(role+'-evidence')}, not in product source.
Write TRIAL_HANDOFF.md with exact commits/files, interface decisions, tests/actual failures, current revision, remaining work and successor instructions.
Finish even if incomplete, preserving evidence. No other agents, external services except normal model transport, production calls, schedules, deployments, remote Git, credential reads, host skills, other trial arms or prior conversations.
Your time allowance is {LIMITS.get(stage,1800)//60} minutes. No stronger model will repair your implementation.
'''
    if stage == 'initial':
        text += '\nImplement revision1 and hand off at its first candidate. Do not implement the later revision2 early; R2-specific acceptance failures are expected at this checkpoint and must not cause premature implementation. The first-stage checkpoint is when all initial owners finish or reach the fixed deadline, not after the coordinator inspects which arm is winning.\n'
    if stage in ('revision', 'correction'):
        text += '\nRequired revision2 is now active: current retention10 applies retroactively to old snapshots; existing expiry must never extend. Re-read current shared instructions and peer handoffs. Old revision1 results alone are insufficient.\n'
    if role == 'integration':
        text += f'''\nYou also own writable {directory/'support/integration'}.
Status owner branches storage, api and browser share your Git repository; merge those LOCAL branches.
Support export and integration share the support repository; merge export there.
Read the original owner handoffs from peer checkouts. Record missing deliverables rather than fabricating them.
Write CORRECTIONS.json with {{"requests":[{{"owner":"storage|api|browser|export","reason":"concrete acceptance failure","preserve":"required constraints"}}]}}; an empty list means no owner correction requested.
Write DELIVERY.json with exact status/support HEADs, current revision and actual validation state.
Do not change evaluator files or supply implementation for absent owner features.\n'''
    if findings:
        text += '\nObserved correction requests (not solutions):\n' + findings + '\n'
    if arm.endswith('aware'):
        alias = 'PI-LUNA03-' + arm.upper() + '-' + role.upper()
        session = 'luna03-' + arm + '-' + role + ('-successor' if role == 'storage' and stage != 'initial' else '')
        pi = f"{ROOT/'tools/pi/project-intent'} --worker-config {directory/'context/map.json'}"
        touching={'storage':'--touching-path src/state.mjs --touching-path migrations',
                  'api':'--touching-path src/worker.mjs',
                  'browser':'--touching-path src/ui.mjs --touching-path src/history-browser.mjs',
                  'export':'--touching-path bin --touching-path package.json',
                  'integration':'--touching-path .'}[role]
        text += f'''\nAdditional channel: actual Project Intent, restricted to this arm. All facts also exist in ordinary instructions/notes.
Use {pi} onboard --workstream {alias}; inspect context, then {pi} enroll --workstream {alias} --session {session} --access edit {touching} --touching-seam study03/public-contract --working "bounded actual work".
Update declared paths to match actual edits, including newly added modules/tests. This declaration grants no ownership of another role's files.
Revisit start when dependency context or revision changes. It is an observation, not execution authority.
Report using a JSON FILE: {{"summary":"actual result","readiness":{{"implementation":"actual state"}},"next_step":"remaining work","evidence":[{{"ref":"path","sha256":"64 lowercase hex"}}]}}.
Minimal summary/next_step is allowed if no evidence file exists. Invoke {pi} report --workstream {alias} --session {session} --input /path/to/file.json.
Do not pass inline JSON to --input. Reports are LOCAL, not remote publication. No credentials or global scope map.
At handoff release with {pi} enroll --workstream {alias} --session {session} --inactive.
If PI fails, retain the error and continue authorized work through ordinary notes. There is no reporting quota.\n'''
    return text


def execute(arm, role, stage, *, resume=None, findings='', seconds=None, task=None):
    directory, checkout = paths(arm, role)
    label = stage + '-' + role
    artifacts = directory / 'artifacts' / label
    artifacts.mkdir(exist_ok=False)
    session_label = role + ('-successor' if role == 'storage' and stage != 'initial' else '')
    home = ROOT / 'session-homes' / arm / session_label
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    args = [str(ROOT/'tools/common/codex-bin/codex'), '-a', 'never', 'exec',
            '--ignore-user-config', '--ignore-rules', '--enable', 'skip_host_skill_discovery',
            '--disable', 'plugins', '--disable', 'apps', '--disable', 'memories', '--disable', 'multi_agent',
            '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
            '-c', 'model_context_window=200000', '-c', 'model_auto_compact_token_limit=160000',
            '-c', 'model_reasoning_effort="medium"', '-m', MODEL, '-s', 'danger-full-access', '-C', str(checkout)]
    if resume:
        args += ['resume', '--ignore-user-config', '--ignore-rules', '-m', MODEL,
                 '--enable', 'skip_host_skill_discovery', '--disable', 'plugins', '--disable', 'apps',
                 '--disable', 'memories', '--disable', 'multi_agent',
                 '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
                 '-c', 'model_context_window=200000', '-c', 'model_auto_compact_token_limit=160000',
                 '-c', 'model_reasoning_effort="medium"', '--json', '-o', str(artifacts/'final.md'), resume, '-']
    else:
        args += ['--json', '-o', str(artifacts/'final.md'), '-']
    common_git = Path(call('git', '-C', checkout, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    readonly = [ROOT/'tools/common', directory/'instructions', directory/'acceptance']
    writable = [artifacts, directory/'notes', common_git]
    readonly += [paths(arm,r)[1] for r in ROLES if r != role]
    if role == 'integration':
        writable += [directory/'support/integration', directory/'support/repository/.git']
    elif role != 'export':
        readonly += [directory/'support/repository/.git']
    else:
        readonly += [directory/'status/repository/.git']
    if arm.endswith('aware'):
        readonly += [ROOT/'tools/pi', directory/'context']
        writable += [directory/'presence', directory/'reports']
    launch = isolated(ROOT, checkout, args, readonly=readonly, writable=writable)
    if AUTH.is_symlink() or AUTH.stat().st_mode & 0o077:
        raise ValueError('Private regular CLI auth required')
    launch[1:1] = ['--bind', str(home), '/home/worker/.codex', '--ro-bind', str(AUTH), '/home/worker/.codex/auth.json']
    text = task if task is not None else prompt(arm, role, stage.split('-')[0], findings)
    write(artifacts/'prompt.txt', text)
    write_json(artifacts/'command.json', launch)
    started = time.monotonic()
    before_handoff = sha(checkout/'TRIAL_HANDOFF.md') if (checkout/'TRIAL_HANDOFF.md').exists() else None
    expired = False
    with (artifacts/'events.jsonl').open('x') as out, (artifacts/'stderr.txt').open('x') as err:
        process = subprocess.Popen(launch, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True, start_new_session=True)
        try:
            process.communicate(text, timeout=seconds or LIMITS[stage.split('-')[0]])
        except subprocess.TimeoutExpired:
            expired = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    thread = None
    usage = {}
    for line in (artifacts/'events.jsonl').read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') == 'thread.started':
            thread = event.get('thread_id')
        if event.get('type') == 'turn.completed':
            for k,v in event.get('usage',{}).items():
                usage[k] = usage.get(k,0) + v
    handoff = checkout/'TRIAL_HANDOFF.md'
    if handoff.exists():
        shutil.copyfile(handoff, artifacts/'handoff.md')
    observed = session_metadata(home, thread)
    result = {'arm': arm, 'role': role, 'stage': stage, 'model': MODEL, 'effort': 'medium',
              'observed_model_settings': observed,
              'model_verified': observed.get('model') == MODEL and observed.get('effort') == 'medium'
                                and observed.get('effective_context_window') == 190000,
              'exit_code': process.returncode, 'timeout': expired, 'elapsed_seconds': time.monotonic()-started,
              'thread_id': thread, 'resumed_from': resume, 'usage': usage,
              'head': call('git','-C',checkout,'rev-parse','HEAD'), 'handoff_exists': handoff.exists(),
              'handoff_updated': handoff.exists() and sha(handoff) != before_handoff,
              'dirty': call('git','-C',checkout,'status','--porcelain'), 'at': now()}
    write_json(artifacts/'execution.json', result)
    print(json.dumps({k:result[k] for k in ('arm','role','stage','exit_code','timeout','elapsed_seconds','thread_id')}),flush=True)
    return result


def session_metadata(home, thread):
    # Read only this exact disposable session's typed metadata, not arbitrary logs.
    if not thread or any(c not in '0123456789abcdef-' for c in thread):
        return {}
    logs=list((home/'sessions').rglob('*'+thread+'.jsonl'))
    if len(logs)!=1:
        return {}
    observed={}
    for line in logs[0].read_text().splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        payload=event.get('payload',{})
        if event.get('type')=='turn_context':
            observed={'model':payload.get('model'),'effort':payload.get('effort')}
        if event.get('type')=='event_msg' and payload.get('type')=='token_count' and payload.get('info'):
            observed['effective_context_window']=payload['info'].get('model_context_window')
    return observed


def validate_resume(arm):
    if arm not in PREFLIGHT_ARMS:
        raise ValueError('Only exact preflight sessions may be used for launcher validation')
    directory=ROOT/'arms'/arm
    previous=read_json(directory/'preflight.json')
    result=execute(arm,'api','preflight-resume-verified',resume=previous['execution']['thread_id'],seconds=180,
        task='Continue the preflight, without tools or reading files. Reply only with the private conversation-only phrase I asked you to remember during the original preflight.')
    final=(directory/'artifacts/preflight-resume-verified-api/final.md').read_text().strip()
    write_json(directory/'resume-validation.json',{'at':now(),'execution':result,
        'passed':result['model_verified'] and result['exit_code']==0 and result['thread_id']==previous['execution']['thread_id'] and final=='continuity-cedar-43',
        'reason':'Original resume reverted context size to CLI default; original failed setting evidence preserved. Corrected resume reapplies settings after subcommand.'})


def preflight(arm):
    if arm not in PREFLIGHT_ARMS:
        raise ValueError('Preflight requires a dedicated disposable preflight arm')
    directory, checkout = paths(arm, 'api')
    instructions = f'''This is a neutral harness capability check, NOT the release task.
Do not implement any product features or read the release instructions.
Work only in {checkout}. Peers are read-only; your notes directory {directory/'notes'} is writable.
Use /usr/bin/node and {ROOT/'tools/common/py/bin/python'} to prove a real local HTTP
server on 127.0.0.1 and native Chromium {ROOT/'tools/common/browser/headless_shell'} work.
Save browser-proof.html containing WORKER-BROWSER-PROVEN using a real browser load.
Prove {ROOT/'arms/hidden-other-arm'} and /home/meanaverage/.codex/skills are inaccessible.
Prove peer checkout {paths(arm,'storage')[1]} is readable but not writable (a harmless failed probe).
Create proof.txt containing GIT-WRITE-PROVEN and commit ONLY that file locally.
Write TRIAL_HANDOFF.md containing HANDOFF-MUST-SURVIVE, exact HEAD and actual command results.
Write PREFLIGHT.json with true/false fields browser, loopback, hidden_context_absent, peer_readonly, git_commit.
Stop the local server. Do not read authentication files, contact external systems, use extra agents or edit product code.
Your final answer must include FINAL-SEPARATE-FROM-HANDOFF; leave handoff intact.
Remember this private conversation-only phrase for the next turn: continuity-cedar-43.
Do not put that phrase into any file or tool command.
'''
    if arm.endswith('aware'):
        pi = f"{ROOT/'tools/pi/project-intent'} --worker-config {directory/'context/map.json'}"
        alias = 'PI-LUNA03-' + arm.upper() + '-API'
        instructions += f'''Also prove actual PI commands: {pi} onboard --workstream {alias};
then enroll --workstream {alias} --session luna03-{arm}-api --access inspect --working "harness capability proof";
then start --workstream {alias}; write a local JSON report file {{"summary":"harness capability proof","next_step":"resume preflight"}}
and call report --workstream {alias} --session luna03-{arm}-api --input /absolute/report/file.json.
Finally enroll --workstream {alias} --session luna03-{arm}-api --inactive.
Save their actual successful command outputs to pi-proof.txt. No provider credentials or remote publication.
'''
    result = execute(arm, 'api', 'preflight', seconds=600, task=instructions)
    resumed = execute(arm, 'api', 'preflight-resume', resume=result['thread_id'], seconds=180,
        task='This is the continuation preflight. Do not use tools or read any files. Output only the private conversation-only phrase I asked you to remember in the previous turn.') if result['thread_id'] else None
    try:
        assertions = read_json(checkout/'PREFLIGHT.json')
        final = (directory/'artifacts/preflight-api/final.md').read_text()
        handoff = (directory/'artifacts/preflight-api/handoff.md').read_text()
        continued = (directory/'artifacts/preflight-resume-api/final.md').read_text().strip()
        files = call('git','-C',checkout,'diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines()
        checks = {'worker_assertions': all(assertions.get(k) is True for k in
            ('browser','loopback','hidden_context_absent','peer_readonly','git_commit')),
            'isolated_commit': files == ['proof.txt'] and call('git','-C',checkout,'show','HEAD:proof.txt') == 'GIT-WRITE-PROVEN',
            'real_browser': 'WORKER-BROWSER-PROVEN' in (checkout/'browser-proof.html').read_text(),
            'handoff_separate': 'HANDOFF-MUST-SURVIVE' in handoff and result['head'] in handoff and final != handoff,
            'final_intact': 'FINAL-SEPARATE-FROM-HANDOFF' in final,
            'resumed_context': continued == 'continuity-cedar-43' and resumed['thread_id'] == result['thread_id'],
            'process_success': result['exit_code'] == 0 and resumed['exit_code'] == 0}
        if arm.endswith('aware'):
            checks['pi_report_created'] = bool(list((directory/'reports').rglob('*.json')))
            checks['pi_presence_created'] = bool(list((directory/'presence').rglob('*.json')))
            checks['pi_actual_commands'] = (checkout/'pi-proof.txt').is_file()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks = {'artifact_error': str(exc), 'complete': False}
    report = {'arm': arm, 'at': now(), 'checks': checks,
              'passed': all(value is True for value in checks.values()), 'execution': result, 'resume': resumed}
    write_json(directory/'preflight.json', report)
    print(json.dumps(report, indent=2), flush=True)
    return report


def revision(arm):
    directory = ROOT/'arms'/arm
    write(directory/'instructions/CURRENT_REVISION.md', 'Current required revision: 2. Retention10 applies retroactively; never extend stored expiry. Revalidate all clients and old snapshot references.\n')
    if arm.endswith('aware'):
        config = read_json('/home/meanaverage/sayhi/state/project-intent/config.json')
        _, provider = configured(config, 'sayhi/project-intent')
        snapshot = read_json(directory/'context/snapshot.json')
        for record in snapshot['records']:
            native = provider.resolve(record['provider_identifier'])
            revised = dict(native['record'])
            revised['revision'] = '2'
            revised['scope'] = revised['scope'].replace('Current required revision: 1.', 'Current required revision: 2. Retention10 now retroactive; do not reuse revision1 evidence as acceptance.')
            revised['readiness'] = {**revised['readiness'], 'implementation': 'revision2-revalidation-required'}
            packet = {'scope':'sayhi/project-intent','confirmed':True,'native_identifier':native['identifier'],
                      'expected_digest':native['metadata_digest'],'record':revised}
            write_json(directory/'context'/ (record['id']+'-revision2.json'),packet)
            result = reconcile(provider,'sayhi/project-intent',packet,config['operator']['journal_directory'])
            if result['state']!='published':
                raise RuntimeError('Revision publication uncertain; do not launch next stage')
            record.update(revised)
        snapshot['source']['captured_at']=now()
        write_json(directory/'context/snapshot.json',snapshot)
    write_json(directory/'revision-event.json',{'revision':2,'at':now(),'replacement_owner':'storage',
        'checkpoint':'all initial owner sessions terminated or reached predeclared timeout; no outcome-selected interruption'})


def run_arm(arm):
    require_preflight()
    if arm in ORDER:
        require_frozen(arm)
    elif arm not in REHEARSAL_ARMS:
        raise ValueError('Only rehearsal/scored arms are product candidates')
    directory = ROOT/'arms'/arm
    if (directory/'execution-start.json').exists():
        raise ValueError('Arm already started; preserve failure and resume explicitly, never overwrite')
    write_json(directory/'execution-start.json',{'at':now(),'model':MODEL,'effort':'medium','input_hashes':inputs()})
    begin=time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        initial=dict(zip(ROLES,pool.map(lambda r:execute(arm,r,'initial'),ROLES)))
    ref_violations=check_owner_refs(arm,'initial',initial)
    if any(not r['thread_id'] or not r['model_verified'] for r in initial.values()):
        write_json(directory/'arm-outcome.json',{'state':'harness-or-transport-failure','initial':initial})
        return
    revision(arm)
    with ThreadPoolExecutor(max_workers=4) as pool:
        revised=dict(zip(ROLES,pool.map(lambda r:execute(arm,r,'revision',resume=None if r=='storage' else initial[r]['thread_id']),ROLES)))
    ref_violations += check_owner_refs(arm,'revision',revised)
    if any(not r['thread_id'] or not r['model_verified'] for r in revised.values()):
        write_json(directory/'arm-outcome.json',{'state':'harness-or-transport-failure','initial':initial,'revision':revised})
        return
    integrated=execute(arm,'integration','integration')
    # Corrections use actual integrator findings only; no coordinator-crafted solutions.
    corrections=[]
    current_owners=dict(revised)
    procedure_failures=list(ref_violations)
    for number in (1,2):
        if integrated['exit_code'] != 0 or not integrated['thread_id'] or not integrated['model_verified']:
            procedure_failures.append('Integration process or model metadata failed at '+integrated['stage'])
            break
        path=directory/'status/integration/CORRECTIONS.json'
        if not path.exists():
            procedure_failures.append('Missing integration correction declaration at '+integrated['stage'])
            break
        try:
            requests=read_json(path)['requests']
        except (ValueError,KeyError):
            procedure_failures.append('Malformed integration correction declaration at '+integrated['stage'])
            break
        if not isinstance(requests,list):
            procedure_failures.append('Correction requests must be a list at '+integrated['stage'])
            break
        if not requests:
            break
        if any(not isinstance(r,dict) or r.get('owner') not in ROLES or any(
            not isinstance(r.get(key),str) or not r[key].strip() for key in ('reason','preserve')) for r in requests):
            procedure_failures.append('Invalid correction request at '+integrated['stage'])
            break
        write_json(directory/'artifacts'/f'correction-requests-{number}.json', requests)
        owners=[r for r in ROLES if any(x['owner']==r for x in requests)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda r:execute(arm,r,f'correction-{number}',
                resume=current_owners[r]['thread_id'], findings=json.dumps([x for x in requests if x['owner']==r]),seconds=LIMITS['correction']),owners))
        corrections.extend(results)
        for result in results:
            current_owners[result['role']] = result
            if not result['model_verified'] or result['exit_code'] != 0:
                procedure_failures.append('Correction process or model metadata failed for '+result['role'])
        procedure_failures += check_owner_refs(arm,f'correction-{number}',current_owners)
        integrated=execute(arm,'integration',f'integration-{number}',resume=integrated['thread_id'])
    if integrated['exit_code'] != 0 or not integrated['model_verified']:
        procedure_failures.append('Final integration process/model verification failed')
    try:
        remaining=read_json(directory/'status/integration/CORRECTIONS.json')['requests']
        if not isinstance(remaining,list) or remaining:
            procedure_failures.append('Final correction declaration is invalid or requests remain after bounded rounds')
    except (OSError,ValueError,KeyError,TypeError):
        procedure_failures.append('Final correction declaration missing or malformed')
    write_json(directory/'arm-outcome.json',{'state':'procedure-incomplete' if procedure_failures else 'delivered-awaiting-independent-gates',
        'procedure_failures':procedure_failures,
        'elapsed_seconds':time.monotonic()-begin,'initial':initial,'revision':revised,'integration':integrated,'corrections':corrections})


def check_owner_refs(arm, stage, executions):
    directory=ROOT/'arms'/arm
    observed={}
    failures=[]
    for role,execution in executions.items():
        product='support' if role=='export' else 'status'
        try:
            actual=call('git','-C',directory/product/'repository','rev-parse','refs/heads/'+role)
        except subprocess.CalledProcessError:
            actual=None
        observed[role]={'expected_own_head':execution['head'],'observed_branch':actual}
        if actual != execution['head']:
            failures.append(f'Owner branch/head disagreement at {stage}: {role}; retained for protocol review')
    write_json(directory/'artifacts'/(stage+'-owner-refs.json'),observed)
    return failures


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['tools','setup','run','preflight','validate-resume','gates','review','freeze','summarize'])
    parser.add_argument('--arm',choices=[BASELINE_ARM,*PREFLIGHT_ARMS,*REHEARSAL_ARMS,*ORDER])
    parser.add_argument('--resume-setup',action='store_true',help='Resume only unchanged unstarted partial native setup from exact saved packets')
    args=parser.parse_args()
    if args.action=='tools': setup_tools()
    elif args.action=='setup': setup_arm(args.arm,resume=args.resume_setup)
    elif args.action=='preflight': preflight(args.arm)
    elif args.action=='validate-resume': validate_resume(args.arm)
    elif args.action=='freeze': freeze()
    elif args.action in ('gates','review','summarize'):
        from experiments import luna_release_evaluation as evaluation
        import sys
        study=sys.modules[__name__]
        if args.arm in ORDER: require_frozen(args.arm)
        if args.action=='gates': evaluation.gates(study,args.arm)
        elif args.action=='review': evaluation.review(study,args.arm)
        else: print(json.dumps(evaluation.summarize(study),indent=2))
    else: run_arm(args.arm)


if __name__=='__main__': main()
