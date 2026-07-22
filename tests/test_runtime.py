# tests/test_runtime.py
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Thêm robot-compiler vào sys.path
sys.path.insert(0, str(ROOT / "robot-compiler"))

from compiler.binary import ProgramEncoder, BinaryHeader, ConstantPool, FunctionTable, InstructionStream, BinaryProgram
from compiler.isa import InstructionBuilder, RobotOpcode
from runtime import ProgramLoader, RuntimeProgram
from runtime.exceptions import InvalidBinaryException, UnsupportedVersionException
from runtime.iterator import InstructionIterator


class TestRuntime(unittest.TestCase):
    def test_load_program(self):
        builder = InstructionBuilder()
        builder.create_program()
        func = builder.create_function("main")
        builder.move_run(builder.const_string("forward"), builder.const_int(50))
        builder.wait(builder.const_int(1000))
        builder.move_stop()

        encoder = ProgramEncoder()
        binary_prog = encoder.encode(builder.get_program())
        runtime_prog = ProgramLoader.load(binary_prog)

        self.assertIsInstance(runtime_prog, RuntimeProgram)
        self.assertEqual(len(runtime_prog.instructions), 3)
        self.assertEqual(len(runtime_prog.functions), 1)
        self.assertEqual(len(runtime_prog.constants), 1)

        func0 = runtime_prog.functions[0]
        self.assertEqual(func0.instruction_count, 3)
        self.assertEqual(func0.function_id, 0)

        ins0 = runtime_prog.instructions[0]
        self.assertEqual(ins0.opcode, RobotOpcode.MOVE_RUN)
        self.assertEqual(ins0.operands[0], "forward")
        self.assertEqual(ins0.operands[1], 50)

        it = InstructionIterator(runtime_prog, function_id=0)
        self.assertTrue(it.has_next())
        ins = it.next()
        self.assertEqual(ins.opcode, RobotOpcode.MOVE_RUN)
        ins = it.next()
        self.assertEqual(ins.opcode, RobotOpcode.WAIT)
        ins = it.next()
        self.assertEqual(ins.opcode, RobotOpcode.MOVE_STOP)
        self.assertFalse(it.has_next())

    def test_invalid_magic(self):
        header = BinaryHeader(magic=0x12345678, abi_version=1)
        cp = ConstantPool([])
        ft = FunctionTable([])
        inst = InstructionStream(b"")
        binary_prog = BinaryProgram(header, cp, ft, inst)
        with self.assertRaises(InvalidBinaryException):
            ProgramLoader.load(binary_prog)

    def test_unsupported_version(self):
        header = BinaryHeader(magic=0x4E494252, abi_version=99)
        cp = ConstantPool([])
        ft = FunctionTable([])
        inst = InstructionStream(b"")
        binary_prog = BinaryProgram(header, cp, ft, inst)
        with self.assertRaises(UnsupportedVersionException):
            ProgramLoader.load(binary_prog)

    def test_constant_pool_access(self):
        builder = InstructionBuilder()
        builder.create_program()
        builder.create_function("main")
        builder.move_run(builder.const_string("backward"), builder.const_int(30))
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(builder.get_program())
        runtime_prog = ProgramLoader.load(binary_prog)
        self.assertEqual(len(runtime_prog.constants), 1)
        self.assertEqual(runtime_prog.constants[0], "backward")


if __name__ == "__main__":
    unittest.main()