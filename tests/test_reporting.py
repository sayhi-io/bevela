import copy
import tempfile
import unittest
from pathlib import Path

from project_intent.reporting import submit,reports,publish,digest
from project_intent.provider_write import configured,reconcile
from project_intent.runtime import read_json,write_json
from project_intent.model import project


class FakeProvider:
    config={'project':'TEST'}
    def __init__(self):self.comments=[];self.calls=0;self.fail=False
    def resolve(self,reference):return {'native_id':1}
    def find_comment(self,issue,marker):return next((r for r in self.comments if r['body'].startswith(marker)),None)
    def comment(self,issue,body):
        self.calls+=1
        if self.fail:raise OSError('ambiguous')
        row={'id':self.calls,'body':body};self.comments.append(row);return row


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.packet={'summary':'Local validation complete; review pending','readiness':{'review':'pending'},'evidence':[{'ref':'source.py','sha256':'a'*64}]}
        self.provider=FakeProvider()

    def test_immutable_idempotent_and_scoped(self):
        a=submit(self.root,'scope','WORK-1','worker',self.packet)
        b=submit(self.root,'scope','WORK-1','worker',self.packet,True)
        self.assertEqual(a['id'],b['id']);self.assertEqual(b['state'],'pending')
        self.assertEqual(reports(self.root,'other'),[])
        bad=copy.deepcopy(self.packet);bad['summary']='Correction'
        self.assertNotEqual(submit(self.root,'scope','WORK-1','worker',bad)['id'],a['id'])
        self.assertEqual(len(reports(self.root,'scope')),2)

    def test_publish_once_and_local_not_implicit_submission(self):
        r=submit(self.root,'scope','WORK-1','worker',self.packet)
        with self.assertRaises(ValueError):publish(self.root,'scope',r['id'],self.provider)
        submit(self.root,'scope','WORK-1','worker',self.packet,True)
        self.assertEqual(publish(self.root,'scope',r['id'],self.provider)['state'],'published')
        publish(self.root,'scope',r['id'],self.provider);self.assertEqual(self.provider.calls,1)

    def test_uncertain_never_blindly_retries(self):
        r=submit(self.root,'scope','WORK-1','worker',self.packet,True);self.provider.fail=True
        self.assertEqual(publish(self.root,'scope',r['id'],self.provider)['state'],'uncertain')
        self.provider.fail=False
        self.assertEqual(publish(self.root,'scope',r['id'],self.provider)['state'],'uncertain')
        self.assertEqual(self.provider.calls,1)
        self.provider.comments.append({'id':9,'body':'project-intent-report:'+r['id']+'\naccepted remotely'})
        self.assertEqual(publish(self.root,'scope',r['id'],self.provider)['native_comment'],9)

    def test_tamper_and_wrong_scope_refused(self):
        r=submit(self.root,'scope','WORK-1','worker',self.packet,True)
        with self.assertRaises(ValueError):publish(self.root,'other',r['id'],self.provider)
        file=self.root/(r['id']+'.json');value=read_json(file);value['payload']['packet']['summary']='tampered';write_json(file,value)
        self.assertEqual(reports(self.root,'scope'),[])

    def test_scope_needs_operator_allowlist(self):
        with self.assertRaises(ValueError):configured({'scopes':[{'id':'scope'}]},'scope')

    def test_exact_publication_survives_listing_overflow(self):
        r=submit(self.root,'scope','WORK-1','worker',self.packet,True)
        for n in range(501):write_json(self.root/(f'{n:064x}'+'.json'),{})
        with self.assertRaisesRegex(ValueError,'500'):reports(self.root,'scope')
        self.assertEqual(publish(self.root,'scope',r['id'],self.provider)['state'],'published')

    def test_native_update_cannot_duplicate_alias(self):
        record={'id':'WORK-1','kind':'workstream','revision':'1','state':'active','statement':'work','scope':'bounded','boundaries':[],'acceptance':['test']}
        self.provider.inventory=lambda:[{'identifier':'TEST-1','native_id':1,'record':record,'metadata_digest':digest(record)}, {'identifier':'TEST-2','native_id':2,'record':None,'metadata_digest':digest(None)}]
        packet={'scope':'scope','confirmed':True,'native_identifier':'TEST-2','expected_digest':digest(None),'record':record}
        with self.assertRaisesRegex(ValueError,'Alias already'):reconcile(self.provider,'scope',packet,self.root)

    def test_report_validation_and_reported_hash(self):
        for bad in ({'summary':''},{'summary':'x','evidence':[{'ref':'x','sha256':'bad'}]},{'summary':'x','credential':'no'}):
            with self.assertRaises(ValueError):submit(self.root,'scope','WORK-1','worker',bad)

    def test_reconciliation_preconditions(self):
        old={'id':'WORK-1','kind':'workstream','revision':'1','state':'active','statement':'work','scope':'bounded','boundaries':[],'acceptance':['test'],'completion_evidence':['historic']}
        self.provider.inventory=lambda:[{'identifier':'TEST-1','native_id':1,'record':old,'metadata_digest':digest(old)}]
        packet={'scope':'scope','confirmed':True,'native_identifier':'TEST-1','expected_digest':'stale','record':dict(old,revision='2')}
        with self.assertRaisesRegex(ValueError,'Metadata changed'):reconcile(self.provider,'scope',packet,self.root)
        packet['expected_digest']=digest(old);packet['record']['completion_evidence']=[]
        with self.assertRaisesRegex(ValueError,'Historical evidence'):reconcile(self.provider,'scope',packet,self.root)
        packet['scope']='other'
        with self.assertRaisesRegex(ValueError,'scope'):reconcile(self.provider,'scope',packet,self.root)


if __name__=='__main__':unittest.main()
