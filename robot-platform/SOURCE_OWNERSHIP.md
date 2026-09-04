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

## Retired ownership

- `main/src/Communication/ProgramLoader.cpp` was an empty orphan and did not own a production loader.
- `main/src/generated/opcode.h` was a shadow copy of the generated opcode contract. The canonical header is `main/include/generated/opcode.h`.
- The former `robot-platform/runtime/` C++ VM/execution-engine tree was a parallel runtime architecture and has been retired.
- The historical `robot-platform/legacy/runtime_cpp_prototype/` archive has been removed after real hardware validation of the canonical runtime/deployment path.
- The former `robot-platform/deploy.py` deployment script and its `robot-platform/deploy_program.py` sample have been retired; normal deployment is owned by `tools/deploy_robot.py`.

## Deployment ownership

| Concern | Canonical owner |
|---|---|
| Rewrite | `tools/rewrite.py` |
| Compile | `tools/compile.py` |
| Deployment contract | `tools/deployment_contract.py` |
| One-click deployment | `tools/deploy_robot.py` |
| Physical preflight | `tools/physical_validation.py` |
| Low-level flash/recovery primitive | `tools/flash.py` |

## Legacy rule

Production firmware must only consume sources under `robot-platform/main`. Legacy code must not be introduced as a second implementation of the production VM, loader, dispatcher, instruction registry, Robot API dispatch, or deployment workflow.

## Merge rule

Future feature merges must target the canonical owner above. Do not add a second implementation when the canonical implementation already exists. Changes to the generated opcode contract must be synchronized from the generator source rather than copied into another header.
