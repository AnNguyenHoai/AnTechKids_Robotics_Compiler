# RSD-20-P — Production Portable Release Proof & Dependency Closure

## Objective

Prove that the **actual release ZIP** is self-contained for its application-owned
runtime and does not depend on developer-machine Python, PlatformIO, virtualenv,
current working directory, or leaked host-specific paths.

RSD-20-P is a proof gate, not a replacement for RSD-07/RSD-09/RSD-16. It consumes
the release artifact produced by the existing release pipeline and adds an
offline dependency-closure check.

## Contract

A production portable release proof must:

- validate the existing RSD-19 release artifact integrity first;
- validate that the ZIP has no duplicate, absolute, traversal, or symlink members;
- extract the artifact into a fresh unrelated temporary directory;
- require the declared application to exist inside the extracted root;
- require the application-owned portable Python runtime;
- require application-owned PlatformIO `platforms` and `packages` directories;
- require application-owned runtime resources;
- inspect shipped PE images (`.exe`, `.dll`, `.pyd`, and PE-formatted files) for
  normal imported DLLs;
- treat Windows OS DLLs and API-set contracts as host-provided dependencies;
- require every other imported DLL to exist physically inside the release;
- scan shipped payloads for common developer-machine absolute path leakage;
- produce a stable machine-readable report;
- never install, download, resolve, or execute a host tool as part of the proof.

## What this proves

The gate proves **offline dependency closure for normal PE DLL imports** and
catches common host-path leakage. It does not claim that every Windows OS
component is bundled; Windows system DLLs are explicitly treated as OS
requirements.

It also does not replace real clean-machine GUI/hardware qualification. RSD-16
still covers the runtime execution boundary, while final production qualification
must run the shipped ZIP on an actual clean Windows machine and exercise the
intended GUI and hardware workflow.

## Canonical API

`tools/portable_release_proof.py` provides:

- `prove_portable_release(artifact, manifest=None)`;
- `PortableReleaseProofReport`;
- `DependencyFinding`;
- `report_to_dict(report)`.

The CLI is:

```powershell
python tools\portable_release_proof.py --artifact <path-to-release.zip>
```

Optional JSON report output:

```powershell
python tools\portable_release_proof.py --artifact <path-to-release.zip> --report release-proof.json
```

The command exits non-zero on any integrity, layout, host-path, or non-system
PE dependency violation.

## Release qualification sequence

```text
Production inputs
    ↓
RSD-17 Production Distribution
    ↓
RSD-09 Release Packaging
    ↓
RSD-18 Provenance
    ↓
RSD-19 Integrity
    ↓
RSD-20-P Portable Proof & Dependency Closure
    ↓
RSD-16 Clean-Machine Acceptance
    ↓
Actual Windows / GUI / Hardware qualification
```

RSD-20-P intentionally does not change the existing packaging format. It verifies
the bytes already selected by the release packaging pipeline.

## Verification

Run the focused suite:

```powershell
python tests\rsd_20_p\run_rsd_20_p.py
```

Run the complete regression suite:

```powershell
python run_all_tests.py
```

## Limitations / follow-up

- A PE import table cannot describe every runtime dependency (for example,
  dynamically loaded DLLs). Those remain part of clean-machine qualification.
- GUI startup and physical robot upload remain outside the automated proof.
- The build source of the runtime inputs must still be controlled by the
  production build process; RSD-20-P proves the shipped artifact, not the
  provenance of an arbitrary developer-selected input directory.
