#include "MotorSafetyController.h"

void MotorSafetyController::begin() {
    _gate.beginSafe();
    _driverEnabled = false;
    _lastDisarmReason = MotorDisarmReason::RESET;
    _state = MotorSafetyState::SAFE;
}

bool MotorSafetyController::arm() {
    if (!_motorFeatureEnabled || _state == MotorSafetyState::BOOT || _state == MotorSafetyState::FAULT) {
        _gate.setDriverEnabled(false);
        _driverEnabled = false;
        return false;
    }

    _gate.setDriverEnabled(true);
    _driverEnabled = true;
    _lastDisarmReason = MotorDisarmReason::NONE;
    _state = MotorSafetyState::ARMED;
    return true;
}

void MotorSafetyController::disarm(MotorDisarmReason reason) {
    _gate.setDriverEnabled(false);
    _driverEnabled = false;
    _lastDisarmReason = reason;
    _state = isFaultReason(reason) ? MotorSafetyState::FAULT : MotorSafetyState::SAFE;
}

bool MotorSafetyController::recoverFaultToSafe(MotorDisarmReason reason) {
    if (_state != MotorSafetyState::FAULT || _lastDisarmReason != reason) {
        return false;
    }

    // Recovery never enables the physical driver. A fresh approved START
    // press is still required to transition SAFE -> ARMED.
    _gate.setDriverEnabled(false);
    _driverEnabled = false;
    _state = MotorSafetyState::SAFE;
    return true;
}

bool MotorSafetyController::isArmed() const {
    return _driverEnabled &&
           (_state == MotorSafetyState::ARMED || _state == MotorSafetyState::RUNNING);
}

bool MotorSafetyController::allowPhysicalOutput(int leftCommand, int rightCommand) {
    const bool nonZero = leftCommand != 0 || rightCommand != 0;

    if (!nonZero) {
        if (_state == MotorSafetyState::RUNNING) {
            _state = MotorSafetyState::ARMED;
        }
        return true;
    }

    if (!isArmed()) {
        return false;
    }

    _state = MotorSafetyState::RUNNING;
    return true;
}

bool MotorSafetyController::isFaultReason(MotorDisarmReason reason) {
    switch (reason) {
        case MotorDisarmReason::LOW_BATTERY:
        case MotorDisarmReason::FATAL_PLATFORM_FAULT:
        case MotorDisarmReason::MOTOR_SAFETY_FAULT:
        case MotorDisarmReason::WATCHDOG:
            return true;
        default:
            return false;
    }
}
