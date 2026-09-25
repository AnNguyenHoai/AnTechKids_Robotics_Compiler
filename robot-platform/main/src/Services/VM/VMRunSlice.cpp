#include "VM.h"

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

    while (workUnits < budget.maxWorkUnits) {
        Step();
        ++workUnits;

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

        if (mContext.mPendingOperation == VMPendingOperation::Wait) {
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
