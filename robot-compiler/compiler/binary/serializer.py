# compiler/binary/serializer.py
import struct
from .model import BinaryProgram, ConstantPool, FunctionTable, InstructionStream
from .header import BinaryHeader
from .layout import OPERAND_TYPE_STRING

class BinarySerializer:
    @staticmethod
    def serialize(program: BinaryProgram) -> bytes:
        # Header
        header_bytes = program.header.to_bytes()
        result = header_bytes

        # Constant pool
        cp_bytes = BinarySerializer._serialize_constant_pool(program.constant_pool)
        result += cp_bytes

        # Function table
        ft_bytes = BinarySerializer._serialize_function_table(program.function_table)
        result += ft_bytes

        # Instruction stream
        result += program.instruction_stream.data

        return result

    @staticmethod
    def _serialize_constant_pool(cp: ConstantPool) -> bytes:
        constants = cp.constants
        result = struct.pack("<I", len(constants))
        for c in constants:
            if isinstance(c, str):
                encoded = c.encode('utf-8')
                result += struct.pack("<B", OPERAND_TYPE_STRING)
                result += struct.pack("<I", len(encoded))
                result += encoded
            else:
                # Chưa hỗ trợ các loại khác
                raise ValueError(f"Unsupported constant type: {type(c)}")
        return result

    @staticmethod
    def _serialize_function_table(ft: FunctionTable) -> bytes:
        entries = ft.entries
        result = struct.pack("<H", len(entries))
        for e in entries:
            result += struct.pack("<H I H", e.function_id, e.entry_offset, e.instruction_count)
        return result