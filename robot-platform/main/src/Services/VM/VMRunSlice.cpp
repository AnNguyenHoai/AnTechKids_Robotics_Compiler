#include "VM.h"
#include "VMRuntimeTelemetry.h"
#include "../../Sensor/LineSensorSnapshot.h"
#include <Arduino.h>

namespace {
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

    while (workUnits < budget.maxWorkUnits) {
        const uint16_t executedPc = mContext.mProgramCounter;
        const Instruction* executedInstruction =
            (mProgram != nullptr && executedPc < mProgram->mInstructionCount)
                ? &mProgram->mInstructions[executedPc]
                : nullptr;
        const uint32_t workStartUs = micros();
        Step();
        const uint32_t workEndUs = micros();
        const uint32_t workDurationUs = workEndUs - workStartUs;
        ++workUnits;

        if (workDurationUs > maxWorkUnitDurationUs) {
            maxWorkUnitDurationUs = workDurationUs;
            maxWorkUnitProgramCounter = executedPc;
        }

        // Capture the real reactive chain without UART observer effect. The
        // line sample timestamp comes from the exact shared snapshot consumed
        // by GetTraceState; Stop is stamped only after its Step() returned, so
        // the value includes RobotAPI::Stop() and PWM submission time.
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

        if (mContext.mErrorCode != ToErrorCode(VMErrorCode::None)) {
            return finalize(makeResult(VMRunSliceStopReason::Fault,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }

        if (!IsRunning()) {
            bool halted = (mProgram != nullptr) &&
                          (mContext.mProgramCounter >= mProgram->mInstructionCount);

            // Legacy Step() treats a branch whose target is exactly the
            // instruction count as normal program completion, but it does not
            // rewrite the PC to that end value. Classify that legacy outcome as
            // Halted without changing Step() or its PC semantics.
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

        // Wall-clock is a second, independent guard. Work-unit count remains a
        // hard ceiling, while the time ceiling prevents a burst of individually
        // cheap opcodes from monopolizing the firmware cycle. Check only between
        // Step() calls so legacy Step() semantics stay untouched.
        if (budget.maxDurationUs != 0 &&
            static_cast<uint32_t>(micros() - sliceStartUs) >= budget.maxDurationUs) {
            return finalize(makeResult(VMRunSliceStopReason::TimeBudgetExhausted,
                                       workUnits,
                                       startPc,
                                       mContext.mProgramCounter));
        }
    }

    return finalize(makeResult(VMRunSliceStopReason::BudgetExhausted,
                               workUnits,
                               startPc,
                               mContext.mProgramCounter));
}
