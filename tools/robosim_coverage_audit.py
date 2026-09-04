"""C1 lightweight static coverage audit.

This intentionally reports source-level gaps; it does not claim hardware E2E.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "robot-compiler/compiler/generated/function_registry.py"
OP = ROOT / "robot-compiler/compiler/generated/opcode.py"
VM = ROOT / "robot-platform/main/src/Services/VM/VM.cpp"
TRANS = ROOT / "robot-frontend-robosim/frontend/transformer.py"

reg = REG.read_text()
op = OP.read_text()
vm = VM.read_text()
trans = TRANS.read_text()

registry = re.findall(r'^    "([^"]+)": \{', reg, re.M)
opcodes = dict(re.findall(r'^    (\w+) = (\d+)', op, re.M))
vm_cases = set(re.findall(r'case Opcode::(\w+)', vm))

print(f"Canonical registry functions: {len(registry)}")
print(f"Generated opcodes: {len(opcodes)}")
print(f"ESP32 VM dispatch cases: {len(vm_cases)}")
print("\nOpcodes defined but not dispatched by ESP32 VM:")
for name in opcodes:
    if name not in vm_cases and name not in {
        'Label', 'Nop'
    }:
        print(f"  - {name}")

print("\nRoboSim transformer contains direct rcu mappings:")
for name in sorted(set(re.findall(r'attr == [\"\']([^\"\']+)[\"\']', trans))):
    print(f"  - {name}")
