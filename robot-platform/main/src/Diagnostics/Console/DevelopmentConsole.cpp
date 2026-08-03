#include "DevelopmentConsole.h"
#include "ConsoleFormatter.h"
#include "ConsoleOutput.h"
#include "../DiagnosticsManager.h"
#include "../../Sensor/SensorManager.h"
#include "../../Sensor/TCRT5000.h"
#include "../../Sensor/SensorID.h"
#include <Arduino.h>

DevelopmentConsole& DevelopmentConsole::instance() {
    static DevelopmentConsole console;
    return console;
}

void DevelopmentConsole::begin() {
    _enabled = true;
    _refreshRateHz = 10;
    _lastOutputTime = 0;
    ConsoleOutput::begin();
}

void DevelopmentConsole::update() {
    if (!_enabled) return;
    uint32_t now = millis();
    uint32_t interval = _getIntervalMs();
    if (now - _lastOutputTime >= interval) {
        _output();
        _lastOutputTime = now;
    }
}

void DevelopmentConsole::setEnabled(bool enabled) {
    _enabled = enabled;
}

bool DevelopmentConsole::isEnabled() const {
    return _enabled;
}

void DevelopmentConsole::setRefreshRateHz(uint8_t hz) {
    if (hz < 1) hz = 1;
    if (hz > 50) hz = 50;
    _refreshRateHz = hz;
}

uint8_t DevelopmentConsole::getRefreshRateHz() const {
    return _refreshRateHz;
}

uint32_t DevelopmentConsole::_getIntervalMs() const {
    return 1000 / _refreshRateHz;
}

void DevelopmentConsole::_output() {
    auto& diagMgr = DiagnosticsManager::instance();
    auto& sensorMgr = SensorManager::instance();

    // Lấy state hiện tại (không gọi update, chỉ đọc giá trị đã có)
    auto leftSensor = static_cast<TCRT5000*>(sensorMgr.getSensor(SensorID::LineLeft));
    auto centerSensor = static_cast<TCRT5000*>(sensorMgr.getSensor(SensorID::LineCenter));
    auto rightSensor = static_cast<TCRT5000*>(sensorMgr.getSensor(SensorID::LineRight));

    uint8_t leftState = leftSensor ? leftSensor->isLineDetected() : 0;
    uint8_t centerState = centerSensor ? centerSensor->isLineDetected() : 0;
    uint8_t rightState = rightSensor ? rightSensor->isLineDetected() : 0;
    uint8_t mask = (leftState ? 4 : 0) | (centerState ? 2 : 0) | (rightState ? 1 : 0);

    // Lấy stats
    auto leftStat = diagMgr.getStatistics(SensorID::LineLeft);
    auto centerStat = diagMgr.getStatistics(SensorID::LineCenter);
    auto rightStat = diagMgr.getStatistics(SensorID::LineRight);

    // Runtime
    uint32_t tickCount = diagMgr.getTickCount();
    float loopFreq = diagMgr.getLoopFrequency();
    uint32_t lastLoopUs = diagMgr.getLastLoopTimeUs();
    uint32_t minLoopUs = diagMgr.getMinLoopTimeUs();
    uint32_t maxLoopUs = diagMgr.getMaxLoopTimeUs();

    ConsoleData data;
    data.leftState = leftState;
    data.centerState = centerState;
    data.rightState = rightState;
    data.mask = mask;
    data.leftStat = leftStat;
    data.centerStat = centerStat;
    data.rightStat = rightStat;
    data.tickCount = tickCount;
    data.loopFreq = loopFreq;
    data.lastLoopUs = lastLoopUs;
    data.minLoopUs = minLoopUs;
    data.maxLoopUs = maxLoopUs;

    String output = ConsoleFormatter::format(data);
    ConsoleOutput::print(output);
}