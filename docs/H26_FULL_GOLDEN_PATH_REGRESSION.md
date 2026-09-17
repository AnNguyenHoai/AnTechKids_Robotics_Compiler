# H26 Full Golden Path Regression

## Purpose

Provide one deterministic, portable command that executes the complete H26 acceptance suite and returns a single regression result.

## Execution order

1. Run the H26 Acceptance Runner Audit.
2. Discover every `tests/h26_*/run_*.py` acceptance runner, in sorted path order.
3. Execute every discovered H26 gate with the active Python interpreter.
4. Continue after individual failures so the final output identifies every failing gate.
5. Return exit code `0` only when every gate passes.

The runner itself does not invoke pytest.

## Gate

From the repository root:

```text
python tests\h26_golden_path\run_full_golden_path.py
```

The command is also CWD-independent because the runner derives the repository root from its own `__file__` location and executes each gate with that root as its working directory.

## Scope

This is an orchestration gate. It does not replace the individual H26 acceptance tests. Existing H26-A through H26-O and H26 OTA gates remain the owners of their respective contracts; this runner proves that the complete set can be executed together and that no individual gate is silently skipped.

## Failure semantics

Any failed gate produces:

```text
H26 Golden Path Regression: FAIL
```

and a non-zero process exit code. The summary lists every failed runner.

## Success semantics

When all discovered H26 acceptance gates pass:

```text
H26 Golden Path Regression: PASS
```

with exit code `0`.
