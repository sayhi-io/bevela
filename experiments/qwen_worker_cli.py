"""Qwen-only entry point; backend commands for other callers are unchanged."""
import argparse
from pathlib import Path
import sys
from types import SimpleNamespace


class WorkerParser(argparse.ArgumentParser):
    def add_argument(self, *args, **kwargs):
        if args == ('command',):
            kwargs['choices'] = [name for name in kwargs['choices'] if name != 'presence']
        return super().add_argument(*args, **kwargs)


def main():
    # Copied to the disposable release's project_intent/_worker_cli.py, so
    # onboarding's generated commands keep using this same filtered entry point.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from project_intent import cli
    original = cli.argparse
    try:
        # Do not mutate argparse globally or change the backend parser source.
        cli.argparse = SimpleNamespace(ArgumentParser=WorkerParser)
        cli.main()
    finally:
        cli.argparse = original


if __name__ == '__main__':
    main()
