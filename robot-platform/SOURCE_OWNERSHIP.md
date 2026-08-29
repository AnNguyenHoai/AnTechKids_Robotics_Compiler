# Source Ownership Cleanup (H24-H2)

## Canonical production firmware

The only canonical firmware implementation is:

- `main/main.ino`
- `main/src/Services/VM/`
- `main/src/Services/Robot/`
- `main/src/Services/Line/`
- `main/src/Services/Motion/`
- `main/src/Sensor/`
- `main/src/Devices/`
- `main/src/Communication/`

PlatformIO production source root is `robot-platform/main`.

## Canonical VM ownership

| Domain | Canonical owner |
|---|---|
| Instruction ABI | `main/src/Services/VM/Instruction.h` |
| Program | `main/src/Services/VM/Program.h` |
| Program loading | `main/src/Services/VM/ProgramLoader.*` |
| VM state/context | `main/src/Services/VM/VMContext.h` |
| VM execution/dispatch | `main/src/Services/VM/VM.cpp` |
| Opcode contract | `main/include/generated/opcode.h` |
| Generated program | `main/src/Application/generated_program.h` |

## Explicitly removed / retired ownership

- `main/src/Communication/ProgramLoader.cpp` was an empty orphan and did not own a production loader.
- `main/src/generated/opcode.h` was a shadow copy of the generated opcode contract. The canonical header is `main/include/generated/opcode.h`.
- The former `robot-platform/runtime/` C++ VM/execution-engine tree was a parallel runtime architecture. It is preserved as non-production legacy material under `robot-platform/legacy/runtime_cpp_prototype/`.

## Legacy rule

Code under `robot-platform/legacy/` must not be included by production firmware and must not be used as a second implementation of the production VM, loader, dispatcher, instruction registry, or Robot API dispatch.

## Merge rule

Future feature merges must target the canonical owner above. Do not add a second implementation when the canonical implementation already exists. Changes to the generated opcode contract must be synchronized from the generator source rather than copied into another header.
