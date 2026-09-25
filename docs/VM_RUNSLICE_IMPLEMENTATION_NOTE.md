# VM RunSlice Core — Implementation Note

Tracking: #305, parent #302
Baseline: `main@e5dc9b166d84ba741570ab599e415e4e4889b99d`

## Scope implemented in VM-RT C

`RunSlice(const VMRunSliceBudget&)` is an additive runtime API layered on top of the frozen legacy `Step()` contract.

Normative work-unit rule:

- one slice work unit is at most one `Step()` invocation;
- `maxWorkUnits == 0` executes no VM work;
- the loop is bounded by `maxWorkUnits`;
- `RunSlice` never dispatches an instruction directly;
- `Step()` source semantics are unchanged.

The result reports:

- termination reason;
- work units consumed;
- start PC;
- end PC.

Termination reasons implemented by this phase:

- `BudgetExhausted`;
- `Yielded` for a non-wait cooperative pending operation;
- `Waiting` for `VMPendingOperation::Wait`;
- `Halted` when execution is no longer running at/after program end;
- `Stopped` when execution is no longer running before program end without a VM fault;
- `Fault` when the VM error contract is non-zero.

## Compatibility boundary

This phase does **not**:

- alter opcode numbering or bytecode format;
- alter compiler output;
- alter `Step()` dispatch semantics;
- convert remaining blocking RobotAPI calls;
- claim a hard wall-clock slice deadline;
- integrate `RunSlice` into the firmware main loop.

A bounded work-unit slice is cooperative, not preemptive. If one `Step()` enters a synchronous RobotAPI call such as bounded ultrasonic I/O or an unresolved blocking call, `RunSlice` cannot interrupt that call mid-step. Those conversions/measurements remain assigned to #307/#310.

## Test evidence

Host CI runs:

- `tests/vm_responsiveness/run_vm_responsiveness_baseline.py` to protect the #304 `Step()` baseline;
- `tests/vm_responsiveness/run_run_slice_core.py` to verify the scheduler API, work-unit bound, termination reasons, pending/yield mapping, and non-preemptive limitation.

The impact-based workflow runs these gates plus line-follow and relevant H32–H35 gates for VM changes, without building production release artifacts.
