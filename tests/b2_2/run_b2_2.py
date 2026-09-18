#!/usr/bin/env python3
"""B2.2 portable dependency-closure regression suite."""
from __future__ import annotations

import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dependency_closure, deployment_runtime, production_e2e


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_closure_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except dependency_closure.DependencyClosureError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def _tool_name() -> str:
    return "b22-probe.cmd" if os.name == "nt" else "b22-probe"


def _write_tool(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        path.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
    else:
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)


def hostile_environment(base: Path, host: Path) -> dict[str, str]:
    hostile = os.environ.copy()
    hostile.update(
        {
            "PATH": str(host),
            "PYTHONHOME": str(base / "HostPython"),
            "PYTHONPATH": str(base / "HostProject"),
            "VIRTUAL_ENV": str(base / "HostVenv"),
            "CONDA_PREFIX": str(base / "HostConda"),
            "NODE_PATH": str(base / "HostNode"),
            "NPM_CONFIG_PREFIX": str(base / "HostNpm"),
            "PIOHOME_DIR": str(base / "HostPlatformIO"),
            "PLATFORMIO_CORE_DIR": str(base / "HostPlatformIO"),
            "PLATFORMIO_PLATFORMS_DIR": str(base / "HostPlatforms"),
            "PLATFORMIO_PACKAGES_DIR": str(base / "HostPackages"),
        }
    )
    return hostile


def test_closed_path_and_fail_fast(base: Path) -> None:
    artifact = base / "RoboStudio"
    artifact_tool = artifact / "runtime" / "bin" / _tool_name()
    host = base / "HostTools"
    host_tool = host / _tool_name()
    _write_tool(artifact_tool)
    _write_tool(host_tool)
    (artifact / "runtime" / "platformio" / "platforms").mkdir(parents=True)
    (artifact / "runtime" / "platformio" / "packages").mkdir(parents=True)

    hostile = hostile_environment(base, host)
    env, report = dependency_closure.build_closed_environment(artifact, hostile)
    path_entries = [Path(value) for value in env["PATH"].split(os.pathsep) if value]
    check("host PATH is not inherited", host.resolve() not in [p.resolve() for p in path_entries])
    check("closure mode is explicit", env["ROBOSTUDIO_DEPENDENCY_MODE"] == "artifact-closed")
    check("application home is artifact-owned", Path(env["ROBOSTUDIO_HOME"]).resolve() == artifact.resolve())
    check("PlatformIO core is artifact-owned", Path(env["PLATFORMIO_CORE_DIR"]).resolve() == (artifact / "runtime" / "platformio").resolve())
    check("host Python injection is removed", "PYTHONHOME" not in env and "PYTHONPATH" not in env and "VIRTUAL_ENV" not in env)
    check("host Node injection is removed", "NODE_PATH" not in env and "NPM_CONFIG_PREFIX" not in env)
    check("host PlatformIO injection is replaced", env["PLATFORMIO_CORE_DIR"] != hostile["PLATFORMIO_CORE_DIR"])
    dependency_closure.validate_closed_environment(report)

    resolved = dependency_closure.resolve_artifact_executable(
        _tool_name(), root=artifact, environment=env
    )
    check("required tool resolves from artifact", resolved.resolve() == artifact_tool.resolve())
    checked = dependency_closure.validate_artifact_command(
        [str(artifact_tool)], root=artifact, environment=env, label="B2.2 probe"
    )
    check("explicit artifact command is accepted", checked.resolve() == artifact_tool.resolve())

    artifact_tool.unlink()
    expect_closure_error(
        "missing artifact tool never falls back to hostile host PATH",
        lambda: dependency_closure.resolve_artifact_executable(
            _tool_name(), root=artifact, environment=env
        ),
        "host PATH fallback is disabled",
    )
    expect_closure_error(
        "explicit host executable is rejected",
        lambda: dependency_closure.validate_artifact_command(
            [str(host_tool)], root=artifact, environment=env, label="B2.2 probe"
        ),
        "outside production artifact",
    )


def test_packaged_deployment_runtime_is_closed(base: Path) -> None:
    artifact = base / "RoboStudio"
    host = base / "HostTools"
    _write_tool(artifact / "runtime" / "bin" / _tool_name())
    host.mkdir(parents=True, exist_ok=True)
    (artifact / "runtime" / "platformio" / "platforms").mkdir(parents=True)
    (artifact / "runtime" / "platformio" / "packages").mkdir(parents=True)
    hostile = hostile_environment(base, host)

    original_is_frozen = deployment_runtime.is_frozen
    original_application_root = deployment_runtime.application_root
    try:
        deployment_runtime.is_frozen = lambda: True
        deployment_runtime.application_root = lambda: artifact
        env = deployment_runtime.deployment_runtime_environment(hostile)
    finally:
        deployment_runtime.is_frozen = original_is_frozen
        deployment_runtime.application_root = original_application_root

    path_entries = [Path(value).resolve() for value in env["PATH"].split(os.pathsep) if value]
    check("frozen deployment runtime removes host PATH", host.resolve() not in path_entries)
    check("frozen deployment runtime enables closure mode", env.get("ROBOSTUDIO_DEPENDENCY_MODE") == "artifact-closed")
    check("frozen deployment runtime removes Node injection", "NODE_PATH" not in env and "NPM_CONFIG_PREFIX" not in env)
    check("frozen deployment runtime rebinds PlatformIO", Path(env["PLATFORMIO_CORE_DIR"]).resolve() == (artifact / "runtime" / "platformio").resolve())

    original_is_frozen = deployment_runtime.is_frozen
    try:
        deployment_runtime.is_frozen = lambda: False
        developer = deployment_runtime.deployment_runtime_environment(hostile)
    finally:
        deployment_runtime.is_frozen = original_is_frozen
    check("source development mode retains developer PATH", developer["PATH"] == hostile["PATH"])


def test_production_e2e_records_closure(base: Path) -> None:
    payload = base / "payload"
    (payload / "runtime" / "bin").mkdir(parents=True)
    (payload / "runtime" / "platformio" / "platforms").mkdir(parents=True)
    (payload / "runtime" / "platformio" / "packages").mkdir(parents=True)
    (payload / "compiler").mkdir(parents=True)
    (payload / "RoboStudio.exe").write_bytes(b"b22-fake-app")
    (payload / "runtime" / "bin" / "python.exe").write_bytes(b"b22-fake-python")
    (payload / "compiler" / "main.py").write_text("# b2.2 fixture\n", encoding="utf-8")

    artifact = base / "RoboStudio-portable.zip"
    with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in payload.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(payload).as_posix())

    source = base / "student.py"
    source.write_text("print('robot')\n", encoding="utf-8")
    hostile = hostile_environment(base, base / "HostOnly")

    result = production_e2e.evaluate_production_artifact(
        artifact=artifact,
        source=source,
        launch=False,
        environment=hostile,
    )
    closure = result.evidence.get("dependency_closure", {})
    check("production artifact keeps closure evidence", closure.get("mode") == "artifact-closed")
    check("production gate records no host PATH inheritance", closure.get("host_path_inherited") is False)
    check("production gate does not execute source tree", result.source_tree_execution is False)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-b22-") as temp:
        base = Path(temp)
        test_closed_path_and_fail_fast(base / "closure")
        test_packaged_deployment_runtime_is_closed(base / "deployment")
        test_production_e2e_records_closure(base / "production")
    print("B2.2 portable dependency closure checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
