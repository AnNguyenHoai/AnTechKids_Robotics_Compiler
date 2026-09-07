# H28-B — Deployment Runtime Hardening

## Goal

Make the RoboStudio deployment boundary deterministic and diagnosable on classroom Windows machines, without changing compiler or VM semantics.

## Hardened runtime

- PlatformIO is invoked through the active Python interpreter (`python -m platformio`) rather than depending on a `pio` executable being present in `PATH`.
- External deployment commands have a bounded runtime and are terminated when the deadline is exceeded.
- Deployment subprocess output is streamed line-by-line so RoboStudio can display build/upload progress while the operation is running.
- OTA targets are validated as hostname/IP values; URL/path input is rejected before an HTTP transaction starts.
- OTA performs a lightweight `/api/v1/health` preflight before uploading.
- HTTP OTA uses a total transport deadline and bounded socket waits instead of an unbounded socket operation.
- The generated firmware header is restored if the build/upload transaction fails, preventing a failed deployment from leaving a misleading active artifact in the firmware project.
- Low-level `tools/flash.py` follows the same PlatformIO runtime contract.

## RoboStudio behavior

The deployment workers now convert unexpected runtime exceptions into normal deployment results instead of allowing a background thread to terminate without a useful UI result. Live deployment output is appended to the existing log viewer while preserving the user's scroll position when they are inspecting older output.

## Non-goals

H28-B does not change:

- compiler semantics or bytecode generation;
- robot VM execution;
- the H27-A discovery protocol;
- the HTTP OTA endpoint contract;
- the existing first-flash / OTA Golden Path.

## Validation

```bash
python tests/h28_b/run_h28_b.py
python tests/h26_m/run_h26_m.py
python tests/h27_b0/run_h27_b0.py
python tests/h27_b/run_h27_b.py
python run_all_tests.py
```

Hardware regression remains the final acceptance step:

1. First-flash a new ESP32 over USB from RoboStudio.
2. Discover the robot over Wi-Fi.
3. Deploy a sample program over OTA.
4. Verify the robot reboots and becomes ready.
5. Repeat OTA deployment to confirm the runtime remains usable.
