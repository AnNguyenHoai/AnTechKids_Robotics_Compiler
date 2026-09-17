# RSD-27 — Deployment Regression Hardening

## Scope

Audit the merged RSD-26 isolated firmware workspace change before moving to the next production-release gate.

## Findings

### 1. RSD-26 regression test was incorrect

The isolation test created `program.h` inside a conditional expression using `Path.write_text()`. Because `write_text()` returns `None`, the test always assigned `None` to `generated` and failed its own assertion.

RSD-27 replaces that with explicit fixture creation and adds coverage for:

- forbidden development payload rejection;
- missing required firmware project files;
- template immutability;
- exclusion of forbidden directories during copy;
- generated-header installation into the workspace only;
- missing generated-header failure.

### 2. Deployment compiler invocation used the host interpreter directly

`deploy_robot.py` invoked `sys.executable` for rewrite and compile. That bypassed the application-owned Python resolver when a managed runtime is available.

RSD-27 routes both compiler helper invocations through `runtime_paths.python_command()`. Source development still falls back to the current interpreter, while packaged/frozen execution is fail-closed if the managed Python runtime is absent.

## RSD-26 invariants retained

- Production/frozen firmware is resolved from `firmware/robot-platform`.
- Source development may use the repository firmware project.
- A writable per-project firmware copy is created before PlatformIO execution.
- `generated_program.h` is never written into the packaged/repository firmware template.
- PlatformIO build/workspace/cache/libdeps/shared directories remain isolated.
- `esp32dev`, `esp32dev_bootstrap`, and `esp32dev_ota` remain supported.

## Verification status

The GitHub connector can inspect and modify repository state, but this environment does not provide the actual Windows + bundled PlatformIO + ESP32 hardware runtime needed to claim physical deployment qualification.

Therefore RSD-27 claims code-level regression hardening, not clean-machine or hardware qualification.

## Next release gates

1. Pin and prove the complete PlatformIO dependency closure.
2. Build firmware in production-style E2E from the packaged firmware payload.
3. Verify production artifact portability on a clean Windows machine.
4. Qualify USB bootstrap/deployment with the real ESP32.
5. Qualify OTA deployment and post-flash health verification with the real ESP32.
