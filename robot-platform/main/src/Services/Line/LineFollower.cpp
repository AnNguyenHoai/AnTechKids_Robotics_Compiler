#include "LineFollower.h"
#include "LinePerception.h"
#include "LineErrorEstimator.h"
#include "MotorMixer.h"
#include <Arduino.h>
#include "../Robot/MotionConfig.h"
#include <math.h>

LineFollower& LineFollower::instance() {
    static LineFollower follower;
    return follower;
}

LineFollower::LineFollower()
    : _pid(1.0f, 0.0f, 0.0f, 0.02f),
      _speed(50),
      _stopped(false),
      _turnRequested(false),
      _turnDirection(0),
      _stopAtIntersectionRequested(false),
      _bmpActive(false),
      _bmpDuration(0),
      _lastLineDirection(RecoveryStrategy::DIR_UNKNOWN),
      _lastControlUpdate(0),
      _wasRecovering(false),
      _scaleFactor(10.0f)
{
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
    _lastLineDirection = RecoveryStrategy::DIR_UNKNOWN;
    _lastControlUpdate = 0;
    _wasRecovering = false;
    _recovery.reset();
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
    if (_stopped) { leftMotor = rightMotor = 0; return false; }

    if (_bmpActive && millis() - _bmpStart >= _bmpDuration) {
        _bmpActive = false; _stopped = true; leftMotor = rightMotor = 0; return false;
    }

    LineState state = LinePerception::interpret(mask);

    // Remember the last side that actually saw the line.
    if (state == LineState::LEFT || state == LineState::LEFT_CENTER) {
        _lastLineDirection = RecoveryStrategy::DIR_LEFT;
        _recovery.setLastDirection(_lastLineDirection);
    } else if (state == LineState::RIGHT || state == LineState::CENTER_RIGHT) {
        _lastLineDirection = RecoveryStrategy::DIR_RIGHT;
        _recovery.setLastDirection(_lastLineDirection);
    }

    bool intersection = _intersectionDetector.update(mask);
    _stateMachine.update(mask, intersection, _turnRequested, _stopAtIntersectionRequested);
    FollowerState fs = _stateMachine.getState();
    bool recovering = (fs == FollowerState::LOST || fs == FollowerState::SEARCHING);

    // Recovery owns steering only after loss is confirmed. Start every recovery
    // episode from phase zero so behavior never depends on system uptime.
    if (recovering && !_wasRecovering) {
        _recovery.reset();
        _pid.reset();
    } else if (!recovering && _wasRecovering) {
        // Reacquiring the line clears recovery state and PID history before the
        // next FOLLOWING correction.
        _pid.reset();
        _recovery.reset();
    }
    _wasRecovering = recovering;

    switch (fs) {
        case FollowerState::LOST:
        case FollowerState::SEARCHING:
            _recovery.update(mask, leftMotor, rightMotor);
            return true;

        case FollowerState::INTERSECTION:
            if (_stopAtIntersectionRequested) {
                leftMotor = rightMotor = 0;
            } else {
                leftMotor = rightMotor = speed;
                _stateMachine.reset();
            }
            break;

        case FollowerState::TURNING:
            if (_turnDirection == 1) { leftMotor = -speed; rightMotor = speed; }
            else if (_turnDirection == 2) { leftMotor = speed; rightMotor = -speed; }
            else leftMotor = rightMotor = 0;
            break;

        default: { // FOLLOWING
            const int baseSpeed = constrain(speed, 0, 100);
            const float error = LineErrorEstimator::estimate(state);
            const float correction = _pid.update(error);
            MotorOutput out = MotorMixer::mix(baseSpeed, correction, _scaleFactor);
            leftMotor = out.left;
            rightMotor = out.right;
            break;
        }
    }

    if (_stopAtIntersectionRequested && intersection) {
        _stopAtIntersectionRequested = false; _stopped = true; leftMotor = rightMotor = 0; return false;
    }
    if (_turnRequested && mask != 0) _turnRequested = false;
    return true;
}
