#include "VMRuntimeTelemetry.h"
#include <Arduino.h>

namespace {
VMRuntimeTelemetrySnapshot g_snapshot{};

#if VM_RESPONSIVENESS_DIAGNOSTICS
constexpr uint16_t kSliceBufferCapacity = 256;
VMRunSliceResult g_sliceBuffer[kSliceBufferCapacity]{};
uint32_t g_sliceOrdinal[kSliceBufferCapacity]{};
uint16_t g_sliceWriteIndex = 0;
uint16_t g_sliceBufferedCount = 0;

struct ReactiveTimingRecord
{
    uint32_t lineSequence;
    uint32_t sampleTimestampUs;
    uint32_t observationUs;
    uint32_t stopSubmittedUs;
    uint32_t sampleToStopUs;
    uint32_t observationToStopUs;
};

constexpr uint16_t kReactiveBufferCapacity = 64;
ReactiveTimingRecord g_reactiveBuffer[kReactiveBufferCapacity]{};
uint16_t g_reactiveWriteIndex = 0;
uint16_t g_reactiveBufferedCount = 0;

struct PendingReactiveObservation
{
    bool armed;
    uint32_t lineSequence;
    uint32_t sampleTimestampUs;
    uint32_t observationUs;
};

PendingReactiveObservation g_pendingReactive{};

void printJson(uint32_t sliceOrdinal,
               const VMRunSliceResult& r,
               uint32_t stopLatencyUs,
               uint32_t maxStopLatencyUs)
{
    Serial.printf(
        "{\"type\":\"vm_rt\",\"slice\":%lu,\"duration_us\":%lu,"
        "\"work_units\":%u,\"reason\":%u,\"start_pc\":%u,\"end_pc\":%u,"
        "\"max_work_us\":%lu,\"max_work_pc\":%u,\"pending_op\":%u,"
        "\"pending_state\":%u,\"pending_pc\":%u,\"pending_gen\":%lu,"
        "\"pending_opcode\":%u,\"pending_opcode_valid\":%u,"
        "\"line_seq\":%lu,\"line_age_us\":%lu,\"line_reads\":%lu,"
        "\"line_consumers\":%lu,\"line_invalid\":%lu,\"line_valid\":%u,"
        "\"stop_latency_us\":%lu,\"max_stop_latency_us\":%lu}\n",
        static_cast<unsigned long>(sliceOrdinal),
        static_cast<unsigned long>(r.sliceDurationUs),
        static_cast<unsigned>(r.workUnits),
        static_cast<unsigned>(r.reason),
        static_cast<unsigned>(r.startProgramCounter),
        static_cast<unsigned>(r.endProgramCounter),
        static_cast<unsigned long>(r.maxWorkUnitDurationUs),
        static_cast<unsigned>(r.maxWorkUnitProgramCounter),
        static_cast<unsigned>(r.pendingOperation),
        static_cast<unsigned>(r.pendingLifecycle),
        static_cast<unsigned>(r.pendingOwnerProgramCounter),
        static_cast<unsigned long>(r.pendingGeneration),
        static_cast<unsigned>(r.pendingOpcode),
        r.pendingOpcodeValid ? 1u : 0u,
        static_cast<unsigned long>(r.lineSnapshotSequence),
        static_cast<unsigned long>(r.lineSnapshotAgeUs),
        static_cast<unsigned long>(r.lineSnapshotPhysicalReadCount),
        static_cast<unsigned long>(r.lineSnapshotConsumerCount),
        static_cast<unsigned long>(r.lineSnapshotInvalidCount),
        r.lineSnapshotValid ? 1u : 0u,
        static_cast<unsigned long>(stopLatencyUs),
        static_cast<unsigned long>(maxStopLatencyUs));
}

void printReactiveJson(const ReactiveTimingRecord& r)
{
    Serial.printf(
        "{\"type\":\"vm_rt_reactive\",\"line_seq\":%lu,"
        "\"sample_us\":%lu,\"observation_us\":%lu,\"stop_us\":%lu,"
        "\"sample_to_stop_us\":%lu,\"observation_to_stop_us\":%lu}\n",
        static_cast<unsigned long>(r.lineSequence),
        static_cast<unsigned long>(r.sampleTimestampUs),
        static_cast<unsigned long>(r.observationUs),
        static_cast<unsigned long>(r.stopSubmittedUs),
        static_cast<unsigned long>(r.sampleToStopUs),
        static_cast<unsigned long>(r.observationToStopUs));
}
#endif
}

