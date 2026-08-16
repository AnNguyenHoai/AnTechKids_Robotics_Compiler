#include "HeadingController.h"
#include <math.h>
#include <Arduino.h>

HeadingController::HeadingController()
    : _kp(1.0f), _ki(0.0f), _kd(0.0f), _maxCorrection(20.0f),
      _targetHeading(0.0f), _active(false), _lastError(0.0f),
      _lastCorrection(0.0f), _pidInitialized(false),
      _firstUpdate(true), _lastTimestamp(0) {}

void HeadingController::init(float kp, float ki, float kd, float maxCorrection) {
    _kp = kp;
    _ki = ki;
    _kd = kd;
    _maxCorrection = maxCorrection;
    _pid.setGains(kp, ki, kd);
    _pid.setDt(0.01f);
    _pid.setLimits(-maxCorrection, maxCorrection);
    _pidInitialized = true;
    reset();
}

void HeadingController::start(float currentHeading) {
    _targetHeading = currentHeading;
    reset();
    _active = true;
}

float HeadingController::update(float currentHeading, uint32_t timestamp) {
    if (!_active || !_pidInitialized) {
        _lastCorrection = 0.0f;
        return 0.0f;
    }

    // ---- Timing ----
    float dt = 0.01f;
    if (_firstUpdate) {
        // First update: only establish timestamp, do NOT integrate
        _firstUpdate = false;
        _lastTimestamp = timestamp;
        _lastCorrection = 0.0f;
        return 0.0f;
    }

    if (timestamp > _lastTimestamp) {
        uint32_t dtMs = timestamp - _lastTimestamp;
        dt = dtMs / 1000.0f;
        if (dt > 0.1f) dt = 0.1f;  // clamp to prevent huge jumps
        _lastTimestamp = timestamp;
    } else {
        // Invalid dt (timestamp not advancing)
        _lastCorrection = 0.0f;
        return 0.0f;
    }

    // ---- Heading error ----
    float rawError = _targetHeading - currentHeading;
    float error = normalizeAngle(rawError);
    _lastError = error;

    // ---- PID update ----
    _pid.setDt(dt);
    float correction = _pid.update(error);
    if (correction > _maxCorrection) correction = _maxCorrection;
    if (correction < -_maxCorrection) correction = -_maxCorrection;
    _lastCorrection = correction;

    return correction;
}

void HeadingController::stop() {
    _active = false;
    reset();
}

void HeadingController::reset() {
    _pid.reset();
    _lastError = 0.0f;
    _lastCorrection = 0.0f;
    _firstUpdate = true;
    _lastTimestamp = 0;
}

float HeadingController::normalizeAngle(float angle) {
    while (angle > 180.0f) angle -= 360.0f;
    while (angle < -180.0f) angle += 360.0f;
    return angle;
}