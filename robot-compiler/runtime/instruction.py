# runtime/instruction.py
from dataclasses import dataclass
from typing import List, Any
from compiler.generated.opcode import Opcode

@dataclass(frozen=True)
class RuntimeInstruction:
    opcode: Opcode
    operands: List[Any]
    index: int