#pragma once

#include <stdint.h>

#include "BatteryMonitor.h"
#include "IBatterySafetyActions.h"

enum class BatterySafetyEvent : uint8_t {
    NONE = 0,
    LOW_WARNING,
    CRITICAL_DISARMED,
    RECOVERED_SAFE,
    INVALID_READING
};

class BatterySafetyPolicy {
public:
    static constexpr uint32_t SAMPLE_INTERVAL_MS = 250;

    BatterySafetyPolicy(BatteryMonitor& monitor, IBatterySafetyActions& actions)
        : _monitor(monitor), _actions(actions) {}

    BatterySafetyEvent update(uint32_t nowMs);

    bool criticalLatched() const { return _criticalLatched; }
    bool servoActivityAllowed() const { return !_criticalLatched; }
    bool lowWarningActive() const {
        return _lastState == BatteryState::LOW || _lastState == BatteryState::CRITICAL;
    }
    BatteryState lastState() const { return _lastState; }

private:
    BatteryMonitor& _monitor;
    IBatterySafetyActions& _actions;

    uint32_t _lastSampleMs = 0;
    bool _hasSampled = false;
    bool _criticalLatched = false;
    BatteryState _lastState = BatteryState::INVALID;
};
