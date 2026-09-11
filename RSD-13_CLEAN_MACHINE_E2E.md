# RSD-13 — Clean-Machine End-to-End Execution

## Objective

Close the gap between a portable release artifact being structurally valid and
its application-owned runtime actually starting on a clean machine boundary.

RSD-13 exercises a real child process using the packaged Python runtime while
running from an unrelated working directory and while supplying hostile
host Python/PlatformIO variables. The test deliberately does not require a
GUI/display or a physical robot.

## Contract

A packaged RoboStudio runtime is execution-ready only when:

- the portable interpreter exists under `runtime/bin`;
- the child process is started through an absolute application-owned path;
- the child process starts successfully within a bounded timeout;
- the child keeps the caller-selected working directory outside the application;
- `ROBOSTUDIO_HOME` identifies the packaged application root;
- PlatformIO core, platforms and packages resolve under `runtime/platformio`;
- host `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV` and `PIOHOME_DIR` cannot leak into
  the packaged runtime;
- the packaged runtime preflight is performed against the explicit application
  root rather than the current working directory or process environment;
- missing portable Python fails before a child process is started;
- an application-root working directory is rejected by the clean-machine gate.

## Canonical API

`tools/clean_machine_e2e.py` provides:

- `execute_clean_machine_probe(root, cwd, base_env=None, timeout=30.0)` —
  execute the application-owned Python runtime under a hostile host environment;
- `CleanMachineE2EReport` — machine-readable execution result;
- `CleanMachineE2EError` — fail-closed execution/preflight error.

The probe uses a real subprocess and `shell=False`; it is not a mocked process
execution. The GUI itself remains outside this automated gate because GUI startup
requires a display and is long-lived.

## Verification

Run:

```powershell
python tests\rsd_13\run_rsd_13.py
python tests\rsd_12\run_rsd_12.py
python tests\rsd_11\run_rsd_11.py
python run_all_tests.py
```

For release qualification, RSD-13 should additionally be exercised against the
actual release ZIP on a Windows machine with no host PlatformIO installation.
