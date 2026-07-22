from typing import List, Optional, Any
from .opcode import RobotOpcode
from .operand import ISAOperand


class ISAInstruction:
    """Immutable Robot ISA instruction."""

    def __init__(
        self,
        opcode: RobotOpcode,
        operands: Optional[List[ISAOperand]] = None,
        metadata: Optional[Any] = None
    ):
        self._opcode = opcode
        self._operands = tuple(operands) if operands else ()
        self._metadata = metadata

    @property
    def opcode(self) -> RobotOpcode:
        return self._opcode

    @property
    def operands(self) -> tuple:
        return self._operands

    @property
    def metadata(self) -> Optional[Any]:
        return self._metadata

    @property
    def operand_count(self) -> int:
        return len(self._operands)

    def __repr__(self) -> str:
        return f"ISAInstruction(opcode={self._opcode.name}, operands={self.operand_count})"