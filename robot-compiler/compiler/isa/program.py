from typing import List, Dict, Any, Optional
from .function import ISAFunction


class ISAProgram:
    """Complete executable Robot ISA program."""

    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        self._functions: List[ISAFunction] = []
        self._metadata = metadata or {}
        self._constant_pool: List[Any] = []  # future

    @property
    def functions(self) -> List[ISAFunction]:
        return self._functions

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def function_count(self) -> int:
        return len(self._functions)

    def add_function(self, function: ISAFunction) -> None:
        self._functions.append(function)

    def get_function(self, name: str) -> Optional[ISAFunction]:
        for func in self._functions:
            if func.name == name:
                return func
        return None

    def add_constant(self, value: Any) -> int:
        """Add constant to pool, return index."""
        self._constant_pool.append(value)
        return len(self._constant_pool) - 1

    def get_constant(self, index: int) -> Any:
        return self._constant_pool[index]