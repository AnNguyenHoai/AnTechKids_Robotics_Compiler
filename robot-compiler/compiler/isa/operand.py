from enum import Enum
from typing import Union, Optional


class OperandKind(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"
    REGISTER = "register"
    LABEL = "label"
    CONSTANT_POOL = "constant_pool"


class ISAOperand:
    """Type-safe operand for Robot ISA instructions."""

    def __init__(self, kind: OperandKind, value: Union[int, float, bool, str, int]):
        self._kind = kind
        self._value = value

    @property
    def kind(self) -> OperandKind:
        return self._kind

    @property
    def value(self):
        return self._value

    # Convenience constructors
    @classmethod
    def integer(cls, val: int) -> "ISAOperand":
        return cls(OperandKind.INTEGER, val)

    @classmethod
    def float(cls, val: float) -> "ISAOperand":
        return cls(OperandKind.FLOAT, val)

    @classmethod
    def boolean(cls, val: bool) -> "ISAOperand":
        return cls(OperandKind.BOOLEAN, val)

    @classmethod
    def string(cls, val: str) -> "ISAOperand":
        return cls(OperandKind.STRING, val)

    @classmethod
    def enum(cls, val: int) -> "ISAOperand":
        return cls(OperandKind.ENUM, val)

    @classmethod
    def register(cls, idx: int) -> "ISAOperand":
        return cls(OperandKind.REGISTER, idx)

    @classmethod
    def label(cls, idx: int) -> "ISAOperand":
        return cls(OperandKind.LABEL, idx)

    @classmethod
    def constant_pool(cls, idx: int) -> "ISAOperand":
        return cls(OperandKind.CONSTANT_POOL, idx)

    # Accessors
    def as_integer(self) -> int:
        if self._kind != OperandKind.INTEGER:
            raise TypeError(f"Operand is not integer: {self._kind}")
        return self._value

    def as_float(self) -> float:
        if self._kind != OperandKind.FLOAT:
            raise TypeError(f"Operand is not float: {self._kind}")
        return self._value

    def as_boolean(self) -> bool:
        if self._kind != OperandKind.BOOLEAN:
            raise TypeError(f"Operand is not boolean: {self._kind}")
        return self._value

    def as_string(self) -> str:
        if self._kind != OperandKind.STRING:
            raise TypeError(f"Operand is not string: {self._kind}")
        return self._value

    def as_index(self) -> int:
        if self._kind not in (OperandKind.REGISTER, OperandKind.LABEL,
                              OperandKind.CONSTANT_POOL, OperandKind.ENUM):
            raise TypeError(f"Operand has no index: {self._kind}")
        return self._value

    def __repr__(self) -> str:
        return f"ISAOperand(kind={self._kind.value}, value={repr(self._value)})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, ISAOperand):
            return False
        return self._kind == other._kind and self._value == other._value