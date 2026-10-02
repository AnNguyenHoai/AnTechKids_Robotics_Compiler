# RSD-20-P Regression Fix

The valid RSD-20-P fixture now uses a real runnable minimal CPython closure: `runtime/bin/python.exe`, CPython core DLLs beside the interpreter, and the standard-library `Lib` tree. The optional Windows `DLLs` tree is intentionally excluded because it contains native extension modules not needed by the clean-machine probe and would add unrelated transitive PE dependencies.

The portability proof remains fail-closed. Every packaged PE is still scanned, and every non-system import absent from the release is still reported as a finding. The change is limited to making the positive fixture accurately model the runtime required by the RSD-16 probe (`json`, `os`, `sys`, and `pathlib`).
