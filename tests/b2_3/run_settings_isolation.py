#!/usr/bin/env python3
"""B2.3 regression checks for RoboStudio user-setting persistence."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robostudio.domain.hardware_config import HardwareConfig
from robostudio.domain.hardware_config_service import HardwareConfigService
from robostudio.services.firmware_service import FirmwareService
from tools import runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        sorted(
            (path.relative_to(root).as_posix(), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-b23-settings-") as temp:
        base = Path(temp)
        app = base / "Robo Studio Ứng dụng"
        state = base / "Người dùng Nguyễn An" / "RoboStudio State"
        config = app / "config"
        config.mkdir(parents=True)

        packaged_hardware = HardwareConfig.create_default()
        (config / "hardware.json").write_text(
            json.dumps(packaged_hardware.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (config / "config.json").write_text(
            json.dumps(
                {"compiler_command": "robot", "firmware_project": ""},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        firmware = app / "firmware" / "RobotVM.ino"
        firmware.parent.mkdir(parents=True)
        firmware.write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8")

        before = snapshot(app)
        previous = os.environ.copy()
        try:
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(app)
            os.environ[runtime_paths.STATE_ROOT_ENV] = str(state)
            os.environ[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
            os.environ[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"

            hardware_service = HardwareConfigService()
            loaded = hardware_service.load()
            check("hardware defaults load from packaged read-only config", loaded.to_dict() == packaged_hardware.to_dict())
            check("hardware user path is external", hardware_service.user_config_path == state.resolve() / "hardware.json")
            check("hardware package path stays inside application", hardware_service.package_config_path == app.resolve() / "config" / "hardware.json")

            loaded.set_enabled("imu", True)
            hardware_service.save(loaded)
            check("hardware changes persist to external state", hardware_service.user_config_path.is_file())
            check("saved hardware change is readable", HardwareConfigService(hardware_service.user_config_path).load().is_enabled("imu"))

            firmware_service = FirmwareService()
            check("firmware user config is external", firmware_service.user_config_path == state.resolve() / "config.json")
            firmware_service.set_firmware_path(firmware)
            check("firmware selection persists externally", firmware_service.user_config_path.is_file())
            saved = json.loads(firmware_service.user_config_path.read_text(encoding="utf-8"))
            check("firmware path is stored relocatably", saved["firmware_project"] == "firmware/RobotVM.ino")
            check("firmware selection resolves inside application", firmware_service.get_firmware_path() == firmware.resolve())
        finally:
            os.environ.clear()
            os.environ.update(previous)

        check("RoboStudio settings never mutate release", snapshot(app) == before)
        check("external user state was created", state.is_dir())

    print("B2.3 RoboStudio user settings isolation checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
