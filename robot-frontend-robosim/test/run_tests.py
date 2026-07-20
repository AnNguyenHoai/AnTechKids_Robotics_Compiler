from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.compiler import RoboSimCompiler

EXAMPLES = ROOT / "examples"

compiler = RoboSimCompiler()

program = compiler.compile(
    EXAMPLES / "robosim_demo.py"
)

print()

print("Instruction Count:", len(program.instructions))

for i, ins in enumerate(program.instructions):

    print(i, ins)

print()

assert len(program.instructions) == 3

print("PASS")

program = compiler.compile(
    EXAMPLES / "robosim_wait.py"
)

assert len(program.instructions) == 2

assert program.instructions[0].opcode == \
    compiler.compiler.opcodes.get("LoadConst")

assert program.instructions[1].opcode == \
    compiler.compiler.opcodes.get("Wait")

print("Test robosim_wait.py : PASS")


program = compiler.compile(
    EXAMPLES / "robosim_move_second.py"
)

assert len(program.instructions) == 5

print("Test robosim_move_second.py : PASS")


program = compiler.compile(
    EXAMPLES / "robosim_variable.py"
)

assert len(program.instructions) == 3

assert program.instructions[0].opcode == \
    compiler.compiler.opcodes.get("LoadConst")

assert program.instructions[1].opcode == \
    compiler.compiler.opcodes.get("Forward")

assert program.instructions[2].opcode == \
    compiler.compiler.opcodes.get("Stop")

print("Test robosim_variable.py : PASS")