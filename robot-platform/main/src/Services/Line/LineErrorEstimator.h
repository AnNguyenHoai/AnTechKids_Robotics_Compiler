#ifndef LINE_ERROR_ESTIMATOR_H
#define LINE_ERROR_ESTIMATOR_H

#include "LineState.h"

/**
 * LineErrorEstimator
 * 
 * Responsibility: Convert semantic LineState to a continuous error value.
 * 
 * This is the SINGLE SOURCE OF TRUTH for error calculation.
 * No other module should compute error from mask or state.
 * 
 * Error Convention:
 *   LEFT, LEFT_CENTER  -> -1.0  (turn left)
 *   CENTER             ->  0.0  (straight)
 *   RIGHT, CENTER_RIGHT -> +1.0 (turn right)
 *   LOST, INTERSECTION ->  0.0  (fallback)
 */
class LineErrorEstimator {
public:
    /**
     * Convert a LineState to a continuous error value in [-1.0, 1.0].
     * 
     * @param state  Semantic state from LinePerception
     * @return       Error value: negative = turn left, positive = turn right
     */
    static float estimate(LineState state);
};

#endif // LINE_ERROR_ESTIMATOR_H