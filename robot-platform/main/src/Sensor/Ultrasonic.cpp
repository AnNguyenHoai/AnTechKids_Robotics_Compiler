#include "Ultrasonic.h"
#include "../HAL/HAL.h"

Ultrasonic::Ultrasonic(int trigPin, int echoPin, uint32_t timeoutUs, const char* name)
    : _trigPin(trigPin), _echoPin(echoPin), _timeoutUs(timeoutUs),
      _name(name), _lastDistance(-1.0f), _healthy(true), _initialized(false),
      _consecutiveTimeouts(0) {}

bool Ultrasonic::initialize() {
    HAL::getGPIO().pinMode(_trigPin, HAL::PinMode::OUTPUT_MODE);
    HAL::getGPIO().pinMode(_echoPin, HAL::PinMode::INPUT_MODE);
    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::LOW_STATE);
    _initialized = true;
    _healthy = true;
    _consecutiveTimeouts = 0;
    return true;
}

void Ultrasonic::update() {
    if (!_initialized) {
        _healthy = false;
        return;
    }

    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::LOW_STATE);
    HAL::getTime().delayUs(2);
    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::HIGH_STATE);
    HAL::getTime().delayUs(10);
    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::LOW_STATE);

    uint32_t duration = HAL::getPulse().pulseIn(_echoPin, HAL::PinState::HIGH_STATE, _timeoutUs);

    if (duration == 0) {
        _lastDistance = -1.0f;
        _consecutiveTimeouts++;
        if (_consecutiveTimeouts >= MAX_CONSECUTIVE_TIMEOUTS) {
            _healthy = false;
        }
    } else {
        _lastDistance = (duration * 0.034f) / 2.0f;
        _consecutiveTimeouts = 0;
        _healthy = true;
    }
}

bool Ultrasonic::healthy() const {
    return _healthy && _initialized;
}

const char* Ultrasonic::name() const {
    return _name;
}

void Ultrasonic::shutdown() {}

float Ultrasonic::distanceCm() const {
    return _lastDistance;
}

float Ultrasonic::maxRangeCm() const {
    return 400.0f;
}

const char* Ultrasonic::unit() const {
    return "cm";
}