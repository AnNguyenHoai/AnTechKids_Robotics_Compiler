#include "HeadingEstimator.h"

HeadingEstimator::HeadingEstimator()
    : _headingDeg(0.0f), _initialized(false), _prevTimestamp(0),
      _lastDt(0.0f), _lastGyroZ(0.0f), _lastTimestamp(0) {}

void HeadingEstimator::reset() {
    _headingDeg = 0.0f;
    _initialized = false;
    _prevTimestamp = 0;
    _lastDt = 0.0f;
    _lastGyroZ = 0.0f;
    _lastTimestamp = 0;
}

bool HeadingEstimator::update(const IMUSample& sample) {
    if (!sample.valid) return false;

    if (!_initialized) {
        _prevTimestamp = sample.timestamp;
        _lastTimestamp = sample.timestamp;
        _initialized = true;
        return false;
    }

    uint32_t dtMs = sample.timestamp - _prevTimestamp;
    if (dtMs == 0) return false;

    float dtSec = dtMs / 1000.0f;
    if (dtSec > MAX_DT) {
        _prevTimestamp = sample.timestamp;
        _lastTimestamp = sample.timestamp;
        _lastDt = dtSec;
        _lastGyroZ = sample.gyro.gz;
        return false;
    }

    float gyroZ = sample.gyro.gz;
    _headingDeg += gyroZ * dtSec;

    _lastDt = dtSec;
    _lastGyroZ = gyroZ;
    _lastTimestamp = sample.timestamp;
    _prevTimestamp = sample.timestamp;

    return true;
}

float HeadingEstimator::getHeadingDeg() const {
    return _headingDeg;
}