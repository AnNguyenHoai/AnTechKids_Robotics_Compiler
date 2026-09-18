"""End-to-end acceptance gate for portable RoboStudio releases.

RSD-12 composes the existing release contracts at the final artifact boundary.
It validates the ZIP, relocates it to an unrelated filesystem location, then
verifies that immutable dependencies resolve from the artifact while all
mutable build/PlatformIO state resolves to an external user-owned state root.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from tools import (
    build_isolation,
    distribution_launch,
    release_package,
    runtime_paths,
    runtime_preflight,
)

GATE_SCHEMA = "antechkids.robostudio.portable-release-gate"
GATE_SCHEMA_VERSION = 1


class PortableReleaseGateError(RuntimeError):
    """Raised when a release fails the portable clean-machine acceptance gate."""


@dataclass(frozen=True)
class PortableReleaseReport:
    """Machine-readable result of the RSD-12 acceptance gate."""

    artifact: Path
    relocated_root: Path
    relocation_verified: bool
    file_count: int
    application: str
    build_workspace: Path


def _same_path(left: Path | str, right: Path | str) -> bool:
    """Compare filesystem identity using Windows-safe canonical semantics."""
    return os.path.normcase(os.path.realpath(os.path.abspath(str(left)))) == os.path.normcase(
        os.path.realpath(os.path.abspath(str(right)))
    )


def _inside(path: Path | str, root: Path | str) -> bool:
    candidate = Path(path).resolve()
    parent = Path(root).resolve()
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_host_independence(root: Path, base_env: Mapping[str, str]) -> None:
    """Verify dependency and state resolution ignores hostile host settings."""
    env = distribution_launch.clean_machine_environment(root, base_env)
    packaged_platformio = root / "runtime" / "platformio"
    state_root = Path(env[runtime_paths.STATE_ROOT_ENV])

    if not _same_path(env["ROBOSTUDIO_HOME"], root):
        raise PortableReleaseGateError(
            "Launch environment does not identify relocated application root"
        )
    if _inside(state_root, root):
        raise PortableReleaseGateError("RoboStudio mutable state is inside the application root")
    if not _inside(env["PLATFORMIO_CORE_DIR"], state_root):
        raise PortableReleaseGateError(
            "Launch environment does not isolate PlatformIO core state under external user state"
        )
    if _inside(env["PLATFORMIO_CORE_DIR"], root):
        raise PortableReleaseGateError("Launch environment writes PlatformIO core state into release")
    if not _same_path(
        env["PLATFORMIO_PLATFORMS_DIR"], packaged_platformio / "platforms"
    ):
        raise PortableReleaseGateError(
            "Launch environment resolves PlatformIO platforms outside application runtime"
        )
    if not _same_path(
        env["PLATFORMIO_PACKAGES_DIR"], packaged_platformio / "packages"
    ):
        raise PortableReleaseGateError(
            "Launch environment resolves PlatformIO packages outside application runtime"
        )

    if "PATH" in base_env and env.get("PATH") == base_env["PATH"]:
        raise PortableReleaseGateError("Launch environment still inherits hostile host PATH")
    if env.get("ROBOSTUDIO_DEPENDENCY_MODE") != "artifact-closed":
        raise PortableReleaseGateError(
            "Launch environment does not enforce artifact dependency closure"
        )
    if env.get("PYTHONNOUSERSITE") != "1":
        raise PortableReleaseGateError(
            "Launch environment does not disable host Python user-site packages"
        )

    external_cwd = root.parent / "external-working-directory"
    external_cwd.mkdir(parents=True, exist_ok=True)
    spec = distribution_launch.build_launch_spec(
        root, cwd=external_cwd, base_env=base_env
    )
    if _inside(spec.cwd, root):
        raise PortableReleaseGateError(
            "Packaged launch working directory is inside the application root"
        )
    if not _same_path(spec.command[0], root / "RoboStudio.exe"):
        raise PortableReleaseGateError(
            "Packaged launch command is not rooted at the relocated application"
        )


def _validate_build_isolation(root: Path, base_env: Mapping[str, str]) -> Path:
    """Verify generated build state stays below the declared external state root."""
    env = dict(base_env)
    state_root = root.parent / "user-data"
    env[runtime_paths.APPLICATION_HOME_ENV] = str(root)
    env[runtime_paths.STATE_ROOT_ENV] = str(state_root)
    env[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
    env[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"
    env.pop(runtime_paths.PORTABLE_DATA_ENV, None)

    workspace = build_isolation.build_workspace("release-acceptance", base_env=env)
    if _inside(workspace, root):
        raise PortableReleaseGateError("Build workspace is inside the portable application")
    if not _inside(workspace, state_root):
        raise PortableReleaseGateError("Build workspace is outside declared RoboStudio user state")

    isolated = build_isolation.build_environment("release-acceptance", env)
    for key in (
        build_isolation.PLATFORMIO_WORKSPACE_DIR_ENV,
        build_isolation.PLATFORMIO_BUILD_DIR_ENV,
        build_isolation.PLATFORMIO_LIBDEPS_DIR_ENV,
        build_isolation.PLATFORMIO_CACHE_DIR_ENV,
        build_isolation.PLATFORMIO_BUILD_CACHE_DIR_ENV,
        build_isolation.PLATFORMIO_SHARED_DIR_ENV,
    ):
        value = Path(isolated[key])
        if _inside(value, root):
            raise PortableReleaseGateError(
                f"Build variable {key} points inside application root"
            )
        if not _inside(value, state_root):
            raise PortableReleaseGateError(
                f"Build variable {key} escaped declared RoboStudio user state"
            )
    return workspace


def _validate_relocated_runtime(root: Path, hostile_env: Mapping[str, str]) -> None:
    """Validate a relocated distribution with its application identity injected."""
    old_home = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    try:
        os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(root)
        try:
            runtime_preflight.validate_distribution(root)
        except Exception as exc:
            raise PortableReleaseGateError(
                f"Relocated runtime preflight failed: {exc}"
            ) from exc
        _validate_host_independence(root, hostile_env)
    finally:
        if old_home is None:
            os.environ.pop(runtime_paths.APPLICATION_HOME_ENV, None)
        else:
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = old_home


def validate_release_artifact(
    artifact: Path,
    manifest: Path | None = None,
    *,
    base_env: Mapping[str, str] | None = None,
) -> PortableReleaseReport:
    """Validate a release ZIP as a relocatable clean-machine distribution."""
    artifact = Path(artifact).resolve()
    try:
        release_manifest = release_package.validate_release_artifact(artifact, manifest)
    except release_package.ReleasePackageError as exc:
        raise PortableReleaseGateError(
            f"Release artifact validation failed: {exc}"
        ) from exc

    with tempfile.TemporaryDirectory(prefix="robostudio-rsd12-") as temp:
        relocated = Path(temp) / "Relocated RoboStudio Ứng dụng"
        relocated.mkdir()
        try:
            with zipfile.ZipFile(artifact, "r") as archive:
                archive.extractall(relocated)
        except (OSError, zipfile.BadZipFile) as exc:
            raise PortableReleaseGateError(
                f"Unable to relocate release artifact: {exc}"
            ) from exc

        hostile = dict(os.environ if base_env is None else base_env)
        hostile.update(
            {
                "PYTHONHOME": "C:\\HostPython",
                "PYTHONPATH": "C:\\HostProject",
                "VIRTUAL_ENV": "C:\\HostVenv",
                "PIOHOME_DIR": "C:\\HostPlatformIO",
                "PLATFORMIO_CORE_DIR": "C:\\HostPlatformIO",
                "PLATFORMIO_PLATFORMS_DIR": "C:\\HostPlatforms",
                "PLATFORMIO_PACKAGES_DIR": "C:\\HostPackages",
                "PLATFORMIO_WORKSPACE_DIR": "C:\\HostWorkspace",
                "PLATFORMIO_CACHE_DIR": "C:\\HostCache",
                runtime_paths.STATE_ROOT_ENV: str(Path(temp) / "User State Nguyễn An"),
            }
        )
        _validate_relocated_runtime(relocated, hostile)
        workspace = _validate_build_isolation(relocated, hostile)

        if (relocated / ".pio").exists() or (
            relocated / "robot-platform" / ".pio"
        ).exists():
            raise PortableReleaseGateError(
                "Portable release contains a source-tree .pio build workspace"
            )

        application = release_manifest.get("application")
        if not isinstance(application, str) or not application:
            raise PortableReleaseGateError(
                "Release manifest does not declare an application"
            )

        return PortableReleaseReport(
            artifact=artifact,
            relocated_root=relocated,
            relocation_verified=True,
            file_count=int(release_manifest.get("file_count", 0)),
            application=application,
            build_workspace=workspace,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a portable RoboStudio release"
    )
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    report = validate_release_artifact(args.artifact, args.manifest)
    print("RSD-12 portable release gate: PASS")
    print(
        json.dumps(
            {
                "schema": GATE_SCHEMA,
                "schema_version": GATE_SCHEMA_VERSION,
                "artifact": str(report.artifact),
                "application": report.application,
                "file_count": report.file_count,
                "relocation_verified": report.relocation_verified,
                "build_workspace": str(report.build_workspace),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
