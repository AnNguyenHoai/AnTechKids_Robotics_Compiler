"""Small bootstrap helpers for direct execution of repository CLI scripts."""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_repository_root(module_file: str) -> Path:
    """Put the repository root on sys.path when a CLI module is run directly."""
    root = Path(module_file).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root
