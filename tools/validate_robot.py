#!/usr/bin/env python3
"""Host-side physical validation gate for a connected robot.

This tool verifies the network-visible robot identity/readiness. It deliberately
never commands motors or other actuators; physical motion/sensor checks remain
operator-controlled until the hardware is available.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def get_json(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a network-connected ESP32 robot")
    parser.add_argument("--robot", required=True, help="Robot hostname/IP, e.g. robot-A1B2C3.local")
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    base = f"http://{args.robot}"
    try:
        info = get_json(f"{base}/api/v1/info", args.timeout)
        health = get_json(f"{base}/api/v1/health", args.timeout)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"PHYSICAL VALIDATION BLOCKED: robot is not reachable/ready: {exc}")
        return 1

    checks = {
        "identity": info.get("device") == "AnTechKids-Robot",
        "target": info.get("target") == "esp32",
        "ota": info.get("ota") is True,
        "health": health.get("status") == "ok",
        "ready": health.get("ready") is True,
    }
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")

    print("\nOperator hardware checks still required:")
    for item in ("BOOT/READY", "motor forward/backward", "turn left/right", "sensor input", "student-program behavior"):
        print(f"  [ ] {item}")

    if not all(checks.values()):
        return 1

    print("\nSOFTWARE PHYSICAL-VALIDATION GATE PASS")
    print(json.dumps({"info": info, "health": health}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
