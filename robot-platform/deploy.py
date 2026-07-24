#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPILER = ROOT / "robot-compiler" / "main.py"

# File nguồn mẫu: chứa chương trình robot (ví dụ forward(50); wait(1000); stop())
SOURCE_FILE = ROOT / "robot-platform" / "deploy_program.py"

# Đầu ra header
OUTPUT_HEADER = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"

def main():
    # 1. Kiểm tra file nguồn
    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        print("Please create deploy_program.py with your robot code.")
        sys.exit(1)

    # 2. Biên dịch sang header
    print("🛠️  Compiling robot program...")
    cmd = [sys.executable, str(COMPILER), "--file", str(SOURCE_FILE), "--output", str(OUTPUT_HEADER)]
    try:
        subprocess.check_call(cmd)
        print("✅ Compilation successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Compilation failed: {e}")
        sys.exit(1)

    # 3. Build firmware (PlatformIO)
    print("🔨 Building firmware...")
    try:
        subprocess.check_call(["pio", "run", "-d", str(ROOT / "robot-platform")])
        print("✅ Build successful.")
    except FileNotFoundError:
        print("⚠️  PlatformIO not found. Please build manually using Arduino IDE.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

    # 4. Upload firmware
    print("📤 Uploading firmware...")
    try:
        subprocess.check_call(["pio", "run", "-t", "upload", "-d", str(ROOT / "robot-platform")])
        print("✅ Upload successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)

    print("🎉 Deployment complete! Robot is running.")

if __name__ == "__main__":
    main()