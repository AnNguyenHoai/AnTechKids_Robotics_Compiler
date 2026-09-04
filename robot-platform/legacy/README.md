# Legacy / non-production code

This directory is intentionally outside the canonical production firmware.

`runtime_cpp_prototype/` is a historical parallel C++ runtime/execution-engine architecture retained only as an archive. Production firmware uses `robot-platform/main/src/Services/VM/` and `robot-platform/main/main.ino`.

## Retirement rule

The prototype is not a supported implementation and must not be imported into production. Its physical deletion is deferred until the first real ESP32 hardware validation confirms the canonical runtime/deployment path.

Any reusable feature must be adapted explicitly to the canonical production ownership model before the archive is removed.
