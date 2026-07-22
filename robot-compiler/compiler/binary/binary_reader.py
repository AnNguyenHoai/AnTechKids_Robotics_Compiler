# compiler/binary/binary_reader.py
import struct
from .model import BinaryProgram, ConstantPool, FunctionTable, FunctionTableEntry, InstructionStream
from .header import BinaryHeader, HEADER_SIZE
from .layout import OPERAND_TYPE_STRING

class BinaryReader:
    def read(self, data: bytes) -> BinaryProgram:
        offset = 0
        header = BinaryHeader.from_bytes(data[offset:offset+HEADER_SIZE])
        offset += HEADER_SIZE

        # Đọc constant pool
        cp, offset = self._read_constant_pool(data, offset)

        # Đọc function table
        ft, offset = self._read_function_table(data, offset)

        # Phần còn lại là instruction stream
        inst_stream = InstructionStream(data[offset:])

        return BinaryProgram(header, cp, ft, inst_stream)

    def _read_constant_pool(self, data, offset):
        count = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4
        constants = []
        for _ in range(count):
            tag = data[offset]
            offset += 1
            if tag == OPERAND_TYPE_STRING:
                length = struct.unpack("<I", data[offset:offset+4])[0]
                offset += 4
                s = data[offset:offset+length].decode('utf-8')
                offset += length
                constants.append(s)
            else:
                raise ValueError(f"Unsupported constant tag: {tag}")
        return ConstantPool(constants), offset

    def _read_function_table(self, data, offset):
        entry_count = struct.unpack("<H", data[offset:offset+2])[0]
        offset += 2
        entries = []
        for _ in range(entry_count):
            func_id, entry_offset, ins_count = struct.unpack("<H I H", data[offset:offset+8])
            offset += 8
            entries.append(FunctionTableEntry(func_id, entry_offset, ins_count))
        return FunctionTable(entries), offset