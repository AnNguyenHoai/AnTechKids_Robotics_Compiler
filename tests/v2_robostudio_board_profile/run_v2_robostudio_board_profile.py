#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "robostudio"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from robostudio.domain.device_registry import DeviceRegistry
from tools.hardware_feature_config import (
    V2_BOARD_DISPLAY_NAME,
    V2_BOARD_PROFILE,
    V2_BOARD_REVISION,
    board_profile_definition,
)

HW_TAB = ROOT / "robostudio/ui/hardware_tab.py"
RESP_TAB = ROOT / "robostudio/ui/responsive_hardware_tab.py"
CONFIG = ROOT / "robostudio/config/hardware.json"
BOARD = ROOT / "robot-platform/main/src/HardwareAbstraction/BoardProfile.h"

INFRASTRUCTURE = {
    "mcp23017",
    "battery_monitor",
    "motor_safety",
    "start",
    "start_arm",
    "robot_health",
}


def test_board_metadata_matches_firmware_contract() -> None:
    definition = board_profile_definition(V2_BOARD_PROFILE)
    assert definition.display_name == "AnTech Robot V2"
    assert definition.revision == "v2"

    board = BOARD.read_text(encoding="utf-8")
    assert f'ID = "{V2_BOARD_PROFILE}"' in board
    assert f'REVISION = "{V2_BOARD_REVISION}"' in board


def test_ui_shows_board_and_revision() -> None:
    for path in (HW_TAB, RESP_TAB):
        text = path.read_text(encoding="utf-8")
        assert 'QGroupBox("Board Profile")' in text
        assert 'board_profile_label' in text
        assert 'board_revision_label' in text

    standard = HW_TAB.read_text(encoding="utf-8")
    assert 'setText(f"Board: {profile.display_name}")' in standard
    assert 'setText(f"Revision: {profile.revision}' in standard


def test_student_devices_are_capabilities_only() -> None:
    ids = set(DeviceRegistry.ids())
    assert not (ids & INFRASTRUCTURE), ids & INFRASTRUCTURE

    display_names = {d.display_name.lower() for d in DeviceRegistry.all()}
    forbidden_names = {
        "mcp23017",
        "battery monitor",
        "motor safety",
        "start",
        "robot health",
    }
    assert not (display_names & forbidden_names)

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["board_profile"] == V2_BOARD_PROFILE
    assert set(config["devices"]) == ids


def test_ui_has_no_pin_remapping_controls_or_wiring_fields() -> None:
    combined = (
        HW_TAB.read_text(encoding="utf-8") + "\n" +
        RESP_TAB.read_text(encoding="utf-8")
    )

    # Capability rows remain checkboxes only; no numeric/text pin editor exists.
    assert "QSpinBox" not in combined
    assert "QLineEdit" not in combined
    assert "GPIO" not in combined
    assert "connector mapping" not in combined.lower()

    payload = CONFIG.read_text(encoding="utf-8").lower()
    for forbidden in ("gpio", "pin", "connector", "mcp23017", "address"):
        assert forbidden not in payload, forbidden


def test_unknown_profile_cannot_be_rendered_as_supported_board() -> None:
    try:
        board_profile_definition("other_board")
    except ValueError as exc:
        assert "Unsupported board profile" in str(exc)
    else:
        raise AssertionError("unknown board profile accepted")


def main() -> int:
    test_board_metadata_matches_firmware_contract()
    print("PASS: RoboStudio board metadata matches firmware BoardProfile ID/revision")
    test_ui_shows_board_and_revision()
    print("PASS: standard and responsive Hardware tabs expose board identity/revision")
    test_student_devices_are_capabilities_only()
    print("PASS: board infrastructure is not student-selectable")
    test_ui_has_no_pin_remapping_controls_or_wiring_fields()
    print("PASS: Hardware UI/config cannot remap physical pins/connectors")
    test_unknown_profile_cannot_be_rendered_as_supported_board()
    print("PASS: unknown board profile fails clearly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
