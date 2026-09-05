from datetime import timedelta
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from project_intent.enrollment import registration, read_registrations, telemetry_path, find_codex_session
from project_intent.model import utcnow, project
from project_intent.runtime import Store, write_json

ROOT=Path(__file__).resolve().parents[1]


class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.directory=self.root/'enrolled';self.directory.mkdir()
        self.logs=self.root/'logs';self.logs.mkdir()
        self.path=self.logs/'worker.jsonl'
        self.path.write_text(json.dumps({'type':'session_meta','payload':{'id':'worker'}})+'\n')
        self.snapshot=json.loads((ROOT/'.project-intent/snapshot.json').read_text())
        self.now=utcnow();self.scope=self.snapshot['scope_id']
        self.source={'directory':str(self.directory),'telemetry_roots':[str(self.logs)]}

    def record(self,**kwargs):
        return registration(self.snapshot,'PI-MISSION-01','worker','test',['intent/projection'],[],str(self.path),now=self.now,**kwargs)

    def read(self,**kwargs):
        return read_registrations(self.source,self.scope,{'PI-MISSION-01'},now=kwargs.get('now',self.now))

    def test_enroll_and_renew_preserves_attribution_boundary(self):
        first=self.record();second=registration(self.snapshot,'PI-MISSION-01','worker','renew',[],[],old=first,now=self.now+timedelta(minutes=20))
        self.assertEqual(first['claimed_at'],second['claimed_at'])
        self.assertEqual(second['telemetry']['since'],first['claimed_at'])
        self.assertGreater(second['expires_at'],first['expires_at'])

    def test_expired_renewal_starts_new_boundary(self):
        first=self.record();second=registration(self.snapshot,'PI-MISSION-01','worker','renew',[],[],old=first,now=self.now+timedelta(hours=2))
        self.assertNotEqual(first['claimed_at'],second['claimed_at'])

    def test_no_silent_reassignment_or_path_replacement(self):
        first=self.record();first['workstream']='other'
        with self.assertRaises(ValueError):self.record(old=first)
        first=self.record();first['telemetry']['path']='other'
        with self.assertRaises(ValueError):self.record(old=first)

    def test_session_header_and_telemetry_root_checked(self):
        with self.assertRaises(ValueError):telemetry_path(self.path,'other',[self.logs])
        with self.assertRaises(ValueError):telemetry_path(self.path,'worker',[self.directory])
        self.assertEqual(telemetry_path(self.path,'worker',[self.logs]),str(self.path))

    def test_named_discovery_only_and_symlink_rejected(self):
        dated=self.logs/'2026/09/05';dated.mkdir(parents=True)
        target=dated/'rollout-test-worker.jsonl';target.write_bytes(self.path.read_bytes())
        self.assertEqual(find_codex_session(self.logs,'worker'),str(target))
        link=self.logs/'link.jsonl';link.symlink_to(self.path)
        with self.assertRaises(ValueError):telemetry_path(link,'worker',[self.logs])

    def test_discovery_watches_new_files_without_restart(self):
        write_json(self.root/'snapshot.json',self.snapshot)
        config={'scopes':[{'id':self.scope,'label':'test','cache':str(self.root/'snapshot.json'),'enrollment_sources':[self.source]}]}
        store=Store(config)
        self.assertEqual(store.view()[0]['presence'],[])
        write_json(self.directory/'worker.json',self.record())
        state=store.view()[0];self.assertEqual(state['presence'][0]['session'],'worker')
        view=project([state],[self.scope]);a=next(w for w in view['workstreams'] if w['id']=='PI-MISSION-01')['activity']
        self.assertEqual(a['session'],'worker');self.assertEqual(a['status'],'not-observed')
        self.assertNotIn(str(self.path),json.dumps(view))
        self.assertNotIn('worker',json.dumps(project([state],['unrelated'])))

    def test_expiry_and_release_stop_log_read_binding(self):
        write_json(self.directory/'worker.json',self.record())
        records,failures=self.read(now=self.now+timedelta(hours=2))
        self.assertEqual(failures,0);self.assertIsNone(records[0][1])
        write_json(self.directory/'worker.json',self.record(inactive=True))
        self.assertIsNone(self.read()[0][0][1])

    def test_wrong_scope_unknown_work_and_bad_shape_rejected(self):
        for field,value in [('scope','unrelated'),('workstream','MISSING'),('session','../bad'),('claimed_at','bad')]:
            record=self.record();record[field]=value;write_json(self.directory/'worker.json',record)
            self.assertEqual(self.read(),([],1))
        write_json(self.directory/'worker.json',[])
        self.assertEqual(self.read(),([],1))

    def test_bad_telemetry_preserves_presence_but_never_reads_outside_root(self):
        record=self.record();record['telemetry']['path']=str(self.root/'private')
        write_json(self.directory/'worker.json',record)
        records,failures=self.read();self.assertEqual(failures,1)
        self.assertEqual(records[0][0]['session'],'worker');self.assertEqual(records[0][1]['kind'],'unavailable')

    def test_two_workers_have_separate_series(self):
        write_json(self.root/'snapshot.json',self.snapshot)
        config={'scopes':[{'id':self.scope,'label':'test','cache':str(self.root/'snapshot.json'),'enrollment_sources':[self.source]}]}
        first=self.record();write_json(self.directory/'worker.json',first)
        second=copy.deepcopy(first);second['session']='second';path=self.logs/'second.jsonl'
        path.write_text(json.dumps({'type':'session_meta','payload':{'id':'second'}})+'\n');second['telemetry']['path']=str(path)
        write_json(self.directory/'second.json',second)
        activity=Store(config).view()[0]['activity']['PI-MISSION-01']
        self.assertEqual({a['session'] for a in activity['sessions']},{'worker','second'})
        self.assertEqual(activity['points'],[])

    def test_cli_no_provider_credentials_and_release(self):
        write_json(self.root/'snapshot.json',self.snapshot)
        command=[sys.executable,'-m','project_intent.cli','enroll','--snapshot',str(self.root/'snapshot.json'),'--workstream','PI-MISSION-01','--session','worker','--directory',str(self.directory)]
        result=subprocess.run(command+['--telemetry-file',str(self.path),'--working','real work'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['telemetry'],'registered')
        result=subprocess.run(command+['--inactive'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        saved=json.loads((self.directory/'worker.json').read_text())
        self.assertEqual(saved['status'],'inactive');self.assertEqual(saved['working'],'real work')

    def test_missing_assignment_and_bad_session_fail(self):
        with self.assertRaises(ValueError):registration(self.snapshot,'MISSING','worker','',[],[])
        with self.assertRaises(ValueError):registration(self.snapshot,'PI-MISSION-01','../bad','',[],[])

    def test_credential_free_scope_map_cli(self):
        write_json(self.root/'snapshot.json',self.snapshot)
        write_json(self.root/'worker.json',{'scopes':{self.scope:{'snapshot':str(self.root/'snapshot.json'),'enrollment_directory':str(self.directory)}}})
        command=[sys.executable,'-m','project_intent.cli','enroll','--worker-config',str(self.root/'worker.json'),'--scope',self.scope,'--workstream','PI-MISSION-01','--session','worker']
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['telemetry'],'not-connected')
        self.assertTrue((self.directory/'worker.json').exists())

    def test_registration_symlink_and_oversized_record_rejected(self):
        target=self.root/'target.json';write_json(target,self.record())
        link=self.directory/'worker.json';link.symlink_to(target)
        self.assertEqual(self.read(),([],1))
        link.unlink();link.write_text(' ' * 65537)
        self.assertEqual(self.read(),([],1))
