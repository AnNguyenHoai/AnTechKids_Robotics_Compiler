#ifndef LINE_CONTEXT_H
#define LINE_CONTEXT_H

#include <stdint.h>
#include "LineState.h"
#include "LineDecisionEngine.h"

/**
 * LineContext holds all data for a single line-following tick.
 * It is created once per iteration from fresh sensor data
 * and then reused across layers.
 */
struct LineContext {
    uint8_t mask;                 // raw sensor mask (3 bits)
    LineState state;              // interpreted state
    MotorCommand command;         // decision result
};

#endif // LINE_CONTEXT_H