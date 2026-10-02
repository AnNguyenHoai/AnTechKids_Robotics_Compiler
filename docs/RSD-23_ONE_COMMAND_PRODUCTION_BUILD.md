# RSD-23 — One-Command Production Build

> RSD-22 remains the authoritative production release boundary. RSD-23 implements the transition from host Python/PlatformIO prerequisites to an application-owned Windows runtime.

## Objective

Produce the complete RoboStudio production release from one repository-owned command, with Python and PlatformIO copied into the release boundary so the target Windows machine does not need a developer Python installation, PlatformIO installation, repository checkout, or user-local PlatformIO state.

The build machine may use its normal development toolchain. The important boundary is the generated artifact: all runtime components required by RoboStudio must be owned by the release.

## Canonical command

```powershell
python tools\\one_command_production_build.py `
  --executable <path-to-RoboStudio.exe> `
  --runtime-bin <path-to-portable-python> `
  --runtime-platformio <path-to-application-owned-platformio-core> `
  --runtime-resources <path-to-runtime-resources> `
  --version-file VERSION `
  --source-revision <git-revision> `
  --output releases\\production
```

The command can be launched from any current working directory. Repository-relative defaults are resolved from the script location, never from CWD.

## Runtime ownership contract

The command requires these application-owned runtime inputs:

```text
runtime-bin/
├── python.exe
└── Lib/site-packages/platformio/...

runtime-platformio/
├── deployment-runtime.json
├── platforms/
└── packages/
```

`runtime-bin` must not be a virtual environment. `runtime-platformio` must not contain `penv`, `.venv`, `.pio`, or repository metadata.

The builder does not silently copy the host user's `%USERPROFILE%\\.platformio` or search PATH. Runtime inputs are explicit and are copied into the final artifact under `runtime/bin` and `runtime/platformio`.

## Deployment manifest

The production builder writes/normalizes `runtime/platformio/deployment-runtime.json` with the canonical application-owned layout:

- schema `antechkids.robostudio.deployment-runtime`;
- schema version `1`;
- `portable_python_required: true`;
- `host_virtualenv_included: false`;
- Python at `runtime/bin/python.exe`;
- PlatformIO core at `runtime/platformio`;
- required PlatformIO directories `platforms` and `packages`.

## Fail-closed rules

The one-command build fails when:

- the executable, VERSION, resources, compiler, frontend, Python runtime, or PlatformIO runtime is missing;
- Python is not `python.exe` on the Windows production boundary;
- the Python runtime does not contain the PlatformIO module;
- PlatformIO `platforms` or `packages` is missing;
- a host virtual environment or forbidden development directory is present;
- an output directory is inside an input source tree;
- downstream release packaging, provenance, or portable proof fails.

No release-ready artifact is reported after a failed gate.

## Result

The generated ZIP is the unit copied to another Windows machine. Its runtime is application-owned:

```text
RoboStudio-<version>/
├── RoboStudio.exe
├── RoboStudio.cmd
├── VERSION
├── compiler/
├── runtime/
│   ├── bin/          # application-owned Python
│   ├── platformio/   # application-owned PlatformIO core/packages/platforms
│   └── resources/
└── release metadata
```

The target machine may have arbitrary PATH/PYTHONPATH/PLATFORMIO_CORE_DIR values; RoboStudio's bundled runtime resolution must remain inside the release boundary.

## Scope boundary

RSD-23 owns deterministic runtime assembly. It does not claim final GUI or physical robot qualification. RSD-24 performs clean Windows qualification and H28 performs real robot E2E.

## Verification

```powershell
python tests\\rsd_23\\run_rsd_23.py
python run_all_tests.py
```
