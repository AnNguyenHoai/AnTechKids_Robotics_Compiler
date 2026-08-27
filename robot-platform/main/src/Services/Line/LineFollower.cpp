#include "LineFollower.h"
#include "LinePerception.h"        // for LinePerception::interpret
#include <Arduino.h>
#include "../Robot/MotionConfig.h"
#include <math.h>

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
      _bmpDuration(0),
      _lastLineDirection(RecoveryStrategy::DIR_UNKNOWN),
      _lastControlUpdate(0),
      _wasRecovering(false) {
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

    // Reacquiring a line exits recovery in the same control cycle. Reset the
    // PID transient so the old search state cannot cause a derivative kick.
    if (_wasRecovering && mask != 0) {
        _pid.reset();
        _recovery.reset();
    }
    _wasRecovering = recovering;

    switch (fs) {
        case FollowerState::LOST:
            // Start a gentle directed recovery immediately instead of stopping
            // for 500 ms and then spinning aggressively.
            _recovery.update(mask, leftMotor, rightMotor);
            return true;

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

        default: {
            // H22: command-domain steering with one global calibration owner.
            //
            // LineFollower must output the normal motor command domain only.
            // RobotAPI::_setMotors() is the sole owner of motor calibration.
            // Do not invert or pre-apply left/right calibration here.
            //
            // Keep a little headroom so line tracking can slow one wheel while
            // the other remains at the requested speed. At full requested speed
            // there is no need to push either wheel above the caller's command.
            const int baseSpeed = constrain(speed, 0, 100);
            int steering = 0;

            // Discrete three-sensor steering. Values are intentionally moderate:
            // calibration already compensates straight-line motor mismatch.
            const int softSteering = max(8, (int)roundf(baseSpeed * 0.10f));
            const int hardSteering = max(15, (int)roundf(baseSpeed * 0.22f));

            switch (state) {
                case LineState::LEFT:
                    steering = hardSteering;
                    break;
                case LineState::LEFT_CENTER:
                    steering = softSteering;
                    break;
                case LineState::RIGHT:
                    steering = -hardSteering;
                    break;
                case LineState::CENTER_RIGHT:
                    steering = -softSteering;
                    break;
                case LineState::CENTER:
                default:
                    steering = 0;
                    break;
            }

            // Positive steering turns left: left wheel slows, right wheel keeps
            // the requested base command. Negative steering is symmetric.
            if (steering > 0) {
                leftMotor = max(0, baseSpeed - steering);
                rightMotor = baseSpeed;
            } else if (steering < 0) {
                leftMotor = baseSpeed;
                rightMotor = max(0, baseSpeed + steering);
            } else {
                // Preserve the exact calibrated straight command supplied by
                // the caller. RobotAPI applies calibration exactly once.
                leftMotor = baseSpeed;
                rightMotor = baseSpeed;
            }
            break;
        }
    }

    if (_stopAtIntersectionRequested && intersection) {
        _stopAtIntersectionRequested = false; _stopped = true; leftMotor = rightMotor = 0; return false;
    }
    if (_turnRequested && mask != 0) _turnRequested = false;
    return true;
}
