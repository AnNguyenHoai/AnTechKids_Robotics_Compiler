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
 * Cooperative slice execution
 ******************************************************************************/

enum class VMRunSliceStopReason : uint8_t
{
    BudgetExhausted = 0,
    Yielded,
    Waiting,
    Halted,
    Stopped,
    Fault,
};

struct VMRunSliceBudget
{
    uint16_t maxWorkUnits;
};

struct VMRunSliceResult
{
    VMRunSliceStopReason reason;
    uint16_t workUnits;
    uint16_t startProgramCounter;
    uint16_t endProgramCounter;
};

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
     * Execute one bounded instruction/tick.
     *
     * Long-running instructions keep the program counter on the current
     * instruction and return immediately so the platform loop can service
     * network and control-plane work between ticks.
     */
    void Step();

    /**
     * Execute a deterministic, bounded amount of VM work.
     *
     * One work unit is at most one legacy Step() invocation. RunSlice never
     * changes Step() semantics and stops early when the VM yields/waits,
     * halts, is stopped, or faults.
     *
     * Important: this is a cooperative boundary, not preemption. A single
     * synchronous RobotAPI call executed by Step() can still consume more
     * wall-clock time than the slice target until later VM-RT work converts
     * or bounds that operation.
     */
    VMRunSliceResult RunSlice(const VMRunSliceBudget& budget);

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

    /**
     * Advance one pending cooperative line tick.
     * Returns true when the current instruction was already pending and was
     * therefore handled by this call.
     */
    bool ContinuePendingLineOperation();

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
