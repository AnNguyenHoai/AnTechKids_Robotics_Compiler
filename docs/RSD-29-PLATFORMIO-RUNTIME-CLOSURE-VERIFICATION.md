# RSD-29 — PlatformIO Runtime Closure Verification

## Purpose

RSD-28 established a metadata closure gate, but its resolver treated every package in `platform.json` as required and did not model the effective PlatformIO environment. RSD-29 closes that gap before production firmware build E2E.

The production contract is now:

> The packaged PlatformIO runtime must contain exactly the concrete package versions required by the effective production environments, including selected frameworks, explicit `platform_packages`, and transitive package dependencies, without consulting host PlatformIO state.

## Evidence from PlatformIO

The upstream `espressif32@6.12.0` manifest contains required and optional packages. In particular, `framework-arduinoespressif32` is marked optional at the platform-manifest level but is selected when the project declares `framework = arduino`; `toolchain-xtensa-esp32` and `tool-esptoolpy` are non-optional for this platform. The manifest also contains many optional debugger/filesystem/alternate-toolchain packages.

PlatformIO's documentation defines `platform_packages` as environment-level package overrides and documents package version requirements including `^`, `~`, comparison operators and `!=`. Therefore closure validation must model the effective environment rather than simply requiring every entry from `platform.json`.

## RSD-29 changes

### 1. Effective environment resolution

The validator now resolves the effective values of:

- `platform`
- `framework`
- `platform_packages`

through `extends`, including the three supported production environments:

- `esp32dev`
- `esp32dev_bootstrap`
- `esp32dev_ota`

Circular `extends` chains fail closed.

### 2. Platform package selection

The validator now distinguishes between:

- non-optional platform packages, which are required;
- optional packages, which are not required merely because they exist in `platform.json`;
- framework packages, which become required when selected by the environment.

This matches the production use of `framework = arduino` instead of over-constraining the runtime to every optional package published by the platform.

### 3. `platform_packages` overrides

Explicit environment package overrides are included in the closure. Remote Git/HTTP/local package sources are rejected because this production contract requires application-owned deterministic runtime contents rather than another external resolution path.

### 4. Transitive dependencies

Resolved `package.json` manifests are recursively inspected for `dependencies`. Each dependency must resolve to exactly one packaged concrete version satisfying every accumulated requirement.

### 5. Version requirements

The resolver now supports the PlatformIO forms relevant to the production closure:

- exact versions;
- `~` compatible ranges;
- `^` compatible ranges;
- `>`, `>=`, `<`, `<=`;
- `!=`;
- comma-separated constraint sets.

The production platform itself remains required to use an exact `@x.y.z` pin.

## Dependency graph

```text
platformio.ini
   |
   +-- effective environment
   |      |
   |      +-- platform = espressif32@6.12.0
   |      +-- framework = arduino
   |      +-- platform_packages (if any)
   |
   +-- platform.json
   |      |
   |      +-- required platform packages
   |      +-- selected framework package
   |
   +-- package.json
          |
          +-- transitive dependencies
          |
          +-- concrete packaged versions
```

## Regression coverage

The RSD-29 test suite covers:

- all three supported environments and inherited configuration;
- selected framework package closure;
- optional package exclusion;
- missing required package;
- transitive package dependency;
- custom `platform_packages`;
- unsupported remote package sources;
- exact platform pinning;
- platform version mismatch;
- package requirement mismatch;
- `!=` and compound constraints.

## Remaining limitation

RSD-29 is still a metadata/static closure verifier. It does **not** execute PlatformIO and therefore does not prove that the real Windows runtime can compile firmware. The next gate is RSD-30: production firmware Build E2E using the actual bundled Python, bundled PlatformIO runtime and isolated writable workspace.

The repository still does not contain the actual Windows application-owned PlatformIO runtime payload, so RSD-29 cannot produce final release evidence until that runtime is supplied to the production distribution build.
