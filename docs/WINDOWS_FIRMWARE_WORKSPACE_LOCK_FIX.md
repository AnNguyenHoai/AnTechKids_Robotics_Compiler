# Windows Firmware Workspace Lock Fix

## Failure reproduced

A repeated first-flash/bootstrap could fail before PlatformIO starts:

```text
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process
...
RoboStudio/build/bootstrap/platformio/firmware
```

## Root cause

The old firmware staging model reused one fixed source workspace:

```text
<state>/build/<project>/platformio/firmware
```

Before every deployment, `prepare_firmware_workspace()` deleted that directory with `shutil.rmtree()` and copied the firmware template again.

On Windows, a PlatformIO/esptool descendant can briefly outlive the parent process or retain its current working directory / another handle below the firmware tree. Windows then refuses to remove the directory. The next deployment fails before it can create a fresh staging workspace.

This is a workspace-lifecycle problem, not a hardware-config problem.

## New contract

Firmware source staging is per deployment run:

```text
<state>/build/<project>/platformio/
├── build/
├── cache/
├── libdeps/
└── runs/
    ├── <uuid-1>/firmware/
    ├── <uuid-2>/firmware/
    └── ...
```

`PLATFORMIO_BUILD_DIR`, cache and libdeps contracts remain unchanged. Only the disposable firmware source copy becomes per-run.

A deployment never removes or reuses an older firmware source workspace before starting a new run.

## Cleanup

After build/upload/bootstrap/OTA, RoboStudio performs best-effort cleanup for the current run workspace.

- unlocked workspace: removed normally;
- workspace still locked by Windows: cleanup is deferred and deployment result is preserved;
- the next run is unaffected because it receives a different UUID workspace.

Cleanup validates that the requested path belongs to the expected `<platformio>/runs/<uuid>/firmware` topology before deleting anything.

## Regression

`tests/b2_3/run_firmware_workspace_lock_regression.py` reproduces the pre-fix topology and simulates WinError 32. It verifies:

- the old fixed `platformio/firmware` tree is never deleted before a new run;
- consecutive deployments receive different run workspaces;
- a locked completed run causes deferred cleanup rather than deployment failure;
- another deployment can start while the previous run remains locked;
- normal cleanup still succeeds when the handle is released.
