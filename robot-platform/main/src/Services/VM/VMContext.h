/******************************************************************************
 * File        : VMContext.h
 *
 * Description :
 *      Robot Virtual Machine Runtime Context.
 *
 *      VMContext contains the complete runtime state of Robot VM.
 *
 ******************************************************************************/

#pragma once

#include <stdint.h>
#include <string.h>

#include "VMPendingState.h"

/*----------------------------------------------------------------------------
 * Configuration
 *---------------------------------------------------------------------------*/

constexpr uint8_t MAX_VARIABLE_COUNT = 32;
constexpr uint8_t MAX_LOOP_DEPTH = 8;
constexpr uint8_t MAX_CALL_STACK = 8;

/*----------------------------------------------------------------------------
 * Loop Frame
 *---------------------------------------------------------------------------*/

struct LoopFrame
{
    uint8_t variableId;
    uint16_t current;
    uint16_t count;
    uint16_t startPc;
};

/*----------------------------------------------------------------------------
 * VM Context
 *---------------------------------------------------------------------------*/

class VMContext
{
public:
    VMContext()
    {
        // Pending-state ownership is tied to the live program counter. Existing
        // opcode code can keep assigning VMPendingOperation directly while the
        // state layer captures the owning instruction deterministically.
        mPendingOperation.BindProgramCounter(&mProgramCounter);
        Reset();
    }

    void Reset()
    {
        memset(mVariables, 0, sizeof(mVariables));
        mRegister0 = 0;
        mFlag = false;
        mProgramCounter = 0;
        mRunning = true;
        mLoopStackPointer = 0;
        mCallStackPointer = 0;
        mFramePointer = 0;
        mReturnAddress = 0;
        mErrorCode = 0;
        ClearPendingOperation();
    }

    void ClearPendingOperation()
    {
        mPendingOperation.Reset();
        mPendingDeadlineMs = 0;
    }

    bool BeginPendingOperation(VMPendingOperation operation)
    {
        return mPendingOperation.Begin(operation, mProgramCounter);
    }

    bool HasPendingOperation() const
    {
        return mPendingOperation.IsPending();
    }

    bool PendingOperationOwnedByCurrentPc() const
    {
        return mPendingOperation.IsOwnedBy(mProgramCounter);
    }

    uint16_t PendingOwnerProgramCounter() const
    {
        return mPendingOperation.OwnerProgramCounter();
    }

    uint32_t PendingGeneration() const
    {
        return mPendingOperation.Generation();
    }

    bool IsPendingDeadlineReached(uint32_t nowMs) const
    {
        if (mPendingOperation != VMPendingOperation::Wait) {
            return false;
        }

        // Signed subtraction gives wrap-safe elapsed/deadline comparison for
        // the uint32_t monotonic millisecond clock used by Arduino millis().
        return static_cast<int32_t>(nowMs - mPendingDeadlineMs) >= 0;
    }

public:
    int32_t mVariables[MAX_VARIABLE_COUNT];
    int16_t mRegister0;
    bool mFlag;
    uint16_t mProgramCounter;
    bool mRunning;

    // Generic cooperative execution state. While an operation is pending, its
    // owner PC remains stable and the VM returns control after bounded work.
    VMPendingState mPendingOperation;
    uint32_t mPendingDeadlineMs;

    // Loop stack (for break/continue)
    LoopFrame mLoopStack[MAX_LOOP_DEPTH];
    uint8_t mLoopStackPointer;

    // --- Call Stack (placeholder for future function calls) ---
    uint16_t mCallStack[MAX_CALL_STACK];   // return addresses
    uint8_t mCallStackPointer;
    uint16_t mFramePointer;                // current frame pointer
    uint16_t mReturnAddress;               // temporary return address
    uint8_t mErrorCode;                    // 0 = no error, >0 = error code
};
