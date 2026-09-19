#include "CooperativeLineOperation.h"

#include <Arduino.h>

#include "../Line/LineFollower.h"
#include "../Robot/RobotAPI.h"

namespace {
constexpr uint32_t kLineTickIntervalMs = 20UL;
constexpr uint32_t kMaxRelativeDeadlineMs = 0x7FFFFFFFUL;

struct OperationState {
    CooperativeLineOperation::Kind kind = CooperativeLineOperation::Kind::None;
    int speed = 0;
    uint32_t deadlineMs = 0;
    uint32_t nextTickMs = 0;
};

OperationState g_state;

bool timeReached(uint32_t now, uint32_t target) {
    return static_cast<int32_t>(now - target) >= 0;
}

void clearState() {
    g_state = OperationState{};
}

bool runtimeAvailable() {
    return RobotAPI::isRobotReady() &&
           RobotAPI::isHardwareEnabled(HardwareCapability::Device::LineSensor);
}

bool beginCommon(CooperativeLineOperation::Kind kind, int speed) {
    if (!runtimeAvailable()) {
        clearState();
        return false;
    }

    if (g_state.kind != CooperativeLineOperation::Kind::None) {
        CooperativeLineOperation::Cancel(true);
    }

    const uint32_t now = millis();
    g_state.kind = kind;
    g_state.speed = speed;
    g_state.deadlineMs = 0;
    g_state.nextTickMs = now;
    return true;
}

void finishAndStop() {
    LineFollower::instance().stop();
    RobotAPI::Stop();
    clearState();
}

} // namespace

namespace CooperativeLineOperation {

bool StartMillisecond(int speed, int milliseconds) {
    if (milliseconds <= 0) {
        RobotAPI::LineStop();
        clearState();
        return false;
    }
    if (!beginCommon(Kind::Millisecond, speed)) {
        return false;
    }

    auto& follower = LineFollower::instance();
    follower.setSpeed(speed);
    follower.reset();

    const uint32_t duration = static_cast<uint32_t>(milliseconds) > kMaxRelativeDeadlineMs
        ? kMaxRelativeDeadlineMs
        : static_cast<uint32_t>(milliseconds);
    g_state.deadlineMs = millis() + duration;

    return Update();
}

bool StartIntersectionStop(int speed, int type) {
    (void)type; // Existing RobotAPI behavior does not use the type parameter yet.
    if (!beginCommon(Kind::IntersectionStop, speed)) {
        return false;
    }

    auto& follower = LineFollower::instance();
    follower.reset();
    follower.setSpeed(speed);
    follower.stopAtIntersection();
    return Update();
}

bool StartTurnEncounterLine(int speed, int angle, int direction) {
    (void)angle; // Existing RobotAPI behavior currently uses direction only.
    if (!beginCommon(Kind::TurnEncounterLine, speed)) {
        return false;
    }

    auto& follower = LineFollower::instance();
    follower.reset();
    follower.setSpeed(speed);
    follower.turnEncounterLine(direction);
    return Update();
}

bool StartBmp(int speed, int degree) {
    if (!beginCommon(Kind::Bmp, speed)) {
        return false;
    }

    auto& follower = LineFollower::instance();
    follower.followForBmp(speed, degree);
    return Update();
}

bool Update() {
    if (g_state.kind == Kind::None) {
        return false;
    }

    if (!runtimeAvailable()) {
        Cancel(true);
        return false;
    }

    uint32_t now = millis();
    if (g_state.kind == Kind::Millisecond && timeReached(now, g_state.deadlineMs)) {
        finishAndStop();
        return false;
    }

    if (!timeReached(now, g_state.nextTickMs)) {
        return true;
    }
    g_state.nextTickMs = now + kLineTickIntervalMs;

    // LineBasis is a single bounded sensor/control/output tick. It also owns the
    // transition into LINE motion-control mode, preventing the heading loop from
    // overwriting line motor commands between cooperative VM steps.
    RobotAPI::LineBasis(g_state.speed);

    auto& follower = LineFollower::instance();
    switch (g_state.kind) {
        case Kind::Millisecond:
            now = millis();
            if (timeReached(now, g_state.deadlineMs)) {
                finishAndStop();
                return false;
            }
            return true;

        case Kind::IntersectionStop:
            if (follower.isStopped()) {
                clearState();
                return false;
            }
            return true;

        case Kind::TurnEncounterLine:
            // LineFollower clears its turn request in the same control tick that
            // reacquires a line. Query that state rather than sampling the sensor
            // a second time, so cooperative execution preserves legacy completion
            // semantics exactly for the mask that drove the motor update.
            if (!follower.isTurnRequested()) {
                clearState();
                return false;
            }
            return true;

        case Kind::Bmp:
            if (!follower.isBmpActive()) {
                finishAndStop();
                return false;
            }
            return true;

        case Kind::None:
        default:
            return false;
    }
}

bool IsActive() {
    return g_state.kind != Kind::None;
}

Kind CurrentKind() {
    return g_state.kind;
}

void Cancel(bool stopMotion) {
    if (g_state.kind == Kind::None) {
        return;
    }

    LineFollower::instance().stop();
    clearState();
    if (stopMotion) {
        RobotAPI::Stop();
    }
}

} // namespace CooperativeLineOperation
