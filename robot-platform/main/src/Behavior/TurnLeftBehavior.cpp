#include "TurnLeftBehavior.h"

TurnLeftBehavior::TurnLeftBehavior(int spd, uint16_t dur)
    : speed(spd), durationMs(dur), startTime(0), isRunning(false) {
    name = "TurnLeft";
}

void TurnLeftBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void TurnLeftBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.turnLeft(speed);
        isRunning = true;
        startTime = millis();
        setStatus(BehaviorStatus::RUNNING);
    }
}

void TurnLeftBehavior::update(BehaviorContext& context) {
    if (!isRunning) return;
    if (durationMs > 0 && (millis() - startTime >= durationMs)) {
        context.stop();
        isRunning = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void TurnLeftBehavior::pause() {}
void TurnLeftBehavior::resume() {}
void TurnLeftBehavior::stop() {
    isRunning = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void TurnLeftBehavior::reset() {
    isRunning = false;
    setStatus(BehaviorStatus::CREATED);
}