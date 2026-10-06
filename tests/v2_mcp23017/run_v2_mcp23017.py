from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
DRIVER_CPP = HAL / "MCP23017Driver.cpp"
WIRE_CPP = HAL / "MCP23017WireTransport.cpp"
PROFILE = HAL / "BoardProfile.h"
SYSTEM_I2C_CPP = HAL / "SystemI2CBusManager.cpp"


def test_board_profile_allocation() -> None:
    profile = PROFILE.read_text(encoding="utf-8")
    expected = [
        "ADDRESS = 0x20",
        "LINE_FAR_LEFT = 0",
        "LINE_LEFT = 1",
        "LINE_CENTER = 2",
        "LINE_RIGHT = 3",
        "LINE_FAR_RIGHT = 4",
        "LED_LEFT = 0",
        "LED_RIGHT = 1",
        "BUZZER_CTRL = 2",
    ]
    for needle in expected:
        assert needle in profile, f"Missing MCP BoardProfile allocation: {needle}"


def test_transport_does_not_own_bus_init() -> None:
    wire = WIRE_CPP.read_text(encoding="utf-8")
    assert "SystemI2CBusManager::instance().ensureInitialized()" in wire
    assert "Wire.begin(" not in wire, "MCP transport must not initialize System I2C"
    system = SYSTEM_I2C_CPP.read_text(encoding="utf-8")
    assert "Wire.begin(" in system


def test_motor_safety_independence() -> None:
    combined = DRIVER_CPP.read_text(encoding="utf-8") + WIRE_CPP.read_text(encoding="utf-8")
    for forbidden in ("MotorSafety", "MOTOR_SAFE_EN", "MOTOR_L_IN", "MOTOR_R_IN"):
        assert forbidden not in combined, f"MCP HAL must remain independent from motor safety: {forbidden}"


HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <map>
#include <utility>
#include "MCP23017Driver.h"

struct FakeTransport : IMCP23017Transport {
    bool busOk = true;
    bool present = true;
    bool failRead = false;
    bool failWrite = false;
    std::map<uint8_t, uint8_t> regs;

    bool ensureBusInitialized() override { return busOk; }
    bool probe(uint8_t) override { return present; }

    bool writeRegister(uint8_t, uint8_t reg, uint8_t value) override {
        if (failWrite) return false;
        regs[reg] = value;
        return true;
    }

    bool readRegister(uint8_t, uint8_t reg, uint8_t& value) override {
        if (failRead) return false;
        value = regs[reg];
        return true;
    }
};

int main() {
    {
        FakeTransport t;
        MCP23017Driver d(t);
        assert(d.address() == 0x20);
        assert(d.begin());
        assert(d.healthy());
        assert(d.lastError() == MCP23017Error::OK);
        assert(t.regs[0x00] == 0xFF);
        assert(t.regs[0x01] == 0xFF);
        assert(t.regs[0x0C] == 0x00);
        assert(t.regs[0x0D] == 0x00);

        assert(d.configureInput(MCP23017Port::A, 2, true));
        assert((t.regs[0x00] & (1u << 2)) != 0);
        assert((t.regs[0x0C] & (1u << 2)) != 0);

        assert(d.configureOutput(MCP23017Port::B, 1));
        assert((t.regs[0x01] & (1u << 1)) == 0);
        assert((t.regs[0x0D] & (1u << 1)) == 0);

        t.regs[0x12] = 0xA5;
        uint8_t a = 0;
        assert(d.readPortA(a) && a == 0xA5);

        t.regs[0x13] = 0x5A;
        uint8_t b = 0;
        assert(d.readPortB(b) && b == 0x5A);

        bool pin = false;
        assert(d.readPin(MCP23017Port::A, 0, pin) && pin);
        assert(d.readPin(MCP23017Port::A, 1, pin) && !pin);

        t.regs[0x15] = 0x00;
        assert(d.writePin(MCP23017Port::B, 2, true));
        assert(t.regs[0x15] == 0x04);
        assert(d.writePin(MCP23017Port::B, 2, false));
        assert(t.regs[0x15] == 0x00);

        assert(!d.writePin(MCP23017Port::B, 8, true));
        assert(d.lastError() == MCP23017Error::I2C_ERROR);
    }

    {
        FakeTransport t;
        t.present = false;
        MCP23017Driver d(t);
        assert(!d.begin());
        assert(!d.healthy());
        assert(d.lastError() == MCP23017Error::NOT_FOUND);
    }

    {
        FakeTransport t;
        t.busOk = false;
        MCP23017Driver d(t);
        assert(!d.begin());
        assert(d.lastError() == MCP23017Error::I2C_ERROR);
    }

    {
        FakeTransport t;
        MCP23017Driver d(t);
        assert(d.begin());
        t.failRead = true;
        uint8_t value = 0;
        assert(!d.readPortA(value));
        assert(!d.healthy());
        assert(d.lastError() == MCP23017Error::I2C_ERROR);
    }

    {
        FakeTransport t;
        MCP23017Driver d(t);
        assert(d.begin());
        t.failWrite = true;
        assert(!d.configureOutput(MCP23017Port::B, 0));
        assert(d.lastError() == MCP23017Error::I2C_ERROR);
    }

    return 0;
}
"""


def test_real_cpp_driver_with_mock_transport() -> None:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        harness = td_path / "mcp23017_host_test.cpp"
        exe = td_path / "mcp23017_host_test"
        harness.write_text(HARNESS, encoding="utf-8")
        cmd = [
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL),
            str(harness), str(DRIVER_CPP),
            "-o", str(exe),
        ]
        subprocess.run(cmd, check=True)
        subprocess.run([str(exe)], check=True)


def main() -> int:
    test_board_profile_allocation()
    print("PASS: MCP23017 BoardProfile allocation")
    test_transport_does_not_own_bus_init()
    print("PASS: MCP transport consumes shared System I2C")
    test_motor_safety_independence()
    print("PASS: MCP HAL independent from motor safety")
    test_real_cpp_driver_with_mock_transport()
    print("PASS: real MCP23017 C++ driver behavior with mock transport")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
