# RSD-21.5 — Artifact Evidence Path Normalization Fix

## Root cause

RSD-21.5 now requires and records the application-owned Python runtime. The E2E fixture expects the artifact-relative evidence path `runtime/bin/python.exe`.

On Windows, `Path.relative_to()` renders path separators using `\\`, so the evidence became `runtime\\bin\\python.exe`. The runtime was present and actually executed, but the machine-readable evidence comparison failed.

## Fix

`tools/production_e2e.py` now centralizes artifact-relative evidence formatting through `_artifact_relative()`, which always returns POSIX-style paths via `Path.as_posix()`.

This keeps ZIP/artifact evidence platform-independent while preserving native filesystem paths for actual process execution.

## Regression protection

The existing RSD-21.5 assertion continues to require the canonical artifact path:

`runtime/bin/python.exe`

The fix does not weaken the bundled-runtime requirement and does not reintroduce host `sys.executable` fallback.
