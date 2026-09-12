# RSD-20-P Portable Python Fixture

The RSD-20-P regression fixture uses a real CPython executable so RSD-16 clean-machine acceptance can actually launch it.

The fixture deliberately copies only:

- `python.exe` (or `python` on POSIX);
- CPython core DLLs installed beside the interpreter on Windows;
- the standard-library `Lib` tree.

It does **not** copy the full `DLLs` directory. That directory contains optional native extension modules with additional transitive dependencies which are not needed by the clean-machine probe (`json`, `os`, `sys`, `pathlib`). Copying the entire developer Python installation would turn an acceptance fixture into a host-specific dependency bundle and make the portability proof reject an otherwise valid fixture.

This is a test-fixture boundary only. Production release assembly remains responsible for packaging the complete runtime required by the actual application, and RSD-20-P remains fail-closed for every non-system PE dependency found in the resulting production artifact.
