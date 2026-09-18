# B2.4 — Hardware & Flash Portability

## Goal

A production RoboStudio ZIP copied to a clean supported Windows machine must be able to reach the USB-flash boundary without borrowing developer tooling.

The software contract is:

`copy ZIP -> extract -> select visible COM port -> compile with packaged compiler -> build/upload with packaged PlatformIO + ESP32 packages -> flash selected robot port`

Global Python, global PlatformIO, a source checkout, developer virtual environments, and developer-machine COM defaults are not part of the contract.

## What belongs to the production artifact

The release owns:

- RoboStudio.
- Portable Python runtime.
- PlatformIO Core Python package.
- Packaged PlatformIO platform metadata and packages/toolchain/uploader closure.
- Application-owned compiler and RoboSim frontend.
- Production firmware project.
- Minimal runtime deployment tools under `tools/`.

The deployment runtime tool allow-list intentionally excludes release builders, tests, repository migration tools, and other development-only scripts.

## What remains an operating-system prerequisite

The USB/UART bridge driver is not bundled into the RoboStudio ZIP.

Different ESP32 boards may expose CP210x, CH34x, FTDI, native USB, or another bridge. Windows may already provide a compatible driver. RoboStudio therefore does not install or guess a vendor driver.

Driver readiness is proven objectively: the selected serial device must be visible through RoboStudio's application-owned PlatformIO runtime.

## Serial discovery contract

`tools/hardware_preflight.py` is the canonical USB serial preflight.

It executes:

`platformio device list --json-output`

through the B2.2/B2.3 sealed deployment boundary.

Properties:

- PlatformIO resolves from the production artifact in packaged mode.
- Host `PATH`, `PYTHONPATH`, virtualenv, Node, and host PlatformIO injection cannot satisfy the check.
- Writable PlatformIO state is external to the extracted release.
- An explicit requested port is mandatory.
- RoboStudio never automatically selects the first serial device.
- A missing requested port fails before firmware staging or uploader execution.
- The diagnostic lists detected ports or tells the user to reconnect the robot/install the board's USB/UART driver when no serial device is visible.

## USB upload contract

Both first-flash bootstrap and normal USB deployment:

1. Require `--port`.
2. Run canonical hardware preflight.
3. Use the canonical port returned by preflight.
4. Always invoke PlatformIO upload with an explicit `--upload-port <validated-port>`.
5. Never use a `platformio.ini` developer-machine COM fallback.

The old `upload_port = COM4` fallback is removed from the base ESP32 environment.

OTA retains its explicit network upload target and is not treated as USB serial deployment.

## Compiler portability

Deployment no longer compiles through source-tree wrappers such as `tools/rewrite.py` and `tools/compile.py`.

It uses the same relocatable compiler application contract as RoboStudio GUI compilation:

`compiler/robostudio_bridge.py --request <compile_request.json>`

This prevents USB/OTA deployment from depending on repository layout after the production ZIP is copied elsewhere.

## Production deployment tool payload

The production distribution contains only the runtime modules required by deployment/preflight/qualification:

- `bootstrap_config.py`
- `build_isolation.py`
- `dependency_closure.py`
- `deploy_robot.py`
- `deployment_contract.py`
- `deployment_runtime.py`
- `firmware_workspace.py`
- `hardware_preflight.py`
- `runtime_paths.py`
- `runtime_resources.py`
- `target_machine_prerequisites.py`
- `target_machine_qualification.py`

After this allow-list is staged, production boundary evidence, runtime-closure validation, and the distribution manifest are regenerated so the added runtime files cannot bypass release validation.

## Target-machine qualification scopes

- `compile`: no external runtime/tool prerequisite.
- `hardware`: records the external USB/UART-driver policy without claiming a physical port is currently ready.
- `flash`: strict readiness scope. It only passes when an explicitly selected port is visible through application-owned PlatformIO.

Example on a real extracted release:

```text
runtime\bin\python.exe tools\target_machine_qualification.py --scope flash --serial-port COM7 --json
```

A successful `flash` qualification proves software/runtime closure and current serial-device visibility. It does not by itself prove that a physical upload and robot execution completed successfully.

## Automated B2.4 acceptance

`tests/b2_4/run_b2_4.py` verifies:

- PlatformIO device-list JSON parsing.
- Explicit-port selection and case-insensitive Windows COM matching.
- No implicit first-port selection.
- Missing/wrong port diagnostics.
- No-device driver guidance.
- Device discovery through the canonical packaged PlatformIO command boundary.
- External writable state for preflight.
- Host PATH not forwarded into the final discovery subprocess.
- Preflight failure stops before firmware staging/uploader execution.
- Successful bootstrap upload always uses the validated port.
- `flash` qualification fails without visible hardware and passes with deterministic visible-port evidence.
- USB/UART driver remains external rather than bundled.
- Firmware configuration contains no developer `COM4` fallback.

The B2.4 gate is a separate fail-closed Windows CI step and is also part of `run_all_tests.py`.

## B2.4 / B2.5 boundary

B2.4 proves the production software path up to and including the USB upload boundary with deterministic automated tests and clean artifact ownership rules.

GitHub-hosted CI does not have the project's physical ESP32/robot or its USB bridge. Therefore B2.4 does **not** claim a real robot was physically flashed by CI.

B2.5 must perform the final independent-machine E2E:

`copy ZIP -> extract -> launch RoboStudio -> select real COM -> compile -> physically flash -> robot reboots/runs -> collect evidence`

on a clean Windows machine with the appropriate board driver available.
