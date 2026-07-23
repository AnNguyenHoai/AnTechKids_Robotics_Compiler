import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unittest
from compiler.binary import ProgramEncoder
from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, ISAOperand
from compiler.generated.opcode import Opcode
from runtime import ProgramLoader, VirtualMachine

def make_arithmetic_program():
    prog = ISAProgram()
    func = ISAFunction("main")
    func.add_instruction(ISAInstruction(Opcode.LoadConst, [ISAOperand.integer(0), ISAOperand.integer(5)]))
    func.add_instruction(ISAInstruction(Opcode.LoadConst, [ISAOperand.integer(1), ISAOperand.integer(3)]))
    func.add_instruction(ISAInstruction(Opcode.Add, [ISAOperand.integer(0), ISAOperand.integer(1), ISAOperand.integer(2)]))
    func.add_instruction(ISAInstruction(Opcode.Forward, [ISAOperand.integer(2)]))
    func.add_instruction(ISAInstruction(Opcode.Stop, []))
    prog.add_function(func)
    return prog

class TestEngine(unittest.TestCase):
    def test_arithmetic(self):
        isa_prog = make_arithmetic_program()
        encoder = ProgramEncoder()
        binary = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime = loader.load(binary)
        vm = VirtualMachine()
        vm.load(runtime)
        vm.run()
        log = vm.robot.hardware.log
        self.assertEqual(log[0], ("set_motor", 8, 8))
        self.assertEqual(log[1], ("set_motor", 0, 0))

if __name__ == "__main__":
    unittest.main()