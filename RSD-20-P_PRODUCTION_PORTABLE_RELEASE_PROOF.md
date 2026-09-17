# RSD-20-P — Production Portable Release Proof & Dependency Closure

> **RSD-22 authority notice:** This document defines the portable dependency-proof mechanism. The production release boundary is defined by `RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md`.

## Objective

Prove the dependency closure of the actual release ZIP and catch developer-machine path leakage.

RSD-20-P is a proof gate, not a replacement for RSD-07/RSD-09/RSD-16. It consumes the release artifact produced by the existing release pipeline and adds an offline dependency-closure check.

## Current-state boundary

The current production distribution still treats Python and PlatformIO as target-machine prerequisites. Therefore the current gate does not prove that those external tools are bundled.

The final product target is defined by RSD-22: after RSD-23, application-owned Python and PlatformIO runtime inputs are expected to become release-owned dependencies, and this gate must verify their closure.

## Contract

A production portable release proof must:

- validate the existing RSD-19 release artifact integrity first;
- validate that the ZIP has no duplicate, absolute, traversal, or symlink members;
- extract the artifact into a fresh unrelated temporary directory;
- require the declared application to exist inside the extracted root;
- inspect shipped PE images for normal imported DLLs;
- treat Windows OS DLLs and API-set contracts as host-provided dependencies;
- require every non-system imported DLL to exist physically inside the release;
- scan shipped payloads for common developer-machine absolute path leakage;
- produce a stable machine-readable report;
- never install, download, resolve, or execute a host tool as part of the proof.

When application-owned Python/PlatformIO are introduced by RSD-23, their presence and dependency closure become mandatory release assertions rather than optional host prerequisites.

## What this proves

The gate proves offline dependency closure for normal PE DLL imports and catches common host-path leakage. It does not claim that every Windows OS component is bundled; Windows system DLLs remain OS requirements.

It does not replace real clean-machine GUI/hardware qualification.

## Canonical API

`tools/portable_release_proof.py` provides:

- `prove_portable_release(artifact, manifest=None)`;
- `PortableReleaseProofReport`;
- `DependencyFinding`;
- `report_to_dict(report)`.

## Verification

```powershell
python tests\rsd_20_p\run_rsd_20_p.py
python run_all_tests.py
```
