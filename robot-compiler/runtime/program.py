from dataclasses import dataclass
from typing import List, Optional, Any
from .function import RuntimeFunction


@dataclass(frozen=True)
class RuntimeProgram:
    """
    Immutable runtime program, fully prepared for execution.
    Contains constants, functions, instructions, and the capabilities required
    by its instruction stream.
    """
    constants: List[Any]
    functions: List[RuntimeFunction]
    instructions: List[Any]          # list of RuntimeInstruction
    entry_function_id: int = 0
    abi_version: int = 1
    required_capabilities: tuple[str, ...] = ()

    def get_function(self, function_id: int) -> Optional[RuntimeFunction]:
        for f in self.functions:
            if f.function_id == function_id:
                return f
        return None

    def get_constant(self, index: int) -> Any:
        if index < 0 or index >= len(self.constants):
            raise IndexError(f"Constant index {index} out of range")
        return self.constants[index]

    def instruction_count(self) -> int:
        return len(self.instructions)
