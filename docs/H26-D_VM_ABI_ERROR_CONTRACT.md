# H26-D — VM ABI / Error Contract Hardening

## Scope

H26-D defines the authoritative, versioned error contract shared by the Robot VM, compiler-side Python tooling, and IDE diagnostics.

The contract source of truth is:

- `packages/robot-isa/error_contract.json`

Runtime adapters:

- `robot-platform/main/src/Services/VM/VMErrorContract.h`
- `robot-compiler/compiler/error_contract.py`

## Stable codes

| Code | ID | Meaning | Compatibility |
|---:|---|---|---|
| 0 | `ok` | No error | existing success state |
| 1 | `invalid_opcode` | VM cannot execute opcode | preserved |
| 2 | `program_overflow` | Program exceeds `MAX_PROGRAM_SIZE` | newly assigned |
| 3 | `invalid_jump` | Jump target is outside valid program range | preserved |
| 4 | `stack_overflow` | Call stack is full | preserved |
| 5 | `invalid_return` | Return executed without active call frame | preserved |
| 6 | `division_by_zero` | Integer division by zero | preserved |
| 7 | `modulo_by_zero` | Integer modulo by zero | preserved |
| 8 | `invalid_operand` | Operand is outside supported contract | reserved |
| 9 | `invalid_variable` | Variable index is outside supported range | reserved |
| 255 | `unknown` | Unknown/unrecognized diagnostic code | adapter fallback |

Existing production error numbers 1, 3, 4, 5, 6 and 7 are intentionally unchanged.

## Runtime behavior

`VM` now exposes:

- `GetErrorCode()` — stable numeric ABI code.
- `GetErrorId()` — semantic identifier for diagnostics.
- `GetErrorMessage()` — canonical human-readable message.

`Program::AddInstruction()` reports `program_overflow` through `Program::GetErrorCode()` while preserving the existing `false` return contract.

No successful instruction semantics, opcode numbering, generated program format, or Golden Path build/flash flow is changed by H26-D.

## Diagnostic rule

Consumers must use the numeric code and semantic ID from this contract rather than matching free-form log strings. Human-readable messages are presentation text and may be localized later without changing the ABI.

Unknown numeric codes must be treated as `unknown`; consumers must not infer a new meaning from an unrecognized value.

## Validation

The H26-D test suite verifies:

- unique and stable manifest codes/IDs;
- preserved legacy numeric meanings;
- Python adapter parity with the manifest;
- C++ adapter parity with the manifest;
- VM no longer embeds the preserved error codes as magic numbers;
- program overflow is surfaced by the program container.

Standalone runner:

```text
python tests/h26_d/run_h26_d.py
```

PlatformIO/ESP32 build and physical robot execution are not claimed as validated by this task unless the repository CI or hardware test environment executes them.

## Non-goals

- no opcode renumbering;
- no binary format migration;
- no compiler emission changes;
- no VM instruction dispatch redesign;
- no behavioral reinterpretation of existing error codes;
- no forced implementation of the currently reserved operand/variable validation rules.
