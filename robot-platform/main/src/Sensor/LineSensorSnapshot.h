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

    // #385 fixed-rate qualification evidence. These fields are observations;
    // consumers continue to use the same coherent L/C/R mask contract.
    uint32_t sampleIntervalUs;
    uint32_t maxSampleJitterUs;
    uint32_t staleCount;
    bool fixedRateActive;
};

// Control-cycle ownership. BeginCycle/EndCycle do not sample by themselves;
// the first in-cycle line consumer obtains one coherent L/C/R sample set.
void BeginCycle();
void EndCycle();
void Invalidate();

bool IsCycleActive();
bool EnsureSample();
void RecordConsumer();

// Qualification-only fixed-rate source. The producer task performs only the
// three digital line reads plus coherent publication; controller/PWM/logging
// remain outside the task. Existing production behavior remains unchanged
// unless StartFixedRateSampling() is explicitly called.
bool StartFixedRateSampling(uint32_t periodUs, uint32_t staleAfterUs);
void StopFixedRateSampling();
bool IsFixedRateSamplingActive();
uint32_t FixedRatePeriodUs();
uint32_t StaleAfterUs();

const Snapshot& Current();

} // namespace LineSensorSnapshot
