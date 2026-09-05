import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robostudio"))

import pytest

PySide6 = pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from services.robot_discovery_service import RobotInfo, validate_robot_info
from ui.robot_tab import RobotTab


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def make_robot(ready=True, ota=True):
    return RobotInfo(
        device_id="robot-A1B2C3",
        name="AnTechKids Robot A1B2C3",
        hostname="robot-A1B2C3.local",
        ip="192.168.1.10",
        target="esp32",
        firmware="dev",
        robot_ready=ready,
        network_ready=True,
        ready=ready,
        ota=ota,
        capabilities={"motor": True, "line_sensor": True},
    )


def test_identity_validation():
    payload = {
        "protocol": "antechkids.robot.v1",
        "schema_version": 1,
        "device_id": "robot-A1B2C3",
        "name": "AnTechKids Robot A1B2C3",
        "hostname": "robot-A1B2C3.local",
        "ip": "192.168.1.10",
        "target": "esp32",
        "firmware": "dev",
        "robot_ready": True,
        "network_ready": True,
        "ready": True,
        "ota": True,
        "capabilities": {"motor": True, "line_sensor": True},
    }
    info = validate_robot_info(payload)
    assert info.device_id == "robot-A1B2C3"
    assert info.schema_version == 1
    assert info.ready is True
    assert info.ota is True


def test_identity_validation_rejects_schema_mismatch():
    payload = {"protocol": "antechkids.robot.v1", "schema_version": 2}
    with pytest.raises(ValueError):
        validate_robot_info(payload)


def test_robot_tab_starts_with_no_selected_robot(app):
    tab = RobotTab(lambda: "motor.forward(50)")
    assert tab.robot_combo.count() == 0
    assert tab.deploy_button.isEnabled() is False


def test_robot_tab_enables_run_for_ready_ota_robot(app):
    tab = RobotTab(lambda: "motor.forward(50)")
    tab._robots = [make_robot()]
    tab.robot_combo.addItem("Robot A1B2C3", "robot-A1B2C3")
    tab.robot_combo.setCurrentIndex(0)
    tab._on_robot_selected(0)
    assert tab.deploy_button.isEnabled() is True


def test_robot_tab_blocks_non_ready_robot(app):
    tab = RobotTab(lambda: "motor.forward(50)")
    tab._robots = [make_robot(ready=False)]
    tab.robot_combo.addItem("Robot A1B2C3", "robot-A1B2C3")
    tab.robot_combo.setCurrentIndex(0)
    tab._on_robot_selected(0)
    assert tab.deploy_button.isEnabled() is False


def test_robot_tab_blocks_robot_without_ota(app):
    tab = RobotTab(lambda: "motor.forward(50)")
    tab._robots = [make_robot(ota=False)]
    tab.robot_combo.addItem("Robot A1B2C3", "robot-A1B2C3")
    tab.robot_combo.setCurrentIndex(0)
    tab._on_robot_selected(0)
    assert tab.deploy_button.isEnabled() is False
