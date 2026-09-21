#!/usr/bin/env python3
"""B2.3 portable path + mutable-state isolation regression suite."""
from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import (
    build_isolation,
    dependency_closure,
    deployment_runtime,
    firmware_workspace,
    runtime_paths,
)


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_path_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except runtime_paths.RuntimePathError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def _inside(path: Path | str, root: Path | str) -> bool:
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _tool_name() -> str:
    return "python.exe" if os.name == "nt" else "python"


def _prepare_artifact(root: Path) -> Path:
    tool = root / "runtime" / "bin" / _tool_name()
    tool.parent.mkdir(parents=True, exist_ok=True)
    tool.write_bytes(b"b23-packaged-tool")
    (root / "runtime" / "platformio" / "platforms").mkdir(parents=True)
    (root / "runtime" / "platformio" / "packages").mkdir(parents=True)
    firmware = root / "firmware" / "robot-platform"
    (firmware / "main").mkdir(parents=True)
    (firmware / "platformio.ini").write_text(
        "[env:esp32dev]\nboard=esp32dev\n", encoding="utf-8"
    )
    (firmware / "wifi_config.py").write_text("# fixture\n", encoding="utf-8")
    (firmware / "main" / "main.cpp").write_text(
        "void setup(){}\nvoid loop(){}\n", encoding="utf-8"
    )
    return tool


def _snapshot(root: Path) -> tuple[tuple[str, ...], tuple[tuple[str, bytes], ...]]:
    directories = tuple(
        sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir())
    )
    files = tuple(
        sorted(
            (p.relative_to(root).as_posix(), p.read_bytes())
            for p in root.rglob("*")
            if p.is_file()
        )
    )
    return directories, files


def _packaged_env(artifact: Path, state: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            runtime_paths.APPLICATION_HOME_ENV: str(artifact),
            runtime_paths.STATE_ROOT_ENV: str(state),
            runtime_paths.RUNTIME_MODE_ENV: "packaged",
            runtime_paths.DEPENDENCY_MODE_ENV: "artifact-closed",
        }
    )
    return env


def test_path_relocation_and_state_contract(base: Path) -> None:
    artifact = base / "Ổ đĩa giả lập" / "Robo Studio Portable Ứng Dụng"
    state = base / "Người dùng" / "Trạng thái Robo Studio"
    unrelated = base / "CWD hoàn toàn khác"
    _prepare_artifact(artifact)
    unrelated.mkdir(parents=True)
    env = _packaged_env(artifact, state)

    resolved = runtime_paths.user_data_root(
        base_env=env,
        application_root_override=artifact,
        enforce_external=True,
    )
    check("Unicode/space state root is preserved", resolved == state.resolve())
    check("state root is outside release", not _inside(resolved, artifact))

    previous = Path.cwd()
    try:
        os.chdir(unrelated)
        again = runtime_paths.user_data_root(
            base_env=env,
            application_root_override=artifact,
            enforce_external=True,
        )
    finally:
        os.chdir(previous)
    check("state resolution is independent of cwd", again == resolved)

    inside = dict(env)
    inside[runtime_paths.STATE_ROOT_ENV] = str(artifact / "data")
    expect_path_error(
        "state inside release is rejected",
        lambda: runtime_paths.user_data_root(
            base_env=inside,
            application_root_override=artifact,
            enforce_external=True,
        ),
        "outside the application/release root",
    )

    relative = dict(env)
    relative[runtime_paths.STATE_ROOT_ENV] = "relative-state"
    expect_path_error(
        "relative state override is rejected",
        lambda: runtime_paths.user_data_root(
            base_env=relative,
            application_root_override=artifact,
            enforce_external=True,
        ),
        "must be an absolute path",
    )

    legacy = dict(env)
    legacy.pop(runtime_paths.STATE_ROOT_ENV, None)
    legacy[runtime_paths.PORTABLE_DATA_ENV] = "1"
    expect_path_error(
        "legacy in-install portable data is rejected in production",
        lambda: runtime_paths.user_data_root(
            base_env=legacy,
            application_root_override=artifact,
            enforce_external=True,
        ),
        "cannot place mutable state inside a packaged RoboStudio release",
    )

    blocked = base / "state-is-a-file"
    blocked.write_text("not a directory", encoding="utf-8")
    blocked_env = dict(env)
    blocked_env[runtime_paths.STATE_ROOT_ENV] = str(blocked)
    expect_path_error(
        "unwritable/invalid state root fails fast",
        lambda: runtime_paths.prepare_user_data_root(
            base_env=blocked_env,
            application_root_override=artifact,
            enforce_external=True,
        ),
        "state root is not writable",
    )


