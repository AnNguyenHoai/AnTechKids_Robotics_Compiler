# runtime/sensors/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional
from .sensor_value import SensorValue
from .sensor_event import SensorEvent, SensorEventType

class ISensor(ABC):
    """Base interface for all sensors."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the sensor hardware."""
        pass

    @abstractmethod
    def update(self) -> None:
        """Poll the sensor and update internal state."""
        pass

    @abstractmethod
    def read(self) -> SensorValue:
        """Return the current sensor reading."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the sensor to default state."""
        pass

    @abstractmethod
    def health(self) -> str:
        """Return health status: 'healthy', 'disconnected', 'timeout', 'invalid', 'calibration_required'."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Release hardware resources."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable sensor name."""
        pass

    @property
    @abstractmethod
    def event_handler(self):
        """Callback for events (optional)."""
        pass

    @event_handler.setter
    @abstractmethod
    def event_handler(self, handler):
        pass