"""Read-only RoboStudio client for the robot V2 health endpoint."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class RobotHealthNetworkError(RuntimeError):
    """Transport-level failure: robot cannot be reached."""


class RobotHealthPayloadError(RuntimeError):
    """Reachable endpoint returned malformed/incompatible health data."""


@dataclass(frozen=True)
class RobotHealthSnapshot:
    payload: dict[str, Any]

    @property
    def battery(self) -> dict[str, Any]:
        return self.payload["battery"]

    @property
    def motor(self) -> dict[str, Any]:
        return self.payload["motor"]

    @property
    def line(self) -> dict[str, Any]:
        return self.payload["line"]

    @property
    def encoder(self) -> dict[str, Any]:
        return self.payload["encoder"]

    @property
    def i2c(self) -> dict[str, Any]:
        return self.payload["i2c"]


def _require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise RobotHealthPayloadError(f"missing/invalid {key}")
    return value


def validate_health_payload(data: Any) -> RobotHealthSnapshot:
    if not isinstance(data, dict):
        raise RobotHealthPayloadError("health payload must be an object")
    if data.get("status") != "ok":
        raise RobotHealthPayloadError("robot health status is not ok")

    for key in ("ready", "robot_ready", "network_ready"):
        if not isinstance(data.get(key), bool):
            raise RobotHealthPayloadError(f"missing/invalid {key}")

    for key in ("hostname", "ip", "firmware_version", "board_profile", "board_revision", "reset_reason"):
        if not isinstance(data.get(key), str):
            raise RobotHealthPayloadError(f"missing/invalid {key}")

    for key in ("ota", "http_ota"):
        if not isinstance(data.get(key), bool):
            raise RobotHealthPayloadError(f"missing/invalid {key}")

    if not isinstance(data.get("uptime_ms"), int):
        raise RobotHealthPayloadError("missing/invalid uptime_ms")
    if not isinstance(data.get("rssi"), int):
        raise RobotHealthPayloadError("missing/invalid rssi")

    battery = _require_dict(data, "battery")
    if not isinstance(battery.get("voltage"), (int, float)) or not isinstance(battery.get("state"), str):
        raise RobotHealthPayloadError("invalid battery")

    motor = _require_dict(data, "motor")
    if not isinstance(motor.get("armed"), bool) or not isinstance(motor.get("enabled"), bool):
        raise RobotHealthPayloadError("invalid motor flags")
    if not isinstance(motor.get("state"), str) or not isinstance(motor.get("last_stop_reason"), str):
        raise RobotHealthPayloadError("invalid motor state")

    line = _require_dict(data, "line")
    if not isinstance(line.get("available"), bool) or not isinstance(line.get("healthy"), bool):
        raise RobotHealthPayloadError("invalid line status")
    if not isinstance(line.get("mask"), int):
        raise RobotHealthPayloadError("invalid line mask")

    encoder = _require_dict(data, "encoder")
    if not isinstance(encoder.get("available"), bool) or not isinstance(encoder.get("healthy"), bool):
        raise RobotHealthPayloadError("invalid encoder status")
    if not isinstance(encoder.get("left_count"), int) or not isinstance(encoder.get("right_count"), int):
        raise RobotHealthPayloadError("invalid encoder counts")

    i2c = _require_dict(data, "i2c")
    if not isinstance(i2c.get("healthy"), bool) or not isinstance(i2c.get("mcp23017"), bool):
        raise RobotHealthPayloadError("invalid i2c status")

    return RobotHealthSnapshot(dict(data))


class RobotHealthClient:
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    def get_health(self, host: str) -> RobotHealthSnapshot:
        target = str(host).strip()
        if not target:
            raise RobotHealthNetworkError("robot host is empty")
        url = f"http://{target}/api/v1/health"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise RobotHealthNetworkError(f"Unable to reach robot health endpoint: {exc}") from exc

        try:
            data = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RobotHealthPayloadError(f"Invalid health JSON: {exc}") from exc
        return validate_health_payload(data)
