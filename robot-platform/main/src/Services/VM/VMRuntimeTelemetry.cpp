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

void printJson(uint32_t sliceOrdinal, const VMRunSliceResult& r)
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
        static_cast<unsigned long>(g_snapshot.lastStopLatencyUs),
        static_cast<unsigned long>(g_snapshot.maxStopLatencyUs));
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

const VMRuntimeTelemetrySnapshot& Current()
{
    return g_snapshot;
}

void PrintLatestJson()
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    printJson(g_snapshot.sliceCount, g_snapshot.lastSlice);
#endif
}

void PrintBufferedJson()
{
#if VM_RESPONSIVENESS_DIAGNOSTICS
    if (g_sliceBufferedCount == 0) {
        return;
    }

    const uint16_t oldest = static_cast<uint16_t>(
        (g_sliceWriteIndex + kSliceBufferCapacity - g_sliceBufferedCount) % kSliceBufferCapacity);

    for (uint16_t offset = 0; offset < g_sliceBufferedCount; ++offset) {
        const uint16_t index = static_cast<uint16_t>((oldest + offset) % kSliceBufferCapacity);
        printJson(g_sliceOrdinal[index], g_sliceBuffer[index]);
    }
#endif
}

} // namespace VMRuntimeTelemetry
