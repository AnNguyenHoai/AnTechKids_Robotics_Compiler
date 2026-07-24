#include "ObstacleStopBehavior.h"

ObstacleStopBehavior::ObstacleStopBehavior(int spd, int thresh)
    : speed(spd), threshold(thresh), isMoving(false), stopRequested(false) {
    name = "ObstacleStop";
}

void ObstacleStopBehavior::init(BehaviorContext& context) {
    setStatus(BehaviorStatus::INITIALIZED);
}

void ObstacleStopBehavior::start(BehaviorContext& context) {
    if (getStatus() == BehaviorStatus::INITIALIZED) {
        context.forward(speed);
        isMoving = true;
        stopRequested = false;
        setStatus(BehaviorStatus::RUNNING);
    }
}

void ObstacleStopBehavior::update(BehaviorContext& context) {
    if (!isMoving) return;
    int dist = context.readUltrasonic();
    if (dist < threshold) {
        context.stop();
        isMoving = false;
        setStatus(BehaviorStatus::COMPLETED);
    }
}

void ObstacleStopBehavior::pause() {}
void ObstacleStopBehavior::resume() {}
void ObstacleStopBehavior::stop() {
    isMoving = false;
    setStatus(BehaviorStatus::INTERRUPTED);
}
void ObstacleStopBehavior::reset() {
    isMoving = false;
    stopRequested = false;
    setStatus(BehaviorStatus::CREATED);
}