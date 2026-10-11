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

constexpr int INNER_FLOOR_MARGIN = 12;

// Preserve the commanded outer/inner ordering instead of naively applying
// two independent floors, which can invert yaw when L=48/R=40.
void sustainablePair(int left, int right, int& outputLeft, int& outputRight) {
    const int leftMag = left < 0 ? -left : left;
    const int rightMag = right < 0 ? -right : right;
    if (leftMag == 0 && rightMag == 0) {
        outputLeft = outputRight = 0;
        return;
    }
    if (leftMag == rightMag && leftMag != 0) {
        // Straight motion and same-magnitude opposite-direction turns must not
        // acquire an artificial left/right imbalance from unlike motor floors.
        const int equalFloor = RIGHT_RUN_MIN;
        const int common = leftMag < equalFloor ? equalFloor : leftMag;
        outputLeft = left < 0 ? -common : common;
        outputRight = right < 0 ? -common : common;
        return;
    }
    const bool leftOuter = leftMag > rightMag;
    const int outerRequested = leftOuter ? leftMag : rightMag;
    const int innerRequested = leftOuter ? rightMag : leftMag;
    const int outerFloor = leftOuter ? LEFT_RUN_MIN : RIGHT_RUN_MIN;
    const int innerFloor = leftOuter ? RIGHT_RUN_MIN : LEFT_RUN_MIN;
    const int outer = outerRequested < outerFloor ? outerFloor : outerRequested;

    int inner = innerRequested;
    if (inner != 0 && inner < innerFloor) {
        // Small steering differences: keep the inner wheel moving reliably.
        // Strong steering or a floor that would invert yaw: true inner stop.
        inner = (inner + INNER_FLOOR_MARGIN >= innerFloor && outer > innerFloor)
                    ? innerFloor : 0;
    }
    const int leftOutputMag = leftOuter ? outer : inner;
    const int rightOutputMag = leftOuter ? inner : outer;
    outputLeft = left < 0 ? -leftOutputMag : leftOutputMag;
    outputRight = right < 0 ? -rightOutputMag : rightOutputMag;
}

} // namespace

void LineMotorOperatingPolicy::reset() {
    _left = Wheel{};
    _right = Wheel{};
}

void LineMotorOperatingPolicy::apply(int requestedLeft, int requestedRight,
                                    uint32_t nowMs, int& outputLeft, int& outputRight) {
    int left = 0;
    int right = 0;
    sustainablePair(requestedLeft, requestedRight, left, right);
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
