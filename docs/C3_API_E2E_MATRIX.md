# C3 — RoboSim API / Hardware E2E Matrix

## Scope

C3 closes the verified execution path for the P0 RoboSim capabilities that already
have a real compiler, VM and platform implementation. The automated C3 suite runs:

`RoboSim source → frontend rewrite → RobotCompiler → ISA → binary → ProgramLoader → VM → MockHardware`

A C3 MockHardware PASS is **not** a physical ESP32 PASS.

## Results

| Capability | Compile | Bytecode | VM | Runtime / MockHardware | Physical ESP32 | Status |
|---|---|---|---|---|---|---|
| `SetMoveRun` / `SetMoveStop` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `SetWaitForTime` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `GetUltrasound` | PASS | PASS | PASS | PASS | UNVERIFIED here | MOCK-E2E PASS |
| `GetTouch` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `GetLightSensor` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `GetTraceV2I2CChxState` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `GetTraceV2I2C` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `GetTraceV2I2CData` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `Set3CLed` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `line_basis` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `line_follow` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `line_stop` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |
| `line_millisecond` | PASS | PASS | PASS | PASS | UNVERIFIED | MOCK-E2E PASS |

## Important C3 implementation finding

The existing integration ISA conversion used a sparse-operand fallback that dropped
valid operands when an earlier operand was zero. This affected APIs such as:

- `Set3CLed(1, 1)` after rewrite to canonical operands
- `ReadLine`
- trace APIs
- other fixed-position operand instructions

C3 fixed the converter to preserve **operand position**, including zero-valued
operands, for the covered sensor/output/line opcodes.

This was required for a real E2E path; it was not merely a test workaround.

## Runtime additions

The Python VM runtime now has MockHardware-backed execution for:

- LED output
- trace value/state/raw reads
- `line_basis`
- `line_follow`
- `line_stop`
- `line_millisecond`

These use the existing runtime/MockHardware abstractions and do not alter the ESP32
RobotAPI implementation.

## Known boundary

Physical ESP32 validation remains a separate step. PlatformIO/physical hardware
evidence is not available from the automated C3 environment, so no physical PASS is
claimed here.

## Next

C4 should address the remaining language-construct gaps and then build the physical
ESP32 program matrix for the P0 capabilities.
