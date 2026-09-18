#!/usr/bin/env python3
"""B2.2 regression: propagate dependency closure through portable Python children."""
from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dependency_closure, deployment_runtime


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def tool_name() -> str:
    return "b22-child-probe.cmd" if os.name == "nt" else "b22-child-probe"


def write_tool(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        path.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
    else:
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-b22-child-") as temp:
        base = Path(temp)
        artifact = base / "RoboStudio"
        host = base / "HostTools"
        artifact_tool = artifact / "runtime" / "bin" / tool_name()
        host_tool = host / tool_name()
        write_tool(artifact_tool)
        write_tool(host_tool)
        (artifact / "runtime" / "platformio" / "platforms").mkdir(parents=True)
        (artifact / "runtime" / "platformio" / "packages").mkdir(parents=True)

        hostile = os.environ.copy()
        hostile["PATH"] = str(host)
        hostile["PYTHONPATH"] = str(base / "HostProject")
        closed, _ = dependency_closure.build_closed_environment(artifact, hostile)

        # Simulate a portable-Python helper that is not frozen but inherited
        # the production marker, then accidentally receives poisoned values.
        contaminated = dict(closed)
        contaminated["PATH"] = str(host)
        contaminated["PYTHONPATH"] = str(base / "HostProject")

        captured: list[dict[str, str]] = []

        class FakePopen:
            def __init__(self, command, **kwargs):
                self.command = command
                self.returncode = 0
                self.stdout = io.StringIO("")
                captured.append(dict(kwargs["env"]))

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                return self.returncode

        original_is_frozen = deployment_runtime.is_frozen
        original_application_root = deployment_runtime.application_root
        original_popen = deployment_runtime.subprocess.Popen
        original_environment = os.environ.copy()
        try:
            deployment_runtime.is_frozen = lambda: False
            deployment_runtime.application_root = lambda: artifact
            deployment_runtime.subprocess.Popen = FakePopen

            deployment_runtime.run_process(
                [str(artifact_tool)], cwd=artifact, env=contaminated, timeout=1.0
            )
            explicit = captured[-1]
            explicit_path = [Path(value).resolve() for value in explicit["PATH"].split(os.pathsep) if value]
            check("portable child marker re-seals caller PATH", host.resolve() not in explicit_path)
            check("portable child marker strips caller PYTHONPATH", "PYTHONPATH" not in explicit)
            check(
                "portable child keeps dependency-closed mode",
                explicit.get("ROBOSTUDIO_DEPENDENCY_MODE") == "artifact-closed",
            )

            os.environ.clear()
            os.environ.update(contaminated)
            deployment_runtime.run_process([str(artifact_tool)], cwd=artifact, timeout=1.0)
            implicit = captured[-1]
            implicit_path = [Path(value).resolve() for value in implicit["PATH"].split(os.pathsep) if value]
            check("portable child env=None is re-sealed", host.resolve() not in implicit_path)
            check("portable child env=None strips PYTHONPATH", "PYTHONPATH" not in implicit)
        finally:
            os.environ.clear()
            os.environ.update(original_environment)
            deployment_runtime.is_frozen = original_is_frozen
            deployment_runtime.application_root = original_application_root
            deployment_runtime.subprocess.Popen = original_popen

    print("B2.2 portable child closure propagation checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
