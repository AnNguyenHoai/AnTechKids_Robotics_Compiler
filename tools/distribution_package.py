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
DEVELOPER_PAYLOAD_NAMES = frozenset({
    ".git",
    ".github",
    ".pio",
    "penv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
})
ESPTOOL_FIRMWARE_HELPERS = ("esptool_path_fix.py", "esptool_runner.py")


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
    """Copy a runtime tree while removing dependency/developer metadata.

    Third-party PlatformIO/Python packages can legitimately ship repository
    metadata such as ``.github/workflows``. Those files are not executable
    runtime dependencies and may contain CI-machine paths (for example
    ``/home/...``), so they must not cross the production artifact boundary.
    """
    if not source.is_dir():
        raise DistributionPackageError(f"Missing distribution input {label}: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(*DEVELOPER_PAYLOAD_NAMES)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            if item.name.lower() in DEVELOPER_PAYLOAD_NAMES:
                continue
            shutil.copytree(item, target, dirs_exist_ok=True, ignore=ignore)
        elif item.is_file():
            shutil.copy2(item, target)


def _firmware_esptool_helpers_required(source: Path) -> bool:
    platformio = source / "platformio.ini"
    if not platformio.is_file():
        return False
    try:
        text = platformio.read_text(encoding="utf-8")
    except OSError:
        return False
    return "esptool_path_fix.py" in text or (source / "esptool_path_fix.py").is_file()


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

    if _firmware_esptool_helpers_required(source):
        missing_helpers = [name for name in ESPTOOL_FIRMWARE_HELPERS if not (source / name).is_file()]
        if missing_helpers:
            raise DistributionPackageError(
                "Production firmware esptool integration is incomplete: " + ", ".join(missing_helpers)
            )

    allowed_top_level = {"platformio.ini", "wifi_config.py", "main", *ESPTOOL_FIRMWARE_HELPERS}
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if any(part.lower() in DEVELOPER_PAYLOAD_NAMES for part in relative.parts):
            continue
        if relative.parts[0] not in allowed_top_level:
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    if any(
        part.lower() in DEVELOPER_PAYLOAD_NAMES
        for path in destination.rglob("*")
        for part in path.relative_to(destination).parts
    ):
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
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_entries(root: Path) -> list[dict[str, object]]:
    excluded = {DISTRIBUTION_MANIFEST, production_artifact_boundary.BOUNDARY_MANIFEST}
    return [
        {"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": _sha256(p)}
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name not in excluded
    ]


def _copy_application_metadata(executable: Path, output: Path) -> None:
    version = executable.parent / runtime_integrity.APPLICATION_VERSION_FILE
    if version.is_file():
        shutil.copy2(version, output / runtime_integrity.APPLICATION_VERSION_FILE)


def _copy_application_dependencies(executable: Path, output: Path) -> None:
    for dependency in sorted(executable.parent.glob("*.dll"), key=lambda item: item.name.lower()):
        if dependency.is_file():
            shutil.copy2(dependency, output / dependency.name)


def _copy_launcher(launcher: Path | None, output: Path) -> None:
    if launcher is None:
        return
    launcher = Path(launcher).resolve()
    if not launcher.is_file():
        raise DistributionPackageError(f"Missing production launcher: {launcher}")
    if launcher.suffix.lower() not in {".cmd", ".bat"}:
        raise DistributionPackageError(f"Unsupported production launcher type: {launcher.name}")
    shutil.copy2(launcher, output / launcher.name)


def _copy_compiler(compiler_root: Path | None, frontend_root: Path | None, output: Path) -> None:
    if compiler_root is None:
        raise DistributionPackageError("Production distribution requires application-owned compiler")
    source = Path(compiler_root).resolve()
    if not source.is_dir():
        raise DistributionPackageError(f"Missing application-owned compiler: {source}")
    if not (source / "main.py").is_file() or not (source / "compiler").is_dir():
        raise DistributionPackageError("Compiler root must contain main.py and compiler/")
    destination = output / "compiler"
    if destination.exists():
        raise DistributionPackageError(f"Compiler destination already exists: {destination}")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*DEVELOPER_PAYLOAD_NAMES))
    if frontend_root is not None:
        frontend = Path(frontend_root).resolve()
        if not frontend.is_dir():
            raise DistributionPackageError(f"Missing RoboSim frontend: {frontend}")
        frontend_destination = destination / "frontend"
        if frontend_destination.exists():
            raise DistributionPackageError(f"Compiler source already contains frontend payload: {frontend_destination}")
        shutil.copytree(frontend, frontend_destination, ignore=shutil.ignore_patterns(*DEVELOPER_PAYLOAD_NAMES))


