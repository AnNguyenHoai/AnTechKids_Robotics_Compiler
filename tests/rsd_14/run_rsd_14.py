#!/usr/bin/env python3
"""RSD-14 deployment process/error-boundary regression tests."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import deployment_runtime


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except Exception as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: compilation unexpectedly succeeded")


def test_output_and_exit_code() -> None:
    lines: list[str] = []
    result = deployment_runtime.run_process(
        [sys.executable, "-c", "import sys; print('stdout'); print('stderr', file=sys.stderr); sys.exit(7)"],
        cwd=ROOT,
        timeout=5.0,
        on_output=lines.append,
    )
    check("non-zero exit is returned", result.returncode == 7)
    check("combined output is retained", "stdout" in result.output and "stderr" in result.output)
    check("output callback receives process lines", "stdout\n" in "".join(lines) and "stderr\n" in "".join(lines))


def test_timeout_is_bounded() -> None:
    started = time.monotonic()
    try:
        deployment_runtime.run_process(
            [sys.executable, "-c", "import time; print('before-timeout', flush=True); time.sleep(30)"],
            cwd=ROOT,
            timeout=0.5,
        )
    except deployment_runtime.DeploymentRuntimeError as exc:
        elapsed = time.monotonic() - started
        check("timeout raises deployment error", "timed out" in str(exc))
        check("timeout remains bounded", elapsed < 8.0)
        check("timeout preserves diagnostic output", "before-timeout" in str(exc))
    else:
        raise AssertionError("timeout unexpectedly succeeded")


def test_invalid_process_contracts() -> None:
    expect_error(
        "empty command is rejected",
        lambda: deployment_runtime.run_process([], cwd=ROOT),
        "must not be empty",
    )
    expect_error(
        "non-positive timeout is rejected",
        lambda: deployment_runtime.run_process([sys.executable, "-c", "pass"], cwd=ROOT, timeout=0),
        "greater than zero",
    )


def main() -> int:
    test_output_and_exit_code()
    test_timeout_is_bounded()
    test_invalid_process_contracts()
    print("RSD-14 process/error boundary checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
