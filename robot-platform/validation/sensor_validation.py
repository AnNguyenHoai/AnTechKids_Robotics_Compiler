#!/usr/bin/env python3
"""
Sensor Validation Framework
Automates compilation, upload, and data collection for golden sensor programs.
"""
import subprocess
import sys
import time
import json
import re
import serial
import serial.tools.list_ports
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PLATFORM_DIR = ROOT / "robot-platform"
GOLDEN_DIR = PLATFORM_DIR / "golden_sensors"
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

def read_serial_log(port, timeout=20):
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

def parse_sensor_events(logs):
    # Tìm các sự kiện sensor và stop
    events = []
    for line in logs:
        if "ReadUltrasonic" in line or "ReadTouch" in line or "ReadLight" in line or "ReadColor" in line or "ReadLine" in line:
            events.append(line)
        if "Stop" in line and "RobotAPI" in line:
            events.append(line)
    return events

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

    events = parse_sensor_events(logs)

    # Kiểm tra xem có lệnh Stop không (tùy program)
    has_stop = any("Stop" in e for e in events)

    return {
        "program": program_name,
        "events": events,
        "has_stop": has_stop,
        "logs": logs
    }

def main():
    programs = [
        "001_touch_stop.py",
        "002_line_detect.py",
        "003_obstacle_stop.py",
        "004_light_trigger.py",
        "005_color_detect.py",
        "006_sensor_monitor.py"
    ]

    results = []
    for prog in programs:
        print(f"\n=== Validating {prog} ===")
        result = run_validation(prog)
        if result:
            results.append(result)
            print(f"  Has stop: {result['has_stop']}")
            for evt in result['events'][:5]:
                print(f"  {evt}")
        else:
            print("  FAILED.")

    report_path = VALIDATION_DIR / "sensor_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nValidation complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()