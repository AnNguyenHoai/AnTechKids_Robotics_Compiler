#!/usr/bin/env python3
"""Contract gate for the VM-RT physical qualification PlatformIO profile (#329)."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PIO = ROOT / "robot-platform" / "platformio.ini"
WORKFLOW = ROOT / ".github" / "workflows" / "robotics-ci.yml"
RUNBOOK = ROOT / "docs" / "VM_PHYSICAL_QUALIFICATION.md"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def section(text: str, header: str) -> str:
    marker = f"[{header}]"
    start = text.find(marker)
    if start < 0:
        return ""
    next_header = text.find("\n[", start + len(marker))
    return text[start: next_header if next_header >= 0 else len(text)]


def main() -> int:
    pio = PIO.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    qualification = section(pio, "env:esp32dev_vm_qualification")
    check("qualification environment exists", bool(qualification))
    check("qualification environment extends production", "extends = env:esp32dev" in qualification)
    check(
        "qualification environment enables VM responsiveness diagnostics",
        "-DVM_RESPONSIVENESS_DIAGNOSTICS=1" in qualification,
    )
    check(
        "qualification profile does not replace production environment",
        bool(section(pio, "env:esp32dev")),
    )

    install_match = re.search(
        r"- name: Install PlatformIO for VM/release firmware validation\n(?P<body>.*?)(?=\n\s*- name:)",
        workflow,
        re.DOTALL,
    )
    check("workflow has qualification PlatformIO install step", install_match is not None)
    if install_match:
        check(
            "PlatformIO install covers VM/full/release scopes",
            all(token in install_match.group("body") for token in (
                "steps.impact.outputs.vm == 'true'",
                "steps.impact.outputs.full == 'true'",
                "steps.impact.outputs.release == 'true'",
            )),
        )

    compile_match = re.search(
        r"- name: Compile VM-RT qualification firmware\n(?P<body>.*?)(?=\n\s*- name:)",
        workflow,
        re.DOTALL,
    )
    check("workflow compiles VM-RT qualification firmware", compile_match is not None)
    if compile_match:
        body = compile_match.group("body")
        check("qualification compile uses exact profile", "-e esp32dev_vm_qualification" in body)
        check(
            "qualification compile covers VM/full/release scopes",
            all(token in body for token in (
                "steps.impact.outputs.vm == 'true'",
                "steps.impact.outputs.full == 'true'",
                "steps.impact.outputs.release == 'true'",
            )),
        )

    production_match = re.search(
        r"- name: Compile impacted ESP32 production firmware\n(?P<body>.*?)(?=\n\s*- name:)",
        workflow,
        re.DOTALL,
    )
    check("production compile step remains separate", production_match is not None)
    if production_match:
        check("production compile still targets esp32dev", "-e esp32dev" in production_match.group("body"))
        check("production compile does not use qualification profile", "esp32dev_vm_qualification" not in production_match.group("body"))

    check("runbook names qualification profile", "esp32dev_vm_qualification" in runbook)
    check("runbook requires exact evidence commit", "exact git sha" in runbook.lower() or "exact firmware commit" in runbook.lower())
    check("runbook states CI build verification", "build-verified" in runbook.lower() or "ci-verified" in runbook.lower())

    print("VM-RT qualification profile contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
