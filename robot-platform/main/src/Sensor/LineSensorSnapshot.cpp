#include "LineSensorSnapshot.h"

#include <Arduino.h>

#include "SensorID.h"
#include "SensorManager.h"
#include "TCRT5000.h"

#if defined(ARDUINO_ARCH_ESP32)
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#endif

namespace {
LineSensorSnapshot::Snapshot g_snapshot{};
bool g_cycleActive = false;
bool g_sampledThisCycle = false;

TCRT5000* g_fixedLeft = nullptr;
TCRT5000* g_fixedCenter = nullptr;
TCRT5000* g_fixedRight = nullptr;
volatile bool g_fixedRateActive = false;
uint32_t g_fixedRatePeriodUs = 0;
uint32_t g_staleAfterUs = 0;
uint32_t g_staleCount = 0;

struct FixedRateSample {
    bool left;
    bool center;
    bool right;
    uint8_t mask;
    uint32_t timestampUs;
    uint32_t sequence;
    uint32_t sampleIntervalUs;
    uint32_t maxSampleJitterUs;
    bool valid;
};

FixedRateSample g_fixedLatest{};

#if defined(ARDUINO_ARCH_ESP32)
portMUX_TYPE g_fixedRateMux = portMUX_INITIALIZER_UNLOCKED;
TaskHandle_t g_fixedRateTask = nullptr;
#endif

TCRT5000* lineSensor(SensorID id)
{
    auto* sensor = SensorManager::instance().getSensor(id);
    return sensor ? static_cast<TCRT5000*>(sensor) : nullptr;
}

void applyInvalidFallback(TCRT5000* left, TCRT5000* center, TCRT5000* right)
{
    if (left) left->ApplySnapshotReading(0);
    if (center) center->ApplySnapshotReading(0);
    if (right) right->ApplySnapshotReading(0);
}

void sampleFixedRateOnce()
{
    if (!g_fixedLeft || !g_fixedCenter || !g_fixedRight) {
        return;
    }

    g_fixedLeft->SampleHardwareDirect();
    g_fixedCenter->SampleHardwareDirect();
    g_fixedRight->SampleHardwareDirect();

    FixedRateSample next{};
    next.left = g_fixedLeft->isLineDetected();
    next.center = g_fixedCenter->isLineDetected();
    next.right = g_fixedRight->isLineDetected();
    next.mask = static_cast<uint8_t>((next.left ? 4 : 0) |
                                     (next.center ? 2 : 0) |
                                     (next.right ? 1 : 0));
    next.timestampUs = micros();
    next.valid = true;

#if defined(ARDUINO_ARCH_ESP32)
    portENTER_CRITICAL(&g_fixedRateMux);
#endif
    next.sequence = g_fixedLatest.sequence + 1u;
    if (g_fixedLatest.valid) {
        next.sampleIntervalUs = next.timestampUs - g_fixedLatest.timestampUs;
        const uint32_t jitter = next.sampleIntervalUs > g_fixedRatePeriodUs
            ? next.sampleIntervalUs - g_fixedRatePeriodUs
            : g_fixedRatePeriodUs - next.sampleIntervalUs;
        next.maxSampleJitterUs = jitter > g_fixedLatest.maxSampleJitterUs
            ? jitter : g_fixedLatest.maxSampleJitterUs;
    }
    g_fixedLatest = next;
#if defined(ARDUINO_ARCH_ESP32)
    portEXIT_CRITICAL(&g_fixedRateMux);
#endif
}

#if defined(ARDUINO_ARCH_ESP32)
void fixedRateTask(void*)
{
    const TickType_t periodTicks = pdMS_TO_TICKS((g_fixedRatePeriodUs + 999u) / 1000u);
    TickType_t lastWake = xTaskGetTickCount();
    while (g_fixedRateActive) {
        sampleFixedRateOnce();
        vTaskDelayUntil(&lastWake, periodTicks == 0 ? 1 : periodTicks);
    }
    g_fixedRateTask = nullptr;
    vTaskDelete(nullptr);
}
#endif
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
    g_snapshot.valid = false;
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

