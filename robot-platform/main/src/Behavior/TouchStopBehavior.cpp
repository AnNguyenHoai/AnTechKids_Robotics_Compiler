#include "TouchStopBehavior.h"

TouchStopBehavior::TouchStopBehavior(int p, int spd) 
    : port(p), speed(spd), isMoving(false), stopRequested(false) {
    name = "TouchStop";
}

void TouchStopBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void TouchStopBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.forward(speed);
        isMoving = true;
        stopRequested = false;
        setStatus(BehaviorStatus::RUNNING);
    }
}

void TouchStopBehavior::update(BehaviorContext& context) {
    if (!isMoving) return;
    if (stopRequested) {
        context.stop();
        isMoving = false;
        setStatus(BehaviorStatus::COMPLETED);
        return;
    }
    // Kiểm tra cảm biến touch
    if (context.readTouch(port) == 1) {
        stopRequested = true;
        // Sẽ dừng ở vòng lặp tiếp theo (hoặc dừng ngay)
        context.stop();
        isMoving = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void TouchStopBehavior::pause() {}
void TouchStopBehavior::resume() {}
void TouchStopBehavior::stop() {
    isMoving = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void TouchStopBehavior::reset() {
    isMoving = false;
    stopRequested = false;
    setStatus(BehaviorStatus::CREATED);
}