namespace VMRuntimeTelemetry {

void Reset()
{
    g_snapshot = VMRuntimeTelemetrySnapshot{};
#if VM_RESPONSIVENESS_DIAGNOSTICS
    g_sliceWriteIndex = 0;
    g_sliceBufferedCount = 0;
    g_reactiveWriteIndex = 0;
    g_reactiveBufferedCount = 0;
    g_pendingReactive = PendingReactiveObservation{};
#endif
}

void RecordSlice(const VMRunSliceResult& result)
{
    g_snapshot.lastSlice = result;
    ++g_snapshot.sliceCount;

    if (result.sliceDurationUs > g_snapshot.maxSliceDurationUs) {
        g_snapshot.maxSliceDurationUs = result.sliceDurationUs;
    }

    if (result.maxWorkUnitDurationUs > g_snapshot.maxWorkUnitDurationUs) {
        g_snapshot.maxWorkUnitDurationUs = result.maxWorkUnitDurationUs;
        g_snapshot.maxWorkUnitProgramCounter = result.maxWorkUnitProgramCounter;
    }

#if VM_RESPONSIVENESS_DIAGNOSTICS
    // RAM-only capture: never transmit UART data while the VM control loop is
    // active. The ring keeps the latest bounded window for post-run evidence.
    g_sliceBuffer[g_sliceWriteIndex] = result;
    g_sliceOrdinal[g_sliceWriteIndex] = g_snapshot.sliceCount;
    g_sliceWriteIndex = static_cast<uint16_t>((g_sliceWriteIndex + 1) % kSliceBufferCapacity);
    if (g_sliceBufferedCount < kSliceBufferCapacity) {
        ++g_sliceBufferedCount;
    }
#endif
}

void RecordStopLatency(uint32_t latencyUs)
{
    g_snapshot.lastStopLatencyUs = latencyUs;
    if (latencyUs > g_snapshot.maxStopLatencyUs) {
        g_snapshot.maxStopLatencyUs = latencyUs;
    }
}

void RecordFirmwareCycle(uint32_t cycleStartUs,
                         uint32_t lineSampleTimestampUs,
                         uint32_t cycleEndUs)
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    const uint32_t cycleUs = cycleEndUs - cycleStartUs;
    g_snapshot.lastFirmwareCycleUs = cycleUs;
    if (cycleUs > g_snapshot.maxFirmwareCycleUs) {
        g_snapshot.maxFirmwareCycleUs = cycleUs;
    }

    if (lineSampleTimestampUs != 0) {
        if (g_snapshot.lastLineSampleTimestampUs != 0) {
            const uint32_t periodUs = lineSampleTimestampUs - g_snapshot.lastLineSampleTimestampUs;
            g_snapshot.lastLineSamplePeriodUs = periodUs;
            if (periodUs > g_snapshot.maxLineSamplePeriodUs) {
                g_snapshot.maxLineSamplePeriodUs = periodUs;
            }
        }
        g_snapshot.lastLineSampleTimestampUs = lineSampleTimestampUs;
    }
#else
    (void)cycleStartUs;
    (void)lineSampleTimestampUs;
    (void)cycleEndUs;
#endif
}

void RecordReactiveLineObservation(uint32_t lineSampleTimestampUs,
                                   uint32_t observationUs,
                                   uint32_t lineSequence,
                                   bool detected)
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    if (!detected || lineSampleTimestampUs == 0) {
        g_pendingReactive = PendingReactiveObservation{};
        return;
    }

    g_pendingReactive.armed = true;
    g_pendingReactive.lineSequence = lineSequence;
    g_pendingReactive.sampleTimestampUs = lineSampleTimestampUs;
    g_pendingReactive.observationUs = observationUs;
#else
    (void)lineSampleTimestampUs;
    (void)observationUs;
    (void)lineSequence;
    (void)detected;
#endif
}

