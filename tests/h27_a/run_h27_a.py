#!/usr/bin/env python3
"""H27-A Robot Discovery & Device Identity contract tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_H = ROOT / "robot-platform/main/src/Communication/RobotIdentity.h"
IDENTITY_CPP = ROOT / "robot-platform/main/src/Communication/RobotIdentity.cpp"
DISCOVERY_H = ROOT / "robot-platform/main/src/Communication/RobotDiscoveryService.h"
DISCOVERY_CPP = ROOT / "robot-platform/main/src/Communication/RobotDiscoveryService.cpp"
NETWORK_CPP = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.cpp"
DISCOVER_TOOL = ROOT / "tools/discover_robot.py"


def main() -> int:
    identity_h = IDENTITY_H.read_text(encoding="utf-8")
    identity_cpp = IDENTITY_CPP.read_text(encoding="utf-8")
    discovery_h = DISCOVERY_H.read_text(encoding="utf-8")
    discovery_cpp = DISCOVERY_CPP.read_text(encoding="utf-8")
    network_cpp = NETWORK_CPP.read_text(encoding="utf-8")
    host_tool = DISCOVER_TOOL.read_text(encoding="utf-8")

    for symbol in ("deviceId", "hostname", "displayName", "target", "firmwareVersion", "capabilitiesJson", "infoJson"):
        assert symbol in identity_h and symbol in identity_cpp, symbol
    assert 'antechkids.robot.v1' in identity_cpp
    assert '"device_id"' in identity_cpp
    assert '"capabilities"' in identity_cpp

    assert 'ANTECHKIDS_ROBOT_DISCOVER_V1' in discovery_cpp
    assert 'ANTECHKIDS_ROBOT_INFO_V1' in discovery_cpp
    assert 'kDiscoveryPort = 4210' in discovery_cpp
    assert 'WiFiUDP' in discovery_cpp
    assert 'parsePacket' in discovery_cpp
    assert 'sendResponse' in discovery_cpp
    assert 'bool begin()' in discovery_h
    assert 'void update(bool robotReady, bool otaReady)' in discovery_h

    assert '#include "RobotIdentity.h"' in network_cpp
    assert '#include "RobotDiscoveryService.h"' in network_cpp
    assert 'RobotIdentity::infoJson' in network_cpp
    assert 'RobotDiscoveryService::begin' in network_cpp
    assert 'RobotDiscoveryService::update' in network_cpp

    assert '255.255.255.255' in host_tool
    assert 'ANTECHKIDS_ROBOT_DISCOVER_V1' in host_tool
    assert 'device_id' in host_tool
    assert 'json.dumps' in host_tool

    print('H27-A Robot Discovery & Device Identity: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
