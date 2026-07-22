import unittest
import io
from compiler.isa import (
    RobotOpcode, ISAOperand, OperandKind, ISAInstruction,
    ISAFunction, ISAProgram, InstructionBuilder, InstructionPrinter
)


class TestISA(unittest.TestCase):

    def test_opcode_enum(self):
        self.assertEqual(RobotOpcode.MOVE_RUN.name, "MOVE_RUN")
        self.assertEqual(RobotOpcode.WAIT.name, "WAIT")
        self.assertEqual(len(RobotOpcode), 12)  # Count all opcodes

    def test_operand_creation(self):
        int_op = ISAOperand.integer(42)
        self.assertEqual(int_op.kind, OperandKind.INTEGER)
        self.assertEqual(int_op.as_integer(), 42)

        float_op = ISAOperand.float(3.14)
        self.assertEqual(float_op.kind, OperandKind.FLOAT)
        self.assertEqual(float_op.as_float(), 3.14)

        string_op = ISAOperand.string("forward")
        self.assertEqual(string_op.kind, OperandKind.STRING)
        self.assertEqual(string_op.as_string(), "forward")

        reg_op = ISAOperand.register(0)
        self.assertEqual(reg_op.kind, OperandKind.REGISTER)
        self.assertEqual(reg_op.as_index(), 0)

        label_op = ISAOperand.label(1)
        self.assertEqual(label_op.kind, OperandKind.LABEL)
        self.assertEqual(label_op.as_index(), 1)

    def test_instruction(self):
        ins = ISAInstruction(RobotOpcode.MOVE_RUN, [
            ISAOperand.string("forward"),
            ISAOperand.integer(50)
        ])
        self.assertEqual(ins.opcode, RobotOpcode.MOVE_RUN)
        self.assertEqual(ins.operand_count, 2)
        self.assertEqual(ins.operands[0].as_string(), "forward")

    def test_function(self):
        func = ISAFunction("main", "entry")
        self.assertEqual(func.name, "main")
        self.assertEqual(func.entry_label, "entry")
        self.assertEqual(func.size, 0)

        func.add_instruction(ISAInstruction(RobotOpcode.MOVE_STOP))
        self.assertEqual(func.size, 1)
        func.add_label("loop", 0)
        self.assertTrue(func.has_label("loop"))
        self.assertEqual(func.get_label_index("loop"), 0)

    def test_program(self):
        prog = ISAProgram()
        func = ISAFunction("main")
        prog.add_function(func)
        self.assertEqual(prog.function_count, 1)
        self.assertIs(prog.get_function("main"), func)

    def test_builder(self):
        builder = InstructionBuilder()
        prog = builder.create_program()
        func = builder.create_function("main")
        builder.move_run(
            builder.const_string("forward"),
            builder.const_int(50)
        )
        builder.wait(builder.const_int(1000))
        builder.move_stop()

        self.assertEqual(func.size, 3)
        self.assertEqual(func.instructions[0].opcode, RobotOpcode.MOVE_RUN)

    def test_printer(self):
        builder = InstructionBuilder()
        builder.create_program()
        func = builder.create_function("main")
        builder.move_run(builder.const_string("forward"), builder.const_int(50))
        builder.wait(builder.const_int(1000))
        builder.move_stop()

        output = io.StringIO()
        InstructionPrinter.print(builder.get_program(), output)
        printed = output.getvalue()

        self.assertIn("Function: main", printed)
        self.assertIn("MOVE_RUN", printed)
        self.assertIn("forward", printed)
        self.assertIn("50", printed)
        self.assertIn("WAIT", printed)
        self.assertIn("1000", printed)
        self.assertIn("MOVE_STOP", printed)


if __name__ == "__main__":
    unittest.main()