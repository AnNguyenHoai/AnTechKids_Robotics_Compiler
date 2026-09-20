#!/usr/bin/env python3
"""B2.3 deployment-operation concurrency regression.

RoboStudio exposes first-flash and OTA through separate QThreads. The service
boundary must nevertheless guarantee that only one deployment owns the local
PlatformIO/deployment lane at a time.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

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
        name="h23-bootstrap-holder",
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


def test_source_contract() -> None:
    source = (ROOT / "robostudio" / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    check("threading.Lock()" in source, "deployment mutex is process-wide at service boundary")
    check("acquire(blocking=False)" in source, "deployment collision fails fast rather than waiting")
    check(source.count("_DEPLOYMENT_OPERATION_LOCK.release()") >= 2,
          "both first-flash and OTA release the deployment lane in finally blocks")


def main() -> int:
    test_first_flash_blocks_parallel_ota()
    test_lock_releases_when_operation_raises()
    test_source_contract()
    print("B2.3 RoboStudio deployment concurrency: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
