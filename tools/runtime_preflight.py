"""Preflight validation for a packaged RoboStudio distribution.

The launcher must fail early and explain exactly which application-owned
runtime component is missing. This module validates the distribution layout
without consulting the current working directory, PATH, or host PlatformIO
installation. When an RSD-10 integrity manifest is present it is authoritative
for the packaged runtime bytes.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from tools import runtime_integrity, runtime_resources, runtime_paths

DEPLOYMENT_MANIFEST = "deployment-runtime.json"
RUNTIME_BIN = Path("runtime") / "bin"
RUNTIME_PLATFORMIO = Path("runtime") / "platformio"
RUNTIME_RESOURCES = Path("runtime") / "resources"


class RuntimePreflightError(RuntimeError):
    """Raised when a packaged RoboStudio distribution is incomplete."""


@dataclass(frozen=True)
class RuntimePreflightReport:
    """Machine-readable result of packaged runtime validation."""

    application_root: Path
    python: Path
    platformio: Path
    resources: Path
    deployment_manifest: Path
    resource_manifest: Path


def _require_directory(root: Path, relative: Path, label: str) -> Path:
    path = root / relative
    if not path.is_dir():
        raise RuntimePreflightError(f"RoboStudio runtime is missing {label}: {path}")
    return path


def _require_file(root: Path, relative: Path, label: str) -> Path:
    path = root / relative
    if not path.is_file():
        raise RuntimePreflightError(f"RoboStudio runtime is missing {label}: {path}")
    return path


def _python_relative_path() -> Path:
    if sys.platform == "win32":
        return RUNTIME_BIN / "python.exe"
    return RUNTIME_BIN / "python"


def _validate_deployment_manifest(path: Path, platformio_root: Path) -> None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimePreflightError(
            f"Unable to load deployment runtime manifest: {exc}"
        ) from exc

    if manifest.get("schema") != "antechkids.robostudio.deployment-runtime":
        raise RuntimePreflightError("Unsupported deployment runtime manifest schema")
    if manifest.get("schema_version") != 1:
        raise RuntimePreflightError("Unsupported deployment runtime manifest version")
    if manifest.get("portable_python_required") is not True:
        raise RuntimePreflightError("Deployment manifest must require portable Python")
    if manifest.get("host_virtualenv_included") is not False:
        raise RuntimePreflightError("Deployment manifest must exclude host virtualenv")

    layout = manifest.get("runtime_layout", {})
    if layout.get("core_dir") != "runtime/platformio":
        raise RuntimePreflightError("Deployment manifest has an invalid PlatformIO core path")
    if layout.get("python") != "runtime/bin/python.exe" and sys.platform == "win32":
        raise RuntimePreflightError("Deployment manifest has an invalid Windows Python path")

    required = manifest.get("platformio_core", {}).get("required_directories", [])
    for directory in ("platforms", "packages"):
        if directory not in required or not (platformio_root / directory).is_dir():
            raise RuntimePreflightError(
                f"RoboStudio deployment runtime is missing PlatformIO {directory}: "
                f"{platformio_root / directory}"
            )

    if (platformio_root / "penv").exists():
        raise RuntimePreflightError(
            f"RoboStudio deployment runtime contains host-specific penv: {platformio_root / 'penv'}"
        )


def validate_distribution(root: Path | None = None) -> RuntimePreflightReport:
    """Validate a complete application-owned packaged runtime.

    The supplied root is treated as an application identity. No path is
    resolved from the process CWD and no executable is searched through PATH.
    """
    application_root = Path(root) if root is not None else runtime_paths.application_root()
    application_root = application_root.expanduser()
    if not application_root.is_dir():
        raise RuntimePreflightError(
            f"RoboStudio application root does not exist: {application_root}"
        )

    python = _require_file(application_root, _python_relative_path(), "portable Python")
    platformio = _require_directory(application_root, RUNTIME_PLATFORMIO, "PlatformIO runtime")
    _require_directory(application_root, RUNTIME_PLATFORMIO / "platforms", "PlatformIO platforms")
    _require_directory(application_root, RUNTIME_PLATFORMIO / "packages", "PlatformIO packages")
    resources = _require_directory(application_root, RUNTIME_RESOURCES, "runtime resources")

    deployment_manifest = _require_file(
        platformio, Path(DEPLOYMENT_MANIFEST), "deployment runtime manifest"
    )
    _validate_deployment_manifest(deployment_manifest, platformio)

    resource_manifest = _require_file(
        resources, runtime_resources.RESOURCE_MANIFEST_NAME, "resource manifest"
    )
    try:
        runtime_resources.validate_resource_manifest(resource_manifest)
    except runtime_resources.RuntimeResourceError as exc:
        raise RuntimePreflightError(str(exc)) from exc

    # RSD-10 manifests are generated by the distribution assembler. Keep the
    # pre-RSD-10 hand-built fixture layout valid, but whenever the manifest is
    # present its component fingerprints and file digests become mandatory.
    integrity_manifest = application_root / "runtime" / runtime_integrity.MANIFEST_NAME
    if integrity_manifest.is_file():
        try:
            runtime_integrity.validate_runtime_manifest(integrity_manifest)
        except runtime_integrity.RuntimeIntegrityError as exc:
            raise RuntimePreflightError(str(exc)) from exc

    target_profile = runtime_resources.resolve_resource("target_profiles", required=True)
    if target_profile is None or not target_profile.is_file():
        raise RuntimePreflightError("Required target profile resource is unavailable")

    return RuntimePreflightReport(
        application_root=application_root,
        python=python,
        platformio=platformio,
        resources=resources,
        deployment_manifest=deployment_manifest,
        resource_manifest=resource_manifest,
    )


if __name__ == "__main__":
    report = validate_distribution()
    print("RoboStudio packaged runtime: PASS")
    print(f"Application root: {report.application_root}")
    print(f"Portable Python: {report.python}")
    print(f"PlatformIO runtime: {report.platformio}")
    print(f"Resources: {report.resources}")
