#!/usr/bin/env python3
"""H27-B0 contract tests for first-flash Wi-Fi bootstrap."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    generator = ROOT / "tools" / "bootstrap_config.py"
    config_service = ROOT / "robostudio" / "services" / "bootstrap_config_service.py"
    wifi_script = ROOT / "robot-platform" / "wifi_config.py"
    platformio = ROOT / "robot-platform" / "platformio.ini"
    wifi_header = ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotWiFiConfig.h"
    wifi_cpp = ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotWiFiConfig.cpp"
    network_cpp = ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotNetworkService.cpp"
    deploy = ROOT / "tools" / "deploy_robot.py"
    robot_tab = ROOT / "robostudio" / "ui" / "robot_tab.py"
    docs = ROOT / "docs" / "FIRST_FLASH_ARDUINO.md"

    for path in (generator, config_service, wifi_script, platformio, wifi_header, wifi_cpp, network_cpp, deploy, robot_tab, docs):
        assert path.is_file(), f"missing H27-B0 file: {path}"

    generated = generator.read_text(encoding="utf-8")
    assert "antechkids.robot.bootstrap" in generated
    assert "schema_version" in generated
    assert "Wi-Fi password" in generated
    assert "write_arduino_header" in generated
    assert "ROBOT_BOOTSTRAP_PROVISIONED" in generated

    service = config_service.read_text(encoding="utf-8")
    assert "tools.bootstrap_config" in service
    # B2.3 replaces the historical source/install-relative .robostudio state
    # directory with the canonical external RoboStudio state-root contract.
    assert "runtime_paths.user_data_root" in service
    assert 'self.bootstrap_root = self.state_root / "bootstrap"' in service
    assert "arduino_bootstrap_header" in service
    assert "open_arduino_sketch" in service  # compatibility helper; not used by RoboStudio deployment

    pio = platformio.read_text(encoding="utf-8")
    assert "[env:esp32dev_bootstrap]" in pio
    assert "extends = env:esp32dev" in pio
    assert "src_dir = main" in pio
    assert "build_src_filter = +<*>" in pio

    wifi = wifi_script.read_text(encoding="utf-8")
    assert "ROBOT_BOOTSTRAP_CONFIG" in wifi
    assert "antechkids.robot.bootstrap" in wifi
    assert "ROBOT_BOOTSTRAP_PROVISIONED" in wifi
    assert 'env.get("PIOENV") == "esp32dev_bootstrap"' in wifi

    header = wifi_header.read_text(encoding="utf-8")
    cpp = wifi_cpp.read_text(encoding="utf-8")
    assert "bool begin()" in header
    assert "Preferences" in cpp
    assert "robot-net" in cpp
    assert "putBool" in cpp
    assert "ROBOT_WIFI_SSID" in cpp
    assert "generated_bootstrap_config.h" in cpp

    network = network_cpp.read_text(encoding="utf-8")
    assert '#include "RobotWiFiConfig.h"' in network
    assert "RobotWiFiConfig::begin()" in network
    assert "RobotWiFiConfig::ssid()" in network
    assert "RobotWiFiConfig::otaPassword()" in network

    deploy_text = deploy.read_text(encoding="utf-8")
    assert '"bootstrap"' in deploy_text
    assert "--bootstrap-config" in deploy_text
    assert "esp32dev_bootstrap" in deploy_text
    # deploy_robot.py must use the canonical PlatformIO resolver so frozen
    # RoboStudio deployments can use the application-owned Python runtime
    # without depending on the host interpreter or PATH.
    assert "from tools.deployment_runtime import" in deploy_text
    assert "platformio_command" in deploy_text
    assert 'platformio_command("run"' in deploy_text

    ui = robot_tab.read_text(encoding="utf-8")
    assert "BootstrapConfigService" in ui
    assert "RobotDeploymentService" in ui
    # H27-B0 validates the current RoboStudio first-flash controls. The UI was
    # refined after the original contract was written, so these assertions
    # follow the user-facing labels that are actually rendered now.
    assert "Generate Config" in ui
    assert "Flash via USB" in ui
    assert "_BootstrapFlashWorker" in ui
    assert "flash_first_robot" in ui
    assert "open_arduino_sketch" not in ui

    docs_text = docs.read_text(encoding="utf-8")
    assert "First Flash with PlatformIO" in docs_text
    assert "PlatformIO" in docs_text
    assert "python -m platformio" in docs_text
    assert "esp32dev_bootstrap" in docs_text
    assert "Arduino IDE interaction is not required" in docs_text

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "robot_bootstrap.json"
        header_output = Path(tmp) / "generated_bootstrap_config.h"
        import subprocess
        result = subprocess.run(
            [
                sys.executable, str(generator), "generate",
                "--ssid", "Classroom-WiFi",
                "--password", "secret",
                "--ota-password", "ota-secret",
                "--output", str(output),
                "--arduino-header-output", str(header_output),
            ], cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["type"] == "antechkids.robot.bootstrap"
        assert data["schema_version"] == 1
        assert data["wifi"]["ssid"] == "Classroom-WiFi"
        assert data["wifi"]["password"] == "secret"
        assert data["ota"]["password"] == "ota-secret"
        generated_header = header_output.read_text(encoding="utf-8")
        assert '#define ROBOT_WIFI_SSID "Classroom-WiFi"' in generated_header
        assert '#define ROBOT_WIFI_PASSWORD "secret"' in generated_header
        assert '#define ROBOT_OTA_PASSWORD "ota-secret"' in generated_header
        assert "ROBOT_BOOTSTRAP_PROVISIONED 1" in generated_header

    print("H27-B0 PASS: first-flash Wi-Fi bootstrap + PlatformIO canonical path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
