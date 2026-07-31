#include "TCRT5000.h"
#include <Arduino.h>

TCRT5000::TCRT5000(int pin, const char* sensorName, int threshold)
    : _pin(pin), _name(sensorName), _threshold(threshold),
      _lastReading(LOW), _healthy(true) {}

bool TCRT5000::initialize() {
    pinMode(_pin, INPUT);
    _healthy = true;
    return true;
}

void TCRT5000::update() {
    _lastReading = digitalRead(_pin);
    // Basic health check: if pin is not changing (stuck), could mark unhealthy
    // but for simplicity we keep healthy always true.
}

bool TCRT5000::healthy() const {
    return _healthy;
}

const char* TCRT5000::name() const {
    return _name;
}

void TCRT5000::shutdown() {
    // Nothing to release for simple GPIO sensor
}

int TCRT5000::read() const {
    return _lastReading;
}

bool TCRT5000::isLineDetected() const {
    // By convention, HIGH means line (black) detected.
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