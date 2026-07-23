# runtime/robot/interface.py
from abc import ABC, abstractmethod

class IRobot(ABC):
    """Robot interface that the VM uses to control the robot."""

    @abstractmethod
    def forward(self, speed: int) -> None:
        """Move robot forward at given speed."""
        pass

    @abstractmethod
    def backward(self, speed: int) -> None:
        """Move robot backward at given speed."""
        pass

    @abstractmethod
    def left(self, speed: int) -> None:
        """Turn robot left at given speed."""
        pass

    @abstractmethod
    def right(self, speed: int) -> None:
        """Turn robot right at given speed."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop all motion."""
        pass

    @abstractmethod
    def wait(self, ms: int) -> None:
        """Blocking delay in milliseconds."""
        pass

    @abstractmethod
    def set_motor(self, left: int, right: int) -> None:
        """Set individual motor speeds."""
        pass

    # Future APIs
    # def buzzer(self, frequency: int, duration: int) -> None: ...
    # def servo(self, port: int, angle: int) -> None: ...
    # def led(self, port: int, state: bool) -> None: ...
    # def read_ultrasonic(self) -> int: ...
    # def read_line_sensor(self, channel: int) -> int: ...