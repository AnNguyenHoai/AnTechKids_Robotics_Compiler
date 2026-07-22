# robot-compiler/runtime/function.py
from dataclasses import dataclass
from typing import List
from .instruction import RuntimeInstruction


@dataclass(frozen=True)
class RuntimeFunction:
    """
    Immutable runtime function.
    Contains metadata and the list of instructions belonging to this function.
    """
    function_id: int
    entry_index: int                  # index of first instruction in global instruction list
    instruction_count: int
    instructions: List[RuntimeInstruction]
    local_variable_count: int = 0
    stack_size: int = 0