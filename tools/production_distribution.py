"""Build a production RoboStudio distribution from declared release inputs.

RSD-17 is the source-integration boundary between real application/runtime
artifacts and the generic RSD-07 distribution assembler.  Inputs are explicit
paths; this module never discovers tools from PATH, the current working
 directory, or a developer's PlatformIO installation.
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from tools import distribution_package

PRODUCTION_SCHEMA = "antechkids.robostudio.production-distribution"
PRODUCTION_SCHEMA_VERSION = 1
DEFAULT_VERSION_FILE = "VERSION"


class ProductionDistributionError(RuntimeError):
    """Raised when production distribution inputs are incomplete or unsafe."""


@dataclass(frozen=True)
class ProductionDistributionInputs:
    """Explicit source artifacts used to assemble the production distribution."""

    executable: Path
    runtime_bin: Path
    runtime_platformio: Path
    runtime_resources: Path
    version_file: Path


@dataclass(frozen=True)
class ProductionDistributionResult:
    """Result of production distribution assembly."""

    distribution_root: Path
    manifest: Path
    application: str
    application_version: str


def repository_root() -> Path:
    """Return the source repository root without consulting the caller CWD."""
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
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ProductionDistributionError(f"Application VERSION is empty: {path}")
    if "\n" in value or "\r" in value:
        raise ProductionDistributionError(f"Application VERSION must be a single line: {path}")
    return value


def validate_inputs(inputs: ProductionDistributionInputs) -> str:
    """Validate all production inputs and return the declared application version."""
    _require_file(inputs.executable, "RoboStudio executable")
    _require_file(inputs.version_file, "application VERSION file")
    _require_directory(inputs.runtime_bin, "portable Python runtime")
    _require_directory(inputs.runtime_platformio, "application-owned PlatformIO runtime")
    _require_directory(inputs.runtime_resources, "runtime resources")
    return _read_version(Path(inputs.version_file).expanduser().resolve())


def _stage_application(executable: Path, version_file: Path, stage: Path) -> Path:
    """Create an application staging directory with VERSION adjacent to the executable."""
    stage.mkdir(parents=True, exist_ok=True)
    staged_executable = stage / executable.name
    shutil.copy2(executable, staged_executable)
    shutil.copy2(version_file, stage / DEFAULT_VERSION_FILE)
    return staged_executable


def build_production_distribution(
    inputs: ProductionDistributionInputs,
    output: Path,
) -> ProductionDistributionResult:
    """Assemble a production distribution using the canonical RSD-07 assembler.

    The source VERSION may live at repository root while the executable is
    produced in another build directory.  A temporary application staging
    directory bridges that layout without changing the generic assembler's
    contract and without copying any unrelated build/host files.
    """
    executable = Path(inputs.executable).expanduser().resolve()
    version_file = Path(inputs.version_file).expanduser().resolve()
    runtime_bin = Path(inputs.runtime_bin).expanduser().resolve()
    runtime_platformio = Path(inputs.runtime_platformio).expanduser().resolve()
    runtime_resources = Path(inputs.runtime_resources).expanduser().resolve()
    output = Path(output).expanduser().resolve()

    version = validate_inputs(
        ProductionDistributionInputs(
            executable=executable,
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            runtime_resources=runtime_resources,
            version_file=version_file,
        )
    )

    if output == executable or executable in output.parents:
        raise ProductionDistributionError("Distribution output must not be inside the executable source directory.")
    if output == runtime_bin or runtime_bin in output.parents:
        raise ProductionDistributionError("Distribution output must not be inside the Python runtime source.")
    if output == runtime_platformio or runtime_platformio in output.parents:
        raise ProductionDistributionError("Distribution output must not be inside the PlatformIO runtime source.")
    if output == runtime_resources or runtime_resources in output.parents:
        raise ProductionDistributionError("Distribution output must not be inside the resource source.")

    with tempfile.TemporaryDirectory(prefix="robostudio-production-stage-") as temp:
        stage = Path(temp) / "application"
        staged_executable = _stage_application(executable, version_file, stage)
        try:
            manifest = distribution_package.assemble_distribution(
                distribution_package.DistributionInputs(
                    executable=staged_executable,
                    runtime_bin=runtime_bin,
                    runtime_platformio=runtime_platformio,
                    runtime_resources=runtime_resources,
                ),
                output,
            )
        except distribution_package.DistributionPackageError as exc:
            raise ProductionDistributionError(f"Production distribution assembly failed: {exc}") from exc

    return ProductionDistributionResult(
        distribution_root=output,
        manifest=manifest,
        application=staged_executable.name,
        application_version=version,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assemble a production RoboStudio distribution from explicit application/runtime inputs"
    )
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--runtime-bin", required=True, type=Path)
    parser.add_argument("--runtime-platformio", required=True, type=Path)
    parser.add_argument("--runtime-resources", required=True, type=Path)
    parser.add_argument("--version-file", type=Path, default=repository_root() / DEFAULT_VERSION_FILE)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    result = build_production_distribution(
        ProductionDistributionInputs(
            executable=args.executable,
            runtime_bin=args.runtime_bin,
            runtime_platformio=args.runtime_platformio,
            runtime_resources=args.runtime_resources,
            version_file=args.version_file,
        ),
        args.output,
    )
    print("RSD-17 production distribution: PASS")
    print(f"Distribution: {result.distribution_root}")
    print(f"Manifest: {result.manifest}")
    print(f"Application: {result.application}")
    print(f"Application version: {result.application_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
