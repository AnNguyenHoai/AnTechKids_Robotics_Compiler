#pragma once

#include <stdint.h>

#include "BoardProfile.h"
#include "IServoPwmTransport.h"

enum class ServoError : uint8_t {
    OK = 0,
    INVALID_PORT,
    PWM_ERROR
};

class ServoHAL {
public:
    explicit ServoHAL(IServoPwmTransport& transport) : _transport(transport) {}

    bool setAngle(int port, int angle);

    ServoError lastError() const { return _lastError; }

    static int clampAngle(int angle);
    static uint32_t angleToDuty(int angle);
    static bool pinForPort(int port, uint8_t& pin);

    static constexpr uint32_t PWM_FREQUENCY_HZ = 50;
    static constexpr uint8_t PWM_RESOLUTION_BITS = 16;
    static constexpr uint32_t MIN_PULSE_US = 500;
    static constexpr uint32_t MAX_PULSE_US = 2500;
    static constexpr uint32_t PERIOD_US = 20000;

private:
    bool ensureAttached(int port, uint8_t pin);

    IServoPwmTransport& _transport;
    bool _attached[2] = {false, false};
    ServoError _lastError = ServoError::OK;
};
