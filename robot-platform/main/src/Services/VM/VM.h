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
    // Appended to preserve the numeric values of the existing diagnostic
    // reasons. This is a scheduler-only result, not a bytecode/opcode change.
    TimeBudgetExhausted,
};

struct VMRunSliceBudget
{
    // Hard semantic work ceiling. Keep the original declaration unchanged so
    // existing source/contract checks remain valid.
    uint16_t maxWorkUnits;

    // Optional wall-clock ceiling for one cooperative slice. Keep this struct a
    // plain C++11 aggregate: VMRunSliceBudget{4} zero-initializes this trailing
    // field, while production can use VMRunSliceBudget{16, 2000}.
    uint32_t maxDurationUs;
};

struct VMRunSliceResult
{
    VMRunSliceStopReason reason;
    uint16_t workUnits;
    uint16_t startProgramCounter;
    uint16_t endProgramCounter;

    // VM-RT H diagnostic evidence. These are observations only; they do not
    // participate in VM scheduling or alter legacy Step() semantics.
    uint32_t sliceDurationUs;
    uint32_t maxWorkUnitDurationUs;
    uint16_t maxWorkUnitProgramCounter;

    uint8_t pendingOperation;
    uint8_t pendingLifecycle;
    uint16_t pendingOwnerProgramCounter;
    uint32_t pendingGeneration;
    uint8_t pendingOpcode;
    bool pendingOpcodeValid;

    uint32_t lineSnapshotSequence;
    uint32_t lineSnapshotAgeUs;
    uint32_t lineSnapshotPhysicalReadCount;
    uint32_t lineSnapshotConsumerCount;
    uint32_t lineSnapshotInvalidCount;
    bool lineSnapshotValid;
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
     * halts, is stopped, faults, or reaches an enabled wall-clock ceiling.
     *
     * Important: this is a cooperative boundary, not preemption. A single
     * synchronous RobotAPI call executed by Step() can still consume more
     * wall-clock time than the slice target and must be converted/bounded at
     * that operation's owner.
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

    /**
     * Cancel active cooperative work without treating cancellation as logical
     * instruction completion. Used by stop/reset/fault cleanup paths.
     */
    void CancelPendingOperation(bool stopLineMotors);

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
