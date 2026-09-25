# VM Responsiveness Compatibility Matrix

## 1. Purpose

This document records which VM-responsiveness changes are compatible with the current compiler/firmware contract and which changes require explicit H35 compatibility review.

It is intentionally fail-closed: absence from the allowed matrix is not evidence of compatibility.

## 2. Current baseline

Baseline for this initiative:

- repository base commit: `5fd5b18b422f8b6e36eb741d7472e04633d8d522`;
- current H35 platform/compiler/firmware compatibility generation: generation 1;
- existing opcode numbering and bytecode encoding remain authoritative;
- existing `Step()` behavior remains the legacy execution contract;
- existing C2 dispatch semantics, including documented blocking operations, remain the compatibility reference until their cooperative conversion is explicitly implemented and tested.

## 3. Allowed changes within current generation

The following changes are considered candidates to remain within the current compatibility generation **provided regression evidence proves externally equivalent program semantics**:

| Change | Default classification | Required evidence |
|---|---|---|
| Add `RunSlice(...)` alongside existing `Step()` | Compatible extension | Step regression + slice tests |
| Add VM-internal pending/resume state | Internal implementation | PC/state regression |
| Convert wait from firmware-thread blocking to cooperative pending state while preserving elapsed-time semantics | Semantic-preserving runtime change | timing + PC + stop tests |
| Add instrumentation counters/timestamps | Internal/diagnostic | no behavior drift |
| Share one line-sensor snapshot per control cycle | Contract clarification | sensor consistency + line-follow regression |
| Integrate bounded VM slices in firmware main loop | Runtime scheduling change | full regression + physical qualification |

These rows do not automatically approve a change. They define the expected compatibility posture for review.

## 4. Changes requiring explicit H35 review

The following MUST trigger H35 compatibility analysis and may require a new generation/policy entry:

- opcode number changes;
- bytecode encoding/layout changes;
- source-language semantic changes;
- compiler emitting a new instruction sequence that old generation-1 firmware cannot correctly execute;
- firmware assigning a different externally observable meaning to existing bytecode;
- changed sensor return semantics visible to programs beyond same-cycle consistency;
- changed duration/motion semantics that alter the logical outcome of an existing program;
- removal or incompatible redefinition of `Step()`;
- new wire/discovery/runtime contract fields required for execution compatibility.

No implementation PR may infer that a semantic change is safe only because tests for one scenario pass.

## 5. Compatibility guards

Every implementation PR under this initiative must state whether it changes any of these axes:

| Axis | Expected default |
|---|---|
| Robot Language API | unchanged |
| canonical ISA | unchanged |
| opcode numbering | unchanged |
| bytecode encoding | unchanged |
| compiler generation | unchanged |
| firmware compatibility generation | unchanged unless H35 review says otherwise |
| discovery protocol/schema | unchanged |
| `Step()` semantics | unchanged |
| existing source program logical result | unchanged |

If any answer is not `unchanged`, the PR must link the relevant contract/policy update.

## 6. Legacy blocking behavior and cooperative path

Some current operations are documented as blocking. Cooperative conversion must distinguish two concepts:

1. **Logical instruction semantics** — what the program means and when an instruction is complete.
2. **Firmware scheduling behavior** — whether the firmware thread remains blocked while that logical operation is pending.

The target is to improve the second without silently changing the first.

For an operation converted to cooperative execution:

- initialization side effects happen once;
- pending time/condition is explicit;
- PC does not advance while incomplete;
- completion/finalization happens once;
- stop/fault behavior is deterministic;
- observable program result remains equivalent unless separately versioned.

## 7. `Step()` vs `RunSlice()` matrix

| Property | `Step()` | `RunSlice()` |
|---|---|---|
| Primary role | legacy compatibility | responsive scheduling |
| Instruction count | existing single-step semantics | bounded multiple work units allowed |
| Pending cooperative op | implementation must preserve Step contract | explicit yield/wait supported |
| Returns platform control regularly | not guaranteed by legacy blocking op | required |
| Compiler changes required | no | no |
| Bytecode changes required | no | no |

Implementation must avoid making `RunSlice()` merely an unbounded loop around blocking `Step()`.

## 8. Sensor compatibility

Same-cycle line snapshot consistency is intended as a sampling-quality/runtime contract, not a new Robot Language API.

Allowed by default:

- one physical read feeding left/center/right getters in the same control cycle;
- timestamp/sequence metadata used internally/tests;
- diagnostics reusing the same valid cycle sample.

Requires explicit review:

- changing threshold meanings;
- changing polarity/normalization visible to user programs;
- changing channel mapping;
- changing stale/error fallback values;
- changing source API return type/range.

## 9. Regression gate

No responsiveness implementation is complete unless all relevant existing gates pass, including the existing line-follow steering stability gate and H32/H33/H34/H35 compatibility chain where applicable.

New responsiveness tests are additive; they never replace existing regression coverage.

## 10. Review checklist

Every PR under this initiative must answer:

- Does this alter source-language behavior?
- Does this alter compiler output?
- Does this alter opcode numbers/encoding?
- Does this alter logical instruction completion semantics?
- Does this alter sensor values visible to programs?
- Does this alter stop/fault semantics?
- Is `Step()` still compatible?
- Is H35 generation review required?
- Which regression and physical tests prove the answer?

A missing answer is treated as unresolved, not as compatible.
