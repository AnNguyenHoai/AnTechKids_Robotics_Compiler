from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from tools import runtime_paths


def test_bundled_tool_uses_explicit_application_home_identity() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        root.mkdir()
        runtime_bin = root / "runtime" / "bin"
        runtime_bin.mkdir(parents=True)
        pio = runtime_bin / "pio.exe"
        pio.write_text("stub", encoding="utf-8")

        with patch.dict(
            os.environ,
            {runtime_paths.APPLICATION_HOME_ENV: str(root)},
            clear=False,
        ), patch.object(runtime_paths, "is_frozen", return_value=True):
            assert runtime_paths.resolve_bundled_tool("pio") == pio
            assert runtime_paths.platformio_command("run") == [str(pio), "run"]
