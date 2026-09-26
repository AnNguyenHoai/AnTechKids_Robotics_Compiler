#include "VM.h"
#include "VMRuntimeTelemetry.h"
#include "../../Sensor/LineSensorSnapshot.h"
#include <Arduino.h>

#ifndef VM_RESPONSIVENESS_DIAGNOSTICS
#define VM_RESPONSIVENESS_DIAGNOSTICS 0
#endif

namespace {
static constexpr uint16_t VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS = 8;

VMRunSliceResult makeResult(VMRunSliceStopReason reason,
                            uint16_t workUnits,
                            uint16_t startPc,
                            uint16_t endPc)
{
    VMRunSliceResult result{};
    result.reason = reason;
    result.workUnits = workUnits;
    result.startProgramCounter = startPc;
    result.endProgramCounter = endPc;
    return result;
}

bool isTakenBackEdge(const Program* program,
                     const VMContext& context,
                     uint16_t executedPc)
{
    if (program == nullptr || executedPc >= program->mInstructionCount) {
        return false;
    }

    const Instruction& executed = program->mInstructions[executedPc];
    switch (executed.opcode) {
        case Opcode::Jump:
            return executed.p2 <= executedPc;
        case Opcode::JumpIfFalse:
            return (context.mVariables[executed.p1] == 0) &&
                   (executed.p2 <= executedPc);
        case Opcode::JumpIfTrue:
            return (context.mVariables[executed.p1] != 0) &&
                   (executed.p2 <= executedPc);
        default:
            return false;
    }
}

class LineSnapshotCycleGuard
{
public:
    LineSnapshotCycleGuard()
        : mOwnsCycle(!LineSensorSnapshot::IsCycleActive())
    {
        if (mOwnsCycle) {
            LineSensorSnapshot::BeginCycle();
        }
    }

    ~LineSnapshotCycleGuard()
    {
        if (mOwnsCycle) {
            LineSensorSnapshot::EndCycle();
        }
    }

private:
    bool mOwnsCycle;
};
}

