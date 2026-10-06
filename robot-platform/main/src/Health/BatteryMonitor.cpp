#include "BatteryMonitor.h"

BatteryMonitor::BatteryMonitor(
    IBatteryAdcSource& source,
    const BatteryMonitorConfig& config
) : _source(source), _config(config) {}

void BatteryMonitor::setConfig(const BatteryMonitorConfig& config) {
    _config = config;
    _state = BatteryState::INVALID;
    _voltage = 0.0f;
    _lastRawAverage = 0;
}

bool BatteryMonitor::configValid() const {
    return _config.calibrationValid &&
           _config.adcMaxCount > 0 &&
           _config.adcReferenceVolts > 0.0f &&
           _config.calibrationFactor > 0.0f &&
           _config.sampleCount > 0 &&
           _config.invalidLowRaw < _config.invalidHighRaw &&
           _config.invalidHighRaw <= _config.adcMaxCount &&
           _config.criticalThresholdVolts > 0.0f &&
           _config.lowThresholdVolts > _config.criticalThresholdVolts &&
           _config.hysteresisVolts >= 0.0f;
}

bool BatteryMonitor::sample() {
    if (!configValid()) {
        _state = BatteryState::INVALID;
        _voltage = 0.0f;
        _lastRawAverage = 0;
        return false;
    }

    uint32_t sum = 0;
    for (uint8_t i = 0; i < _config.sampleCount; ++i) {
        const int raw = _source.readRaw();
        if (raw <= static_cast<int>(_config.invalidLowRaw) ||
            raw >= static_cast<int>(_config.invalidHighRaw)) {
            _state = BatteryState::INVALID;
            _voltage = 0.0f;
            _lastRawAverage = raw;
            return false;
        }
        sum += static_cast<uint32_t>(raw);
    }

    _lastRawAverage = static_cast<int>(sum / _config.sampleCount);
    const float sensedVolts =
        (static_cast<float>(_lastRawAverage) / static_cast<float>(_config.adcMaxCount)) *
        _config.adcReferenceVolts;
    _voltage = sensedVolts * _config.calibrationFactor;
    _state = classify(_voltage);
    return true;
}

BatteryState BatteryMonitor::classify(float voltage) const {
    switch (_state) {
        case BatteryState::CRITICAL:
            if (voltage < _config.criticalThresholdVolts + _config.hysteresisVolts) {
                return BatteryState::CRITICAL;
            }
            if (voltage < _config.lowThresholdVolts + _config.hysteresisVolts) {
                return BatteryState::LOW;
            }
            return BatteryState::GOOD;

        case BatteryState::LOW:
            if (voltage <= _config.criticalThresholdVolts) {
                return BatteryState::CRITICAL;
            }
            if (voltage < _config.lowThresholdVolts + _config.hysteresisVolts) {
                return BatteryState::LOW;
            }
            return BatteryState::GOOD;

        case BatteryState::GOOD:
            if (voltage <= _config.criticalThresholdVolts) {
                return BatteryState::CRITICAL;
            }
            if (voltage <= _config.lowThresholdVolts) {
                return BatteryState::LOW;
            }
            return BatteryState::GOOD;

        case BatteryState::INVALID:
        default:
            if (voltage <= _config.criticalThresholdVolts) {
                return BatteryState::CRITICAL;
            }
            if (voltage <= _config.lowThresholdVolts) {
                return BatteryState::LOW;
            }
            return BatteryState::GOOD;
    }
}

const char* BatteryMonitor::stateName(BatteryState state) {
    switch (state) {
        case BatteryState::GOOD: return "GOOD";
        case BatteryState::LOW: return "LOW";
        case BatteryState::CRITICAL: return "CRITICAL";
        case BatteryState::INVALID: return "INVALID";
        default: return "INVALID";
    }
}
