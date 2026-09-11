import hashlib
from pathlib import Path
import unittest


class FrozenQwenSourceTests(unittest.TestCase):
    def test_original_cohort_recorder_is_preserved_byte_for_byte(self):
        root = Path(__file__).resolve().parents[1] / 'experiments/frozen/qwen-distributed-candidate2-v1'
        expected = {
            'qwen_code_adapter.py.txt': 'a55ef9d134355732ab115729a502def5f96dc80caf50f3a080660ab34a1f1d51',
            'qwen_distributed_study.py.txt': 'cd413553362119e588a4893958288d47e9311206b16f5d28142ed32542b265a0'}
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
