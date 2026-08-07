#include "PIDController.h"

PIDController::PIDController(float kp, float ki, float kd, float dt)
    : _kp(kp), _ki(ki), _kd(kd), _dt(dt),
      _minOut(-100.0f), _maxOut(100.0f),
      _integral(0.0f), _prevError(0.0f), _initialized(false) {}

void PIDController::reset() {
    _integral = 0.0f;
    _prevError = 0.0f;
    _initialized = false;
}

void PIDController::setGains(float kp, float ki, float kd) {
    _kp = kp; _ki = ki; _kd = kd;
}

void PIDController::setDt(float dt) {
    _dt = dt;
}

void PIDController::setLimits(float minOut, float maxOut) {
    _minOut = minOut;
    _maxOut = maxOut;
}

float PIDController::update(float error) {
    float p = _kp * error;

    _integral += error * _dt;
    float i = _ki * _integral;

    float d = 0.0f;
    if (_initialized) {
        d = _kd * (error - _prevError) / _dt;
    }
    _prevError = error;
    _initialized = true;

    float output = p + i + d;
    if (output > _maxOut) output = _maxOut;
    else if (output < _minOut) output = _minOut;

    // Anti‑windup
    if (output >= _maxOut || output <= _minOut) {
        _integral -= error * _dt;
    }

    return output;
}