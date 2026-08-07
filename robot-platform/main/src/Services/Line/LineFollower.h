#ifndef LINE_FOLLOWER_H
#define LINE_FOLLOWER_H

#include <stdint.h>
#include "PIDController.h"
#include "FollowerStateMachine.h"
#include "IntersectionDetector.h"
#include "RecoveryStrategy.h"
#include "LineErrorEstimator.h"
#include "MotorMixer.h"
#include "MotionController.h"

class LineFollower {
public:
    static LineFollower& instance();

    // Main tick: processes mask, updates state, computes motor speeds
    bool update(uint8_t mask, int speed, int &leftMotor, int &rightMotor);

    // Commands
    void setSpeed(int speed) { _speed = speed; }
    void turnEncounterLine(int direction);
    void stopAtIntersection();
    void followForBmp(int speed, int degree);
    void stop();
    bool isStopped() const { return _stopped; }
    bool isBmpActive() const { return _bmpActive; }

    // Tuning
    void setPIDGains(float kp, float ki, float kd);
    void setPIDLimits(float min, float max);

    // Reset
    void reset();

private:
    LineFollower();

    // Components
    FollowerStateMachine _stateMachine;
    IntersectionDetector _intersectionDetector;
    RecoveryStrategy _recovery;
    MotionController _motionController;

    int _speed;
    bool _stopped;
    bool _turnRequested;
    int _turnDirection;
    bool _stopAtIntersectionRequested;

    // BMP
    bool _bmpActive;
    uint32_t _bmpStart;
    int _bmpDuration;
};

#endif