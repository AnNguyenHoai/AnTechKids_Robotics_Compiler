# compiler/binary/__init__.py
from .header import BinaryHeader, Magic, Endianness
from .operand_encoder import OperandEncoder
from .instruction_encoder import InstructionEncoder
from .constant_pool import ConstantPoolBuilder
from .program_encoder import ProgramEncoder
from .binary_reader import BinaryReader
from .binary_printer import BinaryPrinter
from .serializer import BinarySerializer
from .model import (
    BinaryProgram,
    ConstantPool,
    FunctionTable,
    FunctionTableEntry,
    InstructionStream,
    Metadata,
)
from .descriptor import OpcodeDescriptor

__all__ = [
    "BinaryHeader",
    "Magic",
    "Endianness",
    "OperandEncoder",
    "InstructionEncoder",
    "ConstantPoolBuilder",
    "ProgramEncoder",
    "BinaryReader",
    "BinaryPrinter",
    "BinarySerializer",
    "BinaryProgram",
    "ConstantPool",
    "FunctionTable",
    "FunctionTableEntry",
    "InstructionStream",
    "Metadata",
    "OpcodeDescriptor",
]