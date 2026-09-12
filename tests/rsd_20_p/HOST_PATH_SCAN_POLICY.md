# RSD-20-P Host-Path Scan Policy

RSD-20-P treats absolute host paths in release text/configuration as portability findings. Native binaries are validated separately through PE dependency closure.

Binary payloads may contain compiler, linker, debug, or build metadata that names the machine used to produce the binary. Treating arbitrary byte strings inside executables and DLLs as runtime filesystem dependencies creates false positives for otherwise relocatable native runtimes such as CPython.

Therefore:

- `.json`, `.txt`, `.cfg`, `.ini`, `.toml`, `.yaml`, and `.yml` are scanned for known host-specific absolute-path markers.
- PE binaries are scanned for imported DLL dependencies independently.
- Missing non-system PE imports remain a hard portability finding.
- Symlinks and unsafe ZIP paths remain rejected.

This boundary is intentionally aligned with `tools/release_package.py` so RSD-20-P does not disagree with the release-package integrity gate about which payloads constitute textual host configuration.
