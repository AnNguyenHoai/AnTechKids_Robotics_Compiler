#!/usr/bin/env python3
"""B2.3 RoboStudio user-settings and mutable-state isolation regression."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

from domain.hardware_config_service import HardwareConfigService
from services.bootstrap_config_service import BootstrapConfigService
from services.build_service import BuildService
from services.firmware_service import FirmwareService
from services.hardware_macro_service import HardwareMacroService
from tools import build_isolation, deployment_runtime, runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, contains: str) -> None:
    try:
        fn()
    except Exception as exc:
        check(name, contains.lower() in str(exc).lower())
        return
    raise AssertionError(name)


def snapshot(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(root))] = path.read_bytes().hex()
    return result


def write_runtime_fixture(app: Path, bundled_python: Path) -> None:
    runtime = app / "runtime" / "platformio"
    (runtime / "platforms" / "espressif32").mkdir(parents=True, exist_ok=True)
    packages = runtime / "packages"
    framework = packages / deployment_runtime.ESP32_FRAMEWORK_PACKAGE
    (framework / "cores" / "esp32").mkdir(parents=True, exist_ok=True)
    (framework / "variants" / "esp32").mkdir(parents=True, exist_ok=True)
    (framework / ".piopm").write_text("{}", encoding="utf-8")
    (framework / "cores" / "esp32" / "Arduino.h").write_text("// arduino\n", encoding="utf-8")
    (framework / "variants" / "esp32" / "pins_arduino.h").write_text("// pins\n", encoding="utf-8")
    for package in deployment_runtime.ESP32_USB_TOOL_PACKAGES:
        directory = packages / package
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".piopm").write_text("{}", encoding="utf-8")

    (app / "runtime" / "python").mkdir(parents=True, exist_ok=True)
    packaged_python = app / "runtime" / "python" / bundled_python.name
    shutil.copy2(bundled_python, packaged_python)
    bridge = app / "compiler" / "robostudio_bridge.py"
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.write_text("print('bridge')\n", encoding="utf-8")


def main() -> int:
    previous = os.environ.copy()
    compile_workspace: Path | None = None
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        app = base / "Program Files" / "RoboStudio"
        state = base / "Users" / "Học sinh" / "AppData" / "RoboStudio"
        app.mkdir(parents=True)

        # Minimal read-only application payload used by services under test.
        (app / "config").mkdir(parents=True)
        (app / "config" / "hardware.json").write_text(
            json.dumps(
                {
                    "board_profile": "esp32dev",
                    "devices": {
                        "motor": {"enabled": True},
                        "line_sensor": {"enabled": True},
                        "ultrasonic": {"enabled": False},
                    },
                }
            ),
            encoding="utf-8",
        )
        (app / "config" / "config.json").write_text(
            json.dumps({"compiler_command": "host-python-should-not-be-used"}),
            encoding="utf-8",
        )
        firmware_root = app / "robot-platform"
        firmware_root.mkdir(parents=True)
        packaged_firmware = firmware_root / "platformio.ini"
        packaged_firmware.write_text("[env:esp32dev]\n", encoding="utf-8")
        sibling = firmware_root / "main.cpp"
        sibling.write_text("// packaged firmware sibling\n", encoding="utf-8")
        include_dir = firmware_root / "main" / "include" / "generated"
        include_dir.mkdir(parents=True)
        packaged_device = include_dir / "DeviceConfig.h"
        packaged_device.write_text("// packaged-default\n", encoding="utf-8")
        bundled_python = Path(sys.executable).resolve()
        write_runtime_fixture(app, bundled_python)

        arduino_template = app / "robot-platform" / "arduino" / "robot_firmware"
        arduino_template.mkdir(parents=True)
        (arduino_template / "robot_firmware.ino").write_text("// template\n", encoding="utf-8")

        before = snapshot(app)

        try:
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(app)
            os.environ[runtime_paths.STATE_ROOT_ENV] = str(state)
            os.environ[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
            os.environ[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"

            # Hardware config: packaged defaults are read-only input; user changes
            # belong under external user state. Exercise the HardwareConfig public
            # API rather than the legacy dictionary representation.
            hardware_service = HardwareConfigService()
            defaults = hardware_service.load()
            check(
                "hardware defaults load from packaged read-only config",
                defaults.is_enabled("motor") is True
                and defaults.is_enabled("line_sensor") is True
                and defaults.is_enabled("ultrasonic") is False,
            )
            check(
                "hardware user path is external",
                app.resolve() not in hardware_service.user_config_path.resolve().parents,
            )
            check(
                "hardware package path stays inside application",
                app.resolve() in hardware_service.package_config_path.resolve().parents,
            )
            defaults.set_enabled("ultrasonic", True)
            hardware_service.save(defaults)
            check(
                "hardware changes persist to external state",
                hardware_service.user_config_path.is_file(),
            )
            check(
                "saved hardware change is readable",
                hardware_service.load().is_enabled("ultrasonic") is True,
            )

            # Generated hardware macro is derived from user state and staged only
            # into an external firmware working copy.
            macro_service = HardwareMacroService(config_service=hardware_service)
            generated_macro = macro_service.generate()
            check(
                "generated hardware macro is external",
                app.resolve() not in generated_macro.resolve().parents,
            )
            check(
                "generated hardware macro reflects user state",
                "ROBOT_ENABLE_ULTRASONIC 1" in generated_macro.read_text(encoding="utf-8"),
            )
            check(
                "packaged device header remains default before staging",
                packaged_device.read_text(encoding="utf-8") == "// packaged-default\n",
            )
            expect_error(
                "generated hardware macro inside release is rejected",
                lambda: macro_service.generate(app / "DeviceConfig.h"),
                "outside the packaged RoboStudio application",
            )

            staged_firmware = build_isolation.prepare_firmware_workspace(
                firmware_root,
                "settings-isolation",
            )
            staged_macro = macro_service.stage_for_firmware(staged_firmware)
            check(
                "hardware macro is overlaid only into external firmware workspace",
                app.resolve() not in staged_macro.resolve().parents,
            )
            check(
                "staged firmware receives user hardware macro",
                "ROBOT_ENABLE_ULTRASONIC 1" in staged_macro.read_text(encoding="utf-8"),
            )
            check(
                "packaged device header remains unchanged after staging",
                packaged_device.read_text(encoding="utf-8") == "// packaged-default\n",
            )

            # Firmware config: the immutable packaged firmware is copied to an
            # external editable location before any edit is possible.
            firmware_service = FirmwareService()
            check(
                "firmware user config is external",
                app.resolve() not in firmware_service.config_path.resolve().parents,
            )
            firmware_service.save_config(
                {
                    "source": "robot-platform/platformio.ini",
                    "source_kind": "packaged",
                }
            )
            check("firmware selection persists externally", firmware_service.config_path.is_file())
            saved_firmware_config = json.loads(firmware_service.config_path.read_text(encoding="utf-8"))
            check(
                "firmware path is stored relocatably",
                saved_firmware_config["source"] == "robot-platform/platformio.ini",
            )
            check(
                "firmware selection resolves inside application",
                firmware_service.get_firmware_path().resolve() == packaged_firmware.resolve(),
            )
            editable = firmware_service.prepare_editable_firmware()
            check(
                "packaged firmware is copied outside release before editing",
                app.resolve() not in editable.resolve().parents,
            )
            check(
                "editable firmware preserves packaged content",
                editable.read_text(encoding="utf-8") == "[env:esp32dev]\n",
            )
            check(
                "firmware sibling files are copied to editable state",
                editable.with_name("main.cpp").read_text(encoding="utf-8")
                == "// packaged firmware sibling\n",
            )
            editable.write_text("[env:user-edited]\n", encoding="utf-8")
            check(
                "editing external firmware never changes packaged firmware",
                packaged_firmware.read_text(encoding="utf-8") == "[env:esp32dev]\n",
            )
            check(
                "firmware service persists external editable path",
                Path(json.loads(firmware_service.config_path.read_text(encoding="utf-8"))["source"]).resolve()
                == editable.resolve(),
            )
            check(
                "future firmware resolution uses external editable copy",
                firmware_service.get_firmware_path().resolve() == editable.resolve(),
            )

            # Bootstrap config/header: generated secrets/state must be external.
            bootstrap_service = BootstrapConfigService()
            bootstrap_json = bootstrap_service.generate("Lớp Robotics", "wifi", "ota-secret")
            check("bootstrap JSON is external", app.resolve() not in bootstrap_json.resolve().parents)
            check(
                "bootstrap JSON is valid",
                json.loads(bootstrap_json.read_text(encoding="utf-8"))["schema_version"] == 1,
            )
            working_sketch = bootstrap_service.prepare_arduino_working_copy(bootstrap_json)
            check("Arduino working sketch is external", app.resolve() not in working_sketch.resolve().parents)
            check(
                "Arduino template is copied to external state",
                (working_sketch / "robot_firmware.ino").is_file(),
            )
            generated_header = working_sketch / "generated_bootstrap_config.h"
            check("generated Arduino header is external", app.resolve() not in generated_header.resolve().parents)
            check(
                "generated Arduino header contains bootstrap SSID",
                "Lớp Robotics" in generated_header.read_text(encoding="utf-8"),
            )
            check(
                "packaged Arduino template receives no generated bootstrap header",
                not (arduino_template / "generated_bootstrap_config.h").exists(),
            )
            expect_error(
                "bootstrap output inside release is rejected",
                lambda: bootstrap_service.generate(
                    "Lớp Robotics",
                    "wifi",
                    "ota-secret",
                    app / "generated-bootstrap.json",
                ),
                "outside the packaged RoboStudio application",
            )

            # GUI compile path: hostile host Python/PATH hints must be sealed,
            # while all request/source/output scratch data stays under state.
            os.environ["PATH"] = str(base / "Host Tools")
            os.environ["PYTHONPATH"] = str(base / "Host Project")
            build_service = BuildService()
            command, compile_env, temp_file = build_service.get_command("print('hello')\n")
            compile_source = Path(temp_file).resolve()
            compile_workspace = compile_source.parent
            check(
                "GUI compiler resolves bundled Python",
                Path(command[0]).resolve() == bundled_python.resolve(),
            )
            check(
                "GUI compile workspace is under external state",
                compile_workspace
                == state.resolve() / "build" / "compile" / compile_workspace.name,
            )
            check(
                "GUI compile workspace is outside release",
                app.resolve() not in compile_workspace.parents,
            )
            check("GUI compiler strips host PYTHONPATH", "PYTHONPATH" not in compile_env)
            check(
                "GUI compiler keeps artifact-closed mode",
                compile_env.get(runtime_paths.DEPENDENCY_MODE_ENV) == "artifact-closed",
            )
            check(
                "GUI compiler state root remains external",
                Path(compile_env[runtime_paths.STATE_ROOT_ENV]).resolve() == state.resolve(),
            )
            worker_source = (
                ROOT / "robostudio" / "services" / "build_worker.py"
            ).read_text(encoding="utf-8")
            check(
                "GUI worker CWD is derived from external compile workspace",
                '"cwd": str(self._workspace())' in worker_source
                and "ROBOSTUDIO_HOME" not in worker_source,
            )
        finally:
            if compile_workspace is not None:
                shutil.rmtree(compile_workspace, ignore_errors=True)
            os.environ.clear()
            os.environ.update(previous)

        check("RoboStudio mutable state never changes release", snapshot(app) == before)
        check("external user state was created", state.is_dir())

    print("B2.3 RoboStudio user settings isolation checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
