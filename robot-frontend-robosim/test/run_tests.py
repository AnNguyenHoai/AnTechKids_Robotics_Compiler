from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.compiler import RoboSimCompiler
from compiler.generated.opcode import Opcode

EXAMPLES = ROOT / "examples"
compiler = RoboSimCompiler()

# ---- Test 1: robosim_demo.py ----
program = compiler.compile(EXAMPLES / "robosim_demo.py")
print("\nInstruction Count:", len(program.instructions))
for i, ins in enumerate(program.instructions):
    print(i, f"Opcode: {Opcode(ins.opcode).name}, p1={ins.p1}, p2={ins.p2}, p3={ins.p3}")
print()
assert len(program.instructions) == 5
assert program.instructions[0].opcode == Opcode.LoadConst.value
assert program.instructions[0].p1 == 0 and program.instructions[0].p2 == 80
assert program.instructions[1].opcode == Opcode.Forward.value
assert program.instructions[1].p1 == 0
assert program.instructions[2].opcode == Opcode.LoadConst.value
assert program.instructions[2].p1 == 1 and program.instructions[2].p2 == 1000
assert program.instructions[3].opcode == Opcode.Wait.value
assert program.instructions[3].p1 == 1
assert program.instructions[4].opcode == Opcode.Stop.value
print("Test robosim_demo.py : PASS")

# ---- Test 2: robosim_wait.py ----
program = compiler.compile(EXAMPLES / "robosim_wait.py")
assert len(program.instructions) == 2
assert program.instructions[0].opcode == Opcode.LoadConst.value
assert program.instructions[1].opcode == Opcode.Wait.value
print("Test robosim_wait.py : PASS")

# ---- Test 3: robosim_move_second.py ----
program = compiler.compile(EXAMPLES / "robosim_move_second.py")
print("\nrobosim_move_second.py instructions:")
for i, ins in enumerate(program.instructions):
    print(i, f"Opcode: {Opcode(ins.opcode).name}, p1={ins.p1}, p2={ins.p2}, p3={ins.p3}")
print()
assert len(program.instructions) == 7
# Có thể kiểm tra thêm giá trị của Mul
assert program.instructions[4].opcode == Opcode.Mul.value
assert program.instructions[4].p1 == 1
assert program.instructions[4].p2 == 2
assert program.instructions[4].p3 == 3
print("Test robosim_move_second.py : PASS")
# ---- Test 4: robosim_variable.py ----
program = compiler.compile(EXAMPLES / "robosim_variable.py")
assert len(program.instructions) == 3
assert program.instructions[0].opcode == Opcode.LoadConst.value
assert program.instructions[1].opcode == Opcode.Forward.value
assert program.instructions[2].opcode == Opcode.Stop.value
print("Test robosim_variable.py : PASS")