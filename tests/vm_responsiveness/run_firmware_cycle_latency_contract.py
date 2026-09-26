#!/usr/bin/env python3
"""Whole-firmware-cycle latency contract for VM-RT X (#380)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "robot-platform" / "main" / "main.ino"
SERIAL = ROOT / "robot-platform" / "main" / "src" / "Communication" / "SerialCommandHandler.cpp"
NETWORK = ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotNetworkService.cpp"
DISCOVERY = ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotDiscoveryService.cpp"
VM_SLICE = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"
TELEMETRY_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRuntimeTelemetry.h"
TELEMETRY_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRuntimeTelemetry.cpp"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    main = MAIN.read_text(encoding="utf-8")
    serial = SERIAL.read_text(encoding="utf-8")
    network = NETWORK.read_text(encoding="utf-8")
    discovery = DISCOVERY.read_text(encoding="utf-8")
    vm_slice = VM_SLICE.read_text(encoding="utf-8")
    telemetry_h = TELEMETRY_H.read_text(encoding="utf-8")
    telemetry = TELEMETRY_CPP.read_text(encoding="utf-8")

    # Serial input must never wait for a delimiter/timeout in the control loop.
    require("readStringUntil" not in serial,
            "serial command input must not use timeout-blocking readStringUntil")
    require("kSerialBytesPerCycle" in serial and "kSerialCommandMaxLength" in serial,
            "serial parser must expose explicit per-cycle and buffer bounds")
    require("consumed < kSerialBytesPerCycle" in serial and "Serial.read()" in serial,
            "serial parser must consume a bounded number of bytes incrementally")
    require("g_discardUntilNewline" in serial,
            "oversize serial input must be discarded incrementally without blocking")

    # Fresh sample -> VM -> actuator is the critical phase. Background services
    # must not sit between the sample and RunSlice.
    loop = main[main.index("void loop()") :]
    begin = loop.index("LineSensorSnapshot::BeginCycle();")
    sample = loop.index("SensorManager::instance().updateAll();")
    vm = loop.index("vm.RunSlice(budget);")
    end_snapshot = loop.index("LineSensorSnapshot::EndCycle();")
    serial_call = loop.index("SerialCommandHandler::handle();")
    network_call = loop.index("RobotNetworkService::update(ROBOT_NETWORK_SERVICE_BUDGET_US);")
    require(begin < sample < vm < end_snapshot < serial_call < network_call,
            "firmware must execute sensor -> VM before serial/network background work")
    require("ROBOT_NETWORK_SERVICE_BUDGET_US = 500" in main,
            "normal network background budget must remain explicit")
    require("RobotNetworkService::update(0);" in loop[:begin],
            "active OTA must retain an unrestricted service path only after actuator stop")

    # Network scheduling is bounded between indivisible framework calls.
    require("serviceBudgetExpired" in network,
            "network service must enforce a cooperative inter-call budget")
    require("ArduinoOTA.handle();" in network and "g_server.handleClient();" in network,
            "network service contract must cover OTA and HTTP calls")
    require(network.count("serviceBudgetExpired(startedUs, budgetUs)") >= 3,
            "network budget must be checked between major background calls")
    require("RobotAPI::Stop();" in network[network.index("void onOtaStart()"):network.index("void onOtaEnd()")],
            "Arduino OTA start must stop actuators before flash/network ownership")

    require("while (packetSize > 0)" not in discovery,
            "discovery must not drain an unbounded packet queue in one cycle")
    require("const int packetSize = g_udp.parsePacket();" in discovery,
            "discovery must inspect at most one datagram per update")

    # Whole-cycle/sample cadence and reactive stop timing must be RAM-observable.
    for symbol in (
        "RecordFirmwareCycle",
        "RecordReactiveLineObservation",
        "RecordReactiveStop",
        "maxFirmwareCycleUs",
        "maxLineSamplePeriodUs",
        "maxReactiveSampleToStopUs",
    ):
        require(symbol in telemetry_h or symbol in telemetry,
                f"missing whole-cycle/reactive timing symbol: {symbol}")

    require("Opcode::GetTraceState" in vm_slice and "RecordReactiveLineObservation" in vm_slice,
            "GetTraceState execution must capture the consumed snapshot timestamp")
    require("Opcode::Stop" in vm_slice and "RecordReactiveStop" in vm_slice,
            "Stop execution must capture post-Step/PWM submission time")
    require("vm_rt_reactive" in telemetry and "sample_to_stop_us" in telemetry,
            "qualification output must expose sample-to-stop timing evidence")
    require("vm_rt_cycle_summary" in telemetry and "max_line_sample_period_us" in telemetry,
            "qualification output must expose whole-cycle/sample-cadence evidence")

    print("VM-RT firmware-cycle latency contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
