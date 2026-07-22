import unittest
import io
from compiler.ir import (
    IRProgram, IRFunction, IRBasicBlock, IRInstruction,
    IRValue, IROpcode
)
from compiler.isa import BackendLowering, InstructionPrinter, InstructionBuilder
from compiler.passes import PassContext, PassManager
from compiler.diagnostics import DiagnosticEngine


class TestBackend(unittest.TestCase):

    def test_lower_move_run(self):
        # Build IR program
        ir_prog = IRProgram()
        ir_func = IRFunction("main")
        block = IRBasicBlock("entry")
        block.append(IRInstruction(
            IROpcode.MOVE_RUN,
            [IRValue.string("forward"), IRValue.integer(50)]
        ))
        block.append(IRInstruction(IROpcode.MOVE_STOP))
        ir_func.add_block(block)
        ir_prog.add_function(ir_func)

        # Lower to ISA
        lower = BackendLowering()
        isa_prog = lower.lower(ir_prog)

        self.assertEqual(isa_prog.function_count, 1)
        isa_func = isa_prog.functions[0]
        self.assertEqual(isa_func.size, 2)
        self.assertEqual(isa_func.instructions[0].opcode.name, "MOVE_RUN")
        self.assertEqual(isa_func.instructions[0].operands[0].as_string(), "forward")
        self.assertEqual(isa_func.instructions[0].operands[1].as_integer(), 50)

    def test_lower_wait(self):
        ir_prog = IRProgram()
        ir_func = IRFunction("main")
        block = IRBasicBlock("entry")
        block.append(IRInstruction(
            IROpcode.WAIT,
            [IRValue.integer(1000)]
        ))
        ir_func.add_block(block)
        ir_prog.add_function(ir_func)

        lower = BackendLowering()
        isa_prog = lower.lower(ir_prog)

        isa_func = isa_prog.functions[0]
        self.assertEqual(isa_func.instructions[0].opcode.name, "WAIT")
        self.assertEqual(isa_func.instructions[0].operands[0].as_integer(), 1000)

    def test_lower_multi_block(self):
        ir_prog = IRProgram()
        ir_func = IRFunction("main")
        block1 = IRBasicBlock("start")
        block1.append(IRInstruction(IROpcode.MOVE_RUN, [IRValue.string("forward"), IRValue.integer(50)]))
        block1.append(IRInstruction(IROpcode.JUMP_IF_FALSE, [IRValue.integer(1), IRValue.integer(0)]))
        block2 = IRBasicBlock("end")
        block2.append(IRInstruction(IROpcode.MOVE_STOP))
        ir_func.add_block(block1)
        ir_func.add_block(block2)
        ir_prog.add_function(ir_func)

        lower = BackendLowering()
        isa_prog = lower.lower(ir_prog)

        isa_func = isa_prog.functions[0]
        # Each block should have a label
        self.assertGreater(isa_func.size, 0)

    def test_lower_with_pass_manager(self):
        ir_prog = IRProgram()
        ir_func = IRFunction("main")
        block = IRBasicBlock("entry")
        block.append(IRInstruction(
            IROpcode.MOVE_RUN,
            [IRValue.string("forward"), IRValue.integer(80)]
        ))
        block.append(IRInstruction(IROpcode.WAIT, [IRValue.integer(2000)]))
        block.append(IRInstruction(IROpcode.MOVE_STOP))
        ir_func.add_block(block)
        ir_prog.add_function(ir_func)

        diag = DiagnosticEngine()
        context = PassContext(ir_prog, diag)
        manager = PassManager()
        manager.register(BackendLowering())
        result = manager.run(context)

        self.assertTrue(result.success)
        self.assertIn("isa_program", context.config)
        isa_prog = context.config["isa_program"]
        isa_func = isa_prog.functions[0]
        self.assertEqual(isa_func.size, 3)


if __name__ == "__main__":
    unittest.main()