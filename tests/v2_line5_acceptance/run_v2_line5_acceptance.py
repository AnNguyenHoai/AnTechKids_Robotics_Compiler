from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE = ROOT / "robot-platform/main/src/Services/Line"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
ROBOT = ROOT / "robot-platform/main/src/Services/Robot"
API_H = ROBOT / "RobotAPI.h"
API_CPP = ROBOT / "RobotAPI.cpp"

HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include <map>

#include "MCP23017Driver.h"
#include "LineSensorBank.h"
#include "LineErrorEstimator.h"
#include "LinePerception.h"
#include "IntersectionDetector.h"
#include "RecoveryStrategy.h"

static uint32_t g_now = 0;
uint32_t millis() { return g_now; }

struct FakeTransport : IMCP23017Transport {
    std::map<uint8_t, uint8_t> regs;
    int portAReads = 0;

    bool ensureBusInitialized() override { return true; }
    bool probe(uint8_t) override { return true; }
    bool writeRegister(uint8_t, uint8_t reg, uint8_t value) override {
        regs[reg] = value;
        return true;
    }
    bool readRegister(uint8_t, uint8_t reg, uint8_t& value) override {
        if (reg == 0x12) ++portAReads;
        value = regs[reg];
        return true;
    }
};

static void close(float a, float b) {
    assert(std::fabs(a - b) < 0.0001f);
}

struct Case {
    uint8_t physical;
    uint8_t canonical;
    float error;
    LineState state;
};

int main() {
    FakeTransport transport;
    MCP23017Driver mcp(transport);
    LineSensorBank bank(mcp);
    assert(bank.begin());

    // End-to-end physical MCP Port-A -> canonical mask -> perception contract.
    const Case cases[] = {
        // physical bits are GPA0=FL, GPA1=L, GPA2=C, GPA3=R, GPA4=FR
        {0b00100, 0b00100,  0.0f, LineState::CENTER},       // 00100
        {0b00110, 0b01100, -0.5f, LineState::LEFT_CENTER},  // 01100
        {0b00011, 0b11000, -1.5f, LineState::LEFT},         // 11000
        {0b11000, 0b00011,  1.5f, LineState::RIGHT},        // 00011
        {0b00000, 0b00000,  0.0f, LineState::LOST},         // 00000
        {0b11111, 0b11111,  0.0f, LineState::INTERSECTION}, // 11111
    };

    for (const auto& tc : cases) {
        transport.regs[0x12] = tc.physical;
        const int before = transport.portAReads;
        uint8_t mask = 0xFF;
        assert(bank.readMask(mask));
        assert(transport.portAReads == before + 1);
        assert(mask == tc.canonical);
        close(LineErrorEstimator::estimate(mask), tc.error);
        assert(LinePerception::interpret(mask) == tc.state);
    }

    // Public contract sanitizes high bits to canonical five eyes.
    close(LineErrorEstimator::estimate(0b11100100), 0.0f);
    assert(LinePerception::interpret(0b11100100) == LineState::CENTER);

    // Frozen temporal intersection policy: first decision only after six
    // samples; 3..5 candidates in a six-sample window is intersection.
    {
        IntersectionDetector detector;
        for (int i = 0; i < 5; ++i) {
            assert(!detector.update(0b11111));
        }
        assert(detector.update(0b00100));
    }

    // Frozen quirk: 6/6 intersection candidates currently returns false.
    // Do not silently change without product/hardware evidence.
    {
        IntersectionDetector detector;
        for (int i = 0; i < 6; ++i) {
            assert(!detector.update(0b11111));
        }
    }

    // Recovery follows the last meaningful direction.
    {
        RecoveryStrategy recovery;
        recovery.setLastDirection(RecoveryStrategy::DIR_RIGHT);
        g_now = 100;
        recovery.reset();
        int left = 0, right = 0;
        recovery.update(0, left, right);
        assert(left == 80 && right == -80);

        // Any non-zero mask preserves frozen V1 immediate-reacquire behavior.
        recovery.update(0b00100, left, right);
        assert(left == 0 && right == 0);
    }

    {
        RecoveryStrategy recovery;
        recovery.setLastDirection(RecoveryStrategy::DIR_LEFT);
        g_now = 1000;
        recovery.reset();
        g_now = 3600; // >2500 ms -> sweep phase
        int left = 0, right = 0;
        recovery.update(0, left, right);
        assert((left == -80 && right == 80) || (left == 80 && right == -80));
    }

    return 0;
}
"""


def test_integrated_line5_cpp_contract() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        arduino = td / "Arduino.h"
        arduino.write_text(
            "#pragma once\n#include <stdint.h>\nuint32_t millis();\n",
            encoding="utf-8",
        )
        src = td / "line5_acceptance.cpp"
        exe = td / "line5_acceptance"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(td), "-I", str(HAL), "-I", str(LINE),
            str(src),
            str(HAL / "MCP23017Driver.cpp"),
            str(LINE / "LineSensorBank.cpp"),
            str(LINE / "LineErrorEstimator.cpp"),
            str(LINE / "LinePerception.cpp"),
            str(LINE / "IntersectionDetector.cpp"),
            str(LINE / "RecoveryStrategy.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_public_raw_api_is_single_canonical_acquisition() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    header = API_H.read_text(encoding="utf-8")

    assert "int16_t GetTraceRaw(int port);" in header
    assert "int16_t ReadLine(int channel);" in header

    start = api.index("int16_t GetTraceRaw(int port)")
    end = api.index("// ===== Initialization =====", start)
    raw = api[start:end]
    assert raw.count("g_lineSensorBank.readMask(") == 1
    assert "SensorManager::instance()" not in raw

    for signature in (
        "void LineBasis(int speed);",
        "void LineFollow(int speed);",
        "void LineStop();",
        "void LineIntersectionStop(int speed, int type);",
        "void LineTurnEncounterLine(int speed, int angle, int direction);",
    ):
        assert signature in header


def test_station_pattern_is_explicit_requirement_gap() -> None:
    # There is no distinct StationPattern/StationDetector implementation in the
    # frozen Line service. IntersectionDetector must not be relabeled as station
    # detection without a product requirement defining station semantics.
    line_text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in LINE.glob("*")
        if p.is_file()
    )
    assert "StationPattern" not in line_text
    assert "StationDetector" not in line_text

    requirement = (
        ROOT / "robot-docs/Robotics_V2_Software_Development_Requirements.md"
    ).read_text(encoding="utf-8")
    section = requirement[
        requirement.index("## V2-TEST-004"):
        requirement.index("## V2-TEST-005"),
    ]
    assert "REQUIREMENT_GAP" in section
    assert "station" in section.lower()


def test_line_response_diagnostic_remains_available() -> None:
    api = API_CPP.read_text(encoding="utf-8")
    for marker in (
        "g_lineResponseDiagnosticEnabled",
        "sensorStartUs",
        "sensorDoneUs",
        "controlDoneUs",
        "outputDoneUs",
        "[LINE-RESPONSE]",
    ):
        assert marker in api, marker


def main() -> int:
    test_integrated_line5_cpp_contract()
    print("PASS: MCP physical bits -> canonical Line5 -> weighted perception/intersection/recovery")
    test_public_raw_api_is_single_canonical_acquisition()
    print("PASS: public Line5 API and raw-mask path remain canonical and single-read")
    test_station_pattern_is_explicit_requirement_gap()
    print("PASS: station-pattern gap is explicit; intersection is not silently relabeled")
    test_line_response_diagnostic_remains_available()
    print("PASS: Line response timing diagnostics remain available for hardware acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
