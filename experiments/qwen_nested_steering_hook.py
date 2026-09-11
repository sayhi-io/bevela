"""Distributed adapter for frozen v1 steering: bounded nested source paths only."""
import hashlib
import importlib.util
import os
from pathlib import Path
import stat

spec = importlib.util.spec_from_file_location('frozen_steering', Path(__file__).with_name('qwen_steering_hook.py'))
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def file_digest(root, name):
    path = Path(name)
    if path.is_absolute() or not path.parts or any(p in ('.', '..') for p in path.parts):
        raise ValueError('Bounded relative source path required')
    # Traverse directory descriptors so a symlink swap cannot escape the checkout.
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[:-1]:
            next_directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = next_directory
        fd = os.open(path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('Regular source required')
            raw = stream.read(1048577)
        if len(raw) > 1048576:
            raise ValueError('Source exceeds observation bound')
        return hashlib.sha256(raw).hexdigest()
    except FileNotFoundError:
        return 'missing'
    finally:
        os.close(directory)


hook.file_digest = file_digest

if __name__ == '__main__':
    hook.main()
