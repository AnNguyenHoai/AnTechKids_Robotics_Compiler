"""Static audit for portable H26 acceptance runners.

The H26 acceptance gates are intended to run on target/developer machines
with the supported Python runtime and without a locally installed pytest.
This audit prevents regression to the failure mode fixed by H26-L/M/OTA/O.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = ROOT / "tests"


def acceptance_runners():
    """Return all H26 acceptance runner scripts in deterministic order."""
    runners = sorted(TESTS_ROOT.glob("h26_*/run_*.py"))
    assert runners, "No H26 acceptance runners discovered"
    return runners


def parse_runner(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def pytest_dependency_references(tree: ast.AST):
    """Find imports or subprocess invocations that require pytest."""
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest" or alias.name.startswith("pytest."):
                    violations.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "pytest" or (node.module and node.module.startswith("pytest.")):
                violations.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Call):
            func = node.func
            is_subprocess_call = (
                isinstance(func, ast.Attribute)
                and func.attr in {"run", "check_call", "check_output"}
                and isinstance(func.value, ast.Name)
                and func.value.id == "subprocess"
            )
            if not is_subprocess_call or not node.args:
                continue
            command = node.args[0]
            if isinstance(command, (ast.List, ast.Tuple)):
                values = [
                    item.value
                    for item in command.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                ]
                if "pytest" in values:
                    violations.append("subprocess invocation of pytest")
    return violations


def runner_root_resolution_violations(path: Path):
    """Ensure each runner derives paths from its own file, not cwd."""
    source = path.read_text(encoding="utf-8")
    if "Path(__file__).resolve().parents[2]" not in source:
        return ["runner does not derive repository root from __file__"]
    return []


def test_all_h26_acceptance_runners_are_discovered():
    runners = acceptance_runners()
    assert all(path.name.startswith("run_") for path in runners)
    assert all(path.is_file() for path in runners)


def test_h26_acceptance_runners_do_not_depend_on_pytest():
    violations = []
    for path in acceptance_runners():
        tree = parse_runner(path)
        for violation in pytest_dependency_references(tree):
            violations.append(f"{path.relative_to(ROOT)}: {violation}")
    assert not violations, "H26 acceptance runners must not depend on pytest: " + "; ".join(violations)


def test_h26_acceptance_runners_are_cwd_independent():
    violations = []
    for path in acceptance_runners():
        for violation in runner_root_resolution_violations(path):
            violations.append(f"{path.relative_to(ROOT)}: {violation}")
    assert not violations, "H26 acceptance runners must resolve paths from __file__: " + "; ".join(violations)


def test_h26_acceptance_runners_compile_as_python():
    failures = []
    for path in acceptance_runners():
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(f"{path.relative_to(ROOT)}: {result.stderr.strip()}")
    assert not failures, "H26 acceptance runner syntax check failed: " + "; ".join(failures)
