"""Read-only onboarding guidance; no task selection, enrollment or broad searches."""
from pathlib import Path
import shlex
import sys

from .worker_context import integration_context


def documentation():
    # Resolve the installed module, not cwd or a search across other checkouts.
    root = Path(__file__).resolve().parents[1]
    paths = {
        'readme': root / 'README.md',
        'task_registration': root / 'docs/TASK_REGISTRATION.md',
        'reporting': root / 'docs/REPORTING.md',
        'repair_coordination': root / 'docs/REPAIR_COORDINATION.md',
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
        argv += ['--worker-config', str(Path(args.worker_config).resolve())]
    if args.checkout:
        argv += ['--checkout', str(Path(args.checkout).resolve())]
    for option in ('snapshot', 'directory'):
        if getattr(args, option, None):
            argv += ['--' + option, str(Path(getattr(args, option)).resolve())]
    if scope:
        argv += ['--scope', scope]
    return argv + list(extra)


def integration_guidance(args, state, selected, checkout, touching=(), seams=(), session=None):
    context=integration_context(state,selected,checkout,touching,seams,session)
    extra=['--workstream',selected['id']]
    if session:
        extra += ['--session',session]
    for path in touching:
        extra += ['--touching-path',path]
    for seam in seams:
        extra += ['--touching-seam',seam]
    argv=command_argv(args,'start',state['id'],*extra)
    if checkout:
        if '--checkout' in argv:
            argv[argv.index('--checkout')+1]=checkout['root']
        else:
            argv += ['--checkout',checkout['root']]
        context['refresh']={'argv':argv,'command':shlex.join(argv)}
    else:
        context['refresh']={'argv':None,'command':None,
                            'unavailable':'Checkout could not be observed; supply the actual --checkout before refreshing.'}
    context['next_action']=(
        'Account for the related tasks even before peers enroll. When changing a contract, keep your working '
        'summary current with the affected symbols/fields/units and replacements. Before claiming completion, '
        'refresh this context and inspect current affected imports/callers, not only your initial file reads. '
        'Where authorized, check producer and consumer together; if checks cannot run, report integration as '
        'unverified, not complete. For a competing repair, use the existing one-repairer peer-acknowledgment '
        'protocol. This is not an instruction to wait for every worker or override user exclusions.')
    if not context['related_work'] and not context['last_known_workers']:
        context['next_action']='No related declared work is visible in this context. This is not proof of no concurrent changes; no additional integration ceremony is imposed.'
    return context


def inventory_recovery(args, entries):
    # Never widen beyond the already selected entries. Multiple visible scopes
    # get separate commands so the worker can choose its task's actual scope.
    return [
        {'scope': scope, 'argv': argv, 'command': shlex.join(argv)}
        for scope in sorted(entries)
        for argv in [command_argv(args, 'discover', scope)]
    ]
