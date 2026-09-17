# RSD-20-P.1 — Production Release Artifact Assembly

> **RSD-22 authority notice:** This document defines release artifact assembly only. RSD-23 owns application runtime packaging.

## Objective

Provide one repository-owned assembly stage that turns real RoboStudio build outputs and application-owned runtime inputs into the release artifact.

## Canonical command

RSD-23 exposes the complete one-command entry point:

```powershell
python <repository>\tools\one_command_production_build.py `
  --executable <path-to-RoboStudio.exe> `
  --runtime-bin <path-to-portable-python> `
  --runtime-platformio <path-to-application-owned-platformio> `
  --runtime-resources <path-to-runtime-resources> `
  --version-file <path-to-VERSION> `
  --source-revision <git-revision> `
  --output <release-output>
```

The command is independent of the caller's CWD and packages Python/PlatformIO inside the final ZIP.

## Fail-closed rules

Assembly fails when any required input is missing, the runtime contains a developer virtual environment, output is inside an input source tree, VERSION is unsafe, or a downstream release gate fails.

## Verification

```powershell
python tests\rsd_20_p1\run_rsd_20_p1.py
python tests\rsd_23\run_rsd_23.py
python run_all_tests.py
```
