# runtime/sensors/sensor_manager.py
from typing import Dict, List, Optional, Type
from .base import ISensor
from .sensor_value import SensorValue
from .sensor_event import SensorEvent, SensorEventType

class SensorManager:
    """Manages multiple sensors: registration, lifecycle, polling."""

    def __init__(self):
        self._sensors: Dict[str, ISensor] = {}
        self._callbacks = []

    def register(self, sensor: ISensor) -> None:
        """Register a sensor instance."""
        if sensor.name in self._sensors:
            raise ValueError(f"Sensor '{sensor.name}' already registered")
        self._sensors[sensor.name] = sensor

    def initialize_all(self) -> None:
        """Initialize all registered sensors."""
        for name, sensor in self._sensors.items():
            try:
                sensor.initialize()
            except Exception as e:
                print(f"[SensorManager] Error initializing {name}: {e}")

    def update_all(self) -> None:
        """Update all sensors (poll hardware)."""
        for name, sensor in self._sensors.items():
            try:
                sensor.update()
            except Exception as e:
                print(f"[SensorManager] Error updating {name}: {e}")

    def read(self, sensor_name: str) -> Optional[SensorValue]:
        """Read a sensor by name."""
        sensor = self._sensors.get(sensor_name)
        if sensor is None:
            return None
        return sensor.read()

    def health(self, sensor_name: str) -> Optional[str]:
        """Get health status of a sensor."""
        sensor = self._sensors.get(sensor_name)
        if sensor is None:
            return None
        return sensor.health()

    def shutdown_all(self) -> None:
        """Shutdown all sensors."""
        for name, sensor in self._sensors.items():
            try:
                sensor.shutdown()
            except Exception as e:
                print(f"[SensorManager] Error shutting down {name}: {e}")

    def get_all_sensor_names(self) -> List[str]:
        return list(self._sensors.keys())

    # Event handling (optional, future)
    def on_event(self, callback):
        """Register a callback for sensor events."""
        self._callbacks.append(callback)