# RSD-12 — Portable Release Acceptance & Clean-Machine Gate

## Objective

Provide one deterministic acceptance boundary for a RoboStudio release artifact.
RSD-12 verifies that the artifact remains self-contained after relocation and
that launch/build path resolution cannot fall back to the developer machine.

RSD-02 through RSD-11 establish individual portability contracts. RSD-12 is the
end-to-end gate that composes those contracts at the final release artifact.

## Contract

A release artifact is acceptable only when all of the following hold:

- the release ZIP and its release manifest are valid;
- the artifact can be extracted into an unrelated temporary directory;
- the relocated distribution passes packaged-runtime preflight;
- the launch executable is resolved as an absolute path inside the relocated
  application root;
- a caller-supplied host Python/PlatformIO environment cannot replace the
  application-owned runtime paths;
- the launch working directory may be outside the application root;
- the isolated PlatformIO build workspace remains user-owned and outside the
  application/install tree;
- no `.pio` build tree is required inside the relocated application;
- the release remains independent of the current working directory and PATH.

## Canonical API

`tools/portable_release_gate.py` provides:

- `validate_release_artifact(artifact, manifest=None)` — end-to-end acceptance
  of a release ZIP;
- `PortableReleaseReport` — machine-readable acceptance result;
- `PortableReleaseGateError` — fail-closed validation error.

The validator never installs Python or PlatformIO and never modifies the source
checkout. Temporary extraction is performed only in a temporary directory.

## CLI

```powershell
python tools\portable_release_gate.py --artifact <path-to-release.zip>
```

The command returns a non-zero exit code when the release cannot satisfy the
portable clean-machine contract.

## Verification

Run:

```powershell
python tests\rsd_12\run_rsd_12.py
python tests\rsd_11\run_rsd_11.py
python tests\rsd_10\run_rsd_10.py
python tests\rsd_09\run_rsd_09.py
python tests\h26_ota\run_h26_ota.py
python run_all_tests.py
```

For final release qualification, run the gate against the actual release ZIP
on a machine without a host PlatformIO installation and without relying on the
repository checkout.
