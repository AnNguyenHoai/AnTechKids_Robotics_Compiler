#!/usr/bin/env python3
"""H26-B contract drift checker.

The checker is intentionally read-only and non-breaking. It validates the
production Golden Path boundaries and compares the compiler's generated
function registry against its generated opcode contract. It can also enforce
an explicit baseline of protected file blob SHAs so future refactors must
update the baseline deliberately rather than silently changing the path.

Exit codes:
  0: no unexpected drift detected
  1: drift detected or a required contract is missing
  2: invalid checker usage / baseline format
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "docs" / "H26-B_CONTRACT_BASELINE.json"


@dataclass
class Finding:
    check_id: str
    severity: str
    message: str
    path: str | None = None


def git_blob_sha(content: str) -> str:
    data = content.encode("utf-8")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def required_path(findings: list[Finding], path: Path) -> str | None:
    if not path.is_file():
        findings.append(Finding("path-exists", "ERROR", "Required file is missing", str(path.relative_to(ROOT))))
        return None
    return read_text(path)


def check_build_boundary(findings: list[Finding]) -> None:
    build = ROOT / "tools" / "build.py"
    text = required_path(findings, build)
    if text is None:
        return

    rewrite = text.find('"tools" / "rewrite.py"')
    compile_ = text.find('"tools" / "compile.py"')
    rewrite_call = text.find("rewrite_script", text.find("# Rewrite"))
    compile_call = text.find("compile_script", text.find("# Compile"))

    if rewrite < 0 or compile_ < 0:
        findings.append(Finding("build-stage-tools", "ERROR", "build.py no longer declares rewrite.py and compile.py", str(build.relative_to(ROOT))))
    if rewrite_call < 0 or compile_call < 0 or rewrite_call > compile_call:
        findings.append(Finding("build-stage-order", "ERROR", "build.py no longer performs rewrite before compile", str(build.relative_to(ROOT))))
    if "--input" not in text or "--output" not in text:
        findings.append(Finding("build-cli-contract", "ERROR", "build.py no longer forwards input/output artifacts", str(build.relative_to(ROOT))))


def check_compile_boundary(findings: list[Finding]) -> None:
    path = ROOT / "tools" / "compile.py"
    text = required_path(findings, path)
    if text is None:
        return
    required_tokens = [
        "from compiler.compiler import RobotCompiler",
        "from compiler.emitter import HeaderEmitter",
        "compiler.compile(str(input_path))",
        "HeaderEmitter().emit(program, output_header)",
        '"instruction_count"',
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        findings.append(Finding("compile-boundary", "ERROR", f"compile.py is missing required production boundary tokens: {missing}", str(path.relative_to(ROOT))))


def check_flash_boundary(findings: list[Finding]) -> None:
    path = ROOT / "tools" / "flash.py"
    text = required_path(findings, path)
    if text is None:
        return
    required_tokens = [
        'build_dir / "program.h"',
        '"generated_program.h"',
        '"pio", "run", "-t", "upload"',
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        findings.append(Finding("flash-boundary", "ERROR", f"flash.py no longer consumes the protected program artifact/upload flow: {missing}", str(path.relative_to(ROOT))))


def parse_opcode_values(text: str) -> dict[str, int]:
    pattern = re.compile(r"^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+)\s*$", re.MULTILINE)
    return {name: int(value) for name, value in pattern.findall(text)}


def parse_registry_opcodes(text: str) -> dict[str, str]:
    pattern = re.compile(r'"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:\s*\{.*?"opcode"\s*:\s*"([A-Za-z_][A-Za-z0-9_]*)"', re.DOTALL)
    return {func: opcode for func, opcode in pattern.findall(text)}


def check_generated_contract(findings: list[Finding]) -> None:
    opcode_path = ROOT / "robot-compiler" / "compiler" / "generated" / "opcode.py"
    registry_path = ROOT / "robot-compiler" / "compiler" / "generated" / "function_registry.py"
    opcode_text = required_path(findings, opcode_path)
    registry_text = required_path(findings, registry_path)
    if opcode_text is None or registry_text is None:
        return

    opcodes = parse_opcode_values(opcode_text)
    registry = parse_registry_opcodes(registry_text)

    if not opcodes:
        findings.append(Finding("opcode-parse", "ERROR", "No generated Opcode values could be parsed", str(opcode_path.relative_to(ROOT))))
        return
    if not registry:
        findings.append(Finding("registry-parse", "ERROR", "No generated function registry entries could be parsed", str(registry_path.relative_to(ROOT))))
        return

    missing = sorted(set(registry.values()) - set(opcodes))
    if missing:
        findings.append(Finding("registry-opcode-sync", "ERROR", f"Registry references undefined opcodes: {missing}"))

    duplicate_values: dict[int, list[str]] = {}
    for name, value in opcodes.items():
        duplicate_values.setdefault(value, []).append(name)
    duplicates = {value: names for value, names in duplicate_values.items() if len(names) > 1}
    if duplicates:
        findings.append(Finding("opcode-values-unique", "ERROR", f"Generated opcode numeric values are duplicated: {duplicates}", str(opcode_path.relative_to(ROOT))))


def check_program_boundary(findings: list[Finding]) -> None:
    path = ROOT / "robot-platform" / "main" / "src" / "Application" / "generated_program.h"
    text = required_path(findings, path)
    if text is None:
        return
    for token in ["const Instruction generatedProgram[]", "generatedProgramSize"]:
        if token not in text:
            findings.append(Finding("program-artifact-boundary", "ERROR", f"Firmware generated program artifact is missing {token}", str(path.relative_to(ROOT))))


def check_golden_corpus(findings: list[Finding]) -> None:
    golden_dir = ROOT / "robot-platform" / "golden"
    if not golden_dir.is_dir():
        findings.append(Finding("golden-corpus", "ERROR", "Golden program directory is missing", str(golden_dir.relative_to(ROOT))))
        return
    programs = sorted(golden_dir.glob("*.py"))
    if not programs:
        findings.append(Finding("golden-corpus", "ERROR", "Golden program directory is empty", str(golden_dir.relative_to(ROOT))))


def check_protected_baseline(findings: list[Finding], baseline: dict) -> None:
    protected = baseline.get("protected_files", {})
    if not isinstance(protected, dict):
        findings.append(Finding("baseline-format", "ERROR", "protected_files must be an object", str(BASELINE_PATH.relative_to(ROOT))))
        return

    for raw_path, expected_sha in sorted(protected.items()):
        path = ROOT / raw_path
        text = required_path(findings, path)
        if text is None:
            continue
        actual_sha = git_blob_sha(text)
        if actual_sha != expected_sha:
            findings.append(
                Finding(
                    "protected-file-drift",
                    "ERROR",
                    f"Protected baseline changed: expected {expected_sha}, got {actual_sha}",
                    raw_path,
                )
            )


def load_baseline(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Baseline file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON baseline: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Baseline root must be an object")
    return data


def run(check_baseline: bool = True) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    baseline = load_baseline(BASELINE_PATH)
    check_build_boundary(findings)
    check_compile_boundary(findings)
    check_flash_boundary(findings)
    check_generated_contract(findings)
    check_program_boundary(findings)
    check_golden_corpus(findings)
    if check_baseline:
        check_protected_baseline(findings, baseline)
    return findings, baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect contract drift without changing the production Golden Path")
    parser.add_argument("--json", dest="json_path", help="Write machine-readable report to this path")
    parser.add_argument("--no-baseline", action="store_true", help="Skip protected-file blob SHA checks")
    args = parser.parse_args()

    try:
        findings, baseline = run(check_baseline=not args.no_baseline)
    except ValueError as exc:
        print(f"H26-B ERROR: {exc}", file=sys.stderr)
        return 2

    errors = [f for f in findings if f.severity == "ERROR"]
    result = {
        "task": "H26-B",
        "status": "FAIL" if errors else "PASS",
        "baseline_commit": baseline.get("baseline_commit"),
        "checks": [asdict(item) for item in findings],
        "error_count": len(errors),
    }

    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if findings:
        for item in findings:
            prefix = "ERROR" if item.severity == "ERROR" else item.severity
            location = f" [{item.path}]" if item.path else ""
            print(f"{prefix} {item.check_id}: {item.message}{location}")
    else:
        print("PASS H26-B: no contract drift detected")

    print(f"H26-B result: {result['status']} (errors={result['error_count']})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
