# RSD-20-P regression scope

The positive release fixture uses a real packaged CPython runtime. RSD-20-P validates that runtime's PE imports without treating arbitrary strings embedded in native binaries as textual host paths.

Negative cases continue to prove:

- missing non-system PE dependencies are rejected;
- host-specific absolute paths in textual configuration are rejected;
- unsafe ZIP symlinks are rejected.
