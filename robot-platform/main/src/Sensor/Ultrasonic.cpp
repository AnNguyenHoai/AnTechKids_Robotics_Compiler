#include "Ultrasonic.h"
#include "../HAL/HAL.h"
#include <Arduino.h>

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

    // H13 diagnostic trace:
    // Keep the measurement algorithm/timing unchanged. This instrumentation
    // records the trigger/pulseIn timing so timeout origin can be distinguished
    // from VM/API scheduling effects.
    static uint32_t traceSeq = 0;
    const uint32_t seq = ++traceSeq;

    const uint32_t triggerStartUs = HAL::getTime().micros();
    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::LOW_STATE);
    HAL::getTime().delayUs(2);

    const uint32_t triggerHighUs = HAL::getTime().micros();
    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::HIGH_STATE);
    HAL::getTime().delayUs(10);

    const uint32_t triggerEndUs = HAL::getTime().micros();
    HAL::getGPIO().digitalWrite(_trigPin, HAL::PinState::LOW_STATE);

    // Diagnostic-only: capture ECHO immediately before and after pulseIn().
    // Do not alter the pulse measurement algorithm or timeout.
    const int echoBefore = static_cast<int>(
        HAL::getGPIO().digitalRead(_echoPin) == HAL::PinState::HIGH_STATE
    );

    const uint32_t pulseStartUs = HAL::getTime().micros();
    const uint32_t duration =
        HAL::getPulse().pulseIn(_echoPin, HAL::PinState::HIGH_STATE, _timeoutUs);
    const uint32_t pulseEndUs = HAL::getTime().micros();

    const uint32_t triggerLowToHighUs = triggerHighUs - triggerStartUs;
    const uint32_t triggerHighWidthUs = triggerEndUs - triggerHighUs;
    const uint32_t pulseElapsedUs = pulseEndUs - pulseStartUs;
    const int echoAfter = static_cast<int>(
        HAL::getGPIO().digitalRead(_echoPin) == HAL::PinState::HIGH_STATE
    );

    Serial.printf(
        "[ULTRA-TRACE] seq=%lu trigStart=%lu trigHigh=%lu trigEnd=%lu "
        "trigLowToHigh=%lu trigHighWidth=%lu pulseStart=%lu pulseEnd=%lu "
        "pulseElapsed=%lu duration=%lu echoBefore=%d echoAfter=%d timeout=%lu\n",
        (unsigned long)seq,
        (unsigned long)triggerStartUs,
        (unsigned long)triggerHighUs,
        (unsigned long)triggerEndUs,
        (unsigned long)triggerLowToHighUs,
        (unsigned long)triggerHighWidthUs,
        (unsigned long)pulseStartUs,
        (unsigned long)pulseEndUs,
        (unsigned long)pulseElapsedUs,
        (unsigned long)duration,
        echoBefore,
        echoAfter,
        (unsigned long)_timeoutUs
    );


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