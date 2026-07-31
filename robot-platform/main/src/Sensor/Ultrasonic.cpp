#include "Ultrasonic.h"
#include <Arduino.h>

Ultrasonic::Ultrasonic(int trigPin, int echoPin, uint32_t timeoutUs, const char* name)
    : _trigPin(trigPin), _echoPin(echoPin), _timeoutUs(timeoutUs),
      _name(name), _lastDistance(-1.0f), _healthy(true), _initialized(false),
      _consecutiveTimeouts(0) {}

bool Ultrasonic::initialize() {
    pinMode(_trigPin, OUTPUT);
    pinMode(_echoPin, INPUT);
    digitalWrite(_trigPin, LOW);
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

    // Send trigger pulse
    digitalWrite(_trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(_trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(_trigPin, LOW);

    // Measure echo pulse
    unsigned long duration = pulseIn(_echoPin, HIGH, _timeoutUs);

    if (duration == 0) {
        // Timeout: no obstacle detected
        _lastDistance = -1.0f;
        _consecutiveTimeouts++;

        // Health logic: too many timeouts in a row = sensor disconnected / faulty
        if (_consecutiveTimeouts >= MAX_CONSECUTIVE_TIMEOUTS) {
            _healthy = false;
        }
        // Note: we keep _healthy true for the first few timeouts
    } else {
        // Valid reading: reset timeout counter and mark healthy
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

void Ultrasonic::shutdown() {
    // Nothing to release for GPIO sensor
}

float Ultrasonic::distanceCm() const {
    return _lastDistance;
}

float Ultrasonic::maxRangeCm() const {
    return 400.0f;  // HC-SR04 typical max range
}

const char* Ultrasonic::unit() const {
    return "cm";
}