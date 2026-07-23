# runtime/value/reference.py
from .base import RuntimeValue

class ReferenceValue(RuntimeValue):
    def __init__(self, index: int):
        self.index = index

    def __repr__(self) -> str:
        return f"Reference({self.index})"

    def __eq__(self, other) -> bool:
        if isinstance(other, ReferenceValue):
            return self.index == other.index
        return False

    def as_int(self) -> int:
        return self.index

    def as_float(self) -> float:
        return float(self.index)

    def as_bool(self) -> bool:
        return True

    def as_string(self) -> str:
        return f"ref:{self.index}"