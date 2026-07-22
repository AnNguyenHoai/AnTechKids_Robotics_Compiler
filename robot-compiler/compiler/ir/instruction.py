from __future__ import annotations
from typing import List, Optional, Any
from .value import IRValue
from .opcode import IROpcode
from .source_location import SourceLocation


class IRInstruction:
    def __init__(self, opcode: IROpcode,
                 operands: Optional[List[IRValue]] = None,
                 location: Optional[SourceLocation] = None,
                 metadata: Optional[Any] = None):
        self.opcode = opcode
        self.operands = operands if operands is not None else []
        self.location = location
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"IRInstruction(opcode={self.opcode.name}, operands={len(self.operands)})"

    def add_operand(self, value: IRValue) -> None:
        self.operands.append(value)

    def replace_operand(self, index: int, value: IRValue) -> None:
        self.operands[index] = value