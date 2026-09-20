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

from tools import distribution_package, production_platformio_closure

PRODUCTION_SCHEMA = "antechkids.robostudio.production-distribution"
PRODUCTION_SCHEMA_VERSION = 5
DEFAULT_VERSION_FILE = "VERSION"
LAUNCHER_NAME = "RoboStudio.cmd"
COMPILER_ROOT_NAME = "compiler"
COMPILER_ENTRY_NAME = "main.py"
FRONTEND_ROOT_NAME = "frontend"
CONTRACT_ENTRY_NAME = "robostudio_bridge.py"

# Production deployment/acceptance runtime allow-list. These are application
# runtime modules, not repository release builders/test helpers. Direct CLI
# tools bootstrap the artifact root onto sys.path, so the copied directory stays
# relocatable when invoked by bundled Python.
DEPLOYMENT_RUNTIME_TOOL_FILES: tuple[str, ...] = (
    "bootstrap_config.py",
    "build_isolation.py",
    "clean_machine_physical_e2e.py",
    "dependency_closure.py",
    "deploy_robot.py",
    "deployment_contract.py",
    "deployment_runtime.py",
    "firmware_workspace.py",
    "hardware_feature_config.py",
    "hardware_preflight.py",
    "runtime_paths.py",
    "runtime_resources.py",
    "target_machine_prerequisites.py",
    "target_machine_qualification.py",
)


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
    """Reject a Python payload that only works by borrowing host dependencies."""
    _require_file(runtime_bin / "python.exe", "Windows portable Python executable")
    if not list(runtime_bin.glob("python*.dll")):
        raise ProductionDistributionError(
            "Portable Python runtime DLL is missing; python.exe must not depend on a host Python installation"
        )
    encodings = runtime_bin / "Lib" / "encodings" / "__init__.py"
    stdlib_zip = list(runtime_bin.glob("python*.zip"))
    if not encodings.is_file() and not stdlib_zip:
        raise ProductionDistributionError(
            "Portable Python standard library is missing; expected Lib/encodings or python*.zip"
        )
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
    """Validate required source markers without requiring a pristine workspace.

    PlatformIO legitimately creates transient development state such as ``.pio``
    inside the firmware source tree during the production build itself. Source
    validation therefore verifies only the application-owned firmware contract.
    The distribution boundary remains fail-closed: ``distribution_package``
    filters developer payload while staging and rejects it if any reaches the
    packaged firmware artifact.
    """
    _require_directory(firmware, "application-owned firmware project")
    _require_file(firmware / "platformio.ini", "firmware platformio.ini")
    _require_file(firmware / "wifi_config.py", "firmware wifi_config.py")
    _require_directory(firmware / "main", "firmware main source")


def _validate_deployment_tool_sources() -> Path:
    tools_root = repository_root() / "tools"
    missing = [name for name in DEPLOYMENT_RUNTIME_TOOL_FILES if not (tools_root / name).is_file()]
    if missing:
        raise ProductionDistributionError(
            "Production deployment runtime tool source is missing: " + ", ".join(missing)
        )
    return tools_root


def validate_inputs(inputs: ProductionDistributionInputs, output: Path | None = None) -> str:
    executable = _require_file(inputs.executable, "RoboStudio executable")
    resources = _require_directory(inputs.runtime_resources, "application resources")
    version = _read_version(inputs.version_file)
    compiler = _require_directory(inputs.compiler_root or _default_compiler_root(), "application-owned compiler")
    frontend = _require_directory(inputs.frontend_root or _default_frontend_root(), "RoboSim frontend")
    firmware = _require_directory(inputs.firmware_root or _default_firmware_root(), "application-owned firmware project")
    runtime_bin = _require_directory(inputs.runtime_bin, "application-owned portable Python")
    runtime_platformio = _require_directory(inputs.runtime_platformio, "application-owned PlatformIO runtime")
    _validate_deployment_tool_sources()

    if not (compiler / COMPILER_ENTRY_NAME).is_file() or not (compiler / "compiler").is_dir():
        raise ProductionDistributionError("Invalid application-owned compiler: must contain main.py and compiler/")
    _contract_source(compiler)
    if not (frontend / "__init__.py").is_file() or not (frontend / "rewriter.py").is_file():
        raise ProductionDistributionError("RoboSim frontend must contain __init__.py and rewriter.py")
    _validate_firmware(firmware)
    _validate_runtime_bin(runtime_bin)
    _validate_runtime_platformio(runtime_platformio)
    try:
        production_platformio_closure.validate_firmware_project(firmware, runtime_platformio)
    except production_platformio_closure.ProductionPlatformIOClosureError as exc:
        raise ProductionDistributionError(f"PlatformIO dependency closure failed: {exc}") from exc

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
    """Stage the application exactly as the downstream packager expects it.

    ``distribution_package`` deliberately discovers application-local DLLs next
    to the executable. The production staging layer must therefore preserve
    those siblings instead of reducing the application input to the EXE alone.
    This matters for non-onefile builds and keeps the generic production
    distribution contract independent of today's PyInstaller layout.
    """
    stage.mkdir(parents=True, exist_ok=True)
    staged_executable = stage / executable.name
    shutil.copy2(executable, staged_executable)
    for dependency in sorted(executable.parent.glob("*.dll"), key=lambda item: item.name.lower()):
        if dependency.is_file():
            shutil.copy2(dependency, stage / dependency.name)
    shutil.copy2(version_file, stage / DEFAULT_VERSION_FILE)
    launcher = stage / LAUNCHER_NAME
    launcher.write_text(_launcher_text(executable.name), encoding="utf-8", newline="")
    return staged_executable


