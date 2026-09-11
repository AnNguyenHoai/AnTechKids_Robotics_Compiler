# RSD-07 — Portable Distribution Assembly

## Goal

Turn the portable-runtime contract into an explicit distribution artifact. A RoboStudio release must be assembled from declared application-owned inputs, not from an implicit snapshot of the developer machine.

## Distribution contract

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

The assembler:

- copies the application executable;
- copies portable Python and the application-owned PlatformIO runtime;
- copies declared runtime resources;
- rejects PlatformIO `penv` because it may contain host-specific paths;
- regenerates the resource manifest after copying;
- runs the RSD-06 runtime preflight on the assembled directory;
- writes a distribution manifest containing every shipped file, size, and SHA-256.

An existing output directory is removed before assembly. This prevents stale host files from surviving a rebuild.

## Validation

`tests/rsd_07/run_rsd_07.py` covers:

- complete distribution assembly;
- executable/runtime/resource copying;
- RSD-06 preflight integration;
- distribution manifest integrity;
- stale-output removal on reassembly;
- rejection of host-specific `penv`;
- checksum drift detection.

Actual platform-specific executable creation remains an upstream build concern; the assembler consumes the resulting executable and runtime inputs.
