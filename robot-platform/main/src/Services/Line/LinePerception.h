#ifndef LINE_PERCEPTION_H
#define LINE_PERCEPTION_H

#include <stdint.h>
#include "LineState.h"

// Canonical three-channel line mask used by RobotAPI::GetTraceRaw(),
// LineSensorSnapshot, LineFollower and the VM GetTraceRaw opcode.
//
// The bit layout is intentionally independent from RoboSim's 1/2/3 channel
// numbering. Frontend channel normalization remains unchanged for the legacy
// per-channel getters.
namespace LineMask {
static constexpr uint8_t RIGHT = 0b001;
static constexpr uint8_t CENTER = 0b010;
static constexpr uint8_t LEFT = 0b100;
static constexpr uint8_t ALL = LEFT | CENTER | RIGHT;
}

class LinePerception {
public:
    static LineState interpret(uint8_t mask);
};

#endif // LINE_PERCEPTION_H