# RSD-11 — Portable Build Isolation

## Objective

RoboStudio deployment builds must not write PlatformIO generated state into the
repository or packaged application tree. Build state is writable user data;
the application/runtime and robot-platform source remain separate.

## Contract

For every one-click deployment project:

- `PLATFORMIO_WORKSPACE_DIR` is an absolute per-project RoboStudio user-data path.
- `PLATFORMIO_BUILD_DIR` is inside that isolated workspace.
- `PLATFORMIO_LIBDEPS_DIR` is inside that isolated workspace.
- `PLATFORMIO_CACHE_DIR` is inside that isolated workspace.
- `PLATFORMIO_BUILD_CACHE_DIR` is inside that isolated workspace.
- `PLATFORMIO_SHARED_DIR` is inside that isolated workspace.
- A host-provided PlatformIO workspace/build path cannot override the deployment paths.
- The PlatformIO build command continues to use the canonical `robot-platform`
  source tree as its project directory, but all generated build state is redirected
  through the environment.
- Firmware lookup uses the isolated build directory rather than a hard-coded
  `robot-platform/.pio` path.
- Different RoboStudio project names receive different build workspaces.
- Build project names are single safe path components; traversal, absolute paths,
  and Windows reserved device names are rejected.

## Source vs packaged runtime

The PlatformIO Core/platform/package locations remain owned by the existing
runtime-resolution contract. RSD-11 only relocates writable build state. In a
frozen distribution, the deployment runtime still resolves the application-owned
PlatformIO Core first; the isolated build workspace is placed under the user's
RoboStudio data directory so the installed/portable application does not need
write access to its own binaries.

## Canonical APIs

`tools/build_isolation.py` provides:

- `build_workspace(project_name)`
- `build_dir(project_name)`
- `libdeps_dir(project_name)`
- `cache_dir(project_name)`
- `build_cache_dir(project_name)`
- `shared_dir(project_name)`
- `prepare_build_workspace(project_name)`
- `build_environment(project_name, base_env=None)`
- `firmware_path(project_name, environment)`
- `clean_build_workspace(project_name)`

`tools/deployment_runtime.py` exposes the integrated
`isolated_deployment_environment()` entry point while retaining the existing
RSD-05 frozen-runtime behavior for callers that do not request a project build.

## Verification

Run:

```text
python tests\rsd_11\run_rsd_11.py
python tests\rsd_10\run_rsd_10.py
python tests\rsd_09\run_rsd_09.py
python tests\h26_ota\run_h26_ota.py
python tests\h27_b0\run_h27_b0.py
python run_all_tests.py
```

A real deployment should also confirm that `robot-platform/.pio` is not created
or modified by the RoboStudio build path and that the resulting firmware is
read from the isolated workspace.
