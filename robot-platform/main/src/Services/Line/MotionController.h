#ifndef MOTION_CONTROLLER_H
#define MOTION_CONTROLLER_H

#include <stdint.h>
#include "LineTypes.h"
#include "MotorMixer.h"
#include "PIDController.h"

/**
 * MotionController translates a MotionIntent into actual motor speeds.
 * For FOLLOW, it uses PID and MotorMixer.
 * For TURN_LEFT/RIGHT and STOP, it directly sets speeds.
 */
class MotionController {
public:
    MotionController();

    /**
     * Compute motor speeds for the given intent.
     * @param intent      The desired motion intent.
     * @param speed       Base speed (0-100) for forward/backward, used for FOLLOW and turns.
     * @param error       Error value for FOLLOW (from LineErrorEstimator). Ignored for other intents.
     * @return MotorOutput with left and right speeds clamped to [-100, 100].
     */
    MotorOutput compute(MotionIntent intent, int speed, float error = 0.0f);

    // PID tuning access
    void setPIDGains(float kp, float ki, float kd);
    void setPIDLimits(float min, float max);
    void resetPID();

private:
    PIDController _pid;
};

#endif