import json
from pathlib import Path
import tempfile
import unittest
from project_intent.activity import codex_activity


class ActivityTests(unittest.TestCase):
    def read(self, events, session='worker', now=1000):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'session.jsonl'
            rows=[{'type':'session_meta','payload':{'id':'worker'}}]+events
            path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            return codex_activity({'kind':'codex-local-usage','session':session,'path':str(path),'since':'1970-01-01T00:00:00Z'},now)

    def event(self, seconds, count):
        from datetime import datetime, timezone
        return {'timestamp':datetime.fromtimestamp(seconds,timezone.utc).isoformat(),'payload':{'type':'token_count','info':{'total_token_usage':{'output_tokens':count,'reasoning_output_tokens':90000}},'private':'NEVER-EXPORT'}}

    def test_rate_uses_output_only_and_exports_no_content(self):
        result=self.read([self.event(980,100),self.event(990,200)])
        self.assertEqual(result['points'][-1]['value'],10)
        self.assertEqual(result['status'],'recent')
        self.assertNotIn('NEVER-EXPORT',json.dumps(result))
        self.assertNotIn('90000',json.dumps(result))

    def test_wrong_session_fails_closed(self):
        self.assertEqual(self.read([self.event(990,10)],session='other')['status'],'unavailable')

    def test_reset_gap_and_future_not_fabricated(self):
        result=self.read([self.event(700,100),self.event(900,200),self.event(950,50),self.event(1100,1000)])
        self.assertEqual([p['value'] for p in result['points']],[None,None,None])
        self.assertEqual(result['last_report_at'],950)

    def test_old_reports_stale_missing_not_zero(self):
        self.assertEqual(self.read([self.event(700,100)])['status'],'stale')
        self.assertEqual(self.read([])['points'],[])
        self.assertEqual(self.read([])['status'],'not-observed')

    def test_duplicate_report_does_not_divide_by_zero(self):
        result=self.read([self.event(980,100),self.event(980,100),self.event(990,200)])
        self.assertEqual(len(result['points']),2)

    def test_absent_file_is_unavailable(self):
        result=codex_activity({'kind':'codex-local-usage','session':'worker','path':'/nonexistent/intent-usage','since':'1970-01-01T00:00:00Z'},1000)
        self.assertEqual(result['status'],'unavailable')
