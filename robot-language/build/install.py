from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "generated"

# Đích cho compiler
DEST_COMPILER = ROOT.parent / "robot-compiler" / "compiler" / "generated"
DEST_COMPILER.mkdir(parents=True, exist_ok=True)

# Đích cho platform (VM)
DEST_PLATFORM = ROOT.parent / "robot-platform" / "main" / "include" / "generated"
DEST_PLATFORM.mkdir(parents=True, exist_ok=True)

# Copy các file .py sang compiler
for file in SOURCE.glob("*.py"):
    print("Copy to compiler:", file.name)
    shutil.copy2(file, DEST_COMPILER / file.name)

# Copy opcode.h và opcode.json sang platform
opcode_h = SOURCE / "opcode.h"
if opcode_h.exists():
    print("Copy to platform:", opcode_h.name)
    shutil.copy2(opcode_h, DEST_PLATFORM / opcode_h.name)

opcode_json = SOURCE / "opcode.json"
if opcode_json.exists():
    print("Copy to platform:", opcode_json.name)
    shutil.copy2(opcode_json, DEST_PLATFORM / opcode_json.name)

print("Artifacts installed.")