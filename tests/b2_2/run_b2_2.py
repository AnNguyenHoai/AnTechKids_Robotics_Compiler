#!/usr/bin/env python3
"""B2.2 portable dependency-closure regression suite."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dependency_closure, deployment_runtime, production_e2e, runtime_paths


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


def expect_runtime_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except deployment_runtime.DeploymentRuntimeError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def _tool_name() -> str:
    return "b22-probe.cmd" if os.name == "nt" else "b22-probe"


def _python_name() -> str:
    return "python.exe" if os.name == "nt" else "python"


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


def _prepare_artifact(artifact: Path) -> Path:
    artifact_tool = artifact / "runtime" / "bin" / _tool_name()
    _write_tool(artifact_tool)
    (artifact / "runtime" / "platformio" / "platforms").mkdir(parents=True, exist_ok=True)
    (artifact / "runtime" / "platformio" / "packages").mkdir(parents=True, exist_ok=True)
    return artifact_tool


def test_closed_path_and_fail_fast(base: Path) -> None:
    artifact = base / "RoboStudio"
    artifact_tool = _prepare_artifact(artifact)
    host = base / "HostTools"
    host_tool = host / _tool_name()
    _write_tool(host_tool)

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
    _prepare_artifact(artifact)
    host.mkdir(parents=True, exist_ok=True)
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


def test_run_process_seals_frozen_boundary(base: Path) -> None:
    artifact = base / "RoboStudio"
    host = base / "HostTools"
    artifact_tool = _prepare_artifact(artifact)
    host_tool = host / _tool_name()
    _write_tool(host_tool)
    hostile = hostile_environment(base, host)
    hostile["ROBOT_WIFI_SSID"] = "B2.2-safe-value"

    captured_envs: list[dict[str, str] | None] = []

    class FakePopen:
        def __init__(self, command, **kwargs):
            self.command = command
            self.returncode = 0
            self.stdout = io.StringIO("sealed-boundary\n")
            captured = kwargs.get("env")
            captured_envs.append(dict(captured) if captured is not None else None)

        def poll(self):
            return self.returncode

    original_is_frozen = deployment_runtime.is_frozen
    original_application_root = deployment_runtime.application_root
    original_popen = deployment_runtime.subprocess.Popen
    original_environment = os.environ.copy()
    try:
        deployment_runtime.is_frozen = lambda: True
        deployment_runtime.application_root = lambda: artifact
        deployment_runtime.subprocess.Popen = FakePopen

        result = deployment_runtime.run_process(
            [str(artifact_tool)], cwd=artifact, env=hostile, timeout=1.0
        )
        check("frozen runner executes through sealed boundary", result.returncode == 0)
        check("frozen runner preserves streamed output", result.output == "sealed-boundary\n")
        explicit_env = captured_envs[-1]
        check("frozen runner always supplies a closed environment", explicit_env is not None)
        assert explicit_env is not None
        explicit_path = [Path(value).resolve() for value in explicit_env["PATH"].split(os.pathsep) if value]
        check("caller host PATH cannot bypass runner closure", host.resolve() not in explicit_path)
        check("caller PYTHONPATH cannot bypass runner closure", "PYTHONPATH" not in explicit_env)
        check("safe deployment values survive closure", explicit_env.get("ROBOT_WIFI_SSID") == "B2.2-safe-value")
        check("runner disables user site packages", explicit_env.get("PYTHONNOUSERSITE") == "1")

        os.environ.clear()
        os.environ.update(hostile)
        deployment_runtime.run_process([str(artifact_tool)], cwd=artifact, timeout=1.0)
        inherited_env = captured_envs[-1]
        check("env=None is sealed instead of inherited", inherited_env is not None)
        assert inherited_env is not None
        inherited_path = [Path(value).resolve() for value in inherited_env["PATH"].split(os.pathsep) if value]
        check("implicit host PATH cannot bypass runner closure", host.resolve() not in inherited_path)
        check("implicit PYTHONPATH cannot bypass runner closure", "PYTHONPATH" not in inherited_env)

        popen_calls_before_rejection = len(captured_envs)
        expect_runtime_error(
            "host absolute deployment executable is rejected before spawn",
            lambda: deployment_runtime.run_process(
                [str(host_tool)], cwd=artifact, env=hostile, timeout=1.0
            ),
            "outside production artifact",
        )
        check(
            "rejected host executable never reaches Popen",
            len(captured_envs) == popen_calls_before_rejection,
        )
    finally:
        os.environ.clear()
        os.environ.update(original_environment)
        deployment_runtime.is_frozen = original_is_frozen
        deployment_runtime.application_root = original_application_root
        deployment_runtime.subprocess.Popen = original_popen


def test_packaged_python_command(base: Path) -> None:
    artifact = base / "RoboStudio"
    packaged_python = artifact / "runtime" / "bin" / _python_name()
    _write_tool(packaged_python)

    old_home = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    original_runtime_is_frozen = runtime_paths.is_frozen
    try:
        os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(artifact)
        command = deployment_runtime.python_command("tools/deploy_robot.py", "--mode", "bootstrap")
        check("deployment script uses packaged Python", Path(command[0]).resolve() == packaged_python.resolve())
        check("deployment script arguments are preserved", command[1:] == ["tools/deploy_robot.py", "--mode", "bootstrap"])

        packaged_python.unlink()
        runtime_paths.is_frozen = lambda: True
        expect_runtime_error(
            "missing packaged Python fails fast",
            lambda: deployment_runtime.python_command("tools/deploy_robot.py"),
            "runtime/bin/python.exe",
        )
    finally:
        runtime_paths.is_frozen = original_runtime_is_frozen
        if old_home is None:
            os.environ.pop(runtime_paths.APPLICATION_HOME_ENV, None)
        else:
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = old_home


def test_robot_deployment_service_uses_portable_python() -> None:
    service = ROOT / "robostudio" / "services" / "robot_deployment_service.py"
    source = service.read_text(encoding="utf-8")
    check("RoboStudio deployment service does not execute helper scripts with sys.executable", "sys.executable" not in source)
    check("RoboStudio deployment service routes helper scripts through python_command", source.count("python_command(") >= 3)


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
        test_run_process_seals_frozen_boundary(base / "runner")
        test_packaged_python_command(base / "python")
        test_robot_deployment_service_uses_portable_python()
        test_production_e2e_records_closure(base / "production")
    print("B2.2 portable dependency closure checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
