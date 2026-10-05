#include "LinePerception.h"
#include "LineErrorEstimator.h"
#include "LineSensorLayout.h"

LineState LinePerception::interpret(uint8_t mask) {
    mask = LineSensorLayout::sanitizeMask(mask);

    if (mask == 0) {
        return LineState::LOST;
    }
    if (LineSensorLayout::isIntersectionCandidate(mask)) {
        return LineState::INTERSECTION;
    }

    const float error = LineErrorEstimator::estimate(mask);
    if (error <= -0.75f) return LineState::LEFT;
    if (error < 0.0f)    return LineState::LEFT_CENTER;
    if (error >= 0.75f)  return LineState::RIGHT;
    if (error > 0.0f)    return LineState::CENTER_RIGHT;
    return LineState::CENTER;
}