def _validate_production_runtime(inputs: DistributionInputs) -> None:
    if inputs.runtime_bin is None or inputs.runtime_platformio is None:
        raise DistributionPackageError("Production distribution requires application-owned Python and PlatformIO runtimes")
    python = Path(inputs.runtime_bin).resolve() / "python.exe"
    if not python.is_file():
        raise DistributionPackageError(f"Bundled Windows Python is missing: {python}")
    platformio = Path(inputs.runtime_platformio).resolve()
    for directory in ("platforms", "packages"):
        if not (platformio / directory).is_dir():
            raise DistributionPackageError(f"Bundled PlatformIO {directory} directory is missing")
    manifest = platformio / "deployment-runtime.json"
    if not manifest.is_file():
        raise DistributionPackageError(f"Bundled PlatformIO deployment manifest is missing: {manifest}")


def _validate_legacy_runtime_inputs(inputs: DistributionInputs) -> None:
    if inputs.runtime_bin is None or inputs.runtime_platformio is None or inputs.runtime_resources is None:
        raise DistributionPackageError("Legacy distribution assembly requires runtime_bin, runtime_platformio, and runtime_resources")


def assemble_distribution(inputs: DistributionInputs, output: Path) -> Path:
    output = Path(output).resolve()
    if output.exists():
        if not output.is_dir():
            raise DistributionPackageError(f"Distribution output is not a directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    executable = Path(inputs.executable).resolve()
    if not executable.is_file():
        raise DistributionPackageError(f"Missing RoboStudio executable: {executable}")
    shutil.copy2(executable, output / executable.name)
    _copy_application_dependencies(executable, output)
    _copy_application_metadata(executable, output)

    if inputs.production_boundary:
        if inputs.runtime_resources is None:
            raise DistributionPackageError("Production artifact assembly requires application resources")
        if inputs.firmware_root is None:
            raise DistributionPackageError("Production artifact assembly requires application-owned firmware project")
        if inputs.deployment_tools_root is None:
            raise DistributionPackageError("Production artifact assembly requires application-owned deployment tools")
        _validate_production_runtime(inputs)
        _copy_launcher(inputs.launcher, output)
        _copy_compiler(inputs.compiler_root, inputs.frontend_root, output)
        _copy_tree(Path(inputs.runtime_bin), output / "runtime" / "bin", "portable Python")
        _copy_tree(Path(inputs.runtime_platformio), output / "runtime" / "platformio", "PlatformIO runtime")
        _copy_tree(Path(inputs.runtime_resources), output / "runtime" / "resources", "application resources")
        _copy_tree(Path(inputs.deployment_tools_root), output / "tools", "deployment runtime tools")
        _normalize_production_resources(output / "runtime" / "resources")
        runtime_resources.write_resource_manifest(output / "runtime" / "resources")
        _copy_firmware(Path(inputs.firmware_root), output / "firmware" / "robot-platform")
        try:
            production_artifact_boundary.validate_distribution_root(output)
            production_artifact_boundary.write_boundary_manifest(output)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
            raise DistributionPackageError(f"Production artifact boundary validation failed: {exc}") from exc
        portable, runtime_root = False, "runtime"
    else:
        _validate_legacy_runtime_inputs(inputs)
        _copy_tree(Path(inputs.runtime_bin), output / "runtime" / "bin", "portable Python")
        _copy_tree(Path(inputs.runtime_platformio), output / "runtime" / "platformio", "PlatformIO")
        _copy_tree(Path(inputs.runtime_resources), output / "runtime" / "resources", "runtime resources")
        runtime_resources.write_resource_manifest(output / "runtime" / "resources")
        if not (output / "runtime" / "platformio" / "deployment-runtime.json").is_file():
            raise DistributionPackageError("PlatformIO deployment manifest is missing")
        portable, runtime_root = True, "runtime"
        try:
            from tools import runtime_preflight
            runtime_preflight.validate_distribution(output)
            runtime_integrity.write_runtime_manifest(output)
        except Exception as exc:
            raise DistributionPackageError(f"Assembled distribution runtime validation failed: {exc}") from exc

    packaged_frontend = (output / "compiler" / "frontend").is_dir() if inputs.production_boundary else False
    packaged_tools = (output / "tools").is_dir() if inputs.production_boundary else False
    manifest = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "application": executable.name,
        "portable": portable,
        "artifact_model": CANONICAL_PRODUCTION_ARTIFACT_MODEL,
        "runtime_root": runtime_root,
        "production_boundary": inputs.production_boundary,
        "compiler": "compiler/main.py" if inputs.production_boundary else None,
        "compiler_contract": "compiler/robostudio_bridge.py" if inputs.production_boundary else None,
        "frontend": "compiler/frontend" if packaged_frontend else None,
        "firmware": "firmware/robot-platform" if inputs.production_boundary else None,
        "deployment_tools": "tools" if packaged_tools else None,
        "files": _file_entries(output),
    }
    manifest_path = output / DISTRIBUTION_MANIFEST
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if inputs.production_boundary:
        try:
            from tools import production_runtime_closure
            production_runtime_closure.validate_distribution(output)
        except Exception as exc:
            raise DistributionPackageError(f"Production runtime dependency closure failed: {exc}") from exc
    return manifest_path


