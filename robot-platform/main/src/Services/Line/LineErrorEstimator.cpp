#include "LineErrorEstimator.h"

float LineErrorEstimator::estimate(LineState state) {
    switch (state) {
        // Left side: negative error (turn left)
        case LineState::LEFT:
        case LineState::LEFT_CENTER:
            return -1.0f;

        // Center: zero error (straight)
        case LineState::CENTER:
            return 0.0f;

        // Right side: positive error (turn right)
        case LineState::RIGHT:
        case LineState::CENTER_RIGHT:
            return 1.0f;

        // Special states: fallback to straight (decision handled elsewhere)
        case LineState::LOST:
        case LineState::INTERSECTION:
        case LineState::UNKNOWN:
        default:
            return 0.0f;
    }
}