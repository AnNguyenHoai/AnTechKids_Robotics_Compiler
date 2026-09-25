# Line Sensor Snapshot Contract

## 1. Purpose

This document defines how line-sensor data is sampled and consumed by VM/control logic so that one logical control decision does not accidentally combine values captured at different times.

The contract applies to multi-channel line sensing used by line following, intersections, recovery, and VM-exposed line sensor getters.

## 2. Problem statement

Independent getters such as:

```text
left = line_left()
center = line_center()
right = line_right()
```

must not implicitly trigger three unrelated physical samples when those values are intended to represent one robot-control state. Mixing samples from different timestamps can create a sensor pattern that never existed physically and can destabilize control decisions.

## 3. Normative snapshot model

A line sensor snapshot is one atomic logical sample containing all channels required for one control cycle.

Conceptual model:

```cpp
struct LineSensorSnapshot {
    value_left;
    value_center;
    value_right;
    timestamp;
    sequence;
    valid;
};
```

Exact types/names may differ.

Normative requirements:

1. All channels in a snapshot come from one logical sampling event.
2. The snapshot carries a monotonic timestamp or equivalent sample-age evidence.
3. A monotonically increasing sequence/cycle identifier should be available for diagnostics/tests.
4. Snapshot validity/error state is represented consistently; partial channel success must not silently look like a fully valid atomic sample.
5. Consumers within the same control cycle read the same snapshot unless they explicitly request a new sample through the defined owner.

## 4. Snapshot ownership

The platform/control-loop sensor layer owns snapshot refresh. Individual VM getters do not own physical sampling.

Recommended cycle:

```text
begin control cycle
    -> refresh line snapshot once
    -> execute VM/control work against that snapshot
    -> diagnostics reuse same snapshot where semantically appropriate
end control cycle
```

The exact class owning the cache is an implementation decision, but ownership must be singular and clear. Duplicate caches in VM, RobotAPI, and line service are prohibited unless they have explicit synchronization contracts.

## 5. Getter semantics

VM/RobotAPI line getters that participate in one logical decision must:

- read from the current snapshot;
- not independently trigger new hardware sampling;
- expose values from the same sequence identifier;
- fail consistently when the current snapshot is invalid.

If the current cycle has no valid snapshot, the implementation must follow an explicit policy: refresh through the owner, return an error/invalid indication, or use another already-defined fallback. It must not silently mix old and new channel values.

## 6. Refresh policy

Snapshot refresh occurs at a defined control-cycle boundary or explicit owner-controlled refresh point.

The implementation must avoid both extremes:

- **too many reads:** every getter performs hardware I/O;
- **stale forever:** snapshot is reused across uncontrolled time without age tracking.

Tests must be able to prove that a sequence of line getter calls inside one cycle observes one snapshot and that the next cycle can observe a new sample.

## 7. Interaction with cooperative VM execution

`RunSlice(...)` can execute multiple instructions inside one firmware cycle. Therefore the snapshot lifetime is tied to the platform/control cycle, not to an arbitrary instruction count.

A slice must not refresh a line snapshot merely because another line getter instruction is encountered.

If one logical VM slice crosses a platform cycle boundary in a future architecture, that boundary must remain explicit and testable. The current initiative should prefer returning control to the firmware loop and refreshing at the next cycle rather than hiding refreshes inside VM dispatch.

## 8. Line follower integration

The line follower/state machine should consume the shared snapshot or a derived value from that same sample. It must not read one set of channels while VM-exposed getters use a different physical read during the same logical decision cycle.

Existing follower semantics such as steering direction, lost-line confirmation, recovery, and intersection handling are outside this contract unless snapshot consistency exposes a bug. This initiative must not rewrite line-follow algorithms under the name of responsiveness.

## 9. Expensive and on-demand I/O

This contract is intentionally narrow.

It does **not** require caching every sensor in the robot. Ultrasonic, IMU, battery, or other hardware may remain on-demand when their API contract requires it.

For diagnostics, duplicate reads should be avoided when one already-valid sample can be reused without changing semantics.

## 10. Failure handling

A physical line-sensor sampling failure must result in a deterministic snapshot state.

The implementation must not:

- preserve one new channel with two old channels and report the snapshot as valid;
- invent default values that look like real sensor data unless an existing API explicitly defines such defaults;
- silently reuse an arbitrarily old snapshot without age/validity evidence.

## 11. Instrumentation

Development/test evidence should expose:

- snapshot sequence;
- snapshot timestamp/age;
- physical-read count per control cycle;
- number of consumers/getters served from the snapshot;
- invalid/error count.

This enables tests to prove consistency rather than inferring it from steering behavior.

## 12. Compatibility guards

1. No bytecode-format or opcode-number change is required.
2. Existing line getter logical meanings remain unchanged; only sampling consistency is formalized.
3. Compiler must not bundle line getters into a special synthetic instruction solely to satisfy this contract.
4. Existing line-follow stability regression remains required.
5. H35 compatibility review is required if implementation changes externally observable sensor semantics beyond same-cycle consistency.

## 13. Required tests

At minimum:

- three line getters in one cycle return values from one sequence;
- repeated getter calls do not increase physical-read count inside the same cycle;
- next cycle can refresh and increment sequence;
- invalid sample is atomic and deterministic;
- line follower and VM getters observe the same cycle sample where both participate;
- stop/reset invalidates stale snapshot state as defined by implementation;
- full line-follow regression remains green.

## 14. Definition of Done

The snapshot contract is complete when one shared owner controls line sampling, all in-scope consumers use a consistent sample per control cycle, sample age/sequence can be tested, duplicate reads are removed where appropriate, and physical qualification confirms stable line-control behavior.
