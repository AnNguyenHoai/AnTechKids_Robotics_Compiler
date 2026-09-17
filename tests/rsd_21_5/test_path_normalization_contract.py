"""RSD-21.5 regression for platform-independent artifact evidence paths."""
from pathlib import Path

from tools import production_e2e


def test_artifact_relative_uses_posix_separators_on_windows_and_posix() -> None:
    root = Path("artifact")
    nested = root / "runtime" / "bin" / "python.exe"
    assert production_e2e._artifact_relative(root, nested) == "runtime/bin/python.exe"
