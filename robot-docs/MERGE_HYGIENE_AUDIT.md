# Merge Hygiene Audit — Robotics(4)

## Scope
Audit of current merged codebase after H24-R recovery.

## Critical finding: duplicate RobotAPI declarations
`robot-platform/main/src/Services/Robot/RobotAPI.h` contains:
- line 146: `void Wait(uint32_t ms);`
- line 262: `void Wait(uint16_t ms);`

VM passes `int32_t`, so overload resolution is ambiguous.

The same header also duplicates:
- line 148 and line 265: `void setMotorsDirect(int left, int right);`

### Required fix
Keep the stable canonical declarations:
```cpp
void Wait(uint32_t ms);
void setMotorsDirect(int left, int right);
```
Remove the late duplicate utility declarations.

## RobotAPI implementation
No duplicate RobotAPI function definitions were found in `RobotAPI.cpp`.

## SerialCommandHandler
Encoder integration is present without a duplicate function definition. Repeated statement text exists in different command branches and is not itself a merge conflict.

## Broader repository hygiene
The repository still contains parallel/legacy source trees:
- runtime and main VM implementations
- duplicate dispatcher/registry trees
- `src/Communication/ProgramLoader.cpp` and `src/Services/VM/ProgramLoader.cpp`
- multiple generated opcode headers

These are not all compile-time conflicts today, but they are merge-risk hotspots because Arduino builds the active source tree recursively.

## Recommendation
H24-H1: remove duplicate RobotAPI declarations immediately.
H24-H2: define canonical source ownership for VM/runtime/generated headers and archive or exclude obsolete parallel implementations.


## H24-H2 Source Ownership Cleanup

Canonical production ownership was established in `robot-platform/SOURCE_OWNERSHIP.md`. The empty Communication ProgramLoader and shadow generated opcode header were removed. The parallel C++ runtime was quarantined under `robot-platform/legacy/runtime_cpp_prototype/`.
