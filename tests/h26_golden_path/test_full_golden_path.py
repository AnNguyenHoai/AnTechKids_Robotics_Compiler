"""Regression tests for the H26 full golden-path orchestrator."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "h26_golden_path" / "run_full_golden_path.py"
AUDIT = ROOT / "tests" / "h26_runner_audit" / "run_h26_runner_audit.py"


def load_runner_module():
    namespace = {"__file__": str(RUNNER)}
    exec(RUNNER.read_text(encoding="utf-8"), namespace)
    return namespace


def test_golden_path_runner_is_valid_python():
    ast.parse(RUNNER.read_text(encoding="utf-8"), filename=str(RUNNER))


def test_golden_path_runner_discovers_h26_acceptance_gates():
    module = load_runner_module()
    runners = module["acceptance_runners"]()
    assert runners
    assert AUDIT not in runners
    assert RUNNER not in runners
    assert all(path.name.startswith("run_") for path in runners)
    assert all(path.is_file() for path in runners)


def test_golden_path_runner_does_not_self_recurse():
    module = load_runner_module()
    runners = module["acceptance_runners"]()
    resolved = {path.resolve() for path in runners}
    assert RUNNER.resolve() not in resolved


def test_golden_path_runner_executes_with_current_python():
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"), filename=str(RUNNER))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    ]
    assert calls
    assert any(
        any(
            isinstance(item, ast.Attribute)
            and isinstance(item.value, ast.Name)
            and item.value.id == "sys"
            and item.attr == "executable"
            for item in call.args[0].elts
        )
        for call in calls
        if call.args and isinstance(call.args[0], (ast.List, ast.Tuple))
    )


def test_golden_path_runner_has_deterministic_failure_summary():
    source = RUNNER.read_text(encoding="utf-8")
    assert "Gates discovered:" in source
    assert "Gates failed:" in source
    assert "H26 Golden Path Regression: FAIL" in source
    assert "H26 Golden Path Regression: PASS" in source
