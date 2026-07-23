# runtime/value/base.py
from abc import ABC, abstractmethod

class RuntimeValue(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def as_int(self) -> int:
        pass

    @abstractmethod
    def as_float(self) -> float:
        pass

    @abstractmethod
    def as_bool(self) -> bool:
        pass

    @abstractmethod
    def as_string(self) -> str:
        pass

    def is_integer(self) -> bool:
        return isinstance(self, IntegerValue)
    def is_float(self) -> bool:
        return isinstance(self, FloatValue)
    def is_boolean(self) -> bool:
        return isinstance(self, BooleanValue)
    def is_string(self) -> bool:
        return isinstance(self, StringValue)
    def is_reference(self) -> bool:
        return isinstance(self, ReferenceValue)# runtime/value/base.py
from abc import ABC, abstractmethod

class RuntimeValue(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def as_int(self) -> int:
        pass

    @abstractmethod
    def as_float(self) -> float:
        pass

    @abstractmethod
    def as_bool(self) -> bool:
        pass

    @abstractmethod
    def as_string(self) -> str:
        pass

    def is_integer(self) -> bool:
        return isinstance(self, IntegerValue)
    def is_float(self) -> bool:
        return isinstance(self, FloatValue)
    def is_boolean(self) -> bool:
        return isinstance(self, BooleanValue)
    def is_string(self) -> bool:
        return isinstance(self, StringValue)
    def is_reference(self) -> bool:
        return isinstance(self, ReferenceValue)