from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "robot-platform/main/src/Devices"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
API_CPP = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
API_H = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.h"
GPIO = HAL / "GPIO.h"
PROFILE = HAL / "BoardProfile.h"
SERIAL = ROOT / "robot-platform/main/src/Communication/SerialCommandHandler.cpp"

ARDUINO_STUB = r"""
#pragma once
#include <stdint.h>

#define IRAM_ATTR
#define INPUT 0
#define CHANGE 1

typedef void (*InterruptArgHandler)(void*);

extern int g_pin_level[64];
extern InterruptArgHandler g_isr[64];
extern void* g_isr_arg[64];
extern uint32_t g_micros;

inline void pinMode(uint8_t, int) {}
inline int digitalRead(uint8_t pin) { return g_pin_level[pin]; }
inline uint32_t micros() { return g_micros; }
inline void noInterrupts() {}
inline void interrupts() {}
inline void attachInterruptArg(uint8_t pin, InterruptArgHandler cb, void* arg, int) {
    g_isr[pin] = cb;
    g_isr_arg[pin] = arg;
}
"""

HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include "Encoder.h"

int g_pin_level[64] = {0};
InterruptArgHandler g_isr[64] = {nullptr};
void* g_isr_arg[64] = {nullptr};
uint32_t g_micros = 0;

static void edge(uint8_t pin, int level) {
    g_pin_level[pin] = level;
    assert(g_isr[pin] != nullptr);
    g_isr[pin](g_isr_arg[pin]);
}

static void cycle_forward(uint8_t a, uint8_t b) {
    // Frozen Encoder.cpp direction contract:
    // 00 -> 10 -> 11 -> 01 -> 00 contributes +4.
    edge(a, 1);
    edge(b, 1);
    edge(a, 0);
    edge(b, 0);
}

