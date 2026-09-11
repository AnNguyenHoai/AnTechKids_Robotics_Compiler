"""H26-M deployment contract.

Defines the artifact manifest consumed by the deployment boundary. The contract
makes deployment deterministic: the selected target, required capabilities and
exact generated artifact are recorded and validated before flashing.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from tools.runtime_resources import resolve_resource

SCHEMA_VERSION = 1
CONTRACT_KIND = "robot_deployment_manifest"


class DeploymentContractError(RuntimeError):
    """Raised when a deployment manifest cannot be safely deployed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact(path: Path) -> dict:
    if not path.is_file():
        raise DeploymentContractError(f"Deployment artifact not found: {path}")
    return {"path": str(path), "size": path.stat().st_size, "sha256": sha256_file(path)}


def _profiles(path: Path | None = None) -> dict[str, dict]:
    path = Path(path) if path is not None else resolve_resource("target_profiles")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentContractError(f"Unable to load target profiles: {exc}") from exc
    if document.get("schema_version") != 1 or document.get("kind") != "robot_target_capability_profiles":
        raise DeploymentContractError("Invalid target capability profile document")
    return {item["id"]: item for item in document.get("profiles", [])}


def validate_target_capabilities(target: str, required: Iterable[str], profiles: Mapping[str, Mapping]) -> None:
    profile = profiles.get(target)
    if profile is None:
        raise DeploymentContractError(f"Unknown deployment target: {target}")
    missing = sorted(set(required) - set(profile.get("capabilities", ())))
    if missing:
        raise DeploymentContractError(f"Target '{target}' cannot deploy program; missing capabilities: {', '.join(missing)}")


@dataclass(frozen=True)
class DeploymentManifest:
    target: str
    required_capabilities: tuple[str, ...]
    program_header: dict
    compile_report: dict | None = None
    source: dict | None = None
    platformio_environment: str = "esp32dev"

    def to_dict(self) -> dict:
        result = {"schema_version": SCHEMA_VERSION, "kind": CONTRACT_KIND, "target": self.target, "platformio_environment": self.platformio_environment, "required_capabilities": list(self.required_capabilities), "artifacts": {"program_header": self.program_header}}
        if self.compile_report is not None:
            result["artifacts"]["compile_report"] = self.compile_report
        if self.source is not None:
            result["artifacts"]["source"] = self.source
        return result


def create_manifest(build_dir: Path, target: str, required_capabilities: Iterable[str], *, source_path: Path | None = None, platformio_environment: str = "esp32dev") -> DeploymentManifest:
    build_dir = Path(build_dir)
    header = build_dir / "program.h"
    report = build_dir / "compile_report.json"
    profiles = _profiles()
    required = tuple(sorted(set(required_capabilities)))
    validate_target_capabilities(target, required, profiles)
    source = _artifact(Path(source_path)) if source_path else None
    compile_report = _artifact(report) if report.is_file() else None
    return DeploymentManifest(target=target, required_capabilities=required, program_header=_artifact(header), compile_report=compile_report, source=source, platformio_environment=platformio_environment)


def write_manifest(manifest: DeploymentManifest, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_manifest(path: Path) -> dict:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentContractError(f"Invalid deployment manifest: {exc}") from exc
    if data.get("schema_version") != SCHEMA_VERSION or data.get("kind") != CONTRACT_KIND:
        raise DeploymentContractError("Unsupported deployment manifest schema")
    for key in ("target", "required_capabilities", "artifacts"):
        if key not in data:
            raise DeploymentContractError(f"Deployment manifest missing '{key}'")
    return data


def validate_manifest(path: Path, expected_target: str | None = None) -> dict:
    manifest = load_manifest(path)
    target = manifest["target"]
    if expected_target is not None and target != expected_target:
        raise DeploymentContractError(f"Deployment target mismatch: manifest={target}, requested={expected_target}")
    validate_target_capabilities(target, manifest["required_capabilities"], _profiles())
    for name, artifact in manifest["artifacts"].items():
        artifact_path = Path(artifact["path"])
        if not artifact_path.is_file():
            raise DeploymentContractError(f"Artifact '{name}' is missing: {artifact_path}")
        if artifact_path.stat().st_size != artifact["size"]:
            raise DeploymentContractError(f"Artifact '{name}' size changed")
        if sha256_file(artifact_path) != artifact["sha256"]:
            raise DeploymentContractError(f"Artifact '{name}' checksum mismatch")
    return manifest
