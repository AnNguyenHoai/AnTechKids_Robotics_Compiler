import unittest
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
    # 0: move_run forward 50
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_RUN, [ISAOperand.string("forward"), ISAOperand.integer(50)]))
    # 1: jump to index 3 (stop)
    func.add_instruction(ISAInstruction(RobotOpcode.JUMP, [ISAOperand.integer(3)]))
    # 2: move_run backward 30 (should be skipped)
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_RUN, [ISAOperand.string("backward"), ISAOperand.integer(30)]))
    # 3: stop
    func.add_instruction(ISAInstruction(RobotOpcode.MOVE_STOP, []))
    prog.add_function(func)
    return prog

def make_call_return_program():
    prog = ISAProgram()
    func1 = ISAFunction("main")
    # main: call function 1, then stop
    func1.add_instruction(ISAInstruction(RobotOpcode.CALL, [ISAOperand.integer(1)]))
    func1.add_instruction(ISAInstruction(RobotOpcode.MOVE_STOP, []))
    prog.add_function(func1)

    func2 = ISAFunction("sub")
    # sub: move_run forward 30, return
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
        self.assertEqual(len(vm.api.output), 2)
        self.assertEqual(vm.api.output[0], ("forward", 50))
        self.assertEqual(vm.api.output[1], ("stop",))

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
        # Only forward and stop should be executed, not backward
        self.assertEqual(len(vm.api.output), 2)
        self.assertEqual(vm.api.output[0], ("forward", 50))
        self.assertEqual(vm.api.output[1], ("stop",))

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
        # main: call sub, then stop. sub: forward 30.
        self.assertEqual(len(vm.api.output), 2)
        self.assertEqual(vm.api.output[0], ("forward", 30))
        self.assertEqual(vm.api.output[1], ("stop",))

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
        self.assertEqual(vm.api.output[0], ("forward", 50))
        vm.step()
        self.assertEqual(vm.api.output[1], ("stop",))
        vm.step()
        self.assertEqual(vm.state.value, "finished")

if __name__ == "__main__":
    unittest.main()