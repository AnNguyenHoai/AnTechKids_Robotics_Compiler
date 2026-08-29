from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE = ROOT / "robot-language" / "generated"

# Destination for compiler
DEST_COMPILER = ROOT / "robot-compiler" / "compiler" / "generated"
DEST_COMPILER.mkdir(parents=True, exist_ok=True)

# Destination for platform (VM)
DEST_PLATFORM = ROOT / "robot-platform" / "main" / "include" / "generated"
DEST_PLATFORM.mkdir(parents=True, exist_ok=True)

# Destination for documentation
DEST_DOCS = ROOT / "robot-docs" / "generated"
DEST_DOCS.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("INSTALLING LANGUAGE ARTIFACTS")
print("=" * 60)

# ----- Copy Python artifacts to compiler -----
for file in SOURCE.glob("*.py"):
    print(f"Copy to compiler: {file.name}")
    shutil.copy2(file, DEST_COMPILER / file.name)

# ----- Copy C++ header to platform -----
opcode_h = SOURCE / "opcode.h"
if opcode_h.exists():
    print(f"Copy to platform: {opcode_h.name}")
    shutil.copy2(opcode_h, DEST_PLATFORM / opcode_h.name)

# ----- Copy JSON to platform -----
opcode_json = SOURCE / "opcode.json"
if opcode_json.exists():
    print(f"Copy to platform: {opcode_json.name}")
    shutil.copy2(opcode_json, DEST_PLATFORM / opcode_json.name)

# ----- Copy documentation -----
DOCS_SOURCE = ROOT / "robot-language" / "docs" / "generated"
if DOCS_SOURCE.exists():
    for file in DOCS_SOURCE.glob("*.md"):
        print(f"Copy to docs: {file.name}")
        shutil.copy2(file, DEST_DOCS / file.name)

# ----- Copy SDK to frontend -----
SDK_SOURCE = ROOT / "robot-language" / "robot"
DEST_FRONTEND_SDK = ROOT / "robot-frontend-robosim" / "robot"

if SDK_SOURCE.exists():
    if DEST_FRONTEND_SDK.exists():
        shutil.rmtree(DEST_FRONTEND_SDK)
    shutil.copytree(SDK_SOURCE, DEST_FRONTEND_SDK)
    print(f"Copied SDK to {DEST_FRONTEND_SDK}")
else:
    print("Warning: SDK source directory not found. Skipping SDK installation.")

print("=" * 60)
print("INSTALL COMPLETE")
print("=" * 60)