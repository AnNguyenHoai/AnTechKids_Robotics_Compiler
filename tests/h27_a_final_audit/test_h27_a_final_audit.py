#!/usr/bin/env python3
"""Regression tests for the H27-A Final Audit runner."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "h27_a_final_audit" / "run_h27_a_final_audit.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("h27_a_final_audit", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_is_valid_python():
    ast.parse(RUNNER.read_text(encoding="utf-8"), filename=str(RUNNER))


def test_runner_discovers_expected_h27_surface():
    module = load_runner()
    runners = module.acceptance_runners()
    names = {path.as_posix() for path in runners}
    assert any("tests/h27_a1/run_h27_a1.py" in name for name in names)
    assert any("tests/h27_b0/run_h27_b0.py" in name for name in names)
    assert any("tests/h27_b/run_h27_b.py" in name for name in names)
    assert RUNNER.resolve() not in {path.resolve() for path in runners}


def test_all_discovered_runners_obey_portable_contract():
    module = load_runner()
    for runner in module.acceptance_runners():
        module.audit_runner_contract(runner)


def test_runner_uses_current_python_and_expected_summary():
    source = RUNNER.read_text(encoding="utf-8")
    assert "subprocess.run([sys.executable, str(path)], cwd=ROOT)" in source
    assert "H27-A Final Audit: PASS" in source
    assert "H27-A Final Audit: FAIL" in source
    assert "Contract failures:" in source
    assert "Execution failures:" in source
