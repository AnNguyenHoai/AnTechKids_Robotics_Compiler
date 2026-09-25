#include "MotorMixer.h"
#include <math.h>

MotorOutput MotorMixer::mix(int baseSpeed, float correction, float scaleFactor) {
    if (baseSpeed > 100) baseSpeed = 100;
    if (baseSpeed < 0) baseSpeed = 0;

    // Steering convention is shared with RobotAPI::TurnLeft/TurnRight:
    //   positive correction -> steer RIGHT -> left motor faster than right
    //   negative correction -> steer LEFT  -> right motor faster than left
    // Keep the correction in floating point until the final motor conversion.
    float delta = correction * scaleFactor;
    int left = (int)lroundf((float)baseSpeed + delta);
    int right = (int)lroundf((float)baseSpeed - delta);

    if (left > 100) left = 100;
    if (left < -100) left = -100;
    if (right > 100) right = 100;
    if (right < -100) right = -100;

    return MotorOutput{left, right};
}
