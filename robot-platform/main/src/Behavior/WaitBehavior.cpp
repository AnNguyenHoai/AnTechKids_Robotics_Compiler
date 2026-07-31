#include "WaitBehavior.h"

WaitBehavior::WaitBehavior(uint32_t  dur)
    : durationMs(dur), startTime(0), isRunning(false) {
    name = "Wait";
}

void WaitBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void WaitBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        isRunning = true;
        startTime = millis();
        setStatus(BehaviorStatus::RUNNING);
    }
}

void WaitBehavior::update(BehaviorContext& context) {
    if (!isRunning) return;
    if (millis() - startTime >= durationMs) {
        isRunning = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void WaitBehavior::pause() {}
void WaitBehavior::resume() {}
void WaitBehavior::stop() {
    isRunning = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void WaitBehavior::reset() {
    isRunning = false;
    setStatus(BehaviorStatus::CREATED);
}