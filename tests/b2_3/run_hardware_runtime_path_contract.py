#!/usr/bin/env python3
"""Regression for one hardware-config path contract across source and EXE modes."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robostudio.domain.hardware_config_service import HardwareConfigService
from robostudio.services.hardware_macro_service import HardwareMacroService
from tools import hardware_feature_config, runtime_paths
from tools.deploy_robot import apply_user_hardware_config


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def configure_user_state(*, ultrasonic: bool, servo: bool, buzzer: bool) -> HardwareConfigService:
    service = HardwareConfigService()
    config = service.load()
    config.set_enabled("motor", True)
    config.set_enabled("line_sensor", True)
    config.set_enabled("ultrasonic", ultrasonic)
    config.set_enabled("servo", servo)
    config.set_enabled("buzzer", buzzer)
    service.save(config)
    return service


def default_template_contract() -> None:
    default_json = json.loads(
        (ROOT / "robostudio" / "config" / "hardware.json").read_text(encoding="utf-8")
    )
    normalized = hardware_feature_config.normalize_hardware_payload(default_json)
    check(
        "shipped hardware.json defaults match shared runtime defaults",
        normalized == hardware_feature_config.defaults(),
    )

    expected_header = hardware_feature_config.render_generated_header(
        hardware_feature_config.defaults()
    )
    template_header = (
        ROOT
        / "robot-platform"
        / "main"
        / "include"
        / "generated"
        / "generated_device_config.h"
    ).read_text(encoding="utf-8")
    check(
        "firmware default header matches shared runtime defaults",
        template_header == expected_header,
    )


def source_mode_contract(base: Path) -> None:
    state = base / "Users" / "EASTVN - An Nguyen" / "AppData" / "Local" / "RoboStudio Dev"
    template = ROOT / "robot-platform" / "main" / "include" / "generated" / "generated_device_config.h"
    template_before = template.read_bytes()

    os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(ROOT)
    os.environ[runtime_paths.STATE_ROOT_ENV] = str(state)
    os.environ.pop(runtime_paths.RUNTIME_MODE_ENV, None)
    os.environ.pop(runtime_paths.DEPENDENCY_MODE_ENV, None)
    os.environ.pop(runtime_paths.PORTABLE_DATA_ENV, None)

    config_service = configure_user_state(ultrasonic=False, servo=True, buzzer=False)
    check(
        "source mode hardware.json uses canonical user state",
        config_service.user_config_path.resolve() == state.resolve() / "hardware.json",
    )

    macro = HardwareMacroService(config_service=config_service)
    output = macro.generate()
    expected = state.resolve() / "generated" / "generated_device_config.h"
    check("source mode generated header uses user state", output == expected)
    text = output.read_text(encoding="utf-8")
    check(
        "source mode generated state reflects current hardware.json",
        "ROBOT_FEATURE_SERVO              1" in text
        and "ROBOT_FEATURE_ULTRASONIC         0" in text,
    )
    check(
        "source mode never mutates repository firmware template",
        template.read_bytes() == template_before,
    )

    # Reproduce the original bug: leave a stale generated header from an older
    # EXE/source session, then change hardware.json. Deployment must regenerate
    # from hardware.json before staging instead of copying the stale header.
    output.write_text(
        "// STALE HEADER MUST NOT WIN\n#define ROBOT_FEATURE_SERVO 1\n",
        encoding="utf-8",
    )
    config = config_service.load()
    config.set_enabled("servo", False)
    config.set_enabled("ultrasonic", True)
    config.set_enabled("buzzer", True)
    config_service.save(config)

    workspace = base / "source workspace with spaces"
    installed = apply_user_hardware_config(workspace)
    current = expected.read_text(encoding="utf-8")
    staged = installed.read_text(encoding="utf-8")
    check(
        "deployment regenerates stale user header from hardware.json",
        "STALE HEADER" not in current
        and "ROBOT_FEATURE_SERVO              0" in current
        and "ROBOT_FEATURE_ULTRASONIC         1" in current,
    )
    check("source deployment stages freshly regenerated hardware header", staged == current)
    check(
        "source template remains unchanged after deployment staging",
        template.read_bytes() == template_before,
    )


def packaged_mode_contract(base: Path) -> None:
    app = base / "RoboStudio Production Folder"
    state = base / "Users" / "EASTVN - An Nguyen" / "AppData" / "Local" / "RoboStudio"
    package_config = app / "config"
    package_config.mkdir(parents=True)
    (package_config / "hardware.json").write_text(
        """{
  "version": 1,
  "devices": {
    "motor": true,
    "encoder": false,
    "line_sensor": true,
    "ultrasonic": true,
    "imu": false,
    "servo": false,
    "buzzer": true
  }
}
""",
        encoding="utf-8",
    )
    immutable_header = (
        app
        / "firmware"
        / "robot-platform"
        / "main"
        / "include"
        / "generated"
        / "generated_device_config.h"
    )
    immutable_header.parent.mkdir(parents=True)
    immutable_header.write_text("// immutable packaged default\n", encoding="utf-8")
    app_snapshot = immutable_header.read_bytes()

    os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(app)
    os.environ[runtime_paths.STATE_ROOT_ENV] = str(state)
    os.environ[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
    os.environ[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"
    os.environ.pop(runtime_paths.PORTABLE_DATA_ENV, None)

    config_service = configure_user_state(ultrasonic=True, servo=True, buzzer=True)
    macro = HardwareMacroService(config_service=config_service)
    output = macro.generate()
    expected = state.resolve() / "generated" / "generated_device_config.h"
    check("packaged mode uses same canonical generated-state layout", output == expected)
    check(
        "packaged generated header is outside immutable application",
        app.resolve() not in output.resolve().parents,
    )

    output.write_text("// STALE PACKAGED HEADER\n", encoding="utf-8")
    workspace = base / "packaged deployment workspace"
    installed = apply_user_hardware_config(workspace)
    staged = installed.read_text(encoding="utf-8")
    check(
        "packaged deployment regenerates stale hardware header",
        "STALE PACKAGED HEADER" not in staged
        and "ROBOT_FEATURE_SERVO              1" in staged
        and "ROBOT_FEATURE_BUZZER             1" in staged,
    )
    check(
        "packaged deployment never mutates release template",
        immutable_header.read_bytes() == app_snapshot,
    )


def renderer_contract() -> None:
    state = hardware_feature_config.defaults()
    text = hardware_feature_config.render_generated_header(state)
    check(
        "shared renderer emits every registered hardware feature",
        all(
            hardware_feature_config.macro_name(device_id) in text
            for device_id in hardware_feature_config.feature_ids()
        ),
    )
    check(
        "shared renderer keeps canonical standard-robot defaults",
        "ROBOT_FEATURE_MOTOR              1" in text
        and "ROBOT_FEATURE_LINE_SENSOR        1" in text
        and "ROBOT_FEATURE_ULTRASONIC         1" in text
        and "ROBOT_FEATURE_BUZZER             1" in text
        and "ROBOT_FEATURE_ENCODER            0" in text
        and "ROBOT_FEATURE_IMU                0" in text
        and "ROBOT_FEATURE_SERVO              0" in text,
    )


def main() -> int:
    previous = os.environ.copy()
    try:
        renderer_contract()
        default_template_contract()
        with tempfile.TemporaryDirectory(prefix="robostudio-hw-path-") as tmp:
            base = Path(tmp)
            source_mode_contract(base / "source mode")
            packaged_mode_contract(base / "packaged mode")
    finally:
        os.environ.clear()
        os.environ.update(previous)

    print("Hardware runtime path contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
