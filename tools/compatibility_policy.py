#!/usr/bin/env python3
"""H35 compatibility/upgrade policy checker and evidence generator.

This checker deliberately treats compatibility as an allow-list. Version
ordering, semantic-version similarity, or a larger schema number never implies
compatibility. Any contract drift requires an explicit H35 policy update.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "packages" / "robot-isa" / "compatibility_policy.json"
EVIDENCE_PATH = ROOT / ".build" / "h35" / "compatibility-report.json"


class CompatibilityPolicyError(RuntimeError):
    pass


def _git_blob_sha1(path: Path) -> str:
    """Return the canonical Git blob SHA-1 for one governed text contract.

    GitHub's blob identity is based on repository bytes, while a Windows
    checkout may materialize the same text file with CRLF line endings. H35
    fingerprints must describe the repository contract rather than the host
    checkout convention, so normalize CRLF to canonical LF before constructing
    the Git blob object. Lone CR bytes are intentionally left untouched: they
    are content and therefore remain visible as contract drift.
    """
    data = path.read_bytes().replace(b"\r\n", b"\n")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompatibilityPolicyError(f"{path}: top level must be an object")
    return value


def _literal_assignments(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            result[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "frozenset"
                and len(node.value.args) == 1
            ):
                try:
                    result[target.id] = frozenset(ast.literal_eval(node.value.args[0]))
                except (ValueError, TypeError):
                    pass
    return result


def _pair(policy: dict[str, Any], compiler: int, firmware: int, operation: str) -> dict[str, Any] | None:
    matches = [
        row
        for row in policy.get("supported_pairs", [])
        if row.get("compiler_generation") == compiler
        and row.get("firmware_generation") == firmware
    ]
    if len(matches) != 1:
        return None
    row = matches[0]
    if operation not in row.get("operations", []):
        return None
    return row


def check_policy(root: Path = ROOT) -> dict[str, Any]:
    policy_path = root / POLICY_PATH.relative_to(ROOT)
    policy = _load_json(policy_path)
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def require(name: str, condition: bool, detail: str = "") -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})
        if not condition:
            errors.append(f"{name}: {detail}" if detail else name)

    require("policy schema is H35 v1", policy.get("schema_version") == 1 and policy.get("task") == "H35")
    require("policy kind is stable", policy.get("kind") == "robot_compatibility_upgrade_policy")

    current = policy.get("current", {})
    release = (root / "VERSION").read_text(encoding="utf-8").strip()
    require("release VERSION is explicitly governed", release == policy.get("current_release"), f"VERSION={release!r}")

    api = yaml.safe_load((root / "robot-language" / "specification" / "api.yaml").read_text(encoding="utf-8"))
    api_version = str((api or {}).get("language", {}).get("version", ""))
    require("Robot Language version matches policy", api_version == current.get("robot_language_version"), f"api={api_version!r}")

    generation = current.get("platform_contract_generation")
    for label, relative in (
        ("canonical ISA", "packages/robot-isa/canonical_isa.json"),
        ("capability model", "packages/robot-isa/capability_model.json"),
        ("target profiles", "packages/robot-isa/target_profiles.json"),
    ):
        doc = _load_json(root / relative)
        require(
            f"{label} schema matches platform contract generation",
            doc.get("schema_version") == generation,
            f"schema={doc.get('schema_version')!r}, generation={generation!r}",
        )

    fingerprints = policy.get("contract_fingerprints", {})
    require("contract fingerprint set is non-empty", isinstance(fingerprints, dict) and bool(fingerprints))
    actual_fingerprints: dict[str, str] = {}
    for name, entry in sorted(fingerprints.items()):
        path_value = entry.get("path") if isinstance(entry, dict) else None
        expected = entry.get("git_blob_sha1") if isinstance(entry, dict) else None
        path = root / str(path_value or "")
        require(f"{name} fingerprint path exists", bool(path_value) and path.is_file(), str(path_value))
        if not path.is_file():
            continue
        actual = _git_blob_sha1(path)
        actual_fingerprints[name] = actual
        require(
            f"{name} contract fingerprint is frozen",
            actual == expected,
            f"expected={expected}, actual={actual}",
        )

    compiler_generation = current.get("compiler_generation")
    firmware_generation = current.get("firmware_generation")
    legacy_generation = policy.get("legacy", {}).get("unversioned_firmware_generation")
    require("compiler generation is a positive integer", isinstance(compiler_generation, int) and compiler_generation > 0)
    require("firmware generation is a positive integer", isinstance(firmware_generation, int) and firmware_generation > 0)
    require("legacy unversioned firmware is generation 0", legacy_generation == 0)

    rows = policy.get("supported_pairs", [])
    pair_keys = [
        (row.get("compiler_generation"), row.get("firmware_generation"))
        for row in rows
        if isinstance(row, dict)
    ]
    require("compatibility pairs are unique", len(pair_keys) == len(set(pair_keys)))
    for operation in ("compile", "first_flash", "ota", "run"):
        require(
            f"current compiler/firmware pair explicitly supports {operation}",
            _pair(policy, compiler_generation, firmware_generation, operation) is not None,
        )
    require(
        "legacy firmware has explicit one-way OTA upgrade path",
        _pair(policy, compiler_generation, legacy_generation, "ota_upgrade") is not None,
    )
    require(
        "legacy firmware is not silently accepted as current run compatibility",
        _pair(policy, compiler_generation, legacy_generation, "run") is None,
    )
    require(
        "unknown future firmware generation is rejected by matrix",
        _pair(policy, compiler_generation, firmware_generation + 1, "ota") is None,
    )

    rules = policy.get("upgrade_rules", {})
    require("forward compatibility is explicit-only", rules.get("forward_compatibility") == "explicit_only")
    require("backward compatibility is explicit-only", rules.get("backward_compatibility") == "explicit_only")
    require("unknown generations reject", rules.get("unknown_generation") == "reject")
    require("contract drift requires generation bump", rules.get("contract_change_requires_generation_bump") is True)
    require("schema changes require migration adapter", rules.get("migration_adapter_required_for_schema_change") is True)
    require("semver never implies compatibility", rules.get("semantic_version_alone_never_implies_compatibility") is True)

    migrations = policy.get("migrations", [])
    migration_ok = any(
        isinstance(row, dict)
        and row.get("from_firmware_generation") == legacy_generation
        and row.get("to_firmware_generation") == firmware_generation
        and row.get("status") == "supported"
        for row in migrations
    )
    require("legacy-to-current firmware migration is documented", migration_ok)

    runtime_values = _literal_assignments(root / "robostudio" / "domain" / "compatibility.py")
    require("runtime release projection matches policy", runtime_values.get("CURRENT_RELEASE") == policy.get("current_release"))
    require("runtime compiler generation matches policy", runtime_values.get("CURRENT_COMPILER_GENERATION") == compiler_generation)
    require("runtime firmware generation matches policy", runtime_values.get("CURRENT_FIRMWARE_GENERATION") == firmware_generation)
    require("runtime legacy generation matches policy", runtime_values.get("LEGACY_UNVERSIONED_FIRMWARE_GENERATION") == legacy_generation)
    require(
        "runtime known firmware generations are explicit",
        runtime_values.get("KNOWN_FIRMWARE_GENERATIONS") == frozenset({legacy_generation, firmware_generation}),
    )

    identity_h = (root / "robot-platform" / "main" / "src" / "Communication" / "RobotIdentity.h").read_text(encoding="utf-8")
    schema_match = re.search(r"kSchemaVersion\s*=\s*(\d+)", identity_h)
    firmware_match = re.search(r"kCompatibilityGeneration\s*=\s*(\d+)", identity_h)
    require(
        "firmware discovery schema matches policy",
        bool(schema_match) and int(schema_match.group(1)) == current.get("discovery_schema"),
    )
    require(
        "firmware advertises current compatibility generation",
        bool(firmware_match) and int(firmware_match.group(1)) == firmware_generation,
    )

    identity_cpp = (root / "robot-platform" / "main" / "src" / "Communication" / "RobotIdentity.cpp").read_text(encoding="utf-8")
    require(
        "firmware discovery protocol matches policy",
        str(current.get("discovery_protocol")) in identity_cpp,
    )
    require(
        "firmware identity publishes compatibility_generation",
        "compatibility_generation" in identity_cpp and "kCompatibilityGeneration" in identity_cpp,
    )

    discovery_py = (root / "robostudio" / "services" / "robot_discovery_service.py").read_text(encoding="utf-8")
    require("RoboStudio discovery records compatibility generation", "compatibility_generation" in discovery_py)
    require("RoboStudio discovery normalizes legacy generation explicitly", "normalize_firmware_generation" in discovery_py)

    report = {
        "schema_version": 1,
        "task": "H35",
        "kind": "compatibility_policy_evidence",
        "status": "PASS" if not errors else "FAIL",
        "release": release,
        "policy_version": policy.get("policy_version"),
        "current": current,
        "legacy_generation": legacy_generation,
        "supported_pair_count": len(rows),
        "contract_fingerprints": actual_fingerprints,
        "checks": checks,
        "errors": errors,
    }
    return report


def main() -> int:
    try:
        report = check_policy()
    except Exception as exc:
        print(f"H35 compatibility checker error: {exc}", file=sys.stderr)
        return 2

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "H35 compatibility: "
        f"release={report['release']} compiler_gen={report['current'].get('compiler_generation')} "
        f"firmware_gen={report['current'].get('firmware_generation')} "
        f"pairs={report['supported_pair_count']} errors={len(report['errors'])}"
    )
    print(f"Evidence: {EVIDENCE_PATH}")
    if report["errors"]:
        for error in report["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("H35 Compatibility / Upgrade Policy: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
