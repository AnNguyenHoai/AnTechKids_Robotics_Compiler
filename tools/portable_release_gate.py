"""End-to-end acceptance gate for portable RoboStudio releases.

RSD-12 composes the existing RSD-08/09/10/11 contracts at the final release
artifact boundary. It validates the ZIP, relocates it to an unrelated
filesystem location, validates the relocated runtime, and verifies that launch
and build path resolution remain application/user owned.
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

from tools import build_isolation, distribution_launch, release_package, runtime_paths, runtime_preflight

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


def _validate_host_independence(root: Path, base_env: Mapping[str, str]) -> None:
    """Verify launch/build resolution is unaffected by hostile host settings."""
    env = distribution_launch.clean_machine_environment(root, base_env)

    expected_core = root / "runtime" / "platformio"
    if not _same_path(env["ROBOSTUDIO_HOME"], root):
        raise PortableReleaseGateError("Launch environment does not identify relocated application root")
    if not _same_path(env["PLATFORMIO_CORE_DIR"], expected_core):
        raise PortableReleaseGateError("Launch environment resolves PlatformIO outside application runtime")
    if not _same_path(env["PLATFORMIO_PLATFORMS_DIR"], expected_core / "platforms"):
        raise PortableReleaseGateError("Launch environment resolves PlatformIO platforms outside application runtime")
    if not _same_path(env["PLATFORMIO_PACKAGES_DIR"], expected_core / "packages"):
        raise PortableReleaseGateError("Launch environment resolves PlatformIO packages outside application runtime")

    # B2.2 requires production PATH closure. Keeping the hostile host PATH is
    # a release-gate failure, not a success condition.
    if "PATH" in base_env and env.get("PATH") == base_env["PATH"]:
        raise PortableReleaseGateError("Launch environment still inherits hostile host PATH")
    if env.get("ROBOSTUDIO_DEPENDENCY_MODE") != "artifact-closed":
        raise PortableReleaseGateError("Launch environment does not enforce artifact dependency closure")
    if env.get("PYTHONNOUSERSITE") != "1":
        raise PortableReleaseGateError("Launch environment does not disable host Python user-site packages")

    external_cwd = root.parent / "external-working-directory"
    external_cwd.mkdir(parents=True, exist_ok=True)
    spec = distribution_launch.build_launch_spec(root, cwd=external_cwd, base_env=base_env)
    try:
        spec.cwd.relative_to(root)
    except ValueError:
        pass
    else:
        raise PortableReleaseGateError("Packaged launch working directory is inside the application root")
    if not _same_path(spec.command[0], root / "RoboStudio.exe"):
        raise PortableReleaseGateError("Packaged launch command is not rooted at the relocated application")


def _validate_build_isolation(root: Path, base_env: Mapping[str, str]) -> Path:
    """Verify deployment build state is writable user data, not the distribution."""
    old_local = os.environ.get("LOCALAPPDATA")
    old_portable = os.environ.get(runtime_paths.PORTABLE_DATA_ENV)
    old_home = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    try:
        user_root = root.parent / "user-data"
        os.environ["LOCALAPPDATA"] = str(user_root)
        os.environ.pop(runtime_paths.PORTABLE_DATA_ENV, None)
        os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(root)
        workspace = build_isolation.build_workspace("release-acceptance")
        try:
            workspace.relative_to(root)
        except ValueError:
            pass
        else:
            raise PortableReleaseGateError("Build workspace is inside the portable application")

        env = build_isolation.build_environment("release-acceptance", base_env)
        for key in (
            build_isolation.PLATFORMIO_WORKSPACE_DIR_ENV,
            build_isolation.PLATFORMIO_BUILD_DIR_ENV,
            build_isolation.PLATFORMIO_LIBDEPS_DIR_ENV,
            build_isolation.PLATFORMIO_CACHE_DIR_ENV,
            build_isolation.PLATFORMIO_BUILD_CACHE_DIR_ENV,
            build_isolation.PLATFORMIO_SHARED_DIR_ENV,
        ):
            value = Path(env[key])
            try:
                value.relative_to(root)
            except ValueError:
                pass
            else:
                raise PortableReleaseGateError(f"Build variable {key} points inside application root")
        return workspace
    finally:
        for name, value in (
            ("LOCALAPPDATA", old_local),
            (runtime_paths.PORTABLE_DATA_ENV, old_portable),
            (runtime_paths.APPLICATION_HOME_ENV, old_home),
        ):
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _validate_relocated_runtime(root: Path, hostile_env: Mapping[str, str]) -> None:
    """Validate a relocated distribution with its application identity injected."""
    old_home = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    try:
        os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(root)
        try:
            runtime_preflight.validate_distribution(root)
        except Exception as exc:
            raise PortableReleaseGateError(f"Relocated runtime preflight failed: {exc}") from exc
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
        raise PortableReleaseGateError(f"Release artifact validation failed: {exc}") from exc

    with tempfile.TemporaryDirectory(prefix="robostudio-rsd12-") as temp:
        relocated = Path(temp) / "RelocatedRoboStudio"
        relocated.mkdir()
        try:
            with zipfile.ZipFile(artifact, "r") as archive:
                archive.extractall(relocated)
        except (OSError, zipfile.BadZipFile) as exc:
            raise PortableReleaseGateError(f"Unable to relocate release artifact: {exc}") from exc

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
            }
        )
        _validate_relocated_runtime(relocated, hostile)
        workspace = _validate_build_isolation(relocated, hostile)

        if (relocated / ".pio").exists() or (relocated / "robot-platform" / ".pio").exists():
            raise PortableReleaseGateError("Portable release contains a source-tree .pio build workspace")

        application = release_manifest.get("application")
        if not isinstance(application, str) or not application:
            raise PortableReleaseGateError("Release manifest does not declare an application")

        return PortableReleaseReport(
            artifact=artifact,
            relocated_root=relocated,
            relocation_verified=True,
            file_count=int(release_manifest.get("file_count", 0)),
            application=application,
            build_workspace=workspace,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a portable RoboStudio release")
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    report = validate_release_artifact(args.artifact, args.manifest)
    print("RSD-12 portable release gate: PASS")
    print(json.dumps({
        "schema": GATE_SCHEMA,
        "schema_version": GATE_SCHEMA_VERSION,
        "artifact": str(report.artifact),
        "application": report.application,
        "file_count": report.file_count,
        "relocation_verified": report.relocation_verified,
        "build_workspace": str(report.build_workspace),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
