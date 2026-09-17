# RSD-20-P.1 — Production Release Artifact Assembly

> **RSD-22 authority notice:** This document defines release artifact assembly only. The production release boundary is defined by `RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md`.

## Objective

Provide one repository-owned command that turns the real, already-built RoboStudio application/runtime inputs into a release artifact suitable for portable proof.

This task is intentionally **not** the GUI/compiler build system. The upstream production build must first produce the application executable and application-owned inputs required by the current release contract.

## Canonical command

Run from any current working directory:

```powershell
python <repository>\tools\production_release_assembly.py `
  --executable <path-to-RoboStudio.exe> `
  --runtime-resources <path-to-runtime-resources> `
  --version-file <path-to-VERSION> `
  --source-revision <git-revision>
```

The current implementation does not require portable Python/PlatformIO inputs because those remain target-machine prerequisites. RSD-23 is responsible for changing that boundary when application-owned runtimes are introduced.

## Produced artifact

The ZIP is the user-facing release artifact and is the unit copied to another machine.

Release evidence remains traceable to the same source revision and version.

## Pipeline

```text
explicit production inputs
        ↓
RSD-17 production distribution
        ↓
RSD-07 distribution assembly
        ↓
RSD-09 release packaging
        ↓
RSD-18 provenance
        ↓
RSD-20-P portable proof
        ↓
PASS / release artifact
```

## Fail-closed rules

Assembly fails when a required input is missing, output is placed inside an input source tree, VERSION is unsafe, or a downstream release gate fails.

## Important boundary

RSD-20-P.1 can assemble a production release only after the upstream build has provided real artifacts. It does not fake `RoboStudio.exe`, create a Python runtime from a developer installation, or download PlatformIO.

The final zero-development-machine packaging target is defined by RSD-22 and implemented by RSD-23.

## Verification

```powershell
python tests\rsd_20_p1\run_rsd_20_p1.py
python run_all_tests.py
```
