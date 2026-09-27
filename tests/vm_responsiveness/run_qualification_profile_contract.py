#!/usr/bin/env python3
"""Contract gate for the VM-RT physical qualification PlatformIO profile (#329/#380)."""
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


def workflow_step(text: str, name_pattern: str) -> str:
    match = re.search(
        rf"- name: {name_pattern}\n(?P<body>.*?)(?=\n\s*- name:)",
        text,
        re.DOTALL,
    )
    return match.group("body") if match else ""


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

    # The install step may grow to cover other firmware qualification profiles
    # (for example line-regression A/B).  VM-RT owns the required scopes and
    # PlatformIO command, not the exact human-readable step title.
    install_body = workflow_step(
        workflow,
        r"Install PlatformIO for .*firmware validation",
    )
    check("workflow has qualification PlatformIO install step", bool(install_body))
    if install_body:
        check("qualification install uses PlatformIO", "platformio" in install_body.lower())
        check(
            "PlatformIO install covers VM/full/release scopes",
            all(token in install_body for token in (
                "steps.impact.outputs.vm == 'true'",
                "steps.impact.outputs.full == 'true'",
                "steps.impact.outputs.release == 'true'",
            )),
        )

    production_body = workflow_step(workflow, r"Compile impacted ESP32 production firmware")
    check("production compile step remains separate", bool(production_body))
    if production_body:
        check("production compile still targets esp32dev", "-e esp32dev" in production_body)
        check("production compile does not use qualification profile", "esp32dev_vm_qualification" not in production_body)
        check(
            "production compile covers VM/full/release scopes",
            all(token in production_body for token in (
                "steps.impact.outputs.vm == 'true'",
                "steps.impact.outputs.full == 'true'",
                "steps.impact.outputs.release == 'true'",
            )),
        )

    compile_body = workflow_step(workflow, r"Compile VM-RT qualification firmware")
    check("workflow compiles VM-RT qualification firmware", bool(compile_body))
    if compile_body:
        check("qualification compile uses exact profile", "-e esp32dev_vm_qualification" in compile_body)
        check(
            "qualification compile covers VM/full/release scopes",
            all(token in compile_body for token in (
                "steps.impact.outputs.vm == 'true'",
                "steps.impact.outputs.full == 'true'",
                "steps.impact.outputs.release == 'true'",
            )),
        )

    check("runbook names qualification profile", "esp32dev_vm_qualification" in runbook)
    check("runbook requires exact evidence commit", "exact git sha" in runbook.lower() or "exact firmware commit" in runbook.lower())
    check("runbook states CI build verification", "build-verified" in runbook.lower() or "ci-verified" in runbook.lower())

    print("VM-RT qualification profile contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
