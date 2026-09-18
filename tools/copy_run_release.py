"""Finalize and validate B2.6 copy-and-run production releases.

This boundary deliberately runs after the existing production distribution has
passed its historical RSD checks.  It adds the self-describing copy-run
contract to the distribution inventory, re-runs production closure, rebuilds
the deterministic ZIP/provenance/proof, and validates the contract from the ZIP
itself.  Older RSD schemas therefore remain stable while the canonical
one-command production build gains the stronger B2.6 release guarantee.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from tools import (
    copy_run_contract,
    distribution_package,
    portable_release_proof,
    production_runtime_closure,
    release_package,
    release_provenance,
)

B2_6_SCHEMA = "antechkids.robostudio.b2-6-copy-run-release"
B2_6_SCHEMA_VERSION = 1
ASSEMBLY_REPORT_NAME = "release-assembly-report.json"
PROOF_REPORT_NAME = "portable-release-proof.json"


class CopyRunReleaseError(RuntimeError):
    """Raised when the final release cannot satisfy the B2.6 contract."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CopyRunReleaseError(f"Invalid {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise CopyRunReleaseError(f"{label} root must be an object: {path}")
    return payload


def install_contract(distribution_root: Path) -> dict[str, Any]:
    """Install the contract and make it a first-class distribution inventory item."""
    root = Path(distribution_root).expanduser().resolve()
    manifest_path = root / distribution_package.DISTRIBUTION_MANIFEST
    try:
        manifest = distribution_package.validate_distribution_manifest(manifest_path)
    except distribution_package.DistributionPackageError as exc:
        raise CopyRunReleaseError(f"Pre-B2.6 distribution validation failed: {exc}") from exc
    if manifest.get("production_boundary") is not True:
        raise CopyRunReleaseError("B2.6 copy-and-run contract requires a production distribution")

    application = str(manifest.get("application", "")).strip()
    try:
        contract_path = copy_run_contract.write_contract(root, application=application)
        contract_payload = copy_run_contract.validate_distribution(root, manifest=manifest)
    except copy_run_contract.CopyRunContractError as exc:
        raise CopyRunReleaseError(f"Copy-and-run contract generation failed: {exc}") from exc

    entry = {
        "path": copy_run_contract.CONTRACT_NAME,
        "size": contract_path.stat().st_size,
        "sha256": _sha256_file(contract_path),
    }
    files = manifest.get("files")
    if not isinstance(files, list):
        raise CopyRunReleaseError("Distribution manifest files must be a list")
    filtered = [item for item in files if isinstance(item, dict) and item.get("path") != copy_run_contract.CONTRACT_NAME]
    filtered.append(entry)
    manifest["files"] = sorted(filtered, key=lambda item: str(item.get("path", "")).lower())
    manifest["copy_run_contract"] = copy_run_contract.CONTRACT_NAME
    manifest["copy_run_ready"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    try:
        verified_manifest = distribution_package.validate_distribution_manifest(manifest_path)
        copy_run_contract.validate_distribution(root, manifest=verified_manifest)
        production_runtime_closure.validate_distribution(root)
    except Exception as exc:
        raise CopyRunReleaseError(f"Post-contract production closure failed: {exc}") from exc

    return {
        "schema": B2_6_SCHEMA,
        "schema_version": B2_6_SCHEMA_VERSION,
        "status": "PASS",
        "copy_run_ready": True,
        "contract": copy_run_contract.CONTRACT_NAME,
        "contract_sha256": entry["sha256"],
        "delivery_model": contract_payload["delivery_model"],
        "application": contract_payload["application"],
        "application_version": contract_payload["application_version"],
    }


def validate_release_zip(artifact: Path, manifest: Path | None = None) -> dict[str, Any]:
    """Validate the B2.6 contract from the immutable ZIP, not from source/staging."""
    artifact = Path(artifact).expanduser().resolve()
    release_manifest = Path(manifest).expanduser().resolve() if manifest is not None else artifact.with_name(release_package.RELEASE_MANIFEST)
    try:
        release = release_package.validate_release_artifact(artifact, release_manifest)
    except release_package.ReleasePackageError as exc:
        raise CopyRunReleaseError(f"Release integrity validation failed: {exc}") from exc

    expected_files = {
        str(item.get("path")): item
        for item in release.get("files", [])
        if isinstance(item, dict) and item.get("path")
    }
    contract_entry = expected_files.get(copy_run_contract.CONTRACT_NAME)
    if not isinstance(contract_entry, dict):
        raise CopyRunReleaseError("Release manifest does not inventory copy-run-contract.json")

    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            names = [item.filename for item in archive.infolist() if not item.is_dir()]
            if distribution_package.DISTRIBUTION_MANIFEST not in names:
                raise CopyRunReleaseError("Release ZIP is missing distribution-manifest.json")
            if copy_run_contract.CONTRACT_NAME not in names:
                raise CopyRunReleaseError("Release ZIP is missing copy-run-contract.json")
            distribution = json.loads(archive.read(distribution_package.DISTRIBUTION_MANIFEST).decode("utf-8"))
            if not isinstance(distribution, dict):
                raise CopyRunReleaseError("Embedded distribution manifest root must be an object")
            if distribution.get("copy_run_ready") is not True or distribution.get("copy_run_contract") != copy_run_contract.CONTRACT_NAME:
                raise CopyRunReleaseError("Embedded distribution manifest does not require the B2.6 contract")
            contract_bytes = archive.read(copy_run_contract.CONTRACT_NAME)
            if len(contract_bytes) != int(contract_entry.get("size", -1)):
                raise CopyRunReleaseError("Copy-and-run contract size disagrees with release manifest")
            if _sha256_bytes(contract_bytes) != str(contract_entry.get("sha256", "")):
                raise CopyRunReleaseError("Copy-and-run contract checksum disagrees with release manifest")
            contract = json.loads(contract_bytes.decode("utf-8"))
            if not isinstance(contract, dict):
                raise CopyRunReleaseError("Copy-and-run contract root must be an object")
            validated = copy_run_contract.validate_payload(
                contract,
                expected_application=str(release.get("application", "")),
                expected_version=str(release.get("application_version", "")),
                member_names=names,
            )
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CopyRunReleaseError(f"Unable to validate copy-and-run ZIP contract: {artifact}") from exc
    except copy_run_contract.CopyRunContractError as exc:
        raise CopyRunReleaseError(f"Invalid copy-and-run ZIP contract: {exc}") from exc

    return {
        "schema": B2_6_SCHEMA,
        "schema_version": B2_6_SCHEMA_VERSION,
        "status": "PASS",
        "copy_run_ready": True,
        "artifact": artifact.name,
        "artifact_sha256": str(release.get("artifact_sha256", "")),
        "contract": copy_run_contract.CONTRACT_NAME,
        "contract_sha256": str(contract_entry.get("sha256", "")),
        "delivery_model": validated["delivery_model"],
        "application": validated["application"],
        "application_version": validated["application_version"],
        "host_python_required": validated["host_requirements"]["python"],
        "host_platformio_required": validated["host_requirements"]["platformio"],
        "host_compiler_toolchain_required": validated["host_requirements"]["compiler_toolchain"],
        "external_state_required": validated["state"]["inside_artifact_allowed"] is False,
        "physical_acceptance_requires_operator": validated["acceptance"]["final_pass_requires_operator_confirmation"],
    }


def finalize_assembly_result(result: dict[str, object], *, source_revision: str) -> dict[str, object]:
    """Upgrade an existing production assembly result to the canonical B2.6 artifact."""
    try:
        distribution_root = Path(str(result["distribution"])).expanduser().resolve()
        artifact = Path(str(result["artifact"])).expanduser().resolve()
    except KeyError as exc:
        raise CopyRunReleaseError(f"Production assembly result is missing {exc.args[0]}") from exc

    installation = install_contract(distribution_root)
    try:
        release = release_package.build_release(distribution_root, artifact)
        provenance_path = artifact.with_name(release_provenance.PROVENANCE_MANIFEST)
        provenance = release_provenance.write_provenance(
            distribution_root,
            release.manifest,
            release.artifact,
            provenance_path,
            source_revision=source_revision,
        )
        proof = portable_release_proof.prove_portable_release(release.artifact, manifest=release.manifest)
        if not proof.passed:
            raise CopyRunReleaseError("Portable release proof failed after B2.6 finalization")
        proof_payload = portable_release_proof.report_to_dict(proof)
        proof_report = artifact.with_name(PROOF_REPORT_NAME)
        proof_report.write_text(json.dumps(proof_payload, indent=2) + "\n", encoding="utf-8")
        validation = validate_release_zip(release.artifact, release.manifest)
    except CopyRunReleaseError:
        raise
    except Exception as exc:
        raise CopyRunReleaseError(f"Unable to rebuild B2.6 release: {exc}") from exc

    updated = dict(result)
    updated.update(
        {
            "artifact": str(release.artifact),
            "artifact_sha256": release.sha256,
            "release_manifest": str(release.manifest),
            "release_provenance": str(provenance),
            "portable_proof_report": str(proof_report),
            "proof": proof_payload,
            "copy_run_contract": copy_run_contract.CONTRACT_NAME,
            "copy_run_ready": True,
            "b2_6": validation,
        }
    )
    report_path = distribution_root.parent / ASSEMBLY_REPORT_NAME
    report_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    return updated


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate a B2.6 copy-and-run RoboStudio release ZIP")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        report = validate_release_zip(args.artifact, args.manifest)
    except CopyRunReleaseError as exc:
        print(f"B2.6 copy-and-run release: FAIL: {exc}")
        return 1
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print("B2.6 copy-and-run release: PASS")
        print(f"Artifact: {Path(args.artifact).resolve()}")
        print(f"Contract: {report['contract']}")
        print(f"Delivery model: {report['delivery_model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
