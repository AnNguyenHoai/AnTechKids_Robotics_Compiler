# S3.2 Architecture Correction Report

**Reviewer/Correction:** Architecture layer  
**Status:** Ready for review

## Corrections made

1. Corrected target API count from 25 to **29**.
2. Corrected coverage denominator: 9/29 = **31.0%**, not 36%.
3. Split evidence classes into `SAMPLE_OBSERVED`, `RC1_OBSERVED`, and `SPEC_ONLY`.
4. Confirmed **26** APIs occur in scanned Python samples; **3** additional APIs are RC1-only.
5. Removed semantic reinterpretation from unresolved canonical names:
   - no `line_follow_bitmap`
   - no `line_turn_until_line`
   - no `line_stop_at_intersection`
6. Preserved trusted spec parameter names where available (`type`, `angle`, `direction`, `degree`) without expanding their meaning.
7. Made `SetWaitForTime(second)` → `wait(milliseconds)` an explicit boundary conversion.
8. Added string-transport gap analysis.
9. Rebuilt priority from actual sample occurrence counts and transport risk.
10. Corrected stale timing documentation.

## String transport finding

The compiler codebase contains string support in IR/ISA/binary constant-pool components.

However the current physical embedded VM uses:

```text
Instruction: opcode + int32_t p1/p2/p3
VM variables: int32_t[]
```

Therefore compiler-side string support does **not** prove embedded VM string transport.

This is a real architecture gap for:

```text
SetMoveInitialize
SetMoveRunAngle
line_set_initialize
```

S3.3 must use enum IDs for closed vocabularies or introduce a string table/ID mechanism. Raw pointers are forbidden.

## Corrected coverage

```text
Target interfaces: 29
Supported end-to-end interfaces: 9
Coverage: 31.0%
Missing pipeline interfaces: 20
```

## Freeze recommendation

The corrected **interface naming and preservation rules** are suitable to freeze as the baseline.

Do not freeze a concrete string ABI until S3.3D (or a preceding string-transport design task) selects enum/string-table transport.
