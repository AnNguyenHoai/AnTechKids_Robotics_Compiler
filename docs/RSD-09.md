# RSD-09 — Portable Release Artifact

## Goal

Turn the validated RoboStudio distribution directory into a self-contained Windows release artifact that can be copied to another machine without importing the developer machine's PlatformIO/Python state.

## Contract

1. The input distribution must pass the existing runtime preflight and distribution manifest validation.
2. The release artifact is a ZIP containing only files from the validated distribution.
3. Archive members must use relative paths and may not contain `.git`, `.pio`, `penv`, or `__pycache__`.
4. Host-specific Python/PlatformIO paths must not appear in textual metadata files shipped in the release.
5. The release manifest records the shipped file list, size, SHA-256 digest, portability flag, and artifact SHA-256.
6. Validation must verify the artifact digest, archive file list, per-file size, and per-file SHA-256.
7. The artifact must remain usable after extraction to a different directory; no repository checkout or host CWD is part of the release contract.

## CLI

Build:

```powershell
python tools/release_package.py --distribution <RoboStudio-distribution> --output <release>\RoboStudio-Windows.zip
```

Validate:

```powershell
python tools/release_package.py --validate --output <release>\RoboStudio-Windows.zip
```

RSD-09 intentionally does not install Python or PlatformIO. Provisioning remains a release-build responsibility covered by the existing runtime packaging tasks.
