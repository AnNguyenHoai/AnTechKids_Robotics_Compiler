# H26 Acceptance Runner Audit

## Purpose

Keep H26 acceptance gates portable and deterministic on the supported target-machine Python runtime.

The gates must not regress to depending on a broken or unrelated local `pytest` installation.

## Scope

The audit discovers every `tests/h26_*/run_*.py` runner, including H26 OTA.

## Required invariants

1. **No pytest dependency**
   - no `pytest` imports
   - no `pytest` subprocess invocation
2. **CWD independent**
   - runner paths are derived from `Path(__file__).resolve()` rather than the caller's working directory
3. **Python-valid runner**
   - every discovered runner must compile successfully with the supported Python interpreter
4. **Deterministic discovery**
   - runner discovery is sorted and the audit fails if no H26 acceptance runner exists

## Gate

Run from the repository root or any other working directory:

```text
python tests\h26_runner_audit\run_h26_runner_audit.py
```

Expected result:

```text
H26 Acceptance Runner Audit: PASS
```

## Non-goals

This audit does not replace the individual H26 acceptance tests, firmware tests, compiler tests, or physical validation. It verifies the **runner infrastructure** that launches those gates.
