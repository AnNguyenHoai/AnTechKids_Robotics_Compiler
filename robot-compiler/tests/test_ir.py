import unittest
from compiler.ir import (
    IRProgram, IRFunction, IRBasicBlock, IRInstruction,
    IRValue, ValueKind, IRBuilder, IRPrinter, IROpcode
)
import io


class TestIR(unittest.TestCase):

    def test_value_creation(self):
        v = IRValue.integer(42)
        self.assertEqual(v.kind, ValueKind.INTEGER)
        self.assertEqual(v.as_integer(), 42)

        v = IRValue.float(3.14)
        self.assertEqual(v.kind, ValueKind.FLOAT)
        self.assertEqual(v.as_float(), 3.14)

        v = IRValue.boolean(True)
        self.assertEqual(v.kind, ValueKind.BOOLEAN)
        self.assertTrue(v.as_boolean())

        v = IRValue.string("hello")
        self.assertEqual(v.kind, ValueKind.STRING)
        self.assertEqual(v.as_string(), "hello")

        v = IRValue.variable("speed", 0)
        self.assertEqual(v.kind, ValueKind.VARIABLE)
        self.assertEqual(v.as_index(), 0)
        self.assertEqual(v.name, "speed")

        v = IRValue.temporary("t1", 1)
        self.assertEqual(v.kind, ValueKind.TEMPORARY)
        self.assertEqual(v.as_index(), 1)

    def test_instruction(self):
        ins = IRInstruction(IROpcode.MOVE_RUN, [IRValue.integer(50), IRValue.string("forward")])
        self.assertEqual(ins.opcode, IROpcode.MOVE_RUN)
        self.assertEqual(len(ins.operands), 2)
        ins.add_operand(IRValue.boolean(True))
        self.assertEqual(len(ins.operands), 3)

    def test_basic_block(self):
        block = IRBasicBlock("entry")
        self.assertEqual(block.label, "entry")
        self.assertTrue(block.is_empty())
        block.append(IRInstruction(IROpcode.MOVE_RUN))
        self.assertFalse(block.is_empty())
        self.assertEqual(block.size(), 1)

    def test_function(self):
        func = IRFunction("main")
        self.assertEqual(func.name, "main")
        self.assertEqual(len(func.blocks), 0)
        block = IRBasicBlock("entry")
        func.add_block(block)
        self.assertEqual(len(func.blocks), 1)
        self.assertIs(func.entry_block(), block)

    def test_program(self):
        prog = IRProgram(metadata={"version": "1.0"})
        self.assertEqual(len(prog.functions), 0)
        func = IRFunction("main")
        prog.add_function(func)
        self.assertEqual(len(prog.functions), 1)
        self.assertIs(prog.get_function("main"), func)
        self.assertIsNone(prog.get_function("missing"))

    def test_builder(self):
        builder = IRBuilder()
        prog = builder.create_program()
        func = builder.create_function("task1")
        block = builder.create_block("entry")
        builder.append_instruction(IROpcode.MOVE_RUN, [builder.const_int(50), builder.const_string("forward")])
        builder.append_instruction(IROpcode.WAIT, [builder.const_int(1000)])
        builder.append_instruction(IROpcode.MOVE_STOP)

        self.assertEqual(len(prog.functions), 1)
        self.assertEqual(len(block.instructions), 3)
        self.assertEqual(block.instructions[0].opcode, IROpcode.MOVE_RUN)
        self.assertEqual(block.instructions[0].operands[0].as_integer(), 50)

        # temporary
        t = builder.temp()
        self.assertIsInstance(t, IRValue)
        self.assertEqual(t.kind, ValueKind.TEMPORARY)

    def test_printer(self):
        builder = IRBuilder()
        prog = builder.create_program()
        func = builder.create_function("task1")
        block = builder.create_block("entry")
        builder.append_instruction(IROpcode.MOVE_RUN, [builder.const_int(50), builder.const_string("forward")])
        builder.append_instruction(IROpcode.WAIT, [builder.const_int(1000)])
        builder.append_instruction(IROpcode.MOVE_STOP)

        output = io.StringIO()
        IRPrinter.print(prog, output)
        printed = output.getvalue()

        self.assertIn("IRProgram", printed)
        self.assertIn("Function: task1", printed)
        self.assertIn("MOVE_RUN", printed)
        self.assertIn("50", printed)
        self.assertIn("forward", printed)
        self.assertIn("WAIT", printed)
        self.assertIn("1000", printed)
        self.assertIn("MOVE_STOP", printed)


if __name__ == "__main__":
    unittest.main()