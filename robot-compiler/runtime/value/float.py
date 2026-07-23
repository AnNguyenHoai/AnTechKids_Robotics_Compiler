# runtime/value/float.py
from .base import RuntimeValue

class FloatValue(RuntimeValue):
    def __init__(self, value: float):
        self.value = value

    def __repr__(self) -> str:
        return f"Float({self.value})"

    def __eq__(self, other) -> bool:
        if isinstance(other, FloatValue):
            return self.value == other.value
        return False

    def as_int(self) -> int:
        return int(self.value)

    def as_float(self) -> float:
        return self.value

    def as_bool(self) -> bool:
        return self.value != 0.0

    def as_string(self) -> str:
        return str(self.value)