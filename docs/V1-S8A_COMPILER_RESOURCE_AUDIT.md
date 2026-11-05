# V1-S8-A — Compiler resource audit and low-risk optimization

**Base:** main at `e0de75ecc535cca8a8240ab24ee9cb39d7026b08`, after S7. **Scope:** compiler only, no VM capacity changes.

## Verified baseline facts

- Resource source of truth: `packages/robot-isa/resource_contract.json`: 128 instructions, 32 VM variable slots, 8 call stack, 8 loop depth.
- Firmware mirrors limits in `robot-platform/main/src/Services/VM/Program.h` and `VMContext.h`.
- Reported original RoboSim program failed with **182 instructions**, at least one variable index **105**; maximum reported slot span >=106.
- User program includes 7 calls to `rcu.GetTraceV2I2CState(1, channel)` with channel 1–7, but physical V1 line array has only 5 channels. Fixing compiler capacity does not add hardware channels. Verify RoboSim channel ordering before deployment.

## Root causes

1. `if` / `while` branches call `compile_expression(test)`. Complex boolean expressions materialize 0/1 values and intermediate jumps even when the only consumer is a conditional branch.
2. `allocate_temp()` previously incremented a fresh identifier and a new global VM slot for **every** constant, comparison or call argument. Unused slots never recycled across statements or nested control flow.
3. User-defined functions are **inlined** by `visit_Call`; repeated invocations expand code size instead of using VM call/return. This remains unchanged in S8-A because it requires more comprehensive ABI analysis.

## Implemented optimization

- Direct conditional short-circuit lowering for `and`, `or`, and `not`; assigned Boolean expressions retain their existing normalized 0/1 behavior.
- Reclaim compiler-generated scratch slots after each statement and after a branch predicate, without reclaiming user variables or enclosing for-loop bounds.
- Same public APIs, Python syntax, VM opcodes, firmware resource caps, and motor behavior.
- A preserved seven-channel program fixture and regression test measure **actual** instructions and used variable span. CI determines results; no physical correctness claim.

## Safety / qualification

- Compiler-generated code still must pass `validate_program` before deployment; **do not** bypass it to enable larger programs.
- A successful compile does not establish correct behavior for seven channels on a five-channel robot.
- Short-circuit order must remain left-to-right; skipped RHS calls must not execute.
- Runtime stability, firmware stack capacity and flash size are not relaxed.
- Reject merge on any changed semantics in existing compiler/VM regression suites.

## Next gate

CI outputs `S8-A USER LINE7: instructions=N/128; variable_index_span=M/32`. If N or M still exceeds limits, retain measured findings and plan targeted follow-up (compiler codegen and then controlled VM capacity in S8-B), rather than altering contract numbers without proof.
