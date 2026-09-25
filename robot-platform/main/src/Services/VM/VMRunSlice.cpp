#include "VM.h"
#include "../../Sensor/LineSensorSnapshot.h"

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
    LineSnapshotCycleGuard() { LineSensorSnapshot::BeginCycle(); }
    ~LineSnapshotCycleGuard() { LineSensorSnapshot::EndCycle(); }
};
}

VMRunSliceResult VM::RunSlice(const VMRunSliceBudget& budget)
{
    const uint16_t startPc = mContext.mProgramCounter;
    uint16_t workUnits = 0;

    if (mContext.mErrorCode != ToErrorCode(VMErrorCode::None)) {
        return makeResult(VMRunSliceStopReason::Fault,
                          workUnits,
                          startPc,
                          mContext.mProgramCounter);
    }

    if (!IsRunning()) {
        const bool halted = (mProgram != nullptr) &&
                            (mContext.mProgramCounter >= mProgram->mInstructionCount);
        return makeResult(halted ? VMRunSliceStopReason::Halted
                                 : VMRunSliceStopReason::Stopped,
                          workUnits,
                          startPc,
                          mContext.mProgramCounter);
    }

    if (budget.maxWorkUnits == 0) {
        return makeResult(VMRunSliceStopReason::BudgetExhausted,
                          workUnits,
                          startPc,
                          mContext.mProgramCounter);
    }

    // One RunSlice invocation is one VM/control-cycle snapshot scope. Sampling
    // itself is lazy: if no line consumer executes, no line hardware is read.
    LineSnapshotCycleGuard lineSnapshotCycle;

    while (workUnits < budget.maxWorkUnits) {
        const uint16_t executedPc = mContext.mProgramCounter;
        Step();
        ++workUnits;

        if (mContext.mErrorCode != ToErrorCode(VMErrorCode::None)) {
            return makeResult(VMRunSliceStopReason::Fault,
                              workUnits,
                              startPc,
                              mContext.mProgramCounter);
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

            return makeResult(halted ? VMRunSliceStopReason::Halted
                                     : VMRunSliceStopReason::Stopped,
                              workUnits,
                              startPc,
                              mContext.mProgramCounter);
        }

        if (mContext.mPendingOperation == VMPendingOperation::Wait ||
            mContext.mPendingOperation == VMPendingOperation::Mp3Play) {
            return makeResult(VMRunSliceStopReason::Waiting,
                              workUnits,
                              startPc,
                              mContext.mProgramCounter);
        }

        if (mContext.mPendingOperation != VMPendingOperation::None) {
            return makeResult(VMRunSliceStopReason::Yielded,
                              workUnits,
                              startPc,
                              mContext.mProgramCounter);
        }
    }

    return makeResult(VMRunSliceStopReason::BudgetExhausted,
                      workUnits,
                      startPc,
                      mContext.mProgramCounter);
}
