# RSD-20-P — Production Portable Release Proof & Dependency Closure

> **RSD-22 authority notice:** This document defines the portable dependency-proof mechanism. RSD-23 now makes application-owned Python and PlatformIO mandatory release payload.

## Objective

Prove the dependency closure of the actual release ZIP and catch developer-machine path leakage.

The proof is offline: it does not install, download, resolve, or execute host tools. After RSD-23, the proof consumes a ZIP that declares and contains the application-owned Python/PlatformIO runtime.

## Contract

A production portable release proof must validate release integrity; reject unsafe ZIP members; extract into a fresh unrelated temporary directory; require the application and declared runtime payload; inspect shipped PE images for normal imported DLLs; treat Windows OS DLLs/API-set contracts as host-provided; require every non-system imported DLL to exist physically inside the release; scan for developer-machine absolute path leakage; and produce machine-readable evidence.

## Verification

```powershell
python tests\rsd_20_p\run_rsd_20_p.py
python tests\rsd_23\run_rsd_23.py
python run_all_tests.py
```
