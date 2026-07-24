#!/usr/bin/env python3
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
VALIDATION_DIR = PLATFORM_DIR / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

# Mapping từ tên behavior sang index trong scheduler
BEHAVIOR_INDEX = {
    "MoveForward": 0,
    "TouchStop": 1,
    "Wait": 2,
    "TurnLeft": 3,       # chưa dùng nhưng có thể thêm
    "Stop": 4,
    "ObstacleStop": 5,
    "LineDetect": 6,
    "LightTrigger": 7,
    "ColorDetect": 8,
}

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "usb" in p.description.lower() or "ch340" in p.description.lower():
            return p.device
    return None

def send_command(port, cmd, timeout=2):
    ser = serial.Serial(port, 115200, timeout=timeout)
    time.sleep(0.5)
    ser.write((cmd + "\n").encode())
    time.sleep(0.5)
    lines = []
    start = time.time()
    while time.time() - start < timeout:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            lines.append(line)
        if "finished with status" in line or "completed" in line.lower():
            # tiếp tục đọc thêm vài dòng
            time.sleep(0.1)
            break
    ser.close()
    return lines

def run_behavior_test(behavior_name, duration=5):
    port = find_serial_port()
    if not port:
        print("No serial port found.")
        return None

    idx = BEHAVIOR_INDEX.get(behavior_name, 0)
    print(f"Running behavior: {behavior_name} (index {idx})")
    # Chuyển sang chế độ behavior engine
    send_command(port, "mode behavior", timeout=1)
    # Gửi lệnh run
    logs = send_command(port, f"behavior run {idx}", timeout=duration+3)
    return logs

def main():
    behaviors = ["MoveForward", "TouchStop", "ObstacleStop", "Wait", "LineDetect", "ColorDetect"]
    results = []
    for b in behaviors:
        print(f"\n=== Validating {b} ===")
        logs = run_behavior_test(b)
        if logs:
            # Kiểm tra xem có dòng "finished with status 2" (COMPLETED) không
            completed = any("finished with status 2" in line for line in logs)
            # fallback: tìm "COMPLETED" nếu có
            if not completed:
                completed = any("COMPLETED" in line for line in logs)
            results.append({
                "behavior": b,
                "completed": completed,
                "logs": logs
            })
            print(f"  Completed: {completed}")
        else:
            print("  FAILED (no logs)")

    report_path = VALIDATION_DIR / "behavior_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nValidation complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()