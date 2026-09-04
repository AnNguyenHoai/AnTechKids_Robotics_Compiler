# Legacy / non-production code

This directory is intentionally outside the canonical production firmware.

`runtime_cpp_prototype/` is a historical parallel C++ runtime/execution-engine architecture retained for reference. Production firmware uses `robot-platform/main/src/Services/VM/` and `robot-platform/main/main.ino`.

Do not merge code from this directory into production by path replacement. Any reusable feature must be adapted explicitly to the canonical production ownership model.
