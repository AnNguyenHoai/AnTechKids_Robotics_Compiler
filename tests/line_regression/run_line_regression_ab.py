#!/usr/bin/env python3
"""LINE-REG-01/02/03 source contracts for physical A/B and wireless capture."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def section(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def main() -> int:
    tcrt_h = read("robot-platform/main/src/Sensor/TCRT5000.h")
    tcrt_cpp = read("robot-platform/main/src/Sensor/TCRT5000.cpp")
    follower = read("robot-platform/main/src/Services/Line/LineFollower.cpp")
    telemetry = read("robot-platform/main/src/Diagnostic/LineRegressionTelemetry.cpp")
    firmware_main = read("robot-platform/main/main.ino")
    receiver = read("tools/line_reg_udp_receiver.py")
    pio = read("robot-platform/platformio.ini")

    check(
        "TCRT exposes read-only raw GPIO probe",
        "int ReadHardwareLevelDirect() const;" in tcrt_h
        and "TCRT5000::ReadHardwareLevelDirect() const" in tcrt_cpp,
    )
    check(
        "diagnostics default OFF in sensor source",
        "#ifndef LINE_REGRESSION_DIAGNOSTICS" in tcrt_cpp
        and "#define LINE_REGRESSION_DIAGNOSTICS 0" in tcrt_cpp,
    )
    check(
        "legacy acquisition defaults OFF",
        "#ifndef LINE_REGRESSION_LEGACY_ACQUISITION" in tcrt_cpp
        and "#define LINE_REGRESSION_LEGACY_ACQUISITION 0" in tcrt_cpp,
    )

    update = section(tcrt_cpp, "void TCRT5000::update()", "bool TCRT5000::healthy()")
    check(
        "legacy A/B mode restores immediate hardware acquisition",
        "#if LINE_REGRESSION_LEGACY_ACQUISITION" in update
        and "SampleHardwareDirect();" in update
        and "return;" in update,
    )
    check(
        "snapshot production path remains present",
        "LineSensorSnapshot::IsCycleActive()" in update
        and "LineSensorSnapshot::EnsureSample();" in update
        and "LineSensorSnapshot::RecordConsumer();" in update,
    )

    sample = section(tcrt_cpp, "void TCRT5000::SampleHardwareDirect()", "void TCRT5000::ApplySnapshotReading")
    check(
        "sensor probe is compile-time gated and change-triggered",
        "#if LINE_REGRESSION_DIAGNOSTICS" in sample
        and "_lastReading != _lastDiagnosticReading" in sample
        and "[LINE-REG][SENSOR]" in sample
        and "LineRegressionTelemetry::Emit" in sample,
    )

    check(
        "follower probe reports snapshot-to-motor decision",
        "[LINE-REG][FOLLOW]" in follower
        and "LineSensorSnapshot::Current()" in follower
        and "snapshot.valid" in follower
        and "snapshot.mask" in follower
        and "snapshot.sequence" in follower
        and "semanticError" in follower
        and "leftMotor" in follower
        and "rightMotor" in follower
        and "LineRegressionTelemetry::Emit" in follower,
    )
    check(
        "follower probe is rate limited",
        "static_cast<uint32_t>(now - lastEmitMs) < 100u" in follower,
    )

    check(
        "wireless transport defaults OFF",
        "#ifndef LINE_REGRESSION_UDP" in telemetry
        and "#define LINE_REGRESSION_UDP 0" in telemetry,
    )
    check(
        "control path only queues telemetry",
        "WiFiUDP" not in tcrt_cpp
        and "WiFiUDP" not in follower
        and "enqueueRecord(record);" in telemetry,
    )
    check(
        "wireless queue is bounded and UDP sends one record per update",
        "kQueueCapacity = 16" in telemetry
        and "kRecordSize = 320" in telemetry
        and "kUdpDestinationPort = 4211" in telemetry
        and "g_udp.beginPacket" in telemetry
        and "--g_count;" in telemetry,
    )
    check(
        "UDP flush occurs after normal network service in background phase",
        firmware_main.index("RobotNetworkService::update(ROBOT_NETWORK_SERVICE_BUDGET_US);")
        < firmware_main.index("LineRegressionTelemetry::Update();"),
    )
    check(
        "host receiver preserves raw LINE-REG records",
        "DEFAULT_PORT = 4211" in receiver
        and '"[LINE-REG]" not in line' in receiver
        and 'log.write(line + "\\n")' in receiver,
    )

    production = section(pio, "[env:esp32dev]", "[env:esp32dev_ota]")
    check(
        "production profile has no line regression flags",
        "LINE_REGRESSION_DIAGNOSTICS" not in production
        and "LINE_REGRESSION_LEGACY_ACQUISITION" not in production
        and "LINE_REGRESSION_UDP" not in production,
    )

    snapshot = section(
        pio,
        "[env:esp32dev_line_snapshot_qualification]",
        "[env:esp32dev_line_legacy_qualification]",
    )
    legacy = pio[pio.index("[env:esp32dev_line_legacy_qualification]"):]
    check(
        "snapshot qualification enables probe and wireless capture",
        "-DLINE_REGRESSION_DIAGNOSTICS=1" in snapshot
        and "-DLINE_REGRESSION_LEGACY_ACQUISITION=0" in snapshot
        and "-DLINE_REGRESSION_UDP=1" in snapshot,
    )
    check(
        "legacy qualification enables direct acquisition and wireless capture",
        "-DLINE_REGRESSION_DIAGNOSTICS=1" in legacy
        and "-DLINE_REGRESSION_LEGACY_ACQUISITION=1" in legacy
        and "-DLINE_REGRESSION_UDP=1" in legacy,
    )
    check(
        "both A/B profiles inherit production board configuration",
        snapshot.count("extends = env:esp32dev") == 1
        and legacy.count("extends = env:esp32dev") >= 1,
    )

    print("LINE-REG-01/02/03 qualification contracts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
