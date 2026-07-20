from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.compiler import RoboSimCompiler
from compiler.generated.opcode import Opcode

EXAMPLES = ROOT / "examples"

compiler = RoboSimCompiler()

def assert_opcode(ins, expected_opcode_name):
    actual_name = Opcode(ins.opcode).name
    assert actual_name == expected_opcode_name, f"Expected {expected_opcode_name}, got {actual_name}"

# Test 1: robosim_demo.py
program = compiler.compile(EXAMPLES / "robosim_demo.py")
print()
print("Instruction Count:", len(program.instructions))
for i, ins in enumerate(program.instructions):
    print(i, ins)
print()
assert len(program.instructions) == 3
print("PASS")

# Test 2: robosim_wait.py
program = compiler.compile(EXAMPLES / "robosim_wait.py")
assert len(program.instructions) == 2
assert_opcode(program.instructions[0], "LoadConst")
assert_opcode(program.instructions[1], "Wait")
print("Test robosim_wait.py : PASS")

# Test 3: robosim_move_second.py
program = compiler.compile(EXAMPLES / "robosim_move_second.py")
assert len(program.instructions) == 5
print("Test robosim_move_second.py : PASS")

# Test 4: robosim_variable.py
program = compiler.compile(EXAMPLES / "robosim_variable.py")
assert len(program.instructions) == 3
assert_opcode(program.instructions[0], "LoadConst")
assert_opcode(program.instructions[1], "Forward")
assert_opcode(program.instructions[2], "Stop")
print("Test robosim_variable.py : PASS")

print("\nAll tests PASSED.")