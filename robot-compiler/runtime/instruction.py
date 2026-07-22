# robot-compiler/runtime/instruction.py
from dataclasses import dataclass
from typing import List, Any
from ..compiler.isa import RobotOpcode


@dataclass(frozen=True)
class RuntimeInstruction:
    """
    Immutable decoded instruction ready for execution.
    All operands are resolved to concrete values (int, float, str, bool, index, etc.).
    """
    opcode: RobotOpcode
    operands: List[Any]          # decoded operand values
    index: int                   # global instruction index in the program