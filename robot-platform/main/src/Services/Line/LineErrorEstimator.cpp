#include "LineErrorEstimator.h"

float LineErrorEstimator::estimate(LineState state) {
    switch (state) {
        // Negative error means the line is left of centre.
        case LineState::LEFT:
            return -1.0f;
        case LineState::LEFT_CENTER:
            return -0.5f;

        case LineState::CENTER:
            return 0.0f;

        // Positive error means the line is right of centre.
        case LineState::CENTER_RIGHT:
            return 0.5f;
        case LineState::RIGHT:
            return 1.0f;

        // Special states are handled by the follower state machine.
        case LineState::LOST:
        case LineState::INTERSECTION:
        case LineState::UNKNOWN:
        default:
            return 0.0f;
    }
}
