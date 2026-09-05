import base64
import copy
from datetime import timedelta
import hashlib
from http.client import IncompleteRead
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from project_intent.model import project, utcnow, validate_snapshot, valid_presence
from project_intent.runtime import Store, write_json
from project_intent.provider import ItsAPlan
from project_intent.server import handler

ROOT=Path(__file__).resolve().parents[1]


class SnapshotCase(unittest.TestCase):
    def setUp(self):
        self.snapshot=json.loads((ROOT/'.project-intent/snapshot.json').read_text())
        self.scope=self.snapshot['scope_id']
        self.state={'id':self.scope,'label':'Project Intent','snapshot':self.snapshot,'provider_status':'live'}


class ProjectionTests(SnapshotCase):
    def test_real_snapshot_valid(self):
        validate_snapshot(self.snapshot)
        view=project([self.state],[self.scope])
        self.assertTrue(view['workstreams']);self.assertTrue(view['architecture'])
        self.assertTrue(view['read_only'])

    def test_filter_precedes_every_aggregate(self):
        other=copy.deepcopy(self.state);other['id']='other/secret'
        other['snapshot']['mission']='DO-NOT-DISCLOSE'
        other['snapshot']['records'][0]['statement']='DO-NOT-DISCLOSE'
        view=project([self.state,other],[self.scope])
        self.assertNotIn('DO-NOT-DISCLOSE',json.dumps(view))
        self.assertEqual([s['id'] for s in view['scopes']],[self.scope])
        with self.assertRaises(PermissionError):project([self.state,other],[self.scope],'other/secret')

    def test_same_boundary_does_not_leak_architecture_across_scopes(self):
        other=copy.deepcopy(self.state);other['id']='other/product'
        view=project([self.state,other],[self.scope,'other/product'])
        for w in view['workstreams']:
            self.assertTrue(all(c['invariant'].startswith(w['scope_id']+':') for c in w['claims']))

    def test_explicit_cross_scope_applicability_requires_both_scope_grants(self):
        other=copy.deepcopy(self.state);other['id']='other/product'
        invariant=next(r for r in other['snapshot']['records'] if r['kind']=='invariant')
        invariant['applies_to']=[{'scope':self.scope,'boundaries':invariant['boundaries']}]
        broad=project([self.state,other],[self.scope,'other/product'],self.scope)
        narrow=project([self.state,other],[self.scope],self.scope)
        self.assertTrue(any(a['scope']=='other/product' for a in broad['architecture']))
        self.assertFalse(any(a['scope']=='other/product' for a in narrow['architecture']))

    def test_imported_architecture_carries_source_outage_and_age(self):
        other=copy.deepcopy(self.state);other['id']='other/shared';other['provider_status']='unavailable'
        invariant=next(r for r in other['snapshot']['records'] if r['kind']=='invariant')
        invariant['applies_to']=[{'scope':self.scope,'boundaries':invariant['boundaries']}]
        view=project([self.state,other],[self.scope,'other/shared'],self.scope)
        self.assertEqual(view['dependency_sources'][0]['provider_status'],'unavailable')
        self.assertIsNotNone(view['dependency_sources'][0]['age_seconds'])
        self.assertIn('dependency-unavailable',[a['kind'] for a in view['attention']])

    def test_intentional_offline_mode_is_not_provider_failure(self):
        self.state['provider_status']='offline'
        view=project([self.state],[self.scope])
        self.assertNotIn('provider-unavailable',[a['kind'] for a in view['attention']])

    def test_source_provenance_is_allowlisted(self):
        self.snapshot['source']['private_token']='never-ship'
        self.assertNotIn('never-ship',json.dumps(project([self.state],[self.scope])))

    def test_old_revision_remains_evidence_not_failure(self):
        work=next(r for r in self.snapshot['records'] if r['id']=='PI-MISSION-01')
        invariant=next(r for r in self.snapshot['records'] if r['kind']=='invariant')
        work['completion_subject']='sha256:reviewed'
        work['conformance_assertions']=[{'invariant':invariant['id'],'revision':'earlier','subject':'sha256:reviewed'}]
        view=project([self.state],[self.scope]);claims=next(w for w in view['workstreams'] if w['id']==work['id'])['claims']
        self.assertIn('reconciliation-required',[c['status'] for c in claims])
        self.assertEqual(work['conformance_assertions'][0]['revision'],'earlier')

    def test_unknown_environment_never_becomes_available(self):
        view=project([self.state],[self.scope])
        for w in view['workstreams']:
            self.assertEqual(w['environment']['availability'],'unknown')
            self.assertEqual(w['environment']['occupancy'],'unknown')

    def test_bad_shapes_refused(self):
        for broken in ([],None,{'version':1,'source':[]},dict(self.snapshot,records=[None])):
            with self.subTest(value=broken),self.assertRaises((ValueError,KeyError)):
                validate_snapshot(broken)
        for field,value in [('readiness',[]),('divergences',['bad']),('applies_to',[None]),('conformance_assertions',[None])]:
            snapshot=copy.deepcopy(self.snapshot);work=next(r for r in snapshot['records'] if r['kind']=='workstream');work[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_snapshot(snapshot)

    def test_presence_expiry_and_invalid_status(self):
        now=utcnow();p={'session':'worker','workstream':'PI-MISSION-01','status':'active','heartbeat_at':(now-timedelta(hours=2)).isoformat(),'expires_at':(now-timedelta(hours=1)).isoformat()}
        self.state['presence']=[p,None,[]]
        self.assertEqual(project([self.state],[self.scope],now=now)['sessions'][0]['status'],'expired')
        p['status']='anything';self.assertFalse(valid_presence(p,now))
        self.assertFalse(project([self.state],[self.scope],now=now)['sessions'])

    def test_incomplete_provider_paging_refused(self):
        adapter=ItsAPlan({'url':'http://127.0.0.1:1','project':'SAYINT','token_file':'unused'})
        with patch.object(adapter,'get',side_effect=[{'customFields':[{'id':1,'name':'Project Intent v0'}],'project':{'description':'m','name':'n'}},{'issues':[]},{'items':[],'total':1}]):
            with self.assertRaises(ValueError):adapter.snapshot()

    def test_interrupted_http_body_normalized_to_provider_failure(self):
        adapter=ItsAPlan({'url':'http://127.0.0.1:1','project':'SAYINT','token_file':'unused'})
        with patch('project_intent.provider.Path.read_text',return_value='test-only'),patch('project_intent.provider.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.side_effect=IncompleteRead(b'partial',10)
            with self.assertRaises(OSError):adapter.get('/test')

    def test_offline_start_has_no_provider_or_product_dependency(self):
        proc=subprocess.run([sys.executable,'-m','project_intent.cli','start','--snapshot',str(ROOT/'.project-intent/snapshot.json'),'--workstream','PI-MISSION-01'],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn('Offline orientation only',proc.stdout)


class ServiceTests(SnapshotCase):
    def setUp(self):
        super().setUp();self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.input=root/'input.json';self.cache=root/'cache.json'
        write_json(self.input,self.snapshot);write_json(self.cache,self.snapshot)
        self.config={'scopes':[{'id':self.scope,'label':'Project Intent','cache':str(self.cache),'provider':{'kind':'snapshot','path':str(self.input)},'presence_sources':[str(root/'missing-feed')]}]}

    def test_provider_and_product_feed_outage_preserves_real_state(self):
        store=Store(self.config);original=self.cache.read_bytes()
        with patch('project_intent.runtime.adapter',side_effect=OSError('unavailable')):store.refresh()
        view=project(store.view(),[self.scope])
        self.assertTrue(view['workstreams'])
        self.assertEqual(view['scopes'][0]['provider_status'],'unavailable')
        self.assertEqual(view['scopes'][0]['execution']['status'],'unavailable')
        self.assertEqual(self.cache.read_bytes(),original)

    def test_wrong_scope_snapshot_cannot_be_relabeled(self):
        store=Store(self.config);wrong=copy.deepcopy(self.snapshot);wrong['scope_id']='other/product';write_json(self.input,wrong)
        store.refresh();state=store.view()[0]
        self.assertEqual(state['provider_status'],'unavailable');self.assertEqual(state['snapshot']['scope_id'],self.scope)

    def test_bad_presence_is_reported_not_fatal(self):
        feed=Path(self.tmp.name)/'presence';feed.mkdir();write_json(feed/'bad.json',[])
        self.config['scopes'][0]['presence_sources']=[str(feed)]
        state=Store(self.config).view()[0]
        self.assertEqual(state['execution']['status'],'unavailable');self.assertFalse(state['presence'])

    def test_cache_restart_requires_no_provider_or_product(self):
        first=Store(self.config);first.refresh()
        self.input.unlink()
        recovered=Store(self.config)
        with patch('socket.socket.connect',side_effect=AssertionError('network disallowed')):
            result=project(recovered.view(),[self.scope])
        self.assertEqual(len(result['workstreams']),len(project(first.view(),[self.scope])['workstreams']))

    def test_bad_refresh_does_not_replace_last_good_cache(self):
        store=Store(self.config);original=self.cache.read_bytes();write_json(self.input,[])
        store.refresh();self.assertEqual(store.view()[0]['provider_status'],'unavailable')
        self.assertEqual(self.cache.read_bytes(),original)

    def test_api_auth_scope_and_readonly(self):
        store=Store(self.config);store.refresh()
        principals={'reader':{'token_sha256':hashlib.sha256(b'test-secret').hexdigest(),'scopes':[self.scope]},'denied':{'token_sha256':hashlib.sha256(b'test-secret').hexdigest(),'scopes':[]}}
        server=ThreadingHTTPServer(('127.0.0.1',0),handler(store,principals));thread=threading.Thread(target=server.serve_forever);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown);self.addCleanup(lambda:None)
        base='http://127.0.0.1:'+str(server.server_port)
        def request(path,user=None,method='GET'):
            headers={}
            if user:headers['Authorization']='Basic '+base64.b64encode((user+':test-secret').encode()).decode()
            return urlopen(Request(base+path,headers=headers,method=method),timeout=2)
        with self.assertRaises(HTTPError) as e:request('/api/v1/observatory')
        self.assertEqual(e.exception.code,401)
        with request('/api/v1/observatory','reader') as r:self.assertTrue(json.load(r)['workstreams'])
        with request('/api/v1/observatory','denied') as r:self.assertFalse(json.load(r)['workstreams'])
        with self.assertRaises(HTTPError) as e:request('/api/v1/observatory?scope=other','reader')
        self.assertEqual(e.exception.code,403)
        with self.assertRaises(HTTPError) as e:request('/api/v1/observatory','reader','POST')
        self.assertEqual(e.exception.code,405)


if __name__=='__main__':unittest.main()
