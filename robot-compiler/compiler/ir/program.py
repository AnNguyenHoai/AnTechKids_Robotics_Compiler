from __future__ import annotations
from typing import List, Dict, Any, Optional
from .function import IRFunction
from .value import IRValue


class IRProgram:
    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        self.functions: List[IRFunction] = []
        self.globals: List[IRValue] = []
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"IRProgram(functions={len(self.functions)}, globals={len(self.globals)})"

    def add_function(self, function: IRFunction) -> None:
        self.functions.append(function)

    def add_global(self, value: IRValue) -> None:
        self.globals.append(value)

    def get_function(self, name: str) -> Optional[IRFunction]:
        for f in self.functions:
            if f.name == name:
                return f
        return None