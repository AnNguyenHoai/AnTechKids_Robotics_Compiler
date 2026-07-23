# compiler/isa/__init__.py
from compiler.generated.opcode import Opcode as RobotOpcode
from .operand import ISAOperand, OperandKind
from .instruction import ISAInstruction
from .function import ISAFunction
from .program import ISAProgram
from .builder import InstructionBuilder
from .printer import InstructionPrinter
from .backend import BackendLowering

# Re-export Opcode under the name RobotOpcode for backward compatibility
RobotOpcode = RobotOpcode

__all__ = [
    "RobotOpcode",
    "ISAOperand",
    "OperandKind",
    "ISAInstruction",
    "ISAFunction",
    "ISAProgram",
    "InstructionBuilder",
    "InstructionPrinter",
    "BackendLowering",
]