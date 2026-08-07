#ifndef PID_CONTROLLER_H
#define PID_CONTROLLER_H

#include <stdint.h>

class PIDController {
public:
    PIDController(float kp = 1.0f, float ki = 0.0f, float kd = 0.0f, float dt = 0.02f);

    void reset();
    float update(float error);
    void setGains(float kp, float ki, float kd);
    void setDt(float dt);
    void setLimits(float minOut, float maxOut);

private:
    float _kp, _ki, _kd;
    float _dt;
    float _minOut, _maxOut;
    float _integral;
    float _prevError;
    bool _initialized;
};

#endif