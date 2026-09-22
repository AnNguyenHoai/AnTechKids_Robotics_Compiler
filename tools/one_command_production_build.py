"""Build the complete application-owned RoboStudio production release."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from tools import copy_run_release, first_flash_runtime_contract, production_release_assembly

FORBIDDEN_NAMES = {".git", ".venv", ".pio", "penv", "__pycache__", ".pytest_cache"}
DEPLOYMENT_MANIFEST = "deployment-runtime.json"
DEPLOYMENT_SCHEMA = "antechkids.robostudio.deployment-runtime"
DEPLOYMENT_SCHEMA_VERSION = 1


class OneCommandProductionBuildError(RuntimeError):
    pass


def _resolve(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _require_directory(path: Path, label: str) -> Path:
    path = _resolve(path)
    if not path.is_dir():
        raise OneCommandProductionBuildError(f"Missing {label}: {path}")
    return path


def _require_file(path: Path, label: str) -> Path:
    path = _resolve(path)
    if not path.is_file():
        raise OneCommandProductionBuildError(f"Missing {label}: {path}")
    return path


def _forbidden_entries(root: Path) -> list[str]:
    violations: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part.lower() in FORBIDDEN_NAMES for part in relative.parts):
            violations.append(relative.as_posix())
    return sorted(violations, key=str.lower)


def _validate_python_runtime(runtime_bin: Path) -> None:
    _require_file(runtime_bin / "python.exe", "Windows portable Python executable")
    _require_file(runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py", "PlatformIO Python module")
    violations = _forbidden_entries(runtime_bin)
    if violations:
        raise OneCommandProductionBuildError("Python runtime contains forbidden development payload: " + ", ".join(violations))


def _validate_platformio_runtime(runtime_platformio: Path) -> None:
    _require_directory(runtime_platformio / "platforms", "PlatformIO platforms")
    _require_directory(runtime_platformio / "packages", "PlatformIO packages")
    violations = _forbidden_entries(runtime_platformio)
    if violations:
        raise OneCommandProductionBuildError("PlatformIO runtime contains forbidden development payload: " + ", ".join(violations))


def _write_deployment_manifest(runtime_platformio: Path) -> Path:
    path = runtime_platformio / DEPLOYMENT_MANIFEST
    payload = {"schema": DEPLOYMENT_SCHEMA, "schema_version": DEPLOYMENT_SCHEMA_VERSION, "portable_python_required": True, "host_virtualenv_included": False, "runtime_layout": {"python": "runtime/bin/python.exe", "core_dir": "runtime/platformio"}, "platformio_core": {"required_directories": ["platforms", "packages"]}}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def validate_inputs(executable: Path, runtime_bin: Path, runtime_platformio: Path, runtime_resources: Path, version_file: Path, output: Path, firmware_root: Path) -> str:
    _require_file(executable, "RoboStudio executable")
    runtime_bin = _require_directory(runtime_bin, "application-owned portable Python")
    runtime_platformio = _require_directory(runtime_platformio, "application-owned PlatformIO runtime")
    firmware_root = _require_directory(firmware_root, "application-owned firmware project")
    _validate_python_runtime(runtime_bin)
    _validate_platformio_runtime(runtime_platformio)
    try:
        first_flash_runtime_contract.validate_esp32dev_first_flash_payload(runtime_platformio)
    except first_flash_runtime_contract.FirstFlashRuntimeContractError as exc:
        raise OneCommandProductionBuildError(f"ESP32 first-flash runtime contract failed: {exc}") from exc
    _require_directory(runtime_resources, "application resources")
    _require_file(firmware_root / "platformio.ini", "firmware platformio.ini")
    _require_file(firmware_root / "wifi_config.py", "firmware wifi_config.py")
    _require_directory(firmware_root / "main", "firmware main source")
    version = production_release_assembly._read_version(_resolve(version_file))
    output = _resolve(output)
    for source in (_resolve(executable).parent, runtime_bin, runtime_platformio, _resolve(runtime_resources), firmware_root):
        try:
            output.relative_to(source)
        except ValueError:
            continue
        raise OneCommandProductionBuildError(f"Production output must not be inside an input source: {output}")
    return version


def build(executable: Path, runtime_bin: Path, runtime_platformio: Path, runtime_resources: Path, version_file: Path, source_revision: str, output: Path, firmware_root: Path) -> dict[str, object]:
    version = validate_inputs(executable, runtime_bin, runtime_platformio, runtime_resources, version_file, output, firmware_root)
    staging = _resolve(output).parent / f".rsd25-runtime-{version}"
    if staging.exists():
        import shutil
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        import shutil
        staged_bin = staging / "bin"
        staged_platformio = staging / "platformio"
        shutil.copytree(_resolve(runtime_bin), staged_bin)
        shutil.copytree(_resolve(runtime_platformio), staged_platformio)
        _write_deployment_manifest(staged_platformio)
        result = production_release_assembly.assemble_release(production_release_assembly.ProductionReleaseInputs(executable=_resolve(executable), runtime_resources=_resolve(runtime_resources), version_file=_resolve(version_file), source_revision=source_revision, runtime_bin=staged_bin, runtime_platformio=staged_platformio, firmware_root=_resolve(firmware_root)), _resolve(output))
        try:
            result = copy_run_release.finalize_assembly_result(result, source_revision=source_revision)
        except copy_run_release.CopyRunReleaseError as exc:
            raise OneCommandProductionBuildError(f"B2.6 copy-and-run finalization failed: {exc}") from exc
        result["rsd25"] = {"status": "PASS", "runtime_model": "application-owned", "portable_python": "runtime/bin/python.exe", "platformio": "runtime/platformio", "firmware": "firmware/robot-platform", "target_machine_host_toolchain_required": False}
        result["b2_6"] = dict(result.get("b2_6", {}), canonical_release_path=True)
        return result
    finally:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)


def _source_revision(value: str | None) -> str:
    if value and value.strip():
        return value.strip()
    env = os.environ.get("RSD_SOURCE_REVISION", "").strip()
    if env:
        return env
    raise OneCommandProductionBuildError("Source revision is required; pass --source-revision or set RSD_SOURCE_REVISION.")


def main() -> int:
    parser = argparse.ArgumentParser(description="RSD-25/B2.6 one-command application-owned copy-and-run RoboStudio production build")
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--runtime-bin", required=True, type=Path)
    parser.add_argument("--runtime-platformio", required=True, type=Path)
    parser.add_argument("--runtime-resources", required=True, type=Path)
    parser.add_argument("--firmware-root", type=Path, default=Path(__file__).resolve().parents[1] / "robot-platform")
    parser.add_argument("--version-file", type=Path, default=Path(__file__).resolve().parents[1] / "VERSION")
    parser.add_argument("--source-revision")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "releases" / "production")
    args = parser.parse_args()
    try:
        result = build(args.executable, args.runtime_bin, args.runtime_platformio, args.runtime_resources, args.version_file, _source_revision(args.source_revision), args.output, args.firmware_root)
    except OneCommandProductionBuildError as exc:
        print(f"RSD-25/B2.6 one-command production build: FAIL: {exc}", file=sys.stderr)
        return 1
    print("RSD-25/B2.6 one-command production build: PASS")
    print(f"Artifact: {result['artifact']}")
    print(f"SHA-256: {result['artifact_sha256']}")
    print("Delivery model: copy-extract-run")
    print("Copy-run contract: copy-run-contract.json")
    print("Bundled Python: runtime/bin/python.exe")
    print("Bundled PlatformIO: runtime/platformio")
    print("Firmware: firmware/robot-platform")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
