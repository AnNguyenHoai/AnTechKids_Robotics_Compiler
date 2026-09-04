
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
FRONTEND_ROOT = ROOT / "robot-frontend-robosim"
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))
sys.path.insert(0, str(FRONTEND_ROOT))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode
from compiler.binary import ProgramEncoder
from compiler.isa import ISAInstruction, ISAOperand, ISAProgram, ISAFunction
from runtime import ProgramLoader, VirtualMachine
from runtime.hardware import MockHardware
from compiler.error import CompilerError
from frontend import rewrite


def to_isa(ins):
    opcode = Opcode(ins.opcode)
    ops = []
    if opcode == Opcode.LoadConst:
        ops = [ISAOperand.integer(ins.p1)]
        if isinstance(ins.p2, bool):
            # ProgramEncoder/loader currently represents booleans as integer
            # operands; runtime truthiness is preserved.
            ops.append(ISAOperand.integer(int(ins.p2)))
        elif isinstance(ins.p2, float):
            ops.append(ISAOperand.float(ins.p2))
        elif isinstance(ins.p2, str):
            ops.append(ISAOperand.string(ins.p2))
        else:
            ops.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.Forward, Opcode.Backward, Opcode.TurnLeft, Opcode.TurnRight, Opcode.Wait):
        ops = [ISAOperand.integer(ins.p1)]
    elif opcode == Opcode.Stop:
        pass
    elif opcode == Opcode.Jump:
        ops = [ISAOperand.integer(ins.p2)]
    elif opcode == Opcode.JumpIfFalse:
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode == Opcode.JumpIfTrue:
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode in (
        Opcode.Add, Opcode.Sub, Opcode.Mul, Opcode.Div, Opcode.Mod, Opcode.Pow,
        Opcode.CompareEQ, Opcode.CompareNE, Opcode.CompareLT,
        Opcode.CompareLE, Opcode.CompareGT, Opcode.CompareGE,
    ):
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2), ISAOperand.integer(ins.p3)]
    elif opcode == Opcode.Neg:
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p3)]
    elif opcode == Opcode.Store:
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode == Opcode.Set3CLed:
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode in (Opcode.SetMotorSpeed,):
        ops = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    else:
        raise AssertionError(f"Unsupported opcode in C4 helper: {opcode}")
    return ISAInstruction(opcode, ops)


def run_source(source, max_steps=1000):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = Path(f.name)
    try:
        rewrite_path = path.with_suffix(".rewrite.py")
        rewrite(path, rewrite_path)
        compiler = RobotCompiler()
        program = compiler.compile(rewrite_path)
        isa = ISAProgram()
        fn = ISAFunction("main")
        for ins in program.instructions:
            fn.add_instruction(to_isa(ins))
        isa.add_function(fn)
        binary = ProgramEncoder().encode(isa)
        runtime_program = ProgramLoader().load(binary)
        hardware = MockHardware()
        vm = VirtualMachine(hardware=hardware)
        vm.load(runtime_program)
        steps = 0
        while vm.get_state().value != "finished":
            vm.step()
            steps += 1
            if steps > max_steps:
                raise AssertionError("program did not terminate")
        return program, hardware
    finally:
        path.unlink(missing_ok=True)
        path.with_suffix(".rewrite.py").unlink(missing_ok=True)


class TestC4SemanticCoverage(unittest.TestCase):
    def test_variable_reassignment_preserves_slot(self):
        _, hw = run_source("""
import rcu
speed = 20
speed = speed + 30
rcu.SetMoveRun("forward", speed)
rcu.SetMoveStop()
""")
        self.assertEqual(hw.log, [
            ("set_motor", 50, 50),
            ("set_motor", 0, 0),
        ])

    def test_arithmetic_expression(self):
        _, hw = run_source("""
import rcu
speed = 10 * 4 + 5
rcu.SetMoveRun("forward", speed)
rcu.SetMoveStop()
""")
        self.assertEqual(hw.log[0], ("set_motor", 45, 45))

    def test_all_comparisons(self):
        comparisons = [
            ("<", 1, 2, True),
            ("<=", 2, 2, True),
            (">", 3, 2, True),
            (">=", 2, 2, True),
            ("==", 2, 2, True),
            ("!=", 2, 3, True),
        ]
        for op, left, right, expected in comparisons:
            _, hw = run_source(f"""
import rcu
a = {left}
b = {right}
if a {op} b:
    rcu.Set3CLed(1, 1)
else:
    rcu.Set3CLed(1, 0)
""")
            self.assertEqual(hw.led_state[1], int(expected), op)

    def test_if_elif_else_semantics(self):
        _, hw = run_source("""
import rcu
x = 15
if x > 20:
    rcu.Set3CLed(1, 1)
elif x > 10:
    rcu.Set3CLed(1, 2)
else:
    rcu.Set3CLed(1, 3)
""")
        self.assertEqual(hw.led_state[1], 2)

    def test_nested_if_semantics(self):
        _, hw = run_source("""
import rcu
a = 1
b = 2
if a < 2:
    if b > 1:
        rcu.Set3CLed(1, 1)
    else:
        rcu.Set3CLed(1, 2)
else:
    rcu.Set3CLed(1, 3)
""")
        self.assertEqual(hw.led_state[1], 1)

    def test_while_semantics(self):
        _, hw = run_source("""
import rcu
i = 0
while i < 3:
    rcu.Set3CLed(1, i)
    i = i + 1
""")
        self.assertEqual(hw.led_state[1], 2)

    def test_range_for_semantics(self):
        _, hw = run_source("""
import rcu
for i in range(3):
    rcu.Set3CLed(1, i)
""")
        self.assertEqual(hw.led_state[1], 2)

    def test_boolean_and_semantics(self):
        _, hw = run_source("""
import rcu
a = 1
b = 2
if a < 2 and b > 1:
    rcu.Set3CLed(1, 1)
else:
    rcu.Set3CLed(1, 0)
""")
        self.assertEqual(hw.led_state[1], 1)

    def test_zero_valued_operands_are_preserved(self):
        _, hw = run_source("""
import rcu
rcu.Set3CLed(1, 0)
""")
        self.assertEqual(hw.log, [("set_led", 1, 0)])

    def test_variable_to_api_argument(self):
        _, hw = run_source("""
import rcu
port = 1
state = 0
rcu.Set3CLed(port, state)
""")
        self.assertEqual(hw.log, [("set_led", 1, 0)])

    def test_expression_to_api_argument(self):
        _, hw = run_source("""
import rcu
state = 1 - 1
rcu.Set3CLed(1, state)
""")
        self.assertEqual(hw.log, [("set_led", 1, 0)])

    def test_function_call_before_definition(self):
        _, hw = run_source("""
import rcu
move_forward()
def move_forward():
    rcu.SetMoveRun("forward", 40)
    rcu.SetMoveStop()
""")
        self.assertEqual(hw.log, [
            ("set_motor", 40, 40),
            ("set_motor", 0, 0),
        ])

    def test_parameterized_function_is_rejected(self):
        source = """
def move(speed):
    return speed
move(40)
"""
        with self.assertRaises(CompilerError):
            run_source(source)

    def test_return_is_rejected_in_user_function(self):
        source = """
def move():
    rcu.SetMoveStop()
    return
move()
"""
        with self.assertRaises(CompilerError):
            run_source(source)


if __name__ == "__main__":
    unittest.main()
