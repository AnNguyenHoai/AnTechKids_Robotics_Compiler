# RSD-06 — Distribution Runtime Preflight

## Goal

A packaged RoboStudio executable must refuse to start against a partial or host-specific runtime. The launcher validates the application-owned distribution before importing the GUI/application services.

## Required packaged layout

```text
RoboStudio/
├── RoboStudio.exe
└── runtime/
    ├── bin/
    │   └── python.exe
    ├── platformio/
    │   ├── deployment-runtime.json
    │   ├── platforms/
    │   └── packages/
    └── resources/
        ├── runtime-resources.json
        └── robot-isa/
            └── target_profiles.json
```

`runtime/platformio/penv` is forbidden because it can contain host-specific interpreter paths.

## Launch contract

`robostudio/main.py` invokes `bootstrap(validate_runtime=True)`. The strict preflight is active only when the process is frozen/packaged. Source development keeps the existing repository workflow.

The preflight does not:

- search for PlatformIO on `PATH`;
- search for Python on `PATH`;
- use the current working directory;
- accept a host-specific PlatformIO `penv`;
- silently fall back to a global developer installation.

## Validation

The preflight checks portable Python, the application-owned PlatformIO runtime, deployment manifest schema/layout, runtime resource manifest integrity, and the required target profile resource.

The aggregate `run_all_tests.py` runner includes RSD-02 through RSD-06 so distribution regressions are part of the normal regression gate.
