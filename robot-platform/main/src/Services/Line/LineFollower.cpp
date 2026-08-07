#include "LineFollower.h"
#include "LinePerception.h"        // for LinePerception::interpret
#include <Arduino.h>

LineFollower& LineFollower::instance() {
    static LineFollower follower;
    return follower;
}

LineFollower::LineFollower()
    : _pid(1.2f, 0.02f, 0.5f, 0.02f),
      _speed(50),
      _stopped(false),
      _turnRequested(false),
      _turnDirection(0),
      _stopAtIntersectionRequested(false),
      _bmpActive(false),
      _bmpDuration(0) {
    _pid.setLimits(-100, 100);
}

void LineFollower::setPIDGains(float kp, float ki, float kd) {
    _pid.setGains(kp, ki, kd);
}

void LineFollower::setPIDLimits(float min, float max) {
    _pid.setLimits(min, max);
}

void LineFollower::reset() {
    _stopped = false;
    _stateMachine.reset();
    _pid.reset();
    _bmpActive = false;
    _turnRequested = false;
    _stopAtIntersectionRequested = false;
}

void LineFollower::turnEncounterLine(int direction) {
    _turnRequested = true;
    _turnDirection = direction; // 1 left, 2 right
    _stateMachine.requestTurn(direction);
}

void LineFollower::stopAtIntersection() {
    _stopAtIntersectionRequested = true;
    _stateMachine.requestStopAtIntersection();
}

void LineFollower::followForBmp(int speed, int degree) {
    _bmpDuration = degree * 5; // ms per degree (calibrate later)
    _bmpStart = millis();
    _bmpActive = true;
    _speed = speed;
    _stopped = false;
}

void LineFollower::stop() {
    _stopped = true;
    _stateMachine.reset();
    _pid.reset();
    _bmpActive = false;
}

bool LineFollower::update(uint8_t mask, int speed, int &leftMotor, int &rightMotor) {
    if (_stopped) {
        leftMotor = rightMotor = 0;
        return false;
    }

    // BMP timed follow
    if (_bmpActive) {
        if (millis() - _bmpStart < _bmpDuration) {
            // continue normal following
        } else {
            _bmpActive = false;
            _stopped = true;
            leftMotor = rightMotor = 0;
            return false;
        }
    }

    // ============================================================
    // CONTROL PIPELINE (SINGLE SOURCE OF TRUTH)
    // ============================================================

    // 1. Perception: mask → LineState
    LineState state = LinePerception::interpret(mask);

    // 2. Error Estimation: LineState → error
    float error = LineErrorEstimator::estimate(state);

    // 3. PID: error → correction
    float correction = _pid.update(error);

    // 4. Motor Mixing: correction + speed → left/right
    MotorOutput output = MotorMixer::mix(speed, correction);

    leftMotor = output.left;
    rightMotor = output.right;

    // ============================================================
    // STATE MACHINE OVERRIDES
    // ============================================================

    bool intersection = _intersectionDetector.update(mask);
    _stateMachine.update(mask, intersection, _turnRequested, _stopAtIntersectionRequested);

    FollowerState fs = _stateMachine.getState();

    switch (fs) {
        case FollowerState::LOST:
            leftMotor = rightMotor = 0;
            break;

        case FollowerState::SEARCHING:
            _recovery.update(mask, leftMotor, rightMotor);
            break;

        case FollowerState::INTERSECTION:
            leftMotor = rightMotor = 0;
            if (!_stopAtIntersectionRequested) {
                _stateMachine.reset();
            }
            break;

        case FollowerState::TURNING: {
            if (_turnDirection == 1) { // left
                leftMotor = -speed;
                rightMotor = speed;
            } else if (_turnDirection == 2) { // right
                leftMotor = speed;
                rightMotor = -speed;
            } else {
                leftMotor = rightMotor = 0;
            }
            break;
        }

        default: // FOLLOWING and others: use the mixed output
            break;
    }

    // Intersection stop override
    if (_stopAtIntersectionRequested && intersection) {
        _stopAtIntersectionRequested = false;
        _stopped = true;
        leftMotor = rightMotor = 0;
        return false;
    }

    // Turn request cleared when line found
    if (_turnRequested && (mask != 0)) {
        _turnRequested = false;
    }

    return true;
}