def test_dependency_and_platformio_state_split(
    base: Path,
) -> tuple[Path, Path, dict[str, str], Path]:
    artifact = base / "Release Có Khoảng Trắng" / "RoboStudio Việt"
    state = base / "External State" / "Học sinh Nguyễn An"
    tool = _prepare_artifact(artifact)
    host = base / "Host PlatformIO State"
    env = _packaged_env(artifact, state)
    env.update(
        {
            "PLATFORMIO_CORE_DIR": str(host / "core"),
            "PLATFORMIO_GLOBALLIB_DIR": str(host / "lib"),
            "PLATFORMIO_CACHE_DIR": str(host / "cache"),
            "PLATFORMIO_BUILD_CACHE_DIR": str(host / "build-cache"),
            "PLATFORMIO_WORKSPACE_DIR": str(host / "workspace"),
            "PLATFORMIO_BUILD_DIR": str(host / "build"),
            "PLATFORMIO_LIBDEPS_DIR": str(host / "libdeps"),
            "PLATFORMIO_SHARED_DIR": str(host / "shared"),
        }
    )

    closed, report = dependency_closure.build_closed_environment(artifact, env)
    packaged_pio = artifact / "runtime" / "platformio"
    check(
        "closure records external state root",
        Path(closed[runtime_paths.STATE_ROOT_ENV]).resolve() == state.resolve(),
    )
    check("closure evidence marks state external", report.state_root == state.resolve())
    check(
        "PlatformIO core service data is external",
        _inside(closed["PLATFORMIO_CORE_DIR"], state),
    )
    check(
        "PlatformIO core service data is not in release",
        not _inside(closed["PLATFORMIO_CORE_DIR"], artifact),
    )
    check(
        "PlatformIO platforms remain bundled",
        Path(closed["PLATFORMIO_PLATFORMS_DIR"]).resolve()
        == (packaged_pio / "platforms").resolve(),
    )
    check(
        "PlatformIO packages remain bundled",
        Path(closed["PLATFORMIO_PACKAGES_DIR"]).resolve()
        == (packaged_pio / "packages").resolve(),
    )

    for name in dependency_closure.MUTABLE_PLATFORMIO_VARS:
        check(f"{name} is outside release", not _inside(closed[name], artifact))
        check(f"{name} is under state root", _inside(closed[name], state))
        check(
            f"host {name} override is rejected",
            Path(closed[name]).resolve() != Path(env[name]).resolve(),
        )

    project_env = build_isolation.build_environment("Bài học số 01", closed)
    reclosed, _ = dependency_closure.build_closed_environment(artifact, project_env)
    for name in (
        "PLATFORMIO_WORKSPACE_DIR",
        "PLATFORMIO_BUILD_DIR",
        "PLATFORMIO_LIBDEPS_DIR",
        "PLATFORMIO_CACHE_DIR",
        "PLATFORMIO_BUILD_CACHE_DIR",
        "PLATFORMIO_SHARED_DIR",
    ):
        check(
            f"trusted project {name} survives final closure",
            Path(reclosed[name]).resolve() == Path(project_env[name]).resolve(),
        )
    return artifact, state, reclosed, tool


