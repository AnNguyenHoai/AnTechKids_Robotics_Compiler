# H27-A Final Audit

## Purpose

H27-A closes the H27 acceptance line by proving that every H27 acceptance runner is present, portable, syntactically valid, and executable from the repository root using the active Python interpreter.

## Scope

The audit automatically discovers `tests/h27_*/run_*.py`. It therefore covers the current H27-A.1 discovery/identity hardening gate, H27-B0 first-flash bootstrap gate, H27-B RoboStudio regression gate, and any future H27 acceptance runner added under the same convention.

The final-audit runner itself is excluded from execution to prevent self-recursion.

## Contract

Every discovered H27 acceptance runner must:

- derive the repository root with `Path(__file__).resolve().parents[2]`;
- compile successfully as Python;
- avoid importing `pytest`;
- avoid invoking pytest as a subprocess;
- be executable with the active `sys.executable`.

The audit first validates these properties for every runner. Only runners that satisfy the contract are executed.

## Execution

From the repository root:

```text
python tests\h27_a_final_audit\run_h27_a_final_audit.py
```

The audit continues after an individual gate failure and reports every failing runner. Exit code `0` is emitted only when all discovered gates pass.

## Expected Result

```text
H27-A Final Audit: PASS
```

A successful result means the H27 acceptance surface is closed at the runner level. It does not replace physical hardware/network validation where an individual H27 gate requires it.
