#!/usr/bin/env python3
"""VM responsiveness scheduler/pending-state/snapshot/instrumentation gate.

This deterministic host gate covers VM-RT C/D/E/F/H. It verifies scheduler,
pending-state, timed-operation, shared line-snapshot, and instrumentation source
contracts without pretending host CI measures ESP32 wall-clock performance.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VM_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.h"
CTX_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMContext.h"
PENDING_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMPendingState.h"
RUN_SLICE_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRunSlice.cpp"
VM_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
TELEMETRY_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRuntimeTelemetry.h"
TELEMETRY_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VMRuntimeTelemetry.cpp"
FIRMWARE = ROOT / "robot-platform" / "main" / "main.ino"
ROBOT_API_H = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.h"
ROBOT_API_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPI.cpp"
ROBOT_COOP_CPP = ROOT / "robot-platform" / "main" / "src" / "Services" / "Robot" / "RobotAPICooperative.cpp"
SNAPSHOT_H = ROOT / "robot-platform" / "main" / "src" / "Sensor" / "LineSensorSnapshot.h"
SNAPSHOT_CPP = ROOT / "robot-platform" / "main" / "src" / "Sensor" / "LineSensorSnapshot.cpp"
TCRT_H = ROOT / "robot-platform" / "main" / "src" / "Sensor" / "TCRT5000.h"
TCRT_CPP = ROOT / "robot-platform" / "main" / "src" / "Sensor" / "TCRT5000.cpp"
SPEC = ROOT / "docs" / "VM_COOPERATIVE_EXECUTION_SPEC.md"
SNAPSHOT_SPEC = ROOT / "docs" / "LINE_SENSOR_SNAPSHOT_CONTRACT.md"
INSTRUMENTATION_SPEC = ROOT / "docs" / "VM_RESPONSIVENESS_INSTRUMENTATION.md"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    header = VM_H.read_text(encoding="utf-8")
    context = CTX_H.read_text(encoding="utf-8")
    pending = PENDING_H.read_text(encoding="utf-8")
    run_slice = RUN_SLICE_CPP.read_text(encoding="utf-8")
    legacy = VM_CPP.read_text(encoding="utf-8")
    telemetry_h = TELEMETRY_H.read_text(encoding="utf-8")
    telemetry_cpp = TELEMETRY_CPP.read_text(encoding="utf-8")
    firmware = FIRMWARE.read_text(encoding="utf-8")
    robot_h = ROBOT_API_H.read_text(encoding="utf-8")
    robot_cpp = ROBOT_API_CPP.read_text(encoding="utf-8")
    robot_coop = ROBOT_COOP_CPP.read_text(encoding="utf-8")
    snapshot_h = SNAPSHOT_H.read_text(encoding="utf-8")
    snapshot_cpp = SNAPSHOT_CPP.read_text(encoding="utf-8")
    tcrt_h = TCRT_H.read_text(encoding="utf-8")
    tcrt_cpp = TCRT_CPP.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    snapshot_spec = SNAPSHOT_SPEC.read_text(encoding="utf-8")
    instrumentation_spec = INSTRUMENTATION_SPEC.read_text(encoding="utf-8")

    for reason in ("BudgetExhausted", "Yielded", "Waiting", "Halted", "Stopped", "Fault"):
        check(f"RunSlice exposes {reason} reason", reason in header)

    check("RunSlice budget has deterministic work-unit bound", "uint16_t maxWorkUnits;" in header)
    check("RunSlice result reports consumed work", "uint16_t workUnits;" in header)
    check("RunSlice result reports start PC", "uint16_t startProgramCounter;" in header)
    check("RunSlice result reports end PC", "uint16_t endProgramCounter;" in header)
    check("VM exposes additive RunSlice API", "VMRunSliceResult RunSlice(const VMRunSliceBudget& budget);" in header)
    check("legacy Step API remains directly exposed", "void Step();" in header)

    step_start = legacy.index("void VM::Step()")
    step_end = legacy.index("bool VM::ContinuePendingLineOperation()", step_start)
    step_body = legacy[step_start:step_end]
    check("legacy Step still dispatches exactly once", step_body.count("ExecuteInstruction(instruction);") == 1)
    check("legacy Step still contains no scheduler loop", "while (" not in step_body and "for (" not in step_body)
    check("RunSlice does not call ExecuteInstruction directly", "ExecuteInstruction(" not in run_slice)

    loop_marker = "while (static_cast<uint32_t>(workUnits) < extendedWorkLimit)"
    check("zero budget exits without Step", run_slice.index("budget.maxWorkUnits == 0") < run_slice.index(loop_marker))
    check(
        "transaction extension is finite",
        "VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS = 8" in run_slice
        and "const uint32_t extendedWorkLimit" in run_slice
        and "static_cast<uint32_t>(budget.maxWorkUnits)" in run_slice
        and "VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS" in run_slice,
    )
    loop = run_slice[run_slice.index(loop_marker):]
    check("slice loop is bounded by extended work limit", loop.startswith(loop_marker))
    check("slice loop invokes legacy Step once", loop.count("Step();") == 1)
    check("each attempted Step consumes one work unit", "++workUnits;" in loop)
    check("slice does not contain nested unbounded while", loop.count("while (") == 1)
    check("pre-existing VM fault returns Fault", run_slice.find("VMRunSliceStopReason::Fault") < run_slice.find(loop_marker))
    check("post-Step VM fault returns Fault", loop.count("VMRunSliceStopReason::Fault") >= 1)
    check("Wait pending returns Waiting", "VMPendingOperation::Wait" in loop and "VMRunSliceStopReason::Waiting" in loop)
    check("timed buzzer pending returns Waiting", "VMPendingOperation::Mp3Play" in loop and "VMRunSliceStopReason::Waiting" in loop)
    check("other pending operation returns Yielded", "mPendingOperation != VMPendingOperation::None" in loop and "VMRunSliceStopReason::Yielded" in loop)
    check("non-running state distinguishes Halted", "VMRunSliceStopReason::Halted" in run_slice)
    check("non-running state distinguishes Stopped", "VMRunSliceStopReason::Stopped" in run_slice)
    check("budget exhaustion is final fallthrough", re.search(r"return finalize\(makeResult\(VMRunSliceStopReason::BudgetExhausted,[\s\S]*?\)\);\s*\n\}", run_slice) is not None)
    check("RunSlice captures executed PC before Step", "const uint16_t executedPc = mContext.mProgramCounter;" in loop)
    check("normal direct jump-to-end maps to Halted", "case Opcode::Jump:" in loop and "executed.p2 == programEnd" in loop)
    check("normal conditional jump-to-end maps to Halted", "case Opcode::JumpIfFalse:" in loop and "case Opcode::JumpIfTrue:" in loop)
    check("RunSlice preserves legacy jump PC rather than rewriting it", "mContext.mProgramCounter = programEnd" not in run_slice)

    check("generic pending state type exists", "class VMPendingState" in pending)
    check("pending lifecycle is explicit", "enum class VMPendingLifecycle" in pending and "Idle" in pending and "Pending" in pending)
    check("pending state records owner PC", "mOwnerProgramCounter" in pending and "OwnerProgramCounter()" in pending)
    check("pending state records generation", "mGeneration" in pending and "Generation()" in pending)
    check("same operation/owner resumes without new generation", "mOperation == operation" in pending and "mOwnerProgramCounter == ownerProgramCounter" in pending and "return false;" in pending)
    check("new logical pending operation increments generation", "++mGeneration;" in pending)
    check("legacy direct assignment captures live PC", "operator=(VMPendingOperation operation)" in pending and "*mProgramCounter" in pending)
    check("context binds pending owner to program counter", "BindProgramCounter(&mProgramCounter)" in context)
    check("context exposes owner invariant", "PendingOperationOwnedByCurrentPc()" in context)
    check("normal clear returns lifecycle to Idle", "mPendingOperation.Clear();" in context)
    check("hard reset starts a fresh pending epoch", "mPendingOperation.HardReset();" in context)
    check("deadline helper is wrap-safe", "static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0" in context)

    wait_case = legacy[legacy.index("case Opcode::Wait:"):legacy.index("case Opcode::CompareEQ:")]
    check("Wait starts one pending generation", "mPendingOperation = VMPendingOperation::Wait;" in wait_case)
    check("Wait stores monotonic deadline", "mPendingDeadlineMs = millis() +" in wait_case)
    check("Wait uses shared wrap-safe deadline helper", "IsPendingDeadlineReached(millis())" in wait_case)
    check("Wait does not call blocking RobotAPI Wait", "RobotAPI::Wait" not in wait_case and "delay(" not in wait_case)
    check("Wait advances PC only after completion", wait_case.index("ClearPendingOperation();") < wait_case.rindex("mProgramCounter++;"))

    mp3_case = legacy[legacy.index("case Opcode::SetMp3Play:"):legacy.index("case Opcode::GetTraceValue:")]
    check("Mp3Play has explicit pending kind", "Mp3Play" in pending)
    check("Mp3Play starts nonblocking RobotAPI primitive", "BeginMp3PlayCooperative" in mp3_case)
    check("Mp3Play stores returned duration as deadline", "mPendingDeadlineMs = millis() + durationMs;" in mp3_case)
    check("Mp3Play resumes through shared deadline helper", "IsPendingDeadlineReached(millis())" in mp3_case)
    check("Mp3Play finalizes once before PC advance", mp3_case.index("EndMp3PlayCooperative();") < mp3_case.index("ClearPendingOperation();") < mp3_case.rindex("mProgramCounter++;"))
    check("VM no longer calls blocking SetMp3Play", "RobotAPI::SetMp3Play(" not in mp3_case)
    check("cooperative buzzer primitive is declared", "BeginMp3PlayCooperative" in robot_h and "EndMp3PlayCooperative" in robot_h)
    check("cooperative buzzer primitive contains no delay", "delay(" not in robot_coop)
    check("cooperative buzzer keeps legacy logical duration", "kMp3PlayDurationMs = 200" in robot_coop and "delay(200);" in robot_cpp)

    check("VM has centralized pending cancellation", "void VM::CancelPendingOperation(bool stopLineMotors)" in legacy)
    cancel_body = legacy[legacy.index("void VM::CancelPendingOperation"):legacy.index("void VM::Reset()")]
    check("pending buzzer is forced off on cancellation", "EndMp3PlayCooperative();" in cancel_body)
    check("cancellation clears pending ownership", "ClearPendingOperation();" in cancel_body)
    check("manual stop uses centralized cleanup", "CancelPendingOperation(true);" in step_body)
    check("fault cleanup uses centralized cleanup", step_body.count("CancelPendingOperation(true);") >= 2)
    check("Reset and Start cancel pending work", "void VM::Reset() {\n    CancelPendingOperation(true);" in legacy and "void VM::Start() {\n    CancelPendingOperation(true);" in legacy)
    check("Line operations still use shared Line pending kind", legacy.count("mPendingOperation = VMPendingOperation::Line;") >= 4)
    check("line pending completion still clears before PC advance", "mContext.ClearPendingOperation();\n        mContext.mProgramCounter++;" in legacy)

    # VM-RT F / S1-S5: one shared physical sample set per RunSlice control cycle.
    check("snapshot model exposes L/C/R values", all(token in snapshot_h for token in ("bool left;", "bool center;", "bool right;")))
    check("snapshot exposes timestamp sequence and validity", all(token in snapshot_h for token in ("timestampUs", "sequence", "valid")))
    check("snapshot exposes physical-read and consumer diagnostics", "physicalReadCount" in snapshot_h and "consumerCount" in snapshot_h and "invalidCount" in snapshot_h)
    check("RunSlice owns one explicit snapshot cycle", "LineSnapshotCycleGuard lineSnapshotCycle;" in run_slice and "BeginCycle()" in run_slice and "EndCycle()" in run_slice)
    check("snapshot sampling is lazy", "EnsureSample()" in snapshot_h and run_slice.index("LineSnapshotCycleGuard lineSnapshotCycle;") < run_slice.index(loop_marker))

    fixed_sample_start = snapshot_cpp.index("void sampleFixedRateOnce()")
    fixed_sample_end = snapshot_cpp.index("void fixedRateTask", fixed_sample_start)
    fixed_sample_body = snapshot_cpp[fixed_sample_start:fixed_sample_end]
    ensure_sample_start = snapshot_cpp.index("bool EnsureSample()")
    ensure_sample_end = snapshot_cpp.index("void RecordConsumer()", ensure_sample_start)
    ensure_sample_body = snapshot_cpp[ensure_sample_start:ensure_sample_end]
    check(
        "firmware-owned sample reads all three physical channels",
        all(f"{name}->SampleHardwareDirect();" in ensure_sample_body for name in ("left", "center", "right"))
        and "g_snapshot.physicalReadCount = 3;" in ensure_sample_body,
    )
    check(
        "fixed-rate producer uses three read-only hardware reads",
        all(f"next.{field} = g_fixed{name}->ReadHardwareDetectedDirect();" in fixed_sample_body for field, name in (("left", "Left"), ("center", "Center"), ("right", "Right")))
        and "SampleHardwareDirect();" not in fixed_sample_body
        and "ApplySnapshotReading(" not in fixed_sample_body
        and "g_snapshot.physicalReadCount = 0;" in ensure_sample_body,
    )
    check("TCRT exposes read-only producer primitive", "ReadHardwareDetectedDirect() const" in tcrt_h and "TCRT5000::ReadHardwareDetectedDirect() const" in tcrt_cpp)
    check("same-cycle repeated consumers reuse sampled set", "if (g_sampledThisCycle)" in snapshot_cpp and "return g_snapshot.valid;" in snapshot_cpp)
    check("next cycle can produce a new sequence", "++g_snapshot.sequence;" in snapshot_cpp and "g_sampledThisCycle = false;" in snapshot_cpp)
    check("invalid snapshot is atomic", "applyInvalidFallback" in snapshot_cpp and "g_snapshot.mask = 0;" in snapshot_cpp and "g_snapshot.valid = false;" in snapshot_cpp)
    check("existing TCRT update delegates to snapshot owner in cycle", "LineSensorSnapshot::EnsureSample();" in tcrt_cpp and "LineSensorSnapshot::RecordConsumer();" in tcrt_cpp)
    check("outside snapshot cycle TCRT keeps direct-read compatibility", "SampleHardwareDirect();" in tcrt_cpp and "if (LineSensorSnapshot::IsCycleActive())" in tcrt_cpp)
    check("threshold semantics remain in TCRT driver", "_lastReading == _threshold" in tcrt_cpp and "setThreshold" in tcrt_h)
    check("snapshot contract forbids getter-owned refresh", "Individual VM getters do not own physical sampling" in snapshot_spec)

    # VM-RT H: measurable responsiveness evidence without changing dispatch.
    for field in (
        "sliceDurationUs", "maxWorkUnitDurationUs", "maxWorkUnitProgramCounter",
        "pendingOperation", "pendingLifecycle", "pendingOwnerProgramCounter",
        "pendingGeneration", "pendingOpcode", "pendingOpcodeValid",
        "lineSnapshotSequence", "lineSnapshotAgeUs", "lineSnapshotPhysicalReadCount",
        "lineSnapshotConsumerCount", "lineSnapshotInvalidCount", "lineSnapshotValid",
    ):
        check(f"RunSlice result exposes {field}", field in header)

    check("slice timing uses monotonic micros", "const uint32_t sliceStartUs = micros();" in run_slice and "result.sliceDurationUs = nowUs - sliceStartUs;" in run_slice)
    work_start_pos = loop.index("const uint32_t workStartUs = micros();")
    step_pos = loop.index("Step();", work_start_pos)
    work_end_pos = loop.index("const uint32_t workEndUs = micros();", step_pos)
    work_duration_pos = loop.index("const uint32_t workDurationUs = workEndUs - workStartUs;", work_end_pos)
    check("work-unit timing surrounds legacy Step", work_start_pos < step_pos < work_end_pos < work_duration_pos)
    check("slowest work unit retains owning PC", "maxWorkUnitProgramCounter = executedPc;" in loop)
    check("pending operation evidence uses generic state", "mPendingOperation.Operation()" in run_slice and "mPendingOperation.Lifecycle()" in run_slice)
    check("pending opcode is resolved from owner PC", "mProgram->mInstructions[result.pendingOwnerProgramCounter].opcode" in run_slice)
    check("snapshot age uses shared snapshot timestamp", "nowUs - snapshot.timestampUs" in run_slice)
    check("instrumentation does not add Step calls", loop.count("Step();") == 1)
    check("telemetry aggregate stores latest slice", "VMRunSliceResult lastSlice;" in telemetry_h and "g_snapshot.lastSlice = result;" in telemetry_cpp)
    check("telemetry tracks max slice duration", "maxSliceDurationUs" in telemetry_h and "result.sliceDurationUs > g_snapshot.maxSliceDurationUs" in telemetry_cpp)
    check("telemetry tracks slowest indivisible work unit", "maxWorkUnitDurationUs" in telemetry_h and "maxWorkUnitProgramCounter" in telemetry_h)
    check("stop latency evidence has last and max", "lastStopLatencyUs" in telemetry_h and "maxStopLatencyUs" in telemetry_h and "RecordStopLatency" in telemetry_cpp)
    check(
        "firmware measures bounded background stop window",
        "vmRunningBeforeBackground" in firmware
        and "backgroundStartUs" in firmware
        and "VMRuntimeTelemetry::RecordStopLatency(micros() - backgroundStartUs);" in firmware,
    )
    check("firmware records every executed VM slice", "VMRuntimeTelemetry::RecordSlice(sliceResult);" in firmware)
    check("JSONL evidence is opt-in", "#define VM_RESPONSIVENESS_DIAGNOSTICS 0" in telemetry_h and "#if VM_RESPONSIVENESS_DIAGNOSTICS" in telemetry_cpp)
    check("JSONL evidence has stable type marker", "\\\"type\\\":\\\"vm_rt\\\"" in telemetry_cpp)
    check("instrumentation spec documents host/physical evidence", "JSONL" in instrumentation_spec and "physical qualification" in instrumentation_spec.lower())

    lower_header = header.lower()
    check("API documents cooperative non-preemptive boundary", "not preemption" in lower_header)
    check("API documents remaining synchronous RobotAPI risk", "synchronous robotapi call" in lower_header)
    check("spec keeps wall-clock secondary to deterministic budget", "Wall-clock time alone should not be the only semantic budget" in spec)

    print("VM RunSlice + pending + snapshot + responsiveness instrumentation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
