#include "StopBehavior.h"

StopBehavior::StopBehavior() {
    name = "Stop";
}

void StopBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void StopBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.stop();
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void StopBehavior::update(BehaviorContext& context) {}
void StopBehavior::pause() {}
void StopBehavior::resume() {}
void StopBehavior::stop() {
    setStatus(BehaviorStatus::INTERRUPTED);
}
void StopBehavior::reset() {
    setStatus(BehaviorStatus::CREATED);
}