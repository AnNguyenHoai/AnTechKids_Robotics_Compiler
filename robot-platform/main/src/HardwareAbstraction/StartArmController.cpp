#include "StartArmController.h"

void StartArmController::begin(uint32_t nowMs) {
    _input.begin();

    _rawPressed = _input.isPressed();
    _stablePressed = _rawPressed;
    _lastRawChangeMs = nowMs;
    _systemReady = false;
    _requireRelease = _rawPressed;
    _armedByStartThisBoot = false;
}

void StartArmController::onSystemReady(uint32_t nowMs) {
    // Re-sample at the readiness boundary. A button that became pressed at
    // any point during setup must be released before a new press can arm.
    _rawPressed = _input.isPressed();
    _stablePressed = _rawPressed;
    _lastRawChangeMs = nowMs;
    _systemReady = true;
    _requireRelease = _rawPressed;
}

bool StartArmController::update(uint32_t nowMs) {
    const bool pressed = _input.isPressed();

    if (pressed != _rawPressed) {
        _rawPressed = pressed;
        _lastRawChangeMs = nowMs;
        return false;
    }

    if ((nowMs - _lastRawChangeMs) < DEBOUNCE_MS) {
        return false;
    }

    if (_stablePressed == _rawPressed) {
        return false;
    }

    _stablePressed = _rawPressed;

    if (!_stablePressed) {
        // A stable release is mandatory after a held/pre-ready press and also
        // provides the edge boundary for any later re-arm policy.
        _requireRelease = false;
        return false;
    }

    if (!_systemReady || _requireRelease) {
        _requireRelease = true;
        return false;
    }

    if (_motorSafety.state() != MotorSafetyState::SAFE) {
        return false;
    }

    if (_motorSafety.arm()) {
        _armedByStartThisBoot = true;
        return true;
    }

    return false;
}
