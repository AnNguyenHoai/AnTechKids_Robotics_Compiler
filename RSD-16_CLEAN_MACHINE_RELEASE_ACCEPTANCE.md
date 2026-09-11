# RSD-16 — Clean-Machine Release Acceptance

## Objective

Close the final release-qualification gap between a valid portable release ZIP and
an actually executable release runtime. RSD-16 validates the final artifact,
relocates it to a fresh temporary location, and starts the application-owned
portable Python runtime from an unrelated working directory under hostile host
Python/PlatformIO settings.

RSD-16 composes the existing RSD-09 release artifact, RSD-12 portable release,
and RSD-13 clean-machine execution contracts into one release-level acceptance
API.

## Contract

A release passes RSD-16 only when:

- the release ZIP and release manifest pass their existing integrity checks;
- the manifest declares an application and application version;
- the complete ZIP can be extracted into a fresh unrelated directory;
- the declared application exists inside the relocated release root;
- the relocated `runtime/bin` portable Python starts successfully;
- the child executable remains inside the relocated application root;
- the child keeps an external working directory;
- `ROBOSTUDIO_HOME` identifies the relocated application;
- application-owned PlatformIO paths are selected instead of hostile host paths;
- host Python/virtualenv and PlatformIO override variables cannot leak into the
  packaged runtime;
- the acceptance operation does not mutate the caller's environment.

The automated gate does **not** launch the long-lived Qt GUI and does not perform
physical robot upload. Those remain release-qualification steps that require a
real Windows machine, display, USB/serial device, and the intended hardware.

## Canonical API

`tools/release_acceptance.py` provides:

- `accept_release(artifact, base_env=None, timeout=30.0)` — final clean-machine
  release acceptance;
- `ReleaseAcceptanceReport` — machine-readable result;
- `ReleaseAcceptanceError` — fail-closed acceptance error;
- `report_to_dict(report)` — stable report serialization.

## CLI

```powershell
python tools\release_acceptance.py --artifact <path-to-release.zip>
```

The command returns non-zero when the release cannot satisfy the clean-machine
acceptance contract.

## Verification

Automated regression:

```powershell
python tests\rsd_16\run_rsd_16.py
python tests\rsd_15\run_rsd_15.py
python tests\rsd_14\run_rsd_14.py
python tests\rsd_13\run_rsd_13.py
python tests\rsd_12\run_rsd_12.py
python run_all_tests.py
```

Final human release qualification on Windows should additionally run the CLI
against the **actual shipped ZIP** from outside the repository checkout, ideally
on a machine without Python/PlatformIO installed. Confirm that RoboStudio GUI
starts and perform the intended physical robot build/upload smoke test.
