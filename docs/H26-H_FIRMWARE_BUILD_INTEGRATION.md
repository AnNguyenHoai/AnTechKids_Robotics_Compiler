# H26-H — Firmware Build Integration

## Purpose

H26-H turns the existing firmware-build step into an explicit, testable contract.
It consumes the compiler-produced `program.h`, stages it as the firmware
`generated_program.h`, and invokes PlatformIO for a **build-only** operation.

The integration is additive. It does not replace `tools/flash.py`, change VM
behavior, renumber opcodes, or claim physical upload success.

## Contract

```text
RoboSim source
    ↓
rewrite + compile
    ↓
build/<program>/program.h
    ↓
H26-H firmware_build.py
    ↓
robot-platform/main/src/Application/generated_program.h
    ↓
PlatformIO build (`pio run`)
    ↓
firmware.bin / firmware.elf
```

The PlatformIO environment defaults to the repository's existing `esp32dev`
environment. The command never includes the upload target.

## Tool

Run:

```text
python tools/firmware_build.py --program-header build/<program>/program.h
```

Optional arguments:

- `--project-dir` to select another PlatformIO project;
- `--environment` to select another PlatformIO environment;
- `--report` to write a machine-readable JSON result.

Before building, the input header is copied to the firmware application
boundary. After the build, the previous `generated_program.h` bytes are
restored, so regression runs do not leave source-tree mutations behind.

## Validation

`tests/h26_h/test_firmware_build.py` validates:

- the command is PlatformIO build-only and cannot silently become an upload;
- the generated header is staged at the production firmware boundary;
- the original firmware header is restored after success;
- the original firmware header is restored after build failure;
- a structured report records status, environment, command, upload=false, and
  firmware artifact candidates.

The standalone runner is:

```text
python tests/h26_h/run_h26_h.py
```

The test runner does not require PlatformIO. Actual firmware compilation is an
environment/toolchain validation and can be invoked through `tools/firmware_build.py`.

## Non-goals

- no ESP32 upload;
- no physical robot acceptance;
- no compiler/VM/RobotAPI changes;
- no replacement of the current `tools/flash.py` deployment command;
- no assumption that PlatformIO is installed in every development/test environment.
