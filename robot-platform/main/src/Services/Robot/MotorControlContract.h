#pragma once

#include <stdint.h>

namespace RobotAPI {

/**
 * H23-A motor control contract.
 *
 * Domain ownership:
 *   Application/behavior -> logical motor command [-100, 100]
 *   RobotAPI::_setMotors -> single owner of speedScale + per-motor calibration
 *   RobotAPI::_setMotorsRaw -> raw direction/PWM conversion only
 *
 * No caller may pre-apply or invert motor calibration before calling
 * RobotAPI::setMotorsDirect() / SetMotorSpeed().
 */
constexpr int MOTOR_LOGICAL_MIN = -100;
constexpr int MOTOR_LOGICAL_MAX = 100;
constexpr int MOTOR_STOP = 0;

inline int clampLogicalMotorCommand(int speed) {
    return speed < MOTOR_LOGICAL_MIN ? MOTOR_LOGICAL_MIN
         : speed > MOTOR_LOGICAL_MAX ? MOTOR_LOGICAL_MAX
         : speed;
}

} // namespace RobotAPI
