#ifndef HEADING_ESTIMATOR_H
#define HEADING_ESTIMATOR_H

#include <stdint.h>
#include "../../Sensor/IMUSensor.h"

class HeadingEstimator {
public:
    HeadingEstimator();

    void reset();
    bool update(const IMUSample& sample);

    float getHeadingDeg() const;
    bool isInitialized() const { return _initialized; }
    float getLastDt() const { return _lastDt; }
    float getLastGyroZ() const { return _lastGyroZ; }
    uint32_t getLastTimestamp() const { return _lastTimestamp; }

private:
    float _headingDeg;
    bool _initialized;
    uint32_t _prevTimestamp;
    float _lastDt;
    float _lastGyroZ;
    uint32_t _lastTimestamp;

    static constexpr float MAX_DT = 0.1f;
};

#endif // HEADING_ESTIMATOR_H