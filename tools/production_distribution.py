"""Build and validate the production RoboStudio distribution boundary."""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    _repository_root = Path(__file__).resolve().parent.parent
    if str(_repository_root) not in sys.path:
        sys.path.insert(0, str(_repository_root))

from tools import distribution_package

PRODUCTION_SCHEMA = "antechkids.robostudio.production-distribution"
PRODUCTION_SCHEMA_VERSION = 4
DEFAULT_VERSION_FILE = "VERSION"
LAUNCHER_NAME = "RoboStudio.cmd"
COMPILER_ROOT_NAME = "compiler"
COMPILER_ENTRY_NAME = "main.py"
FRONTEND_ROOT_NAME = "frontend"
CONTRACT_ENTRY_NAME = "robostudio_bridge.py"


class ProductionDistributionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProductionDistributionInputs:
    executable: Path
    runtime_resources: Path
    version_file: Path
    runtime_bin: Path
    runtime_platformio: Path
    compiler_root: Path | None = None
    frontend_root: Path | None = None
    firmware_root: Path | None = None


@dataclass(frozen=True)
class ProductionDistributionResult:
    distribution_root: Path
    manifest: Path
    application: str
    application_version: str


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_compiler_root() -> Path:
    return repository_root() / "robot-compiler"


def _default_frontend_root() -> Path:
    return repository_root() / "robot-frontend-robosim" / "frontend"


def _default_firmware_root() -> Path:
    return repository_root() / "robot-platform"


