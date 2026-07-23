import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "robot-compiler"))

from compiler.binary import ProgramEncoder
from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, RobotOpcode, ISAOperand
from runtime import ProgramLoader, VirtualMachine

def make_move_stop_program():
    prog = ISAProgram()
    func = ISAFunction("main")
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_RUN, [ISAOperand.string("forward"), ISAOperand.integer(50)]))
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_STOP, []))
    prog.add_function(func)
    return prog

def make_jump_program():
    prog = ISAProgram()
    func = ISAFunction("main")
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_RUN, [ISAOperand.string("forward"), ISAOperand.integer(50)]))
    func.add_instruction(ISAInstruction(RobotOpcode.JUMP, [ISAOperand.integer(3)]))
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_RUN, [ISAOperand.string("backward"), ISAOperand.integer(30)]))
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_STOP, []))
    prog.add_function(func)
    return prog

def make_call_return_program():
    prog = ISAProgram()
    func1 = ISAFunction("main")
    func1.add_instruction(ISAInstruction(RobotOpcode.CALL, [ISAOperand.integer(1)]))
    func1.add_instruction(ISAInstruction(RobotOpcode.MOVE_STOP, []))
    prog.add_function(func1)

    func2 = ISAFunction("sub")
    func2.add_instruction(ISAInstruction(RobotOpcode.MOVE_RUN, [ISAOperand.string("forward"), ISAOperand.integer(30)]))
    func2.add_instruction(ISAInstruction(RobotOpcode.RETURN, []))
    prog.add_function(func2)
    return prog

class TestVM(unittest.TestCase):
    def test_move_stop(self):
        isa_prog = make_move_stop_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm = VirtualMachine()
        vm.load(runtime_prog)
        vm.run()

        self.assertEqual(vm.state.value, "finished")
        log = vm.robot.hardware.log
        self.assertEqual(log[0], ("set_motor", 50, 50))
        self.assertEqual(log[1], ("set_motor", 0, 0))

    def test_jump(self):
        isa_prog = make_jump_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm = VirtualMachine()
        vm.load(runtime_prog)
        vm.run()

        self.assertEqual(vm.state.value, "finished")
        log = vm.robot.hardware.log
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0], ("set_motor", 50, 50))
        self.assertEqual(log[1], ("set_motor", 0, 0))

    def test_call_return(self):
        isa_prog = make_call_return_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm = VirtualMachine()
        vm.load(runtime_prog)
        vm.run()

        self.assertEqual(vm.state.value, "finished")
        log = vm.robot.hardware.log
        self.assertEqual(log[0], ("set_motor", 30, 30))
        self.assertEqual(log[1], ("set_motor", 0, 0))

    def test_step_execution(self):
        isa_prog = make_move_stop_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm = VirtualMachine()
        vm.load(runtime_prog)

        self.assertEqual(vm.get_state().value, "loaded")
        vm.step()
        log = vm.robot.hardware.log
        self.assertEqual(log[-1], ("set_motor", 50, 50))
        vm.step()
        self.assertEqual(log[-1], ("set_motor", 0, 0))
        vm.step()
        self.assertEqual(vm.state.value, "finished")

if __name__ == "__main__":
    unittest.main()