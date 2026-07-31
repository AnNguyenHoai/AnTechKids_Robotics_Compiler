#include "TCRT5000.h"
#include "../HAL/HAL.h"

TCRT5000::TCRT5000(int pin, const char* sensorName, int threshold)
    : _pin(pin), _name(sensorName), _threshold(threshold),
      _lastReading(0), _healthy(true) {}

bool TCRT5000::initialize() {
    HAL::getGPIO().pinMode(_pin, HAL::PinMode::INPUT_MODE);
    _healthy = true;
    return true;
}

void TCRT5000::update() {
    auto state = HAL::getGPIO().digitalRead(_pin);
    _lastReading = (state == HAL::PinState::HIGH_STATE) ? 1 : 0;
}

bool TCRT5000::healthy() const {
    return _healthy;
}

const char* TCRT5000::name() const {
    return _name;
}

void TCRT5000::shutdown() {
    // Nothing to release
}

int TCRT5000::read() const {
    return _lastReading;
}

bool TCRT5000::isLineDetected() const {
    return (_lastReading == _threshold);
}

int TCRT5000::rawLevel() const {
    return _lastReading;
}

void TCRT5000::setThreshold(int threshold) {
    _threshold = threshold;
}

int TCRT5000::getThreshold() const {
    return _threshold;
}