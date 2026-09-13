# RSD-21.1 — Production Release Boundary

## Purpose

RSD-21.1 defines what belongs to a production RoboStudio release and what is
expected to exist on the target machine. The boundary is intentionally explicit
so packaging cannot accidentally capture a developer workstation.

## Product delivered by the ZIP

The production artifact is a **RoboStudio + Compiler** product. The ZIP owns and
delivers:

- RoboStudio IDE/application.
- The application-owned Compiler and all compiler components required by the
  installed product.
- Application resources required by the IDE/compiler.
- Application-local libraries and non-system PE dependencies required by the
  product.
- Release metadata: manifest, provenance, and integrity evidence.

These items are part of the product boundary and must be reproducible from the
release inputs. A target user must not need the source repository or a developer
build directory to obtain them.

## Target-machine prerequisites

The following are **not** product payloads. They are installed/provisioned on
the target machine according to the target-machine requirements document:

| Item | Package in ZIP | Purpose |
| --- | --- | --- |
| Python | No | Compiler execution prerequisite |
| PlatformIO | No | Hardware/build prerequisite |
| ESP32/USB driver | No | Hardware communication prerequisite |
| Git | No | Not required by an installed release |

The exact supported versions and installation procedure belong to the
`TARGET_MACHINE_REQUIREMENTS.md` task and must be verified before production
acceptance.

## Developer-only inputs

The following must never be required by a production release:

- Source repository.
- Developer virtual environment (`.venv`/equivalent).
- Developer-local PlatformIO environment.
- `.pio` build output.
- Absolute paths from a developer workstation.
- IDE/editor installation used to build the product.

## Dependency ownership rule

The release dependency model is:

```text
Application-owned dependency
        -> package in production ZIP

Host prerequisite
        -> do not package
        -> declare in target-machine requirements
        -> verify during target acceptance

Developer-only state
        -> never package
        -> never require at runtime
```

A dependency is **not** considered portable merely because it can be found on
the build machine. Application-owned dependencies must be present in the
artifact; host prerequisites must be explicitly declared; developer-only state
must be absent from the release contract.

## RSD-21.1 acceptance criteria

1. The production artifact is explicitly defined as RoboStudio + Compiler.
2. Application-owned resources and non-system application-local dependencies
   are classified as release payload.
3. Python, PlatformIO, and hardware drivers are classified as target-machine
   prerequisites and are not release payload.
4. Source repository and developer environments are explicitly outside the
   production boundary.
5. Later packaging/qualification tasks can consume one machine-readable
   boundary definition rather than inventing their own classification.

## Machine-readable contract

The canonical programmatic definition is implemented in:

```text
`tools/release_boundary.py`
```

Schema:

```text
antechkids.robostudio.release-boundary
version: 1
```

RSD-21.3 and RSD-21.4 are responsible for wiring this boundary into production
assembly and dependency-closure enforcement. RSD-21.1 itself establishes the
ownership contract without changing the current artifact assembler.
