# RSD-21.8 — Real RoboStudio ↔ Compiler Contract

> **RSD-22 authority notice:** This document defines the compiler/application boundary only. Production release ownership and portability requirements are defined by `RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md`.

## Purpose

RSD-21.7 made the real compiler a production artifact. RSD-21.8 defines the actual application boundary so RoboStudio does not depend on compiler internals.

## Contract

Endpoint:

```text
compiler/robostudio_bridge.py
```

Request is JSON:

```json
{
  "source": "C:/project/main.py",
  "output": "C:/project/build/program.h",
  "report": "C:/project/build/compile-contract-report.json",
  "source_kind": "robosim-python"
}
```

`source_kind` is one of:

- `robosim-python`: the bridge applies the real RoboSim frontend rewrite, then invokes the real compiler.
- `standard-robot-python`: the source is already in the Standard Robot API and is sent directly to the compiler.

Response is JSON with stable schema `antechkids.robostudio.compiler-contract` and contract version `1`.

A successful response contains `status=PASS`, the original source, the generated output path, the report path, and instruction count. Failures use stable error codes such as `SOURCE_NOT_FOUND`, `INVALID_REQUEST`, `INVALID_SOURCE`, and `COMPILE_FAILED`.

## Production ownership

The production distribution packages the real compiler contract payload:

```text
compiler/main.py
compiler/compiler/*
compiler/robostudio_bridge.py
compiler/frontend/*
```

The frontend is copied from `robot-frontend-robosim/frontend` and is therefore the real RoboSim adapter, not a fixture.

The current implementation treats Python and PlatformIO as external target-machine prerequisites. This is a current-state implementation fact and is subordinate to the final product target defined by RSD-22 and RSD-23.

## E2E guarantee

RSD-21.8 tests extract the production ZIP and execute the packaged bridge from the extracted artifact. The request uses a real RoboSim program and the response is checked against the stable contract. The generated header and machine-readable report must exist.

## Regression

```powershell
python tests\rsd_21_8\run_rsd_21_8.py
python run_all_tests.py
```
