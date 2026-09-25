#pragma once

#include <stdint.h>

namespace LineSensorSnapshot {

struct Snapshot {
    bool left;
    bool center;
    bool right;
    uint8_t mask;
    uint32_t timestampUs;
    uint32_t sequence;
    uint32_t physicalReadCount;
    uint32_t consumerCount;
    uint32_t invalidCount;
    bool valid;
};

// Control-cycle ownership. BeginCycle/EndCycle do not sample by themselves;
// the first in-cycle line consumer triggers one atomic L/C/R sample set.
void BeginCycle();
void EndCycle();
void Invalidate();

bool IsCycleActive();
bool EnsureSample();
void RecordConsumer();

const Snapshot& Current();

} // namespace LineSensorSnapshot
