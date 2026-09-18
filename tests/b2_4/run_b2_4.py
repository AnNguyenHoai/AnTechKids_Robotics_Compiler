#!/usr/bin/env python3
"""B2.4 hardware + flash portability regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import deploy_robot, hardware_preflight, target_machine_prerequisites, target_machine_qualification
from tools.deployment_runtime import ProcessResult


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_preflight_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except hardware_preflight.HardwarePreflightError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def fixture_ports():
    return hardware_preflight.parse_device_list(
        json.dumps(
            [
                {
                    "port": "COM11",
                    "description": "CP210x USB to UART Bridge",
                    "hwid": "USB VID:PID=10C4:EA60",
                    "vid": 4292,
                    "pid": 60000,
                    "serial_number": "robot-11",
                    "manufacturer": "Silicon Labs",
                },
                {"port": "COM7", "description": "USB Serial Device"},
            ]
        )
    )


def test_parser_and_selection() -> None:
    ports = fixture_ports()
    check("PlatformIO JSON ports are parsed", [item.port for item in ports] == ["COM11", "COM7"])
    check("serial metadata is retained", ports[0].description == "CP210x USB to UART Bridge")
    check("explicit selected port resolves case-insensitively", hardware_preflight.select_serial_port("com7", ports).port == "COM7")
    expect_preflight_error(
        "empty port never guesses first device",
        lambda: hardware_preflight.select_serial_port("", ports),
        "explicit COM/serial port",
    )
    expect_preflight_error(
        "missing requested port reports detected choices",
        lambda: hardware_preflight.select_serial_port("COM4", ports),
        "Detected ports",
    )
    expect_preflight_error(
        "no visible ports reports USB driver guidance",
        lambda: hardware_preflight.select_serial_port("COM7", ()),
        "USB/UART bridge driver",
    )
    expect_preflight_error(
        "invalid PlatformIO device JSON fails closed",
        lambda: hardware_preflight.parse_device_list("not-json"),
        "invalid serial-device JSON",
    )


def test_discovery_uses_canonical_platformio_boundary(base: Path) -> None:
    captured: dict[str, object] = {}
    original_prepare = hardware_preflight.build_isolation.prepare_build_workspace
    original_env = hardware_preflight.deployment_runtime_environment
    original_command = hardware_preflight.platformio_command
    original_run = hardware_preflight.run_process
    try:
        workspace = base / "external state" / "build" / "hardware-preflight" / "platformio"

        def fake_prepare(project, base_env=None):
            captured["project"] = project
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace

        def fake_env(base_env=None, *, project_name=None):
            captured["base_env"] = dict(base_env or {})
            captured["project_name"] = project_name
            return {"ROBOSTUDIO_DEPENDENCY_MODE": "artifact-closed", "PATH": "ARTIFACT_ONLY"}

        def fake_command(*args):
            captured["command_args"] = args
            return [r"C:\Portable RoboStudio\runtime\bin\python.exe", "-m", "platformio", *args]

        def fake_run(command, *, cwd, env=None, timeout=300.0, on_output=None):
            captured["spawn_command"] = list(command)
            captured["cwd"] = Path(cwd)
            captured["env"] = dict(env or {})
            captured["timeout"] = timeout
            return ProcessResult(0, '[{"port":"COM7","description":"Robot USB"}]')

        hardware_preflight.build_isolation.prepare_build_workspace = fake_prepare
        hardware_preflight.deployment_runtime_environment = fake_env
        hardware_preflight.platformio_command = fake_command
        hardware_preflight.run_process = fake_run
        ports, command = hardware_preflight.discover_serial_ports(
            base_env={"PATH": "HOSTILE_HOST_PATH", "PYTHONPATH": "HOSTILE"}, timeout=12.0
        )
    finally:
        hardware_preflight.build_isolation.prepare_build_workspace = original_prepare
        hardware_preflight.deployment_runtime_environment = original_env
        hardware_preflight.platformio_command = original_command
        hardware_preflight.run_process = original_run

    check("hardware discovery uses isolated external workspace", captured["cwd"] == workspace)
    check("hardware discovery requests PlatformIO device JSON", captured["command_args"] == ("device", "list", "--json-output"))
    check("hardware discovery uses resolved absolute packaged command", str(command[0]).lower().endswith("python.exe"))
    check("hardware discovery runs with artifact-closed environment", captured["env"]["ROBOSTUDIO_DEPENDENCY_MODE"] == "artifact-closed")
    check("host PATH is not forwarded to final discovery process", captured["env"]["PATH"] == "ARTIFACT_ONLY")
    check("hardware discovery returns visible port", ports[0].port == "COM7")


def _valid_bootstrap_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "type": "antechkids.robot.bootstrap",
                "schema_version": 1,
                "wifi": {"ssid": "Classroom", "password": "wifi-secret"},
                "ota": {"password": "ota-secret"},
            }
        ),
        encoding="utf-8",
    )


def test_bootstrap_fails_before_upload_when_port_not_visible(base: Path) -> None:
    config = base / "bootstrap.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    _valid_bootstrap_config(config)
    called = {"run": False, "workspace": False}

    original_env = deploy_robot.deployment_environment
    original_require = deploy_robot.hardware_preflight.require_serial_port
    original_workspace = deploy_robot.firmware_workspace.prepare_firmware_workspace
    original_run = deploy_robot.run
    try:
        deploy_robot.deployment_environment = lambda project: {"ROBOSTUDIO_DEPENDENCY_MODE": "artifact-closed"}

        def missing_port(*args, **kwargs):
            raise hardware_preflight.HardwarePreflightError("COM9 is not visible")

        def should_not_workspace(*args, **kwargs):
            called["workspace"] = True
            raise AssertionError("firmware workspace must not be prepared before hardware preflight passes")

        def should_not_run(*args, **kwargs):
            called["run"] = True
            raise AssertionError("uploader must not run when preflight fails")

        deploy_robot.hardware_preflight.require_serial_port = missing_port
        deploy_robot.firmware_workspace.prepare_firmware_workspace = should_not_workspace
        deploy_robot.run = should_not_run
        try:
            deploy_robot.flash_bootstrap(config, "COM9")
        except RuntimeError as exc:
            check("missing serial port has actionable failure", "COM9 is not visible" in str(exc))
        else:
            raise AssertionError("bootstrap unexpectedly flashed with invisible port")
    finally:
        deploy_robot.deployment_environment = original_env
        deploy_robot.hardware_preflight.require_serial_port = original_require
        deploy_robot.firmware_workspace.prepare_firmware_workspace = original_workspace
        deploy_robot.run = original_run

    check("preflight failure prevents firmware staging", called["workspace"] is False)
    check("preflight failure prevents uploader process", called["run"] is False)


def test_bootstrap_always_uploads_to_preflight_port(base: Path) -> None:
    config = base / "bootstrap.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    _valid_bootstrap_config(config)
    workspace = base / "firmware workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    captured: dict[str, object] = {}

    original_env = deploy_robot.deployment_environment
    original_require = deploy_robot.hardware_preflight.require_serial_port
    original_workspace = deploy_robot.firmware_workspace.prepare_firmware_workspace
    original_template = deploy_robot.firmware_template
    original_apply = deploy_robot.apply_user_hardware_config
    original_command = deploy_robot.platformio_command
    original_run = deploy_robot.run
    try:
        deploy_robot.deployment_environment = lambda project: {"ROBOSTUDIO_DEPENDENCY_MODE": "artifact-closed"}
        deploy_robot.hardware_preflight.require_serial_port = lambda port, base_env=None: SimpleNamespace(
            selected_port=hardware_preflight.SerialPortInfo("COM11", "Robot USB")
        )
        deploy_robot.firmware_template = lambda: base / "template"
        deploy_robot.firmware_workspace.prepare_firmware_workspace = lambda source, project: workspace
        deploy_robot.apply_user_hardware_config = lambda root: None
        deploy_robot.platformio_command = lambda *args: ["PACKAGED_PIO", *args]

        def fake_run(command, *, env=None, cwd=ROOT, timeout=300.0):
            captured["command"] = list(command)
            captured["cwd"] = Path(cwd)
            captured["env"] = dict(env or {})

        deploy_robot.run = fake_run
        result = deploy_robot.flash_bootstrap(config, "com11")
    finally:
        deploy_robot.deployment_environment = original_env
        deploy_robot.hardware_preflight.require_serial_port = original_require
        deploy_robot.firmware_workspace.prepare_firmware_workspace = original_workspace
        deploy_robot.firmware_template = original_template
        deploy_robot.apply_user_hardware_config = original_apply
        deploy_robot.platformio_command = original_command
        deploy_robot.run = original_run

    check("bootstrap flash succeeds after preflight", result == 0)
    check("USB upload always contains explicit --upload-port", "--upload-port" in captured["command"])
    index = captured["command"].index("--upload-port")
    check("USB upload uses canonical preflight port", captured["command"][index + 1] == "COM11")
    check("USB uploader runs in staged firmware workspace", captured["cwd"] == workspace)


def test_target_machine_flash_qualification() -> None:
    original_require = target_machine_qualification.hardware_preflight.require_serial_port
    try:
        target_machine_qualification.hardware_preflight.require_serial_port = lambda port, base_env=None: hardware_preflight.HardwarePreflightReport(
            requested_port=str(port),
            selected_port=hardware_preflight.SerialPortInfo("COM7", "Robot USB"),
            detected_ports=(hardware_preflight.SerialPortInfo("COM7", "Robot USB"),),
            discovery_command=(r"C:\RoboStudio\runtime\bin\python.exe", "-m", "platformio", "device", "list", "--json-output"),
        )
        report = target_machine_qualification.qualify_target_machine(
            scope="flash", env={"PATH": ""}, serial_port="COM7"
        )
    finally:
        target_machine_qualification.hardware_preflight.require_serial_port = original_require

    check("flash scope exists", target_machine_prerequisites.RequirementScope.FLASH.value == "flash")
    check("flash scope includes only external USB driver policy", {item.name for item in target_machine_prerequisites.for_scope("flash")} == {"ESP32/USB driver"})
    check("USB driver remains external rather than bundled", all(not item.packaged for item in target_machine_prerequisites.for_scope("flash")))
    check("flash qualification passes when selected port is visible", report.passed is True)
    check("flash qualification records visible serial evidence", report.flash_preflight["driver_visibility_proven"] is True)

    original_require = target_machine_qualification.hardware_preflight.require_serial_port
    try:
        def fail(*args, **kwargs):
            raise hardware_preflight.HardwarePreflightError("No serial/COM ports were detected")
        target_machine_qualification.hardware_preflight.require_serial_port = fail
        failed = target_machine_qualification.qualify_target_machine(
            scope="flash", env={"PATH": ""}, serial_port="COM7"
        )
    finally:
        target_machine_qualification.hardware_preflight.require_serial_port = original_require
    check("flash qualification fails without visible hardware", failed.passed is False)
    check("flash failure does not claim driver visibility", failed.flash_preflight["driver_visibility_proven"] is False)


def test_firmware_has_no_developer_com_fallback() -> None:
    ini = (ROOT / "robot-platform" / "platformio.ini").read_text(encoding="utf-8")
    deploy = (ROOT / "tools" / "deploy_robot.py").read_text(encoding="utf-8")
    check("firmware config has no COM4 fallback", "upload_port = COM4" not in ini)
    check("USB deploy invokes canonical hardware preflight", "hardware_preflight.require_serial_port" in deploy)
    check("USB deploy requires explicit upload port", '"--upload-port",selected_usb_port' in deploy or '"--upload-port", selected_usb_port' in deploy)
    check("bootstrap upload requires explicit validated port", '"--upload-port",selected_port' in deploy or '"--upload-port", selected_port' in deploy)


def main() -> int:
    test_parser_and_selection()
    with tempfile.TemporaryDirectory(prefix="robostudio-b24-") as temp:
        base = Path(temp)
        test_discovery_uses_canonical_platformio_boundary(base / "discovery")
        test_bootstrap_fails_before_upload_when_port_not_visible(base / "negative")
        test_bootstrap_always_uploads_to_preflight_port(base / "positive")
    test_target_machine_flash_qualification()
    test_firmware_has_no_developer_com_fallback()
    print("B2.4 hardware and flash portability checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
