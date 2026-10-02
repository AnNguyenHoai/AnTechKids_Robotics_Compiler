# RSD-18 — Release Provenance & Reproducibility

## Objective

Make the RoboStudio release artifact auditable and reproducible. Given the same
validated distribution bytes and the same declared source revision, repeated
release builds must produce the same ZIP bytes and the same provenance record.

## Contract

RSD-18 adds `tools/release_provenance.py` and strengthens the RSD-09 ZIP writer.

The provenance sidecar records:

- source revision supplied by the release pipeline (`RSD_SOURCE_REVISION` when
  no explicit revision is passed);
- application name and `VERSION`;
- release artifact SHA-256;
- release-manifest SHA-256;
- distribution-manifest SHA-256;
- deterministic file inventory (path, size, SHA-256);
- deterministic ZIP parameters.

The sidecar does not contain absolute source paths, user names, temporary
folders, timestamps, or other machine-specific metadata.

## Reproducible ZIP contract

`tools.release_package.build_release()` now writes ZIP entries with:

- lexicographic POSIX path ordering;
- fixed ZIP timestamp `1980-01-01T00:00:00`;
- fixed UTF-8 flag and file metadata;
- DEFLATE compression at level 9;
- file bytes read directly from the validated distribution.

The ZIP therefore does not depend on source file modification times or traversal
order. The existing RSD-09 release manifest remains the authoritative artifact
integrity record.

## API

```python
from tools import release_provenance

release_provenance.write_provenance(
    distribution_root,
    release_manifest,
    artifact,
    output_provenance,
    source_revision="<git-commit-or-release-source-id>",
)
```

Validation:

```python
release_provenance.validate_provenance(
    provenance,
    artifact,
    release_manifest,
)
```

## Source revision

For CI/release automation, set:

```powershell
$env:RSD_SOURCE_REVISION = "<git-commit-sha>"
```

or pass `source_revision` explicitly to the API. If neither is available, the
provenance record deliberately uses `unknown`; it never invents a source
revision.

## Release flow

```text
Production build outputs
        |
        v
RSD-17 production distribution
        |
        v
RSD-07 distribution validation
        |
        v
RSD-09 deterministic release ZIP
        |
        +---- release-manifest.json
        |
        +---- release-provenance.json
        |
        v
RSD-12 / RSD-16 acceptance
```

The provenance sidecar is intentionally outside the ZIP to avoid a circular
artifact-hash dependency. It can be published beside the ZIP and independently
verified against both the ZIP and release manifest.

## Verification

```powershell
python tests\rsd_18\run_rsd_18.py
python tests\rsd_17\run_rsd_17.py
python tests\rsd_16\run_rsd_16.py
python tests\rsd_12\run_rsd_12.py
python run_all_tests.py
```

For a real release, build the same distribution twice with the same artifact
filename and source revision. The two ZIP files must have identical SHA-256
values. Preserve the resulting `release-manifest.json` and
`release-provenance.json` next to the shipped ZIP.
