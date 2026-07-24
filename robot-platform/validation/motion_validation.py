#!/usr/bin/env python3
"""
Motion Validation Framework
Automates compilation, upload, and data collection for golden programs.
"""

import subprocess
import sys
import os
import time
import json
import re
import serial
import serial.tools.list_ports
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PLATFORM_DIR = ROOT / "robot-platform"
GOLDEN_DIR = PLATFORM_DIR / "golden"
VALIDATION_DIR = PLATFORM_DIR / "validation"
COMPILER = ROOT / "robot-compiler" / "main.py"
OUTPUT_HEADER = PLATFORM_DIR / "main" / "src" / "Application" / "generated_program.h"

VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    print("Available ports:")
    for p in ports:
        print(f"  {p.device} - {p.description}")
    for port in ports:
        desc = port.description.lower()
        if "usb" in desc or "ch340" in desc or "cp210" in desc:
            return port.device
    return None

def compile_program(source_path):
    cmd = [sys.executable, str(COMPILER), "--file", str(source_path), "--output", str(OUTPUT_HEADER)]
    subprocess.check_call(cmd, cwd=ROOT)

def upload_firmware():
    try:
        subprocess.check_call(["pio", "run", "-t", "upload", "-d", str(PLATFORM_DIR)])
    except FileNotFoundError:
        print("PlatformIO not found. Please upload manually using Arduino IDE.")
        sys.exit(1)

def read_serial_log(port, timeout=15):
    ser = serial.Serial(port, 115200, timeout=timeout)
    time.sleep(2)
    logs = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            logs.append(line)
            if "Execution Finished" in line or "100/100 executions completed" in line:
                break
    ser.close()
    return logs

def parse_motion_times(logs):
    """
    Extract start and end timestamps from logs.
    Assumes first motion command (Forward/Backward/Turn...) is start,
    and Stop is end.
    """
    start = None
    end = None
    for line in logs:
        if "Forward" in line or "Backward" in line or "TurnLeft" in line or "TurnRight" in line:
            m = re.search(r'\[(\d+)\]', line)
            if m:
                start = int(m.group(1))
        if "Stop" in line:
            m = re.search(r'\[(\d+)\]', line)
            if m:
                end = int(m.group(1))
    return start, end

def run_validation(program_name):
    source = GOLDEN_DIR / program_name
    if not source.exists():
        print(f"Golden program {source} not found.")
        return None

    print(f"Compiling {program_name}...")
    compile_program(source)
    print("Uploading...")
    upload_firmware()

    port = find_serial_port()
    if not port:
        print("No serial port found.")
        return None

    print("Reading serial log...")
    logs = read_serial_log(port)

    start, end = parse_motion_times(logs)
    duration = (end - start) / 1000.0 if start and end else None

    return {
        "program": program_name,
        "start_ms": start,
        "end_ms": end,
        "duration_seconds": duration,
        "logs": logs
    }

def main():
    programs = [
        "001_forward.py",
        "002_backward.py",
        "003_turn_left.py",
        "004_turn_right.py",
        "005_square.py",
        "006_triangle.py",
        "007_circle_approx.py",
        "008_zigzag.py"
    ]

    results = []
    for prog in programs:
        print(f"\n=== Validating {prog} ===")
        result = run_validation(prog)
        if result:
            results.append(result)
            print(f"  Duration: {result['duration_seconds']} sec")
        else:
            print("  FAILED.")

    report_path = VALIDATION_DIR / "motion_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nValidation complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()