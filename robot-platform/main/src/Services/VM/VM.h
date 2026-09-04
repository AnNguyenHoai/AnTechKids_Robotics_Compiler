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
#include "VMErrorContract.h"

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
     * Reset VM runtime context.
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

    /**
     * Get canonical error code (0 = no error).
     */
    uint8_t GetErrorCode() const;

    /**
     * Get canonical error identifier for diagnostics.
     */
    const char* GetErrorId() const;

    /**
     * Get canonical error message for diagnostics.
     */
    const char* GetErrorMessage() const;

    // ---- DIAGNOSTIC: manual control ----
    /**
     * Set running state (diagnostic use only).
     */
    void SetRunning(bool running);

    /**
     * Start execution from PC=0 (diagnostic use only).
     */
    void Start();

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