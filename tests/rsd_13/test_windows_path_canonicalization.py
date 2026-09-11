from __future__ import annotations

import os
from pathlib import Path

from tools.clean_machine_e2e import _canonical


def test_canonical_is_absolute_and_normalized(tmp_path: Path) -> None:
    nested = tmp_path / "RoboStudio" / "runtime" / "bin"
    nested.mkdir(parents=True)
    value = _canonical(nested / ".." / "bin")
    assert value == _canonical(nested)
    assert value.is_absolute()


def test_canonical_preserves_equivalent_existing_path(tmp_path: Path) -> None:
    target = tmp_path / "RoboStudio" / "externalworkspace"
    target.mkdir(parents=True)
    equivalent = Path(os.path.realpath(str(target)))
    assert _canonical(target) == _canonical(equivalent)
