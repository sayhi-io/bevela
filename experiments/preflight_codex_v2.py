"""Fresh Codex worker preflight in the outer context-isolation harness.

Explicitly maps only its operator-authorized CLI auth file, never the global home,
skills/configs/transcripts. Auth remains outside evidence and is not copied.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from experiments.isolation_v2 import command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-bin-directory', type=Path, required=True)
    parser.add_argument('--auth-file', type=Path, required=True)
    parser.add_argument('--browser-directory', type=Path, required=True)
    parser.add_argument('--model', default='gpt-6-astra')
    args = parser.parse_args()
    auth = args.auth_file
    if auth.is_symlink() or not auth.is_file() or auth.stat().st_mode & 0o077:
        parser.error('Expected an owner-private regular CLI auth file')
    root = Path(tempfile.mkdtemp(prefix='pi-codex-worker-v2-'))
    (root/'DISPOSABLE_TRIAL').touch()
    worker = root/'worker'; worker.mkdir()
    tools = root/'tools'; tools.mkdir()
    shutil.copytree(args.codex_bin_directory, tools/'codex-bin')
    shutil.copytree(args.browser_directory, tools/'browser')
    artifacts = root/'artifacts'; artifacts.mkdir()
    hidden = root/'other-arm'; hidden.mkdir()
    (hidden/'note').write_text('not worker context')
    subprocess.run(['git','init',str(worker)],check=True,capture_output=True)
    for key,value in [('user.name','Preflight worker'),('user.email','trial@example.invalid')]:
        subprocess.run(['git','-C',str(worker),'config',key,value],check=True)
    subprocess.run(['git','-C',str(worker),'commit','--allow-empty','-m','preflight base'],check=True,capture_output=True)
    binary = tools/'codex-bin/codex'
    cli = [str(binary),'-a','never','exec','--ignore-user-config','--ignore-rules',
           '--ephemeral','--enable','skip_host_skill_discovery','--disable','plugins',
           '--disable','apps','--disable','memories','--disable','multi_agent',
           '-c','project_doc_max_bytes=0','-m',args.model,
           '-c','model_reasoning_effort="medium"','-s','danger-full-access',
           '-C',str(worker),'--json','-o',str(artifacts/'final.md'),'-']
    launch = command(root,worker,cli,readonly=[tools],writable=[artifacts])
    # This explicit auth mount is NOT a general resource/mount escape hatch.
    launch[1:1] = ['--dir','/home/worker/.codex','--ro-bind',str(auth.resolve()),
                    '/home/worker/.codex/auth.json']
    prompt = f'''Run a disposable harness preflight, not a product task.
You are already enclosed by an outer filesystem namespace; global home/context are absent.
Prove a local HTTP server bound to 127.0.0.1 can serve a page and that
{tools/'browser/headless_shell'} --no-sandbox --disable-gpu --dump-dom can read it.
The page must contain WORKER-BROWSER-PROVEN. Save DOM to browser-proof.html.
Prove {hidden} and /home/meanaverage/.codex/skills are inaccessible; do not seek credentials.
Create proof.txt with GIT-WRITE-PROVEN and commit only proof.txt locally.
Write TRIAL_HANDOFF.md with HANDOFF-MUST-SURVIVE, exact HEAD, actual commands and results.
Write PREFLIGHT.json with booleans browser, loopback, hidden_context_absent and git_commit.
Stop your local server. No external calls except your normal model transport, no extra agents.
Your final answer must be FINAL-SEPARATE-FROM-HANDOFF. Do not overwrite the handoff.
'''
    (artifacts/'prompt.txt').write_text(prompt)
    (artifacts/'command.json').write_text(json.dumps(launch,indent=2)+'\n')
    started=time.monotonic()
    with (artifacts/'events.jsonl').open('x') as out, (artifacts/'stderr.txt').open('x') as err:
        result=subprocess.run(launch,input=prompt,text=True,stdout=out,stderr=err,timeout=900)
    report={'root':str(root),'exit_code':result.returncode,
            'elapsed_seconds':round(time.monotonic()-started,3),
            'model':args.model,'effort':'medium','condition':'neutral harness preflight'}
    p=worker/'PREFLIGHT.json'
    try:
        report['worker_assertions']=json.loads(p.read_text()) if p.exists() else None
    except (ValueError, OSError) as exc:
        report['worker_assertions']=None
        report['artifact_error']=str(exc)
    report['handoff_exists']=(worker/'TRIAL_HANDOFF.md').is_file()
    report['final_exists']=(artifacts/'final.md').is_file()
    report['study_result']=False
    def git(*args):
        return subprocess.check_output(['git','-C',str(worker),*args],text=True).strip()
    report['verified_commit_files']=git('diff-tree','--root','--no-commit-id','--name-only','-r','HEAD').splitlines()
    handoff=worker/'TRIAL_HANDOFF.md'
    final=artifacts/'final.md'
    dom=worker/'browser-proof.html'
    report['passed']=(result.returncode==0
        and isinstance(report['worker_assertions'],dict)
        and all(report['worker_assertions'].get(k) is True for k in
                ['browser','loopback','hidden_context_absent','git_commit'])
        and report['verified_commit_files']==['proof.txt']
        and git('show','HEAD:proof.txt')=='GIT-WRITE-PROVEN'
        and handoff.exists() and 'HANDOFF-MUST-SURVIVE' in handoff.read_text()
        and git('rev-parse','HEAD') in handoff.read_text()
        and final.exists() and 'FINAL-SEPARATE-FROM-HANDOFF' in final.read_text()
        and final.read_text() != handoff.read_text()
        and dom.exists() and 'WORKER-BROWSER-PROVEN' in dom.read_text())
    (artifacts/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__=='__main__': main()
