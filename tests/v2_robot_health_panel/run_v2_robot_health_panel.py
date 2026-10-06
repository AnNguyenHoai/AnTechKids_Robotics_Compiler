#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "robostudio"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from robostudio.services.robot_health_presenter import RobotHealthPresenter
from robostudio.services.robot_health_service import (
    RobotHealthPayloadError,
    validate_health_payload,
)

PANEL = ROOT / "robostudio/ui/robot_health_panel.py"
TAB = ROOT / "robostudio/ui/robot_tab.py"
RESP = ROOT / "robostudio/ui/responsive_robot_tab.py"
CLIENT = ROOT / "robostudio/services/robot_health_service.py"

GOOD = {
    "status": "ok",
    "ready": True,
    "robot_ready": True,
    "network_ready": True,
    "ota": True,
    "http_ota": True,
    "hostname": "robot-1",
    "ip": "192.168.1.20",
    "uptime_ms": 12345,
    "firmware_version": "2.0",
    "board_profile": "antech_robot_v2",
    "board_revision": "v2",
    "reset_reason": "BROWNOUT",
    "battery": {"voltage": 7.42, "state": "GOOD"},
    "motor": {
        "armed": False,
        "enabled": False,
        "state": "SAFE",
        "last_stop_reason": "RESET",
    },
    "start": {
        "pressed": False,
        "ready_for_press": True,
        "armed_by_start_this_boot": False,
    },
    "line": {"available": True, "healthy": True, "mask": 4},
    "line_mask": 4,
    "encoder": {
        "available": True,
        "healthy": True,
        "left_count": 123,
        "right_count": -45,
    },
    "i2c": {"healthy": True, "mcp23017": True},
    "i2c_ok": True,
    "rssi": -55,
}


def test_student_view_is_actionable_and_small() -> None:
    snapshot = validate_health_payload(GOOD)
    view = RobotHealthPresenter.student(snapshot)
    assert view.connection == "Robot Connected"
    assert view.battery == "Battery GOOD"
    assert view.motor == "Motor SAFE"
    assert view.line_sensor == "Line Sensor OK"

    critical = json.loads(json.dumps(GOOD))
    critical["battery"]["state"] = "CRITICAL"
    critical["motor"]["state"] = "FAULT"
    view = RobotHealthPresenter.student(validate_health_payload(critical))
    assert view.battery == "Battery CRITICAL"
    assert view.motor == "Motor FAULT"


def test_teacher_view_has_required_diagnostics() -> None:
    text = RobotHealthPresenter.teacher(validate_health_payload(GOOD)).text
    for token in (
        "Battery: 7.42 V",
        "Reset reason: BROWNOUT",
        "Wi-Fi RSSI: -55 dBm",
        "Line raw: 00100",
        "Encoder: OK · L=123 R=-45",
        "Motor: state=SAFE armed=False enabled=False",
        "Firmware: 2.0",
        "Board revision: v2",
        "Uptime: 12345 ms",
        "I2C: OK · MCP23017=OK",
        "Last stop reason: RESET",
    ):
        assert token in text, token


def test_invalid_payload_fails_separately_from_network() -> None:
    bad = json.loads(json.dumps(GOOD))
    del bad["battery"]
    try:
        validate_health_payload(bad)
    except RobotHealthPayloadError as exc:
        assert "battery" in str(exc)
    else:
        raise AssertionError("malformed robot health accepted")

    source = CLIENT.read_text(encoding="utf-8")
    assert "RobotHealthNetworkError" in source
    assert "RobotHealthPayloadError" in source
    assert "/api/v1/health" in source


def test_panel_network_error_is_not_robot_fault() -> None:
    panel = PANEL.read_text(encoding="utf-8")
    assert 'setText("Connection error")' in panel
    block_start = panel.index("def show_network_error")
    block_end = panel.index("def show_payload_error", block_start)
    block = panel[block_start:block_end]
    assert 'setText("Battery —")' in block
    assert 'setText("Motor —")' in block
    assert "FAULT" not in block


def test_student_vs_teacher_information_hierarchy() -> None:
    panel = PANEL.read_text(encoding="utf-8")
    assert 'QPushButton("Teacher Diagnostics")' in panel
    assert "setCheckable(True)" in panel
    assert "setChecked(False)" in panel
    assert "teacher_details.setVisible(False)" in panel

    presenter = (ROOT / "robostudio/services/robot_health_presenter.py").read_text(encoding="utf-8")
    student_block = presenter[presenter.index("def student"):presenter.index("def teacher")]
    for technical in ("reset_reason", "rssi", "left_count", "uptime_ms", "mcp23017"):
        assert technical not in student_block, technical


def test_both_robot_tabs_embed_same_panel_and_async_client() -> None:
    standard = TAB.read_text(encoding="utf-8")
    responsive = RESP.read_text(encoding="utf-8")
    assert "RobotHealthPanel()" in standard
    assert "RobotHealthPanel()" in responsive
    assert "class _HealthWorker(QThread)" in standard
    assert "RobotHealthClient().get_health(self.host)" in standard
    assert "self.refresh_health()" in standard


def main() -> int:
    test_student_view_is_actionable_and_small()
    print("PASS: Student health view stays small and actionable")
    test_teacher_view_has_required_diagnostics()
    print("PASS: Teacher view exposes all required diagnostic fields including encoder counts")
    test_invalid_payload_fails_separately_from_network()
    print("PASS: network vs payload/robot-health failures are distinct")
    test_panel_network_error_is_not_robot_fault()
    print("PASS: network error never renders as battery/motor robot fault")
    test_student_vs_teacher_information_hierarchy()
    print("PASS: teacher diagnostics are collapsed and excluded from Student summary")
    test_both_robot_tabs_embed_same_panel_and_async_client()
    print("PASS: standard/responsive Robot tabs use the same async /api/v1/health panel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
