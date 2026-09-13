"""Assemble the production RoboStudio release artifact.

RSD-21.7 makes the application-owned compiler an explicit production release
input. The resulting ZIP contains RoboStudio, the real compiler, application
resources/dependencies, and release metadata. Python and PlatformIO remain
external target-machine prerequisites.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from tools import portable_release_proof, production_distribution, release_package, release_provenance

REPORT_NAME = "release-assembly-report.json"
PROOF_REPORT_NAME = "portable-release-proof.json"
REPORT_SCHEMA = "antechkids.robostudio.production-release-assembly"
REPORT_SCHEMA_VERSION = 2
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


class ProductionReleaseAssemblyError(RuntimeError):
    """Raised when a production release cannot be assembled safely."""


@dataclass(frozen=True)
class ProductionReleaseInputs:
    executable: Path
    runtime_resources: Path
    version_file: Path
    source_revision: str
    runtime_bin: Path | None = None
    runtime_platformio: Path | None = None
    compiler_root: Path | None = None


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _require_file(path: Path, label: str) -> Path:
    path = _resolve(path)
    if not path.is_file():
        raise ProductionReleaseAssemblyError(f"Missing {label}: {path}")
    return path


def _require_directory(path: Path, label: str) -> Path:
    path = _resolve(path)
    if not path.is_dir():
        raise ProductionReleaseAssemblyError(f"Missing {label}: {path}")
    return path


def _read_version(path: Path) -> str:
    path = _require_file(path, "application VERSION file")
    value = path.read_text(encoding="utf-8").strip()
    if not value or "\n" in value or "\r" in value or not _VERSION_RE.fullmatch(value):
        raise ProductionReleaseAssemblyError(f"Invalid application VERSION: {path}")
    return value


def _source_revision(explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    env = os.environ.get("RSD_SOURCE_REVISION", "").strip()
    if env:
        return env
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository_root(), check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProductionReleaseAssemblyError("Source revision is required when Git is unavailable; pass --source-revision.") from exc
    revision = result.stdout.strip()
    if not revision:
        raise ProductionReleaseAssemblyError("Unable to determine source revision; pass --source-revision.")
    return revision


def validate_inputs(inputs: ProductionReleaseInputs, output_root: Path) -> str:
    """Validate all application-owned production inputs before assembly."""
    executable = _require_file(inputs.executable, "RoboStudio executable")
    resources = _require_directory(inputs.runtime_resources, "application resources")
    version = _read_version(inputs.version_file)
    if inputs.compiler_root is not None:
        compiler_root = _require_directory(inputs.compiler_root, "application-owned compiler")
        if not (compiler_root / "main.py").is_file() or not (compiler_root / "compiler").is_dir():
            raise ProductionReleaseAssemblyError(
                "Application-owned compiler must contain main.py and compiler/"
            )
    output_root = _resolve(output_root)
    sources = [executable.parent, resources]
    if inputs.compiler_root is not None:
        sources.append(_resolve(inputs.compiler_root))
    for source in sources:
        try:
            output_root.relative_to(source)
        except ValueError:
            continue
        raise ProductionReleaseAssemblyError(f"Release output must not be inside an input source: {output_root}")
    return version


def assemble_release(inputs: ProductionReleaseInputs, output_root: Path) -> dict[str, object]:
    """Build distribution -> ZIP -> provenance -> release proof."""
    output_root = _resolve(output_root)
    version = validate_inputs(inputs, output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    distribution_root = output_root / "RoboStudio"
    artifact = output_root / f"RoboStudio-{version}-Windows.zip"
    proof_report = output_root / PROOF_REPORT_NAME
    report_path = output_root / REPORT_NAME
    try:
        distribution = production_distribution.build_production_distribution(
            production_distribution.ProductionDistributionInputs(
                executable=_resolve(inputs.executable),
                runtime_resources=_resolve(inputs.runtime_resources),
                version_file=_resolve(inputs.version_file),
                compiler_root=_resolve(inputs.compiler_root) if inputs.compiler_root is not None else None,
            ),
            distribution_root,
        )
        release = release_package.build_release(distribution.distribution_root, artifact)
        provenance = release_provenance.write_provenance(
            distribution.distribution_root,
            release.manifest,
            release.artifact,
            artifact.with_name(release_provenance.PROVENANCE_MANIFEST),
            source_revision=inputs.source_revision,
        )
        proof = portable_release_proof.prove_portable_release(release.artifact, manifest=release.manifest)
        if not proof.passed:
            raise ProductionReleaseAssemblyError("Portable release proof failed; artifact is not release-ready.")
        proof_payload = portable_release_proof.report_to_dict(proof)
        proof_report.write_text(json.dumps(proof_payload, indent=2) + "\n", encoding="utf-8")
        report = {
            "schema": REPORT_SCHEMA,
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "PASS",
            "portable": True,
            "artifact_model": "RoboStudio + Compiler",
            "host_prerequisites_packaged": False,
            "compiler": "compiler/main.py" if inputs.compiler_root is not None else None,
            "application": distribution.application,
            "application_version": distribution.application_version,
            "source_revision": inputs.source_revision,
            "distribution": str(distribution.distribution_root),
            "artifact": str(release.artifact),
            "artifact_sha256": release.sha256,
            "release_manifest": str(release.manifest),
            "release_provenance": str(provenance),
            "portable_proof_report": str(proof_report),
            "proof": proof_payload,
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    except Exception as exc:
        if isinstance(exc, ProductionReleaseAssemblyError):
            raise
        raise ProductionReleaseAssemblyError(str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a production RoboStudio release with the application-owned compiler")
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--compiler-root", required=False, type=Path, help="application-owned compiler root containing main.py and compiler/")
    parser.add_argument("--runtime-bin", required=False, type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--runtime-platformio", required=False, type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--runtime-resources", required=True, type=Path)
    parser.add_argument("--version-file", type=Path, default=repository_root() / "VERSION")
    parser.add_argument("--source-revision", type=str)
    parser.add_argument("--output", type=Path, default=repository_root() / "releases" / "production")
    args = parser.parse_args()
    try:
        revision = _source_revision(args.source_revision)
        report = assemble_release(
            ProductionReleaseInputs(
                args.executable,
                args.runtime_resources,
                args.version_file,
                revision,
                args.runtime_bin,
                args.runtime_platformio,
                args.compiler_root,
            ),
            args.output,
        )
    except ProductionReleaseAssemblyError as exc:
        print(f"RSD-21.7 production release assembly: FAIL: {exc}", file=sys.stderr)
        return 1
    print("RSD-21.7 production release assembly: PASS")
    print(f"Artifact: {report['artifact']}")
    print(f"SHA-256: {report['artifact_sha256']}")
    print(f"Release manifest: {report['release_manifest']}")
    print(f"Provenance: {report['release_provenance']}")
    print(f"Proof: {report['portable_proof_report']}")
    print(f"Compiler: {report['compiler']}")
    print(f"Assembly report: {Path(args.output).resolve() / REPORT_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
