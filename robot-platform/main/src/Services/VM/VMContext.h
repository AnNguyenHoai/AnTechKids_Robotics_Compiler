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

/*----------------------------------------------------------------------------
 * Loop Frame
 *---------------------------------------------------------------------------*/

/**
 * FOR loop runtime information.
 */
struct LoopFrame
{
    /**
     * Loop variable ID.
     */
    uint8_t variableId;

    /**
     * Current iteration.
     */
    uint16_t current;

    /**
     * Total loop count.
     */
    uint16_t count;

    /**
     * Instruction index after FOR_BEGIN.
     */
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

    /**
     * Reset VM runtime state.
     */
    void Reset()
    {
        memset(mVariables, 0, sizeof(mVariables));

        mRegister0 = 0;

        mFlag = false;

        mProgramCounter = 0;

        mRunning = true;

        mLoopStackPointer = 0;
    }

public:

    /**
     * VM Variables.
     */
    int16_t mVariables[MAX_VARIABLE_COUNT];

    /**
     * General purpose register.
     */
    int16_t mRegister0;

    /**
     * Compare result.
     */
    bool mFlag;

    /**
     * Current instruction index.
     */
    uint16_t mProgramCounter;

    /**
     * VM running state.
     */
    bool mRunning;

    /**
     * Loop stack.
     */
    LoopFrame mLoopStack[MAX_LOOP_DEPTH];

    /**
     * Stack pointer.
     */
    uint8_t mLoopStackPointer;
};