# runtime/value/integer.py
from .base import RuntimeValue

class IntegerValue(RuntimeValue):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self) -> str:
        return f"Integer({self.value})"

    def __eq__(self, other) -> bool:
        if isinstance(other, IntegerValue):
            return self.value == other.value
        return False

    def as_int(self) -> int:
        return self.value

    def as_float(self) -> float:
        return float(self.value)

    def as_bool(self) -> bool:
        return self.value != 0

    def as_string(self) -> str:
        return str(self.value)