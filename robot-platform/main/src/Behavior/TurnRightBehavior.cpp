#include "TurnRightBehavior.h"

TurnRightBehavior::TurnRightBehavior(int spd, uint32_t  dur)
    : speed(spd), durationMs(dur), startTime(0), isRunning(false) {
    name = "TurnRight";
}

void TurnRightBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void TurnRightBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.turnRight(speed);
        isRunning = true;
        startTime = millis();
        setStatus(BehaviorStatus::RUNNING);
    }
}

void TurnRightBehavior::update(BehaviorContext& context) {
    if (!isRunning) return;
    if (durationMs > 0 && (millis() - startTime >= durationMs)) {
        context.stop();
        isRunning = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void TurnRightBehavior::pause() {
    // Không hỗ trợ tạm dừng
}

void TurnRightBehavior::resume() {
    // Không hỗ trợ tiếp tục
}

void TurnRightBehavior::stop() {
    isRunning = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}

void TurnRightBehavior::reset() {
    isRunning = false;
    setStatus(BehaviorStatus::CREATED);
}