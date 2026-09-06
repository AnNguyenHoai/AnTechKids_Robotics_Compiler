#!/usr/bin/env python3
"""H28-B deployment runtime hardening contract tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.deployment_runtime import (
    DEFAULT_PROCESS_TIMEOUT_SECONDS,
    DeploymentRuntimeError,
    platformio_command,
    run_process,
)
from tools.deploy_robot import (
    _copy_program_header_safely,
    _restore_program_header,
    normalize_robot_host,
)


def main() -> int:
    deploy = (ROOT / "tools" / "deploy_robot.py").read_text(encoding="utf-8")
    flash = (ROOT / "tools" / "flash.py").read_text(encoding="utf-8")
    service = (ROOT / "robostudio" / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    robot_tab = (ROOT / "robostudio" / "ui" / "robot_tab.py").read_text(encoding="utf-8")
    runtime = (ROOT / "tools" / "deployment_runtime.py").read_text(encoding="utf-8")

    assert DEFAULT_PROCESS_TIMEOUT_SECONDS == 300.0
    assert platformio_command("run", "-e", "esp32dev")[:3] == [sys.executable, "-m", "platformio"]
    assert "subprocess.Popen" in runtime
    assert "DeploymentRuntimeError" in runtime
    assert "threading.Thread" in runtime
    assert "subprocess.check_call" not in deploy
    assert "subprocess.check_call" not in flash

    streamed: list[str] = []
    result = run_process(
        [sys.executable, "-c", "print('runtime-line-1', flush=True); print('runtime-line-2', flush=True)"],
        cwd=ROOT,
        timeout=10,
        on_output=streamed.append,
    )
    assert result.returncode == 0
    assert "runtime-line-1" in result.output
    assert "runtime-line-2" in result.output
    assert streamed == ["runtime-line-1\n", "runtime-line-2\n"]

    try:
        run_process(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            cwd=ROOT,
            timeout=0.1,
        )
    except DeploymentRuntimeError as exc:
        assert "timed out" in str(exc).lower()
    else:
        raise AssertionError("run_process must enforce its timeout")

    assert normalize_robot_host("robot-470968.local") == "robot-470968.local"
    assert normalize_robot_host("192.168.0.106") == "192.168.0.106"
    for invalid in ("", "http://robot.local", "robot.local/path", "robot.local\\path", "robot name"):
        try:
            normalize_robot_host(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid robot host accepted: {invalid!r}")

    assert 'platformio_command("run", "-e", "esp32dev_ota")' in deploy
    assert 'platformio_command("run", "-e", "esp32dev_bootstrap", "-t", "upload")' in deploy
    assert "preflight_robot(args.robot)" in deploy
    assert "--process-timeout" in deploy
    assert "--verify-timeout" in deploy
    assert "_copy_program_header_safely" in deploy
    assert "_restore_program_header" in deploy
    assert "platformio_command(" in flash

    assert "on_output: DeploymentOutputCallback" in service
    assert "timeout=360.0" in service
    assert "self.output.emit" in robot_tab
    assert "def append_logs" in robot_tab
    assert "without stealing the user's scroll position" in robot_tab

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "new.h"
        destination = tmp_path / "generated_program.h"
        source.write_text("new", encoding="utf-8")
        destination.write_text("old", encoding="utf-8")
        previous = _copy_program_header_safely(source, destination)
        assert previous == b"old"
        assert destination.read_text(encoding="utf-8") == "new"
        _restore_program_header(destination, previous)
        assert destination.read_text(encoding="utf-8") == "old"

    print("H28-B PASS: deployment runtime hardening + live output + bounded subprocesses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
