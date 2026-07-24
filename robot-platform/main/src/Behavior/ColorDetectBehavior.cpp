#include "ColorDetectBehavior.h"

ColorDetectBehavior::ColorDetectBehavior(int target, int spd)
    : targetColor(target), speed(spd), isMoving(false) {
    name = "ColorDetect";
}

void ColorDetectBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void ColorDetectBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.forward(speed);
        isMoving = true;
        setStatus(BehaviorStatus::RUNNING);
    }
}

void ColorDetectBehavior::update(BehaviorContext& context) {
    if (!isMoving) return;
    // Color sensor placeholder: giả sử readColor() trả về giá trị màu
    if (context.readColor() == targetColor) {
        context.stop();
        isMoving = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void ColorDetectBehavior::pause() {}
void ColorDetectBehavior::resume() {}
void ColorDetectBehavior::stop() {
    isMoving = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void ColorDetectBehavior::reset() {
    isMoving = false;
    setStatus(BehaviorStatus::CREATED);
}