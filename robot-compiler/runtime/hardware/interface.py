# runtime/hardware/interface.py
from abc import ABC, abstractmethod

class IHardware(ABC):
    """Hardware abstraction layer for robot peripherals."""

    @abstractmethod
    def set_motor(self, left: int, right: int) -> None:
        """Set motor speeds (range -100 to 100)."""
        pass

    @abstractmethod
    def delay(self, ms: int) -> None:
        """Blocking delay in milliseconds."""
        pass

    @abstractmethod
    def read_ultrasonic(self) -> int:
        """Read ultrasonic sensor distance in cm."""
        pass

    @abstractmethod
    def read_line_sensor(self, channel: int) -> int:
        """Read line sensor value (0-1023) for given channel."""
        pass

    @abstractmethod
    def read_touch(self, port: int) -> bool:
        """Read touch sensor state."""
        pass

    # New sensor methods
    @abstractmethod
    def read_light(self, channel: int) -> int:
        """Read light sensor value (0-1023)."""
        pass

    @abstractmethod
    def read_color(self) -> int:
        """Read color sensor (placeholder)."""
        pass