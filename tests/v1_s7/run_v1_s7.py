#!/usr/bin/env python3
"""V1-S7: static source/contract regression; physical verification separately required."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
gpio = (ROOT / "robot-platform/main/src/HardwareAbstraction/GPIO.h").read_text(encoding="utf-8")
api = (ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp").read_text(encoding="utf-8")
touch = (ROOT / "robot-platform/main/src/Devices/Touch.cpp").read_text(encoding="utf-8")
vm = (ROOT / "robot-platform/main/src/Services/VM/VM.cpp").read_text(encoding="utf-8")
compiler = (ROOT / "robot-compiler/compiler/handlers/sensor_handler.py").read_text(encoding="utf-8")
mapping = (ROOT / "robot-frontend-robosim/frontend/mapping.py").read_text(encoding="utf-8")

assert "#define TOUCH_SENSOR_PIN         ROBOT_PIN_36" in gpio
assert "static Touch touch1(TOUCH_SENSOR_PIN);" in api
assert "static Touch touch0(" not in api
assert "static LightSensor lightSensor(" not in api
assert "ROBOT_PIN_5);" not in api
assert "touch1.init();" in api
assert "touch0.init();" not in api
start = api.index("int16_t ReadTouch(int port)")
end = api.index("int16_t ReadLight(", start)
reader = api[start:end]
assert "if (port == 1) state = touch1.read();" in reader
assert "port == 0" not in reader
assert "pinMode(_pin, INPUT);" in touch
assert "digitalRead(_pin) == HIGH" in touch
light = api[api.index("int16_t ReadLight("):api.index("int16_t ReadColor(")]
assert "return 0;" in light and "analogRead" not in light
assert 'case Opcode::ReadTouch:' in vm
assert "Opcode.ReadTouch.value" in compiler
assert '"GetTouch":' in mapping and '"target": "read_touch"' in mapping

program = (ROOT / "examples/physical/v1_s7_01_touch_gpio36_stop.py").read_text(encoding="utf-8")
ast.parse(program)
assert "rcu.GetTouch(1)" in program
assert "rcu.SetMoveStop()" in program
print("PASS V1-S7 source/API GPIO36 single-Touch contracts")
print("PHYSICAL PENDING: verify stable 3.3V input, boot/reset and switch polarity")
