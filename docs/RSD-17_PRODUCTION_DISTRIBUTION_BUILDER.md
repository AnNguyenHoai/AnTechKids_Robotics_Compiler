# RSD-17 — Production Distribution Builder / Release Source Integration

> **RSD-22 authority notice:** This document defines the production distribution integration mechanism only. The production release boundary is defined by `RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md`; RSD-23 owns application runtime packaging.

## Objective

Connect real RoboStudio application build outputs to the canonical production distribution without allowing host-specific dependency discovery.

The builder now requires explicit paths for the built `RoboStudio.exe`, application-owned portable Python, application-owned PlatformIO runtime, runtime resources, VERSION, compiler payload and RoboSim frontend. It deliberately does not discover production dependencies through PATH, CWD, user-local PlatformIO state, or a host virtual environment.

## Runtime ownership

RSD-23 makes Python and PlatformIO release-owned inputs. The final distribution contains them under `runtime/bin` and `runtime/platformio`.

## Verification

```powershell
python tests\rsd_21_6\run_rsd_21_6.py
python tests\rsd_23\run_rsd_23.py
python run_all_tests.py
```
