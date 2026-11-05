#!/usr/bin/env python3
"""S8-B resource ABI boundary/firmware correspondence validation.

This checks the canonical contract, the firmware layout, and the exact
RoboSim reproduction. It does not claim the physical robot has 7 sensors.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))
sys.path.insert(0, str(ROOT / "robot-frontend-robosim"))
from compiler.safety_validator import validate_instructions, validate_program, _required_variable_indices
from compiler.compiler import RobotCompiler
from frontend import rewrite
from types import SimpleNamespace
from tempfile import TemporaryDirectory

resource = json.loads((ROOT / "packages/robot-isa/resource_contract.json").read_text(encoding="utf-8"))
max_program = resource["program"]["max_instructions"]
max_vars = resource["runtime"]["max_variables"]
assert (max_program, max_vars) == (512, 128)
program_h = (ROOT / "robot-platform/main/src/Services/VM/Program.h").read_text(encoding="utf-8")
vm_h = (ROOT / "robot-platform/main/src/Services/VM/VMContext.h").read_text(encoding="utf-8")
ins_h = (ROOT / "robot-platform/main/src/Services/VM/Instruction.h").read_text(encoding="utf-8")
loader = (ROOT / "robot-platform/main/src/Services/VM/ProgramLoader.cpp").read_text(encoding="utf-8")
assert re.search(r"MAX_PROGRAM_SIZE\s*=\s*512\s*;", program_h)
assert re.search(r"MAX_VARIABLE_COUNT\s*=\s*128\s*;", vm_h)
assert "uint16_t mProgramCounter;" in vm_h
assert "uint16_t mInstructionCount;" in program_h
assert "int32_t p1;" in ins_h and "int32_t p4;" in ins_h
assert "for (uint16_t i = 0; i < generatedProgramSize; i++)" in loader
assert "if (!program.AddInstruction(generatedProgram[i]))" in loader
assert "int32_t mVariables[MAX_VARIABLE_COUNT];" in vm_h
assert resource["runtime"]["max_call_stack"] == 8
assert resource["runtime"]["max_loop_depth"] == 8

def inst(op, a=0, b=0):
    return SimpleNamespace(opcode=op, p1=a, p2=b, p3=0, p4=0)

# Opcode 2 (LoadConst) uses p1 as a destination variable index.
assert not validate_instructions([inst(2, 127)] * 512)
assert any(v.rule == "program_overflow" for v in validate_instructions([inst(2, 0)] * 513))
assert any(v.rule == "invalid_variable" for v in validate_instructions([inst(2, 128)]))
# uint16 branch targets >255 must remain legal.
assert not validate_instructions([inst(14, 0, 300)] + [inst(2, 0)] * 300)

source = ROOT / "tests/v1_s8a/fixtures/user_line7_overflow.py"
with TemporaryDirectory() as temp:
    canonical = Path(temp) / "canonical.py"
    rewrite(source, canonical)
    program = RobotCompiler(target="esp32").compile(canonical)
count = len(program.instructions)
indices = set()
for instruction in program.instructions:
    indices.update(_required_variable_indices(
        int(instruction.opcode),
        (instruction.p1, instruction.p2, instruction.p3, instruction.p4),
    ))
span = max(indices) + 1 if indices else 0
print(f"S8-B USER LINE7: instructions={count}/{max_program}, variable_index_span={span}/{max_vars}")
assert count <= max_program and span <= max_vars, "program still exceeds S8-B resource limit"
violations = validate_program(program)
assert not [v for v in violations if v.rule in ("program_overflow", "invalid_variable", "invalid_jump")], violations

print("PASS S8-B canonical/firmware limits, bounds and original program resource gate")
print("PHYSICAL PENDING: runtime timing, 5-channel sensor projection, OTA and motor/Line5")