def validate_distribution_manifest(path: Path) -> dict:
    path = Path(path)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DistributionPackageError(f"Invalid distribution manifest: {path}") from exc
    if manifest.get("schema") != SCHEMA or manifest.get("schema_version") != SCHEMA_VERSION:
        raise DistributionPackageError("Unsupported distribution manifest schema")
    root = path.parent
    entries = manifest.get("files", [])
    if not isinstance(entries, list):
        raise DistributionPackageError("Distribution manifest files must be a list")

    expected_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or "path" not in entry:
            raise DistributionPackageError("Distribution manifest contains an invalid file entry")
        relative = Path(str(entry["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise DistributionPackageError(f"Distribution manifest path escapes root: {relative}")
        normalized = relative.as_posix()
        if normalized in expected_paths:
            raise DistributionPackageError(f"Distribution manifest contains duplicate file path: {normalized}")
        expected_paths.add(normalized)
        actual = root / relative
        if not actual.is_file():
            raise DistributionPackageError(f"Distribution file is missing: {normalized}")
        if _sha256(actual) != str(entry["sha256"]):
            raise DistributionPackageError(f"Distribution file checksum mismatch: {normalized}")
        if actual.stat().st_size != int(entry["size"]):
            raise DistributionPackageError(f"Distribution file size changed: {normalized}")

    actual_paths = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file()
        and p.name not in {DISTRIBUTION_MANIFEST, production_artifact_boundary.BOUNDARY_MANIFEST}
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unexpected = sorted(actual_paths - expected_paths)
        details = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if unexpected:
            details.append("unexpected=" + ", ".join(unexpected))
        raise DistributionPackageError(
            "Distribution manifest file set does not match filesystem: " + "; ".join(details)
        )
    if manifest.get("production_boundary") is True:
        try:
            production_artifact_boundary.validate_distribution_root(root)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
            raise DistributionPackageError(f"Production artifact boundary validation failed: {exc}") from exc
        if manifest.get("artifact_model") != CANONICAL_PRODUCTION_ARTIFACT_MODEL:
            raise DistributionPackageError("Production distribution has an invalid artifact model")
        for key in ("compiler", "compiler_contract"):
            if manifest.get(key) and not (root / str(manifest[key])).is_file():
                raise DistributionPackageError(f"Production distribution {key} is missing")
        if manifest.get("frontend") and not (root / str(manifest["frontend"])).is_dir():
            raise DistributionPackageError("Production RoboSim frontend payload is missing")
        firmware_root = root / str(manifest.get("firmware") or "")
        if not manifest.get("firmware") or not (firmware_root / "platformio.ini").is_file():
            raise DistributionPackageError("Production firmware payload is missing")
        if _firmware_esptool_helpers_required(firmware_root):
            missing_helpers = [name for name in ESPTOOL_FIRMWARE_HELPERS if not (firmware_root / name).is_file()]
            if missing_helpers:
                raise DistributionPackageError(
                    "Production firmware esptool integration is incomplete: " + ", ".join(missing_helpers)
                )
        if manifest.get("deployment_tools") != "tools" or not (root / "tools").is_dir():
            raise DistributionPackageError("Production deployment runtime tools are missing")
        for relative in (
            Path("runtime/bin/python.exe"),
            Path("runtime/platformio/deployment-runtime.json"),
            Path("runtime/platformio/platforms"),
            Path("runtime/platformio/packages"),
        ):
            if not (root / relative).exists():
                raise DistributionPackageError(f"Production bundled runtime is missing: {relative.as_posix()}")
    return manifest
