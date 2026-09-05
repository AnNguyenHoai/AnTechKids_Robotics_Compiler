#!/usr/bin/env python3
"""H27-B0 contract tests for first-flash Wi-Fi bootstrap."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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

    for path in (generator, config_service, wifi_script, platformio, wifi_header, wifi_cpp, network_cpp, deploy, robot_tab):
        assert path.is_file(), f"missing H27-B0 file: {path}"

    generated = generator.read_text(encoding="utf-8")
    assert "antechkids.robot.bootstrap" in generated
    assert "schema_version" in generated
    assert "Wi-Fi password" in generated

    service = config_service.read_text(encoding="utf-8")
    assert "tools.bootstrap_config" in service
    assert ".robostudio" in service

    pio = platformio.read_text(encoding="utf-8")
    assert "[env:esp32dev_bootstrap]" in pio
    assert "extends = env:esp32dev" in pio

    wifi = wifi_script.read_text(encoding="utf-8")
    assert "ROBOT_BOOTSTRAP_CONFIG" in wifi
    assert "antechkids.robot.bootstrap" in wifi
    assert "ROBOT_BOOTSTRAP_PROVISIONED" in wifi

    header = wifi_header.read_text(encoding="utf-8")
    cpp = wifi_cpp.read_text(encoding="utf-8")
    assert "bool begin()" in header
    assert "Preferences" in cpp
    assert "robot-net" in cpp
    assert "putBool" in cpp
    assert "ROBOT_WIFI_SSID" in cpp

    network = network_cpp.read_text(encoding="utf-8")
    assert '#include "RobotWiFiConfig.h"' in network
    assert "RobotWiFiConfig::begin()" in network
    assert "RobotWiFiConfig::ssid()" in network
    assert "RobotWiFiConfig::otaPassword()" in network

    deploy_text = deploy.read_text(encoding="utf-8")
    assert '"bootstrap"' in deploy_text
    assert "--bootstrap-config" in deploy_text
    assert "esp32dev_bootstrap" in deploy_text

    ui = robot_tab.read_text(encoding="utf-8")
    assert "BootstrapConfigService" in ui
    assert "Generate First-Flash Config" in ui
    assert "Flash New Robot via USB" in ui

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "robot_bootstrap.json"
        import subprocess
        result = subprocess.run(
            [
                "python", str(generator), "generate",
                "--ssid", "Classroom-WiFi",
                "--password", "secret",
                "--ota-password", "ota-secret",
                "--output", str(output),
            ], cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["type"] == "antechkids.robot.bootstrap"
        assert data["schema_version"] == 1
        assert data["wifi"]["ssid"] == "Classroom-WiFi"
        assert data["wifi"]["password"] == "secret"
        assert data["ota"]["password"] == "ota-secret"

    print("H27-B0 PASS: first-flash Wi-Fi bootstrap contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
