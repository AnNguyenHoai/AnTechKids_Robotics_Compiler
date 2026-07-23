# runtime/memory.py
from typing import List
from .value import RuntimeValue

class MemoryManager:
    def __init__(self):
        self.allocations: List[RuntimeValue] = []

    def allocate(self, value: RuntimeValue) -> int:
        self.allocations.append(value)
        return len(self.allocations) - 1

    def get(self, index: int) -> RuntimeValue:
        if index < 0 or index >= len(self.allocations):
            raise IndexError("Memory index out of bounds")
        return self.allocations[index]

    def set(self, index: int, value: RuntimeValue):
        if index < 0 or index >= len(self.allocations):
            raise IndexError("Memory index out of bounds")
        self.allocations[index] = value

    def clear(self):
        self.allocations.clear()