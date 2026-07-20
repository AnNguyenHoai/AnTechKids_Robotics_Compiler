/******************************************************************************
 * File        : VM.h
 *
 * Description :
 *      Robot Virtual Machine.
 *
 ******************************************************************************/

#pragma once

#include "Program.h"
#include "VMContext.h"

/******************************************************************************
 * Robot VM
 ******************************************************************************/

class VM
{
public:

    /**
     * Constructor.
     */
    VM();

    /**
     * Reset VM runtime.
     */
    void Reset();

    /**
     * Load program.
     */
    bool LoadProgram(const Program* program);

    /**
     * Execute one instruction.
     */
    void Step();

    /**
     * Check whether VM is still running.
     */
    bool IsRunning() const;

    /**
     * Get current program counter.
     */
    uint16_t GetProgramCounter() const;

private:

    /**
     * Execute current instruction.
     */
    void ExecuteInstruction(const Instruction& instruction);

private:

    /**
     * Loaded Program.
     */
    const Program* mProgram;

    /**
     * Runtime Context.
     */
    VMContext mContext;
};