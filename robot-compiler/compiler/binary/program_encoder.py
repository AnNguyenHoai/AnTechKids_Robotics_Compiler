# compiler/binary/program_encoder.py
from ..isa import ISAProgram
from .instruction_encoder import InstructionEncoder
from .constant_pool import ConstantPoolBuilder
from .header import BinaryHeader
from .model import BinaryProgram, ConstantPool, FunctionTable, FunctionTableEntry, InstructionStream

class ProgramEncoder:
    def encode(self, program: ISAProgram) -> BinaryProgram:
        # 1. Xây dựng constant pool
        cp = ConstantPoolBuilder.build(program)

        # 2. Mã hóa instruction stream
        ins_encoder = InstructionEncoder()
        entries = []
        stream = b""
        current_offset = 0

        for idx, func in enumerate(program.functions):
            # Lưu entry cho hàm này
            entries.append(FunctionTableEntry(
                function_id=idx,
                entry_offset=current_offset,
                instruction_count=len(func.instructions)
            ))
            # Mã hóa từng instruction và nối vào stream
            for ins in func.instructions:
                stream += ins_encoder.encode(ins)
            current_offset = len(stream)

        ft = FunctionTable(entries)
        inst_stream = InstructionStream(stream)

        # 3. Header (program_size sẽ được serializer tính lại)
        header = BinaryHeader.default()

        return BinaryProgram(
            header=header,
            constant_pool=cp,
            function_table=ft,
            instruction_stream=inst_stream,
            metadata=None
        )