/******************************************************************************
 * File        : Program.h
 *
 * Description :
 *      Robot VM Program Container.
 *
 *      A Program is simply a collection of VM Instructions.
 *
 ******************************************************************************/

#pragma once

#include <stdint.h>

#include "Instruction.h"
#include "VMErrorContract.h"

/*----------------------------------------------------------------------------
 * Configuration
 *---------------------------------------------------------------------------*/

constexpr uint16_t MAX_PROGRAM_SIZE = 128;

/*----------------------------------------------------------------------------
 * Program
 *---------------------------------------------------------------------------*/

class Program
{
public:

    Program()
    {
        Clear();
    }

    /**
     * Remove all instructions and clear load status.
     */
    void Clear()
    {
        mInstructionCount = 0;
        mErrorCode = ToErrorCode(VMErrorCode::None);
    }

    /**
     * Add instruction.
     *
     * @return true  Success
     * @return false Program Full
     */
    bool AddInstruction(const Instruction& instruction)
    {
        if (mInstructionCount >= MAX_PROGRAM_SIZE)
        {
            mErrorCode = ToErrorCode(VMErrorCode::ProgramOverflow);
            return false;
        }

        mInstructions[mInstructionCount++] = instruction;
        mErrorCode = ToErrorCode(VMErrorCode::None);

        return true;
    }

    /**
     * Get the canonical program/container error code.
     */
    uint8_t GetErrorCode() const
    {
        return mErrorCode;
    }

public:

    /**
     * Instruction List.
     *
     * VM reads directly from this array.
     */
    Instruction mInstructions[MAX_PROGRAM_SIZE];

    /**
     * Number of valid instructions.
     */
    uint16_t mInstructionCount;

private:
    /**
     * Canonical loader/container error code.
     */
    uint8_t mErrorCode;
};