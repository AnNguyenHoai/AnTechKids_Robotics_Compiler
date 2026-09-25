#!/usr/bin/env python3
"""Classify changed repository paths into conservative CI impact scopes.

The selector is intentionally fail-closed:
- known narrow areas run only their relevant gates;
- unknown files fall back to the full regression suite;
- production/release packaging is never selected automatically.

Manual workflow scopes can force `full` or `release`.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Iterable


CI_META_FILES = {
    ".github/workflows/robotics-ci.yml",
    "run_all_tests.py",
    "tools/ci_impact.py",
}

VM_PREFIXES = (
    "tests/vm_responsiveness/",
    "robot-platform/main/src/Services/VM/",
    "tools/vm_rt_",
)
VM_FILES = {
    "docs/VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md",
    "docs/VM_COOPERATIVE_EXECUTION_SPEC.md",
    "docs/VM_RUNTIME_BLOCKING_AUDIT.md",
    "docs/VM_FIRMWARE_MAIN_LOOP_INTEGRATION.md",
    "docs/C2_VM_DISPATCH_CONTRACT.md",
    "docs/ROBOT_EXECUTION_MODEL.md",
    "robot-platform/main/main.ino",
    "robot-platform/main/include/generated/opcode.h",
    "robot-platform/main/src/Services/Robot/RobotAPI.h",
    "robot-platform/main/src/Services/Robot/RobotAPICooperative.cpp",
    "robot-platform/main/src/Sensor/LineSensorSnapshot.h",
    "robot-platform/main/src/Sensor/LineSensorSnapshot.cpp",
    "robot-platform/main/src/Sensor/TCRT5000.h",
    "robot-platform/main/src/Sensor/TCRT5000.cpp",
}

LINE_PREFIXES = (
    "tests/line_follow_stability/",
    "robot-platform/main/src/Services/Line/",
    "robot-platform/main/src/Services/Robot/Line",
    "robot-platform/main/src/Services/Robot/CooperativeLine",
)
LINE_FILES = {
    "robot-platform/main/src/Sensor/LineSensorSnapshot.h",
    "robot-platform/main/src/Sensor/LineSensorSnapshot.cpp",
    "robot-platform/main/src/Sensor/TCRT5000.h",
    "robot-platform/main/src/Sensor/TCRT5000.cpp",
    "robot-platform/main/src/Diagnostics/DiagnosticsManager.cpp",
}

CONTRACT_PREFIXES = (
    "tests/h32_platform_contract/",
    "tests/h33_capability_compiler/",
    "tests/h34_contract_traceability/",
    "tests/h35_compatibility/",
    "packages/robot-isa/",
)
CONTRACT_FILES = {
    "tools/platform_contract.py",
    "tools/compatibility_policy.py",
    "robot-compiler/compiler/target_contract.py",
    "docs/H35_COMPATIBILITY_UPGRADE_POLICY.md",
    "docs/H26-B_CONTRACT_BASELINE.json",
}

ROBOSTUDIO_PREFIXES = (
    "robostudio/",
    "tests/ui_responsive/",
    "tests/ui_production/",
)

PACKAGING_PREFIXES = (
    "tests/b2_2/",
    "tests/b2_3/",
    "tests/b2_4/",
    "tests/b2_5/",
    "tests/b2_6/",
    "tests/b2_7/",
)
PACKAGING_FILES = {
    "BUILD_PRODUCTION_ZIP.cmd",
    "scripts/Build-ProductionZip.ps1",
    "tools/copy_run_contract.py",
    "tools/copy_run_release.py",
    "tools/one_click_production_zip.py",
    "tools/packaged_platformio_offline_first_flash.py",
    "tools/hardware_feature_config.py",
    "tools/hardware_preflight.py",
    "tools/clean_machine_physical_e2e.py",
}


def _norm(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _matches(path: str, prefixes: Iterable[str], files: set[str]) -> bool:
    return path in files or any(path.startswith(prefix) for prefix in prefixes)


def classify(paths: Iterable[str], scope: str = "auto") -> dict[str, bool | int]:
    files = sorted({_norm(p) for p in paths if _norm(p)})
    result: dict[str, bool | int] = {
        "vm": False,
        "line": False,
        "contracts": False,
        "robostudio": False,
        "packaging": False,
        "full": False,
        "release": False,
        "docs_only": bool(files) and all(p.startswith("docs/") for p in files),
        "changed_count": len(files),
    }

    if scope == "release":
        result["full"] = True
        result["release"] = True
        return result
    if scope == "full":
        result["full"] = True
        return result
    if scope != "auto":
        raise ValueError(f"unsupported scope: {scope}")
    if not files:
        result["full"] = True
        return result

    unknown: list[str] = []
    for path in files:
        if path in CI_META_FILES:
            continue

        matched = False
        if _matches(path, VM_PREFIXES, VM_FILES):
            result["vm"] = True
            matched = True
            if path == "docs/VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md" or path == "robot-platform/main/include/generated/opcode.h":
                result["contracts"] = True

        if _matches(path, LINE_PREFIXES, LINE_FILES):
            result["line"] = True
            matched = True

        if _matches(path, CONTRACT_PREFIXES, CONTRACT_FILES):
            result["contracts"] = True
            matched = True

        if _matches(path, ROBOSTUDIO_PREFIXES, set()):
            result["robostudio"] = True
            matched = True

        if _matches(path, PACKAGING_PREFIXES, PACKAGING_FILES):
            result["packaging"] = True
            matched = True

        if path.startswith("docs/") and not matched:
            result["contracts"] = True
            matched = True

        if not matched:
            unknown.append(path)

    if unknown:
        result["full"] = True

    return result


def changed_files(base: str, head: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def write_github_output(path: str, result: dict[str, bool | int]) -> None:
    output = Path(path)
    with output.open("a", encoding="utf-8") as stream:
        for key, value in result.items():
            rendered = "true" if value is True else "false" if value is False else str(value)
            stream.write(f"{key}={rendered}\n")


def self_test() -> None:
    vm = classify([
        "tests/vm_responsiveness/run_vm_responsiveness_baseline.py",
        "docs/VM_RESPONSIVENESS_COMPATIBILITY_MATRIX.md",
        "run_all_tests.py",
        ".github/workflows/robotics-ci.yml",
    ])
    assert vm["vm"] is True and vm["contracts"] is True
    assert vm["full"] is False and vm["release"] is False

    firmware_loop = classify([
        "robot-platform/main/main.ino",
        "docs/VM_FIRMWARE_MAIN_LOOP_INTEGRATION.md",
    ])
    assert firmware_loop["vm"] is True
    assert firmware_loop["full"] is False

    cooperative_robot_api = classify([
        "robot-platform/main/src/Services/Robot/RobotAPI.h",
        "robot-platform/main/src/Services/Robot/RobotAPICooperative.cpp",
        "tests/vm_responsiveness/run_run_slice_core.py",
    ])
    assert cooperative_robot_api["vm"] is True
    assert cooperative_robot_api["full"] is False

    line_snapshot = classify([
        "robot-platform/main/src/Sensor/LineSensorSnapshot.cpp",
        "robot-platform/main/src/Sensor/TCRT5000.cpp",
    ])
    assert line_snapshot["vm"] is True
    assert line_snapshot["line"] is True
    assert line_snapshot["full"] is False

    latency_corrective = classify([
        "robot-platform/main/src/Services/VM/VMRunSlice.cpp",
        "robot-platform/main/src/Services/Line/LineFollower.cpp",
        "robot-platform/main/src/Diagnostics/DiagnosticsManager.cpp",
        "tools/vm_rt_qualification.py",
        "tools/vm_rt_physical_campaign.py",
        "tests/vm_responsiveness/run_control_latency_corrective_contract.py",
        "tests/line_follow_stability/run_line_follow_stability.py",
        "docs/VM_CONTROL_LATENCY_CORRECTIVE_AUDIT.md",
    ])
    assert latency_corrective["vm"] is True
    assert latency_corrective["line"] is True
    assert latency_corrective["contracts"] is True
    assert latency_corrective["full"] is False

    docs = classify(["docs/README_ONLY.md"])
    assert docs["contracts"] is True and docs["full"] is False

    unknown = classify(["robot-compiler/compiler/frontend.py"])
    assert unknown["full"] is True

    full = classify(["docs/README_ONLY.md"], scope="full")
    assert full["full"] is True and full["release"] is False

    release = classify(["docs/README_ONLY.md"], scope="release")
    assert release["full"] is True and release["release"] is True

    empty = classify([])
    assert empty["full"] is True

    print("CI impact selector: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--scope", choices=("auto", "full", "release"), default="auto")
    parser.add_argument("--github-output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if not args.base or not args.head:
        parser.error("--base and --head are required unless --self-test is used")

    files = changed_files(args.base, args.head)
    result = classify(files, scope=args.scope)

    print("Changed files:")
    for path in files:
        print(f"  - {path}")
    print("Selected CI scopes:")
    for key, value in result.items():
        print(f"  {key}={value}")

    if args.github_output:
        write_github_output(args.github_output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
