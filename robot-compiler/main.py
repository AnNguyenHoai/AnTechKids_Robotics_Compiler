from pathlib import Path

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter


ROOT = Path(__file__).resolve().parent

demo_file = ROOT / "examples" / "demo.py"

output_file = (
    ROOT.parent
    / "robot-platform"
    / "main"
    / "src"
    / "Application"
    / "generated_program.h"
)

compiler = RobotCompiler()

program = compiler.compile(demo_file)

HeaderEmitter(
    compiler.opcodes
).emit(
    program,
    output_file
)

print("Generate successfully!")