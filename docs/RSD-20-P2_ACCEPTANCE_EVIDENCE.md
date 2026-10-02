# RSD-20-P.2 — Portable Acceptance Evidence

## Goal

Persist the result of the clean-machine release acceptance as a small, machine-readable sidecar that can travel with the release artifact.

## Contract

```text
RoboStudio-<version>-Windows.zip
release-acceptance.json
```

The evidence records:

- application and version;
- release artifact filename;
- release artifact SHA-256;
- relocation verification;
- external-CWD verification;
- application-owned executable verification;
- application-owned runtime environment verification;
- clean-machine probe return code.

Temporary extraction directories, temporary working directories, and injected host environment values are intentionally excluded. They are execution mechanics and must not become host-specific release dependencies.

## CLI

```powershell
python -m tools.release_cli accept RoboStudio-<version>-Windows.zip --report release-acceptance.json
```

The command exits non-zero if acceptance fails. The report is written only after the acceptance gate succeeds.

## Release handoff

A production release is considered acceptance-ready only when all of the following are available:

1. release ZIP;
2. release manifest;
3. provenance manifest;
4. portable proof report;
5. acceptance evidence;
6. matching artifact SHA-256.

This evidence does not claim GUI or physical hardware validation. Those remain explicit production/hardware gates.
