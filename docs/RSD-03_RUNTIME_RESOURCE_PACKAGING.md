# RSD-03 — Runtime Resource & Configuration Packaging

## Objective

Make RoboStudio runtime resources deterministic and relocatable. Frozen builds must consume declared resources from the application-owned `runtime/resources` tree instead of relying on the current working directory or developer checkout.

## Resource contract

The first protected runtime resource is:

```text
runtime/resources/robot-isa/target_profiles.json
```

The resource registry is intentionally explicit. A runtime component cannot resolve an arbitrary filesystem path by treating a user-supplied name as a relative resource name.

## Source vs packaged behavior

- Source/development mode: `packages/robot-isa/target_profiles.json` remains the compatibility source.
- Frozen/packaged mode: only `runtime/resources/robot-isa/target_profiles.json` is accepted.
- `ROBOSTUDIO_HOME` can be used by controlled deployments/tests to identify the application root.
- No resource lookup uses CWD or PATH.

## Integrity

`runtime-resources.json` stores resource paths relative to the resource root plus size and SHA-256. Validation therefore survives relocation while detecting missing or modified resources.

## Packaging

Use:

```powershell
python tools/package_runtime_resources.py --output <RoboStudio>\runtime\resources
```

The packager copies only registered resources and writes the manifest. It does not copy host-specific development state.

## Deployment integration

`tools/deployment_contract.py` resolves `target_profiles.json` through the runtime resource contract. This removes the previous hard dependency on the repository checkout for packaged deployments while preserving source-mode behavior.

## Gate

```powershell
python tests\rsd_03\run_rsd_03.py
python tests\rsd_02\run_rsd_02.py
python tests\rsd_04\run_rsd_04.py
python tests\h26_b\run_h26_b.py
python tests\h26_ota\run_h26_ota.py
python run_all_tests.py
```
