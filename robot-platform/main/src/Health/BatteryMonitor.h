#pragma once

#include <stdint.h>

#include "IBatteryAdcSource.h"

enum class BatteryState : uint8_t {
    GOOD = 0,
    LOW,
    CRITICAL,
    INVALID
};

struct BatteryMonitorConfig {
    uint16_t adcMaxCount = 4095;
    float adcReferenceVolts = 3.3f;
    float calibrationFactor = 1.0f;

    float lowThresholdVolts = 0.0f;
    float criticalThresholdVolts = 0.0f;
    float hysteresisVolts = 0.0f;

    uint8_t sampleCount = 5;
    uint16_t invalidLowRaw = 0;
    uint16_t invalidHighRaw = 4095;

    // Must remain false until the V2 resistor divider and battery thresholds
    // have been measured/approved on real hardware.
    bool calibrationValid = false;
};

class BatteryMonitor {
public:
    explicit BatteryMonitor(
        IBatteryAdcSource& source,
        const BatteryMonitorConfig& config = BatteryMonitorConfig()
    );

    bool sample();

    float voltage() const { return _voltage; }
    BatteryState state() const { return _state; }
    int lastRawAverage() const { return _lastRawAverage; }
    bool healthy() const { return _state != BatteryState::INVALID; }

    void setConfig(const BatteryMonitorConfig& config);
    const BatteryMonitorConfig& config() const { return _config; }

    static const char* stateName(BatteryState state);

private:
    bool configValid() const;
    BatteryState classify(float voltage) const;

    IBatteryAdcSource& _source;
    BatteryMonitorConfig _config;
    float _voltage = 0.0f;
    BatteryState _state = BatteryState::INVALID;
    int _lastRawAverage = 0;
};
