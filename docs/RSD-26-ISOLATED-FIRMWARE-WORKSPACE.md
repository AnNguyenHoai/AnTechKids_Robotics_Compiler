# RSD-26 — Isolated Firmware Workspace

## Purpose

RoboStudio production deployment must never modify the packaged firmware template or the repository checkout. PlatformIO-generated state and `generated_program.h` belong to a writable per-project workspace.

## Runtime flow

```text
Production release
  firmware/robot-platform/
          |
          | copy
          v
User data / RoboStudio / build / <project> / platformio / firmware/
          |
          +-- generated_program.h
          +-- PlatformIO .pio/build state
          +-- firmware.bin
```

## Contract

1. Packaged firmware is read-only input.
2. Source-mode development may fall back to repository `robot-platform`.
3. Frozen/packaged mode requires `firmware/robot-platform` inside the application root.
4. The generated header is written only into the isolated workspace.
5. PlatformIO is executed with isolated workspace/build/cache/libdeps/shared directories.
6. `esp32dev`, `esp32dev_bootstrap`, and `esp32dev_ota` remain the supported production environments.
7. Firmware artifacts are read back from the isolated build directory, never from the packaged project.
8. Credentials remain process environment/config inputs and are not copied into the release template.

## Audit result

The previous deployment path used a repository-global `robot-platform` and copied `generated_program.h` into that tree. That violated the production immutability boundary even though the PlatformIO build cache itself was isolated.

RSD-26 moves the project copy and generated header into the writable application build workspace. This removes the source/install-tree mutation from normal deployment.

## Remaining qualification

This change does not claim a real clean Windows or physical ESP32 qualification. Those still require execution with the actual bundled PlatformIO runtime and hardware.
