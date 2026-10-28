#!/usr/bin/env python3
"""V1-S6 shared GPIO19 servo/buzzer regression checks."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "robostudio"))
from tools.hardware_feature_config import normalize_hardware_payload, render_generated_header
from domain.hardware_config import HardwareConfig

def rejects(fn):
    try:
        fn()
    except ValueError as exc:
        assert "GPIO19" in str(exc), str(exc)
    else:
        raise AssertionError("Expected GPIO19 exclusivity failure")

default = HardwareConfig.create_default()
assert default.is_enabled("buzzer") and not default.is_enabled("servo")
rejects(lambda: default.set_enabled("servo", True))
assert default.is_enabled("buzzer") and not default.is_enabled("servo")
default.set_enabled("buzzer", False)
default.set_enabled("servo", True)
assert "ROBOT_FEATURE_SERVO" in render_generated_header({k: default.is_enabled(k) for k in default.devices})
rejects(lambda: HardwareConfig.from_dict({"devices": {"servo": True, "buzzer": True}}))
rejects(lambda: normalize_hardware_payload({"devices": {"servo": True, "buzzer": True}}))
rejects(lambda: render_generated_header({"servo": True, "buzzer": True}))
api = (ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp").read_text()
assert '#error "GPIO19 is shared' in api
assert "ledcAttach(OUTPUT_BUZZER_PIN, 50, 16)" in api
assert "ledcWrite(OUTPUT_BUZZER_PIN, duty)" in api
assert "port != 1 || angle < 0 || angle > 180" in api
compiler = (ROOT / "robot-compiler/compiler/handlers/servo_handler.py").read_text()
assert "compiler.program.emit(Opcode.SetServo.value, port, angle, 0)" in compiler

# UI state must be committed atomically so default buzzer -> servo switching works.
ui = (ROOT / "robostudio/ui/hardware_tab.py").read_text(encoding="utf-8")
assert "candidate = HardwareConfig.from_dict" in ui
assert "self._config_service.save(candidate)" in ui
assert 'self._config.set_enabled(device_id, checkbox.isChecked())' not in ui
candidate = HardwareConfig.from_dict({"devices": {"buzzer": False, "servo": True}})
assert candidate.is_enabled("servo") and not candidate.is_enabled("buzzer")
# The reverse transition and invalid both-on selection remain guarded.
reverse = HardwareConfig.from_dict({"devices": {"buzzer": True, "servo": False}})
assert reverse.is_enabled("buzzer") and not reverse.is_enabled("servo")
script = (ROOT / "examples/physical/v1_s6_01_servo_sh90_acceptance.py").read_text(encoding="utf-8")
import ast
ast.parse(script)
assert script.count("rcu.SetServo(") == 4
print("PASS V1-S6 GPIO19 exclusivity, config rollback, servo codepath source contracts")
print("PHYSICAL PENDING: verify GPIO19 wiring, SH90 power, PWM output and motor/buzzer regression")
