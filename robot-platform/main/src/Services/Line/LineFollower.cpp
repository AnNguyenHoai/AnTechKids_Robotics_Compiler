#include "LineFollower.h"
#include "LineErrorEstimator.h"
#include "MotorMixer.h"
#include "LineSensorLayout.h"
#include <Arduino.h>
#include "../Robot/MotionConfig.h"
#include <math.h>

namespace {
constexpr float LAST_DIRECTION_THRESHOLD = 0.25f;
constexpr float ERROR_FILTER_ALPHA = 0.70f;
constexpr float GAP_DIRECTIONAL_THRESHOLD = 0.25f;
constexpr float CONTROL_DEADBAND = 0.20f;
constexpr uint8_t STEER_CONFIRM_TICKS = 2;
constexpr float SPEED_FACTOR_MILD = 0.85f;
constexpr float SPEED_FACTOR_MEDIUM = 0.70f;
constexpr float SPEED_FACTOR_STRONG = 0.60f;
// FAR-only / FAR+adjacent means the line has reached the edge of the array.
// Treat it as a corner event rather than waiting for generic LOST recovery.
constexpr uint32_t SHARP_CORNER_HOLD_MS = 350;
}

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
      _sharpDirection(0),
      _sharpStartedMs(0),
      _stableSteerDirection(0),
      _pendingSteerDirection(0),
      _pendingSteerTicks(0),
      _filteredError(0.0f),
      _filterInitialized(false),
      _lastRawError(0.0f),
      _lastFilteredError(0.0f),
      _lastCorrection(0.0f),
      _scaleFactor(12.0f)
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
    _sharpDirection = 0;
    _sharpStartedMs = 0;
    _stableSteerDirection = 0;
    _pendingSteerDirection = 0;
    _pendingSteerTicks = 0;
    _filteredError = 0.0f;
    _filterInitialized = false;
    _lastRawError = 0.0f;
    _lastFilteredError = 0.0f;
    _lastCorrection = 0.0f;
    _recovery.reset();
}

void LineFollower::turnEncounterLine(int direction) {
    _turnRequested = true;
    _turnDirection = direction;
    _stateMachine.requestTurn(direction);
}

void LineFollower::stopAtIntersection() {
    _stopAtIntersectionRequested = true;
    _stateMachine.requestStopAtIntersection();
}

void LineFollower::followForBmp(int speed, int degree) {
    _bmpDuration = degree * 5;
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
    _sharpDirection = 0;
    _sharpStartedMs = 0;
    _stableSteerDirection = 0;
    _pendingSteerDirection = 0;
    _pendingSteerTicks = 0;
    _filteredError = 0.0f;
    _filterInitialized = false;
    _lastRawError = 0.0f;
    _lastFilteredError = 0.0f;
    _lastCorrection = 0.0f;
}

