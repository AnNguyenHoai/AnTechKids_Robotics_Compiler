# RSD-05 — Portable Application Launch & Environment Bootstrap

## Objective

Make RoboStudio start from any working directory while keeping the application, frozen bundle, writable user data, and deployment runtime as separate path domains.

## Startup contract

`robostudio/main.py` now bootstraps the runtime **before importing PySide6 or application services**.

The bootstrap resolves:

```text
RoboStudio.exe location  -> application root
PyInstaller _MEIPASS      -> frozen bundle/import root
LOCALAPPDATA/RoboStudio  -> writable user data
application/runtime       -> private deployment runtime
```

The current working directory is never used to identify the application.

## Frozen runtime environment

Before child processes are started, packaged RoboStudio prepares:

- `ROBOSTUDIO_HOME`
- `ROBOSTUDIO_RUNTIME_MODE=packaged`
- `PLATFORMIO_CORE_DIR`
- `PLATFORMIO_PLATFORMS_DIR`
- `PLATFORMIO_PACKAGES_DIR`
- `PLATFORMIO_CACHE_DIR`
- `PLATFORMIO_BUILD_CACHE_DIR`
- `PLATFORMIO_WORKSPACE_DIR`
- `PLATFORMIO_DISABLE_UPGRADE_CHECK=true`
- `PLATFORMIO_DISABLE_PROGRESSBAR=true`
- `PLATFORMIO_NO_ANSI=true`
- `PYTHONIOENCODING=utf-8`

The host `PATH` and unrelated environment variables are preserved. The bootstrap does not change the process working directory.

## Why application root and bundle root are separate

A frozen executable can be located beside the distributed runtime while PyInstaller places Python modules under its internal extraction/bundle directory. Treating those as the same path causes relocation bugs. The application root therefore identifies distributed writable/read-only assets, while the bundle root identifies frozen Python imports/resources.

## Child-process rule

RoboStudio-owned deployment tools must not rely on a command being installed globally. PlatformIO continues to resolve through the application-owned runtime path. Python-based helper processes must use the packaged Python runtime when one is available rather than assuming the host Python installation.

A frozen application's `sys.executable` identifies the application executable rather than a normal Python interpreter, so helper-process launchers must not blindly use it as `python.exe`.

## Validation

Run:

```powershell
python tests\rsd_05\run_rsd_05.py
python tests\rsd_02\run_rsd_02.py
python tests\rsd_03\run_rsd_03.py
python tests\rsd_04\run_rsd_04.py
python tests\h26_b\run_h26_b.py
python tests\h26_ota\run_h26_ota.py
python run_all_tests.py
```

RSD-05 is intentionally a startup/environment contract. Actual Windows release assembly remains a packaging concern: the release builder must place the executable, required frozen modules/data, portable Python, PlatformIO runtime, compiler runtime, firmware and assets into the documented distribution layout.
