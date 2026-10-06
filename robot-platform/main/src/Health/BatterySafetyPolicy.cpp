#include "BatterySafetyPolicy.h"

BatterySafetyEvent BatterySafetyPolicy::update(uint32_t nowMs) {
    if (_hasSampled && (nowMs - _lastSampleMs) < SAMPLE_INTERVAL_MS) {
        return BatterySafetyEvent::NONE;
    }

    _lastSampleMs = nowMs;
    _hasSampled = true;

    if (!_monitor.sample()) {
        _lastState = BatteryState::INVALID;
        // INVALID is not silently treated as CRITICAL because V2-HLT-001
        // production calibration is intentionally invalid until hardware
        // values are approved. If CRITICAL was already latched, keep the
        // latch and servo block until a valid recovered reading is observed.
        return BatterySafetyEvent::INVALID_READING;
    }

    _lastState = _monitor.state();

    if (_lastState == BatteryState::CRITICAL) {
        if (!_criticalLatched) {
            _criticalLatched = true;
            _actions.disarmForCriticalBattery();
            return BatterySafetyEvent::CRITICAL_DISARMED;
        }
        return BatterySafetyEvent::NONE;
    }

    if (_criticalLatched) {
        // BatteryMonitor hysteresis owns the threshold recovery decision.
        // Once it reports LOW/GOOD again, clear only the LOW_BATTERY fault
        // back to SAFE. Never auto-arm.
        if (_actions.recoverLowBatteryFaultToSafe()) {
            _criticalLatched = false;
            return BatterySafetyEvent::RECOVERED_SAFE;
        }
        return BatterySafetyEvent::NONE;
    }

    if (_lastState == BatteryState::LOW) {
        return BatterySafetyEvent::LOW_WARNING;
    }

    return BatterySafetyEvent::NONE;
}