def test_final_process_boundary(base: Path) -> None:
    artifact, state, env, tool = test_dependency_and_platformio_state_split(base)
    unrelated = base / "Unrelated CWD"
    unrelated.mkdir(parents=True)

    # Junction provisioning uses subprocess.run(), which itself uses Popen.
    # Build the real dependency aliases before this test replaces Popen with a
    # fake process boundary, then let run_process() re-seal and reuse them.
    aliased = deployment_runtime.prepare_platformio_dependency_aliases(artifact, env)
    packaged_pio = artifact / "runtime" / "platformio"
    if os.name == "nt":
        alias_root = Path(
            aliased[deployment_runtime.PLATFORMIO_DEPENDENCY_ALIAS_ROOT_ENV]
        ).resolve()
        check(
            "final boundary short-path alias root stays external",
            not _inside(alias_root, artifact),
        )
        check(
            "final boundary package alias resolves to bundled packages",
            Path(aliased["PLATFORMIO_PACKAGES_DIR"]).resolve()
            == (packaged_pio / "packages").resolve(),
        )
        check(
            "final boundary platform alias resolves to bundled platforms",
            Path(aliased["PLATFORMIO_PLATFORMS_DIR"]).resolve()
            == (packaged_pio / "platforms").resolve(),
        )

    captured: list[dict[str, str]] = []

    class FakePopen:
        def __init__(self, command, **kwargs):
            self.command = command
            self.returncode = 0
            self.stdout = io.StringIO("b23-boundary\n")
            captured.append(dict(kwargs["env"]))

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    original_root = deployment_runtime.application_root
    original_popen = deployment_runtime.subprocess.Popen
    try:
        deployment_runtime.application_root = lambda: artifact
        deployment_runtime.subprocess.Popen = FakePopen
        result = deployment_runtime.run_process(
            [str(tool)], cwd=unrelated, env=aliased, timeout=1.0
        )
    finally:
        deployment_runtime.application_root = original_root
        deployment_runtime.subprocess.Popen = original_popen

    check("final process boundary succeeds from unrelated cwd", result.returncode == 0)
    spawned = captured[-1]
    check(
        "final process keeps external state root",
        Path(spawned[runtime_paths.STATE_ROOT_ENV]).resolve() == state.resolve(),
    )
    check(
        "final process keeps project workspace",
        Path(spawned["PLATFORMIO_WORKSPACE_DIR"]).resolve()
        == Path(env["PLATFORMIO_WORKSPACE_DIR"]).resolve(),
    )
    check(
        "final process never restores release-local cache",
        not _inside(spawned["PLATFORMIO_CACHE_DIR"], artifact),
    )
    if os.name == "nt":
        check(
            "final process keeps package short-path alias",
            Path(spawned["PLATFORMIO_PACKAGES_DIR"]).resolve()
            == (packaged_pio / "packages").resolve(),
        )
        check(
            "final process keeps platform short-path alias",
            Path(spawned["PLATFORMIO_PLATFORMS_DIR"]).resolve()
            == (packaged_pio / "platforms").resolve(),
        )


def test_build_and_firmware_workspace_do_not_mutate_release(base: Path) -> None:
    artifact = base / "Bản phát hành Có dấu" / "Robo Studio"
    state = base / "State Có dấu" / "Người dùng"
    _prepare_artifact(artifact)
    before = _snapshot(artifact)
    env = _packaged_env(artifact, state)
    previous_env = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(env)
        workspace = build_isolation.prepare_build_workspace("Bài học số 02")
        copied = firmware_workspace.prepare_firmware_workspace(
            artifact / "firmware" / "robot-platform",
            "Bài học số 02",
        )
    finally:
        os.environ.clear()
        os.environ.update(previous_env)

    check(
        "build workspace is external",
        _inside(workspace, state) and not _inside(workspace, artifact),
    )
    check(
        "firmware workspace is copied to external state",
        _inside(copied, state) and not _inside(copied, artifact),
    )
    check("release tree is byte-for-byte unchanged", _snapshot(artifact) == before)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-b23-") as temp:
        base = Path(temp)
        test_path_relocation_and_state_contract(base / "paths")
        test_final_process_boundary(base / "boundary")
        test_build_and_firmware_workspace_do_not_mutate_release(base / "workspace")
    print("B2.3 portable path and state isolation checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
