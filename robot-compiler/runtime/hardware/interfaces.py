# runtime/hardware/interfaces.py
from abc import ABC, abstractmethod

class IMotorDriver(ABC):
    @abstractmethod
    def set_motor(self, left_pwm: int, right_pwm: int) -> None:
        """Set motor PWM values (range -100 to 100)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop motors."""
        pass

    @abstractmethod
    def brake(self) -> None:
        """Brake motors."""
        pass

class ITimer(ABC):
    @abstractmethod
    def delay(self, ms: int) -> None:
        """Blocking delay in milliseconds."""
        pass

    @abstractmethod
    def millis(self) -> int:
        """Return current time in milliseconds."""
        pass

    @abstractmethod
    def micros(self) -> int:
        """Return current time in microseconds."""
        pass

class ILogger(ABC):
    @abstractmethod
    def info(self, msg: str) -> None:
        pass

    @abstractmethod
    def warn(self, msg: str) -> None:
        pass

    @abstractmethod
    def error(self, msg: str) -> None:
        pass

    @abstractmethod
    def debug(self, msg: str) -> None:
        pass