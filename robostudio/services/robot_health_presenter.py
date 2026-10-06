"""Presentation mapping for V2 Robot Health student/teacher views."""
from __future__ import annotations

from dataclasses import dataclass

from services.robot_health_service import RobotHealthSnapshot


@dataclass(frozen=True)
class StudentHealthView:
    connection: str
    battery: str
    motor: str
    line_sensor: str


@dataclass(frozen=True)
class TeacherHealthView:
    text: str


class RobotHealthPresenter:
    @staticmethod
    def student(snapshot: RobotHealthSnapshot) -> StudentHealthView:
        data = snapshot.payload
        battery_state = str(snapshot.battery["state"]).upper()
        motor_state = str(snapshot.motor["state"]).upper()

        connection = "Robot Connected"
        battery = f"Battery {battery_state}"

        if motor_state in ("ARMED", "RUNNING"):
            motor = "Motor ARMED"
        elif motor_state == "SAFE":
            motor = "Motor SAFE"
        else:
            motor = f"Motor {motor_state}"

        line = snapshot.line
        if not line["available"]:
            line_sensor = "Line Sensor N/A"
        elif line["healthy"]:
            line_sensor = "Line Sensor OK"
        else:
            line_sensor = "Line Sensor CHECK"

        return StudentHealthView(connection, battery, motor, line_sensor)

    @staticmethod
    def teacher(snapshot: RobotHealthSnapshot) -> TeacherHealthView:
        data = snapshot.payload
        battery = snapshot.battery
        motor = snapshot.motor
        line = snapshot.line
        encoder = snapshot.encoder
        i2c = snapshot.i2c
        mask = int(line["mask"]) & 0x1F
        lines = [
            f"Battery: {float(battery['voltage']):.2f} V ({battery['state']})",
            f"Reset reason: {data['reset_reason']}",
            f"Wi-Fi RSSI: {data['rssi']} dBm",
            f"Line raw: {mask:05b} (0x{mask:02X}) · {'OK' if line['healthy'] else 'CHECK'}",
            (
                "Encoder: "
                f"{'OK' if encoder['healthy'] else ('N/A' if not encoder['available'] else 'CHECK')} "
                f"· L={encoder['left_count']} R={encoder['right_count']}"
            ),
            (
                f"Motor: state={motor['state']} armed={motor['armed']} "
                f"enabled={motor['enabled']}"
            ),
            f"Firmware: {data['firmware_version']}",
            f"Board revision: {data['board_revision']}",
            f"Uptime: {data['uptime_ms']} ms",
            f"I2C: {'OK' if i2c['healthy'] else 'CHECK'} · MCP23017={'OK' if i2c['mcp23017'] else 'CHECK'}",
            f"Last stop reason: {motor['last_stop_reason']}",
        ]
        return TeacherHealthView("\n".join(lines))
