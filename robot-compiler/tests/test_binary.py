import unittest
from compiler.binary import (
    BinaryHeader, Magic, Endianness,
    OperandEncoder, InstructionEncoder,
    ConstantPoolEncoder, ProgramEncoder,
    BinaryReader, BinaryPrinter
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
            # Trong test_operand_encoder_roundtrip
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

        encoder = ProgramEncoder()
        binary = encoder.encode(builder.get_program())

        reader = BinaryReader()
        decoded = reader.read(binary)

        self.assertEqual(len(decoded.functions), 1)
        self.assertEqual(decoded.functions[0].name, "main")