# RSD-17 — Production Distribution Builder / Release Source Integration

## Objective

Connect real RoboStudio application/runtime build outputs to the canonical
RSD-07 distribution assembler without allowing the developer machine to leak
into the release.

## Contract

`tools/production_distribution.py` is the production source-integration
boundary. It requires explicit paths for:

- the built `RoboStudio.exe`;
- the portable Python runtime directory;
- the application-owned PlatformIO runtime directory;
- the declared runtime resources directory;
- the application `VERSION` file.

The builder deliberately does **not** discover Python, PlatformIO, resources,
or the application executable through `PATH`, the current working directory,
user PlatformIO state, or a host virtual environment.

The repository `VERSION` is allowed to live separately from the application
build output. The builder stages a temporary application directory containing
the executable and `VERSION`, then delegates the actual distribution assembly
to the canonical `tools.distribution_package.assemble_distribution()` API.

No temporary staging files are copied into the final distribution. RSD-07
continues to own the final distribution layout, runtime preflight, resource
manifest, runtime integrity manifest, and distribution manifest.

## API

```python
from tools.production_distribution import (
    ProductionDistributionInputs,
    build_production_distribution,
)

result = build_production_distribution(
    ProductionDistributionInputs(
        executable=Path("<built RoboStudio.exe>"),
        runtime_bin=Path("<portable Python>"),
        runtime_platformio=Path("<application-owned PlatformIO>"),
        runtime_resources=Path("<runtime resources>"),
        version_file=Path("VERSION"),
    ),
    Path("<distribution output>"),
)
```

## CLI

Run from the repository root:

```powershell
python tools\production_distribution.py `
  --executable <path-to-RoboStudio.exe> `
  --runtime-bin <path-to-portable-python> `
  --runtime-platformio <path-to-PlatformIO-runtime> `
  --runtime-resources <path-to-runtime-resources> `
  --version-file VERSION `
  --output <distribution-directory>
```

All input paths are explicit. The default `VERSION` path is derived from the
location of `production_distribution.py`, not from the caller's CWD.

## Safety boundaries

The builder rejects missing inputs and rejects a distribution output located
inside any source input. PlatformIO `penv` remains forbidden by RSD-07. The
builder never modifies the source inputs.

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

RSD-17 does not invent or replace a platform-specific RoboStudio build system.
The upstream build is responsible for producing the application executable and
portable runtime inputs; RSD-17 integrates those declared outputs into the
existing portable distribution contract.

## Verification

```powershell
python tests\rsd_17\run_rsd_17.py
python tests\rsd_07\run_rsd_07.py
python tests\rsd_09\run_rsd_09.py
python tests\rsd_12\run_rsd_12.py
python tests\rsd_16\run_rsd_16.py
python run_all_tests.py
```

For a real release, run the CLI with the actual RoboStudio executable and
application-owned runtime directories, then run RSD-16 against the resulting
release artifact on a clean Windows machine.
