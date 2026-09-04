#!/usr/bin/env python3
"""H27-A.1 Discovery & Identity Hardening contract tests."""

from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_H = ROOT / "robot-platform/main/src/Communication/RobotIdentity.h"
IDENTITY_CPP = ROOT / "robot-platform/main/src/Communication/RobotIdentity.cpp"
DISCOVERY_H = ROOT / "robot-platform/main/src/Communication/RobotDiscoveryService.h"
DISCOVERY_CPP = ROOT / "robot-platform/main/src/Communication/RobotDiscoveryService.cpp"
NETWORK_H = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.h"
NETWORK_CPP = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.cpp"
WIFI_CONFIG = ROOT / "robot-platform/wifi_config.py"
PLATFORMIO = ROOT / "robot-platform/platformio.ini"
DEPLOY_TOOL = ROOT / "tools/deploy_robot.py"
DISCOVER_TOOL = ROOT / "tools/discover_robot.py"


def load_discovery_tool():
    spec = importlib.util.spec_from_file_location("discover_robot", DISCOVER_TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def has_cpp_json_key(source: str, key: str) -> bool:
    """Accept JSON keys represented as C++ escaped string literals.

    C++ JSON builders commonly store a quote as `\\"`, so a raw source check
    for `\"key\"` is incorrect even though the generated JSON contains the
    required key. Keep the contract source-based, but match both spellings.
    """
    raw_key = f'"{key}"'
    escaped_key = f'\\"{key}\\"'
    return raw_key in source or escaped_key in source


def main() -> int:
    identity_h = IDENTITY_H.read_text(encoding="utf-8")
    identity_cpp = IDENTITY_CPP.read_text(encoding="utf-8")
    discovery_h = DISCOVERY_H.read_text(encoding="utf-8")
    discovery_cpp = DISCOVERY_CPP.read_text(encoding="utf-8")
    network_h = NETWORK_H.read_text(encoding="utf-8")
    network_cpp = NETWORK_CPP.read_text(encoding="utf-8")
    wifi_config = WIFI_CONFIG.read_text(encoding="utf-8")
    platformio = PLATFORMIO.read_text(encoding="utf-8")
    deploy = DEPLOY_TOOL.read_text(encoding="utf-8")
    host_tool = DISCOVER_TOOL.read_text(encoding="utf-8")

    assert "kSchemaVersion = 1" in identity_h
    for key in ("schema_version", "device_id", "robot_ready", "network_ready", "ready", "ota", "capabilities"):
        assert has_cpp_json_key(identity_cpp, key), key

    assert "bool begin();" in discovery_h
    assert "void update(bool robotReady, bool networkReady, bool otaReady);" in discovery_h
    assert "kRetryIntervalMs = 2000UL" in discovery_cpp
    assert "g_udp.stop()" in discovery_cpp
    assert "packetSize >= static_cast<int>(kMaxRequestSize)" in discovery_cpp
    assert "ANTECHKIDS_ROBOT_DISCOVER_V1" in discovery_cpp
    assert "ANTECHKIDS_ROBOT_INFO_V1" in discovery_cpp

    assert "bool isOtaReady();" in network_h
    assert "bool isUpdateInProgress();" in network_h
    assert "setRobotReady(bool value)" in network_h
    assert "ROBOT_OTA_PASSWORD \"\"" in network_cpp
    assert "g_robotReady && g_networkReady" in network_cpp
    assert "RobotIdentity::infoJson(g_robotReady, g_networkReady, g_otaReady)" in network_cpp
    assert "will retry" in network_cpp

    assert 'ota_password = os.getenv("ROBOT_OTA_PASSWORD", "")' in wifi_config
    assert "esp32dev_ota" in wifi_config
    assert "must be set for esp32dev_ota builds" in wifi_config
    assert '"robot-ota"' not in wifi_config
    assert '"robot-ota"' not in network_cpp

    assert 'platformio_environment="esp32dev_ota" if args.mode == "ota" else "esp32dev"' in deploy
    assert 'default="robot-ota"' not in deploy

    assert "def validate_robot_record(payload: object) -> bool:" in host_tool
    assert "schema_version" in host_tool
    assert "robot_ready" in host_tool
    assert "network_ready" in host_tool
    assert "ipaddress.ip_address" in host_tool

    tool = load_discovery_tool()
    valid = {
        "protocol": "antechkids.robot.v1",
        "schema_version": 1,
        "device_id": "robot-A1B2C3D4E5F6",
        "name": "AnTechKids Robot D4E5F6",
        "hostname": "robot-D4E5F6.local",
        "ip": "192.168.1.42",
        "target": "esp32",
        "firmware": "dev",
        "robot_ready": True,
        "network_ready": True,
        "ready": True,
        "ota": True,
        "capabilities": {"motor": True, "imu": False},
    }
    assert tool.validate_robot_record(valid)

    invalid = dict(valid)
    invalid["ready"] = False
    assert not tool.validate_robot_record(invalid)

    invalid = dict(valid)
    invalid["device_id"] = "robot-not-a-mac"
    assert not tool.validate_robot_record(invalid)

    invalid = dict(valid)
    invalid["schema_version"] = 2
    assert not tool.validate_robot_record(invalid)

    print("H27-A.1 Discovery & Identity Hardening: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
