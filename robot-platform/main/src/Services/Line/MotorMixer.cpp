#include "MotorMixer.h"

MotorOutput MotorMixer::mix(int baseSpeed, float correction, float scaleFactor) {
    // Clamp baseSpeed to valid range
    if (baseSpeed > 100) baseSpeed = 100;
    if (baseSpeed < 0) baseSpeed = 0;

    // Compute motor speeds
    int left = baseSpeed - (int)(correction * scaleFactor);
    int right = baseSpeed + (int)(correction * scaleFactor);

    // Clamp to motor limits
    if (left > 100) left = 100;
    if (left < -100) left = -100;
    if (right > 100) right = 100;
    if (right < -100) right = -100;

    MotorOutput output;
    output.left = left;
    output.right = right;
    return output;
}