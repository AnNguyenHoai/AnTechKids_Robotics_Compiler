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
     * Remove all instructions.
     */
    void Clear()
    {
        mInstructionCount = 0;
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
            return false;
        }

        mInstructions[mInstructionCount++] = instruction;

        return true;
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
};