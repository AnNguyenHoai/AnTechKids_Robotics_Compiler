# RSD-21.5 — RoboStudio + Compiler E2E

## Release boundary

This gate treats the production release ZIP as the system under test. It must not execute RoboStudio or the compiler from the repository checkout.

## Target-machine model

The target machine supplies external prerequisites such as Python and PlatformIO. They are not copied into the production artifact.

## Required proof

1. Extract the production ZIP into an isolated directory.
2. Resolve the RoboStudio executable from the extracted artifact.
3. Start RoboStudio from the extracted artifact.
4. Open/submit a representative RoboSim Python program.
5. Invoke the production compiler.
6. Verify compiler output is produced successfully.
7. Record machine-readable evidence for the release qualification report.

## Negative boundary requirements

The E2E must fail if it silently falls back to repository/source-tree executables, developer virtual environments, host-specific paths, or bundled Python/PlatformIO installations.

## CI note

Automated regression tests validate the contract and orchestration without requiring a GUI session. The real GUI/compile launch is performed as target-machine acceptance using the production ZIP.
