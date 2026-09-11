"""Clean-machine release acceptance for portable RoboStudio artifacts.

RSD-16 is the final automated acceptance boundary between a structurally valid
release ZIP and a release that can actually start its application-owned runtime
from an unrelated working directory under hostile host runtime settings.

The gate composes the existing release-package and clean-machine execution
contracts. It never installs dependencies and never modifies the source checkout.
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

from tools import clean_machine_e2e, release_package

SCHEMA = "antechkids.robostudio.clean-machine-release-acceptance"
SCHEMA_VERSION = 1


class ReleaseAcceptanceError(RuntimeError):
    """Raised when a release fails clean-machine acceptance."""


@dataclass(frozen=True)
class ReleaseAcceptanceReport:
    """Machine-readable result of RSD-16 acceptance."""

    artifact: Path
    application: str
    application_version: str
    artifact_sha256: str
    relocated_root: Path
    external_cwd: Path
    portable_python: Path
    execution_returncode: int
    executable_verified: bool
    environment_verified: bool


def _extract(artifact: Path, destination: Path) -> None:
    """Extract an already-validated release into a fresh directory."""
    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            archive.extractall(destination)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ReleaseAcceptanceError(f"Unable to extract release artifact: {exc}") from exc


def _hostile_environment(base_env: Mapping[str, str]) -> dict[str, str]:
    """Return a deterministic host environment containing conflicting runtime hints."""
    env = dict(base_env)
    env.update(
        {
            "PYTHONHOME": r"C:\HostPython",
            "PYTHONPATH": r"C:\HostProject",
            "VIRTUAL_ENV": r"C:\HostVenv",
            "CONDA_PREFIX": r"C:\HostConda",
            "CONDA_DEFAULT_ENV": "host",
            "PIOHOME_DIR": r"C:\HostPlatformIO",
            "PLATFORMIO_CORE_DIR": r"C:\HostPlatformIO",
            "PLATFORMIO_PLATFORMS_DIR": r"C:\HostPlatforms",
            "PLATFORMIO_PACKAGES_DIR": r"C:\HostPackages",
            "PLATFORMIO_CACHE_DIR": r"C:\HostCache",
            "PLATFORMIO_BUILD_CACHE_DIR": r"C:\HostBuildCache",
            "PLATFORMIO_WORKSPACE_DIR": r"C:\HostWorkspace",
        }
    )
    return env


def _validate_identity(root: Path, manifest: Mapping[str, object]) -> None:
    """Ensure the declared application exists inside the extracted release."""
    application = manifest.get("application")
    if not isinstance(application, str) or not application:
        raise ReleaseAcceptanceError("Release manifest does not declare an application")
    candidate = root / application
    if not candidate.is_file():
        raise ReleaseAcceptanceError(f"Release application is missing: {candidate}")


def accept_release(
    artifact: Path,
    *,
    base_env: Mapping[str, str] | None = None,
    timeout: float = 30.0,
) -> ReleaseAcceptanceReport:
    """Run the complete RSD-16 clean-machine acceptance gate.

    The artifact is validated before extraction. The extracted runtime is then
    executed with hostile host Python/PlatformIO variables and an external
    working directory. GUI startup and physical hardware remain outside this
    automated gate.
    """
    artifact = Path(artifact).resolve()
    if not artifact.is_file():
        raise ReleaseAcceptanceError(f"Release artifact not found: {artifact}")

    try:
        manifest = release_package.validate_release_artifact(artifact)
    except release_package.ReleasePackageError as exc:
        raise ReleaseAcceptanceError(f"Release artifact validation failed: {exc}") from exc

    application = manifest.get("application")
    application_version = manifest.get("application_version")
    if not isinstance(application, str) or not application:
        raise ReleaseAcceptanceError("Release manifest does not declare an application")
    if not isinstance(application_version, str) or not application_version:
        raise ReleaseAcceptanceError("Release manifest does not declare an application version")

    original_env = os.environ.copy()
    hostile = _hostile_environment(original_env if base_env is None else base_env)

    with tempfile.TemporaryDirectory(prefix="robostudio-rsd16-") as temp:
        workspace = Path(temp)
        relocated = workspace / "RelocatedRoboStudio"
        external_cwd = workspace / "ExternalWorkspace"
        relocated.mkdir()
        external_cwd.mkdir()
        _extract(artifact, relocated)
        _validate_identity(relocated, manifest)

        try:
            report = clean_machine_e2e.execute_clean_machine_probe(
                relocated,
                cwd=external_cwd,
                base_env=hostile,
                timeout=timeout,
            )
        except clean_machine_e2e.CleanMachineE2EError as exc:
            raise ReleaseAcceptanceError(f"Clean-machine runtime execution failed: {exc}") from exc

        if os.environ != original_env:
            raise ReleaseAcceptanceError("Clean-machine acceptance changed the caller environment")

        return ReleaseAcceptanceReport(
            artifact=artifact,
            application=application,
            application_version=application_version,
            artifact_sha256=str(manifest.get("artifact_sha256", "")),
            relocated_root=relocated,
            external_cwd=external_cwd,
            portable_python=report.python,
            execution_returncode=report.returncode,
            executable_verified=report.executable_verified,
            environment_verified=report.environment_verified,
        )


def report_to_dict(report: ReleaseAcceptanceReport) -> dict[str, object]:
    """Serialize an acceptance result without exposing injected host settings."""
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "artifact": str(report.artifact),
        "application": report.application,
        "application_version": report.application_version,
        "artifact_sha256": report.artifact_sha256,
        "relocation_verified": True,
        "external_cwd_verified": True,
        "portable_python": str(report.portable_python),
        "execution_returncode": report.execution_returncode,
        "executable_verified": report.executable_verified,
        "environment_verified": report.environment_verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Accept a portable RoboStudio release on a clean-machine boundary")
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    report = accept_release(args.artifact, timeout=args.timeout)
    print("RSD-16 clean-machine release acceptance: PASS")
    print(json.dumps(report_to_dict(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
