#!/usr/bin/env python3
"""VM-RT #385: fixed-rate line sampling qualification contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def main() -> int:
    snapshot_h = read("robot-platform/main/src/Sensor/LineSensorSnapshot.h")
    snapshot_cpp = read("robot-platform/main/src/Sensor/LineSensorSnapshot.cpp")
    tcrt_h = read("robot-platform/main/src/Sensor/TCRT5000.h")
    tcrt_cpp = read("robot-platform/main/src/Sensor/TCRT5000.cpp")
    pio = read("robot-platform/platformio.ini")
    telemetry_cpp = read("robot-platform/main/src/Services/VM/VMRuntimeTelemetry.cpp")

    check("fixed-rate API is additive", "StartFixedRateSampling" in snapshot_h and "StopFixedRateSampling" in snapshot_h)
    check("snapshot exposes interval evidence", "sampleIntervalUs" in snapshot_h)
    check("snapshot exposes jitter evidence", "maxSampleJitterUs" in snapshot_h)
    check("snapshot exposes stale evidence", "staleCount" in snapshot_h)
    check("snapshot identifies fixed-rate source", "fixedRateActive" in snapshot_h)

    qualification = pio.split("[env:esp32dev_vm_qualification]", 1)[1]
    production = pio.split("[env:esp32dev]", 1)[1].split("[env:esp32dev_ota]", 1)[0]
    check("qualification enables fixed-rate sampler", "-DVM_RT_FIXED_RATE_LINE_SAMPLING=1" in qualification)
    check("production does not enable fixed-rate sampler", "VM_RT_FIXED_RATE_LINE_SAMPLING" not in production)

    begin = between(snapshot_cpp, "void BeginCycle()", "void EndCycle()")
    check("qualification target is 1 kHz", "StartFixedRateSampling(1000u, 3000u)" in begin)
    check("fixed-rate bootstrap is build-flag gated", "#if VM_RT_FIXED_RATE_LINE_SAMPLING" in begin)

    producer = between(snapshot_cpp, "void sampleFixedRateOnce()", "#if defined(ARDUINO_ARCH_ESP32)\nvoid fixedRateTask")
    check("read-only direct sensor API exists", "ReadHardwareDetectedDirect() const" in tcrt_h and "TCRT5000::ReadHardwareDetectedDirect() const" in tcrt_cpp)
    check("producer performs exactly three read-only sensor reads", producer.count("ReadHardwareDetectedDirect()") == 3)
    check("producer never mutates legacy TCRT cache", "SampleHardwareDirect()" not in producer and "ApplySnapshotReading(" not in producer)
    check("producer publishes canonical coherent mask", "next.left ? 4 : 0" in producer and "next.center ? 2 : 0" in producer and "next.right ? 1 : 0" in producer)
    check("producer timestamps each sample", "next.timestampUs = micros()" in producer)
    check("producer publication is protected", "portENTER_CRITICAL" in producer and "g_fixedLatest = next" in producer and "portEXIT_CRITICAL" in producer)

    task = between(snapshot_cpp, "void fixedRateTask(void*)", "#endif\n}")
    for forbidden in ("Serial", "RobotAPI", "setMotors", "ledcWrite", "delay("):
        check(f"sampler task excludes {forbidden}", forbidden not in task)
    check("sampler task uses periodic scheduler", "vTaskDelayUntil" in task)
    check("sampler task only invokes sampling helper", "sampleFixedRateOnce()" in task)

    ensure = between(snapshot_cpp, "bool EnsureSample()", "void RecordConsumer()")
    check("consumer copies latest published sample", "latest = g_fixedLatest" in ensure)
    check("consumer has explicit stale threshold", "nowUs - latest.timestampUs" in ensure and "g_staleAfterUs" in ensure)
    check("stale sample fails safe to zero mask", "g_snapshot.mask = fresh ? latest.mask : 0u" in ensure)
    check("stale sample becomes invalid", "g_snapshot.valid = fresh" in ensure)
    check("stale observations are counted", "++g_staleCount" in ensure)
    check("consumer does not perform physical reads in fixed-rate mode", "g_snapshot.physicalReadCount = 0" in ensure)
    check("consumer applies coherent published values at legacy boundary", all(token in ensure for token in (
        "left->ApplySnapshotReading(latest.left ? 1 : 0)",
        "center->ApplySnapshotReading(latest.center ? 1 : 0)",
        "right->ApplySnapshotReading(latest.right ? 1 : 0)",
    )))

    start = between(snapshot_cpp, "bool StartFixedRateSampling", "void StopFixedRateSampling")
    check("restart cannot overlap a stopping producer", "g_fixedRateTask != nullptr" in start)

    check("existing qualification telemetry records sample period", "last_line_sample_period_us" in telemetry_cpp)
    check("existing qualification telemetry records max sample period", "max_line_sample_period_us" in telemetry_cpp)

    print("VM-RT #385 fixed-rate line sampling contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
