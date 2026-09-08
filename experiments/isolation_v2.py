"""Study-only allowlisted filesystem runner; v1 studies remain unchanged.

Network is shared intentionally for model transport and worker-local browsers.
This is context/read isolation, not hostile multi-tenant network containment.
"""
from pathlib import Path
import os
import subprocess


SYSTEM_DIRS = ('/usr', '/bin', '/sbin', '/lib', '/lib64')
SYSTEM_FILES = ('/etc/resolv.conf', '/etc/hosts', '/etc/nsswitch.conf',
                '/etc/passwd', '/etc/group', '/etc/localtime')


def command(root, checkout, argv, *, readonly=(), writable=()):
    root = Path(root).resolve(strict=True)
    checkout = Path(checkout).resolve(strict=True)
    if not (root / 'DISPOSABLE_TRIAL').is_file():
        raise ValueError('Missing disposable trial marker')
    if checkout == root or not checkout.is_relative_to(root):
        raise ValueError('Checkout must be inside trial root')
    if not argv:
        raise ValueError('Missing worker command')
    mounts = []
    for mode, paths in (('--ro-bind', readonly), ('--bind', (checkout, *writable))):
        for raw in paths:
            path = Path(raw).resolve(strict=True)
            if path == root or not path.is_relative_to(root):
                raise ValueError('Explicit worker resources must be descendants of trial root')
            if any(path == old or path.is_relative_to(old) or old.is_relative_to(path)
                   for _, old in mounts):
                raise ValueError('Overlapping resource mounts are ambiguous')
            mounts.append((mode, path))
    args = ['bwrap', '--die-with-parent', '--new-session', '--unshare-user',
            '--unshare-pid', '--unshare-ipc', '--unshare-uts', '--clearenv',
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
            '--dir', '/home/worker', '--setenv', 'HOME', '/home/worker',
            '--setenv', 'PATH', '/usr/bin:/bin', '--setenv', 'LANG', 'C.UTF-8',
            '--setenv', 'GIT_CONFIG_NOSYSTEM', '1', '--setenv', 'GIT_CONFIG_GLOBAL', '/dev/null']
    for name in SYSTEM_DIRS:
        path = Path(name)
        if path.is_symlink():
            args += ['--symlink', os.readlink(path), name]
        elif path.exists():
            args += ['--ro-bind', name, name]
    for name in (*SYSTEM_FILES, '/etc/ssl', '/etc/fonts'):
        if Path(name).exists():
            args += ['--ro-bind', name, name]
    for mode, path in mounts:
        args += [mode, str(path), str(path)]
    return args + ['--chdir', str(checkout), '--', *map(str, argv)]


def run(root, checkout, argv, *, readonly=(), writable=(), timeout=60):
    return subprocess.run(command(root, checkout, argv, readonly=readonly,
                                  writable=writable), text=True, capture_output=True,
                          timeout=timeout, check=False)
