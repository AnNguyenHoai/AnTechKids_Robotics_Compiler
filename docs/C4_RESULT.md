# C4 Result — RoboSim Language & Semantic Coverage

## Result

**PASS**

C4 added semantic coverage for the currently supported language subset and
fixed three correctness issues found during the audit.

### Test result

- C4 semantic tests: **14/14 PASS**
- Existing compiler tests: **PASS**
- Frontend tests: **PASS**
- Existing E2E suite: **8/8 PASS**
- Full `run_all_tests.py`: **PASS**

## Fixes made

1. **Function definitions are pre-registered**
   - A user-defined function can now be called before its definition in source
     order, using the existing inline-function model.

2. **Unsupported function semantics are explicit**
   - Parameterized user functions are rejected.
   - `return` inside user-defined functions is rejected.
   - This prevents unsupported constructs from being silently ignored.

3. **`range()` step validation**
   - The compiler now validates the source step value rather than comparing a
     temporary variable/register index.
   - Only the currently implemented `step=1` contract is accepted.

4. **Boolean constant runtime typing**
   - Runtime constant loading checks `bool` before `int`, preserving the intended
     boolean runtime type.

## Semantic coverage verified

- assignment and reassignment
- arithmetic expressions
- all six comparison operators
- `if / elif / else`
- nested `if`
- `while`
- `for range()` with step 1
- boolean `and`
- variable → API argument
- expression → API argument
- zero-valued API operands
- function call before definition

## Explicitly unsupported

These remain unsupported by the current compiler contract and are documented
rather than silently miscompiled:

- boolean `or`
- boolean `not`
- user-function parameters
- user-function return semantics
- `range()` step values other than 1

## Remaining limitation

C4 validates software semantics through the current compiler/VM/MockHardware
pipeline. Physical ESP32 behavior remains the scope of C5.
