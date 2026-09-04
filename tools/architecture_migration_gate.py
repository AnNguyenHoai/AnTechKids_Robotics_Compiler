#!/usr/bin/env python3
"""Validate H26-I architecture migration and legacy-retirement boundaries."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "packages" / "robot-isa" / "architecture_manifest.json"
CANONICAL_ISA_PATH = ROOT / "packages" / "robot-isa" / "canonical_isa.json"
GENERATED_OPCODE_PATH = ROOT / "robot-compiler" / "compiler" / "generated" / "opcode.py"
SOURCE_EXTENSIONS = {".py", ".h", ".hpp", ".c", ".cc", ".cpp"}


class MigrationGateError(RuntimeError):
    pass


def _repo_path(value: str) -> Path:
    return ROOT / value


def _canonical_repo_path(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationGateError(f"Cannot load architecture manifest: {path}") from exc
    if data.get("schema_version") != 1 or data.get("task") != "H26-I":
        raise MigrationGateError("architecture_manifest.json must declare schema_version=1 and task=H26-I")
    return data


def validate_paths(manifest: dict) -> None:
    production = manifest["production"]
    required = [
        production["isa_source_of_truth"],
        production["compiler_entrypoint"],
        production["build_entrypoint"],
        production["firmware_build_entrypoint"],
        production["deployment_entrypoint"],
        production["runtime_boundary"],
    ]
    required.extend(manifest["canonical_paths"])
    required.extend(item["path"] for item in manifest["legacy_components"])
    required.extend(manifest.get("validation_paths", []))
    missing = [value for value in required if not _repo_path(value).exists()]
    if missing:
        raise MigrationGateError("Missing architecture path(s): " + ", ".join(missing))


def parse_generated_opcodes() -> dict[str, int]:
    text = GENERATED_OPCODE_PATH.read_text(encoding="utf-8")
    return {
        name: int(value)
        for name, value in re.findall(r"^    (\w+) = (\d+)$", text, flags=re.MULTILINE)
    }


def validate_canonical_isa() -> None:
    try:
        data = json.loads(CANONICAL_ISA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MigrationGateError("Cannot load canonical ISA manifest") from exc

    rows = data.get("rows", [])
    if not rows:
        raise MigrationGateError("Canonical ISA contains no rows")

    ids = [row[0] for row in rows]
    names = [row[1] for row in rows]
    codes = [row[2] for row in rows]
    generated = parse_generated_opcodes()

    if len(ids) != len(set(ids)):
        raise MigrationGateError("Canonical ISA contains duplicate semantic IDs")
    if len(names) != len(set(names)):
        raise MigrationGateError("Canonical ISA contains duplicate producer names")
    if len(codes) != len(set(codes)):
        raise MigrationGateError("Canonical ISA contains duplicate numeric opcodes")

    mismatches = [
        f"{name}: canonical={code}, generated={generated.get(name)}"
        for name, code in zip(names, codes)
        if generated.get(name) != code
    ]
    if mismatches:
        raise MigrationGateError("Canonical/generated opcode drift: " + "; ".join(mismatches))


def iter_source_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in SOURCE_EXTENSIONS:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        if "__pycache__" in path.parts:
            continue
        yield path


def _path_key(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        relative = path
    return _canonical_repo_path(str(relative))


def _is_legacy_component_path(path: Path, legacy_paths: set[str]) -> bool:
    return _path_key(path) in legacy_paths


def _is_validation_path(path: Path, validation_paths: set[str]) -> bool:
    return _path_key(path) in validation_paths


def _legacy_reference_patterns(legacy: dict) -> list[tuple[str, re.Pattern[str]]]:
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for token in legacy.get("forbidden_production_tokens", []):
        normalized = token.replace("\\", "/")
        if normalized == "robot-common" or "robot-common/" in normalized:
            pattern = re.compile(
                r"(?i)(?:packages[./\\]robot-common(?:[/\\.]|\\b)|robot-common[/\\])"
            )
        elif normalized.endswith((".h", ".hpp", ".c", ".cc", ".cpp")):
            filename = re.escape(normalized.rsplit("/", 1)[-1])
            pattern = re.compile(rf"(?im)^\s*#\s*include\s*[<\"][^>\"]*{filename}[>\"]")
        else:
            escaped = re.escape(token)
            pattern = re.compile(rf"(?<![A-Za-z0-9_.-]){escaped}(?![A-Za-z0-9_.-])")
        patterns.append((token, pattern))
    return patterns


def validate_legacy_isolation(manifest: dict) -> None:
    roots = [_repo_path(value) for value in manifest["production_scan_roots"]]
    legacy_paths = {_canonical_repo_path(item["path"]) for item in manifest["legacy_components"]}
    validation_paths = {
        _canonical_repo_path(value) for value in manifest.get("validation_paths", [])
    }
    offenders: list[str] = []

    for legacy in manifest["legacy_components"]:
        legacy_path = _canonical_repo_path(legacy["path"])
        patterns = _legacy_reference_patterns(legacy)
        for root in roots:
            for path in iter_source_files(root):
                if _is_legacy_component_path(path, legacy_paths):
                    continue
                if _is_validation_path(path, validation_paths):
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                hits = [token for token, pattern in patterns if pattern.search(text)]
                if hits:
                    offenders.append(
                        f"{_path_key(path)} references isolated legacy component {legacy_path}: {', '.join(hits)}"
                    )

    if offenders:
        raise MigrationGateError("Legacy isolation violated:\n" + "\n".join(offenders))


def validate_retirement_policy(manifest: dict) -> None:
    policy = manifest["retirement_policy"]
    if policy.get("allow_delete") is not False:
        raise MigrationGateError("H26-I retirement policy must keep allow_delete=false")
    required = policy.get("required_evidence", [])
    expected = {
        "canonical semantic equivalence",
        "unified E2E oracle pass",
        "firmware build pass",
        "physical validation gate",
    }
    if set(required) != expected:
        raise MigrationGateError("H26-I retirement evidence set is incomplete or changed")
    for legacy in manifest["legacy_components"]:
        if legacy.get("status") != "legacy-isolated":
            raise MigrationGateError(
                f"Legacy component {legacy['path']} must remain explicitly legacy-isolated"
            )
        if legacy.get("retirement") != "blocked-until-equivalence":
            raise MigrationGateError(
                f"Legacy component {legacy['path']} is not protected by the equivalence gate"
            )


def run_gate() -> dict:
    manifest = load_manifest()
    validate_paths(manifest)
    validate_canonical_isa()
    validate_legacy_isolation(manifest)
    validate_retirement_policy(manifest)
    return {
        "task": "H26-I",
        "status": "PASS",
        "allow_legacy_delete": False,
        "canonical_source_of_truth": manifest["production"]["isa_source_of_truth"],
        "legacy_components": len(manifest["legacy_components"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run H26-I architecture migration gate")
    parser.add_argument("--report", help="Optional JSON report path")
    args = parser.parse_args()
    try:
        report = run_gate()
    except MigrationGateError as exc:
        report = {"task": "H26-I", "status": "FAIL", "error": str(exc)}
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"H26-I architecture migration gate: FAIL\n{exc}")
        return 1

    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("H26-I architecture migration gate: PASS")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
