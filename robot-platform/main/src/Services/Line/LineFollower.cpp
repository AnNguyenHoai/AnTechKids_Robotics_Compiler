#include "LineFollower.h"
#include "LinePerception.h"
#include "LineErrorEstimator.h"
#include "MotorMixer.h"
#include "../../Sensor/LineSensorSnapshot.h"
#include <Arduino.h>
#include "../Robot/MotionConfig.h"
#include <math.h>

#ifndef LINE_REGRESSION_DIAGNOSTICS
#define LINE_REGRESSION_DIAGNOSTICS 0
#endif

#ifndef LINE_REGRESSION_LEGACY_ACQUISITION
#define LINE_REGRESSION_LEGACY_ACQUISITION 0
#endif

namespace {
#if LINE_REGRESSION_DIAGNOSTICS
void emitLineRegressionDecision(
    uint8_t mask,
    LineState lineState,
    FollowerState followerState,
    float semanticError,
    int leftMotor,
    int rightMotor)
{
    // Keep qualification telemetry sparse enough that Serial itself does not
    // become the line-follow timing bottleneck. Emit every state transition and
    // a low-rate heartbeat while a state remains unchanged.
    static uint8_t lastMask = 0xFF;
    static int lastFollowerState = -1;
    static uint32_t lastEmitMs = 0;
    const uint32_t now = millis();
    const int followerStateValue = static_cast<int>(followerState);
    if (mask == lastMask && followerStateValue == lastFollowerState &&
        static_cast<uint32_t>(now - lastEmitMs) < 100u) {
        return;
    }

    const auto& snapshot = LineSensorSnapshot::Current();
    Serial.printf(
        "[LINE-REG][FOLLOW] mode=%s mask=%u%u%u snapshot={valid:%d,mask:%u%u%u,seq:%lu} "
        "lineState=%d followerState=%d error=%.2f cmd={L:%d,R:%d}\n",
        LINE_REGRESSION_LEGACY_ACQUISITION ? "legacy" : "snapshot",
        (mask >> 2) & 1u, (mask >> 1) & 1u, mask & 1u,
        snapshot.valid ? 1 : 0,
        (snapshot.mask >> 2) & 1u, (snapshot.mask >> 1) & 1u, snapshot.mask & 1u,
        static_cast<unsigned long>(snapshot.sequence),
        static_cast<int>(lineState),
        followerStateValue,
        static_cast<double>(semanticError),
        leftMotor,
        rightMotor
    );
    lastMask = mask;
    lastFollowerState = followerStateValue;
    lastEmitMs = now;
}
#endif
}

LineFollower& LineFollower::instance() {
    static LineFollower follower;
    return follower;
}

LineFollower::LineFollower()
    : _pid(1.2f, 0.0f, 0.0f, 0.02f),
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
      _scaleFactor(15.0f)
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
    const LineState state = LinePerception::interpret(mask);
    const float semanticError = LineErrorEstimator::estimate(state);

    if (_stopped) {
        leftMotor = rightMotor = 0;
#if LINE_REGRESSION_DIAGNOSTICS
        emitLineRegressionDecision(mask, state, _stateMachine.getState(), semanticError, leftMotor, rightMotor);
#endif
        return false;
    }

    if (_bmpActive && millis() - _bmpStart >= _bmpDuration) {
        _bmpActive = false;
        _stopped = true;
        leftMotor = rightMotor = 0;
#if LINE_REGRESSION_DIAGNOSTICS
        emitLineRegressionDecision(mask, state, _stateMachine.getState(), semanticError, leftMotor, rightMotor);
#endif
        return false;
    }

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
#if LINE_REGRESSION_DIAGNOSTICS
            emitLineRegressionDecision(mask, state, fs, semanticError, leftMotor, rightMotor);
#endif
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
            const float correction = _pid.update(semanticError);
            MotorOutput out = MotorMixer::mix(baseSpeed, correction, _scaleFactor);
            leftMotor = out.left;
            rightMotor = out.right;
            break;
        }
    }

    if (_stopAtIntersectionRequested && intersection) {
        _stopAtIntersectionRequested = false;
        _stopped = true;
        leftMotor = rightMotor = 0;
#if LINE_REGRESSION_DIAGNOSTICS
        emitLineRegressionDecision(mask, state, fs, semanticError, leftMotor, rightMotor);
#endif
        return false;
    }
    if (_turnRequested && mask != 0) _turnRequested = false;
#if LINE_REGRESSION_DIAGNOSTICS
    emitLineRegressionDecision(mask, state, fs, semanticError, leftMotor, rightMotor);
#endif
    return true;
}
