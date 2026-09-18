"""RSD-25 production runtime dependency closure enforcement."""
from __future__ import annotations

import json
from pathlib import Path

from tools import distribution_package, production_artifact_boundary, production_platformio_closure, runtime_resources

SCHEMA = "antechkids.robostudio.production-runtime-closure"
SCHEMA_VERSION = 4
FORBIDDEN_NAMES = frozenset({".git", ".venv", ".pio", "penv", "__pycache__", ".pytest_cache"})

# Production deployment/acceptance helpers belong to the release runtime
# boundary. Keep this list explicit so closure fails even if a custom packager
# accidentally omits a USB/clean-machine dependency from its manifest.
REQUIRED_DEPLOYMENT_TOOL_FILES: tuple[str, ...] = (
    "bootstrap_config.py",
    "build_isolation.py",
    "clean_machine_physical_e2e.py",
    "dependency_closure.py",
    "deploy_robot.py",
    "deployment_contract.py",
    "deployment_runtime.py",
    "firmware_workspace.py",
    "hardware_preflight.py",
    "runtime_paths.py",
    "runtime_resources.py",
    "target_machine_prerequisites.py",
    "target_machine_qualification.py",
)


def _required_paths(application: str) -> tuple[Path, ...]:
    return (
        Path(application), Path("VERSION"),
        Path("compiler") / "main.py", Path("compiler") / "robostudio_bridge.py",
        Path("compiler") / "compiler", Path("compiler") / "frontend" / "__init__.py",
        Path("compiler") / "frontend" / "rewriter.py",
        Path("runtime") / "bin" / "python.exe",
        Path("runtime") / "bin" / "Lib" / "site-packages" / "platformio" / "__init__.py",
        Path("runtime") / "platformio" / "deployment-runtime.json",
        Path("runtime") / "platformio" / "platforms", Path("runtime") / "platformio" / "packages",
        Path("runtime") / "resources" / runtime_resources.RESOURCE_MANIFEST_NAME,
        Path("runtime") / "resources" / "robot-isa" / "target_profiles.json",
        Path("firmware") / "robot-platform" / "platformio.ini",
        Path("firmware") / "robot-platform" / "wifi_config.py",
        Path("firmware") / "robot-platform" / "main",
        *(Path("tools") / name for name in REQUIRED_DEPLOYMENT_TOOL_FILES),
    )


def _payload_files(root: Path) -> set[str]:
    excluded = {distribution_package.DISTRIBUTION_MANIFEST, production_artifact_boundary.BOUNDARY_MANIFEST, "production-runtime-closure.json"}
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name not in excluded}


def _manifest_files(manifest: dict) -> set[str]:
    result: set[str] = set()
    for entry in manifest.get("files", []):
        relative = Path(str(entry.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"Distribution manifest path escapes root: {relative}")
        result.add(relative.as_posix())
    return result


def _validate_forbidden_payload(root: Path) -> list[str]:
    violations: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part.lower() in FORBIDDEN_NAMES for part in relative.parts):
            violations.append(relative.as_posix())
    return sorted(violations, key=str.lower)


def _validate_deployment_manifest(root: Path) -> dict:
    path = root / "runtime" / "platformio" / "deployment-runtime.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid deployment runtime manifest: {path}") from exc
    if data.get("schema") != "antechkids.robostudio.deployment-runtime" or data.get("schema_version") != 1:
        raise RuntimeError("Unsupported deployment runtime manifest schema")
    if data.get("portable_python_required") is not True or data.get("host_virtualenv_included") is not False:
        raise RuntimeError("Deployment runtime manifest has an invalid ownership contract")
    layout = data.get("runtime_layout", {})
    if layout.get("python") != "runtime/bin/python.exe" or layout.get("core_dir") != "runtime/platformio":
        raise RuntimeError("Deployment runtime manifest has an invalid application-owned layout")
    required = data.get("platformio_core", {}).get("required_directories", [])
    if any(item not in required for item in ("platforms", "packages")):
        raise RuntimeError("Deployment runtime manifest must require platforms and packages")
    return data


def validate_distribution(root: Path) -> dict[str, object]:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"Production distribution not found: {root}")
    manifest = distribution_package.validate_distribution_manifest(root / distribution_package.DISTRIBUTION_MANIFEST)
    if manifest.get("production_boundary") is not True:
        raise RuntimeError("Production runtime closure requires production_boundary=true")
    application = str(manifest.get("application", "")).strip()
    if not application or Path(application).name != application or Path(application).suffix.lower() != ".exe":
        raise RuntimeError("Production distribution manifest must identify a single executable")
    missing = [path.as_posix() for path in _required_paths(application) if not (root / path).exists()]
    if missing:
        raise RuntimeError("Production runtime closure is missing: " + ", ".join(missing))
    _validate_deployment_manifest(root)
    if manifest.get("firmware") != "firmware/robot-platform":
        raise RuntimeError("Production distribution manifest must identify the packaged firmware project")

    manifest_files = _manifest_files(manifest)
    payload_files = _payload_files(root)
    untracked = sorted(payload_files - manifest_files, key=str.lower)
    if untracked:
        raise RuntimeError("Production payload is not covered by distribution manifest: " + ", ".join(untracked))
    missing_inventory = sorted(manifest_files - payload_files, key=str.lower)
    if missing_inventory:
        raise RuntimeError("Distribution manifest references missing payload files: " + ", ".join(missing_inventory))
    forbidden = _validate_forbidden_payload(root)
    if forbidden:
        raise RuntimeError("Production runtime closure contains developer-only payload: " + ", ".join(forbidden))
    resource_manifest = runtime_resources.validate_resource_manifest(root / "runtime" / "resources" / runtime_resources.RESOURCE_MANIFEST_NAME)
    try:
        platformio_evidence = production_platformio_closure.validate_distribution(root)
    except production_platformio_closure.ProductionPlatformIOClosureError as exc:
        raise RuntimeError(f"Production PlatformIO dependency closure failed: {exc}") from exc
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "application": application,
        "required_paths": [p.as_posix() for p in _required_paths(application)],
        "payload_file_count": len(payload_files),
        "runtime_resource_manifest": resource_manifest["schema"],
        "production_boundary": True,
        "runtime_model": "application-owned",
        "firmware_model": "packaged-project",
        "platformio_dependency_closure": platformio_evidence,
    }


def write_evidence(root: Path, output: Path | None = None) -> Path:
    root = Path(root).expanduser().resolve()
    evidence = validate_distribution(root)
    path = Path(output) if output is not None else root / "production-runtime-closure.json"
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return path
