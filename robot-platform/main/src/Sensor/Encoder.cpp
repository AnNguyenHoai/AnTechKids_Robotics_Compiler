#include "Encoder.h"
#include "QuadratureDecoder.h"
#include <Arduino.h>
#include <esp32-hal-gpio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/portmacro.h>

namespace {
portMUX_TYPE g_encoderMux = portMUX_INITIALIZER_UNLOCKED;
}

Encoder::Encoder(int pinA, int pinB, const char* sensorName,
                 float countsPerRevolution, bool invertDirection)
    : _pinA(pinA),
      _pinB(pinB),
      _name(sensorName),
      _countsPerRevolution(countsPerRevolution > 0.0f ? countsPerRevolution : 1.0f),
      _invertDirection(invertDirection),
      _count(0),
      _lastState(0),
      _lastEdgeMicros(0),
      _initialized(false),
      _lastSampleCount(0),
      _lastSampleMicros(0),
      _countsPerSecond(0.0f),
      _healthy(false) {}

bool Encoder::initialize() {
    pinMode(_pinA, INPUT);
    pinMode(_pinB, INPUT);

    const int a = digitalRead(_pinA) ? 1 : 0;
    const int b = digitalRead(_pinB) ? 1 : 0;

    portENTER_CRITICAL(&g_encoderMux);
    _count = 0;
    _lastState = (a << 1) | b;
    _lastEdgeMicros = micros();
    _initialized = true;
    portEXIT_CRITICAL(&g_encoderMux);

    _lastSampleCount = 0;
    _lastSampleMicros = micros();
    _countsPerSecond = 0.0f;

    attachInterruptArg(_pinA, _handleInterruptA, this, CHANGE);
    attachInterruptArg(_pinB, _handleInterruptB, this, CHANGE);

    _healthy = true;
    return true;
}

void Encoder::update() {
    if (!_initialized) {
        _healthy = false;
        return;
    }

    const uint32_t now = micros();
    int64_t count;
    uint32_t lastEdge;
    _snapshot(count, lastEdge);

    const uint32_t dt = now - _lastSampleMicros;
    if (dt == 0) {
        return;
    }

    const int64_t delta = count - _lastSampleCount;
    _countsPerSecond = (static_cast<float>(delta) * 1000000.0f) / static_cast<float>(dt);

    _lastSampleCount = count;
    _lastSampleMicros = now;
    (void)lastEdge;
    _healthy = true;
}

bool Encoder::healthy() const {
    return _healthy && _initialized;
}

const char* Encoder::name() const {
    return _name;
}

void Encoder::shutdown() {
    detachInterrupt(_pinA);
    detachInterrupt(_pinB);
    portENTER_CRITICAL(&g_encoderMux);
    _initialized = false;
    portEXIT_CRITICAL(&g_encoderMux);
    _countsPerSecond = 0.0f;
    _healthy = false;
}

int64_t Encoder::getCount() const {
    int64_t count;
    uint32_t unused;
    _snapshot(count, unused);
    return count;
}

void Encoder::resetCount(int64_t value) {
    portENTER_CRITICAL(&g_encoderMux);
    _count = value;
    portEXIT_CRITICAL(&g_encoderMux);
    _lastSampleCount = value;
    _lastSampleMicros = micros();
    _countsPerSecond = 0.0f;
}

int Encoder::direction() const {
    const float speed = _countsPerSecond;
    if (speed > 0.0f) return 1;
    if (speed < 0.0f) return -1;
    return 0;
}

float Encoder::getCountsPerSecond() const {
    return _countsPerSecond;
}

float Encoder::getRPM() const {
    if (_countsPerRevolution <= 0.0f) return 0.0f;
    return (_countsPerSecond * 60.0f) / _countsPerRevolution;
}

float Encoder::getCountsPerRevolution() const {
    return _countsPerRevolution;
}

void Encoder::setCountsPerRevolution(float value) {
    if (value > 0.0f) {
        _countsPerRevolution = value;
    }
}

int Encoder::pinA() const { return _pinA; }
int Encoder::pinB() const { return _pinB; }

void IRAM_ATTR Encoder::_handleInterruptA(void* context) {
    static_cast<Encoder*>(context)->_handleEdge();
}

void IRAM_ATTR Encoder::_handleInterruptB(void* context) {
    static_cast<Encoder*>(context)->_handleEdge();
}

void IRAM_ATTR Encoder::_handleEdge() {
    if (!_initialized) return;

    const int a = digitalRead(_pinA) ? 1 : 0;
    const int b = digitalRead(_pinB) ? 1 : 0;
    const int currentState = (a << 1) | b;

    const int8_t step = QuadratureDecoder::transition(_lastState, currentState);

    portENTER_CRITICAL_ISR(&g_encoderMux);
    if (step != 0) {
        _count += _invertDirection ? -step : step;
        _lastEdgeMicros = micros();
    }
    _lastState = currentState;
    portEXIT_CRITICAL_ISR(&g_encoderMux);
}

void Encoder::_snapshot(int64_t& count, uint32_t& lastEdgeMicros) const {
    portENTER_CRITICAL(&g_encoderMux);
    count = _count;
    lastEdgeMicros = _lastEdgeMicros;
    portEXIT_CRITICAL(&g_encoderMux);
}
