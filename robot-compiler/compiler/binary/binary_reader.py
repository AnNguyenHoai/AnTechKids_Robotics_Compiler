"""
Binary Reader – reconstruct ISAProgram from binary bytes.
"""

from typing import Tuple
from ..isa import ISAProgram, ISAFunction, ISAInstruction, RobotOpcode
from .header import BinaryHeader
from .instruction_encoder import InstructionEncoder
from .constant_pool_encoder import ConstantPoolEncoder

# Kích thước header cố định
HEADER_SIZE = 19  # phải khớp với BinaryHeader.size()

class BinaryReader:
    def read(self, data: bytes) -> ISAProgram:
        offset = 0
        header = BinaryHeader.from_bytes(data[offset:offset+HEADER_SIZE])
        offset += HEADER_SIZE

        # Đọc constant pool
        pool_encoder = ConstantPoolEncoder()
        constants, offset = pool_encoder.decode(data, offset)

        # Tạo registry cho tất cả opcodes
        registry = {op.value: op for op in RobotOpcode}

        # Giả sử tất cả instructions thuộc về một hàm "main"
        func = ISAFunction("main")
        ins_encoder = InstructionEncoder()

        while offset < len(data):
            ins, offset = ins_encoder.decode(data, offset, registry)
            func.add_instruction(ins)

        prog = ISAProgram()
        prog.add_function(func)
        # Có thể lưu constants vào metadata hoặc ignore
        return prog