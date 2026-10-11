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

    if (logicalLeft == MOTOR_STOP && logicalRight == MOTOR_STOP) {
        mappedLeft = MOTOR_STOP;
        mappedRight = MOTOR_STOP;
        return;
    }

    if (minDrive < 0) minDrive = 0;
    if (minDrive > 100) minDrive = 100;
    if (speedScale < 0.0f) speedScale = 0.0f;
    if (leftMotorScale < 0.0f) leftMotorScale = 0.0f;
    if (rightMotorScale < 0.0f) rightMotorScale = 0.0f;

    auto calibratedMagnitude = [&](int logical, float motorScale) -> float {
        if (logical == MOTOR_STOP) return 0.0f;
        float magnitude = (float)(logical < 0 ? -logical : logical);
        float calibrated = magnitude * speedScale * motorScale;
        // Preserve H23-B's non-zero run guarantee even when calibration is tiny.
        if (calibrated < 1.0f) calibrated = 1.0f;
        if (calibrated > 100.0f) calibrated = 100.0f;
        return calibrated;
    };

    const float leftCal = calibratedMagnitude(logicalLeft, leftMotorScale);
    const float rightCal = calibratedMagnitude(logicalRight, rightMotorScale);
    const float maxCal = leftCal > rightCal ? leftCal : rightCal;

    if (maxCal <= 0.0f) {
        mappedLeft = mappedRight = MOTOR_STOP;
        return;
    }

    // Only the dominant wheel is lifted into the measured start/run range.
    // The inner wheel MUST preserve the steering ratio all the way toward zero.
    // Physical tests show both TT motors need about 65 to start from rest, but
    // once moving they can continue below that threshold (L~40, R~50). Flooring
    // both wheels to minDrive destroys sharp-turn authority (e.g. 84/36 became
    // 94/65). Keeping the dominant wheel >= minDrive guarantees propulsion/
    // restart while allowing the inner wheel to slow deeply or stop for turns.
    const int dominantLogical = (int)lroundf(maxCal);
    const int dominantMapped = mapMagnitude(dominantLogical, 1.0f, minDrive);

    auto mapSide = [&](int logical, float calibrated) -> int {
        if (logical == MOTOR_STOP) return MOTOR_STOP;

        int magnitude = (int)lroundf((float)dominantMapped * (calibrated / maxCal));
        if (magnitude < 0) magnitude = 0;
        if (magnitude > 100) magnitude = 100;

        return logical < 0 ? -magnitude : magnitude;
    };

    mappedLeft = mapSide(logicalLeft, leftCal);
    mappedRight = mapSide(logicalRight, rightCal);
}

} // namespace RobotAPI
