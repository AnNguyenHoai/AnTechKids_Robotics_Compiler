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

/*----------------------------------------------------------------------------
 * Configuration
 *---------------------------------------------------------------------------*/

constexpr uint8_t MAX_VARIABLE_COUNT = 32;
constexpr uint8_t MAX_LOOP_DEPTH = 8;
constexpr uint8_t MAX_CALL_STACK = 8;

/*----------------------------------------------------------------------------
 * Cooperative execution state
 *---------------------------------------------------------------------------*/

enum class VMPendingOperation : uint8_t
{
    None = 0,
    Wait,
    Line,
};

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
        mPendingOperation = VMPendingOperation::None;
        mPendingDeadlineMs = 0;
    }

public:
    int32_t mVariables[MAX_VARIABLE_COUNT];
    int16_t mRegister0;
    bool mFlag;
    uint16_t mProgramCounter;
    bool mRunning;

    // Cooperative execution state. While an operation is pending the VM keeps
    // the program counter on the current instruction and returns control to the
    // Arduino loop after every bounded Step().
    VMPendingOperation mPendingOperation;
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
