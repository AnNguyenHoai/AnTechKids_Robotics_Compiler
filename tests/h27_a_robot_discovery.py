#!/usr/bin/env python3
"""Static contract tests for H27-A robot discovery and identity."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IDENTITY_H = ROOT / "robot-platform/main/src/Communication/RobotIdentity.h"
IDENTITY_CPP = ROOT / "robot-platform/main/src/Communication/RobotIdentity.cpp"
DISCOVERY_H = ROOT / "robot-platform/main/src/Communication/RobotDiscoveryService.h"
DISCOVERY_CPP = ROOT / "robot-platform/main/src/Communication/RobotDiscoveryService.cpp"
NETWORK_CPP = ROOT / "robot-platform/main/src/Communication/RobotNetworkService.cpp"
MAIN_INO = ROOT / "robot-platform/main/main.ino"
DISCOVER_TOOL = ROOT / "tools/discover_robot.py"


def test_identity_contract():
    text = IDENTITY_H.read_text(encoding="utf-8")
    source = IDENTITY_CPP.read_text(encoding="utf-8")
    for symbol in ("deviceId", "hostname", "displayName", "target", "firmwareVersion", "capabilitiesJson", "infoJson"):
        assert symbol in text and symbol in source
    assert "antechkids.robot.v1" in source
    assert "device_id" in source
    assert "capabilities" in source


def test_discovery_contract():
    text = DISCOVERY_CPP.read_text(encoding="utf-8")
    header = DISCOVERY_H.read_text(encoding="utf-8")
    assert "ANTECHKIDS_ROBOT_DISCOVER_V1" in text
    assert "ANTECHKIDS_ROBOT_INFO_V1" in text
    assert "4210" in text
    assert "WiFiUDP" in text
    assert "parsePacket" in text
    assert "sendResponse" in text
    assert "bool begin()" in header
    assert "void update(bool robotReady, bool otaReady)" in header


def test_network_exposes_identity_and_discovery():
    network = NETWORK_CPP.read_text(encoding="utf-8")
    main = MAIN_INO.read_text(encoding="utf-8")
    assert '#include "RobotIdentity.h"' in network
    assert '#include "RobotDiscoveryService.h"' in network
    assert "RobotIdentity::infoJson" in network
    assert "RobotDiscoveryService::begin" in network
    assert "RobotDiscoveryService::update" in network
    assert "RobotIdentity::hostname" in main


def test_host_discovery_client():
    text = DISCOVER_TOOL.read_text(encoding="utf-8")
    assert "255.255.255.255" in text
    assert "ANTECHKIDS_ROBOT_DISCOVER_V1" in text
    assert "device_id" in text
    assert "timeout" in text
    assert "json.dumps" in text


if __name__ == "__main__":
    for test in (test_identity_contract, test_discovery_contract, test_network_exposes_identity_and_discovery, test_host_discovery_client):
        test()
    print("H27-A robot discovery tests: PASS")