bool LineFollower::update(uint8_t mask, int speed, int &leftMotor, int &rightMotor) {
    if (_stopped) { leftMotor = rightMotor = 0; return false; }

    if (_bmpActive && millis() - _bmpStart >= _bmpDuration) {
        _bmpActive = false; _stopped = true; leftMotor = rightMotor = 0; return false;
    }

    const float rawError = LineErrorEstimator::estimate(mask);
    _lastRawError = rawError;

    // Direction persistence: a new left/right/center observation must survive
    // two consecutive 5 ms ticks before it is allowed to reverse/establish
    // steering direction. This rejects one-sample L+C <-> C <-> C+R chatter
    // without delaying FAR sharp-corner handling below.
    int observedDirection = 0;
    if (rawError < -LAST_DIRECTION_THRESHOLD) observedDirection = -1;
    else if (rawError > LAST_DIRECTION_THRESHOLD) observedDirection = 1;

    bool directionConfirmed = (observedDirection == _stableSteerDirection);
    if (!directionConfirmed) {
        if (observedDirection == _pendingSteerDirection) {
            if (_pendingSteerTicks < 255) _pendingSteerTicks++;
        } else {
            _pendingSteerDirection = observedDirection;
            _pendingSteerTicks = 1;
        }

        if (_pendingSteerTicks >= STEER_CONFIRM_TICKS) {
            _stableSteerDirection = observedDirection;
            _pendingSteerDirection = 0;
            _pendingSteerTicks = 0;
            directionConfirmed = true;
        }
    } else {
        _pendingSteerDirection = 0;
        _pendingSteerTicks = 0;
    }

    // A transient unconfirmed direction contributes zero steering error rather
    // than immediately flipping the chassis. Confirmed samples feed the normal
    // low-pass filter. Zero-mask still holds the last valid estimate.
    if (mask != 0) {
        const float filterInput = directionConfirmed ? rawError : 0.0f;
        if (!_filterInitialized) {
            _filteredError = filterInput;
            _filterInitialized = true;
        } else {
            _filteredError += ERROR_FILTER_ALPHA * (filterInput - _filteredError);
        }
    }
    _lastFilteredError = _filteredError;

    // Recovery direction follows the immediate spatial observation so a mild
    // low-pass filter cannot hide which side the line was last seen on.
    if (rawError < -LAST_DIRECTION_THRESHOLD) {
        _lastLineDirection = RecoveryStrategy::DIR_LEFT;
        _recovery.setLastDirection(_lastLineDirection);
    } else if (rawError > LAST_DIRECTION_THRESHOLD) {
        _lastLineDirection = RecoveryStrategy::DIR_RIGHT;
        _recovery.setLastDirection(_lastLineDirection);
    }

    bool intersection = _intersectionDetector.update(mask);

    // Sharp-corner assist:
    // - Enter immediately when the line reaches a FAR eye without center/other
    //   side evidence. This is the earliest reliable indication that normal
    //   proportional following no longer has enough curvature authority.
    // - If the FAR eye is followed by 00000, keep turning in the same direction
    //   instead of paying the 40 ms LOST debounce + 300 ms soft-recovery delay.
    // - Exit as soon as any non-zero mask no longer satisfies the same sharp
    //   edge condition. A bounded timeout prevents an endless turn if the line
    //   is genuinely gone.
    const uint8_t cleanMask = LineSensorLayout::sanitizeMask(mask);
    const bool sharpLeftObserved =
        (cleanMask & LineSensorLayout::MASK_FAR_LEFT) != 0 &&
        (cleanMask & (LineSensorLayout::MASK_CENTER |
                      LineSensorLayout::MASK_RIGHT |
                      LineSensorLayout::MASK_FAR_RIGHT)) == 0;
    const bool sharpRightObserved =
        (cleanMask & LineSensorLayout::MASK_FAR_RIGHT) != 0 &&
        (cleanMask & (LineSensorLayout::MASK_CENTER |
                      LineSensorLayout::MASK_LEFT |
                      LineSensorLayout::MASK_FAR_LEFT)) == 0;

    if (!intersection) {
        if (sharpLeftObserved) {
            _sharpDirection = RecoveryStrategy::DIR_LEFT;
            _sharpStartedMs = millis();
        } else if (sharpRightObserved) {
            _sharpDirection = RecoveryStrategy::DIR_RIGHT;
            _sharpStartedMs = millis();
        }
    }

    if (_sharpDirection != 0) {
        const uint32_t sharpAgeMs = millis() - _sharpStartedMs;
        const bool sameEdgeVisible =
            (_sharpDirection == RecoveryStrategy::DIR_LEFT && sharpLeftObserved) ||
            (_sharpDirection == RecoveryStrategy::DIR_RIGHT && sharpRightObserved);
        const bool continueThroughCornerGap =
            cleanMask == 0 && sharpAgeMs <= SHARP_CORNER_HOLD_MS;

        if (sameEdgeVisible || continueThroughCornerGap) {
            // One-wheel pivot around the inner wheel. The Line5 pair mapper
            // keeps the outer wheel above the measured start threshold while
            // preserving a true zero on the inner wheel.
            const int outerSpeed = constrain(speed, 0, 100);
            _lastCorrection = (_sharpDirection == RecoveryStrategy::DIR_LEFT) ? -100.0f : 100.0f;
            if (_sharpDirection == RecoveryStrategy::DIR_LEFT) {
                leftMotor = 0;
                rightMotor = outerSpeed;
            } else {
                leftMotor = outerSpeed;
                rightMotor = 0;
            }
            return true;
        }

        // Reacquired line, or sharp hold expired. Clear assist and let the
        // normal state machine/PID decide from the current sample.
        _sharpDirection = 0;
        _sharpStartedMs = 0;
    }

    _stateMachine.update(mask, intersection, _turnRequested, _stopAtIntersectionRequested);
    FollowerState fs = _stateMachine.getState();
    bool recovering = (fs == FollowerState::LOST || fs == FollowerState::SEARCHING);

    // Start every real recovery from phase zero. Previously _phaseStart could
    // be stale, causing the first LOST event to jump straight into deep/sweep.
    if (recovering && !_wasRecovering) {
        _recovery.reset();
    }

    // Keep V1 reacquire semantics for this task: any active line sensor exits
    // recovery. Center-zone-only reacquire remains a hardware-validation item.
    if (_wasRecovering && mask != 0) {
        _pid.reset();
        _recovery.reset();
        _filteredError = rawError;
        _lastFilteredError = rawError;
        _filterInitialized = true;
    }
    _wasRecovering = recovering;

    switch (fs) {
        case FollowerState::LOST:
        case FollowerState::SEARCHING:
            _lastCorrection = 0.0f;
            _recovery.update(mask, leftMotor, rightMotor);
            return true;

        case FollowerState::INTERSECTION:
            _lastCorrection = 0.0f;
            if (_stopAtIntersectionRequested) {
                leftMotor = rightMotor = 0;
            } else {
                leftMotor = rightMotor = speed;
                _stateMachine.reset();
            }
            break;

        case FollowerState::TURNING:
            _lastCorrection = 0.0f;
            if (_turnDirection == 1) { leftMotor = -speed; rightMotor = speed; }
            else if (_turnDirection == 2) { leftMotor = speed; rightMotor = -speed; }
            else leftMotor = rightMotor = 0;
            break;

        default: {
            const int requestedSpeed = constrain(speed, 0, 100);

            // Real Line5 hardware commonly reports a brief 00000 while the line
            // crosses the physical gap between adjacent eyes. During the LOST
            // debounce window we must not keep driving straight at full line
            // speed when the last steering estimate was centered.
            if (mask == 0 &&
                (!_filterInitialized || fabsf(_filteredError) < GAP_DIRECTIONAL_THRESHOLD)) {
                _lastCorrection = 0.0f;
                leftMotor = 0;
                rightMotor = 0;
                break;
            }

            // Progressive speed scheduling: the further the line moves from
            // center, the less forward velocity we carry into the correction.
            // This reduces chassis overshoot on arcs and gives the FAR sharp
            // turn a much smaller outward momentum to arrest.
            const float scheduleError = fmaxf(
                fabsf(_filteredError),
                (_stableSteerDirection != 0) ? fabsf(rawError) : 0.0f
            );

            float speedFactor = 1.0f;
            if (scheduleError > 1.25f) speedFactor = SPEED_FACTOR_STRONG;
            else if (scheduleError > 0.75f) speedFactor = SPEED_FACTOR_MEDIUM;
            else if (scheduleError > CONTROL_DEADBAND) speedFactor = SPEED_FACTOR_MILD;

            const int baseSpeed = constrain(
                (int)lroundf((float)requestedSpeed * speedFactor),
                0,
                100
            );

            // Small residual error around CENTER is ignored to prevent the
            // controller from hunting left/right on a wide digital line.
            const float controlError =
                fabsf(_filteredError) < CONTROL_DEADBAND ? 0.0f : _filteredError;

            const float correction = _pid.update(controlError);
            _lastCorrection = correction;
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
        return false;
    }
    if (_turnRequested && mask != 0) _turnRequested = false;
    return true;
}