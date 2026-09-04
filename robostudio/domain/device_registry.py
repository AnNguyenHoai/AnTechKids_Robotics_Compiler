"""Registry of known RoboStudio hardware devices.

H25-A intentionally keeps the registry UI-agnostic. Future tabs, profiles and
macro generators consume this registry rather than duplicating device metadata.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class DeviceDefinition:
    """Stable definition of one selectable hardware feature."""

    device_id: str
    display_name: str
    category: str
    default_enabled: bool = False
    description: str = ""


class DeviceRegistry:
    """Central registry for supported hardware features."""

    _DEVICES: Tuple[DeviceDefinition, ...] = (
        DeviceDefinition(
            "motor", "Motor", "motion", True,
            "Main left/right drive motors.",
        ),
        DeviceDefinition(
            "encoder", "Motor Encoder", "motion", False,
            "Wheel or motor feedback encoder support.",
        ),
        DeviceDefinition(
            "line_sensor", "Line Sensor", "sensors", True,
            "Reflective line sensor array.",
        ),
        DeviceDefinition(
            "ultrasonic", "Ultrasonic Sensor", "sensors", False,
            "Distance measurement sensor.",
        ),
        DeviceDefinition(
            "imu", "MPU6050 IMU", "sensors", False,
            "Inertial measurement unit for heading and motion assistance.",
        ),
        DeviceDefinition(
            "servo", "Servo", "expansion", False,
            "Servo actuator support.",
        ),
        DeviceDefinition(
            "buzzer", "Buzzer", "expansion", False,
            "Audio/buzzer output support.",
        ),
    )
    _BY_ID: Dict[str, DeviceDefinition] = {d.device_id: d for d in _DEVICES}

    @classmethod
    def all(cls) -> Tuple[DeviceDefinition, ...]:
        return cls._DEVICES

    @classmethod
    def get(cls, device_id: str) -> Optional[DeviceDefinition]:
        return cls._BY_ID.get(device_id)

    @classmethod
    def require(cls, device_id: str) -> DeviceDefinition:
        device = cls.get(device_id)
        if device is None:
            raise KeyError(f"Unknown device: {device_id}")
        return device

    @classmethod
    def ids(cls) -> Tuple[str, ...]:
        return tuple(d.device_id for d in cls._DEVICES)

    @classmethod
    def by_category(cls, category: str) -> Tuple[DeviceDefinition, ...]:
        return tuple(d for d in cls._DEVICES if d.category == category)

    @classmethod
    def defaults(cls) -> Dict[str, bool]:
        return {d.device_id: d.default_enabled for d in cls._DEVICES}