def _resolve_root(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _require_file(path: Path, label: str) -> Path:
    path = _resolve_root(path)
    if not path.is_file():
        raise ProductionDistributionError(f"Missing {label}: {path}")
    return path


def _require_directory(path: Path, label: str) -> Path:
    path = _resolve_root(path)
    if not path.is_dir():
        raise ProductionDistributionError(f"Missing {label}: {path}")
    return path


def _read_version(path: Path) -> str:
    value = _require_file(path, "application VERSION file").read_text(encoding="utf-8").strip()
    if not value or "\n" in value or "\r" in value:
        raise ProductionDistributionError(f"Invalid application VERSION: {path}")
    return value


def _contract_source(compiler: Path) -> Path:
    for candidate in (compiler / CONTRACT_ENTRY_NAME, compiler / "compiler" / CONTRACT_ENTRY_NAME):
        if candidate.is_file():
            return candidate
    raise ProductionDistributionError(f"Application-owned compiler contract is missing: {compiler / CONTRACT_ENTRY_NAME}")


def _validate_runtime_bin(runtime_bin: Path) -> None:
    _require_file(runtime_bin / "python.exe", "Windows portable Python executable")
    if not (runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py").is_file():
        raise ProductionDistributionError("Portable Python must contain Lib/site-packages/platformio/__init__.py")
    forbidden = {".venv", "penv", ".pio", ".git", "__pycache__", ".pytest_cache"}
    if any(part.lower() in forbidden for path in runtime_bin.rglob("*") for part in path.relative_to(runtime_bin).parts):
        raise ProductionDistributionError("Portable Python contains forbidden development payload")


def _validate_runtime_platformio(runtime_platformio: Path) -> None:
    for directory in ("platforms", "packages"):
        if not (runtime_platformio / directory).is_dir():
            raise ProductionDistributionError(f"Application-owned PlatformIO runtime is missing {directory}: {runtime_platformio / directory}")
    forbidden = {".venv", "penv", ".pio", ".git", "__pycache__", ".pytest_cache"}
    if any(part.lower() in forbidden for path in runtime_platformio.rglob("*") for part in path.relative_to(runtime_platformio).parts):
        raise ProductionDistributionError("PlatformIO runtime contains forbidden development payload")


def _validate_firmware(firmware: Path) -> None:
    _require_directory(firmware, "application-owned firmware project")
    _require_file(firmware / "platformio.ini", "firmware platformio.ini")
    _require_file(firmware / "wifi_config.py", "firmware wifi_config.py")
    _require_directory(firmware / "main", "firmware main source")
    forbidden = {".git", ".pio", "penv", ".venv", "__pycache__", ".pytest_cache"}
    if any(part.lower() in forbidden for path in firmware.rglob("*") for part in path.relative_to(firmware).parts):
        raise ProductionDistributionError("Firmware project contains forbidden development payload")


def validate_inputs(inputs: ProductionDistributionInputs, output: Path | None = None) -> str:
    executable = _require_file(inputs.executable, "RoboStudio executable")
    resources = _require_directory(inputs.runtime_resources, "application resources")
    version = _read_version(inputs.version_file)
    compiler = _require_directory(inputs.compiler_root or _default_compiler_root(), "application-owned compiler")
    frontend = _require_directory(inputs.frontend_root or _default_frontend_root(), "RoboSim frontend")
    firmware = _require_directory(inputs.firmware_root or _default_firmware_root(), "application-owned firmware project")
    runtime_bin = _require_directory(inputs.runtime_bin, "application-owned portable Python")
    runtime_platformio = _require_directory(inputs.runtime_platformio, "application-owned PlatformIO runtime")

    if not (compiler / COMPILER_ENTRY_NAME).is_file() or not (compiler / "compiler").is_dir():
        raise ProductionDistributionError("Invalid application-owned compiler: must contain main.py and compiler/")
    _contract_source(compiler)
    if not (frontend / "__init__.py").is_file() or not (frontend / "rewriter.py").is_file():
        raise ProductionDistributionError("RoboSim frontend must contain __init__.py and rewriter.py")
    _validate_firmware(firmware)
    _validate_runtime_bin(runtime_bin)
    _validate_runtime_platformio(runtime_platformio)

    if output is not None:
        output = _resolve_root(output)
        for source in (executable.parent, resources, compiler, frontend, firmware, runtime_bin, runtime_platformio):
            try:
                output.relative_to(source)
            except ValueError:
                continue
            raise ProductionDistributionError(f"Distribution output must not be inside an input source: {output}")
    return version


def _launcher_text(executable_name: str) -> str:
    return ('@echo off\r\nsetlocal\r\npushd "%~dp0"\r\n'
            + f'if not exist "{executable_name}" (\r\n'
            + f'  echo RoboStudio executable not found: "%~dp0{executable_name}" 1>&2\r\n'
            + '  popd\r\n  exit /b 1\r\n)\r\n'
            + f'"%~dp0{executable_name}" %*\r\n'
            + 'set "exit_code=%ERRORLEVEL%"\r\npopd\r\nexit /b %exit_code%\r\n')


def _stage_application(executable: Path, version_file: Path, stage: Path) -> Path:
    stage.mkdir(parents=True, exist_ok=True)
    staged = stage / executable.name
    shutil.copy2(executable, staged)
    shutil.copy2(version_file, stage / DEFAULT_VERSION_FILE)
    (stage / LAUNCHER_NAME).write_text(_launcher_text(executable.name), encoding="utf-8")
    for dependency in sorted(executable.parent.glob("*.dll"), key=lambda item: item.name.lower()):
        if dependency.is_file():
            shutil.copy2(dependency, stage / dependency.name)
    return staged


def _stage_compiler(compiler_root: Path, frontend_root: Path, stage: Path) -> Path:
    compiler = _require_directory(compiler_root, "application-owned compiler")
    frontend = _require_directory(frontend_root, "RoboSim frontend")
    destination = stage / COMPILER_ROOT_NAME
    contract_source = _contract_source(compiler)
    shutil.copytree(compiler, destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv", ".pio", "penv", CONTRACT_ENTRY_NAME))
    shutil.copy2(contract_source, destination / CONTRACT_ENTRY_NAME)
    frontend_destination = destination / FRONTEND_ROOT_NAME
    shutil.copytree(frontend, frontend_destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv", ".pio", "penv"))
    return destination


def _stage_runtime(runtime_bin: Path, runtime_platformio: Path, stage: Path) -> tuple[Path, Path]:
    bin_destination = stage / "runtime" / "bin"
    platformio_destination = stage / "runtime" / "platformio"
    shutil.copytree(_require_directory(runtime_bin, "application-owned portable Python"), bin_destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv", ".pio", "penv"))
    shutil.copytree(_require_directory(runtime_platformio, "application-owned PlatformIO runtime"), platformio_destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv", ".pio", "penv"))
    manifest = platformio_destination / "deployment-runtime.json"
    manifest.write_text('{\n  "schema": "antechkids.robostudio.deployment-runtime",\n  "schema_version": 1,\n  "portable_python_required": true,\n  "host_virtualenv_included": false,\n  "runtime_layout": {"python": "runtime/bin/python.exe", "core_dir": "runtime/platformio"},\n  "platformio_core": {"required_directories": ["platforms", "packages"]}\n}\n', encoding="utf-8")
    return bin_destination, platformio_destination


def build_production_distribution(inputs: ProductionDistributionInputs, output: Path) -> ProductionDistributionResult:
    output = _resolve_root(output)
    executable = _resolve_root(inputs.executable)
    version_file = _resolve_root(inputs.version_file)
    runtime_resources = _resolve_root(inputs.runtime_resources)
    compiler_root = _resolve_root(inputs.compiler_root or _default_compiler_root())
    frontend_root = _resolve_root(inputs.frontend_root or _default_frontend_root())
    firmware_root = _resolve_root(inputs.firmware_root or _default_firmware_root())
    validate_inputs(inputs, output)
    version = _read_version(version_file)

    with tempfile.TemporaryDirectory(prefix="robostudio-production-stage-") as temp:
        stage = Path(temp) / "application"
        staged_executable = _stage_application(executable, version_file, stage)
        compiler_stage = _stage_compiler(compiler_root, frontend_root, stage)
        _stage_runtime(inputs.runtime_bin, inputs.runtime_platformio, stage)
        try:
            manifest = distribution_package.assemble_distribution(
                distribution_package.DistributionInputs(
                    executable=staged_executable,
                    runtime_resources=runtime_resources,
                    production_boundary=True,
                    launcher=stage / LAUNCHER_NAME,
                    compiler_root=compiler_stage,
                    frontend_root=None,
                    firmware_root=firmware_root,
                    runtime_bin=stage / "runtime" / "bin",
                    runtime_platformio=stage / "runtime" / "platformio",
                ),
                output,
            )
        except distribution_package.DistributionPackageError as exc:
            raise ProductionDistributionError(f"Production distribution assembly failed: {exc}") from exc
    return ProductionDistributionResult(output, manifest, executable.name, version)


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a production RoboStudio distribution with application-owned runtime")
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--runtime-bin", required=True, type=Path)
    parser.add_argument("--runtime-platformio", required=True, type=Path)
    parser.add_argument("--runtime-resources", required=True, type=Path)
    parser.add_argument("--firmware-root", type=Path)
    parser.add_argument("--version-file", type=Path, default=repository_root() / DEFAULT_VERSION_FILE)
    parser.add_argument("--compiler-root", type=Path)
    parser.add_argument("--frontend-root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build_production_distribution(ProductionDistributionInputs(args.executable, args.runtime_resources, args.version_file, args.runtime_bin, args.runtime_platformio, args.compiler_root, args.frontend_root, args.firmware_root), args.output)
    except ProductionDistributionError as exc:
        print(f"RSD-25 production distribution: FAIL: {exc}", file=sys.stderr)
        return 1
    print("RSD-25 production distribution: PASS")
    print(f"Distribution: {result.distribution_root}")
    print(f"Manifest: {result.manifest}")
    print(f"Firmware: {result.distribution_root / 'firmware' / 'robot-platform'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
