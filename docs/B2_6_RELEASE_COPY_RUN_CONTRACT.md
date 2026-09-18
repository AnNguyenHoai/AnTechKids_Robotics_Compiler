# B2.6 — Release / Copy-and-Run Contract

## 1. Goal

B2.6 closes the portable release chain with one explicit user contract:

> Copy the production ZIP to another Windows machine, extract it, and run RoboStudio without installing the development environment.

The supported delivery flow is:

`copy ZIP -> extract -> RoboStudio.cmd -> RoboStudio.exe -> compile -> connect COM -> flash -> robot runs`

B2.6 does not claim that a physical robot has passed B2.5. Physical acceptance remains a separate real-machine observation. B2.6 makes the release artifact self-describing and machine-verifiable so that the ZIP delivered for that acceptance has one unambiguous runtime contract.

## 2. Canonical release command

The canonical production build remains:

```powershell
python tools/one_command_production_build.py `
  --executable <path-to-RoboStudio.exe> `
  --runtime-bin <portable-python-root> `
  --runtime-platformio <packaged-platformio-root> `
  --runtime-resources <runtime-resources-root> `
  --firmware-root robot-platform `
  --source-revision <git-sha> `
  --output <release-output>
```

The one-command build now runs the B2.6 finalization boundary before returning PASS.

A production artifact is not B2.6-ready merely because an older RSD assembly command produced a ZIP. The final ZIP must pass the B2.6 gate below.

## 3. Contract inside the ZIP

Every B2.6 production ZIP contains:

`copy-run-contract.json`

The contract is a first-class distribution inventory item. Its size and SHA-256 are recorded in `distribution-manifest.json`, and the final release manifest records the same file as part of the immutable ZIP payload.

The contract declares:

- delivery model: `copy-extract-run`;
- platform: Windows;
- primary launcher: `RoboStudio.cmd`;
- application executable: the packaged `RoboStudio.exe` name;
- acceptance probe: `<RoboStudio.exe> --acceptance-probe`;
- physical E2E runner: bundled Python with `-I -B` and `tools/clean_machine_physical_e2e.py`;
- bundled Python: `runtime/bin/python.exe`;
- bundled PlatformIO: `runtime/platformio`;
- compiler: `compiler/main.py`;
- firmware project: `firmware/robot-platform`;
- dependency mode: `artifact-closed`;
- mutable state: external user state, never inside the release tree;
- default Windows state location: `%LOCALAPPDATA%/RoboStudio`;
- state override: `ROBOSTUDIO_STATE_ROOT`;
- relocation support: no absolute build paths and no current-working-directory dependency.

## 4. Host dependency contract

A B2.6 ZIP must explicitly state that these are **not** target-machine requirements:

- source checkout;
- global Python;
- global Node.js;
- global PlatformIO;
- global compiler/toolchain;
- developer virtual environment.

The only allowed external hardware-side prerequisites are:

- the OS/USB-UART driver needed to expose the robot COM port for flashing;
- a physical robot when final B2.5 behavior is being accepted.

These external hardware prerequisites must never be used as a reason to borrow host Python, PlatformIO, compiler, or source files.

## 5. Finalization sequence

`tools/copy_run_release.py` performs the B2.6 finalization boundary:

1. Validate the already assembled production distribution.
2. Generate canonical `copy-run-contract.json` using only relative artifact paths.
3. Add the contract to `distribution-manifest.json` with size and SHA-256.
4. Mark the distribution `copy_run_ready=true`.
5. Revalidate the distribution inventory.
6. Re-run production runtime closure.
7. Rebuild the release ZIP.
8. Rebuild provenance for the new immutable ZIP hash.
9. Re-run portable release proof.
10. Open the final ZIP and validate the copy-run contract from inside the archive.

The assembly report is rewritten with the final B2.6 artifact SHA and B2.6 validation evidence.

## 6. Independent verification

A copied ZIP can be checked without using staging/source paths:

```powershell
python tools/copy_run_release.py <RoboStudio-x.y.z-Windows.zip>
```

For release engineering this command validates:

- ZIP integrity and release manifest;
- embedded distribution declaration `copy_run_ready=true`;
- presence and checksum of `copy-run-contract.json`;
- canonical launcher/runtime/compiler/firmware paths;
- artifact-owned Python/PlatformIO/toolchain contract;
- external mutable-state contract;
- relocation contract;
- physical acceptance remains operator-confirmed rather than CI-invented.

On a true target machine, the production ZIP itself must be copied first. The target user runs `RoboStudio.cmd`; they do not run source-tree build scripts.

## 7. Fail-closed conditions

B2.6 must fail when any of the following is true:

- `copy-run-contract.json` is missing;
- the contract is not inventoried by the distribution/release manifests;
- the contract checksum changes;
- the primary launcher is not `RoboStudio.cmd`;
- the contract points to an absolute build-machine path;
- bundled Python is not `runtime/bin/python.exe`;
- bundled PlatformIO is not `runtime/platformio`;
- compiler or firmware paths escape the artifact;
- host Python/Node/PlatformIO/compiler is declared required;
- mutable state is allowed inside the immutable release;
- copy-to-another-machine support is false;
- final physical acceptance no longer requires explicit operator confirmation;
- post-contract production closure fails;
- portable release proof fails after finalization.

## 8. Automated regression gate

Run:

```powershell
python tests/b2_6/run_b2_6.py
```

The gate covers:

- canonical contract semantics;
- valid final ZIP contract;
- poisoned host-Python requirement rejection;
- absolute runtime path rejection;
- missing contract rejection;
- missing `copy_run_ready` rejection;
- canonical one-command build invoking the B2.6 finalizer.

The same gate is part of `run_all_tests.py` and the Windows GitHub Actions workflow.

## 9. Definition of Done

B2.6 implementation is Done when:

- the canonical one-command production build finalizes through B2.6;
- the final ZIP contains the contract;
- distribution/release inventories protect the contract hash;
- the final ZIP passes B2.6 validation from inside the archive;
- B2.6 regression and the full repository regression are green.

Project-level copy/run completion still depends on B2.5 physical acceptance on an independent Windows machine with the real robot. B2.6 must not convert missing physical evidence into PASS.
