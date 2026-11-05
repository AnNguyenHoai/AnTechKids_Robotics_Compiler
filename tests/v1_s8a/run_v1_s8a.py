#!/usr/bin/env python3
"""S8-A: report exact resource use and guard short-circuit / scratch-slot lowering."""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))
sys.path.insert(0, str(ROOT / "robot-frontend-robosim"))
from frontend import rewrite
from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode
from compiler.safety_validator import validate_program, _required_variable_indices

def compile_robosim(source: str):
    with tempfile.TemporaryDirectory() as directory:
        raw = Path(directory) / "input.py"
        canonical = Path(directory) / "canonical.py"
        raw.write_text(source, encoding="utf-8")
        rewrite(raw, canonical)
        return RobotCompiler().compile(canonical)

def footprint(program):
    used = set()
    for ins in program.instructions:
        used.update(_required_variable_indices(int(ins.opcode), (ins.p1, ins.p2, ins.p3, ins.p4)))
    return len(program.instructions), (max(used) + 1 if used else 0)

example = (ROOT / "tests/v1_s8a/fixtures/user_line7_overflow.py").read_text(encoding="utf-8")
program = compile_robosim(example)
instructions, variables = footprint(program)
violations = validate_program(program)
from compiler.safety_validator import load_resource_contract
limits = load_resource_contract()
instruction_limit = limits["program"]["max_instructions"]
variable_limit = limits["runtime"]["max_variables"]
print(f"S8-A USER LINE7: instructions={instructions}/{instruction_limit}; variable_index_span={variables}/{variable_limit}")
print("S8-A violations:", [(v.rule, v.message) for v in violations][:8])
# Baseline from actual reported failing program: 182 instructions, 106+ indices.
assert instructions < 182, "direct condition branch lowering should reduce instructions"
assert variables < 106, "scratch-slot reuse should reduce variable index span"

# A statement-level boolean value must still be materialized as 0 or 1.
value = compile_robosim("import rcu\na = 1\nb = 0\nc = a and b\n")
assert any(ins.opcode == Opcode.LoadConst.value and ins.p2 == 0 for ins in value.instructions)
assert any(ins.opcode == Opcode.LoadConst.value and ins.p2 == 1 for ins in value.instructions)

# Conditional AND: RHS sensor call must appear only after first branch guard.
and_program = compile_robosim(
    "import rcu\na = 0\nif a and rcu.GetTouch(1):\n    rcu.SetMoveStop()\n"
)
ops = [ins.opcode for ins in and_program.instructions]
assert Opcode.JumpIfFalse.value in ops
assert Opcode.ReadTouch.value in ops
first_guard = next(i for i, ins in enumerate(and_program.instructions)
                   if ins.opcode == Opcode.JumpIfFalse.value)
read_index = ops.index(Opcode.ReadTouch.value)
assert first_guard < read_index < and_program.instructions[first_guard].p2, "AND must skip RHS when LHS false"

# Loop jump targets remain within program bounds.
for name, source in [
    ("nested", "import rcu\na=1\nb=2\nwhile a:\n    if a and (not b):\n        rcu.SetMoveStop()\n    else:\n        rcu.SetWaitForTime(0.02)\n"),
    ("or", "import rcu\na=1\nif a or rcu.GetTouch(1):\n    rcu.SetMoveStop()\n"),
]:
    p = compile_robosim(source)
    assert not [v for v in validate_program(p) if v.rule in ("invalid_jump", "invalid_variable")], name

print("PASS S8-A compiler optimization contract and representative short-circuit checks")
