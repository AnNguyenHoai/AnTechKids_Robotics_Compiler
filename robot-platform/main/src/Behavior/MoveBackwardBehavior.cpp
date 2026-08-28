#include "MoveBackwardBehavior.h"

MoveBackwardBehavior::MoveBackwardBehavior(int spd, uint16_t dur)
    : speed(spd), durationMs(dur), startTime(0), isRunning(false) {
    name = "MoveBackward";
}

void MoveBackwardBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void MoveBackwardBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.backward(speed);
        isRunning = true;
        startTime = millis();
        setStatus(BehaviorStatus::RUNNING);
    }
}

void MoveBackwardBehavior::update(BehaviorContext& context) {
    if (!isRunning) return;
    if (durationMs > 0 && (millis() - startTime >= durationMs)) {
        context.stop();
        isRunning = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void MoveBackwardBehavior::pause() {}
void MoveBackwardBehavior::resume() {}
void MoveBackwardBehavior::stop() {
    isRunning = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void MoveBackwardBehavior::reset() {
    isRunning = false;
    setStatus(BehaviorStatus::CREATED);
}