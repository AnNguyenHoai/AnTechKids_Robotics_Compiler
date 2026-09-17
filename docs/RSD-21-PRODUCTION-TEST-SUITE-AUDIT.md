# RSD-21 Production Test Suite Audit

## Finding

The RSD-21 production-distribution acceptance tests had drifted from the production distribution contract. `tools/production_distribution.py` validates firmware and PlatformIO dependency closure, and its firmware fallback points at the repository `robot-platform`. That repository contains developer build state such as `.pio`, so tests that omitted `firmware_root` were unintentionally validating the developer tree instead of a clean production fixture.

This caused RSD-21.6 to fail before reaching its launcher assertions.

## Contract evidence

`ProductionDistributionInputs` includes `firmware_root`, and `validate_inputs()` validates firmware before staging the distribution. The validator rejects `.pio`, `.git`, virtual environments and Python/test caches. Therefore a production acceptance fixture must explicitly provide a clean firmware project and a complete PlatformIO closure.

## Audit result

- RSD-21.1: contract-only; no production fixture required.
- RSD-21.2: target prerequisite contract; no production fixture required.
- RSD-21.3: already uses the contract-complete fixture from RSD-17.
- RSD-21.4: target-machine qualification; no production fixture required.
- RSD-21.5: intentionally tests a minimal ZIP/E2E harness rather than the production distributor, so its fixture is separate and appropriate.
- RSD-21.6: fixture drift found; fixed to use the shared production fixture.
- RSD-21.7: fixture drift found; fixed to use the shared production fixture while retaining the real compiler/frontend inputs.
- RSD-21.8: fixture drift found; fixed to use the shared production fixture while retaining the real compiler/frontend contract test.

## Design correction

A shared fixture is now the source of truth for production-distribution tests. It supplies:

- clean RoboStudio executable and local DLL;
- VERSION;
- compiler/frontend roots;
- runtime resources and resource manifest;
- clean firmware with all three deployment environments;
- pinned `espressif32@6.12.0` firmware platform;
- matching PlatformIO `platform.json` and package metadata;
- application-owned Python runtime fixture;
- deployment-runtime manifest.

Individual tests may override the compiler/frontend roots when their purpose requires real source, but they no longer recreate the production runtime/firmware closure independently.

## Principle

Production acceptance tests must consume a contract-complete fixture, not silently fall back to the developer repository. If the production contract changes, the shared fixture must change once and all dependent acceptance tests inherit the same contract.

## Required qualification

Run the RSD-21 production suite after this change. A passing individual test is not sufficient; the shared fixture and production validator must both remain contract-aligned.
