#include "MotorMixer.h"
#include <math.h>

MotorOutput MotorMixer::mix(int baseSpeed, float correction, float scaleFactor) {
    if (baseSpeed > 100) baseSpeed = 100;
    if (baseSpeed < 0) baseSpeed = 0;

    // Preserve the correction until the final motor conversion.  The old
    // implementation truncated correction*0.8 to int, so normal line errors
    // frequently produced 0 and both motors stayed at the same speed.
    float delta = correction * scaleFactor;
    // Error convention: negative = line left, positive = line right.
    // For differential drive, a positive correction must yaw the robot right:
    // left wheel faster, right wheel slower. Negative correction mirrors this.
    int left = (int)lroundf((float)baseSpeed + delta);
    int right = (int)lroundf((float)baseSpeed - delta);

    if (left > 100) left = 100;
    if (left < -100) left = -100;
    if (right > 100) right = 100;
    if (right < -100) right = -100;

    return MotorOutput{left, right};
}
