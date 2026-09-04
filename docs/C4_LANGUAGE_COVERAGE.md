# C4 — RoboSim Language & Semantic Coverage

## Scope

C4 validates the semantics of the currently supported RoboSim Python subset from
source through the compiler, bytecode/ISA, VM and MockHardware runtime.

The goal is not to add new language features. Unsupported constructs are made
explicit instead of being silently ignored.

## Coverage

| Construct | Status | Evidence |
|---|---|---|
| Assignment | PASS | `tests/c4/test_language_semantics.py` |
| Variable read/write | PASS | reassignment test |
| Integer constants | PASS | arithmetic/operand tests |
| Arithmetic `+ - * / % **` | PASS (implemented operators) | compiler + runtime handlers |
| Comparisons `== != < > <= >=` | PASS | `test_all_comparisons` |
| `if` | PASS | nested/branch tests |
| `elif` | PASS | `test_if_elif_else_semantics` |
| `else` | PASS | branch tests |
| `while` | PASS | `test_while_semantics` |
| `for range()` step=1 | PASS | `test_range_for_semantics` |
| `break` / `continue` | PASS | existing regression suite |
| Boolean `and` | PASS | `test_boolean_and_semantics` |
| Boolean `or` | UNSUPPORTED | compiler explicitly rejects |
| Boolean `not` | UNSUPPORTED | compiler explicitly rejects |
| User function without parameters | PASS | existing + forward-definition test |
| User function parameters | UNSUPPORTED | compiler explicitly rejects |
| User function `return` | UNSUPPORTED | compiler explicitly rejects |
| Variable → API argument | PASS | dedicated test |
| Expression → API argument | PASS | dedicated test |
| Zero-valued API operands | PASS | dedicated regression test |

## Important semantic fixes

### 1. Function definitions are pre-registered

Previously a call before a function definition could fall through to the
unknown-function path. C4 pre-registers top-level function definitions before
compiling statements, while retaining the existing inline-function execution
model.

### 2. Unsupported user-function parameters/return are rejected

The previous compiler had no `visit_Return`, so a `return` could be silently
ignored. C4 now rejects parameterized user functions and `return` explicitly
instead of silently producing incorrect semantics.

### 3. `range()` step validation is corrected

The compiler previously compared the *variable/register index* of the compiled
step with `1`, rather than checking the source step value. C4 only accepts the
currently implemented `range(..., step=1)` contract and rejects other steps
deterministically.

### 4. Boolean constants

The runtime constant loader now checks `bool` before `int`, matching Python's
type hierarchy and preserving boolean runtime values.

## Non-goals

C4 does not redesign the language, add `or`/`not`, add function parameters,
or implement function-return semantics. Those remain explicit unsupported
features until a product/compiler contract is defined.

## Test command

```bash
python tests/c4/test_language_semantics.py
```

The full project regression is still required before C4 is considered complete.
