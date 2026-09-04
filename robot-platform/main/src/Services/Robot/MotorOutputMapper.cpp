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

} // namespace RobotAPI
