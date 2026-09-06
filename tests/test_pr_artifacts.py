import copy
from datetime import timedelta
import json
from pathlib import Path
import unittest

from project_intent.model import project, pull_requests, utcnow, validate_pull_requests, validate_snapshot


class PullRequestTests(unittest.TestCase):
    def setUp(self):
        self.now=utcnow()
        self.ref={'repository':'https://github.com/meanaverage/sayhi-project-intent','number':1,
                  'url':'https://github.com/meanaverage/sayhi-project-intent/pull/1','relationship':'implementation'}

    def test_optional_observation_and_exact_head(self):
        self.assertEqual(pull_requests([self.ref],self.now)[0]['observation_status'],'not-observed')
        self.ref['observation']={'observed_at':(self.now-timedelta(hours=3)).isoformat(),'source':'GitHub API',
                                 'head':'a'*40,'state':'open','draft':True,'review':'unknown','required_checks':'pending'}
        projected=pull_requests([self.ref],self.now)[0]
        self.assertEqual(projected['observation_status'],'last-known')
        self.assertEqual(projected['age_seconds'],10800)
        self.ref['observation']['observed_at']=(self.now+timedelta(hours=1)).isoformat()
        self.assertEqual(pull_requests([self.ref],self.now)[0]['observation_status'],'future-timestamp')

    def test_multiple_repos_same_number_and_duplicate_ref(self):
        second=dict(self.ref,repository='https://git.example/group/other',url='https://git.example/group/other/-/merge_requests/1',relationship='dependency')
        self.assertEqual(len(validate_pull_requests([self.ref,second])),2)
        with self.assertRaises(ValueError):validate_pull_requests([self.ref,self.ref])

    def test_invalid_fields_and_link_identity(self):
        for update in [{'number':True},{'number':0},{'number':2**53},{'url':'javascript:alert(1)'},
                       {'url':self.ref['url']+'?token=secret'},{'url':self.ref['url']+'#x'},
                       {'url':'https://evil.example/meanaverage/sayhi-project-intent/pull/1'},
                       {'repository':'https://user:pass@github.com/a/b'},
                       {'repository':'https://github.com/a/../b'}, {'relationship':'owner'}, {'secret':'no'}]:
            with self.subTest(update=update),self.assertRaises(ValueError):validate_pull_requests([dict(self.ref,**update)])
        with self.assertRaises(ValueError):validate_pull_requests([self.ref]*21)

    def test_observation_rejects_bad_types_and_unbound_checks(self):
        base={'observed_at':self.now.isoformat(),'source':'GitHub API'}
        for update in [{'observed_at':'2026-01-01'},{'source':''},{'draft':'false'},{'head':'short'},
                       {'state':'ready'},{'review':'approved'},{'required_checks':'passed'},{'extra':'x'}]:
            with self.subTest(update=update),self.assertRaises(ValueError):
                validate_pull_requests([dict(self.ref,observation=dict(base,**update))])

    def test_offline_and_scope_filtering(self):
        snapshot=json.loads((Path(__file__).resolve().parents[1]/'.project-intent/snapshot.json').read_text())
        work=next(r for r in snapshot['records'] if r['kind']=='workstream')
        work['pull_requests']=[self.ref]
        validate_snapshot(snapshot)
        state={'id':'visible','label':'Visible','provider_status':'offline','snapshot':snapshot}
        other=copy.deepcopy(state);other['id']='hidden'
        next(r for r in other['snapshot']['records'] if r['kind']=='workstream')['pull_requests']=[dict(self.ref,repository='https://private.example/team/secret',url='https://private.example/team/secret/pull/1')]
        view=project([state,other],['visible'],now=self.now)
        self.assertNotIn('private.example',json.dumps(view))
        projected=next(w for w in view['workstreams'] if w['id']==work['id'])
        self.assertEqual(projected['pull_requests'][0]['observation_status'],'not-observed')


if __name__=='__main__':unittest.main()
