#include "DiagnosticsManager.h"
#include "../Sensor/SensorManager.h"
#include "../Sensor/TCRT5000.h"
#include "DiagnosticLogger.h"
#include <Arduino.h>

DiagnosticsManager& DiagnosticsManager::instance() {
    static DiagnosticsManager instance;
    return instance;
}

void DiagnosticsManager::updateSensors() {
    updateSensor(SensorID::LineLeft);
    updateSensor(SensorID::LineCenter);
    updateSensor(SensorID::LineRight);
}

void DiagnosticsManager::updateSensor(SensorID id) {
    auto sensor = SensorManager::instance().getSensor(id);
    if (!sensor) return;

    // Diagnostics are observers, not sensor-sampling owners. SensorManager or
    // the VM line snapshot has already refreshed the TCRT5000 cache for this
    // firmware cycle. Calling update() here used to cause a second physical
    // line read and made diagnostic state come from a different instant than
    // the control decision.
    auto lineSensor = static_cast<TCRT5000*>(sensor);
    bool value = lineSensor->isLineDetected();

    size_t idx = static_cast<size_t>(id);
    auto& stat = stats[idx];
    stat.readCount++;

    if (value) stat.highCount++;
    else stat.lowCount++;

    buffers[idx].push(value);
    stat.stability = buffers[idx].stability();

    static bool prevValues[static_cast<size_t>(SensorID::Count)] = {false};
    if (value != prevValues[idx]) {
        stat.transitionCount++;
        stat.lastTransitionTime = micros();
        prevValues[idx] = value;
    }
}

void DiagnosticsManager::recordLoopTime(uint32_t us) {
    tickCount++;
    lastLoopTimeUs = us;
    totalLoopTimeUs += us;
    if (us < minLoopTimeUs) minLoopTimeUs = us;
    if (us > maxLoopTimeUs) maxLoopTimeUs = us;
}

float DiagnosticsManager::getLoopFrequency() const {
    if (tickCount == 0) return 0.0f;
    float avgUs = (float)totalLoopTimeUs / tickCount;
    if (avgUs == 0) return 0.0f;
    return 1000000.0f / avgUs;
}

void DiagnosticsManager::printReport() {
    DiagnosticLogger::printSeparator();
    DiagnosticLogger::printHeader("Sensor Diagnostics");

    auto printSensor = [&](SensorID id, const char* label) {
        auto& stat = stats[static_cast<size_t>(id)];
        DiagnosticLogger::printSensor(label, stat);
    };

    printSensor(SensorID::LineLeft, "LEFT");
    printSensor(SensorID::LineCenter, "CENTER");
    printSensor(SensorID::LineRight, "RIGHT");

    DiagnosticLogger::printRuntime(tickCount, getLoopFrequency(),
                                   lastLoopTimeUs, minLoopTimeUs, maxLoopTimeUs);
    DiagnosticLogger::printSeparator();
}

const SensorStatistics& DiagnosticsManager::getStatistics(SensorID id) const {
    return stats[static_cast<size_t>(id)];
}