int main() {
    const uint8_t A = 34;
    const uint8_t B = 35;

    Encoder enc(A, B, 4.0f);
    assert(enc.begin());
    assert(enc.getCount() == 0);
    assert(enc.getCountsPerSecond() == 0.0f);
    assert(enc.getRPM() == 0.0f);

    cycle_forward(A, B);
    assert(enc.getCount() == 4);

    g_micros = 1000000;
    enc.update();
    assert(std::fabs(enc.getCountsPerSecond() - 4.0f) < 0.0001f);
    assert(std::fabs(enc.getRPM() - 60.0f) < 0.0001f);
    assert(enc.getDirection() == 1);

    enc.setInverted(true);
    assert(enc.isInverted());
    cycle_forward(A, B);
    assert(enc.getCount() == 0);

    g_micros = 2000000;
    enc.update();
    assert(std::fabs(enc.getCountsPerSecond() + 4.0f) < 0.0001f);
    assert(std::fabs(enc.getRPM() + 60.0f) < 0.0001f);
    assert(enc.getDirection() == -1);

    enc.resetCount(10);
    assert(enc.getCount() == 10);
    assert(enc.getCountsPerSecond() == 0.0f);

    enc.setCountsPerRevolution(8.0f);
    assert(std::fabs(enc.getCountsPerRevolution() - 8.0f) < 0.0001f);
    enc.setCountsPerRevolution(0.0f);
    assert(std::fabs(enc.getCountsPerRevolution() - 8.0f) < 0.0001f);

    return 0;
}
"""

def test_real_encoder_cpp() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "Arduino.h").write_text(ARDUINO_STUB, encoding="utf-8")
        src = td / "encoder_test.cpp"
        exe = td / "encoder_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(td), "-I", str(DEV),
            str(src), str(DEV / "Encoder.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_v2_mapping_and_line5_separation() -> None:
    profile = PROFILE.read_text(encoding="utf-8")
    gpio = GPIO.read_text(encoding="utf-8")

    expected = (
        ("ENCODER_L_A = 34", "ENCODER_LEFT_A_PIN"),
        ("ENCODER_L_B = 35", "ENCODER_LEFT_B_PIN"),
        ("ENCODER_R_A = 36", "ENCODER_RIGHT_A_PIN"),
        ("ENCODER_R_B = 39", "ENCODER_RIGHT_B_PIN"),
    )
    for physical, alias in expected:
        assert physical in profile, physical
        line = next(ln for ln in gpio.splitlines() if ln.startswith(f"#define {alias}"))
        assert "BoardProfile::Pins::ENCODER_" in line

    # V2-SW-004 moved Line5 to MCP Port A. Direct TCRT aliases must never
    # reclaim encoder pins 34/35 or any other ESP32 encoder GPIO.
    assert "SENSOR_TRCT5000_" not in gpio


def test_robotapi_feature_contract() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    header = API_H.read_text(encoding="utf-8")

    assert "static Encoder leftEncoder(ENCODER_LEFT_A_PIN, ENCODER_LEFT_B_PIN, 1.0f);" in api
    assert "static Encoder rightEncoder(ENCODER_RIGHT_A_PIN, ENCODER_RIGHT_B_PIN, 1.0f);" in api
    assert "#if ROBOT_FEATURE_ENCODER" in api
    assert "leftEncoder.begin();" in api and "rightEncoder.begin();" in api

    signatures = (
        "void UpdateEncoders();",
        "int64_t GetEncoderCount(int side);",
        "float GetEncoderCountsPerSecond(int side);",
        "float GetEncoderRPM(int side);",
        "void ResetEncoderCount(int side, int64_t value = 0);",
        "void SetEncoderCountsPerRevolution(int side, float value);",
        "float GetEncoderCountsPerRevolution(int side);",
        "void SetEncoderInverted(int side, bool inverted);",
        "bool GetEncoderInverted(int side);",
    )
    for sig in signatures:
        assert sig in header, sig

    off = api[api.index("#else\nvoid UpdateEncoders() {}"):api.index("#endif\n\nvoid Initialize()", api.index("#else\nvoid UpdateEncoders() {}"))]
    assert "int64_t GetEncoderCount(int side) { (void)side; return 0; }" in off
    assert "float GetEncoderCountsPerSecond(int side) { (void)side; return 0.0f; }" in off
    assert "float GetEncoderRPM(int side) { (void)side; return 0.0f; }" in off
    assert "bool GetEncoderInverted(int side) { (void)side; return false; }" in off


def test_diagnostics_and_health_ready_boundary() -> None:
    serial = SERIAL.read_text(encoding="utf-8")
    assert "RobotAPI::GetEncoderCount(side)" in serial
    assert "RobotAPI::GetEncoderCountsPerSecond(side)" in serial
    assert "RobotAPI::GetEncoderRPM(side)" in serial
    assert "RobotAPI::GetEncoderCountsPerRevolution(side)" in serial
    assert "RobotAPI::GetEncoderInverted(side)" in serial


def test_decoder_direction_debt_is_not_silently_changed() -> None:
    encoder = (DEV / "Encoder.cpp").read_text(encoding="utf-8")
    decoder = (ROOT / "robot-platform/main/src/Sensor/QuadratureDecoder.h").read_text(encoding="utf-8")
    assert "const int8_t Encoder::TRANSITION_TABLE[16]" in encoder
    assert "class QuadratureDecoder" in decoder
    # The two tables use opposite sign conventions today. V2-SW-009 freezes
    # Encoder.cpp behavior until physical direction is verified.
    assert "0, -1,  1,  0" in encoder
    assert "0, +1, -1,  0" in decoder


def main() -> int:
    test_real_encoder_cpp()
    print("PASS: real Encoder.cpp quadrature/count/CPS/RPM/inversion regression")
    test_v2_mapping_and_line5_separation()
    print("PASS: V2 encoder GPIO34/35/36/39 mapping and Line5 separation")
    test_robotapi_feature_contract()
    print("PASS: encoder RobotAPI signatures and feature ON/OFF contract")
    test_diagnostics_and_health_ready_boundary()
    print("PASS: encoder data remains available to serial diagnostics")
    test_decoder_direction_debt_is_not_silently_changed()
    print("PASS: decoder sign-convention debt recorded without silent behavior change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
