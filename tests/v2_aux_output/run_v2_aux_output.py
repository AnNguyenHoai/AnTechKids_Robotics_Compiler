from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
OUT = ROOT / "robot-platform/main/src/Services/Output"
API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
GPIO = HAL / "GPIO.h"
LED_HANDLER = ROOT / "robot-compiler/compiler/handlers/led_handler.py"
BUZZER_HANDLER = ROOT / "robot-compiler/compiler/handlers/peripheral_handler.py"
VM = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"

HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <map>
#include "MCP23017Driver.h"
#include "AuxOutputService.h"

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
    FakeTransport t;
    MCP23017Driver mcp(t);
    AuxOutputService out(mcp);

    uint8_t pin = 0;
    assert(AuxOutputService::ledPinForPublicPort(1, pin) && pin == 1); // Right GPB1
    assert(AuxOutputService::ledPinForPublicPort(2, pin) && pin == 0); // Left GPB0
    assert(AuxOutputService::ledPinForPublicPort(3, pin) && pin == 1);
    assert(AuxOutputService::ledPinForPublicPort(4, pin) && pin == 0);
    assert(!AuxOutputService::ledPinForPublicPort(0, pin));

    assert(out.setLed(1, true));
    assert((t.regs[0x01] & (1u << 1)) == 0); // IODIRB GPB1 output
    assert((t.regs[0x15] & (1u << 1)) != 0); // OLATB GPB1 high

    assert(out.setLed(2, true));
    assert((t.regs[0x01] & (1u << 0)) == 0);
    assert((t.regs[0x15] & (1u << 0)) != 0);

    assert(out.setLed(1, false));
    assert((t.regs[0x15] & (1u << 1)) == 0);

    assert(out.setBuzzer(true));
    assert((t.regs[0x01] & (1u << 2)) == 0);
    assert((t.regs[0x15] & (1u << 2)) != 0);

    assert(out.setBuzzer(false));
    assert((t.regs[0x15] & (1u << 2)) == 0);
    assert(out.healthy());

    FakeTransport missing;
    missing.present = false;
    MCP23017Driver missingMcp(missing);
    AuxOutputService missingOut(missingMcp);
    assert(!missingOut.setLed(1, true));
    assert(missingOut.lastError() == AuxOutputError::MCP_UNAVAILABLE);

    FakeTransport writeFail;
    MCP23017Driver failMcp(writeFail);
    assert(failMcp.begin());
    writeFail.failWrite = true;
    AuxOutputService failOut(failMcp);
    assert(!failOut.setBuzzer(true));
    assert(failOut.lastError() == AuxOutputError::WRITE_ERROR);

    return 0;
}
"""

def test_real_cpp_aux_output_service() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "aux_output_test.cpp"
        exe = td / "aux_output_test"
        src.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HAL), "-I", str(OUT),
            str(src),
            str(OUT / "AuxOutputService.cpp"),
            str(HAL / "MCP23017Driver.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_robotapi_has_no_direct_aux_gpio_or_mcp_register_logic() -> None:
    api = API.read_text(encoding="utf-8")
    gpio = GPIO.read_text(encoding="utf-8")

    assert "OUTPUT_LED_LEFT_PIN" not in api
    assert "OUTPUT_LED_RIGHT_PIN" not in api
    assert "OUTPUT_BUZZER_PIN" not in api
    assert "OUTPUT_LED_LEFT_PIN" not in gpio
    assert "OUTPUT_LED_RIGHT_PIN" not in gpio
    assert "OUTPUT_BUZZER_PIN" not in gpio

    led_start = api.index("void Set3CLed")
    led_end = api.index("void SetLightSensorLed", led_start)
    led_body = api[led_start:led_end]
    assert "g_auxOutputService.setLed" in led_body
    assert "digitalWrite(" not in led_body
    assert "writePin(" not in led_body

    buz_start = api.index("void SetMp3Play")
    buz_end = api.index("int16_t GetTraceValue", buz_start)
    buz_body = api[buz_start:buz_end]
    assert "#if !ROBOT_FEATURE_BUZZER" in buz_body
    assert "g_auxOutputService.setBuzzer(true)" in buz_body
    assert "g_auxOutputService.setBuzzer(false)" in buz_body
    assert "delay(200)" in buz_body
    assert "digitalWrite(" not in buz_body
    assert "writePin(" not in buz_body


def test_transport_pipeline_remains_native() -> None:
    led = LED_HANDLER.read_text(encoding="utf-8")
    peripheral = BUZZER_HANDLER.read_text(encoding="utf-8")
    vm = VM.read_text(encoding="utf-8")

    assert "Opcode.Set3CLed.value" in led
    assert "Opcode.SetMp3Play.value" in peripheral
    assert "case Opcode::Set3CLed:" in vm
    assert "RobotAPI::Set3CLed" in vm
    assert "case Opcode::SetMp3Play:" in vm
    assert "RobotAPI::SetMp3Play" in vm


def test_motor_safety_independence_and_health_ready_surface() -> None:
    service = (OUT / "AuxOutputService.h").read_text(encoding="utf-8")
    service += (OUT / "AuxOutputService.cpp").read_text(encoding="utf-8")
    for forbidden in ("MotorSafety", "MOTOR_SAFE_EN", "MOTOR_L_IN", "MOTOR_R_IN"):
        assert forbidden not in service, forbidden
    assert "healthy() const" in service
    assert "lastError() const" in service


def main() -> int:
    test_real_cpp_aux_output_service()
    print("PASS: real AuxOutputService C++ over mock MCP23017 transport")
    test_robotapi_has_no_direct_aux_gpio_or_mcp_register_logic()
    print("PASS: RobotAPI LED/buzzer paths use auxiliary-output abstraction")
    test_transport_pipeline_remains_native()
    print("PASS: LED/buzzer compiler and VM transport remains intact")
    test_motor_safety_independence_and_health_ready_surface()
    print("PASS: auxiliary outputs are motor-safety independent and health-ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
