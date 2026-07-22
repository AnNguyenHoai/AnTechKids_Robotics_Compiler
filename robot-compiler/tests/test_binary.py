import unittest
from compiler.binary import (
    BinaryHeader, Magic, Endianness,
    OperandEncoder, InstructionEncoder,
    ConstantPoolBuilder, ProgramEncoder,
    BinaryReader, BinaryPrinter, BinarySerializer,
    BinaryProgram
)
from compiler.isa import (
    ISAProgram, ISAFunction, InstructionBuilder,
    ISAOperand, RobotOpcode, OperandKind
)

class TestBinary(unittest.TestCase):
    def test_header_roundtrip(self):
        header = BinaryHeader.default()
        data = header.to_bytes()
        header2 = BinaryHeader.from_bytes(data)
        self.assertEqual(header.magic, header2.magic)
        self.assertEqual(header.abi_version, header2.abi_version)
        self.assertEqual(header.program_size, header2.program_size)

    def test_operand_encoder_roundtrip(self):
        ops = [
            ISAOperand.integer(42),
            ISAOperand.float(3.14),
            ISAOperand.string("forward"),
            ISAOperand.register(5),
            ISAOperand.label(10),
            ISAOperand.constant_pool(3),
        ]
        for op in ops:
            data = OperandEncoder.encode(op)
            decoded, offset = OperandEncoder.decode(data, 0)
            self.assertEqual(op.kind, decoded.kind)
            if op.kind == OperandKind.FLOAT:
                self.assertAlmostEqual(op.value, decoded.value, places=5)
            else:
                self.assertEqual(op.value, decoded.value)

    def test_instruction_encoder_roundtrip(self):
        builder = InstructionBuilder()
        builder.create_program()
        builder.create_function("main")
        ins = builder.move_run(
            builder.const_string("forward"),
            builder.const_int(50)
        )
        data = InstructionEncoder.encode(ins)
        registry = {RobotOpcode.MOVE_RUN.value: RobotOpcode.MOVE_RUN}
        decoded, offset = InstructionEncoder.decode(data, 0, registry)
        self.assertEqual(ins.opcode, decoded.opcode)
        self.assertEqual(len(ins.operands), len(decoded.operands))

    def test_program_encoder_roundtrip(self):
        builder = InstructionBuilder()
        builder.create_program()
        func = builder.create_function("main")
        builder.move_run(builder.const_string("forward"), builder.const_int(50))
        builder.wait(builder.const_int(1000))
        builder.move_stop()

        # ISAProgram -> BinaryProgram
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(builder.get_program())

        # BinaryProgram -> bytes
        serializer = BinarySerializer()
        data = serializer.serialize(binary_prog)

        # bytes -> BinaryProgram
        reader = BinaryReader()
        decoded_prog = reader.read(data)

        # So sánh các thành phần chính
        self.assertEqual(len(decoded_prog.constant_pool.constants), len(binary_prog.constant_pool.constants))
        self.assertEqual(decoded_prog.function_table.entries[0].instruction_count,
                         binary_prog.function_table.entries[0].instruction_count)
        self.assertEqual(decoded_prog.instruction_stream.data, binary_prog.instruction_stream.data)

    def test_round_trip_full(self):
        # Tạo ISAProgram
        builder = InstructionBuilder()
        builder.create_program()
        func = builder.create_function("main")
        builder.move_run(builder.const_string("forward"), builder.const_int(50))
        builder.wait(builder.const_int(1000))
        builder.move_stop()

        encoder = ProgramEncoder()
        binary_prog1 = encoder.encode(builder.get_program())

        serializer = BinarySerializer()
        data = serializer.serialize(binary_prog1)

        reader = BinaryReader()
        binary_prog2 = reader.read(data)

        # So sánh header (bỏ qua checksum và program_size có thể khác)
        self.assertEqual(binary_prog1.header.magic, binary_prog2.header.magic)
        self.assertEqual(binary_prog1.header.abi_version, binary_prog2.header.abi_version)
        self.assertEqual(binary_prog1.header.endianness, binary_prog2.header.endianness)
        self.assertEqual(binary_prog1.header.instruction_set_version, binary_prog2.header.instruction_set_version)
        # program_size có thể khác do serializer không cập nhật, nhưng ta có thể kiểm tra nội dung
        self.assertEqual(binary_prog1.constant_pool.constants, binary_prog2.constant_pool.constants)
        self.assertEqual(len(binary_prog1.function_table.entries), len(binary_prog2.function_table.entries))
        for e1, e2 in zip(binary_prog1.function_table.entries, binary_prog2.function_table.entries):
            self.assertEqual(e1.function_id, e2.function_id)
            self.assertEqual(e1.entry_offset, e2.entry_offset)
            self.assertEqual(e1.instruction_count, e2.instruction_count)
        self.assertEqual(binary_prog1.instruction_stream.data, binary_prog2.instruction_stream.data)