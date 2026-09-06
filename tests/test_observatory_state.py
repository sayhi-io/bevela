import copy
from datetime import timedelta
import json
from pathlib import Path
import unittest
from project_intent.model import project, utcnow


class RestedTests(unittest.TestCase):
    def setUp(self):
        self.now=utcnow()
        snapshot=json.loads((Path(__file__).resolve().parents[1]/'.project-intent/snapshot.json').read_text())
        self.scope=snapshot['scope_id']
        self.work=next(r['id'] for r in snapshot['records'] if r['kind']=='workstream')
        self.state={'id':self.scope,'label':'platform','snapshot':snapshot,'provider_status':'offline','presence':[]}

    def presence(self,session,status,age):
        at=self.now-timedelta(seconds=age)
        return {'session':session,'workstream':self.work,'status':status,'heartbeat_at':at.isoformat(),'expires_at':(at+timedelta(hours=1)).isoformat()}

    def test_rested_is_explicit_bounded_and_does_not_override_live(self):
        self.state['presence']=[self.presence('old','inactive',86401),self.presence('expired','active',4000),self.presence('rested','inactive',200),self.presence('live','active',10),self.presence('future','inactive',-10),{'session':'missing','status':'inactive'}]
        view=project([self.state],[self.scope],now=self.now)
        self.assertEqual([p['session'] for p in view['recently_rested']],['rested'])
        self.assertEqual(next(p['status'] for p in view['sessions'] if p['session']=='expired'),'expired')
        self.assertEqual(next(p['status'] for p in view['sessions'] if p['session']=='live'),'active')
        self.assertEqual(view['recently_rested'][0]['reported_inactive_at'],self.state['presence'][2]['heartbeat_at'])

    def test_newest_first_ties_limit_and_scope(self):
        self.state['presence']=[self.presence('session-'+str(i).zfill(2),'inactive',i) for i in range(15)]
        self.state['presence'].append(self.presence('a-tie','inactive',0))
        other=copy.deepcopy(self.state);other['id']='hidden/secret'
        other['presence']=[self.presence('secret','inactive',0)]
        view=project([self.state,other],[self.scope],now=self.now)
        self.assertEqual(len(view['recently_rested']),12)
        self.assertEqual(view['rested_coverage']['total'],16)
        self.assertEqual(view['recently_rested'][0]['session'],'a-tie')
        self.assertNotIn('secret',json.dumps(view))

    def test_local_reports_remain_scoped_and_separate(self):
        report={'payload':{'scope':self.scope,'workstream':self.work,'packet':{'readiness':{'merge':'worker-only'}}}}
        self.state['local_reports']=[report,{'payload':{'scope':'secret','workstream':self.work}}]
        view=project([self.state],[self.scope],now=self.now)
        work=next(w for w in view['workstreams'] if w['id']==self.work)
        self.assertEqual(work['local_reports'],[report])
        self.assertNotEqual(work.get('readiness',{}).get('merge'),'worker-only')
