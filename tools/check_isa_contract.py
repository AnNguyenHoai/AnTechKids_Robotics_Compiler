#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
canonical=(root/'robot-language/generated/opcode.h').read_text()
fw=(root/'robot-platform/main/include/generated/opcode.h').read_text()
def entries(t): return dict(re.findall(r'^\s*(\w+)\s*=\s*(\d+),',t,re.M))
a,b=entries(canonical),entries(fw)
if a!=b:
    print('ISA OPCODE CONTRACT FAILED')
    print('missing:', sorted(set(a)-set(b)))
    print('extra:', sorted(set(b)-set(a)))
    sys.exit(1)
ins=(root/'robot-platform/main/src/Services/VM/Instruction.h').read_text()
if 'int16_t p4;' not in ins:
    print('INSTRUCTION ABI CONTRACT FAILED: firmware missing p4')
    sys.exit(1)
print('ISA CONTRACT OK: opcode map and 4-operand Instruction ABI are synchronized')
