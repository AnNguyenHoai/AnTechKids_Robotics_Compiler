#include "LineDetectBehavior.h"

LineDetectBehavior::LineDetectBehavior(int ch, int spd)
    : channel(ch), speed(spd), isMoving(false) {
    name = "LineDetect";
}

void LineDetectBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void LineDetectBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.forward(speed);
        isMoving = true;
        setStatus(BehaviorStatus::RUNNING);
    }
}

void LineDetectBehavior::update(BehaviorContext& context) {
    if (!isMoving) return;
    if (context.readLine(channel) == 1) {
        context.stop();
        isMoving = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void LineDetectBehavior::pause() {}
void LineDetectBehavior::resume() {}
void LineDetectBehavior::stop() {
    isMoving = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void LineDetectBehavior::reset() {
    isMoving = false;
    setStatus(BehaviorStatus::CREATED);
}