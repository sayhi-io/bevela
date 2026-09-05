import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from project_intent.worker_context import checkout_identity, relative_paths, resolve_assignment, discovery, nearby_workers
from project_intent.model import utcnow, valid_presence
from project_intent.enrollment import registration
from project_intent.provider import ItsAPlan

ROOT=Path(__file__).resolve().parents[1]


class WorkerContextTests(unittest.TestCase):
    def setUp(self):
        self.snapshot=json.loads((ROOT/'.project-intent/snapshot.json').read_text())
        self.scope=self.snapshot['scope_id'];self.state={'id':self.scope,'label':'test','snapshot':self.snapshot,'provider_status':'offline'}
        self.work=next(w for w in self.snapshot['records'] if w['id']=='PI-MISSION-01')
        self.work['provider_identifier']='SAYINT-5'

    def test_capture_real_worktree_not_repo_name(self):
        c=checkout_identity(ROOT/'project_intent')
        self.assertEqual(c['root'],str(ROOT));self.assertTrue(Path(c['repository_common_dir']).is_dir())
        self.assertIn('branch',c);self.assertIn('head',c)

    def test_non_git_checkout_requires_explicit_choice(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaises(ValueError):checkout_identity(d)

    def test_relative_paths_are_explicit_no_escaping_or_globs(self):
        self.assertEqual(relative_paths(['src/','src']),['src'])
        self.assertEqual(relative_paths(['.']),['.'])
        for value in ('/tmp/file','../other','src/../other','src/**','src\\file',''):
            with self.subTest(value=value),self.assertRaises(ValueError):relative_paths([value])

    def test_alias_native_and_qualified_resolution(self):
        for reference in ('PI-MISSION-01','SAYINT-5',self.scope+':PI-MISSION-01'):
            self.assertEqual(resolve_assignment([self.state],reference)[1]['id'],'PI-MISSION-01')
        other=copy.deepcopy(self.state);other['id']='other'
        with self.assertRaises(ValueError):resolve_assignment([self.state,other],'SAYINT-5')

    def test_discovery_keeps_candidates_not_assignments(self):
        self.work['source_checkout']=str(ROOT)
        result=discovery([self.state],checkout_identity(ROOT),'mission')
        candidate=next(w for w in result['candidates'] if w['id']=='PI-MISSION-01')
        self.assertTrue(candidate['checkout_reference_match'])
        self.assertIn('not assignments',result['instruction'])

    def test_same_repo_other_worktree_paths_and_seams(self):
        here=checkout_identity(ROOT);other=dict(here,root='/other/worktree')
        r=registration(self.snapshot,'PI-MISSION-01','nearby','working',['intent/projection'],[])
        r.update(checkout=other,access='edit',touching_paths=['project_intent'],touching_seams=[],avoid_paths=['tests'])
        self.state['presence']=[r]
        result=nearby_workers([self.state],here,['project_intent/cli.py'],['intent/projection'],self.scope)
        self.assertEqual(result[0]['overlapping_paths'],['project_intent/cli.py'])
        self.assertEqual(result[0]['shared_seams'],['intent/projection'])
        self.assertEqual(result[0]['checkout']['root'],'/other/worktree')
        other['repository_common_dir']='/different/repo/.git'
        self.assertEqual(nearby_workers([self.state],here,['project_intent/cli.py'],[],self.scope),[])
        # Same path spelling is not repo identity; semantic keys do not leak globally.
        self.state['id']='other'
        self.assertEqual(nearby_workers([self.state],here,[],['intent/projection'],self.scope),[])

    def test_malformed_granular_presence_rejected(self):
        r=registration(self.snapshot,'PI-MISSION-01','worker','working',[],[])
        r['touching_paths']=['../other'];self.assertFalse(valid_presence(r))
        r['touching_paths']=[];r['checkout']={'root':'relative'};self.assertFalse(valid_presence(r))

    def test_provider_native_identity_and_delegate_retained(self):
        adapter=ItsAPlan({'url':'http://127.0.0.1:8280','project':'SAYINT'})
        scaffold={'project':{'description':'mission','name':'name'},'customFields':[{'id':1,'name':'Project Intent v0'}],
                  'columns':[{'id':7,'name':'In Progress'}],'assignees':[{'userId':'agent','name':'Intent worker','username':'intent'}]}
        board={'issues':[{'title':'Task','id':37,'identifier':'SAYINT-5','delegateUserId':'agent','columnId':7,
                          'fieldValues':[{'fieldId':1,'value':json.dumps(self.work)}]}]}
        with patch.object(adapter,'get',side_effect=[scaffold,board,{'items':[],'total':0}]):result=adapter.snapshot()['records'][0]
        self.assertEqual(result['provider_identifier'],'SAYINT-5');self.assertEqual(result['delegate_name'],'Intent worker')
        self.assertEqual(result['provider_lifecycle'],'In Progress')

    def test_edit_enrollment_requires_granular_paths(self):
        with tempfile.TemporaryDirectory() as d:
            result=subprocess.run([sys.executable,'-m','project_intent.cli','enroll','--snapshot',str(ROOT/'.project-intent/snapshot.json'),
                '--workstream','PI-MISSION-01','--session','worker','--directory',d,'--access','edit'],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('--touching-path',result.stderr)
            self.assertFalse((Path(d)/'worker.json').exists())
