# RSD-17 — Production Distribution Builder / Release Source Integration

> **RSD-22 authority notice:** This document defines the production distribution integration mechanism only. Its release-boundary assumptions are subordinate to `RSD-22_RELEASE_CONTRACT_CONSOLIDATION.md`.

## Objective

Connect real RoboStudio application/runtime build outputs to the canonical
RSD-07 distribution assembler without allowing the developer machine to leak
into the release.

## Contract

`tools/production_distribution.py` is the production source-integration
boundary. It requires explicit paths for:

- the built `RoboStudio.exe`;
- the declared runtime resources directory;
- the application `VERSION` file;
- the application-owned compiler payload and RoboSim frontend, using explicit
  inputs or repository-owned defaults defined by the implementation.

The builder deliberately does **not** discover production dependencies through
`PATH`, the current working directory, user PlatformIO state, or a host virtual
environment.

The repository `VERSION` is allowed to live separately from the application
build output. The builder stages a temporary application directory containing
the executable and `VERSION`, then delegates the actual distribution assembly
to the canonical `tools.distribution_package.assemble_distribution()` API.

No temporary staging files are copied into the final distribution. RSD-07
continues to own the final distribution layout, runtime preflight, resource
manifest, runtime integrity manifest, and distribution manifest.

## Current toolchain boundary

The current implementation treats Python and PlatformIO as target-machine
prerequisites. This is a current-state implementation fact, not the final
zero-development-machine product target. RSD-23 owns the transition to an
application-owned runtime where required.

## API

```python
from tools.production_distribution import (
    ProductionDistributionInputs,
    build_production_distribution,
)
```

## Release flow

```text
Production build outputs
        |
        v
RSD-17 production_distribution.py
        |
        v
RSD-07 distribution_package.py
        |
        v
RSD-09 release_package.py
        |
        v
RSD-12 / RSD-16 release acceptance
```

## Verification

```powershell
python tests\rsd_17\run_rsd_17.py
python tests\rsd_07\run_rsd_07.py
python tests\rsd_09\run_rsd_09.py
python tests\rsd_12\run_rsd_12.py
python tests\rsd_16\run_rsd_16.py
python run_all_tests.py
```
