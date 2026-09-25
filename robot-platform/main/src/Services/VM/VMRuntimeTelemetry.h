#pragma once

#include <stdint.h>
#include "VM.h"

#ifndef VM_RESPONSIVENESS_DIAGNOSTICS
#define VM_RESPONSIVENESS_DIAGNOSTICS 0
#endif

struct VMRuntimeTelemetrySnapshot
{
    uint32_t sliceCount;
    VMRunSliceResult lastSlice;
    uint32_t maxSliceDurationUs;
    uint32_t maxWorkUnitDurationUs;
    uint16_t maxWorkUnitProgramCounter;
    uint32_t lastStopLatencyUs;
    uint32_t maxStopLatencyUs;
};

// Development/qualification-oriented aggregation for VM-RT H. The VM scheduler
// does not consult this state, so telemetry cannot change runtime decisions.
namespace VMRuntimeTelemetry {

void Reset();
void RecordSlice(const VMRunSliceResult& result);

// Records an upper-bound stop/abort observation window measured by the firmware
// control plane (service-cycle entry -> VM observed non-running).
void RecordStopLatency(uint32_t latencyUs);

const VMRuntimeTelemetrySnapshot& Current();

// Stable JSONL evidence format for serial capture during physical qualification.
// Output is compiled as a no-op unless VM_RESPONSIVENESS_DIAGNOSTICS=1.
void PrintLatestJson();

} // namespace VMRuntimeTelemetry
