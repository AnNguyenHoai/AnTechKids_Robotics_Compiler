#include "MotionController.h"

MotionController::MotionController()
    : _pid(1.2f, 0.02f, 0.5f, 0.02f) {
    _pid.setLimits(-100, 100);
}

MotorOutput MotionController::compute(MotionIntent intent, int speed, float error) {
    switch (intent) {
        case MotionIntent::FOLLOW: {
            float correction = _pid.update(error);
            return MotorMixer::mix(speed, correction);
        }
        case MotionIntent::TURN_LEFT: {
            MotorOutput out;
            out.left  = -speed;
            out.right =  speed;
            return out;
        }
        case MotionIntent::TURN_RIGHT: {
            MotorOutput out;
            out.left  =  speed;
            out.right = -speed;
            return out;
        }
        case MotionIntent::STOP:
        default:
            return MotorMixer::mix(0, 0); // returns (0,0)
    }
}

void MotionController::setPIDGains(float kp, float ki, float kd) {
    _pid.setGains(kp, ki, kd);
}

void MotionController::setPIDLimits(float min, float max) {
    _pid.setLimits(min, max);
}

void MotionController::resetPID() {
    _pid.reset();
}