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

    // Whole-firmware-cycle observability. RunSlice timing alone is not an
    // end-to-end sensor-response guarantee because fresh line samples are owned
    // by the firmware cycle.
    uint32_t lastFirmwareCycleUs;
    uint32_t maxFirmwareCycleUs;
    uint32_t lastLineSamplePeriodUs;
    uint32_t maxLineSamplePeriodUs;
    uint32_t lastLineSampleTimestampUs;

    // Reactive line-read -> stop evidence. These fields measure software timing
    // only; mechanical coast/braking distance remains a separate physical fact.
    uint32_t reactiveStopCount;
    uint32_t lastReactiveSampleToStopUs;
    uint32_t maxReactiveSampleToStopUs;
    uint32_t lastReactiveObservationToStopUs;
    uint32_t maxReactiveObservationToStopUs;
};

// Development/qualification-oriented aggregation for VM-RT H/X. The VM
// scheduler does not consult this state, so telemetry cannot change runtime
// decisions.
namespace VMRuntimeTelemetry {

void Reset();
void RecordSlice(const VMRunSliceResult& result);

// Records an upper-bound stop/abort observation window measured by the firmware
// control plane (service-cycle entry -> VM observed non-running).
void RecordStopLatency(uint32_t latencyUs);

// Records one complete firmware-loop period and the physical line-sample
// timestamp used by that cycle. All values are wrap-safe unsigned deltas.
void RecordFirmwareCycle(uint32_t cycleStartUs,
                         uint32_t lineSampleTimestampUs,
                         uint32_t cycleEndUs);

// Reactive timing markers are written from the actual executed VM opcodes.
// A detected line observation arms one pending marker; a subsequent Stop opcode
// closes it at the post-Step/PWM-submission timestamp.
void RecordReactiveLineObservation(uint32_t lineSampleTimestampUs,
                                   uint32_t observationUs,
                                   uint32_t lineSequence,
                                   bool detected);
void RecordReactiveStop(uint32_t stopSubmittedUs);

const VMRuntimeTelemetrySnapshot& Current();

// Stable JSONL evidence format for serial capture during physical qualification.
// These functions are compiled as no-ops unless VM_RESPONSIVENESS_DIAGNOSTICS=1.
// RecordSlice()/timing markers never print: qualification samples are buffered
// in RAM so UART transmission cannot perturb the control loop being measured.
void PrintLatestJson();
void PrintBufferedJson();

} // namespace VMRuntimeTelemetry
