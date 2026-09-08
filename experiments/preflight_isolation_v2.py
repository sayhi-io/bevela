"""Exercise browser, loopback, Git and context isolation in the new outer harness.

This deterministic prerequisite is NOT the actual model-worker preflight or a study.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from experiments.isolation_v2 import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser-directory', type=Path, required=True)
    args = parser.parse_args()
    source = args.browser_directory.resolve(strict=True)
    if not (source / 'headless_shell').is_file():
        parser.error('Expected directory containing headless_shell')
    root = Path(tempfile.mkdtemp(prefix='pi-isolation-browser-v2-'))
    (root/'DISPOSABLE_TRIAL').touch()
    worker = root/'worker'; worker.mkdir()
    browser = root/'browser'
    shutil.copytree(source, browser)
    hidden = root/'other-arm'; hidden.mkdir()
    (hidden/'private-note').write_text('must not enter worker context')
    code = '''import http.server, threading, subprocess, pathlib, json
p=pathlib.Path
assert not p(%r).exists()
assert not p('/home/meanaverage/.codex/skills').exists()
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200); self.end_headers()
  self.wfile.write(b'<html><body id="proof">worker-local-browser</body></html>')
 def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 result=subprocess.run([%r,'--no-sandbox','--disable-gpu','--dump-dom',
  'http://127.0.0.1:'+str(server.server_port)],text=True,capture_output=True,timeout=30)
 assert result.returncode==0, result.stderr
 assert 'worker-local-browser' in result.stdout, result.stdout
 p('browser-dom.html').write_text(result.stdout)
finally: server.shutdown(); server.server_close()
def git(*args): return subprocess.check_output(['git',*args],text=True).strip()
git('init'); git('config','user.name','Harness preflight'); git('config','user.email','trial@example.invalid')
p('proof.txt').write_text('GIT-WRITE-PROVEN')
git('add','proof.txt'); git('commit','-m','preflight proof')
p('TRIAL_HANDOFF.md').write_text('HANDOFF-MUST-SURVIVE')
p('final-message.md').write_text('SEPARATE-FINAL-RESPONSE')
print(json.dumps({'head':git('rev-parse','HEAD'),'browser':True,'loopback':True,'hidden_context_absent':True}))
''' % (str(hidden), str(browser/'headless_shell'))
    result = run(root, worker, ['python3','-c',code], readonly=[browser], timeout=90)
    evidence = {'exit_code':result.returncode, 'stdout':result.stdout,
                'stderr':result.stderr, 'root':str(root),
                'browser_sha256':hashlib.sha256((browser/'headless_shell').read_bytes()).hexdigest(),
                'model_worker_preflight':'not-run',
                'network':'host network shared; not network isolation',
                'browser_sandbox':'outer namespace; Chromium internal sandbox disabled'}
    (root/'preflight.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
    raise SystemExit(result.returncode)


if __name__ == '__main__': main()
