# runtime/value/string.py
from .base import RuntimeValue

class StringValue(RuntimeValue):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self) -> str:
        return f'String("{self.value}")'

    def __eq__(self, other) -> bool:
        if isinstance(other, StringValue):
            return self.value == other.value
        return False

    def as_int(self) -> int:
        raise TypeError("Cannot convert string to int")

    def as_float(self) -> float:
        raise TypeError("Cannot convert string to float")

    def as_bool(self) -> bool:
        return len(self.value) > 0

    def as_string(self) -> str:
        return self.value