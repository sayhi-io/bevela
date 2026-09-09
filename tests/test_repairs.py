from datetime import timedelta
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from project_intent.enrollment import registration
from project_intent.model import utcnow
from project_intent.repairs import change, status
from project_intent.runtime import write_json
from project_intent.worker_context import checkout_identity

ROOT = Path(__file__).resolve().parents[1]


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / 'work'
        self.checkout.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.checkout)], check=True)
        self.identity = checkout_identity(self.checkout)
        self.feed = self.root / 'presence'
        self.snapshot = {
            'version': 1, 'scope_id': 'example/shop', 'mission': 'Shared contracts',
            'source': {'provider': 'snapshot', 'authoritative': False,
                       'captured_at': utcnow().isoformat(), 'mode': 'offline_snapshot'},
            'records': [dict(kind='workstream', id=name, statement='Task ' + name,
                scope='Task ' + name, revision='1', state='active', acceptance=['Preserve contracts'],
                boundaries=['shop/money', 'shop/display'], readiness={}) for name in ('PRODUCER', 'CONSUMER')],
        }
        write_json(self.root / 'snapshot.json', self.snapshot)
        for name in ('producer.py', 'consumer.py', 'test_contract.py'):
            (self.checkout / name).write_text('# source\n')
        self.enroll('a', 'PRODUCER')
        self.enroll('b', 'CONSUMER')

    def enroll(self, session, workstream, **overrides):
        row = registration(self.snapshot, workstream, session, 'Task', [], [])
        row.update(checkout=self.identity, access='edit', touching_paths=['consumer.py'],
                   touching_seams=['shop/money'], avoid_paths=[])
        row.update(overrides)
        write_json(self.feed / (session + '.json'), row)
        return row

    def call(self, action='claim', session='a', workstream='PRODUCER', **kwargs):
        args = dict(directory=self.feed, snapshot=self.snapshot, workstream=workstream,
                    session=session, checkout=self.identity, action=action,
                    seam='shop/money', paths=['consumer.py'],
                    problem='Consumer displays the wrong unit; preserve producer and consumer contracts',
                    check_paths=['producer.py', 'consumer.py', 'test_contract.py'],
                    peer_sessions=['b' if session == 'a' else 'a'])
        args.update(kwargs)
        return change(**args)

    def complete(self, claim, **kwargs):
        self.ack(claim)
        return self.call('complete', claim_id=claim['claim_id'],
                         evidence='Cross-contract regression checks passed',
                         check_paths=['producer.py', 'consumer.py', 'test_contract.py'], **kwargs)

    def ack(self, claim, **kwargs):
        session = 'b' if claim['owner_session'] == 'a' else 'a'
        args = dict(session=session, workstream='CONSUMER' if session == 'b' else 'PRODUCER',
                    repair_id=claim['repair_id'], expected_revision=claim['revision'])
        args.update(kwargs)
        return self.call('ack', **args)

    def test_one_owner_idempotent_claim_and_no_token_for_peer(self):
        first = self.call()
        self.assertTrue(first['accepted'])
        self.assertFalse(first['acquired'])
        self.assertFalse(first['ready_to_edit'])
        self.assertEqual(first['claim_id'], self.call()['claim_id'])
        other = self.call(session='b', workstream='CONSUMER')
        self.assertFalse(other['acquired'])
        self.assertEqual(other['owner_session'], 'a')
        self.assertNotIn('claim_id', other)
        self.assertNotIn('claim_id', status(self.feed, 'example/shop', self.identity)['repairs'][0])
        self.ack(first)
        self.assertTrue(self.call()['ready_to_edit'])

    def test_different_seam_same_path_cannot_create_second_fixer(self):
        self.call()
        other = self.call(session='b', workstream='CONSUMER', seam='shop/display')
        self.assertFalse(other['acquired'])
        self.assertEqual(other['seam'], 'shop/money')

    def test_parent_child_paths_conflict(self):
        self.call(paths=['src'], check_paths=['src/view.py', 'producer.py'])
        other = self.call(session='b', workstream='CONSUMER', seam='shop/display', paths=['src/view.py'])
        self.assertFalse(other['acquired'])

    def test_simultaneous_cli_claims_have_exactly_one_owner(self):
        prefix = [sys.executable, '-I', str(ROOT / 'project_intent/_worker_cli.py'), 'repair-claim',
                  '--snapshot', str(self.root / 'snapshot.json'), '--directory', str(self.feed),
                  '--seam', 'shop/money', '--repair-path', 'consumer.py',
                  '--problem', 'Wrong consumer units', '--check-path', 'consumer.py', '--check-path', 'producer.py']
        processes = [subprocess.Popen(prefix + ['--session', session, '--workstream', work,
            '--peer-session', 'b' if session == 'a' else 'a'],
            cwd=self.checkout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for session, work in [('a', 'PRODUCER'), ('b', 'CONSUMER')]]
        results = []
        for process in processes:
            out, err = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, err)
            results.append(json.loads(out))
        self.assertEqual(sum(r['accepted'] for r in results), 1)
        self.assertFalse(any(r['ready_to_edit'] for r in results))
        self.assertEqual(results[0]['owner_session'], results[1]['owner_session'])

    def test_expired_owner_is_not_taken_over(self):
        self.call()
        old = json.loads((self.feed / 'a.json').read_text())
        old.update(expires_at=(utcnow() - timedelta(seconds=1)).isoformat())
        write_json(self.feed / 'a.json', old)
        other = self.call(session='b', workstream='CONSUMER')
        self.assertFalse(other['acquired'])
        self.assertEqual(other['owner_observation'], 'released-or-expired-no-automatic-takeover')

    def test_explicit_release_and_stale_token_rejected(self):
        first = self.call()
        self.call('release', claim_id=first['claim_id'])
        next_claim = self.call(session='b', workstream='CONSUMER')
        self.assertTrue(next_claim['accepted'])
        self.assertNotEqual(first['claim_id'], next_claim['claim_id'])
        with self.assertRaises(ValueError):
            self.complete(first)
        with self.assertRaises(ValueError):
            self.call('release', claim_id=first['claim_id'])

    def test_peer_cannot_complete_with_owners_token(self):
        first = self.call()
        with self.assertRaises(ValueError):
            self.complete(first, session='b', workstream='CONSUMER')

    def test_reenrollment_cannot_silently_resume_old_claim(self):
        first = self.call()
        self.enroll('a', 'PRODUCER')
        self.assertFalse(self.call()['acquired'])
        with self.assertRaises(ValueError):
            self.complete(first)
        self.call('release', claim_id=first['claim_id'])
        self.assertTrue(self.call()['accepted'])

    def test_resolution_hashes_dependencies_and_detects_later_changes(self):
        first = self.call()
        resolved = self.complete(first)
        self.assertEqual(resolved['verification'], 'owner-reported-checks-source-unchanged')
        self.assertFalse(self.call(session='b', workstream='CONSUMER')['acquired'])
        (self.checkout / 'producer.py').write_text('# changed contract\n')
        rows = status(self.feed, 'example/shop', self.identity)['repairs']
        self.assertEqual(rows[0]['verification'], 'source-changed-revalidation-required')
        self.assertTrue(self.call(session='b', workstream='CONSUMER')['accepted'])

    def test_completion_requires_evidence_and_coverage(self):
        first = self.call()
        self.ack(first)
        for evidence, paths in [('', ['consumer.py']), ('Passed', ['consumer.py']), ('Passed', ['producer.py'])]:
            with self.subTest(evidence=evidence, paths=paths), self.assertRaises(ValueError):
                self.call('complete', claim_id=first['claim_id'], evidence=evidence, check_paths=paths)
        self.assertEqual(status(self.feed, 'example/shop', self.identity)['repairs'][0]['state'], 'claimed')

    def test_disjoint_repairs_on_same_seam_can_proceed_independently(self):
        producer = self.call(paths=['producer.py'], problem='Producer must preserve checkout totals')
        consumer = self.call(session='b', workstream='CONSUMER', problem='Consumer labels need unit conversion')
        self.assertTrue(producer['accepted'])
        self.assertTrue(consumer['accepted'])
        self.assertNotEqual(producer['repair_id'], consumer['repair_id'])
        self.ack(producer)
        self.ack(consumer)
        self.assertTrue(self.call(paths=['producer.py'], problem='Producer must preserve checkout totals')['ready_to_edit'])
        self.assertTrue(self.call(session='b', workstream='CONSUMER', problem='Consumer labels need unit conversion')['ready_to_edit'])

    def test_competing_claim_is_not_peer_agreement(self):
        first = self.call()
        contender = self.call(session='b', workstream='CONSUMER')
        self.assertFalse(contender['accepted'])
        self.assertEqual(contender['acknowledgments'], {})
        with self.assertRaises(ValueError):
            self.call('complete', claim_id=first['claim_id'], evidence='Tests passed')
        self.assertEqual(self.ack(first)['agreement'], 'acknowledged')
        self.assertTrue(self.call()['ready_to_edit'])

    def test_wrong_peer_self_and_stale_revision_cannot_acknowledge(self):
        first = self.call()
        self.enroll('c', 'CONSUMER')
        for kwargs in [dict(session='a', workstream='PRODUCER'), dict(session='c'),
                       dict(expected_revision=first['revision'] + 1)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.ack(first, **kwargs)
        self.assertEqual(self.call()['acknowledgments'], {})

    def test_plan_changes_require_new_agreement(self):
        first = self.call()
        self.ack(first)
        with self.assertRaises(ValueError):
            self.call(problem='Different repair')
        with self.assertRaises(ValueError):
            self.call(check_paths=['consumer.py', 'producer.py'])
        self.call('release', claim_id=first['claim_id'])
        second = self.call(problem='New precise repair')
        self.assertFalse(second['ready_to_edit'])
        self.assertEqual(second['acknowledgments'], {})
        with self.assertRaises(ValueError):
            self.ack(first)

    def test_peer_reenrollment_does_not_reuse_old_agreement_identity(self):
        first = self.call()
        self.enroll('b', 'CONSUMER')
        with self.assertRaises(ValueError):
            self.ack(first)
        self.assertFalse(self.call()['ready_to_edit'])

    def test_all_named_peers_must_acknowledge_once(self):
        self.enroll('c', 'CONSUMER')
        first = self.call(peer_sessions=['b', 'c'])
        one = self.ack(first)
        self.assertEqual(one['pending_peers'], ['c'])
        self.assertEqual(one['state'], 'awaiting-ack')
        self.assertEqual(self.ack(first)['revision'], first['revision'])
        both = self.ack(first, session='c')
        self.assertEqual(both['state'], 'claimed')
        self.assertEqual(set(both['acknowledgments']), {'b', 'c'})

    def test_specific_break_peers_and_cross_seam_checks_required(self):
        for kwargs in [dict(problem=''), dict(peer_sessions=[]), dict(peer_sessions=['a']),
                       dict(peer_sessions=['missing']), dict(check_paths=['consumer.py']),
                       dict(check_paths=['producer.py', 'test_contract.py'])]:
            with self.subTest(kwargs=kwargs), self.assertRaises((ValueError, OSError)):
                self.call(**kwargs)

    def test_validation_uses_agreed_files_without_requiring_repeated_flags(self):
        first = self.call()
        self.ack(first)
        result = self.call('complete', claim_id=first['claim_id'], evidence='Both original task checks passed', check_paths=[])
        self.assertEqual(set(result['source_hashes']), {'consumer.py', 'producer.py', 'test_contract.py'})
        self.assertEqual(result['state'], 'resolved')

    def test_cli_specific_break_agreement_and_cross_seam_result(self):
        def cli(command, session, workstream, *flags, success=True):
            argv = [sys.executable, '-I', str(ROOT / 'project_intent/_worker_cli.py'), command,
                    '--snapshot', str(self.root / 'snapshot.json'), '--directory', str(self.feed),
                    '--session', session, '--workstream', workstream, *flags]
            result = subprocess.run(argv, cwd=self.checkout, capture_output=True, text=True)
            if success:
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
        (self.checkout / 'producer.py').write_text('PRICE = 1250\ndef total(): return PRICE / 100\n')
        (self.checkout / 'consumer.py').write_text('from producer import PRICE\ndef label(): return f"${PRICE:.2f}"\n')
        plan_flags = ['--seam', 'shop/money', '--problem', 'Consumer must show $12.50 while total remains 12.5',
                      '--repair-path', 'consumer.py', '--peer-session', 'b',
                      '--check-path', 'consumer.py', '--check-path', 'producer.py']
        plan = cli('repair-claim', 'a', 'PRODUCER', *plan_flags)
        self.assertTrue(plan['accepted'])
        self.assertFalse(plan['ready_to_edit'])
        cli('repair-complete', 'a', 'PRODUCER', '--claim-id', plan['claim_id'], '--evidence', 'Passed', success=False)
        ack = cli('repair-ack', 'b', 'CONSUMER', '--repair-id', plan['repair_id'],
                  '--expected-revision', str(plan['revision']))
        self.assertEqual(ack['state'], 'claimed')
        self.assertTrue(cli('repair-claim', 'a', 'PRODUCER', *plan_flags)['ready_to_edit'])
        (self.checkout / 'consumer.py').write_text('from producer import PRICE\ndef label(): return f"${PRICE / 100:.2f}"\n')
        checks = subprocess.run([sys.executable, '-B', '-c',
            'from producer import total; from consumer import label; assert total() == 12.5; assert label() == "$12.50"'],
            cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(checks.returncode, 0, checks.stderr)
        closed = cli('repair-complete', 'a', 'PRODUCER', '--repair-id', plan['repair_id'],
                     '--claim-id', plan['claim_id'], '--evidence', 'Both total and label assertions passed')
        self.assertEqual(closed['state'], 'resolved')
        self.assertEqual(set(closed['source_hashes']), {'consumer.py', 'producer.py'})
        (self.checkout / 'producer.py').write_text('PRICE = 1300\ndef total(): return PRICE / 100\n')
        observed = cli('repair-status', 'b', 'CONSUMER')['repairs'][0]
        self.assertEqual(observed['verification'], 'source-changed-revalidation-required')

    def test_new_failure_can_explicitly_reopen_resolved_revision_once(self):
        resolved = self.complete(self.call())
        with self.assertRaises(ValueError):
            self.call(expected_revision=resolved['revision'])
        with self.assertRaises(ValueError):
            self.call(expected_revision=resolved['revision'] - 1, evidence='New failure')
        new = self.call(session='b', workstream='CONSUMER', expected_revision=resolved['revision'], evidence='New failure')
        self.assertTrue(new['accepted'])
        self.assertFalse(self.call(expected_revision=resolved['revision'], evidence='New failure')['acquired'])

    def test_orientation_does_not_claim_to_have_rehashed_source(self):
        self.complete(self.call())
        row = status(self.feed, 'example/shop', self.identity, verify=False)['repairs'][0]
        self.assertEqual(row['verification'], 'owner-reported-checks-refresh-with-repair-status')

    def test_claim_requires_active_edit_identity_exact_seam_and_bounded_paths(self):
        for kwargs in [dict(session='missing'), dict(seam='invented/name'), dict(paths=['.']),
                       dict(paths=['../consumer.py']), dict(paths=[])]:
            with self.subTest(kwargs=kwargs), self.assertRaises((ValueError, OSError)):
                self.call(**kwargs)
        self.enroll('a', 'PRODUCER', access='inspect')
        with self.assertRaises(ValueError):
            self.call()
        self.enroll('a', 'PRODUCER', avoid_paths=['consumer.py'])
        with self.assertRaises(ValueError):
            self.call()

    def test_claim_scope_cannot_silently_expand(self):
        self.call()
        with self.assertRaises(ValueError):
            self.call(paths=['consumer.py', 'producer.py'])

    def test_scope_and_repository_isolation_and_worktree_visibility(self):
        self.call()
        self.assertEqual(status(self.feed, 'other/scope', self.identity)['repairs'], [])
        other = dict(self.identity, repository_common_dir='/other/.git')
        self.assertEqual(status(self.feed, 'example/shop', other)['repairs'], [])
        linked = dict(self.identity, root='/not-readable-other-worktree')
        self.assertEqual(len(status(self.feed, 'example/shop', linked)['repairs']), 1)

    def test_other_checkout_evidence_is_not_read_or_claimed_as_verified(self):
        self.complete(self.call())
        linked = dict(self.identity, root='/not-readable-other-worktree')
        result = status(self.feed, 'example/shop', linked)['repairs'][0]
        self.assertEqual(result['verification'], 'different-checkout-not-verified-here')

    def test_symlink_evidence_and_feed_fail_closed(self):
        first = self.call()
        (self.checkout / 'linked.py').symlink_to(self.checkout / 'consumer.py')
        with self.assertRaises(ValueError):
            self.call('complete', claim_id=first['claim_id'], evidence='Passed',
                      check_paths=['linked.py', 'consumer.py'])
        (self.feed / 'repairs/bad.json').symlink_to(self.root / 'snapshot.json')
        self.assertEqual(status(self.feed, 'example/shop', self.identity)['coverage'], 'unavailable')
        with self.assertRaises(OSError):
            self.call(session='b', workstream='CONSUMER')

    def test_symlink_repair_alias_cannot_create_second_owner(self):
        first = self.call()
        self.ack(first)
        (self.checkout / 'alias.py').symlink_to(self.checkout / 'consumer.py')
        with self.assertRaises(ValueError):
            self.call(session='b', workstream='CONSUMER', paths=['alias.py'],
                      check_paths=['alias.py', 'producer.py'])
        self.assertEqual(len(status(self.feed, 'example/shop', self.identity)['repairs']), 1)
        self.assertTrue(self.call()['ready_to_edit'])

    def test_symlinked_repair_parent_and_hardlink_aliases_rejected(self):
        (self.checkout / 'src').mkdir()
        (self.checkout / 'alias').symlink_to(self.checkout / 'src', target_is_directory=True)
        with self.assertRaises(ValueError):
            self.call(paths=['alias/new.py'], check_paths=['alias/new.py', 'producer.py'])
        os.link(self.checkout / 'consumer.py', self.checkout / 'hard.py')
        for name in ('consumer.py', 'hard.py'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.call(paths=[name], check_paths=[name, 'producer.py'])

    def test_corrupt_record_is_not_empty_inventory(self):
        (self.feed / 'repairs').mkdir()
        (self.feed / 'repairs/bad.json').write_text('{')
        self.assertEqual(status(self.feed, 'example/shop', self.identity)['coverage'], 'unavailable')
        with self.assertRaises(ValueError):
            self.call()

    def test_unreadable_inventory_cannot_overwrite_existing_owner(self):
        first = self.call()
        with patch('project_intent.repairs.os.scandir', side_effect=PermissionError('unreadable')):
            self.assertEqual(status(self.feed, 'example/shop', self.identity)['coverage'], 'unavailable')
            with self.assertRaises(PermissionError):
                self.call(session='b', workstream='CONSUMER')
        self.assertEqual(self.call()['claim_id'], first['claim_id'])

    @unittest.skipIf(os.geteuid() == 0, 'root bypasses directory permissions; mocked failure tested separately')
    def test_real_write_only_inventory_is_not_empty(self):
        first = self.call()
        directory = self.feed / 'repairs'
        directory.chmod(0o300)
        try:
            self.assertEqual(status(self.feed, 'example/shop', self.identity)['coverage'], 'unavailable')
            with self.assertRaises(PermissionError):
                self.call(session='b', workstream='CONSUMER')
        finally:
            directory.chmod(0o700)
        self.assertEqual(self.call()['claim_id'], first['claim_id'])

    def test_owner_can_release_after_assignment_boundary_revision(self):
        first = self.call()
        self.snapshot['records'][0]['boundaries'] = ['shop/display']
        with self.assertRaises(ValueError):
            self.complete(first)
        self.assertEqual(self.call('release', claim_id=first['claim_id'])['state'], 'open')
        self.assertTrue(self.call(session='b', workstream='CONSUMER')['accepted'])

    def test_cli_orientation_exposes_claim_without_token(self):
        self.call()
        argv = [sys.executable, '-I', str(ROOT / 'project_intent/_worker_cli.py'), 'start',
                '--snapshot', str(self.root / 'snapshot.json'), '--directory', str(self.feed),
                '--workstream', 'CONSUMER']
        result = subprocess.run(argv, cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)['repair_coordination']['repairs'][0]
        self.assertEqual(row['owner_session'], 'a')
        self.assertNotIn('claim_id', row)


if __name__ == '__main__':
    unittest.main()
