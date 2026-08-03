#ifndef LINE_DECISION_ENGINE_H
#define LINE_DECISION_ENGINE_H

#include <stdint.h>
#include "LineState.h"

enum class MotorCommand : uint8_t {
    FORWARD,
    TURN_LEFT,
    TURN_RIGHT,
    STOP
};

class LineDecisionEngine {
public:
    static MotorCommand decide(LineState state);
};

#endif // LINE_DECISION_ENGINE_H