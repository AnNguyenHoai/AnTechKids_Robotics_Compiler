#ifndef LINE_TYPES_H
#define LINE_TYPES_H

#include <stdint.h>

/**
 * MotionIntent represents the high-level action the robot should take.
 * It is produced by the FollowerStateMachine and consumed by the MotionController.
 */
enum class MotionIntent : uint8_t {
    FOLLOW,     // Normal line following with PID
    TURN_LEFT,  // Rotate left at current speed
    TURN_RIGHT, // Rotate right at current speed
    STOP,       // Stop motors
    RECOVER     // Use recovery strategy to find the line
};

#endif // LINE_TYPES_H