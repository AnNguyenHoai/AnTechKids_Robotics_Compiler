#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "robostudio") not in sys.path:
    sys.path.insert(0, str(ROOT / "robostudio"))

from robostudio.domain.hardware_config import HardwareConfig
from robostudio.domain.hardware_config_service import HardwareConfigService
from robostudio.domain.hardware_macro_generator import HardwareMacroGenerator
from tools import hardware_feature_config

PROFILE = "antech_robot_v2"


def test_v1_to_v2_migration_preserves_features() -> None:
    v1 = {
        "version": 1,
        "devices": {
            "motor": False,
            "encoder": True,
            "line_sensor": False,
            "ultrasonic": True,
            "imu": True,
            "servo": True,
            "buzzer": False,
        },
    }
    cfg = HardwareConfig.from_dict(v1)
    assert cfg.version == 2
    assert cfg.board_profile == PROFILE
    for device, value in v1["devices"].items():
        assert cfg.is_enabled(device) is value

    out = cfg.to_dict()
    assert out["version"] == 2
    assert out["board_profile"] == PROFILE
    assert out["devices"] == v1["devices"]


def test_service_migrates_only_on_save() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "hardware.json"
        original = {
            "version": 1,
            "devices": {"motor": True, "servo": True, "encoder": True},
        }
        path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
        before = path.read_text(encoding="utf-8")

        service = HardwareConfigService(path)
        cfg = service.load()
        assert path.read_text(encoding="utf-8") == before
        assert cfg.version == 2
        assert cfg.board_profile == PROFILE
        assert cfg.is_enabled("servo")
        assert cfg.is_enabled("encoder")

        service.save(cfg)
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert saved["version"] == 2
        assert saved["board_profile"] == PROFILE
        assert saved["devices"]["servo"] is True
        assert saved["devices"]["encoder"] is True


def test_v2_profile_validation() -> None:
    valid = HardwareConfig.from_dict({
        "version": 2,
        "board_profile": PROFILE,
        "devices": {},
    })
    assert valid.board_profile == PROFILE

    for payload in (
        {"version": 2, "devices": {}},
        {"version": 2, "board_profile": "robot_other", "devices": {}},
        {"version": 3, "board_profile": PROFILE, "devices": {}},
    ):
        try:
            HardwareConfig.from_dict(payload)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid payload accepted: {payload}")


def test_shared_tools_match_domain_migration() -> None:
    v1 = {"version": 1, "devices": {"servo": True, "motor": False}}
    v2 = {
        "version": 2,
        "board_profile": PROFILE,
        "devices": {"servo": True, "motor": False},
    }
    assert hardware_feature_config.normalize_hardware_payload(v1) == hardware_feature_config.normalize_hardware_payload(v2)

    bad = {"version": 2, "board_profile": "wrong", "devices": {}}
    try:
        hardware_feature_config.normalize_hardware_payload(bad)
    except ValueError as exc:
        assert "Unsupported board profile" in str(exc)
    else:
        raise AssertionError("shared deployment tools accepted unknown board profile")


def test_feature_header_is_capability_only() -> None:
    cfg = HardwareConfig.create_default()
    cfg.set_enabled("servo", True)
    text = HardwareMacroGenerator().render(cfg)

    assert "#define ROBOT_FEATURE_SERVO" in text
    assert "antech_robot_v2" not in text
    assert "GPIO" not in text
    assert "MOTOR_SAFE_EN" not in text
    assert "SERVO1" not in text


def test_shipped_default_is_v2() -> None:
    payload = json.loads((ROOT / "robostudio/config/hardware.json").read_text(encoding="utf-8"))
    assert payload["version"] == 2
    assert payload["board_profile"] == PROFILE
    assert hardware_feature_config.normalize_hardware_payload(payload) == hardware_feature_config.defaults()


def main() -> int:
    test_v1_to_v2_migration_preserves_features()
    print("PASS: V1 -> V2 migration preserves feature selections")
    test_service_migrates_only_on_save()
    print("PASS: legacy file is not silently rewritten until explicit save")
    test_v2_profile_validation()
    print("PASS: V2 board profile validation is deterministic")
    test_shared_tools_match_domain_migration()
    print("PASS: RoboStudio and deployment tools share the same migration policy")
    test_feature_header_is_capability_only()
    print("PASS: generated header remains capability-only with no physical pin ownership")
    test_shipped_default_is_v2()
    print("PASS: shipped default config uses V2 schema/profile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
