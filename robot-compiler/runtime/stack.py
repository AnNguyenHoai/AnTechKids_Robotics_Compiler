# runtime/stack.py
from typing import List, Optional
from .value import RuntimeValue

class DataStack:
    def __init__(self, max_size: int = 1024):
        self.items: List[RuntimeValue] = []
        self.max_size = max_size

    def push(self, value: RuntimeValue):
        if len(self.items) >= self.max_size:
            raise OverflowError("Data stack overflow")
        self.items.append(value)

    def pop(self) -> RuntimeValue:
        if not self.items:
            raise IndexError("Data stack underflow")
        return self.items.pop()

    def peek(self) -> Optional[RuntimeValue]:
        if self.items:
            return self.items[-1]
        return None

    def clear(self):
        self.items.clear()

    def size(self) -> int:
        return len(self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0