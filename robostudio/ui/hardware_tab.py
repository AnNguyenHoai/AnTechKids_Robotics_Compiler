"""Hardware / Devices configuration tab (H25-B)."""
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QGroupBox, QMessageBox
)

from domain.device_registry import DeviceRegistry
from domain.hardware_config_service import HardwareConfigService
from services.hardware_macro_service import HardwareMacroService

CATEGORY_TITLES = {"motion": "Motion", "sensors": "Sensors", "expansion": "Expansion"}


class HardwareTab(QWidget):
    """UI adapter for hardware selection and generated firmware macros."""

    configuration_saved = Signal()
    artifacts_generated = Signal(str)

    def __init__(self, config_service=None, macro_service=None, parent=None):
        super().__init__(parent)
        self._config_service = config_service or HardwareConfigService()
        self._macro_service = macro_service or HardwareMacroService(config_service=self._config_service)
        self._config = None
        self._checkboxes: Dict[str, QCheckBox] = {}
        self._build_ui()
        self.reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Hardware Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        description = QLabel("Select the hardware installed on this robot. The selection is saved to hardware.json and will be used by later build steps to generate firmware feature macros.")
        description.setWordWrap(True)
        layout.addWidget(description)
        for category in CATEGORY_TITLES:
            devices = DeviceRegistry.by_category(category)
            if not devices:
                continue
            group = QGroupBox(CATEGORY_TITLES[category])
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(6)
            for device in devices:
                row = QHBoxLayout()
                checkbox = QCheckBox(device.display_name)
                checkbox.setObjectName(f"device_{device.device_id}")
                checkbox.setToolTip(device.description)
                self._checkboxes[device.device_id] = checkbox
                row.addWidget(checkbox)
                hint = QLabel(device.description)
                hint.setWordWrap(True)
                hint.setStyleSheet("color: #666666;")
                row.addWidget(hint, 1)
                group_layout.addLayout(row)
            layout.addWidget(group)
        button_row = QHBoxLayout()
        self.save_button = QPushButton("Apply Configuration")
        self.save_button.clicked.connect(self.save)
        button_row.addWidget(self.save_button)
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload)
        button_row.addWidget(self.reload_button)
        button_row.addStretch()
        layout.addLayout(button_row)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def reload(self):
        try:
            self._config = self._config_service.load()
            for device_id, checkbox in self._checkboxes.items():
                checkbox.setChecked(self._config.is_enabled(device_id))
            self._set_status(f"Loaded: {self._config_service.config_path}", "#666666")
        except Exception as exc:
            self._set_status(f"Failed to load hardware configuration: {exc}", "red")
            QMessageBox.critical(self, "Hardware Configuration", str(exc))

    def save(self):
        try:
            if self._config is None:
                self._config = self._config_service.load()
            for device_id, checkbox in self._checkboxes.items():
                self._config.set_enabled(device_id, checkbox.isChecked())
            self._config_service.save(self._config)
            macro_path = self._macro_service.generate()
            config_path = Path(self._config_service.config_path).expanduser().resolve()
            macro_path = Path(macro_path).expanduser().resolve()
            self._set_status(f"Saved configuration and generated firmware macros: {macro_path}", "green")
            self.artifacts_generated.emit(
                "Hardware configuration generated successfully.\n"
                "Output artifacts:\n"
                f"  Hardware config: {config_path}\n"
                f"  Firmware macros: {macro_path}\n"
            )
            self.configuration_saved.emit()
        except Exception as exc:
            self._set_status(f"Failed to save hardware configuration: {exc}", "red")
            QMessageBox.critical(self, "Hardware Configuration", str(exc))

    def _set_status(self, text: str, color: str):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-weight: bold; color: {color};")
