#pragma once

#include <stdint.h>

// Logical operation currently owning cooperative VM execution.
enum class VMPendingOperation : uint8_t
{
    None = 0,
    Wait,
    Line,
};

// Stored lifecycle is intentionally minimal: completion, reset, stop and fault
// all leave the VM in Idle. The transition reason remains a VM/call-site concern.
enum class VMPendingLifecycle : uint8_t
{
    Idle = 0,
    Pending,
};

// Generic pending-instruction state shared by all cooperative VM operations.
//
// Existing dispatch code assigns VMPendingOperation directly. The assignment
// operator preserves that source compatibility while capturing the owning PC on
// the first transition into Pending. Re-assigning the same operation at the same
// PC is treated as resume, not as a new initialization, so the generation does
// not change and one-time initialization is not replayed by the state layer.
class VMPendingState
{
public:
    VMPendingState()
        : mProgramCounter(nullptr),
          mOperation(VMPendingOperation::None),
          mLifecycle(VMPendingLifecycle::Idle),
          mOwnerProgramCounter(0),
          mGeneration(0)
    {
    }

    void BindProgramCounter(const uint16_t* programCounter)
    {
        mProgramCounter = programCounter;
    }

    void Reset()
    {
        mOperation = VMPendingOperation::None;
        mLifecycle = VMPendingLifecycle::Idle;
        mOwnerProgramCounter = 0;
    }

    bool Begin(VMPendingOperation operation, uint16_t ownerProgramCounter)
    {
        if (operation == VMPendingOperation::None) {
            Reset();
            return false;
        }

        if (mLifecycle == VMPendingLifecycle::Pending &&
            mOperation == operation &&
            mOwnerProgramCounter == ownerProgramCounter) {
            return false;
        }

        mOperation = operation;
        mLifecycle = VMPendingLifecycle::Pending;
        mOwnerProgramCounter = ownerProgramCounter;
        ++mGeneration;
        return true;
    }

    VMPendingState& operator=(VMPendingOperation operation)
    {
        if (operation == VMPendingOperation::None) {
            Reset();
        } else {
            const uint16_t owner = (mProgramCounter != nullptr)
                                       ? *mProgramCounter
                                       : 0;
            Begin(operation, owner);
        }
        return *this;
    }

    bool operator==(VMPendingOperation operation) const
    {
        return mOperation == operation;
    }

    bool operator!=(VMPendingOperation operation) const
    {
        return mOperation != operation;
    }

    VMPendingOperation Operation() const
    {
        return mOperation;
    }

    VMPendingLifecycle Lifecycle() const
    {
        return mLifecycle;
    }

    bool IsPending() const
    {
        return mLifecycle == VMPendingLifecycle::Pending;
    }

    bool IsOwnedBy(uint16_t programCounter) const
    {
        return IsPending() && mOwnerProgramCounter == programCounter;
    }

    uint16_t OwnerProgramCounter() const
    {
        return mOwnerProgramCounter;
    }

    uint32_t Generation() const
    {
        return mGeneration;
    }

private:
    const uint16_t* mProgramCounter;
    VMPendingOperation mOperation;
    VMPendingLifecycle mLifecycle;
    uint16_t mOwnerProgramCounter;
    uint32_t mGeneration;
};