VMRunSliceResult VM::RunSlice(const VMRunSliceBudget& budget)
{
    const uint32_t sliceStartUs = micros();
    const uint16_t startPc = mContext.mProgramCounter;
    uint16_t workUnits = 0;
    uint32_t maxWorkUnitDurationUs = 0;
    uint16_t maxWorkUnitProgramCounter = startPc;

    auto finalize = [&](VMRunSliceResult result) -> VMRunSliceResult {
        const uint32_t nowUs = micros();
        result.sliceDurationUs = nowUs - sliceStartUs;
        result.maxWorkUnitDurationUs = maxWorkUnitDurationUs;
        result.maxWorkUnitProgramCounter = maxWorkUnitProgramCounter;

        result.pendingOperation = static_cast<uint8_t>(mContext.mPendingOperation.Operation());
        result.pendingLifecycle = static_cast<uint8_t>(mContext.mPendingOperation.Lifecycle());
        result.pendingOwnerProgramCounter = mContext.PendingOwnerProgramCounter();
        result.pendingGeneration = mContext.PendingGeneration();
        result.pendingOpcode = 0;
        result.pendingOpcodeValid = false;

        if (mContext.HasPendingOperation() && mProgram != nullptr &&
            result.pendingOwnerProgramCounter < mProgram->mInstructionCount) {
            result.pendingOpcode = static_cast<uint8_t>(
                mProgram->mInstructions[result.pendingOwnerProgramCounter].opcode);
            result.pendingOpcodeValid = true;
        }

        const auto& snapshot = LineSensorSnapshot::Current();
        result.lineSnapshotSequence = snapshot.sequence;
        result.lineSnapshotPhysicalReadCount = snapshot.physicalReadCount;
        result.lineSnapshotConsumerCount = snapshot.consumerCount;
        result.lineSnapshotInvalidCount = snapshot.invalidCount;
        result.lineSnapshotValid = snapshot.valid;
        result.lineSnapshotAgeUs = snapshot.valid ? (nowUs - snapshot.timestampUs) : 0;
        return result;
    };

    if (mContext.mErrorCode != ToErrorCode(VMErrorCode::None)) {
        return finalize(makeResult(VMRunSliceStopReason::Fault,
                                   workUnits,
                                   startPc,
                                   mContext.mProgramCounter));
    }

    if (!IsRunning()) {
        const bool halted = (mProgram != nullptr) &&
                            (mContext.mProgramCounter >= mProgram->mInstructionCount);
        return finalize(makeResult(halted ? VMRunSliceStopReason::Halted
                                          : VMRunSliceStopReason::Stopped,
                                   workUnits,
                                   startPc,
                                   mContext.mProgramCounter));
    }

    if (budget.maxWorkUnits == 0) {
        return finalize(makeResult(VMRunSliceStopReason::BudgetExhausted,
                                   workUnits,
                                   startPc,
                                   mContext.mProgramCounter));
    }

    // Production firmware can own a broader line-snapshot cycle spanning
    // SensorManager -> VM -> Diagnostics. Standalone RunSlice callers still
    // receive the historical one-slice snapshot lifecycle through this guard.
    LineSnapshotCycleGuard lineSnapshotCycle;

    const uint32_t extendedWorkLimit =
        static_cast<uint32_t>(budget.maxWorkUnits) +
        static_cast<uint32_t>(VM_REACTIVE_TRANSACTION_MAX_EXTRA_WORK_UNITS);

    while (static_cast<uint32_t>(workUnits) < extendedWorkLimit) {
        const uint16_t executedPc = mContext.mProgramCounter;
#if VM_RESPONSIVENESS_DIAGNOSTICS
        const Instruction* executedInstruction =
            (mProgram != nullptr && executedPc < mProgram->mInstructionCount)
                ? &mProgram->mInstructions[executedPc]
                : nullptr;
        const uint32_t workStartUs = micros();
#endif

        Step();
        ++workUnits;

#if VM_RESPONSIVENESS_DIAGNOSTICS
        // Detailed per-opcode timing is qualification/debug evidence only.
        // Production still enforces the independent slice wall-clock ceiling,
        // but avoids paying an extra timestamp before every legacy Step().
        const uint32_t workEndUs = micros();
        const uint32_t workDurationUs = workEndUs - workStartUs;
        if (workDurationUs > maxWorkUnitDurationUs) {
            maxWorkUnitDurationUs = workDurationUs;
            maxWorkUnitProgramCounter = executedPc;
        }

        // Capture the real reactive chain without UART observer effect. These
        // opcode-level markers are diagnostic evidence, not scheduler semantics.
        if (executedInstruction != nullptr) {
            if (executedInstruction->opcode == Opcode::GetTraceState) {
                const auto& snapshot = LineSensorSnapshot::Current();
                const bool detected =
                    mContext.mVariables[executedInstruction->p3] != 0;
                VMRuntimeTelemetry::RecordReactiveLineObservation(
                    snapshot.valid ? snapshot.timestampUs : 0u,
                    workEndUs,
                    snapshot.sequence,
                    detected);
            } else if (executedInstruction->opcode == Opcode::Stop) {
                VMRuntimeTelemetry::RecordReactiveStop(workEndUs);
            }
        }
#endif

        if (mContext.mErrorCode != ToErrorCode(VMErrorCode::None)) {
            return finalize(makeResult(VMRunSliceStopReason::Fault,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }

        if (!IsRunning()) {
            bool halted = (mProgram != nullptr) &&
                          (mContext.mProgramCounter >= mProgram->mInstructionCount);

            if (!halted && mProgram != nullptr &&
                executedPc < mProgram->mInstructionCount) {
                const Instruction& executed = mProgram->mInstructions[executedPc];
                const uint16_t programEnd = mProgram->mInstructionCount;

                switch (executed.opcode) {
                    case Opcode::Jump:
                        halted = executed.p2 == programEnd;
                        break;
                    case Opcode::JumpIfFalse:
                        halted = (mContext.mVariables[executed.p1] == 0) &&
                                 (executed.p2 == programEnd);
                        break;
                    case Opcode::JumpIfTrue:
                        halted = (mContext.mVariables[executed.p1] != 0) &&
                                 (executed.p2 == programEnd);
                        break;
                    default:
                        break;
                }
            }

            return finalize(makeResult(halted ? VMRunSliceStopReason::Halted
                                              : VMRunSliceStopReason::Stopped,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }

        if (mContext.mPendingOperation == VMPendingOperation::Wait ||
            mContext.mPendingOperation == VMPendingOperation::Mp3Play) {
            return finalize(makeResult(VMRunSliceStopReason::Waiting,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }

        if (mContext.mPendingOperation != VMPendingOperation::None) {
            return finalize(makeResult(VMRunSliceStopReason::Yielded,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }

        // The wall-clock ceiling is always a hard return boundary, including
        // while the scheduler is consuming bounded transaction headroom.
        if (budget.maxDurationUs != 0 &&
            static_cast<uint32_t>(micros() - sliceStartUs) >= budget.maxDurationUs) {
            return finalize(makeResult(VMRunSliceStopReason::TimeBudgetExhausted,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }

        if (workUnits >= budget.maxWorkUnits) {
            // #383: the work-unit ceiling is a soft boundary only for a short,
            // bounded control-flow transaction. Once the soft budget is reached,
            // prefer returning immediately after a taken loop back-edge so one
            // source-level iteration is not split solely by work count. This is
            // generic control-flow logic: it does not inspect sensor or actuator
            // opcodes. The extra work remains strictly bounded by the constant
            // above, and pending/stop/fault/time boundaries still win first.
            if (isTakenBackEdge(mProgram, mContext, executedPc)) {
                return finalize(makeResult(VMRunSliceStopReason::BudgetExhausted,
                                           workUnits,
                                           startPc,
                                           mContext.mProgramCounter));
            }
        }
    }

    return finalize(makeResult(VMRunSliceStopReason::BudgetExhausted,
                               workUnits,
                               startPc,
                               mContext.mProgramCounter));
}
