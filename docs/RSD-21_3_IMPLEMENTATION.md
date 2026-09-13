# RSD-21.3 — Production Artifact Boundary Enforcement

## Release payload

The production ZIP contains **RoboStudio + Compiler + application-owned resources/dependencies + release metadata**.

## Explicitly excluded

Python installations, PlatformIO installations, `.venv`, `.pio`, `penv`, source repositories, and developer-specific host state are not production payload.

## Enforcement

`tools/production_artifact_boundary.py` is the executable policy gate. Production distribution assembly runs this gate before creating the distribution manifest, and release packaging runs it again before creating the ZIP.

The production distribution path no longer copies `runtime/bin` or `runtime/platformio`. Existing low-level legacy distribution fixtures remain available for historical RSD-20 regression coverage.

## Compatibility

Production release compatibility records `portable_python_required=false` and `bundled_platformio_required=false`. Target-machine prerequisite installation is covered by `tools/target_machine_prerequisites.py` and `docs/TARGET_MACHINE_REQUIREMENTS.md`.

## Evidence

A production distribution contains `release-boundary.json`, and the release manifest records `artifact_model=RoboStudio + Compiler` and `production_boundary=true`.
