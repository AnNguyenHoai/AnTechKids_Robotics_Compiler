import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PySide6 = pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from domain.hardware_config_service import HardwareConfigService
from ui.hardware_tab import HardwareTab


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_hardware_tab_loads_and_saves(tmp_path, app):
    service = HardwareConfigService(tmp_path / "hardware.json")
    tab = HardwareTab(service)

    assert tab._checkboxes["imu"].isChecked() is False
    assert tab._checkboxes["line_sensor"].isChecked() is True

    tab._checkboxes["imu"].setChecked(True)
    tab.save()

    assert service.load().is_enabled("imu") is True
