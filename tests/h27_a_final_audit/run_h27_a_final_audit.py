#!/usr/bin/env python3
"""H27-A Final Audit: execute and validate the complete H27 acceptance surface."""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
AUDIT_RUNNER = ROOT / "tests" / "h27_a_final_audit" / "run_h27_a_final_audit.py"


def acceptance_runners() -> list[Path]:
    """Discover deterministic H27 acceptance runners, excluding audit infrastructure."""
    runners = sorted(ROOT.glob("tests/h27_*/run_*.py"))
    excluded = {SELF.resolve(), AUDIT_RUNNER.resolve()}
    return [path for path in runners if path.resolve() not in excluded]


def audit_runner_contract(path: Path) -> None:
    """Reject H27 runners that violate the portable standalone-runner contract."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert not any(
        (isinstance(node, ast.Import) and any(alias.name == "pytest" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "pytest")
        for node in imports
    ), f"pytest import in {path}"
    assert "-m" not in source or "pytest" not in source, f"pytest subprocess in {path}"
    expected_root = "Path(__file__).resolve().parents[2]"
    assert expected_root in source, f"runner must derive repository root: {path}"
    compile(source, str(path), "exec")


def run_gate(path: Path) -> int:
    print(f"=== Running {path.relative_to(ROOT)} ===", flush=True)
    result = subprocess.run([sys.executable, str(path)], cwd=ROOT)
    status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
    print(f"--- {path.name}: {status} ---", flush=True)
    return result.returncode


def main() -> int:
    runners = acceptance_runners()
    if not runners:
        print("H27-A Final Audit: FAIL (no acceptance runners discovered)")
        return 1

    print(f"H27-A Final Audit: discovered {len(runners)} acceptance runner(s)")
    failures: list[Path] = []
    contract_failures: list[Path] = []

    for runner in runners:
        try:
            audit_runner_contract(runner)
        except (AssertionError, SyntaxError, OSError) as exc:
            print(f"CONTRACT FAIL: {runner}: {exc}")
            contract_failures.append(runner)

    for runner in runners:
        if runner in contract_failures:
            failures.append(runner)
            continue
        if run_gate(runner) != 0:
            failures.append(runner)

    print("=== H27-A Final Audit Summary ===")
    print(f"Runners discovered: {len(runners)}")
    print(f"Contract failures: {len(contract_failures)}")
    print(f"Execution failures: {len(failures) - len(contract_failures)}")
    if failures:
        for path in failures:
            print(f"FAILED: {path.relative_to(ROOT)}")
        print("H27-A Final Audit: FAIL")
        return 1

    print("H27-A Final Audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
