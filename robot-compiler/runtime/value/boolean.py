# runtime/value/boolean.py
from .base import RuntimeValue

class BooleanValue(RuntimeValue):
    def __init__(self, value: bool):
        self.value = value

    def __repr__(self) -> str:
        return f"Boolean({self.value})"

    def __eq__(self, other) -> bool:
        if isinstance(other, BooleanValue):
            return self.value == other.value
        return False

    def as_int(self) -> int:
        return 1 if self.value else 0

    def as_float(self) -> float:
        return 1.0 if self.value else 0.0

    def as_bool(self) -> bool:
        return self.value

    def as_string(self) -> str:
        return "true" if self.value else "false"