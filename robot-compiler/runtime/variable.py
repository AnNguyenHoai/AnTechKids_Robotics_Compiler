# runtime/variable.py
from typing import Dict, Optional
from .value import RuntimeValue

class VariableTable:
    def __init__(self, parent: Optional['VariableTable'] = None):
        self.parent = parent
        self.variables: Dict[str, RuntimeValue] = {}

    def get(self, name: str) -> Optional[RuntimeValue]:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, value: RuntimeValue):
        if name in self.variables:
            self.variables[name] = value
        elif self.parent:
            self.parent.set(name, value)
        else:
            raise KeyError(f"Variable '{name}' not defined")

    def define(self, name: str, value: RuntimeValue = None):
        if name in self.variables:
            raise RuntimeError(f"Variable '{name}' already defined")
        self.variables[name] = value

    def has(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.has(name)
        return False