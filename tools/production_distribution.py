"""Build a production RoboStudio distribution within the RSD-21 release boundary."""
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
PRODUCTION_SCHEMA_VERSION = 2
DEFAULT_VERSION_FILE = "VERSION"
LAUNCHER_NAME = "RoboStudio.cmd"


class ProductionDistributionError(RuntimeError):
    """Raised when production distribution inputs are incomplete or unsafe."""


@dataclass(frozen=True)
class ProductionDistributionInputs:
    """Explicit application-owned inputs used for production assembly."""

    executable: Path
    runtime_resources: Path
    version_file: Path


@dataclass(frozen=True)
class ProductionDistributionResult:
    distribution_root: Path
    manifest: Path
    application: str
    application_version: str


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _require_file(path: Path, label: str) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ProductionDistributionError(f"Missing {label}: {path}")
    return path


def _require_directory(path: Path, label: str) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.is_dir():
        raise ProductionDistributionError(f"Missing {label}: {path}")
    return path


def _read_version(path: Path) -> str:
    path = _require_file(path, "application VERSION file")
    value = path.read_text(encoding="utf-8").strip()
    if not value or "\n" in value or "\r" in value:
        raise ProductionDistributionError(f"Invalid application VERSION: {path}")
    return value


def validate_inputs(inputs: ProductionDistributionInputs, output: Path | None = None) -> str:
    """Validate only application-owned production inputs."""
    executable = _require_file(inputs.executable, "RoboStudio executable")
    resources = _require_directory(inputs.runtime_resources, "application resources")
    version = _read_version(inputs.version_file)
    if output is not None:
        output = Path(output).expanduser().resolve()
        for source in (executable.parent, resources):
            try:
                output.relative_to(source)
            except ValueError:
                continue
            raise ProductionDistributionError(
                f"Distribution output must not be inside an input source: {output}"
            )
    return version


def _launcher_text(executable_name: str) -> str:
    """Return the relocation-safe Windows launcher contents."""
    return (
        "@echo off\r\n"
        "setlocal\r\n"
        "pushd \"%~dp0\"\r\n"
        f'if not exist "{executable_name}" (\r\n'
        f'  echo RoboStudio executable not found: "%~dp0{executable_name}" 1>&2\r\n'
        "  popd\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        f'"%~dp0{executable_name}" %*\r\n'
        "set ""exit_code=%ERRORLEVEL%""\r\n"
        "popd\r\n"
        "exit /b %exit_code%\r\n"
    )


def _stage_application(executable: Path, version_file: Path, stage: Path) -> Path:
    """Stage the executable, launcher, VERSION, and colocated application DLLs."""
    stage.mkdir(parents=True, exist_ok=True)
    staged_executable = stage / executable.name
    shutil.copy2(executable, staged_executable)
    shutil.copy2(version_file, stage / DEFAULT_VERSION_FILE)
    (stage / LAUNCHER_NAME).write_text(_launcher_text(executable.name), encoding="utf-8")
    for dependency in sorted(executable.parent.glob("*.dll"), key=lambda item: item.name.lower()):
        if dependency.is_file():
            shutil.copy2(dependency, stage / dependency.name)
    return staged_executable


def build_production_distribution(inputs: ProductionDistributionInputs, output: Path) -> ProductionDistributionResult:
    """Assemble the application-owned production distribution."""
    output = Path(output).expanduser().resolve()
    executable = Path(inputs.executable).expanduser().resolve()
    version_file = Path(inputs.version_file).expanduser().resolve()
    runtime_resources = Path(inputs.runtime_resources).expanduser().resolve()
    version = validate_inputs(inputs, output)

    with tempfile.TemporaryDirectory(prefix="robostudio-production-stage-") as temp:
        stage = Path(temp) / "application"
        staged_executable = _stage_application(executable, version_file, stage)
        try:
            manifest = distribution_package.assemble_distribution(
                distribution_package.DistributionInputs(
                    executable=staged_executable,
                    runtime_resources=runtime_resources,
                    production_boundary=True,
                    launcher=stage / LAUNCHER_NAME,
                ),
                output,
            )
        except distribution_package.DistributionPackageError as exc:
            raise ProductionDistributionError(
                f"Production distribution assembly failed: {exc}"
            ) from exc

    return ProductionDistributionResult(output, manifest, executable.name, version)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assemble a production RoboStudio distribution without bundling host prerequisites"
    )
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--runtime-resources", required=True, type=Path)
    parser.add_argument("--version-file", type=Path, default=repository_root() / DEFAULT_VERSION_FILE)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build_production_distribution(
            ProductionDistributionInputs(args.executable, args.runtime_resources, args.version_file), args.output
        )
    except ProductionDistributionError as exc:
        print(f"RSD-21.6 production distribution: FAIL: {exc}", file=sys.stderr)
        return 1
    print("RSD-21.6 production distribution: PASS")
    print(f"Distribution: {result.distribution_root}")
    print(f"Manifest: {result.manifest}")
    print(f"Application: {result.application}")
    print(f"Application version: {result.application_version}")
    print(f"Launcher: {result.distribution_root / LAUNCHER_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
