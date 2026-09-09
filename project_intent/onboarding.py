"""Read-only onboarding guidance; no task selection, enrollment or broad searches."""
from pathlib import Path
import shlex
import sys


def documentation():
    # Resolve the installed module, not cwd or a search across other checkouts.
    root = Path(__file__).resolve().parents[1]
    paths = {
        'readme': root / 'README.md',
        'task_registration': root / 'docs/TASK_REGISTRATION.md',
        'reporting': root / 'docs/REPORTING.md',
        'skill': root / 'skills/project-intent/SKILL.md',
        'worker_instructions': root / 'skills/project-intent/assets/worker-instructions.md',
    }
    return {
        'source_root': str(root),
        'documents': {key: {'path': str(path), 'available': path.is_file()} for key, path in paths.items()},
        'search_boundary': 'Use these exact installed paths and task-checkout documentation. Do not search other sessions, transcripts, evaluation archives, home directories or private service configuration for onboarding help. Missing packaged documentation is a packaging gap, not permission to widen the search.',
    }


def command_argv(args, command, scope=None, *extra):
    # Bind generated commands to this release, not a same-named package in cwd
    # or PYTHONPATH. Keep cwd unchanged for the worker's checkout observation.
    launcher = Path(__file__).resolve().with_name('_worker_cli.py')
    argv = [sys.executable, '-I', str(launcher), command]
    if args.worker_config:
        argv += ['--worker-config', args.worker_config]
    if args.checkout:
        argv += ['--checkout', args.checkout]
    if scope:
        argv += ['--scope', scope]
    return argv + list(extra)


def inventory_recovery(args, entries):
    # Never widen beyond the already selected entries. Multiple visible scopes
    # get separate commands so the worker can choose its task's actual scope.
    return [
        {'scope': scope, 'argv': argv, 'command': shlex.join(argv)}
        for scope in sorted(entries)
        for argv in [command_argv(args, 'discover', scope)]
    ]
