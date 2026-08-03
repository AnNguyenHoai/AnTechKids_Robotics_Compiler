#ifndef SENSOR_STATISTICS_H
#define SENSOR_STATISTICS_H

#include <stdint.h>

struct SensorStatistics {
    uint32_t readCount = 0;
    uint32_t highCount = 0;
    uint32_t lowCount = 0;
    uint32_t transitionCount = 0;
    uint32_t lastTransitionTime = 0;
    float stability = 100.0f;
};

#endif