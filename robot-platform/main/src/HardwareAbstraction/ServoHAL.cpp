#include "ServoHAL.h"

int ServoHAL::clampAngle(int angle) {
    if (angle < 0) return 0;
    if (angle > 180) return 180;
    return angle;
}

uint32_t ServoHAL::angleToDuty(int angle) {
    const int clamped = clampAngle(angle);
    const uint32_t pulseUs = MIN_PULSE_US +
        static_cast<uint32_t>((MAX_PULSE_US - MIN_PULSE_US) * clamped / 180);
    const uint32_t maxDuty = (1u << PWM_RESOLUTION_BITS) - 1u;
    return static_cast<uint32_t>((static_cast<uint64_t>(pulseUs) * maxDuty) / PERIOD_US);
}

bool ServoHAL::pinForPort(int port, uint8_t& pin) {
    switch (port) {
        case 1:
            pin = BoardProfile::Pins::SERVO1;
            return true;
        case 2:
            pin = BoardProfile::Pins::SERVO2;
            return true;
        default:
            pin = 0;
            return false;
    }
}

bool ServoHAL::ensureAttached(int port, uint8_t pin) {
    const int index = port - 1;
    if (_attached[index]) return true;

    if (!_transport.attach(pin, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS)) {
        _lastError = ServoError::PWM_ERROR;
        return false;
    }

    _attached[index] = true;
    return true;
}

bool ServoHAL::setAngle(int port, int angle) {
    uint8_t pin = 0;
    if (!pinForPort(port, pin)) {
        _lastError = ServoError::INVALID_PORT;
        return false;
    }

    if (!ensureAttached(port, pin)) {
        return false;
    }

    if (!_transport.write(pin, angleToDuty(angle))) {
        _lastError = ServoError::PWM_ERROR;
        return false;
    }

    _lastError = ServoError::OK;
    return true;
}
