#include "MotorOutputMapper.h"
#include "MotorControlContract.h"
#include <math.h>

namespace RobotAPI {

int MotorOutputMapper::mapMagnitude(int logicalMagnitude, float scale, int minDrive) {
    if (logicalMagnitude <= 0) {
        return 0;
    }

    if (logicalMagnitude > MOTOR_LOGICAL_MAX) {
        logicalMagnitude = MOTOR_LOGICAL_MAX;
    }
    if (scale < 0.0f) {
        scale = 0.0f;
    }

    // Calibration remains in the logical domain. A non-zero command is then
    // mapped to the physical run range so it cannot fall below minDrive.
    float calibrated = logicalMagnitude * scale;
    if (calibrated < 1.0f) {
        calibrated = 1.0f;
    }
    if (calibrated > 100.0f) {
        calibrated = 100.0f;
    }

    if (minDrive < 0) minDrive = 0;
    if (minDrive > 100) minDrive = 100;

    const float mapped = minDrive
        + ((calibrated - 1.0f) * (100.0f - minDrive) / 99.0f);

    return (int)lroundf(mapped);
}

int MotorOutputMapper::map(int logicalSpeed, float speedScale, float motorScale, int minDrive) {
    logicalSpeed = clampLogicalMotorCommand(logicalSpeed);
    if (logicalSpeed == MOTOR_STOP) {
        return MOTOR_STOP;
    }

    const int sign = logicalSpeed < 0 ? -1 : 1;
    const int magnitude = logicalSpeed < 0 ? -logicalSpeed : logicalSpeed;
    const float combinedScale = speedScale * motorScale;

    return sign * mapMagnitude(magnitude, combinedScale, minDrive);
}

void MotorOutputMapper::mapSteeringPair(
    int logicalLeft,
    int logicalRight,
    float speedScale,
    float leftMotorScale,
    float rightMotorScale,
    int minDrive,
    int& mappedLeft,
    int& mappedRight)
{
    logicalLeft = clampLogicalMotorCommand(logicalLeft);
    logicalRight = clampLogicalMotorCommand(logicalRight);

    // Line5 deliberately does NOT use the general-motion [minDrive,100]
    // remap. Real-robot measurements show ~65 is needed to start from rest,
    // but once moving the motors can run lower (L~40, R~50). Lifting every
    // steering command into [65,100] destroys speed resolution and produces
    // limit-cycle zigzag. Startup torque is handled separately by RobotAPI.
    (void)speedScale;
    (void)minDrive;

    if (leftMotorScale < 0.0f) leftMotorScale = 0.0f;
    if (rightMotorScale < 0.0f) rightMotorScale = 0.0f;

    auto mapLineSide = [](int logical, float motorScale) -> int {
        if (logical == MOTOR_STOP) return MOTOR_STOP;

        float calibrated = (float)(logical < 0 ? -logical : logical) * motorScale;
        if (calibrated > 100.0f) calibrated = 100.0f;

        int magnitude = (int)lroundf(calibrated);
        if (magnitude < 0) magnitude = 0;
        if (magnitude > 100) magnitude = 100;

        return logical < 0 ? -magnitude : magnitude;
    };

    mappedLeft = mapLineSide(logicalLeft, leftMotorScale);
    mappedRight = mapLineSide(logicalRight, rightMotorScale);
}

namespace {
constexpr int LEFT_RUN_MIN = 40;
constexpr int RIGHT_RUN_MIN = 50;
constexpr int RESTART_BOOST = 65;
constexpr uint32_t RESTART_BOOST_MS = 60;

int sustainableCommand(int requested, int runMin, int otherRequested, int otherRunMin) {
    if (requested == 0) return 0;
    const int magnitude = requested < 0 ? -requested : requested;
    const int otherMagnitude = otherRequested < 0 ? -otherRequested : otherRequested;
    // A weak inner wheel would hum without turning. Stop it and let the
    // sufficiently driven outer wheel pivot the chassis.
    if (magnitude < runMin && otherMagnitude >= otherRunMin) return 0;
    const int sustainable = magnitude < runMin ? runMin : magnitude;
    return requested < 0 ? -sustainable : sustainable;
}

} // namespace

void LineMotorOperatingPolicy::reset() {
    _left = Wheel{};
    _right = Wheel{};
}

void LineMotorOperatingPolicy::apply(int requestedLeft, int requestedRight,
                                    uint32_t nowMs, int& outputLeft, int& outputRight) {
    const int left = sustainableCommand(requestedLeft, LEFT_RUN_MIN,
                                        requestedRight, RIGHT_RUN_MIN);
    const int right = sustainableCommand(requestedRight, RIGHT_RUN_MIN,
                                         requestedLeft, LEFT_RUN_MIN);
    auto assistRestart = [nowMs](int target, Wheel& wheel) -> int {
        if (target == 0) {
            wheel.running = false;
            wheel.restartAtMs = 0;
            return 0;
        }
        if (!wheel.running) {
            wheel.running = true;
            wheel.restartAtMs = nowMs;
        }
        if ((uint32_t)(nowMs - wheel.restartAtMs) < RESTART_BOOST_MS) {
            const int magnitude = target < 0 ? -target : target;
            if (magnitude < RESTART_BOOST) return target < 0 ? -RESTART_BOOST : RESTART_BOOST;
        }
        return target;
    };
    outputLeft = assistRestart(left, _left);
    outputRight = assistRestart(right, _right);
}

} // namespace RobotAPI
