# RSD-20-P.1 — Production Release Artifact Assembly

## Objective

Provide one repository-owned command that turns the real, already-built
RoboStudio application/runtime inputs into a release artifact suitable for
RSD-20-P portable proof.

This task is intentionally **not** the GUI/compiler build system. The upstream
production build must first produce the application executable and the
application-owned runtime inputs. RSD-20-P.1 makes their hand-off deterministic
and explicit, so release creation does not silently discover Python,
PlatformIO, virtual environments, or resources from the host machine.

## Canonical command

Run from any current working directory:

```powershell
python <repository>\tools\production_release_assembly.py `
  --executable <path-to-RoboStudio.exe> `
  --runtime-bin <path-to-portable-python-runtime> `
  --runtime-platformio <path-to-application-owned-platformio> `
  --runtime-resources <path-to-runtime-resources> `
  --version-file <path-to-VERSION> `
  --source-revision <git-revision>
```

`--output` defaults to `<repository>\releases\production`.

The source revision can also be supplied by `RSD_SOURCE_REVISION`. If neither
is supplied, the tool asks Git for `HEAD`; if Git is unavailable, assembly
fails instead of producing provenance with an unknown source revision.

## Produced artifacts

```text
releases/production/
├── RoboStudio-<version>-Windows.zip
├── release-manifest.json
├── release-provenance.json
├── portable-release-proof.json
├── release-assembly-report.json
└── RoboStudio/                  # intermediate distribution
    ├── RoboStudio.exe
    ├── VERSION
    └── runtime/
```

The ZIP itself remains the user-facing release artifact. The JSON files are
release evidence/sidecars and are not embedded into the ZIP by this task.

## Pipeline

```text
explicit production inputs
        ↓
RSD-17 production_distribution.py
        ↓
RSD-07 distribution_package.py
        ↓
RSD-09 release_package.py
        ↓
RSD-18 release_provenance.py
        ↓
RSD-20-P portable_release_proof.py
        ↓
PASS / release-ready
```

No step resolves runtime inputs from PATH or the caller's CWD. The builder
never mutates the supplied source inputs.

## Fail-closed rules

Assembly fails before destructive output work when any required input is
missing. It also rejects a release output placed inside an input source tree
and rejects unsafe VERSION values that could escape the release output name.

If RSD-17, RSD-09, provenance generation, or RSD-20-P proof fails, the command
returns non-zero and does not report the release as ready.

## Important boundary

RSD-20-P.1 can assemble a production release only after the upstream build has
provided real artifacts. It deliberately does **not** fake `RoboStudio.exe`,
create a Python runtime from the developer installation, or download a
PlatformIO installation. This prevents a false claim of portability.

The next manual qualification remains RSD-16 on a clean Windows machine using
the actual ZIP produced here.

## Verification

```powershell
python tests\rsd_20_p1\run_rsd_20_p1.py
python run_all_tests.py
```

For a real release, inspect `release-assembly-report.json`, retain the
SHA-256, copy the ZIP to a clean Windows machine, and execute the RSD-16
qualification procedure there.
