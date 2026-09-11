"""Portable host resources for Python-only checks through the historical sandbox.

Never used by experiment launchers; historical recorder source stays unchanged.
"""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


@contextmanager
def evaluator_environment(native, temporary_home):
    (temporary_home / '.npm-global').mkdir()
    historical_sandbox = native.sandbox

    def sandbox(*args, **kwargs):
        command = historical_sandbox(*args, **kwargs)
        # The original ARM host needed no /lib64. On x86 this read-only system
        # directory supplies the interpreter's dynamic loader, not user data.
        if Path('/lib64').exists():
            command[1:1] = ['--ro-bind', '/lib64', '/lib64']
        return command

    with patch.object(Path, 'home', return_value=temporary_home), \
            patch.object(native, 'sandbox', sandbox):
        yield
