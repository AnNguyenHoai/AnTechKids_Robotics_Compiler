"""RSD-21 production release qualification for RoboStudio artifacts.

RSD-21 is the post-assembly qualification boundary. It verifies the immutable
release ZIP, validates its provenance sidecar, optionally runs the legacy
portable acceptance gate, or (for a real target machine) validates the host
prerequisite contract without requiring developer-installed runtimes to be
bundled into the artifact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools import portable_release_proof, release_acceptance, release_package, release_provenance, target_machine_qualification

SCHEMA = "antechkids.robostudio.production-release-qualification"
SCHEMA_VERSION = 1
REPORT_NAME = "production-release-qualification.json"


class ProductionReleaseQualificationError(RuntimeError):
    """Raised when a production artifact cannot be qualified."""


def _resolve_file(path: Path, label: str) -> Path:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ProductionReleaseQualificationError(f"Missing {label}: {path}")
    return path


def _sidecar(artifact: Path, explicit: Path | None, filename: str, label: str) -> Path:
    if explicit is not None:
        return _resolve_file(explicit, label)
    return _resolve_file(artifact.with_name(filename), label)


def qualify_release(
    artifact: Path,
    *,
    provenance: Path | None = None,
    acceptance_report: Path | None = None,
    run_acceptance: bool = False,
    target_machine: bool = False,
    prerequisite_scope: str = "compile",
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Qualify a production release without modifying the artifact.

    ``target_machine=True`` switches the acceptance boundary from the legacy
    bundled-runtime RSD-16 probe to the target-machine prerequisite contract.
    This is the production-user model: the release supplies RoboStudio and its
    application-owned compiler; the target host supplies declared tooling.
    """
    artifact = _resolve_file(artifact, "release artifact")

    manifest_path = artifact.with_name(release_package.RELEASE_MANIFEST)
    manifest_path = _resolve_file(manifest_path, "release manifest")
    try:
        manifest = release_package.validate_release_artifact(artifact, manifest_path)
    except release_package.ReleasePackageError as exc:
        raise ProductionReleaseQualificationError(f"RSD-20 integrity/structure validation failed: {exc}") from exc

    try:
        proof = portable_release_proof.prove_portable_release(artifact, manifest=manifest_path)
    except portable_release_proof.PortableReleaseProofError as exc:
        raise ProductionReleaseQualificationError(f"RSD-20 portable proof failed: {exc}") from exc
    if not proof.passed:
        raise ProductionReleaseQualificationError("RSD-20 portable proof failed; artifact is not release-ready")

    provenance_path = _sidecar(
        artifact, provenance, release_provenance.PROVENANCE_MANIFEST, "release provenance"
    )
    try:
        provenance_payload = release_provenance.validate_provenance(
            provenance_path,
            artifact,
            manifest_path,
        )
    except (OSError, ValueError) as exc:
        raise ProductionReleaseQualificationError(f"Release provenance validation failed: {exc}") from exc

    acceptance_payload: dict[str, Any] | None = None
    target_machine_payload: dict[str, Any] | None = None
    if target_machine:
        if run_acceptance:
            raise ProductionReleaseQualificationError("--target-machine and --run-acceptance are mutually exclusive")
        try:
            target_report = target_machine_qualification.require_target_machine(scope=prerequisite_scope)
        except target_machine_qualification.TargetMachineQualificationError as exc:
            raise ProductionReleaseQualificationError(f"RSD-21.4 target-machine qualification failed: {exc}") from exc
        target_machine_payload = target_machine_qualification.to_dict(target_report)
    elif run_acceptance:
        try:
            acceptance = release_acceptance.accept_release(artifact, timeout=timeout)
        except release_acceptance.ReleaseAcceptanceError as exc:
            raise ProductionReleaseQualificationError(f"RSD-16 clean-machine acceptance failed: {exc}") from exc
        acceptance_payload = release_acceptance.evidence_to_dict(acceptance)
        if acceptance_report is not None:
            release_acceptance.write_evidence(acceptance, acceptance_report)
    elif acceptance_report is not None:
        acceptance_path = _resolve_file(acceptance_report, "acceptance evidence")
        try:
            acceptance_payload = json.loads(acceptance_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProductionReleaseQualificationError(f"Invalid acceptance evidence: {acceptance_path}") from exc
        if acceptance_payload.get("schema") != release_acceptance.EVIDENCE_SCHEMA:
            raise ProductionReleaseQualificationError("Unsupported acceptance evidence schema")
        if acceptance_payload.get("status") != "PASS":
            raise ProductionReleaseQualificationError("Acceptance evidence is not PASS")
        if acceptance_payload.get("artifact_sha256") != manifest.get("artifact_sha256"):
            raise ProductionReleaseQualificationError("Acceptance evidence artifact checksum mismatch")

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "qualified": True,
        "artifact": artifact.name,
        "artifact_sha256": str(manifest.get("artifact_sha256", "")),
        "application": manifest.get("application"),
        "application_version": manifest.get("application_version"),
        "file_count": manifest.get("file_count"),
        "portable_dependency_closure": {
            "passed": proof.passed,
            "packaged_dependency_count": proof.packaged_dependency_count,
            "finding_count": len(proof.findings),
        },
        "provenance": {
            "path": provenance_path.name,
            "source_revision": provenance_payload.get("source_revision"),
            "artifact_sha256_verified": True,
            "deterministic_zip_verified": provenance_payload.get("reproducibility", {}).get("deterministic_zip") is True,
        },
        "acceptance": {
            "performed": run_acceptance,
            "evidence": acceptance_payload,
        },
        "target_machine": {
            "performed": target_machine,
            "scope": prerequisite_scope if target_machine else None,
            "qualified": target_machine_payload["passed"] if target_machine_payload else None,
            "evidence": target_machine_payload,
        },
    }
    return report


def write_report(report: dict[str, Any], output: Path) -> Path:
    output = Path(output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qualify a production RoboStudio release artifact")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--acceptance-report", type=Path)
    parser.add_argument("--run-acceptance", action="store_true")
    parser.add_argument("--target-machine", action="store_true", help="qualify the target host using declared prerequisites")
    parser.add_argument("--prerequisite-scope", choices=[scope.value for scope in target_machine_qualification.target_machine_prerequisites.RequirementScope], default="compile")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        report = qualify_release(
            args.artifact,
            provenance=args.provenance,
            acceptance_report=args.acceptance_report,
            run_acceptance=args.run_acceptance,
            target_machine=args.target_machine,
            prerequisite_scope=args.prerequisite_scope,
            timeout=args.timeout,
        )
        report_path = write_report(
            report,
            args.report or Path(args.artifact).with_name(REPORT_NAME),
        )
    except ProductionReleaseQualificationError as exc:
        print(f"RSD-21 production release qualification: FAIL: {exc}")
        return 1

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("RSD-21 production release qualification: PASS")
        print(f"Artifact: {args.artifact.resolve()}")
        print(f"SHA-256: {report['artifact_sha256']}")
        print(f"Portable dependency closure: {report['portable_dependency_closure']['passed']}")
        print(f"Provenance verified: {report['provenance']['artifact_sha256_verified']}")
        print(f"Deterministic ZIP verified: {report['provenance']['deterministic_zip_verified']}")
        print(f"Acceptance performed: {report['acceptance']['performed']}")
        if report["target_machine"]["performed"]:
            print(f"Target-machine qualification: {report['target_machine']['qualified']}")
            print(f"Prerequisite scope: {report['target_machine']['scope']}")
        print(f"Qualification report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
