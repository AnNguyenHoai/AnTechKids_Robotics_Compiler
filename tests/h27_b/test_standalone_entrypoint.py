import os
from pathlib import Path
import subprocess
import sys


def test_standalone_robostudio_entrypoint_imports_shared_tools():
    """`cd robostudio && python -c 'import main'` must resolve repo tools."""
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, "-c", "import main; import tools.bootstrap_config"],
        cwd=root / "robostudio",
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
