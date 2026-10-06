"""Reusable Student/Teacher robot-health panel."""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from services.robot_health_presenter import RobotHealthPresenter
from services.robot_health_service import RobotHealthSnapshot


class RobotHealthPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Robot Health", parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        top = QHBoxLayout()
        self.connection_label = QLabel("No robot selected")
        self.connection_label.setObjectName("health_connection")
        self.connection_label.setStyleSheet("font-weight: 700;")
        top.addWidget(self.connection_label)
        top.addStretch(1)
        self.refresh_button = QPushButton("Refresh Health")
        self.refresh_button.setObjectName("refresh_health")
        top.addWidget(self.refresh_button)
        layout.addLayout(top)

        summary = QHBoxLayout()
        self.battery_label = QLabel("Battery —")
        self.motor_label = QLabel("Motor —")
        self.line_label = QLabel("Line Sensor —")
        for label in (self.battery_label, self.motor_label, self.line_label):
            label.setStyleSheet("font-weight: 600;")
            summary.addWidget(label)
        summary.addStretch(1)
        layout.addLayout(summary)

        self.teacher_button = QPushButton("Teacher Diagnostics")
        self.teacher_button.setCheckable(True)
        self.teacher_button.setChecked(False)
        layout.addWidget(self.teacher_button)

        self.teacher_details = QLabel("")
        self.teacher_details.setObjectName("teacher_health_details")
        self.teacher_details.setWordWrap(True)
        self.teacher_details.setTextInteractionFlags(self.teacher_details.textInteractionFlags())
        self.teacher_details.setVisible(False)
        self.teacher_button.toggled.connect(self.teacher_details.setVisible)
        layout.addWidget(self.teacher_details)

    def show_no_robot(self) -> None:
        self.connection_label.setText("No robot selected")
        self.battery_label.setText("Battery —")
        self.motor_label.setText("Motor —")
        self.line_label.setText("Line Sensor —")
        self.teacher_details.setText("")
        self.refresh_button.setEnabled(False)

    def show_offline(self) -> None:
        self.connection_label.setText("Robot Offline")
        self.battery_label.setText("Battery —")
        self.motor_label.setText("Motor —")
        self.line_label.setText("Line Sensor —")
        self.teacher_details.setText("Health endpoint unavailable because the selected robot is offline.")
        self.refresh_button.setEnabled(False)

    def show_loading(self) -> None:
        self.connection_label.setText("Checking robot health…")
        self.refresh_button.setEnabled(False)

    def show_network_error(self, message: str) -> None:
        # Transport failure is intentionally not rendered as a robot subsystem fault.
        self.connection_label.setText("Connection error")
        self.battery_label.setText("Battery —")
        self.motor_label.setText("Motor —")
        self.line_label.setText("Line Sensor —")
        self.teacher_details.setText(f"Network error: {message}")
        self.refresh_button.setEnabled(True)

    def show_payload_error(self, message: str) -> None:
        self.connection_label.setText("Health data error")
        self.teacher_details.setText(f"Robot responded, but health data is invalid: {message}")
        self.refresh_button.setEnabled(True)

    def show_health(self, snapshot: RobotHealthSnapshot) -> None:
        student = RobotHealthPresenter.student(snapshot)
        teacher = RobotHealthPresenter.teacher(snapshot)
        self.connection_label.setText(student.connection)
        self.battery_label.setText(student.battery)
        self.motor_label.setText(student.motor)
        self.line_label.setText(student.line_sensor)
        self.teacher_details.setText(teacher.text)
        self.refresh_button.setEnabled(True)
