#ifndef LINE_ERROR_ESTIMATOR_H
#define LINE_ERROR_ESTIMATOR_H

#include <stdint.h>

/**
 * LineErrorEstimator
 *
 * Converts the canonical five-bit line mask into a continuous position error.
 * Spatial mask order is FL/L/C/R/FR with weights -2/-1/0/+1/+2.
 *
 * This is the single source of truth for steering error calculation.
 */
class LineErrorEstimator {
public:
    /**
     * Estimate line position from all active sensors.
     *
     * @param mask canonical 5-bit mask: bit4=FL ... bit0=FR
     * @return weighted average in [-2.0, +2.0]; 0.0 for LOST
     */
    static float estimate(uint8_t mask);
};

#endif // LINE_ERROR_ESTIMATOR_H