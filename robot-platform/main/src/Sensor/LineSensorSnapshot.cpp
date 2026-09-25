#include "LineSensorSnapshot.h"

#include <Arduino.h>

#include "SensorID.h"
#include "SensorManager.h"
#include "TCRT5000.h"

namespace {
LineSensorSnapshot::Snapshot g_snapshot{};
bool g_cycleActive = false;
bool g_sampledThisCycle = false;

TCRT5000* lineSensor(SensorID id)
{
    auto* sensor = SensorManager::instance().getSensor(id);
    return sensor ? static_cast<TCRT5000*>(sensor) : nullptr;
}

void applyInvalidFallback(TCRT5000* left, TCRT5000* center, TCRT5000* right)
{
    // Existing RobotAPI behavior already maps unavailable line input to zero.
    // Keep the whole invalid sample atomic rather than mixing fresh/stale data.
    if (left) left->ApplySnapshotReading(0);
    if (center) center->ApplySnapshotReading(0);
    if (right) right->ApplySnapshotReading(0);
}
}

namespace LineSensorSnapshot {

void BeginCycle()
{
    g_cycleActive = true;
    g_sampledThisCycle = false;
    g_snapshot.valid = false;
    g_snapshot.consumerCount = 0;
    g_snapshot.physicalReadCount = 0;
}

void EndCycle()
{
    g_cycleActive = false;
}

void Invalidate()
{
    g_cycleActive = false;
    g_sampledThisCycle = false;
    g_snapshot.valid = false;
    g_snapshot.consumerCount = 0;
    g_snapshot.physicalReadCount = 0;
}

bool IsCycleActive()
{
    return g_cycleActive;
}

bool EnsureSample()
{
    if (!g_cycleActive) {
        return false;
    }
    if (g_sampledThisCycle) {
        return g_snapshot.valid;
    }

    g_sampledThisCycle = true;
    ++g_snapshot.sequence;
    g_snapshot.timestampUs = micros();

    TCRT5000* left = lineSensor(SensorID::LineLeft);
    TCRT5000* center = lineSensor(SensorID::LineCenter);
    TCRT5000* right = lineSensor(SensorID::LineRight);

    if (!left || !center || !right) {
        applyInvalidFallback(left, center, right);
        g_snapshot.left = false;
        g_snapshot.center = false;
        g_snapshot.right = false;
        g_snapshot.mask = 0;
        g_snapshot.valid = false;
        ++g_snapshot.invalidCount;
        return false;
    }

    left->SampleHardwareDirect();
    center->SampleHardwareDirect();
    right->SampleHardwareDirect();
    g_snapshot.physicalReadCount = 3;

    g_snapshot.left = left->isLineDetected();
    g_snapshot.center = center->isLineDetected();
    g_snapshot.right = right->isLineDetected();
    g_snapshot.mask = static_cast<uint8_t>((g_snapshot.left ? 4 : 0) |
                                           (g_snapshot.center ? 2 : 0) |
                                           (g_snapshot.right ? 1 : 0));
    g_snapshot.valid = true;
    return true;
}

void RecordConsumer()
{
    ++g_snapshot.consumerCount;
}

const Snapshot& Current()
{
    return g_snapshot;
}

} // namespace LineSensorSnapshot
