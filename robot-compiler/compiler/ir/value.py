from enum import Enum, auto
from typing import Union, Optional


class ValueKind(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    VARIABLE = auto()
    ENUM = auto()
    TEMPORARY = auto()


class IRValue:
    def __init__(self, kind: ValueKind, value: Union[int, float, bool, str, int],
                 name: Optional[str] = None, value_id: Optional[int] = None):
        self.kind = kind
        self.value = value
        self.name = name
        self.id = value_id   # unique id (future SSA)

    def __repr__(self) -> str:
        if self.name is not None:
            return f"IRValue(kind={self.kind.name}, name='{self.name}')"
        return f"IRValue(kind={self.kind.name}, value={repr(self.value)})"

    @classmethod
    def integer(cls, val: int) -> "IRValue":
        return cls(ValueKind.INTEGER, val)

    @classmethod
    def float(cls, val: float) -> "IRValue":
        return cls(ValueKind.FLOAT, val)

    @classmethod
    def boolean(cls, val: bool) -> "IRValue":
        return cls(ValueKind.BOOLEAN, val)

    @classmethod
    def string(cls, val: str) -> "IRValue":
        return cls(ValueKind.STRING, val)

    @classmethod
    def variable(cls, name: str, index: Optional[int] = None) -> "IRValue":
        return cls(ValueKind.VARIABLE, index if index is not None else 0, name)

    @classmethod
    def enum(cls, val: int) -> "IRValue":
        return cls(ValueKind.ENUM, val)

    @classmethod
    def temporary(cls, name: str, index: int) -> "IRValue":
        return cls(ValueKind.TEMPORARY, index, name)

    def as_integer(self) -> int:
        if self.kind != ValueKind.INTEGER:
            raise TypeError(f"Value is not integer: {self.kind}")
        return self.value

    def as_float(self) -> float:
        if self.kind != ValueKind.FLOAT:
            raise TypeError(f"Value is not float: {self.kind}")
        return self.value

    def as_boolean(self) -> bool:
        if self.kind != ValueKind.BOOLEAN:
            raise TypeError(f"Value is not boolean: {self.kind}")
        return self.value

    def as_string(self) -> str:
        if self.kind != ValueKind.STRING:
            raise TypeError(f"Value is not string: {self.kind}")
        return self.value

    def as_index(self) -> int:
        if self.kind not in (ValueKind.VARIABLE, ValueKind.TEMPORARY, ValueKind.ENUM):
            raise TypeError(f"Value has no index: {self.kind}")
        return self.value