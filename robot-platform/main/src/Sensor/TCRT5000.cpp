#include "TCRT5000.h"
#include <Arduino.h>

TCRT5000::TCRT5000(int pin, const char* sensorName)
    : _pin(pin), _name(sensorName), _lastReading(LOW), _healthy(true) {}

bool TCRT5000::initialize() {
    pinMode(_pin, INPUT);
    _healthy = true;
    return true;
}

void TCRT5000::update() {
    _lastReading = digitalRead(_pin);
    // (Optional) add basic sanity check: if pin stuck, mark unhealthy
}

bool TCRT5000::healthy() const {
    return _healthy;
}

const char* TCRT5000::name() const {
    return _name;
}

int TCRT5000::read() {
    return _lastReading;
}