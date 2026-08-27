#ifndef MOTOR_MIXER_H
#define MOTOR_MIXER_H

#include <stdint.h>

/**
 * MotorOutput
 * 
 * Container for left and right motor speeds.
 */
struct MotorOutput {
    int left;   // [-100, 100]
    int right;  // [-100, 100]
};

/**
 * MotorMixer
 * 
 * Responsibility: Convert base speed and PID correction to left/right motor speeds.
 * Used by LineFollower for line-following control.
 * 
 * Note: This mixer is NOT used by Heading Hold Controller, which has its own
 * direction-aware mixing logic in RobotAPI.
 * 
 * Mixing rule:
 *   left  = baseSpeed - correction * scaleFactor
 *   right = baseSpeed + correction * scaleFactor
 * 
 * Results are clamped to [-100, 100].
 */
class MotorMixer {
public:
    /**
     * Mix base speed and correction into left/right motor speeds.
     * 
     * @param baseSpeed     Desired forward speed (0-100)
     * @param correction    PID correction output (can be negative)
     * @param scaleFactor   Scaling factor for correction (default 0.8)
     * @return              MotorOutput with clamped speeds
     */
    static MotorOutput mix(int baseSpeed, float correction, float scaleFactor = 15.0f);
};

#endif // MOTOR_MIXER_H