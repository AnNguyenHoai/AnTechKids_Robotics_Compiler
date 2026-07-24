#!/usr/bin/env python3
"""
Speed Characterization
Tests each speed level (10,20,...,100) and records duration.
"""
import subprocess
import sys
import json
import time
import serial
import serial.tools.list_ports
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PLATFORM_DIR = ROOT / "robot-platform"
COMPILER = ROOT / "robot-compiler" / "main.py"
OUTPUT_HEADER = PLATFORM_DIR / "main" / "src" / "Application" / "generated_program.h"
VALIDATION_DIR = PLATFORM_DIR / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

SPEEDS = range(10, 110, 10)

def find_serial_port():
    import serial.tools.list_ports
    for port in serial.tools.list_ports.comports():
        if "usb" in port.description.lower() or "ch340" in port.description.lower():
            return port.device
    return None

def compile_and_upload(speed):
    # Tạo file tạm với lệnh forward(speed) wait(1) stop
    source = PLATFORM_DIR / "temp_speed.py"
    with open(source, "w") as f:
        f.write(f"""
import rcu
rcu.SetMoveRunSecond("forward", {speed}, 1.0)
""")
    subprocess.check_call([sys.executable, str(COMPILER), "--file", str(source), "--output", str(OUTPUT_HEADER)])
    subprocess.check_call(["pio", "run", "-t", "upload", "-d", str(PLATFORM_DIR)])
    source.unlink()

def read_log(port, timeout=10):
    ser = serial.Serial(port, 115200, timeout=timeout)
    time.sleep(2)
    lines = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            lines.append(line)
            if "Stop" in line:
                break
    ser.close()
    return lines

def extract_duration(logs):
    import re
    start = None
    end = None
    for line in logs:
        if "Forward" in line:
            m = re.search(r'\[(\d+)\]', line)
            if m: start = int(m.group(1))
        if "Stop" in line:
            m = re.search(r'\[(\d+)\]', line)
            if m: end = int(m.group(1))
    return (end - start)/1000.0 if start and end else None

def main():
    port = find_serial_port()
    if not port:
        print("No serial port found")
        sys.exit(1)

    results = {}
    for speed in SPEEDS:
        print(f"Testing speed {speed}...")
        compile_and_upload(speed)
        logs = read_log(port)
        duration = extract_duration(logs)
        results[speed] = {"duration_sec": duration}
        print(f"  Duration: {duration} sec")

    with open(VALIDATION_DIR / "speed_profile.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Speed characterization complete.")

if __name__ == "__main__":
    main()