    if (g_fixedRateActive) {
        FixedRateSample latest{};
#if defined(ARDUINO_ARCH_ESP32)
        portENTER_CRITICAL(&g_fixedRateMux);
#endif
        latest = g_fixedLatest;
#if defined(ARDUINO_ARCH_ESP32)
        portEXIT_CRITICAL(&g_fixedRateMux);
#endif

        const uint32_t nowUs = micros();
        const bool fresh = latest.valid &&
            (g_staleAfterUs == 0u || static_cast<uint32_t>(nowUs - latest.timestampUs) <= g_staleAfterUs);

        g_snapshot.left = fresh ? latest.left : false;
        g_snapshot.center = fresh ? latest.center : false;
        g_snapshot.right = fresh ? latest.right : false;
        g_snapshot.mask = fresh ? latest.mask : 0u;
        g_snapshot.timestampUs = latest.timestampUs;
        g_snapshot.sequence = latest.sequence;
        g_snapshot.sampleIntervalUs = latest.sampleIntervalUs;
        g_snapshot.maxSampleJitterUs = latest.maxSampleJitterUs;
        g_snapshot.fixedRateActive = true;
        g_snapshot.physicalReadCount = 0;
        g_snapshot.valid = fresh;
        if (!fresh) {
            ++g_staleCount;
            ++g_snapshot.invalidCount;
        }
        g_snapshot.staleCount = g_staleCount;

        TCRT5000* left = lineSensor(SensorID::LineLeft);
        TCRT5000* center = lineSensor(SensorID::LineCenter);
        TCRT5000* right = lineSensor(SensorID::LineRight);
        if (fresh) {
            if (left) left->ApplySnapshotReading(latest.left ? 1 : 0);
            if (center) center->ApplySnapshotReading(latest.center ? 1 : 0);
            if (right) right->ApplySnapshotReading(latest.right ? 1 : 0);
        } else {
            applyInvalidFallback(left, center, right);
        }
        return fresh;
    }

    ++g_snapshot.sequence;
    g_snapshot.timestampUs = micros();
    g_snapshot.fixedRateActive = false;
    g_snapshot.sampleIntervalUs = 0;
    g_snapshot.maxSampleJitterUs = 0;
    g_snapshot.staleCount = 0;

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

bool StartFixedRateSampling(uint32_t periodUs, uint32_t staleAfterUs)
{
#if defined(ARDUINO_ARCH_ESP32)
    if (g_fixedRateActive || periodUs < 1000u) {
        return false;
    }

    g_fixedLeft = lineSensor(SensorID::LineLeft);
    g_fixedCenter = lineSensor(SensorID::LineCenter);
    g_fixedRight = lineSensor(SensorID::LineRight);
    if (!g_fixedLeft || !g_fixedCenter || !g_fixedRight) {
        return false;
    }

    g_fixedRatePeriodUs = periodUs;
    g_staleAfterUs = staleAfterUs;
    g_staleCount = 0;
    g_fixedLatest = FixedRateSample{};
    g_fixedRateActive = true;

    const BaseType_t created = xTaskCreatePinnedToCore(
        fixedRateTask,
        "line-sampler",
        2048,
        nullptr,
        2,
        &g_fixedRateTask,
        1);
    if (created != pdPASS) {
        g_fixedRateActive = false;
        g_fixedRateTask = nullptr;
        return false;
    }
    return true;
#else
    (void)periodUs;
    (void)staleAfterUs;
    return false;
#endif
}

void StopFixedRateSampling()
{
    g_fixedRateActive = false;
}

bool IsFixedRateSamplingActive()
{
    return g_fixedRateActive;
}

uint32_t FixedRatePeriodUs()
{
    return g_fixedRatePeriodUs;
}

uint32_t StaleAfterUs()
{
    return g_staleAfterUs;
}

const Snapshot& Current()
{
    return g_snapshot;
}

} // namespace LineSensorSnapshot
