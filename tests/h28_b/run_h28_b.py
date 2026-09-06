#!/usr/bin/env python3
"""H28-B deployment runtime hardening contract tests."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.deploy_robot as deploy_robot
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


def test_bootstrap_propagates_generated_credentials_to_platformio():
    captured = {}

    def fake_run(command, *, env=None, cwd=ROOT, timeout=DEFAULT_PROCESS_TIMEOUT_SECONDS):
        captured["command"] = command
        captured["env"] = env
        captured["cwd"] = cwd
        captured["timeout"] = timeout

    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "robot_bootstrap.json"
        config_path.write_text(
            json.dumps({
                "type": "antechkids.robot.bootstrap",
                "schema_version": 1,
                "wifi": {"ssid": "classroom-wifi", "password": "wifi-secret"},
                "ota": {"password": "ota-secret"},
            }),
            encoding="utf-8",
        )
        original_run = deploy_robot.run
        deploy_robot.run = fake_run
        try:
            assert deploy_robot.flash_bootstrap(config_path, "COM4") == 0
        finally:
            deploy_robot.run = original_run

    assert captured["command"][:3] == [sys.executable, "-m", "platformio"]
    assert "-e" in captured["command"]
    assert "esp32dev_bootstrap" in captured["command"]
    assert "-t" in captured["command"]
    assert "upload" in captured["command"]
    assert "--upload-port" in captured["command"]
    assert "COM4" in captured["command"]
    assert captured["cwd"] == deploy_robot.PLATFORM
    assert captured["env"]["ROBOT_BOOTSTRAP_CONFIG"] == str(config_path.resolve())
    assert captured["env"]["ROBOT_WIFI_SSID"] == "classroom-wifi"
    assert captured["env"]["ROBOT_WIFI_PASSWORD"] == "wifi-secret"
    assert captured["env"]["ROBOT_OTA_PASSWORD"] == "ota-secret"


def test_bootstrap_build_forces_generated_credentials_before_nvs_fallback():
    wifi = (ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotWiFiConfig.cpp").read_text(encoding="utf-8")
    wifi_config = (ROOT / "robot-platform" / "wifi_config.py").read_text(encoding="utf-8")

    bootstrap_guard = wifi.index("#ifdef ROBOT_BOOTSTRAP_PROVISIONED")
    stored_fallback = wifi.index("if (loadStored())")

    assert bootstrap_guard < stored_fallback
    assert "g_ssid = ROBOT_WIFI_SSID;" in wifi[bootstrap_guard:stored_fallback]
    assert "g_password = ROBOT_WIFI_PASSWORD;" in wifi[bootstrap_guard:stored_fallback]
    assert "g_otaPassword = ROBOT_OTA_PASSWORD;" in wifi[bootstrap_guard:stored_fallback]
    assert "save(g_ssid.c_str(), g_password.c_str(), g_otaPassword.c_str())" in wifi[bootstrap_guard:stored_fallback]
    assert 'env.Append(CPPDEFINES=[("ROBOT_BOOTSTRAP_PROVISIONED", "1")])' in wifi_config


def main() -> int:
    deploy = (ROOT / "tools" / "deploy_robot.py").read_text(encoding="utf-8")
    flash = (ROOT / "tools" / "flash.py").read_text(encoding="utf-8")
    service = (ROOT / "robostudio" / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    robot_tab = (ROOT / "robostudio" / "ui" / "robot_tab.py").read_text(encoding="utf-8")
    runtime = (ROOT / "tools" / "deployment_runtime.py").read_text(encoding="utf-8")

    test_bootstrap_propagates_generated_credentials_to_platformio()
    test_bootstrap_build_forces_generated_credentials_before_nvs_fallback()

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
