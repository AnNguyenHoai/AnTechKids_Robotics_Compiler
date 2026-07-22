# compiler/binary/model.py
from dataclasses import dataclass
from typing import List, Any, Optional, Dict
from .header import BinaryHeader

@dataclass(frozen=True)
class ConstantPool:
    constants: List[Any]  # hỗ trợ int, float, str, bool

@dataclass(frozen=True)
class FunctionTableEntry:
    function_id: int
    entry_offset: int      # byte offset trong instruction stream
    instruction_count: int

@dataclass(frozen=True)
class FunctionTable:
    entries: List[FunctionTableEntry]

@dataclass(frozen=True)
class InstructionStream:
    data: bytes

@dataclass(frozen=True)
class Metadata:
    data: Dict[str, Any]

@dataclass(frozen=True)
class BinaryProgram:
    header: BinaryHeader
    constant_pool: ConstantPool
    function_table: FunctionTable
    instruction_stream: InstructionStream
    metadata: Optional[Metadata] = None