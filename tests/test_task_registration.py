import copy
import io
import json
import tempfile
import unittest
from http.client import IncompleteRead
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from project_intent.cli import main
from project_intent.model import utcnow
from project_intent.reporting import digest
from project_intent.provider_write import OperatorProvider
from project_intent.runtime import read_json, write_json
from project_intent.task_registration import register, validate_task


class Provider:
    config = {'project': 'TEST'}

    def __init__(self):
        self.rows = []
        self.comments = []
        self.creates = 0
        self.puts = 0
        self.fail_create = None
        self.fail_snapshot = False
        self.fail_put = False

    def inventory(self):
        return copy.deepcopy(self.rows)

    def get(self, path):
        return {'columns': [{'id': 1, 'stateType': 'unstarted'}]}

    def request(self, method, path, body):
        if method == 'POST':
            self.creates += 1
            if self.fail_create == 'before':
                raise OSError('ambiguous transport')
            n = len(self.rows) + 1
            self.rows.append({'native_id': n, 'identifier': 'TEST-' + str(n),
                              'title': body['title'], 'description': body['description'],
                              'record': None, 'metadata_digest': digest(None), 'field_id': 1})
            if self.fail_create == 'after':
                raise OSError('accepted remotely, receipt lost')
            return {'id': n}
        self.puts += 1
        row = next(r for r in self.rows if r['native_id'] == int(path.split('/')[2]))
        row['record'] = json.loads(body['value'])
        row['metadata_digest'] = digest(row['record'])
        if self.fail_put:
            raise OSError('accepted metadata, receipt lost')
        return {}

    def find_comment(self, issue, marker):
        return next((c for c in self.comments if c['body'].startswith(marker + '\n')), None)

    def comment(self, issue, body):
        self.comments.append({'body': body})

    def resolve(self, identifier):
        return next(r for r in self.inventory() if r['identifier'] == identifier)

    def snapshot(self):
        if self.fail_snapshot:
            raise OSError('refresh unavailable')
        return {'version': 1, 'mission': 'Test', 'source': {
            'captured_at': utcnow().isoformat(), 'authoritative': False}, 'records': [
                dict(r['record'], provider_identifier=r['identifier']) for r in self.inventory() if r['record']]}


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.checkout = {'root': str(self.root / 'checkout'), 'branch': 'agent/test',
                         'head': 'a' * 40, 'host': 'test', 'repository_common_dir': str(self.root / '.git')}
        self.entry = {'id': 'scope', 'label': 'Test', 'cache': str(self.root / 'snapshot.json'),
                      'provider': {'kind': 'itsaplan', 'url': 'http://127.0.0.1:1', 'project': 'TEST'}}
        self.config = {'scopes': [self.entry], 'operator': {'journal_directory': str(self.root / 'reconcile')},
                       'task_registration': {'journal_directory': str(self.root / 'register'),
                                             'checkout_roots': {'scope': [str(self.root / 'checkout')]}}}
        self.task = {'title': 'Test user task', 'statement': 'Implement assigned change', 'scope': 'Bounded work',
                     'acceptance': ['Tests pass'], 'boundaries': ['test/boundary'], 'avoid': 'Unrelated work',
                     'authority_ref': 'User requested this change in current task'}
        self.provider = Provider()
        for target, value in [('checkout_identity', self.checkout), ('OperatorProvider', self.provider)]:
            mock = patch('project_intent.task_registration.' + target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def preview(self, **kwargs):
        return register(self.config, 'scope', self.task, **kwargs)

    def submit(self, **kwargs):
        preview = self.preview(**kwargs)
        return register(self.config, 'scope', self.task, submit=True,
                        reviewed_digest=preview['inventory_digest'], **kwargs)

    def test_preview_does_not_write(self):
        self.assertEqual(self.preview()['state'], 'preview')
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(self.provider.creates, 0)

    def test_policy_defaults_closed_without_granting_general_operator_access(self):
        self.assertNotIn('allowed_scopes', self.config['operator'])
        self.config.pop('task_registration')
        with self.assertRaisesRegex(ValueError, 'not configured'):
            self.preview()

    def test_identical_journal_locks_refused_before_writing(self):
        self.config['task_registration']['journal_directory'] = self.config['operator']['journal_directory']
        with self.assertRaisesRegex(ValueError, 'distinct lock'):
            self.preview()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_wrong_scope_checkout_and_prefix_sibling_refused(self):
        for root in (str(self.root / 'elsewhere'), str(self.root / 'checkout-other')):
            self.checkout['root'] = root
            with self.assertRaisesRegex(ValueError, 'outside'):
                self.preview()
        with self.assertRaisesRegex(ValueError, 'not configured'):
            register(self.config, 'other', self.task)

    def test_task_fields_bounded_no_readiness_or_authority_invention(self):
        for update in ({'readiness': {'production': 'ready'}}, {'authority_ref': ''}, {'title': 'x'*201},
                       {'acceptance': []}, {'boundaries': ['\n']}):
            with self.assertRaises(ValueError):
                validate_task(dict(self.task, **update))

    def test_stale_inventory_and_changed_task_review_refused(self):
        preview = self.preview()
        self.task['statement'] = 'Changed task'
        with self.assertRaisesRegex(ValueError, 'review missing'):
            register(self.config, 'scope', self.task, submit=True, reviewed_digest=preview['inventory_digest'])
        preview = self.preview()
        self.provider.request('POST', '', {'title': 'Other native task', 'description': ''})
        with self.assertRaisesRegex(ValueError, 'review missing'):
            register(self.config, 'scope', self.task, submit=True, reviewed_digest=preview['inventory_digest'])
        self.assertEqual(self.provider.puts, 0)

    def test_create_refresh_and_retry_across_head_changes(self):
        first = self.submit()
        self.assertEqual(first['state'], 'registered')
        self.checkout['head'] = 'b'*40
        self.checkout['branch'] = 'agent/later'
        self.assertEqual(self.submit()['workstream'], first['workstream'])
        self.assertEqual(self.provider.creates, 1)
        self.assertEqual(self.provider.puts, 1)
        snapshot = read_json(self.entry['cache'])
        self.assertEqual(snapshot['scope_id'], 'scope')
        self.assertEqual(snapshot['records'][0]['readiness']['implementation'], 'unknown')

    def test_native_reuse_never_replaces_existing_metadata(self):
        first = self.submit()
        original = copy.deepcopy(self.provider.rows)
        self.task['title'] = 'Another wording for existing task'
        result = self.submit(native_identifier=first['identifier'])
        self.assertEqual(result['workstream'], first['workstream'])
        self.assertEqual(self.provider.rows, original)

    def test_unannotated_candidate_requires_explicit_selection(self):
        self.provider.request('POST', '', {'title': self.task['title'].upper(), 'description': 'Existing owner task'})
        with self.assertRaisesRegex(ValueError, 'Existing native candidate'):
            self.submit()
        self.assertEqual(self.submit(native_identifier='TEST-1')['state'], 'registered')
        self.assertEqual(self.provider.creates, 1)
        self.assertEqual(self.provider.rows[0]['description'], 'Existing owner task')

    def test_absent_native_and_non_workstream_refused(self):
        with self.assertRaisesRegex(ValueError, 'absent'):
            self.submit(native_identifier='TEST-999')
        self.provider.request('POST', '', {'title': 'Invariant', 'description': ''})
        self.provider.rows[0]['record'] = {'id': 'INV-1', 'kind': 'invariant'}
        with self.assertRaisesRegex(ValueError, 'not a workstream'):
            self.submit(native_identifier='TEST-1')

    def test_concurrent_same_task_creates_once(self):
        preview = self.preview()
        def run(_):
            return register(self.config, 'scope', self.task, submit=True,
                            reviewed_digest=preview['inventory_digest'])
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(run, range(2)))
        self.assertTrue(all(r['state'] == 'registered' for r in results))
        self.assertEqual(self.provider.creates, 1)

    def test_uncertain_create_is_not_blindly_repeated(self):
        self.provider.fail_create = 'before'
        self.assertEqual(self.submit()['state'], 'uncertain')
        self.provider.fail_create = None
        self.assertEqual(self.submit()['state'], 'uncertain')
        self.assertEqual(self.provider.creates, 1)

    def test_lost_create_receipt_recovers_original_operation(self):
        self.provider.fail_create = 'after'
        self.assertEqual(self.submit()['state'], 'uncertain')
        self.checkout['branch'] = 'agent/retry'
        self.provider.fail_create = None
        self.assertEqual(self.submit()['state'], 'registered')
        self.assertEqual(self.provider.creates, 1)

    def test_lost_metadata_receipt_recovers_without_second_put(self):
        self.provider.fail_put = True
        self.assertEqual(self.submit()['state'], 'uncertain')
        self.assertEqual(self.submit()['state'], 'registered')
        self.assertEqual(self.provider.puts, 1)

    def test_uncertain_request_cannot_be_changed_in_place(self):
        self.provider.fail_create = 'before'
        self.submit()
        self.task['scope'] = 'Changed scope'
        with self.assertRaisesRegex(ValueError, 'prior registration'):
            self.submit()

    def test_refresh_failure_recovers_without_recreating(self):
        self.provider.fail_snapshot = True
        self.assertEqual(self.submit()['state'], 'registered-refresh-pending')
        self.assertFalse(Path(self.entry['cache']).exists())
        self.provider.fail_snapshot = False
        self.assertEqual(self.submit()['state'], 'registered')
        self.assertEqual(self.provider.creates, 1)

    def test_refresh_retry_never_recreates_disappeared_native_issue(self):
        preview = self.preview()
        self.provider.fail_snapshot = True
        self.assertEqual(self.submit()['state'], 'registered-refresh-pending')
        self.provider.rows.clear()
        self.provider.fail_snapshot = False
        result = register(self.config, 'scope', self.task, submit=True,
                          reviewed_digest=preview['inventory_digest'])
        self.assertEqual(result['state'], 'registered-refresh-pending')
        self.assertEqual(self.provider.creates, 1)
        self.assertEqual(self.provider.puts, 1)

    def test_refresh_retry_accepts_normal_metadata_advancement(self):
        self.provider.fail_snapshot = True
        self.submit()
        row = self.provider.rows[0]
        row['record']['revision'] = '2'
        row['record']['readiness']['implementation'] = 'complete'
        row['metadata_digest'] = digest(row['record'])
        self.provider.fail_snapshot = False
        self.assertEqual(register(self.config, 'scope', self.task, submit=True)['state'], 'registered')
        self.assertEqual(read_json(self.entry['cache'])['records'][0]['revision'], '2')
        self.assertEqual(self.provider.puts, 1)

    def test_wrapper_crash_recovers_native_success_without_recreating(self):
        def fail_receipt(path, value):
            if 'result' in value:
                raise OSError('local receipt write interrupted')
            return write_json(path, value)
        with patch('project_intent.task_registration.write_json', side_effect=fail_receipt):
            with self.assertRaises(OSError):
                self.submit()
        self.provider.rows.clear()
        result = register(self.config, 'scope', self.task, submit=True)
        self.assertEqual(result['state'], 'registered-refresh-pending')
        self.assertEqual(self.provider.creates, 1)
        self.assertEqual(self.provider.puts, 1)

    def test_final_locked_read_refuses_native_drift_and_allows_fresh_review(self):
        self.provider.request('POST', '', {'title': self.task['title'], 'description': 'Original'})
        inventory = self.provider.inventory
        calls = 0
        def drift():
            nonlocal calls
            calls += 1
            if calls == 3:  # Preview, submission check, then final reconciliation read.
                self.provider.rows[0].update(title='Changed title', description='Changed scope',
                                             delegate={'user_id': 'another-owner'}, lifecycle='Done')
            return inventory()
        self.provider.inventory = drift
        preview = self.preview(native_identifier='TEST-1')
        with self.assertRaisesRegex(ValueError, 'mutation boundary'):
            register(self.config, 'scope', self.task, native_identifier='TEST-1', submit=True,
                     reviewed_digest=preview['inventory_digest'])
        self.assertEqual(self.provider.puts, 0)
        self.assertEqual(self.provider.comments, [])
        # A stored packet from a pre-write rejection must not bypass fresh review.
        with self.assertRaisesRegex(ValueError, 'review missing'):
            register(self.config, 'scope', self.task, native_identifier='TEST-1', submit=True,
                     reviewed_digest=preview['inventory_digest'])
        self.assertEqual(self.submit(native_identifier='TEST-1')['state'], 'registered')
        self.assertEqual(self.provider.creates, 1)

    def test_uncertain_retry_requires_review_of_new_inventory(self):
        self.provider.fail_create = 'after'
        preview = self.preview()
        result = register(self.config, 'scope', self.task, submit=True,
                          reviewed_digest=preview['inventory_digest'])
        self.assertEqual(result['state'], 'uncertain')
        with self.assertRaisesRegex(ValueError, 'review missing'):
            register(self.config, 'scope', self.task, submit=True,
                     reviewed_digest=preview['inventory_digest'])
        self.assertEqual(self.submit()['state'], 'registered')
        self.assertEqual(self.provider.creates, 1)

    def test_real_inventory_adapter_preserves_native_review_fields(self):
        provider = OperatorProvider(self.entry['provider'])
        project = {'customFields': [{'id': 3, 'name': 'Project Intent v0'}],
                   'assignees': [{'userId': 7, 'name': 'Native owner', 'username': 'owner'}],
                   'columns': [{'id': 5, 'name': 'Done'}]}
        board = {'issues': [{'id': 1, 'identifier': 'TEST-1', 'title': 'Native task',
                             'description': 'Native scope', 'fieldValues': [], 'columnId': 5,
                             'delegateUserId': 7, 'assigneeUserId': 8}]}
        with patch.object(provider, 'get', side_effect=[project, board]):
            row = provider.inventory()[0]
        self.assertEqual(row['delegate'], {'user_id': 7, 'name': 'Native owner', 'username': 'owner'})
        self.assertEqual(row['assignee']['user_id'], 8)
        self.assertIsNone(row['assignee']['name'])
        self.assertEqual(row['lifecycle'], 'Done')
        self.assertEqual(row['description'], 'Native scope')
        self.assertIsNone(row['record'])

    def test_incomplete_write_transport_is_normalized(self):
        token = self.root/'test-token'
        token.write_text('isolated-test-token')
        provider = OperatorProvider(dict(self.entry['provider'], token_file=str(token)))
        with patch('project_intent.provider_write.build_opener') as opener:
            opener.return_value.open.side_effect = IncompleteRead(b'partial')
            with self.assertRaisesRegex(OSError, 'transport incomplete'):
                provider.request('POST', '/test', {})

    def test_wrong_scope_refresh_preserves_existing_cache(self):
        write_json(self.entry['cache'], {'existing': 'cache'})
        snapshot = self.provider.snapshot
        self.provider.snapshot = lambda: dict(snapshot(), scope_id='other')
        self.assertEqual(self.submit()['state'], 'registered-refresh-pending')
        self.assertEqual(read_json(self.entry['cache']), {'existing': 'cache'})

    def cli(self, *args):
        stdout = io.StringIO()
        with patch('sys.argv', ['project-intent', *args]), redirect_stdout(stdout):
            main()
        return json.loads(stdout.getvalue())

    def test_cli_register_onboard_enroll_renew_release(self):
        cfg = self.root/'config.json'; task = self.root/'task.json'; worker = self.root/'worker.json'
        leases = self.root/'leases'
        write_json(cfg, self.config); write_json(task, self.task)
        write_json(worker, {'scopes': {'scope': {'snapshot': self.entry['cache'], 'enrollment_directory': str(leases)}}})
        base = ['task-register', '--registration-config', str(cfg), '--worker-config', str(worker),
                '--scope', 'scope', '--input', str(task)]
        result = self.cli(*base)
        registered = self.cli(*base, '--submit', '--inventory-digest', result['inventory_digest'])
        common = ['--worker-config', str(worker), '--scope', 'scope', '--workstream', registered['workstream']]
        onboard = self.cli('onboard', *common)
        self.assertEqual(onboard['orientation']['assignment']['id'], registered['workstream'])
        self.assertFalse(leases.exists())
        with patch('project_intent.cli.checkout_identity', return_value=self.checkout):
            enrolled = self.cli('enroll', *common, '--session', 'isolated-worker', '--access', 'inspect', '--working', 'Test')
            renewed = self.cli('enroll', *common, '--session', 'isolated-worker')
            released = self.cli('enroll', *common, '--session', 'isolated-worker', '--inactive')
        self.assertEqual(enrolled['status'], 'active')
        self.assertEqual(renewed['session'], enrolled['session'])
        self.assertEqual(released['status'], 'inactive')

    def test_cli_cache_mismatch_fails_before_provider_write(self):
        cfg = self.root/'config.json'; task = self.root/'task.json'; worker = self.root/'worker.json'
        write_json(cfg, self.config); write_json(task, self.task)
        write_json(worker, {'scopes': {'scope': {'snapshot': str(self.root/'other.json')}}})
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.cli('task-register', '--registration-config', str(cfg), '--worker-config', str(worker),
                     '--scope', 'scope', '--input', str(task), '--submit')
        self.assertEqual(self.provider.creates, 0)

    def test_empty_onboard_offers_registration_without_enrolling(self):
        worker = self.root/'worker.json'
        write_json(self.entry['cache'], dict(self.provider.snapshot(), scope_id='scope'))
        write_json(worker, {'scopes': {'scope': {'snapshot': self.entry['cache'],
                                               'enrollment_directory': str(self.root/'leases')}}})
        result = self.cli('onboard', '--worker-config', str(worker), '--scope', 'scope', '--query', 'missing task')
        self.assertEqual(result['discovery']['candidates'], [])
        self.assertIn('task-register', result['next_step'])
        self.assertNotIn('enrollment_template', result)
        self.assertFalse((self.root/'leases').exists())