void RecordReactiveStop(uint32_t stopSubmittedUs)
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    if (!g_pendingReactive.armed) {
        return;
    }

    ReactiveTimingRecord record{};
    record.lineSequence = g_pendingReactive.lineSequence;
    record.sampleTimestampUs = g_pendingReactive.sampleTimestampUs;
    record.observationUs = g_pendingReactive.observationUs;
    record.stopSubmittedUs = stopSubmittedUs;
    record.sampleToStopUs = stopSubmittedUs - record.sampleTimestampUs;
    record.observationToStopUs = stopSubmittedUs - record.observationUs;

    g_reactiveBuffer[g_reactiveWriteIndex] = record;
    g_reactiveWriteIndex = static_cast<uint16_t>((g_reactiveWriteIndex + 1) % kReactiveBufferCapacity);
    if (g_reactiveBufferedCount < kReactiveBufferCapacity) {
        ++g_reactiveBufferedCount;
    }

    ++g_snapshot.reactiveStopCount;
    g_snapshot.lastReactiveSampleToStopUs = record.sampleToStopUs;
    g_snapshot.lastReactiveObservationToStopUs = record.observationToStopUs;
    if (record.sampleToStopUs > g_snapshot.maxReactiveSampleToStopUs) {
        g_snapshot.maxReactiveSampleToStopUs = record.sampleToStopUs;
    }
    if (record.observationToStopUs > g_snapshot.maxReactiveObservationToStopUs) {
        g_snapshot.maxReactiveObservationToStopUs = record.observationToStopUs;
    }

    g_pendingReactive = PendingReactiveObservation{};
#else
    (void)stopSubmittedUs;
#endif
}

const VMRuntimeTelemetrySnapshot& Current()
{
    return g_snapshot;
}

void PrintLatestJson()
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    printJson(g_snapshot.sliceCount,
              g_snapshot.lastSlice,
              g_snapshot.lastStopLatencyUs,
              g_snapshot.maxStopLatencyUs);
#endif
}

void PrintBufferedJson()
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    if (g_sliceBufferedCount != 0) {
        const uint16_t oldest = static_cast<uint16_t>(
            (g_sliceWriteIndex + kSliceBufferCapacity - g_sliceBufferedCount) % kSliceBufferCapacity);

        for (uint16_t offset = 0; offset < g_sliceBufferedCount; ++offset) {
            const uint16_t index = static_cast<uint16_t>((oldest + offset) % kSliceBufferCapacity);
            const bool lastRecord = (offset + 1u) == g_sliceBufferedCount;

            // A control-plane stop is observed after the last active VM slice.
            // Do not stamp that one observation onto every buffered record.
            printJson(g_sliceOrdinal[index],
                      g_sliceBuffer[index],
                      lastRecord ? g_snapshot.lastStopLatencyUs : 0u,
                      g_snapshot.maxStopLatencyUs);
        }
    }

    if (g_reactiveBufferedCount != 0) {
        const uint16_t oldest = static_cast<uint16_t>(
            (g_reactiveWriteIndex + kReactiveBufferCapacity - g_reactiveBufferedCount) % kReactiveBufferCapacity);
        for (uint16_t offset = 0; offset < g_reactiveBufferedCount; ++offset) {
            const uint16_t index = static_cast<uint16_t>((oldest + offset) % kReactiveBufferCapacity);
            printReactiveJson(g_reactiveBuffer[index]);
        }
    }

    Serial.printf(
        "{\"type\":\"vm_rt_cycle_summary\",\"last_cycle_us\":%lu,"
        "\"max_cycle_us\":%lu,\"last_line_sample_period_us\":%lu,"
        "\"max_line_sample_period_us\":%lu,\"reactive_stop_count\":%lu,"
        "\"last_sample_to_stop_us\":%lu,\"max_sample_to_stop_us\":%lu,"
        "\"last_observation_to_stop_us\":%lu,\"max_observation_to_stop_us\":%lu}\n",
        static_cast<unsigned long>(g_snapshot.lastFirmwareCycleUs),
        static_cast<unsigned long>(g_snapshot.maxFirmwareCycleUs),
        static_cast<unsigned long>(g_snapshot.lastLineSamplePeriodUs),
        static_cast<unsigned long>(g_snapshot.maxLineSamplePeriodUs),
        static_cast<unsigned long>(g_snapshot.reactiveStopCount),
        static_cast<unsigned long>(g_snapshot.lastReactiveSampleToStopUs),
        static_cast<unsigned long>(g_snapshot.maxReactiveSampleToStopUs),
        static_cast<unsigned long>(g_snapshot.lastReactiveObservationToStopUs),
        static_cast<unsigned long>(g_snapshot.maxReactiveObservationToStopUs));
#endif
}

} // namespace VMRuntimeTelemetry
