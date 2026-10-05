#include "LineErrorEstimator.h"
#include "LineSensorLayout.h"

float LineErrorEstimator::estimate(uint8_t mask) {
    mask = LineSensorLayout::sanitizeMask(mask);
    if (mask == 0) return 0.0f;

    float weightedSum = 0.0f;
    int activeCount = 0;

    if (mask & LineSensorLayout::MASK_FAR_LEFT)  { weightedSum += -2.0f; activeCount++; }
    if (mask & LineSensorLayout::MASK_LEFT)      { weightedSum += -1.0f; activeCount++; }
    if (mask & LineSensorLayout::MASK_CENTER)    { weightedSum +=  0.0f; activeCount++; }
    if (mask & LineSensorLayout::MASK_RIGHT)     { weightedSum +=  1.0f; activeCount++; }
    if (mask & LineSensorLayout::MASK_FAR_RIGHT) { weightedSum +=  2.0f; activeCount++; }

    return activeCount > 0 ? (weightedSum / static_cast<float>(activeCount)) : 0.0f;
}