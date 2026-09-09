"""Exact-release entry point for printed worker commands (invoke with Python -I)."""
from pathlib import Path
import sys


if __name__ == '__main__':
    # Isolated Python omits cwd/PYTHONPATH. Add only this resolved release root;
    # do not chdir, since enrollment must observe the worker's actual checkout.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from project_intent.cli import main
    main()
