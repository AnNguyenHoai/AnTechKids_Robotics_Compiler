#!/usr/bin/env python3
"""B2.3 deployment-operation concurrency and COM ownership regression."""
from __future__ import annotations

import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

import services.robot_deployment_service as deployment_service
from services.robot_deployment_service import (
    DeploymentResult,
    RobotDeploymentService,
    deployment_operation_busy,
)
from services.robot_discovery_service import RobotInfo


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def robot() -> RobotInfo:
    return RobotInfo(
        device_id="robot-CONC01",
        name="Concurrency Robot",
        hostname="robot-conc01",
        ip="192.168.1.70",
        target="esp32",
        firmware="0.1.1",
        robot_ready=True,
        network_ready=True,
        ready=True,
        ota=True,
        capabilities={"motor": True},
    )


def test_first_flash_blocks_parallel_ota() -> None:
    service = RobotDeploymentService(root=ROOT)
    entered = threading.Event()
    release = threading.Event()
    completed: list[DeploymentResult] = []

    def fake_flash(config_path, usb_port, on_output):
        entered.set()
        if not release.wait(timeout=5.0):
            raise AssertionError("test deployment lock holder timed out")
        return DeploymentResult(True, "bootstrap done")

    service._flash_first_robot_locked = fake_flash  # type: ignore[method-assign]

    thread = threading.Thread(
        target=lambda: completed.append(service.flash_first_robot(Path("ignored.json"), "COM4")),
        name="b23-bootstrap-holder",
    )
    thread.start()
    check(entered.wait(timeout=2.0), "first-flash acquired deployment lane")
    check(deployment_operation_busy(), "deployment lane reports busy while first-flash is active")

    competing = service.deploy_ota(
        "print('student')",
        robot(),
        "ClassroomWiFi",
        "wifi-secret",
        "ota-secret",
    )
    check(not competing.success, "parallel OTA is rejected instead of running concurrently")
    check(
        competing.error is not None and "already in progress" in competing.error,
        "parallel deployment returns actionable busy diagnostic",
    )

    release.set()
    thread.join(timeout=3.0)
    check(not thread.is_alive(), "first-flash holder completes")
    check(bool(completed) and completed[0].success, "owning deployment result is preserved")
    check(not deployment_operation_busy(), "deployment lane releases after completion")


def test_lock_releases_when_operation_raises() -> None:
    service = RobotDeploymentService(root=ROOT)

    def explode(config_path, usb_port, on_output):
        raise RuntimeError("synthetic deployment crash")

    service._flash_first_robot_locked = explode  # type: ignore[method-assign]
    try:
        service.flash_first_robot(Path("ignored.json"), "COM4")
    except RuntimeError as exc:
        check("synthetic deployment crash" in str(exc), "synthetic operation failure propagates")
    else:
        raise AssertionError("synthetic operation failure unexpectedly succeeded")

    check(not deployment_operation_busy(), "deployment lane releases after exception")


def test_busy_serial_port_fails_before_build_or_discovery() -> None:
    service = RobotDeploymentService(root=ROOT)
    discovery_called = False

    def unexpected_discover():
        nonlocal discovery_called
        discovery_called = True
        raise AssertionError("discovery must not run when selected COM port is already busy")

    service.discovery.discover = unexpected_discover  # type: ignore[method-assign]
    original_probe = deployment_service.windows_serial_port_busy_error
    deployment_service.windows_serial_port_busy_error = lambda port: (
        f"Serial port {port} is busy. Disconnect USB Serial Console first."
    )
    try:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "robot_bootstrap.json"
            config.write_text("{}", encoding="utf-8")
            result = service.flash_first_robot(config, "COM7")
    finally:
        deployment_service.windows_serial_port_busy_error = original_probe

    check(not result.success, "busy selected COM port rejects first-flash")
    check(result.error is not None and "Disconnect USB Serial Console" in result.error,
          "busy COM diagnostic tells user how to release RoboStudio serial ownership")
    check(not discovery_called, "busy COM is detected before discovery/build work starts")
    check(not deployment_operation_busy(), "deployment lane releases after busy COM rejection")


def test_source_contract() -> None:
    source = (ROOT / "robostudio" / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    check("threading.Lock()" in source, "deployment mutex is process-wide at service boundary")
    check("acquire(blocking=False)" in source, "deployment collision fails fast rather than waiting")
    check(source.count("_DEPLOYMENT_OPERATION_LOCK.release()") >= 2,
          "both first-flash and OTA release the deployment lane in finally blocks")
    check("CreateFileW" in source and "no sharing" in source,
          "Windows first-flash probes exclusive COM ownership before spawning deployment")


def main() -> int:
    test_first_flash_blocks_parallel_ota()
    test_lock_releases_when_operation_raises()
    test_busy_serial_port_fails_before_build_or_discovery()
    test_source_contract()
    print("B2.3 RoboStudio deployment concurrency + COM ownership: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
