import unittest
import sys
import time
import threading
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
COMPILER_ROOT = REPO_ROOT / "robot-compiler"
FRONTEND_ROOT = REPO_ROOT / "robot-frontend-robosim"

if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from frontend import rewrite
from compiler.compiler import RobotCompiler
from compiler.binary import ProgramEncoder
from runtime import ProgramLoader, VirtualMachine
from runtime.hardware import MockHardware
from compiler.generated.opcode import Opcode
from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, ISAOperand

PROGRAMS_DIR = Path(__file__).parent / "programs"

def compile_robosim(source_path):
    """Rewrite and compile a RoboSim source file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rewrite.py', delete=False) as tmp:
        rewrite_path = Path(tmp.name)
    try:
        rewrite(source_path, rewrite_path)
        compiler = RobotCompiler()
        program = compiler.compile(rewrite_path)
        return program
    finally:
        rewrite_path.unlink(missing_ok=True)

# Hàm chuyển đổi Instruction sang ISA (giữ nguyên)
def convert_instruction(ins):
    opcode = Opcode(ins.opcode)
    operands = []
    if opcode == Opcode.LoadConst:
        operands.append(ISAOperand.integer(ins.p1))
        if isinstance(ins.p2, float):
            operands.append(ISAOperand.float(ins.p2))
        else:
            operands.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.Forward, Opcode.Backward, Opcode.TurnLeft, Opcode.TurnRight, Opcode.Wait):
        operands.append(ISAOperand.integer(ins.p1))
    elif opcode == Opcode.Stop:
        pass
    elif opcode == Opcode.Jump:
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.JumpIfFalse, Opcode.JumpIfTrue):
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.Add, Opcode.Sub, Opcode.Mul, Opcode.Div, Opcode.Mod, Opcode.Pow):
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
        operands.append(ISAOperand.integer(ins.p3))
    elif opcode == Opcode.Neg:
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p3))
    elif opcode == Opcode.Store:
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode == Opcode.Call:
        operands.append(ISAOperand.integer(ins.p1))
    elif opcode == Opcode.Return:
        pass
    elif opcode in (Opcode.CompareEQ, Opcode.CompareNE, Opcode.CompareLT, 
                    Opcode.CompareLE, Opcode.CompareGT, Opcode.CompareGE):
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
        operands.append(ISAOperand.integer(ins.p3))
    elif opcode == Opcode.Label:
        pass
    else:
        if ins.p1 != 0: operands.append(ISAOperand.integer(ins.p1))
        if ins.p2 != 0: operands.append(ISAOperand.integer(ins.p2))
        if ins.p3 != 0: operands.append(ISAOperand.integer(ins.p3))
    return ISAInstruction(opcode, operands)

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        pass  # không còn compiler instance

    def _run_program(self, program_path, expected_motor_commands, timeout=30):
        program = compile_robosim(program_path)
        self.assertIsNotNone(program)

        # In debug
        print(f"\n--- Instructions for {program_path.name} ---")
        for i, ins in enumerate(program.instructions):
            op_name = Opcode(ins.opcode).name
            print(f"{i}: {op_name} p1={ins.p1} p2={ins.p2} p3={ins.p3}")
        print("--- End instructions ---\n")

        isa_prog = ISAProgram()
        func = ISAFunction("main")
        for ins in program.instructions:
            func.add_instruction(convert_instruction(ins))
        isa_prog.add_function(func)

        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)

        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        hardware = MockHardware()
        vm = VirtualMachine(hardware=hardware)
        vm.load(runtime_prog)

        result = {"done": False, "error": None}
        def run_vm():
            try:
                vm.run()
                result["done"] = True
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(target=run_vm)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            vm.stop()
            thread.join(1)
            self.fail("Execution timed out")
        if result["error"]:
            raise result["error"]

        self.assertEqual(vm.state.value, "finished")
        motor_commands = []
        for item in hardware.log:
            if len(item) >= 3 and item[0] == "set_motor":
                motor_commands.append((item[1], item[2]))
        self.assertEqual(len(motor_commands), len(expected_motor_commands))
        for i, (left, right) in enumerate(expected_motor_commands):
            self.assertEqual(motor_commands[i][0], left)
            self.assertEqual(motor_commands[i][1], right)

    # Các test cases
    def test_demo_forward(self):
        self._run_program(PROGRAMS_DIR / "demo_forward.py", [(80,80), (0,0)])

    def test_demo_backward(self):
        self._run_program(PROGRAMS_DIR / "demo_backward.py", [(-50,-50), (0,0)])

    def test_demo_turn(self):
        self._run_program(PROGRAMS_DIR / "demo_turn.py", [(-60,60), (0,0), (60,-60), (0,0)])

    def test_demo_variable(self):
        self._run_program(PROGRAMS_DIR / "demo_variable.py", [(60,60), (0,0)])

    def test_demo_if(self):
        self._run_program(PROGRAMS_DIR / "demo_if.py", [(80,80), (0,0)])

    def test_demo_loop(self):
        self._run_program(PROGRAMS_DIR / "demo_loop.py", [(70,70), (0,0)])

    def test_demo_function(self):
        self._run_program(PROGRAMS_DIR / "demo_function.py", [(80,80), (0,0)])

    def test_demo_wait(self):
        source = """import rcu
rcu.SetWaitForTime(0.1)
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(source)
            path = Path(f.name)
        try:
            program = compile_robosim(path)
            isa_prog = ISAProgram()
            func = ISAFunction("main")
            for ins in program.instructions:
                func.add_instruction(convert_instruction(ins))
            isa_prog.add_function(func)

            encoder = ProgramEncoder()
            binary_prog = encoder.encode(isa_prog)
            loader = ProgramLoader()
            runtime_prog = loader.load(binary_prog)
            hardware = MockHardware()
            vm = VirtualMachine(hardware=hardware)
            vm.load(runtime_prog)

            result = {"done": False, "error": None}
            def run_vm():
                try:
                    vm.run()
                    result["done"] = True
                except Exception as e:
                    result["error"] = e

            thread = threading.Thread(target=run_vm)
            thread.start()
            thread.join(10)
            if thread.is_alive():
                vm.stop()
                thread.join(1)
                self.fail("Wait test timed out")
            if result["error"]:
                raise result["error"]

            self.assertEqual(vm.state.value, "finished")
            motor_commands = []
            for item in hardware.log:
                if len(item) >= 3 and item[0] == "set_motor":
                    motor_commands.append((item[1], item[2]))
            self.assertEqual(len(motor_commands), 0)
        finally:
            path.unlink(missing_ok=True)

if __name__ == "__main__":
    unittest.main()