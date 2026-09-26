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
    TimeBudgetExhausted,
};

struct VMRunSliceBudget
{
    constexpr VMRunSliceBudget(uint16_t workUnits = 0, uint32_t durationUs = 0)
        : maxWorkUnits(workUnits), maxDurationUs(durationUs) {}

    uint16_t maxWorkUnits;
    uint32_t maxDurationUs = 0;
};

struct VMRunSliceResult
{
    VMRunSliceStopReason reason;
    uint16_t workUnits;
    uint16_t startProgramCounter;
    uint16_t endProgramCounter;

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

    // #385 qualification observations for the independent line producer.
    uint32_t lineSnapshotIntervalUs;
    uint32_t lineSnapshotMaxJitterUs;
    uint32_t lineSnapshotStaleCount;
    bool lineSnapshotFixedRateActive;
};

/******************************************************************************
 * Robot VM
 ******************************************************************************/

class VM
{
public:
    VM();
    void Reset();
    bool LoadProgram(const Program* program);
    void Step();
    VMRunSliceResult RunSlice(const VMRunSliceBudget& budget);
    bool IsRunning() const;
    uint16_t GetProgramCounter() const;
    uint8_t GetErrorCode() const;
    const char* GetErrorId() const;
    const char* GetErrorMessage() const;
    void SetRunning(bool running);
    void Start();

private:
    void ExecuteInstruction(const Instruction& instruction);
    bool ContinuePendingLineOperation();
    void CancelPendingOperation(bool stopLineMotors);

private:
    const Program* mProgram;
    VMContext mContext;
};
