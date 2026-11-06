# V1-S8-B — VM Capacity Expansion

## Status and dependency

S8-B is a **stacked change on the S8-A optimization branch**, not a stand-alone merge-ready release. Base commit: `cc1f789b6429bc937c5757d9440e511942351b24`. Merge S8-A first after it passes compiler/boolean regression gates; then rebase/retarget S8-B to main.

## Capacity contract

| Resource | Old | New |
|---|---:|---:|
| Program instructions | 128 | **512** |
| Runtime variables (int32) | 32 | **128** |
| Call stack depth | 8 | **8** |
| Loop nesting | 8 | **8** |

The single source of truth for tooling is `packages/robot-isa/resource_contract.json`. The firmware uses matching constants in `Program.h` and `VMContext.h`. The safety validator reads the canonical JSON. No safety validation is bypassed.

### ABI and memory review

- `Instruction`: `Opcode` plus four `int32_t` operands. A typical ESP32 layout uses 20 bytes per instruction; verify using the actual firmware toolchain.
- Instruction array grows from approximately **2,560 bytes to 10,240 bytes** (increment **7,680 bytes**). `Program` is global in `main.ino`; it is **not allocated as a local 10 KiB stack object** there.
- `VMContext::mVariables` grows from **128 bytes to 512 bytes** (increment **384 bytes**), assuming 4-byte `int32_t`.
- Program counter and instruction count are already `uint16_t` (sufficient for 512). VM operands are `int32_t`; bytecode fields are unchanged. `LoopFrame::variableId` is `uint8_t` and supports index 0..127.
- The generated program header may also occupy flash as a separate `const Instruction[]` image; check actual RAM/flash and OTA footprint after Arduino build.
- Capacity is a **compiler + firmware pair**. An old 128/32 firmware cannot safely execute an independently supplied 512/128 program. Use the upgraded full firmware/OTA build for long programs; do not claim compatibility with legacy program-upload paths.
- No change to opcodes, motor operations, Line5 controller, timing, GPIO mapping or hardware feature flags.

## Tests and acceptance criteria

1. 512 simple instructions accepted; 513 rejected as `program_overflow`.
2. VM variables 0..127 accepted; 128 rejected as `invalid_variable`.
3. Jump target over 255 accepted when within program length; out-of-range jumps still rejected.
4. Exact user line-following fixture must fit the expanded resource contract; print generated instruction count and maximum referenced variable span.
5. S8-A Boolean semantics and compiler regressions pass. S8-B must **not** relax safety gate rules.
6. Firmware toolchain compile, Windows production packaging and RoboStudio integration pass with one canonical contract.
7. Before physical sign-off: measure free heap/flash, verify OTA, run motor/Line5/Touch/Servo smoke regressions and check feedback latency.

## Limits of this change

The user fixture reads RoboSim channels 1..7, while V1 physical line sensor has 5 detectors. VM capacity expansion does not add channels or correct the robot motion algorithm. Complete projection/mapping verification and on-robot acceptance separately.

If the fixture remains above 512 instructions or 128 variables, **do not silently increase the values**. Record the exact numbers and continue compiler-level reductions or a separately audited S8-B revision.
