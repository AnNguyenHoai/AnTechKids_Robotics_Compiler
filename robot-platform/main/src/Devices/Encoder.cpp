#include "Encoder.h"

const int8_t Encoder::TRANSITION_TABLE[16] = {
     0, -1,  1,  0,
     1,  0,  0, -1,
    -1,  0,  0,  1,
     0,  1, -1,  0
};

Encoder::Encoder(uint8_t pinA, uint8_t pinB, float countsPerRevolution)
    : _pinA(pinA), _pinB(pinB),
      _countsPerRevolution(countsPerRevolution > 0.0f ? countsPerRevolution : 1.0f) {}

bool Encoder::begin() {
    // GPIO34-39 are input-only and have no internal pull-up/pull-down.
    pinMode(_pinA, INPUT);
    pinMode(_pinB, INPUT);
    _state = (digitalRead(_pinA) ? 2 : 0) | (digitalRead(_pinB) ? 1 : 0);
    _lastSampleCount = _count;
    _lastSampleUs = micros();
    attachInterruptArg(_pinA, &Encoder::isrA, this, CHANGE);
    attachInterruptArg(_pinB, &Encoder::isrB, this, CHANGE);
    _started = true;
    return true;
}

void IRAM_ATTR Encoder::isrA(void* arg) { static_cast<Encoder*>(arg)->handleEdge(); }
void IRAM_ATTR Encoder::isrB(void* arg) { static_cast<Encoder*>(arg)->handleEdge(); }

void IRAM_ATTR Encoder::handleEdge() {
    const uint8_t current = (digitalRead(_pinA) ? 2 : 0) | (digitalRead(_pinB) ? 1 : 0);
    const uint8_t index = (_state << 2) | current;
    int8_t delta = TRANSITION_TABLE[index & 0x0F];
    if (_inverted) delta = -delta;
    _count += delta;
    _state = current;
}

void Encoder::update() {
    if (!_started) return;
    const uint32_t now = micros();
    const uint32_t elapsed = now - _lastSampleUs;
    if (elapsed < 1000) return; // avoid excessive noise; actual window is caller-driven
    noInterrupts();
    const int64_t current = _count;
    interrupts();
    _countsPerSecond = (float)(current - _lastSampleCount) * 1000000.0f / (float)elapsed;
    _lastSampleCount = current;
    _lastSampleUs = now;
}

int64_t Encoder::getCount() const { noInterrupts(); int64_t v = _count; interrupts(); return v; }
void Encoder::resetCount(int64_t value) { noInterrupts(); _count = value; interrupts(); _lastSampleCount = value; _countsPerSecond = 0.0f; _lastSampleUs = micros(); }
float Encoder::getCountsPerSecond() const { return _countsPerSecond; }
float Encoder::getRPM() const { return (_countsPerRevolution > 0.0f) ? (_countsPerSecond * 60.0f / _countsPerRevolution) : 0.0f; }
int Encoder::getDirection() const { return _countsPerSecond > 0.0f ? 1 : (_countsPerSecond < 0.0f ? -1 : 0); }
void Encoder::setCountsPerRevolution(float value) { if (value > 0.0f) _countsPerRevolution = value; }
float Encoder::getCountsPerRevolution() const { return _countsPerRevolution; }
void Encoder::setInverted(bool inverted) { _inverted = inverted; }
bool Encoder::isInverted() const { return _inverted; }
