"""Assemble and validate RoboStudio distribution payloads."""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from tools import production_artifact_boundary, runtime_integrity, runtime_resources

DISTRIBUTION_MANIFEST = "distribution-manifest.json"
SCHEMA = "antechkids.robostudio.distribution"
SCHEMA_VERSION = 2
CANONICAL_PRODUCTION_ARTIFACT_MODEL = "RoboStudio + Compiler + Application-Owned Runtime"


class DistributionPackageError(RuntimeError):
    pass


@dataclass(frozen=True)
class DistributionInputs:
    executable: Path
    runtime_bin: Path | None = None
    runtime_platformio: Path | None = None
    runtime_resources: Path | None = None
    production_boundary: bool = False
    launcher: Path | None = None
    compiler_root: Path | None = None
    frontend_root: Path | None = None
    firmware_root: Path | None = None
    deployment_tools_root: Path | None = None


def _copy_tree(source: Path, destination: Path, label: str) -> None:
    if not source.is_dir():
        raise DistributionPackageError(f"Missing distribution input {label}: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            if item.name.lower() in {"penv", ".venv", ".pio", ".git"}:
                raise DistributionPackageError(f"Host/development state is not allowed: {item}")
            shutil.copytree(item, target, dirs_exist_ok=True)
        elif item.is_file():
            shutil.copy2(item, target)


def _copy_firmware(source: Path, destination: Path) -> None:
    """Copy only the firmware project inputs needed by PlatformIO."""
    source = Path(source).resolve()
    if not source.is_dir():
        raise DistributionPackageError(f"Missing production firmware project: {source}")
    if not (source / "platformio.ini").is_file():
        raise DistributionPackageError("Production firmware project must contain platformio.ini")
    if not (source / "wifi_config.py").is_file():
        raise DistributionPackageError("Production firmware project must contain wifi_config.py")
    if not (source / "main").is_dir():
        raise DistributionPackageError("Production firmware project must contain main/")
    forbidden = {".git", ".pio", "penv", ".venv", "__pycache__", ".pytest_cache"}
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if any(part.lower() in forbidden for part in relative.parts):
            continue
        if relative.parts[0] not in {"platformio.ini", "wifi_config.py", "main"}:
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    if any(part.lower() in forbidden for path in destination.rglob("*") for part in path.relative_to(destination).parts):
        raise DistributionPackageError("Production firmware contains forbidden development payload")


def _normalize_production_resources(destination: Path) -> None:
    canonical = destination / "robot-isa" / "target_profiles.json"
    legacy = destination / "target_profiles.json"
    if canonical.is_file():
        if legacy.exists():
            if legacy.is_dir():
                raise DistributionPackageError("Conflicting production resource layouts: target_profiles.json")
            legacy.unlink()
    elif legacy.is_file():
        canonical.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy), str(canonical))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: path.read_bytes() if False else b"", b""):
            digest.update(chunk)
    return digest.hexdigest()
