# compiler/isa/instruction.py
from typing import List, Optional, Any
from compiler.generated.opcode import Opcode
from .operand import ISAOperand

class ISAInstruction:
    def __init__(self, opcode: Opcode, operands: Optional[List[ISAOperand]] = None, metadata: Optional[Any] = None):
        self._opcode = opcode
        self._operands = tuple(operands) if operands else ()
        self._metadata = metadata

    @property
    def opcode(self) -> Opcode:
        return self._opcode

    @property
    def operands(self) -> tuple:
        return self._operands

    @property
    def operand_count(self) -> int:
        return len(self._operands)