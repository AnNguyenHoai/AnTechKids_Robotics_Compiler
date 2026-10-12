#!/usr/bin/env python3
"""V1-S5 source/API acceptance gates. Hardware outcomes remain manual PENDING."""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "physical"
API = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.cpp"
MAIN = ROOT / "robot-platform" / "main" / "main.ino"
MAPPING = ROOT / "robot-frontend-robosim" / "frontend" / "mapping.py"

def check_samples() -> None:
    expected = {
        "v1_s5_01_motor_commands.py": (0, 3),
        "v1_s5_02_student_line3.py": (3, 1),
        "v1_s5_03_student_line5.py": (5, 1),
    }
    for filename, (sensor_count, min_stop) in expected.items():
        content = (SAMPLES / filename).read_text(encoding="utf-8")
        tree = ast.parse(content, filename=filename)
        calls = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        names = [node.func.attr for node in calls]
        assert names.count("GetTraceV2I2CChxState") == sensor_count, filename
        assert names.count("SetMoveStop") >= min_stop, filename
        assert "SetMoveSpeed" in names and "SetWaitForTime" in names, filename
        assert "line_basis" not in names, filename
        if sensor_count:
            channels = sorted(node.args[1].value for node in calls
                              if node.func.attr == "GetTraceV2I2CChxState"
                              and isinstance(node.args[1], ast.Constant))
            assert channels == list(range(sensor_count)), (filename, channels)
            assert any(isinstance(node, ast.While) for node in ast.walk(tree)), filename

def check_contract() -> None:
    api = API.read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    mapping = MAPPING.read_text(encoding="utf-8")
    student = api[api.index("void SetMotorSpeed("):api.index("void Forward(")]
    assert "TTMotorAwareOutput::applyLinePair" in student
    assert "g_studentMotorPolicy" in student
    assert "STUDENT_CONTROL_LEASE_MS" not in api
    assert "g_studentControlDeadlineMs" not in api
    assert "GetTraceV2I2CChxState" in mapping
    assert '"target": "read_line"' in mapping
    assert "g_programExecutionFinished" in main
    assert "RobotAPI::Stop();" in main
    assert "LINE_CONTROL_LEASE_MS = 120" in api

if __name__ == "__main__":
    check_samples()
    check_contract()
    print("PASS V1-S5: student RoboSim samples and V1 lifecycle/TT contracts")
    print("PENDING PHYSICAL: requires supervised ESP32 robot tests and recorded evidence")
