# RSD-14 — Production Process & Error Boundary

## Objective

Make compiler/build/deployment subprocess execution deterministic, bounded and
safe for a long-lived RoboStudio application.

## Contract

The deployment process boundary must:

- reject an empty command;
- reject a non-positive timeout;
- invoke child processes without a shell;
- keep the child in an isolated process group/session;
- stream combined stdout/stderr without coupling the runner to the GUI;
- retain diagnostic output for non-zero exits and timeout failures;
- enforce a hard timeout using a monotonic deadline;
- terminate the complete child process tree on timeout where the host supports it;
- force-kill the process tree if graceful termination does not finish;
- leave no intentionally orphaned compiler/PlatformIO descendant after a timeout;
- preserve the caller environment object rather than mutating it.

## Canonical API

`tools.deployment_runtime.run_process(...)` is the canonical subprocess boundary.
It returns `ProcessResult(returncode, output)` for completed processes and raises
`DeploymentRuntimeError` for start/timeout failures.

## Verification

Run:

```powershell
python tests\rsd_14\run_rsd_14.py
python tests\rsd_13\run_rsd_13.py
python tests\rsd_12\run_rsd_12.py
python run_all_tests.py
```

RSD-14 does not launch the Qt GUI or require a physical robot. GUI responsiveness
and real hardware upload remain release-qualification concerns; the process
boundary underneath those operations is tested here with real child processes.
