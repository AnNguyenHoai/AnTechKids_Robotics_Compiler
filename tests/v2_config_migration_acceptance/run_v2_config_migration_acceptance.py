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

from robostudio.domain.device_registry import DeviceRegistry
from robostudio.domain.hardware_config import HardwareConfig
from robostudio.domain.hardware_config_service import HardwareConfigService
from tools import hardware_feature_config

PROFILE = "antech_robot_v2"


def expect_error(fn, contains: str) -> None:
    try:
        fn()
    except (ValueError, KeyError) as exc:
        assert contains.lower() in str(exc).lower(), (contains, str(exc))
        return
    raise AssertionError(f"expected error containing {contains!r}")


def test_v1_load_and_explicit_v2_save_migration() -> None:
    legacy_devices = {
        "motor": False,
        "encoder": True,
        "line_sensor": False,
        "ultrasonic": True,
        "imu": True,
        "servo": True,
        "buzzer": False,
    }
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "hardware.json"
        legacy = {"version": 1, "devices": legacy_devices}
        path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
        before = path.read_text(encoding="utf-8")

        service = HardwareConfigService(path)
        cfg = service.load()
        assert path.read_text(encoding="utf-8") == before
        assert cfg.version == 2
        assert cfg.board_profile == PROFILE
        for device_id, enabled in legacy_devices.items():
            assert cfg.is_enabled(device_id) is enabled

        service.save(cfg)
        saved = json.loads(path.read_text(encoding="utf-8"))
        assert saved["version"] == 2
        assert saved["board_profile"] == PROFILE
        assert saved["devices"] == legacy_devices


def test_v2_save_reload_is_stable() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "hardware.json"
        cfg = HardwareConfig.create_default()
        cfg.set_enabled("motor", False)
        cfg.set_enabled("encoder", True)
        cfg.set_enabled("servo", True)

        service = HardwareConfigService(path)
        service.save(cfg)
        loaded = service.load()

        assert loaded.to_dict() == cfg.to_dict()
        assert loaded.version == 2
        assert loaded.board_profile == PROFILE


def test_unknown_board_rejected() -> None:
    payload = {"version": 2, "board_profile": "unknown_board", "devices": {}}
    expect_error(lambda: HardwareConfig.from_dict(payload), "unsupported board profile")
    expect_error(lambda: hardware_feature_config.normalize_hardware_payload(payload), "unsupported board profile")


def test_unknown_feature_rejected() -> None:
    payload = {
        "version": 2,
        "board_profile": PROFILE,
        "devices": {"warp_drive": True},
    }
    expect_error(lambda: HardwareConfig.from_dict(payload), "warp_drive")
    expect_error(lambda: hardware_feature_config.normalize_hardware_payload(payload), "unknown device")


def test_missing_device_field_uses_registry_default() -> None:
    payload = {
        "version": 2,
        "board_profile": PROFILE,
        "devices": {"motor": False},
    }
    cfg = HardwareConfig.from_dict(payload)
    normalized = hardware_feature_config.normalize_hardware_payload(payload)

    assert cfg.is_enabled("motor") is False
    assert normalized["motor"] is False

    defaults = DeviceRegistry.defaults()
    for device_id, default_enabled in defaults.items():
        if device_id == "motor":
            continue
        assert cfg.is_enabled(device_id) is default_enabled, device_id
        assert normalized[device_id] is default_enabled, device_id


def test_missing_devices_object_is_deterministic_defaults() -> None:
    payload = {"version": 2, "board_profile": PROFILE}
    cfg = HardwareConfig.from_dict(payload)
    normalized = hardware_feature_config.normalize_hardware_payload(payload)

    assert cfg.to_dict()["devices"] == DeviceRegistry.defaults()
    assert normalized == DeviceRegistry.defaults()


def test_invalid_version_rejected() -> None:
    for version in (0, 3, 99, "not-an-int"):
        payload = {"version": version, "board_profile": PROFILE, "devices": {}}
        expect_error(lambda payload=payload: HardwareConfig.from_dict(payload), "version")
        expect_error(
            lambda payload=payload: hardware_feature_config.normalize_hardware_payload(payload),
            "version",
        )


def test_domain_and_deployment_tools_normalize_identically() -> None:
    cases = (
        {"version": 1, "devices": {"servo": True, "motor": False}},
        {
            "version": 2,
            "board_profile": PROFILE,
            "devices": {"encoder": True, "line_sensor": False, "buzzer": False},
        },
        {"version": 2, "board_profile": PROFILE},
    )
    for payload in cases:
        domain = HardwareConfig.from_dict(payload).to_dict()["devices"]
        deployment = hardware_feature_config.normalize_hardware_payload(payload)
        assert domain == deployment, payload


def main() -> int:
    test_v1_load_and_explicit_v2_save_migration()
    print("PASS: V1 config loads in memory as V2 and migrates only on explicit save")
    test_v2_save_reload_is_stable()
    print("PASS: V2 config save/reload is stable")
    test_unknown_board_rejected()
    print("PASS: unknown board profile is rejected")
    test_unknown_feature_rejected()
    print("PASS: unknown feature is rejected")
    test_missing_device_field_uses_registry_default()
    test_missing_devices_object_is_deterministic_defaults()
    print("PASS: missing device fields resolve to deterministic registry defaults")
    test_invalid_version_rejected()
    print("PASS: invalid schema versions are rejected")
    test_domain_and_deployment_tools_normalize_identically()
    print("PASS: RoboStudio and deployment tools share one migration policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
