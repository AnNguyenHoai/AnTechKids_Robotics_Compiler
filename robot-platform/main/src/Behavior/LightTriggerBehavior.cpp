#include "LightTriggerBehavior.h"

LightTriggerBehavior::LightTriggerBehavior(int ch, int th, int spd)
    : channel(ch), threshold(th), speed(spd), isMoving(false) {
    name = "LightTrigger";
}

void LightTriggerBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void LightTriggerBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.forward(speed);
        isMoving = true;
        setStatus(BehaviorStatus::RUNNING);
    }
}

void LightTriggerBehavior::update(BehaviorContext& context) {
    if (!isMoving) return;
    if (context.readLight(channel) > threshold) {
        context.stop();
        isMoving = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void LightTriggerBehavior::pause() {}
void LightTriggerBehavior::resume() {}
void LightTriggerBehavior::stop() {
    isMoving = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void LightTriggerBehavior::reset() {
    isMoving = false;
    setStatus(BehaviorStatus::CREATED);
}