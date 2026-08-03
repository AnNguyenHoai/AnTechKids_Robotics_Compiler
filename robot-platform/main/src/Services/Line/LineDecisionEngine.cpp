#include "LineDecisionEngine.h"

MotorCommand LineDecisionEngine::decide(LineState state) {
    switch (state) {
        case LineState::CENTER:
            return MotorCommand::FORWARD;
        case LineState::LEFT:
        case LineState::LEFT_CENTER:
            return MotorCommand::TURN_LEFT;
        case LineState::RIGHT:
        case LineState::CENTER_RIGHT:
            return MotorCommand::TURN_RIGHT;
        case LineState::LOST:
        case LineState::INTERSECTION:
        case LineState::UNKNOWN:
        default:
            return MotorCommand::STOP;
    }
}