#include "MoveForwardBehavior.h"

MoveForwardBehavior::MoveForwardBehavior(int spd, uint32_t  dur) 
    : speed(spd), durationMs(dur), startTime(0), isRunning(false) {
    name = "MoveForward";
}

void MoveForwardBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void MoveForwardBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.forward(speed);
        isRunning = true;
        startTime = millis();
        setStatus(BehaviorStatus::RUNNING);
    }
}

void MoveForwardBehavior::update(BehaviorContext& context) {
    if (!isRunning) return;
    if (durationMs > 0 && (millis() - startTime >= durationMs)) {
        context.stop();
        isRunning = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void MoveForwardBehavior::pause() {}
void MoveForwardBehavior::resume() {}
void MoveForwardBehavior::stop() {
    isRunning = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void MoveForwardBehavior::reset() {
    isRunning = false;
    setStatus(BehaviorStatus::CREATED);
}