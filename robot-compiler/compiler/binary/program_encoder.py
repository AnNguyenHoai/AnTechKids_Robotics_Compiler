from ..isa import ISAProgram
from .header import BinaryHeader
from .instruction_encoder import InstructionEncoder
from .constant_pool_encoder import ConstantPoolEncoder


class ProgramEncoder:
    def encode(self, program: ISAProgram) -> bytes:
        pool_encoder = ConstantPoolEncoder()
        pool_data = pool_encoder.encode(program)

        ins_encoder = InstructionEncoder()
        ins_data = b""
        for func in program.functions:
            for ins in func.instructions:
                ins_data += ins_encoder.encode(ins)

        header = BinaryHeader.default()
        header.program_size = len(ins_data) + len(pool_data)

        result = header.to_bytes()
        result += pool_data
        result += ins_data

        return result