def _stage_compiler(compiler: Path, frontend: Path, stage: Path) -> tuple[Path, Path]:
    """Stage compiler and frontend as separate packager inputs.

    ``distribution_package`` owns the final merge into ``compiler/frontend``.
    Keeping these staging roots separate prevents double-inserting the frontend
    payload and preserves one clear assembly boundary.
    """
    staged_compiler = stage / COMPILER_ROOT_NAME
    if staged_compiler.exists():
        shutil.rmtree(staged_compiler)
    shutil.copytree(
        compiler,
        staged_compiler,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv", FRONTEND_ROOT_NAME),
    )
    contract = _contract_source(compiler)
    contract_target = staged_compiler / CONTRACT_ENTRY_NAME
    if contract.resolve() != (compiler / CONTRACT_ENTRY_NAME).resolve():
        shutil.copy2(contract, contract_target)
    elif not contract_target.is_file():
        raise ProductionDistributionError(f"Compiler contract staging failed: {contract_target}")

    staged_frontend = stage / "compiler-frontend"
    if staged_frontend.exists():
        shutil.rmtree(staged_frontend)
    shutil.copytree(
        frontend,
        staged_frontend,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv"),
    )
    return staged_compiler, staged_frontend


def _stage_deployment_tools(stage: Path) -> Path:
    source = _validate_deployment_tool_sources()
    destination = stage / "deployment-tools"
    destination.mkdir(parents=True, exist_ok=True)
    for name in DEPLOYMENT_RUNTIME_TOOL_FILES:
        shutil.copy2(source / name, destination / name)
    return destination


def build_production_distribution(inputs: ProductionDistributionInputs, output: Path) -> ProductionDistributionResult:
    version = validate_inputs(inputs, output)
    executable = _resolve_root(inputs.executable)
    resources = _resolve_root(inputs.runtime_resources)
    version_file = _resolve_root(inputs.version_file)
    compiler = _resolve_root(inputs.compiler_root or _default_compiler_root())
    frontend = _resolve_root(inputs.frontend_root or _default_frontend_root())
    firmware = _resolve_root(inputs.firmware_root or _default_firmware_root())
    runtime_bin = _resolve_root(inputs.runtime_bin)
    runtime_platformio = _resolve_root(inputs.runtime_platformio)
    output = _resolve_root(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="robostudio-production-stage-", dir=output.parent) as temp:
        stage = Path(temp)
        staged_executable = _stage_application(executable, version_file, stage)
        staged_compiler, staged_frontend = _stage_compiler(compiler, frontend, stage)
        staged_tools = _stage_deployment_tools(stage)
        try:
            manifest = distribution_package.assemble_distribution(
                distribution_package.DistributionInputs(
                    executable=staged_executable,
                    runtime_bin=runtime_bin,
                    runtime_platformio=runtime_platformio,
                    runtime_resources=resources,
                    production_boundary=True,
                    launcher=stage / LAUNCHER_NAME,
                    compiler_root=staged_compiler,
                    frontend_root=staged_frontend,
                    firmware_root=firmware,
                    deployment_tools_root=staged_tools,
                ),
                output,
            )
        except Exception as exc:
            raise ProductionDistributionError(f"Production distribution assembly failed: {exc}") from exc

    return ProductionDistributionResult(
        distribution_root=output,
        manifest=manifest,
        application=executable.name,
        application_version=version,
    )


def _default_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a production RoboStudio distribution")
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--resources", required=True, type=Path)
    parser.add_argument("--version-file", default=DEFAULT_VERSION_FILE, type=Path)
    parser.add_argument("--runtime-bin", required=True, type=Path)
    parser.add_argument("--runtime-platformio", required=True, type=Path)
    parser.add_argument("--compiler-root", type=Path)
    parser.add_argument("--frontend-root", type=Path)
    parser.add_argument("--firmware-root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _default_argument_parser().parse_args(argv)
    inputs = ProductionDistributionInputs(
        executable=args.exe,
        runtime_resources=args.resources,
        version_file=args.version_file,
        runtime_bin=args.runtime_bin,
        runtime_platformio=args.runtime_platformio,
        compiler_root=args.compiler_root,
        frontend_root=args.frontend_root,
        firmware_root=args.firmware_root,
    )
    result = build_production_distribution(inputs, args.output)
    print(f"Production distribution: {result.distribution_root}")
    print(f"Manifest: {result.manifest}")
    print(f"Application: {result.application} {result.application_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
