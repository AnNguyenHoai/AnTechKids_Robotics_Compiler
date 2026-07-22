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

# Đích cho tài liệu (docs)
DEST_DOCS = ROOT.parent / "robot-docs" / "generated"
DEST_DOCS.mkdir(parents=True, exist_ok=True)

# ----- Copy artifact cho compiler và platform -----
for file in SOURCE.glob("*.py"):
    print("Copy to compiler:", file.name)
    shutil.copy2(file, DEST_COMPILER / file.name)

opcode_h = SOURCE / "opcode.h"
if opcode_h.exists():
    print("Copy to platform:", opcode_h.name)
    shutil.copy2(opcode_h, DEST_PLATFORM / opcode_h.name)

opcode_json = SOURCE / "opcode.json"
if opcode_json.exists():
    print("Copy to platform:", opcode_json.name)
    shutil.copy2(opcode_json, DEST_PLATFORM / opcode_json.name)

# Copy tài liệu đã sinh từ docs/generated (trong robot-language) sang robot-docs/generated
DOCS_SOURCE = ROOT / "docs" / "generated"
if DOCS_SOURCE.exists():
    for file in DOCS_SOURCE.glob("*.md"):
        print("Copy to docs:", file.name)
        shutil.copy2(file, DEST_DOCS / file.name)

# ----- Copy SDK (Standard Robot API) sang frontend -----
SDK_SOURCE = ROOT / "robot"
DEST_FRONTEND_SDK = ROOT.parent / "robot-frontend-robosim" / "robot"

if SDK_SOURCE.exists():
    # Xóa thư mục đích cũ nếu có
    if DEST_FRONTEND_SDK.exists():
        shutil.rmtree(DEST_FRONTEND_SDK)
    # Copy toàn bộ thư mục robot/
    shutil.copytree(SDK_SOURCE, DEST_FRONTEND_SDK)
    print(f"Copied SDK to {DEST_FRONTEND_SDK}")
else:
    print("Warning: SDK source directory not found. Skipping SDK installation.")

print("Artifacts installed.")