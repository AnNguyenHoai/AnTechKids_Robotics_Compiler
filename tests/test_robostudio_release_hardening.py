#!/usr/bin/env python3
"""Regression contract for classroom-safe RoboStudio compile/deploy UX."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

from ui import theme
from tools import deployment_runtime


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def test_button_styles_render_valid_balanced_qss() -> None:
    for name, style in (
        ("primary", theme.primary_button_style()),
        ("secondary", theme.secondary_button_style()),
    ):
        check(style.count("{") == style.count("}"), f"{name} button QSS braces are balanced")
        check("}}" not in style, f"{name} button QSS has no accidental doubled closing brace")
        check("QPushButton" in style, f"{name} button QSS retains QPushButton selector")


def test_classroom_timeout_policy() -> None:
    timeout = deployment_runtime.CLASSROOM_BUILD_TIMEOUT_SECONDS
    check(timeout >= 900.0, "classroom compile/deploy timeout is at least 15 minutes")
    check(
        deployment_runtime.DEFAULT_PROCESS_TIMEOUT_SECONDS == timeout,
        "deployment runner default uses the classroom timeout policy",
    )


def test_windows_hidden_console_policy() -> None:
    flags = deployment_runtime.windows_hidden_process_creation_flags()
    if os.name == "nt":
        check(bool(flags & subprocess.CREATE_NO_WINDOW), "Windows child process hides console window")
        check(
            bool(flags & subprocess.CREATE_NEW_PROCESS_GROUP),
            "Windows child process keeps a dedicated process group",
        )
    else:
        check(flags == 0, "non-Windows child process flags remain untouched")


def test_compile_and_deploy_paths_use_shared_policy() -> None:
    worker = (ROBOSTUDIO / "services" / "build_worker.py").read_text(encoding="utf-8")
    service = (ROBOSTUDIO / "services" / "build_service.py").read_text(encoding="utf-8")
    deploy = (ROBOSTUDIO / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    runtime = (ROOT / "tools" / "deployment_runtime.py").read_text(encoding="utf-8")

    check("QProcess" not in worker, "GUI compiler no longer launches through a console-prone QProcess path")
    check("QThread" in worker, "GUI compile remains non-blocking")
    check(
        "windows_hidden_process_creation_flags()" in worker,
        "GUI compile applies hidden Windows process flags",
    )
    check(
        "CLASSROOM_BUILD_TIMEOUT_SECONDS" in worker,
        "GUI compile applies classroom timeout",
    )
    check(
        "windows_hidden_process_creation_flags()" in service,
        "synchronous compiler path applies hidden Windows process flags",
    )
    check(
        "CLASSROOM_BUILD_TIMEOUT_SECONDS" in service,
        "synchronous compiler path applies classroom timeout",
    )
    check(
        deploy.count("timeout=CLASSROOM_BUILD_TIMEOUT_SECONDS") >= 3,
        "bootstrap, USB flash and OTA deployment share classroom timeout",
    )
    check(
        'popen_kwargs["creationflags"] = windows_hidden_process_creation_flags()' in runtime,
        "canonical deployment runner applies hidden Windows process flags",
    )


def test_project_cleanup_and_release_trigger_contract() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "robotics-ci.yml").read_text(encoding="utf-8")
    for entry in ("__pycache__/", ".coverage", "artifacts/", "releases/", ".pio/"):
        check(entry in gitignore, f"generated project debris ignored: {entry}")
    check("PR_TITLE" in workflow, "release workflow inspects release-candidate PR title")
    check("^\\[release\\]" in workflow, "[release] PR convention selects release scope")
    check("Upload Windows production build" in workflow, "release workflow uploads production artifact")


def main() -> int:
    test_button_styles_render_valid_balanced_qss()
    test_classroom_timeout_policy()
    test_windows_hidden_console_policy()
    test_compile_and_deploy_paths_use_shared_policy()
    test_project_cleanup_and_release_trigger_contract()
    print("RoboStudio release hardening: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
